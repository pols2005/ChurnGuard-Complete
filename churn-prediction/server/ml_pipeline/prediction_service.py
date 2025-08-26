# ChurnGuard Enhanced Prediction Service
# Epic 2 - Advanced ML Pipeline Implementation

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from .model_registry import ModelRegistry
from .ab_testing import ABTestingFramework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PredictionRequest:
    """Prediction request structure"""
    customer_id: str
    features: Dict[str, Any]
    model_id: Optional[str] = None
    ab_test_id: Optional[str] = None
    include_explanation: bool = False
    include_confidence: bool = True

@dataclass
class PredictionResponse:
    """Prediction response structure"""
    customer_id: str
    prediction: float
    confidence: Optional[float]
    model_used: str
    prediction_time: str
    response_time_ms: float
    explanation: Optional[str] = None
    feature_importance: Optional[Dict[str, float]] = None
    
class ModelCache:
    """Thread-safe model caching for performance"""
    
    def __init__(self, max_size: int = 10):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def get(self, model_key: str, loader_func):
        """Get model from cache or load it"""
        with self.lock:
            if model_key in self.cache:
                self.access_times[model_key] = time.time()
                return self.cache[model_key]
            
            # Load model
            model = loader_func(model_key)
            
            # Add to cache, evict oldest if necessary
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[model_key] = model
            self.access_times[model_key] = time.time()
            return model
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()

