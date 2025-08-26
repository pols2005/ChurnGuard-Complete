# ChurnGuard A/B Testing Framework
# Epic 2 - Advanced ML Pipeline Implementation

import random
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from .model_registry import ModelRegistry

@dataclass
class ABTestConfig:
    """Configuration for A/B test"""
    test_id: str
    test_name: str
    model_a: str  # model_key
    model_b: str  # model_key
    traffic_split: float  # 0.0 to 1.0, percentage to model_b
    start_date: str
    end_date: str
    success_metric: str  # 'accuracy', 'precision', 'recall', 'f1', 'roc_auc'
    minimum_sample_size: int
    significance_level: float
    status: str  # 'running', 'completed', 'stopped'
    created_by: str
    description: str

@dataclass
class ABTestResult:
    """Individual A/B test prediction result"""
    test_id: str
    timestamp: str
    customer_id: str
    model_used: str
    prediction: float
    actual_outcome: Optional[int]
    response_time_ms: float
    features: Dict[str, Any]

class ABTestingFramework:
    """A/B testing framework for model comparison"""
    
    def __init__(self, registry: ModelRegistry, results_path: str = "models/ab_tests"):
        self.registry = registry
        self.results_path = Path(results_path)
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.config_file = self.results_path / "ab_configs.json"
        self.results_file = self.results_path / "ab_results.json"
        self._load_configs()
        self._load_results()
    
    def _load_configs(self):
        """Load existing A/B test configurations"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.configs = {k: ABTestConfig(**v) for k, v in data.items()}
        else:
            self.configs = {}
    
    def _save_configs(self):
        """Save A/B test configurations"""
        data = {k: asdict(v) for k, v in self.configs.items()}
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_results(self):
        """Load existing A/B test results"""
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                self.results = [ABTestResult(**item) for item in data]
        else:
            self.results = []
    
    def _save_results(self):
        """Save A/B test results"""
        data = [asdict(result) for result in self.results]
        with open(self.results_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_ab_test(
        self,
        test_name: str,
        model_a: str,
        model_b: str,
        traffic_split: float = 0.5,
        duration_days: int = 30,
        success_metric: str = "accuracy",
        minimum_sample_size: int = 1000,
        significance_level: float = 0.05,
        description: str = "",
        created_by: str = "system"
    ) -> str:
        """Create a new A/B test"""
        
        # Validate models exist
        if model_a not in self.registry.models:
            raise ValueError(f"Model A {model_a} not found in registry")
        if model_b not in self.registry.models:
            raise ValueError(f"Model B {model_b} not found in registry")
        
        # Generate test ID
        test_id = hashlib.md5(f"{test_name}_{datetime.now()}".encode()).hexdigest()[:8]
        
        # Create configuration
        config = ABTestConfig(
            test_id=test_id,
            test_name=test_name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split,
            start_date=datetime.now().isoformat(),
            end_date=(datetime.now() + timedelta(days=duration_days)).isoformat(),
            success_metric=success_metric,
            minimum_sample_size=minimum_sample_size,
            significance_level=significance_level,
            status="running",
            created_by=created_by,
            description=description
        )
        
        self.configs[test_id] = config
        self._save_configs()
        
        return test_id
    
    def _hash_customer_id(self, customer_id: str, test_id: str) -> float:
        """Generate consistent hash for customer ID"""
        hash_input = f"{customer_id}_{test_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        return (hash_value % 10000) / 10000.0
    
    def route_prediction(
        self,
        test_id: str,
        customer_id: str,
        features: Dict[str, Any]
    ) -> Tuple[str, Any, float]:
        """Route prediction request through A/B test"""
        
        if test_id not in self.configs:
            raise ValueError(f"A/B test {test_id} not found")
        
        config = self.configs[test_id]
        
        # Check if test is running
        if config.status != "running":
            raise ValueError(f"A/B test {test_id} is not running")
        
        current_time = datetime.now()
        start_time = datetime.fromisoformat(config.start_date)
        end_time = datetime.fromisoformat(config.end_date)
        
        if current_time < start_time or current_time > end_time:
            raise ValueError(f"A/B test {test_id} is not active")
        
        # Determine which model to use based on consistent hashing
        customer_hash = self._hash_customer_id(customer_id, test_id)
        use_model_b = customer_hash < config.traffic_split
        
        model_key = config.model_b if use_model_b else config.model_a
        
        # Load model and make prediction
        start_time = datetime.now()
        model = self.registry.load_model(model_key)
        
        # Convert features to model input format
        feature_values = [features[f] for f in self.registry.models[model_key].features]
        prediction = model.predict_proba([feature_values])[0][1]  # Probability of churn
        
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log result for analysis
        result = ABTestResult(
            test_id=test_id,
            timestamp=datetime.now().isoformat(),
            customer_id=customer_id,
            model_used=model_key,
            prediction=float(prediction),
            actual_outcome=None,  # Will be updated later
            response_time_ms=response_time_ms,
            features=features
        )
        
        self.results.append(result)
        self._save_results()
        
        return model_key, prediction, response_time_ms
    
    def update_outcome(self, customer_id: str, test_id: str, actual_outcome: int):
        """Update actual outcome for A/B test result"""
        for result in self.results:
            if (result.customer_id == customer_id and 
                result.test_id == test_id and 
                result.actual_outcome is None):
                result.actual_outcome = actual_outcome
                break
        
        self._save_results()
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results"""
        
        if test_id not in self.configs:
            raise ValueError(f"A/B test {test_id} not found")
        
        config = self.configs[test_id]
        test_results = [r for r in self.results if r.test_id == test_id]
        
        if not test_results:
            return {"error": "No results found for this test"}
        
        # Split results by model
        model_a_results = [r for r in test_results if r.model_used == config.model_a]
        model_b_results = [r for r in test_results if r.model_used == config.model_b]
        
        # Calculate basic statistics
        total_samples = len(test_results)
        model_a_samples = len(model_a_results)
        model_b_samples = len(model_b_results)
        
        # Calculate performance metrics for samples with actual outcomes
        model_a_with_outcomes = [r for r in model_a_results if r.actual_outcome is not None]
        model_b_with_outcomes = [r for r in model_b_results if r.actual_outcome is not None]
        
        def calculate_metrics(results_with_outcomes):
            if not results_with_outcomes:
                return {}
            
            predictions = [r.prediction for r in results_with_outcomes]
            actuals = [r.actual_outcome for r in results_with_outcomes]
            
            # Convert predictions to binary (threshold = 0.5)
            binary_preds = [1 if p > 0.5 else 0 for p in predictions]
            
            # Calculate metrics
            tp = sum(1 for p, a in zip(binary_preds, actuals) if p == 1 and a == 1)
            tn = sum(1 for p, a in zip(binary_preds, actuals) if p == 0 and a == 0)
            fp = sum(1 for p, a in zip(binary_preds, actuals) if p == 1 and a == 0)
            fn = sum(1 for p, a in zip(binary_preds, actuals) if p == 0 and a == 1)
            
            accuracy = (tp + tn) / len(results_with_outcomes) if results_with_outcomes else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            avg_response_time = np.mean([r.response_time_ms for r in results_with_outcomes])
            
            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'avg_response_time_ms': avg_response_time,
                'sample_size': len(results_with_outcomes)
            }
        
        model_a_metrics = calculate_metrics(model_a_with_outcomes)
        model_b_metrics = calculate_metrics(model_b_with_outcomes)
        
        # Statistical significance test
        significance_result = None
        if (len(model_a_with_outcomes) >= 30 and len(model_b_with_outcomes) >= 30):
            metric_key = config.success_metric
            if metric_key in model_a_metrics and metric_key in model_b_metrics:
                a_values = [getattr(r, 'prediction', 0) for r in model_a_with_outcomes]
                b_values = [getattr(r, 'prediction', 0) for r in model_b_with_outcomes]
                
                # Perform t-test
                t_stat, p_value = stats.ttest_ind(a_values, b_values)
                
                significance_result = {
                    'test_statistic': t_stat,
                    'p_value': p_value,
                    'is_significant': p_value < config.significance_level,
                    'significance_level': config.significance_level
                }
        
        # Recommendation
        recommendation = "inconclusive"
        if model_a_metrics and model_b_metrics:
            metric_key = config.success_metric
            if metric_key in model_a_metrics and metric_key in model_b_metrics:
                if model_b_metrics[metric_key] > model_a_metrics[metric_key]:
                    recommendation = "use_model_b"
                elif model_a_metrics[metric_key] > model_b_metrics[metric_key]:
                    recommendation = "use_model_a"
                else:
                    recommendation = "no_difference"
        
        return {
            'test_config': asdict(config),
            'total_samples': total_samples,
            'model_a_samples': model_a_samples,
            'model_b_samples': model_b_samples,
            'model_a_metrics': model_a_metrics,
            'model_b_metrics': model_b_metrics,
            'statistical_significance': significance_result,
            'recommendation': recommendation,
            'analysis_date': datetime.now().isoformat()
        }
    
    def stop_test(self, test_id: str):
        """Stop a running A/B test"""
        if test_id not in self.configs:
            raise ValueError(f"A/B test {test_id} not found")
        
        self.configs[test_id].status = "stopped"
        self._save_configs()
    
    def list_tests(self, status: str = None) -> List[ABTestConfig]:
        """List A/B tests with optional status filtering"""
        configs = list(self.configs.values())
        
        if status:
            configs = [c for c in configs if c.status == status]
        
        return sorted(configs, key=lambda x: x.start_date, reverse=True)