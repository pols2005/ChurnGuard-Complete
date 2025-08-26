# ChurnGuard Advanced Anomaly Detection System
# Epic 4 - Advanced Analytics & AI Insights

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import threading
import time
from abc import ABC, abstractmethod

from .statistical_analysis import get_stats_service
from .time_series_db import get_time_series_db, TimeSeriesPoint
from .real_time_engine import get_analytics_engine, AlertSeverity

logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    POINT_ANOMALY = "point_anomaly"        # Single unusual data point
    CONTEXTUAL_ANOMALY = "contextual_anomaly"  # Unusual in specific context
    COLLECTIVE_ANOMALY = "collective_anomaly"  # Group of points together unusual
    TREND_ANOMALY = "trend_anomaly"        # Unusual trend or pattern change
    SEASONAL_ANOMALY = "seasonal_anomaly"   # Deviation from seasonal pattern

class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class DetectionMethod(Enum):
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    ENSEMBLE = "ensemble"
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    ONE_CLASS_SVM = "one_class_svm"

@dataclass
class Anomaly:
    """Detected anomaly with detailed information"""
    id: str
    timestamp: datetime
    metric_name: str
    organization_id: str
    value: float
    expected_value: float
    deviation_score: float
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    method: DetectionMethod
    confidence: float
    context: Dict[str, Any]
    explanation: str
    recommendations: List[str]
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass  
class DetectionRule:
    """Rule for anomaly detection"""
    id: str
    metric_name: str
    organization_id: str
    method: DetectionMethod
    parameters: Dict[str, Any]
    enabled: bool = True
    sensitivity: float = 1.0
    min_data_points: int = 10
    window_hours: int = 24

class AnomalyDetector(ABC):
    """Abstract base class for anomaly detectors"""
    
    @abstractmethod
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in the provided data"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get detector name"""
        pass

class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical anomaly detector using Z-score and IQR methods"""
    
    def __init__(self):
        self.stats_service = get_stats_service()
    
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect statistical anomalies"""
        if data.empty or len(data) < 3:
            return []
        
        values = data['value'].tolist()
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        
        method = parameters.get('method', 'zscore')
        sensitivity = parameters.get('sensitivity', 2.0)
        
        anomaly_result = self.stats_service.anomaly_detection(
            values, method=method, sensitivity=sensitivity
        )
        
        anomalies = []
        for anomaly in anomaly_result.anomalies:
            anomalies.append({
                'index': anomaly['index'],
                'timestamp': timestamps[anomaly['index']],
                'value': anomaly['value'],
                'expected': anomaly.get('expected', np.mean(values)),
                'score': anomaly.get('z_score', 0),
                'method': method,
                'type': AnomalyType.POINT_ANOMALY
            })
        
        return anomalies
    
    def get_name(self) -> str:
        return "Statistical Detector"

