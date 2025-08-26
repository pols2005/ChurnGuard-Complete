# ChurnGuard Real-Time Analytics Engine
# Epic 4 - Advanced Analytics & AI Insights

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import threading
import time

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"
    PERCENTILE = "percentile"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Alert:
    """Analytics alert"""
    id: str
    metric_name: str
    severity: AlertSeverity
    message: str
    threshold_value: float
    actual_value: float
    organization_id: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None

class RealTimeAnalyticsEngine:
    """
    High-performance real-time analytics engine for ChurnGuard
    
    Features:
    - Real-time metric ingestion and processing
    - Sliding window calculations
    - Anomaly detection
    - Threshold-based alerting
    - Multi-tenant data isolation
    - Sub-second query performance
    """
    
    def __init__(self, max_points_per_metric: int = 10000):
        self.max_points = max_points_per_metric
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self.aggregations: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.alerts: List[Alert] = []
        self.alert_thresholds: Dict[str, Dict[str, Any]] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.running = False
        self.processor_thread = None
        self._lock = threading.RLock()
        
        # Performance tracking
        self.processing_times = deque(maxlen=1000)
        self.ingestion_count = 0
        self.last_performance_log = datetime.now()
        
    def start(self):
        """Start the real-time processing engine"""
        if self.running:
            return
            
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processor_thread.start()
        logger.info("Real-time analytics engine started")
        
    def stop(self):
        """Stop the analytics engine"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("Real-time analytics engine stopped")
    
    def ingest_metric(self, metric_name: str, value: float, org_id: str, 
                     timestamp: Optional[datetime] = None, tags: Optional[Dict[str, str]] = None):
        """
        Ingest a new metric data point
        
        Args:
            metric_name: Name of the metric (e.g., 'churn_predictions_per_hour')
            value: Numeric value of the metric
            org_id: Organization ID for multi-tenant isolation
            timestamp: Optional timestamp (defaults to now)
            tags: Optional tags for metric filtering and grouping
        """
        start_time = time.time()
        
        if timestamp is None:
            timestamp = datetime.now()
            
        if tags is None:
            tags = {}
            
        # Add organization tag for multi-tenant isolation
        tags['organization_id'] = org_id
        
        # Create metric point
        point = MetricPoint(
            timestamp=timestamp,
            value=value,
            tags=tags
        )
        
        # Store metric point
        metric_key = f"{org_id}:{metric_name}"
        with self._lock:
            self.metrics[metric_key].append(point)
            self.ingestion_count += 1
            
        # Track processing time
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        
        # Check for alerts
        self._check_alerts(metric_name, value, org_id, tags)
        
        # Notify subscribers
        self._notify_subscribers(metric_name, point, org_id)
        
    def query_metric(self, metric_name: str, org_id: str, 
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    tags: Optional[Dict[str, str]] = None,
                    aggregation: Optional[str] = None) -> List[MetricPoint]:
        """
        Query metric data points with optional filtering and aggregation
        
        Args:
            metric_name: Name of the metric to query
            org_id: Organization ID
            start_time: Optional start time filter
            end_time: Optional end time filter  
            tags: Optional tag filters
            aggregation: Optional aggregation ('avg', 'sum', 'count', 'min', 'max')
            
        Returns:
            List of metric points matching the query
        """
        metric_key = f"{org_id}:{metric_name}"
        
        with self._lock:
            if metric_key not in self.metrics:
                return []
                
            points = list(self.metrics[metric_key])
        
        # Apply time filtering
        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]
            
        # Apply tag filtering
        if tags:
            for tag_key, tag_value in tags.items():
                points = [p for p in points if p.tags.get(tag_key) == tag_value]
        
        # Apply aggregation if requested
        if aggregation and points:
            return self._aggregate_points(points, aggregation)
            
        return points
    
    def get_real_time_stats(self, metric_name: str, org_id: str, 
                           window_minutes: int = 5) -> Dict[str, float]:
        """
        Get real-time statistics for a metric over a sliding window
        
        Args:
            metric_name: Name of the metric
            org_id: Organization ID
            window_minutes: Sliding window size in minutes
            
        Returns:
            Dictionary with statistics (avg, count, rate, etc.)
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=window_minutes)
        
        points = self.query_metric(metric_name, org_id, start_time, end_time)
        
        if not points:
            return {
                'count': 0,
                'avg': 0.0,
                'sum': 0.0,
                'min': 0.0,
                'max': 0.0,
                'rate_per_minute': 0.0,
                'last_value': 0.0
            }
        
        values = [p.value for p in points]
        
        return {
            'count': len(values),
            'avg': np.mean(values),
            'sum': np.sum(values),
            'min': np.min(values),
            'max': np.max(values),
            'rate_per_minute': len(values) / window_minutes,
            'last_value': values[-1] if values else 0.0,
            'std_dev': np.std(values),
            'p50': np.percentile(values, 50),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99)
        }
    
    def setup_alert(self, metric_name: str, org_id: str, 
                   threshold_type: str, threshold_value: float,
                   severity: AlertSeverity = AlertSeverity.MEDIUM,
                   window_minutes: int = 5):
        """
        Set up threshold-based alerting for a metric
        
        Args:
            metric_name: Name of the metric to monitor
            org_id: Organization ID
            threshold_type: Type of threshold ('above', 'below', 'change_rate')
            threshold_value: Threshold value to trigger alert
            severity: Alert severity level
            window_minutes: Window for threshold evaluation
        """
        alert_key = f"{org_id}:{metric_name}"
        
        self.alert_thresholds[alert_key] = {
            'threshold_type': threshold_type,
            'threshold_value': threshold_value,
            'severity': severity,
            'window_minutes': window_minutes,
            'last_triggered': None
        }
        
        logger.info(f"Alert setup: {metric_name} {threshold_type} {threshold_value} for org {org_id}")
    
    def subscribe_to_metric(self, metric_name: str, callback: Callable):
        """
        Subscribe to real-time metric updates
        
        Args:
            metric_name: Name of the metric to subscribe to
            callback: Function to call when new data arrives
        """
        self.subscribers[metric_name].append(callback)
        
    def get_anomalies(self, metric_name: str, org_id: str, 
                     sensitivity: float = 2.0, window_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metric data using statistical methods
        
        Args:
            metric_name: Name of the metric to analyze
            org_id: Organization ID
            sensitivity: Standard deviation threshold for anomaly detection
            window_hours: Time window to analyze
            
        Returns:
            List of detected anomalies
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=window_hours)
        
        points = self.query_metric(metric_name, org_id, start_time, end_time)
        
        if len(points) < 10:  # Need minimum points for statistical analysis
            return []
            
        values = [p.value for p in points]
        timestamps = [p.timestamp for p in points]
        
        # Calculate rolling statistics
        df = pd.DataFrame({'value': values, 'timestamp': timestamps})
        df['rolling_mean'] = df['value'].rolling(window=min(10, len(values)//2)).mean()
        df['rolling_std'] = df['value'].rolling(window=min(10, len(values)//2)).std()
        
        # Detect anomalies using z-score
        anomalies = []
        for i, row in df.iterrows():
            if pd.isna(row['rolling_mean']) or pd.isna(row['rolling_std']):
                continue
                
            z_score = abs(row['value'] - row['rolling_mean']) / (row['rolling_std'] + 1e-6)
            
            if z_score > sensitivity:
                anomalies.append({
                    'timestamp': row['timestamp'].isoformat(),
                    'value': row['value'],
                    'expected_value': row['rolling_mean'],
                    'z_score': z_score,
                    'severity': 'high' if z_score > 3.0 else 'medium',
                    'type': 'statistical_outlier'
                })
        
        return anomalies
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics"""
        with self._lock:
            total_points = sum(len(points) for points in self.metrics.values())
            avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
            
        return {
            'total_metrics': len(self.metrics),
            'total_data_points': total_points,
            'ingestion_count': self.ingestion_count,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'active_alerts': len([a for a in self.alerts if a.resolved_at is None]),
            'memory_usage_mb': self._estimate_memory_usage() / (1024 * 1024),
            'engine_uptime': (datetime.now() - self.last_performance_log).total_seconds()
        }
    
    def _process_loop(self):
        """Background processing loop for aggregations and cleanup"""
        while self.running:
            try:
                self._update_aggregations()
                self._cleanup_old_data()
                self._log_performance()
                time.sleep(1)  # Process every second
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(5)  # Back off on error
    
    def _update_aggregations(self):
        """Update pre-calculated aggregations for common queries"""
        with self._lock:
            for metric_key, points in self.metrics.items():
                if not points:
                    continue
                    
                # Calculate common aggregations
                recent_points = [p for p in points if 
                               (datetime.now() - p.timestamp).total_seconds() < 300]  # 5 minutes
                
                if recent_points:
                    values = [p.value for p in recent_points]
                    self.aggregations[metric_key] = {
                        'count_5m': len(values),
                        'avg_5m': np.mean(values),
                        'sum_5m': np.sum(values),
                        'rate_per_minute': len(values) / 5.0,
                        'last_updated': datetime.now().isoformat()
                    }
    
    def _check_alerts(self, metric_name: str, value: float, org_id: str, tags: Dict[str, str]):
        """Check if metric value triggers any alerts"""
        alert_key = f"{org_id}:{metric_name}"
        
        if alert_key not in self.alert_thresholds:
            return
            
        threshold_config = self.alert_thresholds[alert_key]
        threshold_type = threshold_config['threshold_type']
        threshold_value = threshold_config['threshold_value']
        severity = threshold_config['severity']
        
        should_alert = False
        message = ""
        
        if threshold_type == 'above' and value > threshold_value:
            should_alert = True
            message = f"{metric_name} value {value:.2f} is above threshold {threshold_value:.2f}"
        elif threshold_type == 'below' and value < threshold_value:
            should_alert = True  
            message = f"{metric_name} value {value:.2f} is below threshold {threshold_value:.2f}"
        elif threshold_type == 'change_rate':
            # Calculate rate of change
            stats = self.get_real_time_stats(metric_name, org_id, 5)
            if stats['count'] > 1:
                rate = stats['rate_per_minute']
                if rate > threshold_value:
                    should_alert = True
                    message = f"{metric_name} rate {rate:.2f}/min exceeds threshold {threshold_value:.2f}/min"
        
        if should_alert:
            alert = Alert(
                id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{org_id[:8]}",
                metric_name=metric_name,
                severity=severity,
                message=message,
                threshold_value=threshold_value,
                actual_value=value,
                organization_id=org_id,
                triggered_at=datetime.now()
            )
            
            self.alerts.append(alert)
            
            # Update last triggered time to prevent spam
            threshold_config['last_triggered'] = datetime.now()
            
            logger.warning(f"Alert triggered: {message}")
    
    def _notify_subscribers(self, metric_name: str, point: MetricPoint, org_id: str):
        """Notify subscribers of new metric data"""
        for callback in self.subscribers.get(metric_name, []):
            try:
                callback(metric_name, point, org_id)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def _aggregate_points(self, points: List[MetricPoint], aggregation: str) -> List[MetricPoint]:
        """Apply aggregation to metric points"""
        if not points:
            return []
            
        values = [p.value for p in points]
        
        if aggregation == 'avg':
            agg_value = np.mean(values)
        elif aggregation == 'sum':
            agg_value = np.sum(values)
        elif aggregation == 'count':
            agg_value = len(values)
        elif aggregation == 'min':
            agg_value = np.min(values)
        elif aggregation == 'max':
            agg_value = np.max(values)
        else:
            return points  # No aggregation
            
        # Return single aggregated point
        return [MetricPoint(
            timestamp=points[-1].timestamp,
            value=agg_value,
            tags={'aggregation': aggregation, 'point_count': len(points)}
        )]
    
    def _cleanup_old_data(self):
        """Clean up old data points to manage memory"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours
        
        with self._lock:
            for metric_key in list(self.metrics.keys()):
                points = self.metrics[metric_key]
                # Remove old points (deque maxlen handles most of this)
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()
    
    def _log_performance(self):
        """Log performance metrics periodically"""
        now = datetime.now()
        if (now - self.last_performance_log).total_seconds() > 60:  # Every minute
            perf_metrics = self.get_performance_metrics()
            logger.info(f"Analytics Engine Performance: {perf_metrics}")
            self.last_performance_log = now
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        total_size = 0
        
        # Estimate size of metric points
        for points in self.metrics.values():
            total_size += len(points) * 200  # Rough estimate per MetricPoint
            
        # Estimate size of aggregations
        total_size += len(self.aggregations) * 500
        
        # Estimate size of alerts
        total_size += len(self.alerts) * 300
        
        return total_size

# Global analytics engine instance
analytics_engine = RealTimeAnalyticsEngine()

def get_analytics_engine() -> RealTimeAnalyticsEngine:
    """Get the global analytics engine instance"""
    if not analytics_engine.running:
        analytics_engine.start()
    return analytics_engine

# Convenience functions for common operations
def track_metric(metric_name: str, value: float, org_id: str, **tags):
    """Track a metric value"""
    engine = get_analytics_engine()
    engine.ingest_metric(metric_name, value, org_id, tags=tags)

def get_metric_stats(metric_name: str, org_id: str, window_minutes: int = 5) -> Dict[str, float]:
    """Get real-time statistics for a metric"""
    engine = get_analytics_engine()
    return engine.get_real_time_stats(metric_name, org_id, window_minutes)

def setup_metric_alert(metric_name: str, org_id: str, threshold_type: str, 
                      threshold_value: float, severity: str = 'medium'):
    """Set up an alert for a metric"""
    engine = get_analytics_engine()
    severity_enum = AlertSeverity(severity.lower())
    engine.setup_alert(metric_name, org_id, threshold_type, threshold_value, severity_enum)