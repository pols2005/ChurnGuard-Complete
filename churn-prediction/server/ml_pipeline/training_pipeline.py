# ChurnGuard Automated Training Pipeline
# Epic 2 - Advanced ML Pipeline Implementation

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import logging
import json
from dataclasses import dataclass, asdict

# ML Libraries
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb

from .model_registry import ModelRegistry, ModelMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for training pipeline"""
    model_id: str
    algorithms: List[str]
    hyperparameter_tuning: bool
    cross_validation_folds: int
    test_size: float
    random_state: int
    feature_selection: bool
    auto_promotion: bool  # Auto-promote best model to staging
    training_data_path: str
    target_column: str
    created_by: str

class AutomatedTrainingPipeline:
    """Automated training pipeline for ChurnGuard models"""
    
    def __init__(self, registry: ModelRegistry, config_path: str = "models/training"):
        self.registry = registry
        self.config_path = Path(config_path)
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        # Algorithm configurations
        self.algorithms = {
            'xgboost': {
                'model_class': xgb.XGBClassifier,
                'hyperparameters': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'subsample': [0.8, 1.0]
                }
            },
            'random_forest': {
                'model_class': RandomForestClassifier,
                'hyperparameters': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [None, 10, 20],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            },
            'gradient_boosting': {
                'model_class': GradientBoostingClassifier,
                'hyperparameters': {
                    'n_estimators': [100, 200],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2]
                }
            },
            'extra_trees': {
                'model_class': ExtraTreesClassifier,
                'hyperparameters': {
                    'n_estimators': [100, 200],
                    'max_depth': [None, 10, 20],
                    'min_samples_split': [2, 5, 10]
                }
            },
            'knn': {
                'model_class': KNeighborsClassifier,
                'hyperparameters': {
                    'n_neighbors': [3, 5, 7, 11],
                    'weights': ['uniform', 'distance'],
                    'algorithm': ['ball_tree', 'kd_tree', 'brute']
                }
            },
            'adaboost': {
                'model_class': AdaBoostClassifier,
                'hyperparameters': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 1.0],
                    'algorithm': ['SAMME', 'SAMME.R']
                }
            },
            'logistic_regression': {
                'model_class': LogisticRegression,
                'hyperparameters': {
                    'C': [0.1, 1.0, 10.0],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear', 'saga']
                }
            },
            'svm': {
                'model_class': SVC,
                'hyperparameters': {
                    'C': [0.1, 1.0, 10.0],
                    'kernel': ['rbf', 'linear', 'poly'],
                    'gamma': ['scale', 'auto']
                }
            },
            'naive_bayes': {
                'model_class': GaussianNB,
                'hyperparameters': {}
            },
            'decision_tree': {
                'model_class': DecisionTreeClassifier,
                'hyperparameters': {
                    'max_depth': [None, 5, 10, 20],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            }
        }
    
    def load_and_prepare_data(self, data_path: str, target_column: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Load and prepare training data"""
        logger.info(f"Loading data from {data_path}")
        
        # Load data
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        
        # Separate features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Handle categorical variables
        categorical_columns = X.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col in ['Geography', 'Gender']:  # Known categorical features
                # One-hot encode
                dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
                X = pd.concat([X.drop(columns=[col]), dummies], axis=1)
        
        # Remove non-feature columns if they exist
        columns_to_remove = ['RowNumber', 'CustomerId', 'Surname']
        X = X.drop(columns=[col for col in columns_to_remove if col in X.columns])
        
        feature_names = list(X.columns)
        
        logger.info(f"Prepared {len(feature_names)} features: {feature_names}")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")
        
        return X, y, feature_names
    
    def train_single_model(
        self,
        algorithm: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        hyperparameter_tuning: bool = True,
        cv_folds: int = 5
    ) -> Tuple[Any, Dict[str, Any], float]:
        """Train a single model with optional hyperparameter tuning"""
        
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        config = self.algorithms[algorithm]
        model_class = config['model_class']
        hyperparams = config['hyperparameters']
        
        logger.info(f"Training {algorithm} model")
        
        if hyperparameter_tuning and hyperparams:
            # Grid search with cross-validation
            logger.info(f"Performing hyperparameter tuning with {cv_folds}-fold CV")
            grid_search = GridSearchCV(
                model_class(),
                hyperparams,
                cv=cv_folds,
                scoring='f1_weighted',
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            cv_score = grid_search.best_score_
            
            logger.info(f"Best parameters: {best_params}")
            logger.info(f"Best CV score: {cv_score:.4f}")
            
        else:
            # Train with default parameters
            model = model_class()
            model.fit(X_train, y_train)
            best_params = model.get_params()
            
            # Calculate cross-validation score
            cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='f1_weighted')
            cv_score = np.mean(cv_scores)
        
        return model, best_params, cv_score
    
    def run_training_pipeline(self, config: TrainingConfig) -> Dict[str, Any]:
        """Run complete training pipeline"""
        
        logger.info(f"Starting training pipeline for model_id: {config.model_id}")
        
        # Load and prepare data
        X, y, feature_names = self.load_and_prepare_data(
            config.training_data_path, 
            config.target_column
        )
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=config.test_size,
            random_state=config.random_state,
            stratify=y
        )
        
        logger.info(f"Train set: {len(X_train)} samples, Test set: {len(X_test)} samples")
        
        # Train models
        results = {}
        trained_models = {}
        
        for algorithm in config.algorithms:
            try:
                model, params, cv_score = self.train_single_model(
                    algorithm,
                    X_train, y_train,
                    X_test, y_test,
                    config.hyperparameter_tuning,
                    config.cross_validation_folds
                )
                
                # Register model in registry
                model_key = self.registry.register_model(
                    model=model,
                    model_id=f"{config.model_id}_{algorithm}",
                    algorithm=algorithm,
                    X_test=X_test,
                    y_test=y_test,
                    features=feature_names,
                    hyperparameters=params,
                    tags=['automated_training'],
                    created_by=config.created_by
                )
                
                trained_models[algorithm] = model_key
                
                # Get performance metrics
                metadata = self.registry.get_model_metadata(model_key)
                results[algorithm] = {
                    'model_key': model_key,
                    'cv_score': cv_score,
                    'test_metrics': metadata.performance_metrics,
                    'hyperparameters': params
                }
                
                logger.info(f"Successfully trained {algorithm}: {model_key}")
                
            except Exception as e:
                logger.error(f"Failed to train {algorithm}: {str(e)}")
                results[algorithm] = {'error': str(e)}
        
        # Find best model
        best_model = None
        best_score = -1
        
        for algorithm, result in results.items():
            if 'error' not in result:
                f1_score = result['test_metrics'].get('f1_score', 0)
                if f1_score > best_score:
                    best_score = f1_score
                    best_model = algorithm
        
        # Auto-promote best model if configured
        if config.auto_promotion and best_model:
            best_model_key = results[best_model]['model_key']
            self.registry.promote_model(best_model_key, 'staging')
            logger.info(f"Auto-promoted {best_model_key} to staging")
        
        # Create summary
        summary = {
            'training_date': datetime.now().isoformat(),
            'config': asdict(config),
            'data_summary': {
                'total_samples': len(X),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'features': feature_names,
                'target_distribution': y.value_counts().to_dict()
            },
            'results': results,
            'best_model': best_model,
            'best_score': best_score,
            'trained_models': trained_models
        }
        
        # Save training log
        log_file = self.config_path / f"training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Training pipeline completed. Best model: {best_model} (F1: {best_score:.4f})")
        
        return summary
    
    def create_training_config(
        self,
        model_id: str,
        training_data_path: str,
        target_column: str = "Exited",
        algorithms: List[str] = None,
        hyperparameter_tuning: bool = True,
        created_by: str = "automated_pipeline"
    ) -> TrainingConfig:
        """Create training configuration with sensible defaults"""
        
        if algorithms is None:
            algorithms = ['xgboost', 'random_forest', 'gradient_boosting', 'extra_trees']
        
        return TrainingConfig(
            model_id=model_id,
            algorithms=algorithms,
            hyperparameter_tuning=hyperparameter_tuning,
            cross_validation_folds=5,
            test_size=0.2,
            random_state=42,
            feature_selection=False,
            auto_promotion=True,
            training_data_path=training_data_path,
            target_column=target_column,
            created_by=created_by
        )
    
    def schedule_retraining(
        self,
        model_id: str,
        data_path: str,
        frequency_days: int = 7,
        performance_threshold: float = 0.8
    ):
        """Schedule automated retraining (would integrate with task scheduler)"""
        
        # This would integrate with a task scheduler like Celery or Airflow
        # For now, we'll create a configuration that can be picked up by a scheduler
        
        schedule_config = {
            'model_id': model_id,
            'data_path': data_path,
            'frequency_days': frequency_days,
            'performance_threshold': performance_threshold,
            'last_training': datetime.now().isoformat(),
            'next_training': (datetime.now() + timedelta(days=frequency_days)).isoformat(),
            'enabled': True
        }
        
        schedule_file = self.config_path / f"schedule_{model_id}.json"
        with open(schedule_file, 'w') as f:
            json.dump(schedule_config, f, indent=2)
        
        logger.info(f"Scheduled retraining for {model_id} every {frequency_days} days")
        
        return schedule_config