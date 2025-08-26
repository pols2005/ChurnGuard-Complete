# ChurnGuard ML Model Performance Monitoring
# Epic 2 - Advanced ML Pipeline Implementation

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import threading
from collections import defaultdict, deque

from .model_registry import ModelRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric tracking"""
    timestamp: str
    model_key: str
    metric_name: str
    metric_value: float
    customer_id: str
    prediction: float
    actual_outcome: Optional[int]
    response_time_ms: float
    features: Dict[str, Any]

@dataclass
class DriftAlert:
    """Model drift alert"""
    alert_id: str
    timestamp: str
    model_key: str
    drift_type: str  # 'data_drift', 'concept_drift', 'performance_drift'
    severity: str  # 'low', 'medium', 'high', 'critical'
    metric_name: str
    current_value: float
    baseline_value: float
    threshold: float
    description: str
    recommended_action: str

class ModelPerformanceMonitor:
    """Real-time model performance monitoring and alerting"""
    
    def __init__(
        self, 
        registry: ModelRegistry,
        monitoring_path: str = "models/monitoring",
        window_size: int = 1000,
        alert_thresholds: Dict[str, float] = None
    ):
        self.registry = registry
        self.monitoring_path = Path(monitoring_path)
        self.monitoring_path.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.metrics = deque(maxlen=window_size)
        self.baseline_metrics = {}
        self.current_stats = defaultdict(lambda: defaultdict(list))
        
        # Alert configuration
        self.alert_thresholds = alert_thresholds or {
            'accuracy_drop': 0.05,
            'prediction_drift': 0.1,
            'response_time_increase': 2.0,
            'error_rate_increase': 0.02
        }
        
        self.alerts = []
        self.lock = threading.RLock()
        
        # Load existing data
        self._load_monitoring_data()
    
    def _load_monitoring_data(self):
        """Load existing monitoring data"""
        metrics_file = self.monitoring_path / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                data = json.load(f)
                self.metrics.extend([PerformanceMetric(**item) for item in data[-1000:]])
        
        baseline_file = self.monitoring_path / "baselines.json"
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                self.baseline_metrics = json.load(f)
        
        alerts_file = self.monitoring_path / "alerts.json"
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                data = json.load(f)
                self.alerts = [DriftAlert(**item) for item in data]
    
    def _save_monitoring_data(self):
        """Save monitoring data to disk"""
        # Save metrics
        metrics_file = self.monitoring_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            data = [asdict(metric) for metric in self.metrics]
            json.dump(data, f, indent=2)
        
        # Save baselines
        baseline_file = self.monitoring_path / "baselines.json"
        with open(baseline_file, 'w') as f:
            json.dump(self.baseline_metrics, f, indent=2)
        
        # Save alerts
        alerts_file = self.monitoring_path / "alerts.json"
        with open(alerts_file, 'w') as f:
            data = [asdict(alert) for alert in self.alerts[-100:]]  # Keep last 100 alerts
            json.dump(data, f, indent=2)
    
    def record_prediction(
        self,
        model_key: str,
        customer_id: str,
        prediction: float,
        response_time_ms: float,
        features: Dict[str, Any],
        actual_outcome: Optional[int] = None
    ):
        """Record a prediction for monitoring"""
        with self.lock:
            metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                model_key=model_key,
                metric_name="prediction",
                metric_value=prediction,
                customer_id=customer_id,
                prediction=prediction,
                actual_outcome=actual_outcome,
                response_time_ms=response_time_ms,
                features=features
            )
            
            self.metrics.append(metric)
            
            # Update current stats
            self.current_stats[model_key]['predictions'].append(prediction)
            self.current_stats[model_key]['response_times'].append(response_time_ms)
            
            if actual_outcome is not None:
                self.current_stats[model_key]['actual_outcomes'].append(actual_outcome)
            
            # Check for drift
            self._check_drift(model_key)
            
            # Periodically save data
            if len(self.metrics) % 100 == 0:
                self._save_monitoring_data()
    
    def update_actual_outcome(self, customer_id: str, actual_outcome: int):
        """Update actual outcome for a previous prediction"""
        with self.lock:
            for metric in reversed(self.metrics):
                if (metric.customer_id == customer_id and 
                    metric.actual_outcome is None):
                    metric.actual_outcome = actual_outcome
                    
                    # Update current stats
                    self.current_stats[metric.model_key]['actual_outcomes'].append(actual_outcome)
                    
                    # Re-check drift with new outcome data
                    self._check_drift(metric.model_key)
                    break
    
    def _calculate_baseline_metrics(self, model_key: str):
        """Calculate baseline metrics for a model"""
        model_metrics = [m for m in self.metrics if m.model_key == model_key]
        
        if len(model_metrics) < 50:  # Need minimum samples
            return
        
        # Use first 50% of data as baseline
        baseline_size = len(model_metrics) // 2
        baseline_data = model_metrics[:baseline_size]
        
        predictions = [m.prediction for m in baseline_data]
        response_times = [m.response_time_ms for m in baseline_data]
        
        # Calculate baseline statistics
        baseline = {
            'prediction_mean': np.mean(predictions),
            'prediction_std': np.std(predictions),
            'response_time_mean': np.mean(response_times),
            'response_time_std': np.std(response_times),
            'sample_size': len(baseline_data)
        }
        
        # Calculate accuracy if we have outcomes
        outcomes = [m.actual_outcome for m in baseline_data if m.actual_outcome is not None]
        predictions_with_outcomes = [m.prediction for m in baseline_data if m.actual_outcome is not None]
        
        if len(outcomes) >= 20:
            binary_preds = [1 if p > 0.5 else 0 for p in predictions_with_outcomes]
            accuracy = sum(1 for p, a in zip(binary_preds, outcomes) if p == a) / len(outcomes)
            baseline['accuracy'] = accuracy
        
        self.baseline_metrics[model_key] = baseline
        logger.info(f"Updated baseline metrics for {model_key}")
    
    def _check_drift(self, model_key: str):
        """Check for various types of drift"""
        if model_key not in self.baseline_metrics:
            self._calculate_baseline_metrics(model_key)
            return
        
        recent_metrics = [m for m in list(self.metrics)[-100:] if m.model_key == model_key]
        if len(recent_metrics) < 20:
            return
        
        baseline = self.baseline_metrics[model_key]
        
        # Check prediction drift
        recent_predictions = [m.prediction for m in recent_metrics]
        self._check_prediction_drift(model_key, recent_predictions, baseline)
        
        # Check performance drift
        recent_with_outcomes = [m for m in recent_metrics if m.actual_outcome is not None]
        if len(recent_with_outcomes) >= 20:
            self._check_performance_drift(model_key, recent_with_outcomes, baseline)
        
        # Check response time drift
        recent_response_times = [m.response_time_ms for m in recent_metrics]
        self._check_response_time_drift(model_key, recent_response_times, baseline)
    
    def _check_prediction_drift(self, model_key: str, recent_predictions: List[float], baseline: Dict):
        """Check for drift in prediction distribution"""
        if 'prediction_mean' not in baseline:
            return
        
        recent_mean = np.mean(recent_predictions)
        recent_std = np.std(recent_predictions)
        
        # Statistical test for mean shift
        baseline_mean = baseline['prediction_mean']
        baseline_std = baseline['prediction_std']
        
        # Z-test for mean difference
        pooled_std = np.sqrt((baseline_std**2 + recent_std**2) / 2)
        if pooled_std > 0:
            z_score = abs(recent_mean - baseline_mean) / (pooled_std / np.sqrt(len(recent_predictions)))
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
            
            if p_value < 0.05:  # Significant drift
                drift_magnitude = abs(recent_mean - baseline_mean)
                
                if drift_magnitude > self.alert_thresholds['prediction_drift']:
                    severity = 'high' if drift_magnitude > 0.2 else 'medium'
                    
                    alert = DriftAlert(
                        alert_id=f"pred_drift_{model_key}_{int(time.time())}",
                        timestamp=datetime.now().isoformat(),
                        model_key=model_key,
                        drift_type='data_drift',
                        severity=severity,
                        metric_name='prediction_mean',
                        current_value=recent_mean,
                        baseline_value=baseline_mean,
                        threshold=self.alert_thresholds['prediction_drift'],
                        description=f"Significant shift in prediction distribution detected (p={p_value:.4f})",
                        recommended_action="Review input data quality and consider model retraining"
                    )
                    
                    self._create_alert(alert)
    
    def _check_performance_drift(self, model_key: str, recent_with_outcomes: List[PerformanceMetric], baseline: Dict):
        """Check for drift in model performance"""
        if 'accuracy' not in baseline:
            return
        
        predictions = [m.prediction for m in recent_with_outcomes]
        outcomes = [m.actual_outcome for m in recent_with_outcomes]
        
        # Calculate current accuracy
        binary_preds = [1 if p > 0.5 else 0 for p in predictions]
        current_accuracy = sum(1 for p, a in zip(binary_preds, outcomes) if p == a) / len(outcomes)
        
        baseline_accuracy = baseline['accuracy']
        accuracy_drop = baseline_accuracy - current_accuracy
        
        if accuracy_drop > self.alert_thresholds['accuracy_drop']:
            severity = 'critical' if accuracy_drop > 0.1 else 'high'
            
            alert = DriftAlert(
                alert_id=f"perf_drift_{model_key}_{int(time.time())}",
                timestamp=datetime.now().isoformat(),
                model_key=model_key,
                drift_type='concept_drift',
                severity=severity,
                metric_name='accuracy',
                current_value=current_accuracy,
                baseline_value=baseline_accuracy,
                threshold=self.alert_thresholds['accuracy_drop'],
                description=f"Model accuracy dropped by {accuracy_drop:.3f}",
                recommended_action="Urgent model retraining required"
            )
            
            self._create_alert(alert)
    
    def _check_response_time_drift(self, model_key: str, recent_response_times: List[float], baseline: Dict):
        """Check for drift in response times"""
        if 'response_time_mean' not in baseline:
            return
        
        current_mean_time = np.mean(recent_response_times)
        baseline_mean_time = baseline['response_time_mean']
        
        time_increase_ratio = current_mean_time / baseline_mean_time
        
        if time_increase_ratio > self.alert_thresholds['response_time_increase']:
            severity = 'high' if time_increase_ratio > 3.0 else 'medium'
            
            alert = DriftAlert(
                alert_id=f"time_drift_{model_key}_{int(time.time())}",
                timestamp=datetime.now().isoformat(),
                model_key=model_key,
                drift_type='performance_drift',
                severity=severity,
                metric_name='response_time',
                current_value=current_mean_time,
                baseline_value=baseline_mean_time,
                threshold=self.alert_thresholds['response_time_increase'],
                description=f"Response time increased by {(time_increase_ratio-1)*100:.1f}%",
                recommended_action="Check system resources and model complexity"
            )
            
            self._create_alert(alert)
    
    def _create_alert(self, alert: DriftAlert):
        """Create and log an alert"""
        with self.lock:
            # Check for duplicate alerts (same type within last hour)
            recent_alerts = [
                a for a in self.alerts 
                if (a.model_key == alert.model_key and 
                    a.drift_type == alert.drift_type and
                    datetime.fromisoformat(a.timestamp) > datetime.now() - timedelta(hours=1))
            ]
            
            if not recent_alerts:  # Only create if no recent similar alert
                self.alerts.append(alert)
                logger.warning(f"DRIFT ALERT: {alert.description} for model {alert.model_key}")
                
                # Save alerts immediately
                self._save_monitoring_data()
    
    def get_model_health(self, model_key: str) -> Dict[str, Any]:
        """Get health status for a specific model"""
        with self.lock:
            model_metrics = [m for m in self.metrics if m.model_key == model_key]
            
            if not model_metrics:
                return {'error': 'No metrics found for this model'}
            
            # Recent metrics (last 100 predictions)
            recent_metrics = model_metrics[-100:]
            
            health_status = {
                'model_key': model_key,
                'total_predictions': len(model_metrics),
                'recent_predictions': len(recent_metrics),
                'avg_response_time': np.mean([m.response_time_ms for m in recent_metrics]),
                'prediction_stats': {
                    'mean': np.mean([m.prediction for m in recent_metrics]),
                    'std': np.std([m.prediction for m in recent_metrics]),
                    'min': np.min([m.prediction for m in recent_metrics]),
                    'max': np.max([m.prediction for m in recent_metrics])
                }
            }
            
            # Calculate accuracy if we have outcomes
            recent_with_outcomes = [m for m in recent_metrics if m.actual_outcome is not None]
            if recent_with_outcomes:
                predictions = [m.prediction for m in recent_with_outcomes]
                outcomes = [m.actual_outcome for m in recent_with_outcomes]
                binary_preds = [1 if p > 0.5 else 0 for p in predictions]
                accuracy = sum(1 for p, a in zip(binary_preds, outcomes) if p == a) / len(outcomes)
                health_status['accuracy'] = accuracy
                health_status['samples_with_outcomes'] = len(recent_with_outcomes)
            
            # Recent alerts
            recent_alerts = [
                a for a in self.alerts 
                if (a.model_key == model_key and
                    datetime.fromisoformat(a.timestamp) > datetime.now() - timedelta(days=7))
            ]
            health_status['recent_alerts'] = len(recent_alerts)
            health_status['alert_severity'] = max([a.severity for a in recent_alerts], default='none')
            
            # Health score (0-1)
            health_score = 1.0
            
            # Penalize for alerts
            if recent_alerts:
                severity_penalties = {'low': 0.05, 'medium': 0.1, 'high': 0.2, 'critical': 0.4}
                max_penalty = max([severity_penalties.get(a.severity, 0) for a in recent_alerts])
                health_score -= max_penalty
            
            # Penalize for slow response times
            if health_status['avg_response_time'] > 1000:  # >1 second
                health_score -= 0.1
            
            # Penalize for low accuracy
            if 'accuracy' in health_status and health_status['accuracy'] < 0.7:
                health_score -= 0.2
            
            health_status['health_score'] = max(0.0, health_score)
            health_status['status'] = 'healthy' if health_score > 0.8 else 'warning' if health_score > 0.6 else 'unhealthy'
            
            return health_status
    
    def get_alerts(self, severity: str = None, hours: int = 24) -> List[DriftAlert]:
        """Get recent alerts with optional filtering"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a.timestamp) > cutoff_time
        ]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        with self.lock:
            summary = {
                'total_predictions': len(self.metrics),
                'models_monitored': len(set(m.model_key for m in self.metrics)),
                'active_alerts': len(self.get_alerts(hours=24)),
                'critical_alerts': len(self.get_alerts(severity='critical', hours=24)),
                'monitoring_window_hours': 24,
                'timestamp': datetime.now().isoformat()
            }
            
            # Model health summary
            model_keys = list(set(m.model_key for m in self.metrics))
            summary['model_health'] = {}
            
            for model_key in model_keys:
                health = self.get_model_health(model_key)
                summary['model_health'][model_key] = {
                    'status': health.get('status', 'unknown'),
                    'health_score': health.get('health_score', 0.0),
                    'recent_predictions': health.get('recent_predictions', 0),
                    'accuracy': health.get('accuracy')
                }
            
            return summary