class IsolationForestDetector(AnomalyDetector):
    """Isolation Forest anomaly detector"""
    
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using Isolation Forest"""
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            logger.warning("sklearn not available, skipping Isolation Forest detection")
            return []
        
        if data.empty or len(data) < 10:
            return []
        
        # Prepare features (value and time-based features)
        df = data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        features = df[['value', 'hour', 'day_of_week']].values
        
        # Configure Isolation Forest
        contamination = parameters.get('contamination', 0.1)
        random_state = parameters.get('random_state', 42)
        
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        
        # Fit and predict
        predictions = iso_forest.fit_predict(features)
        anomaly_scores = iso_forest.score_samples(features)
        
        anomalies = []
        for i, (prediction, score) in enumerate(zip(predictions, anomaly_scores)):
            if prediction == -1:  # Anomaly
                anomalies.append({
                    'index': i,
                    'timestamp': df.iloc[i]['timestamp'],
                    'value': df.iloc[i]['value'],
                    'expected': np.mean(df['value']),
                    'score': abs(score),
                    'method': 'isolation_forest',
                    'type': AnomalyType.POINT_ANOMALY
                })
        
        return anomalies
    
    def get_name(self) -> str:
        return "Isolation Forest Detector"

class LocalOutlierFactorDetector(AnomalyDetector):
    """Local Outlier Factor anomaly detector"""
    
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using Local Outlier Factor"""
        try:
            from sklearn.neighbors import LocalOutlierFactor
        except ImportError:
            logger.warning("sklearn not available, skipping LOF detection")
            return []
        
        if data.empty or len(data) < 20:
            return []
        
        # Prepare features
        df = data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        features = df[['value', 'hour', 'day_of_week']].values
        
        # Configure LOF
        n_neighbors = min(parameters.get('n_neighbors', 20), len(data) - 1)
        contamination = parameters.get('contamination', 0.1)
        
        lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination
        )
        
        # Fit and predict
        predictions = lof.fit_predict(features)
        outlier_factors = lof.negative_outlier_factor_
        
        anomalies = []
        for i, (prediction, factor) in enumerate(zip(predictions, outlier_factors)):
            if prediction == -1:  # Anomaly
                anomalies.append({
                    'index': i,
                    'timestamp': df.iloc[i]['timestamp'],
                    'value': df.iloc[i]['value'],
                    'expected': np.mean(df['value']),
                    'score': abs(factor),
                    'method': 'local_outlier_factor',
                    'type': AnomalyType.CONTEXTUAL_ANOMALY
                })
        
        return anomalies
    
    def get_name(self) -> str:
        return "Local Outlier Factor Detector"

class TrendAnomalyDetector(AnomalyDetector):
    """Detector for trend-based anomalies"""
    
    def __init__(self):
        self.stats_service = get_stats_service()
    
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect trend anomalies"""
        if data.empty or len(data) < 10:
            return []
        
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        values = data['value'].tolist()
        
        # Analyze overall trend
        trend_analysis = self.stats_service.trend_analysis(timestamps, values)
        
        anomalies = []
        
        # Detect trend change points using sliding windows
        window_size = min(parameters.get('window_size', 7), len(values) // 3)
        min_trend_change = parameters.get('min_trend_change', 0.1)
        
        for i in range(window_size, len(values) - window_size):
            # Compare trends before and after this point
            before_values = values[i-window_size:i]
            after_values = values[i:i+window_size]
            before_timestamps = timestamps[i-window_size:i]
            after_timestamps = timestamps[i:i+window_size]
            
            before_trend = self.stats_service.trend_analysis(before_timestamps, before_values)
            after_trend = self.stats_service.trend_analysis(after_timestamps, after_values)
            
            # Check for significant trend change
            trend_change = abs(after_trend.slope - before_trend.slope)
            
            if trend_change > min_trend_change and before_trend.p_value < 0.1 and after_trend.p_value < 0.1:
                anomalies.append({
                    'index': i,
                    'timestamp': timestamps[i],
                    'value': values[i],
                    'expected': before_trend.slope * i + values[0],  # Extrapolated from before trend
                    'score': trend_change,
                    'method': 'trend_change_detection',
                    'type': AnomalyType.TREND_ANOMALY,
                    'metadata': {
                        'before_slope': before_trend.slope,
                        'after_slope': after_trend.slope,
                        'trend_change': trend_change
                    }
                })
        
        return anomalies
    
    def get_name(self) -> str:
        return "Trend Anomaly Detector"

class SeasonalAnomalyDetector(AnomalyDetector):
    """Detector for seasonal anomalies"""
    
    def __init__(self):
        self.stats_service = get_stats_service()
    
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect seasonal anomalies"""
        if data.empty or len(data) < 24:  # Need minimum data for seasonality
            return []
        
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        values = data['value'].tolist()
        
        # Analyze seasonality
        seasonality_analysis = self.stats_service.seasonality_analysis(timestamps, values)
        
        if seasonality_analysis.seasonal_strength < 0.3:
            return []  # Not enough seasonality to detect anomalies
        
        anomalies = []
        period = seasonality_analysis.period
        seasonal_components = seasonality_analysis.seasonal_components
        
        if not seasonal_components or period == 0:
            return []
        
        # Detect deviations from seasonal pattern
        threshold = parameters.get('seasonal_threshold', 2.0)
        
        for i, value in enumerate(values):
            if i < period:
                continue
                
            # Get expected seasonal value
            season_index = i % period
            if season_index < len(seasonal_components):
                expected_seasonal = seasonal_components[season_index]
                
                # Calculate residual after removing seasonality
                residual = value - expected_seasonal
                
                # Check if residual is anomalous compared to other residuals
                residuals = [values[j] - seasonal_components[j % period] 
                           for j in range(period, i)]
                
                if residuals:
                    residual_std = np.std(residuals)
                    residual_mean = np.mean(residuals)
                    
                    if residual_std > 0:
                        z_score = abs(residual - residual_mean) / residual_std
                        
                        if z_score > threshold:
                            anomalies.append({
                                'index': i,
                                'timestamp': timestamps[i],
                                'value': value,
                                'expected': expected_seasonal + residual_mean,
                                'score': z_score,
                                'method': 'seasonal_deviation',
                                'type': AnomalyType.SEASONAL_ANOMALY,
                                'metadata': {
                                    'seasonal_component': expected_seasonal,
                                    'residual': residual,
                                    'season_index': season_index
                                }
                            })
        
        return anomalies
    
    def get_name(self) -> str:
        return "Seasonal Anomaly Detector"