class EnhancedPredictionService:
    """Enhanced prediction service with caching, A/B testing, and monitoring"""
    
    def __init__(
        self, 
        registry: ModelRegistry,
        ab_testing: ABTestingFramework = None,
        cache_size: int = 10,
        max_workers: int = 4
    ):
        self.registry = registry
        self.ab_testing = ab_testing
        self.model_cache = ModelCache(cache_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Performance tracking
        self.prediction_stats = {
            'total_predictions': 0,
            'average_response_time': 0.0,
            'model_usage': {},
            'error_count': 0
        }
        self.stats_lock = threading.Lock()
    
    def _update_stats(self, model_key: str, response_time_ms: float, error: bool = False):
        """Update prediction statistics"""
        with self.stats_lock:
            self.prediction_stats['total_predictions'] += 1
            
            # Update average response time
            current_avg = self.prediction_stats['average_response_time']
            total = self.prediction_stats['total_predictions']
            self.prediction_stats['average_response_time'] = (
                (current_avg * (total - 1) + response_time_ms) / total
            )
            
            # Update model usage
            if model_key not in self.prediction_stats['model_usage']:
                self.prediction_stats['model_usage'][model_key] = 0
            self.prediction_stats['model_usage'][model_key] += 1
            
            # Update error count
            if error:
                self.prediction_stats['error_count'] += 1
    
    def _prepare_features(self, features: Dict[str, Any], model_metadata) -> np.ndarray:
        """Prepare features for model input"""
        feature_vector = []
        
        for feature_name in model_metadata.features:
            if feature_name in features:
                feature_vector.append(features[feature_name])
            else:
                # Handle missing features with defaults
                if 'Geography_' in feature_name:
                    feature_vector.append(0)  # One-hot encoded geography
                elif 'Gender_' in feature_name:
                    feature_vector.append(0)  # One-hot encoded gender
                else:
                    feature_vector.append(0)  # Default value
                    logger.warning(f"Missing feature {feature_name} for prediction")
        
        return np.array(feature_vector).reshape(1, -1)
    
    def _calculate_confidence(self, model, feature_vector: np.ndarray) -> float:
        """Calculate prediction confidence"""
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(feature_vector)[0]
            # Confidence is the maximum probability
            return float(np.max(probabilities))
        else:
            # For models without probability, use distance-based confidence
            if hasattr(model, 'decision_function'):
                decision = model.decision_function(feature_vector)[0]
                # Convert decision to confidence (0-1)
                confidence = 1.0 / (1.0 + np.exp(-abs(decision)))
                return float(confidence)
            else:
                return 0.5  # Default confidence for models without probability
    
    def _get_feature_importance(self, model, model_metadata) -> Dict[str, float]:
        """Get feature importance from model"""
        importance_dict = {}
        
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            for i, feature_name in enumerate(model_metadata.features):
                if i < len(importances):
                    importance_dict[feature_name] = float(importances[i])
        elif hasattr(model, 'coef_'):
            # For linear models, use coefficient magnitudes
            coefficients = np.abs(model.coef_[0])
            for i, feature_name in enumerate(model_metadata.features):
                if i < len(coefficients):
                    importance_dict[feature_name] = float(coefficients[i])
        
        # Normalize to sum to 1
        total_importance = sum(importance_dict.values())
        if total_importance > 0:
            importance_dict = {
                k: v / total_importance 
                for k, v in importance_dict.items()
            }
        
        return importance_dict
    
    def predict_single(self, request: PredictionRequest) -> PredictionResponse:
        """Make a single prediction"""
        start_time = time.time()
        
        try:
            # Determine which model to use
            model_key = None
            
            if request.ab_test_id and self.ab_testing:
                # Use A/B testing framework
                model_key, prediction, response_time_ms = self.ab_testing.route_prediction(
                    request.ab_test_id,
                    request.customer_id,
                    request.features
                )
                
                response = PredictionResponse(
                    customer_id=request.customer_id,
                    prediction=prediction,
                    confidence=None,
                    model_used=model_key,
                    prediction_time=datetime.now().isoformat(),
                    response_time_ms=response_time_ms
                )
                
                self._update_stats(model_key, response_time_ms)
                return response
            
            elif request.model_id:
                # Use specific model
                try:
                    model_key, model, metadata = self.registry.get_production_model(request.model_id)
                except ValueError:
                    # Fallback to any available model with this ID
                    models = self.registry.list_models(model_id=request.model_id)
                    if not models:
                        raise ValueError(f"No models found for model_id: {request.model_id}")
                    
                    latest_model = models[0]  # Most recent
                    model_key = f"{latest_model.model_id}_{latest_model.version}"
                    model = self.model_cache.get(model_key, self.registry.load_model)
                    metadata = latest_model
            
            else:
                # Use any production model (fallback)
                available_models = self.registry.list_models(status="production")
                if not available_models:
                    available_models = self.registry.list_models()
                
                if not available_models:
                    raise ValueError("No models available")
                
                metadata = available_models[0]
                model_key = f"{metadata.model_id}_{metadata.version}"
                model = self.model_cache.get(model_key, self.registry.load_model)
            
            # Prepare features
            feature_vector = self._prepare_features(request.features, metadata)
            
            # Make prediction
            if hasattr(model, 'predict_proba'):
                prediction = float(model.predict_proba(feature_vector)[0][1])
            else:
                prediction = float(model.predict(feature_vector)[0])
            
            # Calculate confidence if requested
            confidence = None
            if request.include_confidence:
                confidence = self._calculate_confidence(model, feature_vector)
            
            # Get feature importance if requested
            feature_importance = None
            if request.include_explanation:
                feature_importance = self._get_feature_importance(model, metadata)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            response = PredictionResponse(
                customer_id=request.customer_id,
                prediction=prediction,
                confidence=confidence,
                model_used=model_key,
                prediction_time=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                feature_importance=feature_importance
            )
            
            self._update_stats(model_key, response_time_ms)
            return response
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self._update_stats("error", response_time_ms, error=True)
            logger.error(f"Prediction error for customer {request.customer_id}: {str(e)}")
            raise
    
    def predict_batch(self, requests: List[PredictionRequest]) -> List[PredictionResponse]:
        """Make batch predictions using thread pool"""
        futures = []
        
        for request in requests:
            future = self.executor.submit(self.predict_single, request)
            futures.append(future)
        
        responses = []
        for future in as_completed(futures):
            try:
                response = future.result(timeout=30)  # 30 second timeout
                responses.append(response)
            except Exception as e:
                logger.error(f"Batch prediction error: {str(e)}")
                # Create error response
                error_response = PredictionResponse(
                    customer_id="unknown",
                    prediction=0.0,
                    confidence=None,
                    model_used="error",
                    prediction_time=datetime.now().isoformat(),
                    response_time_ms=0.0
                )
                responses.append(error_response)
        
        return responses
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prediction service statistics"""
        with self.stats_lock:
            return {
                'prediction_stats': self.prediction_stats.copy(),
                'cache_stats': {
                    'cached_models': len(self.model_cache.cache),
                    'cache_size': self.model_cache.max_size
                },
                'timestamp': datetime.now().isoformat()
            }
    
    def healthcheck(self) -> Dict[str, Any]:
        """Health check for the prediction service"""
        try:
            # Test if we can load models
            models = self.registry.list_models()
            if not models:
                return {
                    'status': 'unhealthy',
                    'reason': 'No models available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Test if we can make a dummy prediction
            test_features = {
                'CreditScore': 650,
                'Age': 35,
                'Tenure': 5,
                'Balance': 50000.0,
                'NumOfProducts': 2,
                'HasCrCard': 1,
                'IsActiveMember': 1,
                'EstimatedSalary': 75000.0,
                'Geography_France': 0,
                'Geography_Germany': 1,
                'Geography_Spain': 0,
                'Gender_Male': 1,
                'Gender_Female': 0
            }
            
            test_request = PredictionRequest(
                customer_id="healthcheck",
                features=test_features
            )
            
            start_time = time.time()
            response = self.predict_single(test_request)
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'test_prediction': response.prediction,
                'response_time_ms': response_time,
                'models_available': len(models),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def shutdown(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down prediction service...")
        self.executor.shutdown(wait=True)
        self.model_cache.clear()
        logger.info("Prediction service shutdown complete")