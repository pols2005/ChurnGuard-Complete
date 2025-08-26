# ChurnGuard ML Model Registry
# Epic 2 - Advanced ML Pipeline Implementation

import os
import json
import pickle
import hashlib
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

@dataclass
class ModelMetadata:
    """Model metadata for versioning and tracking"""
    model_id: str
    version: str
    model_type: str
    algorithm: str
    training_date: str
    performance_metrics: Dict[str, float]
    features: List[str]
    hyperparameters: Dict[str, Any]
    data_hash: str
    model_hash: str
    deployment_status: str  # 'development', 'staging', 'production', 'deprecated'
    created_by: str
    tags: List[str]

class ModelRegistry:
    """Centralized model registry for versioning and A/B testing"""
    
    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_path / "model_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load existing model metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                self.models = {k: ModelMetadata(**v) for k, v in data.items()}
        else:
            self.models = {}
    
    def _save_metadata(self):
        """Save model metadata to disk"""
        data = {k: asdict(v) for k, v in self.models.items()}
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _calculate_model_hash(self, model) -> str:
        """Calculate hash of model for change detection"""
        model_str = str(model.get_params() if hasattr(model, 'get_params') else str(model))
        return hashlib.md5(model_str.encode()).hexdigest()[:8]
    
    def _calculate_data_hash(self, X: pd.DataFrame, y: pd.Series) -> str:
        """Calculate hash of training data"""
        data_str = str(X.values.tobytes()) + str(y.values.tobytes())
        return hashlib.md5(data_str.encode()).hexdigest()[:8]
    
    def register_model(
        self,
        model,
        model_id: str,
        algorithm: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        features: List[str],
        hyperparameters: Dict[str, Any] = None,
        tags: List[str] = None,
        created_by: str = "system"
    ) -> str:
        """Register a new model version"""
        
        # Generate version number
        existing_versions = [m.version for m in self.models.values() if m.model_id == model_id]
        version = f"v{len(existing_versions) + 1:03d}"
        
        # Calculate performance metrics
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average='weighted')),
            'recall': float(recall_score(y_test, y_pred, average='weighted')),
            'f1_score': float(f1_score(y_test, y_pred, average='weighted'))
        }
        
        if y_pred_proba is not None:
            metrics['roc_auc'] = float(roc_auc_score(y_test, y_pred_proba))
        
        # Create model metadata
        model_key = f"{model_id}_{version}"
        metadata = ModelMetadata(
            model_id=model_id,
            version=version,
            model_type="classification",
            algorithm=algorithm,
            training_date=datetime.datetime.now().isoformat(),
            performance_metrics=metrics,
            features=features,
            hyperparameters=hyperparameters or {},
            data_hash=self._calculate_data_hash(X_test, y_test),
            model_hash=self._calculate_model_hash(model),
            deployment_status="development",
            created_by=created_by,
            tags=tags or []
        )
        
        # Save model file
        model_path = self.registry_path / f"{model_key}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Register metadata
        self.models[model_key] = metadata
        self._save_metadata()
        
        return model_key
    
    def load_model(self, model_key: str):
        """Load a specific model version"""
        model_path = self.registry_path / f"{model_key}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Model {model_key} not found")
        
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    
    def get_model_metadata(self, model_key: str) -> ModelMetadata:
        """Get metadata for a specific model"""
        if model_key not in self.models:
            raise KeyError(f"Model {model_key} not found in registry")
        return self.models[model_key]
    
    def list_models(self, model_id: str = None, status: str = None) -> List[ModelMetadata]:
        """List models with optional filtering"""
        models = list(self.models.values())
        
        if model_id:
            models = [m for m in models if m.model_id == model_id]
        
        if status:
            models = [m for m in models if m.deployment_status == status]
        
        return sorted(models, key=lambda x: x.training_date, reverse=True)
    
    def promote_model(self, model_key: str, target_status: str):
        """Promote model to different deployment status"""
        if model_key not in self.models:
            raise KeyError(f"Model {model_key} not found")
        
        # Demote existing models if promoting to production
        if target_status == "production":
            for key, model in self.models.items():
                if (model.model_id == self.models[model_key].model_id and 
                    model.deployment_status == "production"):
                    model.deployment_status = "staging"
        
        self.models[model_key].deployment_status = target_status
        self._save_metadata()
    
    def get_production_model(self, model_id: str):
        """Get current production model for given model_id"""
        production_models = [
            (key, model) for key, model in self.models.items()
            if model.model_id == model_id and model.deployment_status == "production"
        ]
        
        if not production_models:
            raise ValueError(f"No production model found for {model_id}")
        
        if len(production_models) > 1:
            # Return most recent if multiple production models
            production_models.sort(key=lambda x: x[1].training_date, reverse=True)
        
        model_key, metadata = production_models[0]
        return model_key, self.load_model(model_key), metadata
    
    def compare_models(self, model_keys: List[str]) -> pd.DataFrame:
        """Compare performance metrics of multiple models"""
        comparison_data = []
        
        for key in model_keys:
            if key not in self.models:
                continue
            
            model = self.models[key]
            row = {
                'model_key': key,
                'model_id': model.model_id,
                'version': model.version,
                'algorithm': model.algorithm,
                'training_date': model.training_date,
                'deployment_status': model.deployment_status,
                **model.performance_metrics
            }
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)