class EnsembleAnomalyDetector(AnomalyDetector):
    """Ensemble detector combining multiple detection methods"""
    
    def __init__(self):
        self.detectors = [
            StatisticalAnomalyDetector(),
            IsolationForestDetector(),
            LocalOutlierFactorDetector(),
            TrendAnomalyDetector(),
            SeasonalAnomalyDetector()
        ]
    
    def detect(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using ensemble approach"""
        if data.empty:
            return []
        
        all_anomalies = []
        voting_threshold = parameters.get('voting_threshold', 2)  # Minimum detectors that must agree
        
        # Run each detector
        detector_results = {}
        for detector in self.detectors:
            try:
                detector_anomalies = detector.detect(data, parameters)
                detector_results[detector.get_name()] = detector_anomalies
            except Exception as e:
                logger.error(f"Error in {detector.get_name()}: {e}")
                detector_results[detector.get_name()] = []
        
        # Combine results using voting
        timestamp_to_anomalies = defaultdict(list)
        
        for detector_name, anomalies in detector_results.items():
            for anomaly in anomalies:
                timestamp_key = anomaly['timestamp'].replace(second=0, microsecond=0)
                timestamp_to_anomalies[timestamp_key].append({
                    'detector': detector_name,
                    'anomaly': anomaly
                })
        
        # Find consensus anomalies
        for timestamp, detector_anomalies in timestamp_to_anomalies.items():
            if len(detector_anomalies) >= voting_threshold:
                # Combine information from multiple detectors
                combined_anomaly = self._combine_detector_results(detector_anomalies)
                all_anomalies.append(combined_anomaly)
        
        return all_anomalies
    
    def _combine_detector_results(self, detector_anomalies: List[Dict]) -> Dict[str, Any]:
        """Combine results from multiple detectors"""
        # Take the most severe anomaly as base
        base_anomaly = max(detector_anomalies, key=lambda x: x['anomaly']['score'])['anomaly']
        
        # Average scores from all detectors
        avg_score = np.mean([da['anomaly']['score'] for da in detector_anomalies])
        
        # Collect all detector names
        detectors = [da['detector'] for da in detector_anomalies]
        
        combined = base_anomaly.copy()
        combined['score'] = avg_score
        combined['method'] = 'ensemble'
        combined['ensemble_detectors'] = detectors
        combined['detector_count'] = len(detectors)
        
        return combined
    
    def get_name(self) -> str:
        return "Ensemble Detector"

class AnomalyDetectionSystem:
    """
    Comprehensive anomaly detection system for ChurnGuard analytics
    
    Features:
    - Multiple detection algorithms (statistical, ML, ensemble)
    - Real-time and batch anomaly detection
    - Configurable detection rules per organization/metric
    - Anomaly severity classification and alerting
    - Historical anomaly tracking and analysis
    - Adaptive thresholds and learning
    - Integration with alerting and notification systems
    """
    
    def __init__(self):
        self.detectors = {
            DetectionMethod.STATISTICAL: StatisticalAnomalyDetector(),
            DetectionMethod.ISOLATION_FOREST: IsolationForestDetector(),
            DetectionMethod.LOCAL_OUTLIER_FACTOR: LocalOutlierFactorDetector(),
            DetectionMethod.ENSEMBLE: EnsembleAnomalyDetector()
        }
        
        self.ts_db = get_time_series_db()
        self.analytics_engine = get_analytics_engine()
        
        # Detection rules per organization
        self.detection_rules: Dict[str, List[DetectionRule]] = defaultdict(list)
        
        # Detected anomalies history
        self.anomalies_history: List[Anomaly] = []
        
        # Real-time monitoring
        self.running = False
        self.monitor_thread = None
        self.monitoring_interval = 60  # seconds
        
        # Performance tracking
        self.detection_count = 0
        self.false_positive_rate = 0.05  # Estimated
        
    def start_monitoring(self):
        """Start real-time anomaly monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Anomaly detection monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("Anomaly detection monitoring stopped")
    
    def add_detection_rule(self, rule: DetectionRule) -> str:
        """Add anomaly detection rule"""
        self.detection_rules[rule.organization_id].append(rule)
        logger.info(f"Added detection rule for {rule.metric_name} in org {rule.organization_id}")
        return rule.id
    
    def remove_detection_rule(self, organization_id: str, rule_id: str) -> bool:
        """Remove detection rule"""
        rules = self.detection_rules[organization_id]
        for i, rule in enumerate(rules):
            if rule.id == rule_id:
                rules.pop(i)
                logger.info(f"Removed detection rule {rule_id}")
                return True
        return False
    
    def detect_anomalies(self, metric_name: str, organization_id: str,
                        time_window_hours: int = 24,
                        method: Optional[DetectionMethod] = None) -> List[Anomaly]:
        """
        Detect anomalies in specified metric data
        
        Args:
            metric_name: Name of the metric to analyze
            organization_id: Organization ID
            time_window_hours: Time window for analysis
            method: Specific detection method (None for auto-select)
            
        Returns:
            List of detected anomalies
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        # Get metric data
        data = self.ts_db.query(metric_name, organization_id, start_time, end_time)
        
        if data.empty or len(data) < 10:
            return []
        
        # Find applicable detection rules
        applicable_rules = [
            rule for rule in self.detection_rules[organization_id]
            if rule.metric_name == metric_name and rule.enabled
        ]
        
        if not applicable_rules and method is None:
            # Use default ensemble method
            method = DetectionMethod.ENSEMBLE
            parameters = {'voting_threshold': 2, 'sensitivity': 2.0}
        
        detected_anomalies = []
        
        # Apply rules or use specified method
        if applicable_rules:
            for rule in applicable_rules:
                if len(data) >= rule.min_data_points:
                    rule_anomalies = self._detect_with_rule(data, rule)
                    detected_anomalies.extend(rule_anomalies)
        elif method:
            detector = self.detectors.get(method)
            if detector:
                parameters = {'sensitivity': 2.0}
                raw_anomalies = detector.detect(data, parameters)
                rule_anomalies = self._convert_raw_anomalies(
                    raw_anomalies, metric_name, organization_id, method
                )
                detected_anomalies.extend(rule_anomalies)
        
        # Remove duplicates and sort by severity
        unique_anomalies = self._deduplicate_anomalies(detected_anomalies)
        sorted_anomalies = sorted(unique_anomalies, 
                                key=lambda x: (x.severity.value, -x.confidence), 
                                reverse=True)
        
        # Store in history
        self.anomalies_history.extend(sorted_anomalies)
        self.detection_count += len(sorted_anomalies)
        
        # Trigger alerts for high-severity anomalies
        self._trigger_alerts(sorted_anomalies)
        
        return sorted_anomalies
    
    def get_anomaly_summary(self, organization_id: str, 
                          hours_back: int = 24) -> Dict[str, Any]:
        """Get summary of recent anomalies"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        recent_anomalies = [
            a for a in self.anomalies_history
            if a.organization_id == organization_id and a.timestamp >= cutoff_time
        ]
        
        # Group by severity
        severity_counts = defaultdict(int)
        for anomaly in recent_anomalies:
            severity_counts[anomaly.severity.value] += 1
        
        # Group by metric
        metric_counts = defaultdict(int)
        for anomaly in recent_anomalies:
            metric_counts[anomaly.metric_name] += 1
        
        # Group by type
        type_counts = defaultdict(int)
        for anomaly in recent_anomalies:
            type_counts[anomaly.anomaly_type.value] += 1
        
        return {
            'total_anomalies': len(recent_anomalies),
            'severity_distribution': dict(severity_counts),
            'metric_distribution': dict(metric_counts),
            'type_distribution': dict(type_counts),
            'unresolved_anomalies': len([a for a in recent_anomalies if not a.resolved]),
            'detection_rate': len(recent_anomalies) / hours_back if hours_back > 0 else 0,
            'most_anomalous_metrics': sorted(metric_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:5]
        }
    
    def resolve_anomaly(self, anomaly_id: str, resolution_notes: str = "") -> bool:
        """Mark an anomaly as resolved"""
        for anomaly in self.anomalies_history:
            if anomaly.id == anomaly_id:
                anomaly.resolved = True
                anomaly.resolved_at = datetime.now()
                if resolution_notes:
                    anomaly.metadata['resolution_notes'] = resolution_notes
                return True
        return False
    
    def _monitoring_loop(self):
        """Main monitoring loop for real-time detection"""
        while self.running:
            try:
                # Get all organizations with active rules
                organizations = list(self.detection_rules.keys())
                
                for org_id in organizations:
                    # Get unique metrics for this organization
                    metrics = set(rule.metric_name for rule in self.detection_rules[org_id] 
                                if rule.enabled)
                    
                    for metric_name in metrics:
                        try:
                            # Detect anomalies for this metric
                            anomalies = self.detect_anomalies(
                                metric_name, org_id, time_window_hours=1
                            )
                            
                            if anomalies:
                                logger.info(f"Detected {len(anomalies)} anomalies in {metric_name} for org {org_id}")
                        
                        except Exception as e:
                            logger.error(f"Error monitoring {metric_name} for org {org_id}: {e}")
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Back off on error
    
    def _detect_with_rule(self, data: pd.DataFrame, rule: DetectionRule) -> List[Anomaly]:
        """Detect anomalies using a specific rule"""
        detector = self.detectors.get(rule.method)
        if not detector:
            logger.warning(f"Unknown detection method: {rule.method}")
            return []
        
        # Apply rule parameters
        parameters = rule.parameters.copy()
        parameters['sensitivity'] = rule.sensitivity
        
        try:
            raw_anomalies = detector.detect(data, parameters)
            return self._convert_raw_anomalies(
                raw_anomalies, rule.metric_name, rule.organization_id, rule.method
            )
        except Exception as e:
            logger.error(f"Error detecting with rule {rule.id}: {e}")
            return []
    
    def _convert_raw_anomalies(self, raw_anomalies: List[Dict], 
                              metric_name: str, organization_id: str,
                              method: DetectionMethod) -> List[Anomaly]:
        """Convert raw anomaly detections to Anomaly objects"""
        anomalies = []
        
        for raw in raw_anomalies:
            severity = self._determine_severity(raw['score'], method)
            explanation = self._generate_explanation(raw, metric_name)
            recommendations = self._generate_recommendations(raw, metric_name)
            
            anomaly = Anomaly(
                id=f"anomaly_{organization_id}_{metric_name}_{int(raw['timestamp'].timestamp())}",
                timestamp=raw['timestamp'],
                metric_name=metric_name,
                organization_id=organization_id,
                value=raw['value'],
                expected_value=raw['expected'],
                deviation_score=raw['score'],
                anomaly_type=raw.get('type', AnomalyType.POINT_ANOMALY),
                severity=severity,
                method=method,
                confidence=min(raw['score'] / 5.0, 1.0),  # Normalize score to confidence
                context={
                    'detection_method': raw['method'],
                    'detector_metadata': raw.get('metadata', {})
                },
                explanation=explanation,
                recommendations=recommendations,
                metadata=raw.get('metadata', {})
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    def _determine_severity(self, score: float, method: DetectionMethod) -> AnomalySeverity:
        """Determine severity based on anomaly score"""
        if score > 5.0:
            return AnomalySeverity.CRITICAL
        elif score > 3.0:
            return AnomalySeverity.HIGH
        elif score > 2.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_explanation(self, raw_anomaly: Dict, metric_name: str) -> str:
        """Generate human-readable explanation for anomaly"""
        value = raw_anomaly['value']
        expected = raw_anomaly['expected']
        score = raw_anomaly['score']
        method = raw_anomaly['method']
        
        deviation = ((value - expected) / expected * 100) if expected != 0 else 0
        direction = "higher" if value > expected else "lower"
        
        return f"The {metric_name.replace('_', ' ')} value of {value:.2f} is {abs(deviation):.1f}% {direction} than expected ({expected:.2f}). This anomaly was detected using {method} with a deviation score of {score:.2f}."
    
    def _generate_recommendations(self, raw_anomaly: Dict, metric_name: str) -> List[str]:
        """Generate recommendations for handling anomaly"""
        recommendations = [
            f"Investigate the root cause of this anomaly in {metric_name.replace('_', ' ')}",
            "Check for any system changes or external events during this time period",
            "Verify data quality and collection processes"
        ]
        
        if 'churn' in metric_name.lower():
            recommendations.extend([
                "Review customer behavior patterns for this period",
                "Check for marketing campaigns or pricing changes that might affect churn"
            ])
        elif 'revenue' in metric_name.lower():
            recommendations.extend([
                "Analyze transaction patterns and customer segments",
                "Review pricing strategy and promotional activities"
            ])
        
        return recommendations
    
    def _deduplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Remove duplicate anomalies"""
        seen = set()
        unique_anomalies = []
        
        for anomaly in anomalies:
            # Create key based on timestamp, metric, and organization
            key = (
                anomaly.timestamp.replace(minute=0, second=0, microsecond=0),
                anomaly.metric_name,
                anomaly.organization_id
            )
            
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(anomaly)
        
        return unique_anomalies
    
    def _trigger_alerts(self, anomalies: List[Anomaly]):
        """Trigger alerts for high-severity anomalies"""
        for anomaly in anomalies:
            if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                try:
                    # Convert to analytics engine alert
                    alert_severity = AlertSeverity.CRITICAL if anomaly.severity == AnomalySeverity.CRITICAL else AlertSeverity.HIGH
                    
                    # This would integrate with the alerting system
                    logger.warning(f"High-severity anomaly detected: {anomaly.explanation}")
                    
                except Exception as e:
                    logger.error(f"Error triggering alert for anomaly {anomaly.id}: {e}")

# Global anomaly detection system
anomaly_system = AnomalyDetectionSystem()

def get_anomaly_system() -> AnomalyDetectionSystem:
    """Get the global anomaly detection system"""
    if not anomaly_system.running:
        anomaly_system.start_monitoring()
    return anomaly_system

# Convenience functions
def detect_anomalies(metric_name: str, organization_id: str, hours: int = 24) -> List[Anomaly]:
    """Detect anomalies in a metric"""
    system = get_anomaly_system()
    return system.detect_anomalies(metric_name, organization_id, hours)

def get_anomaly_summary(organization_id: str, hours: int = 24) -> Dict[str, Any]:
    """Get anomaly summary for organization"""
    system = get_anomaly_system()
    return system.get_anomaly_summary(organization_id, hours)

def add_detection_rule(metric_name: str, organization_id: str, 
                      method: DetectionMethod = DetectionMethod.ENSEMBLE,
                      sensitivity: float = 2.0) -> str:
    """Add anomaly detection rule"""
    system = get_anomaly_system()
    rule = DetectionRule(
        id=f"rule_{organization_id}_{metric_name}_{int(time.time())}",
        metric_name=metric_name,
        organization_id=organization_id,
        method=method,
        parameters={'sensitivity': sensitivity},
        sensitivity=sensitivity
    )
    return system.add_detection_rule(rule)