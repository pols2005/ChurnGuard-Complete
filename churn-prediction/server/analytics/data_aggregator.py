# ChurnGuard Data Aggregation Pipeline
# Epic 4 - Advanced Analytics & AI Insights

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .statistical_analysis import get_stats_service, StatisticalSummary
from .time_series_db import get_time_series_db, TimeSeriesPoint, write_metric
from .real_time_engine import get_analytics_engine, track_metric

logger = logging.getLogger(__name__)

class AggregationLevel(Enum):
    RAW = "raw"           # Individual data points
    MINUTE = "minute"     # 1-minute aggregations
    HOUR = "hour"         # 1-hour aggregations  
    DAY = "day"           # Daily aggregations
    WEEK = "week"         # Weekly aggregations
    MONTH = "month"       # Monthly aggregations

class AggregationFunction(Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    PERCENTILE = "percentile"
    STDDEV = "stddev"
    VARIANCE = "variance"

@dataclass
class AggregationRule:
    """Defines how to aggregate a specific metric"""
    source_metric: str
    target_metric: str
    level: AggregationLevel
    function: AggregationFunction
    organization_id: str
    tags_to_group_by: List[str]
    percentile_value: Optional[float] = None  # For percentile aggregations
    window_size: int = 1  # Number of periods to aggregate over
    enabled: bool = True

@dataclass
class AggregationJob:
    """Represents a scheduled aggregation job"""
    id: str
    rule: AggregationRule
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    error_message: Optional[str] = None

class DataAggregationPipeline:
    """
    High-performance data aggregation pipeline for ChurnGuard analytics
    
    Features:
    - Multi-level time-series aggregation (minute, hour, day, week, month)
    - Real-time and batch aggregation modes
    - Parallel processing for large datasets
    - Configurable aggregation rules per organization
    - Memory-efficient sliding window calculations
    - Error handling and retry logic
    - Performance monitoring and optimization
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.aggregation_rules: Dict[str, List[AggregationRule]] = defaultdict(list)
        self.jobs: Dict[str, AggregationJob] = {}
        self.running = False
        self.scheduler_thread = None
        self.stats_service = get_stats_service()
        self.ts_db = get_time_series_db()
        self.analytics_engine = get_analytics_engine()
        
        # Performance tracking
        self.processed_metrics = 0
        self.processing_times = deque(maxlen=1000)
        self.error_count = 0
        self.last_performance_log = datetime.now()
        
        # Cache for frequently accessed aggregations
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes
        
    def start(self):
        """Start the aggregation pipeline"""
        if self.running:
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Setup default aggregation rules
        self._setup_default_rules()
        
        logger.info(f"Data aggregation pipeline started with {self.max_workers} workers")
        
    def stop(self):
        """Stop the aggregation pipeline"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        self.executor.shutdown(wait=True)
        logger.info("Data aggregation pipeline stopped")
    
    def add_aggregation_rule(self, rule: AggregationRule) -> str:
        """
        Add a new aggregation rule
        
        Args:
            rule: AggregationRule defining how to aggregate data
            
        Returns:
            Rule ID for later reference
        """
        rule_id = f"{rule.organization_id}:{rule.source_metric}:{rule.target_metric}:{rule.level.value}"
        
        # Add to organization's rules
        self.aggregation_rules[rule.organization_id].append(rule)
        
        # Create initial job
        job = AggregationJob(
            id=f"job_{rule_id}_{int(time.time())}",
            rule=rule,
            next_run=self._calculate_next_run(rule)
        )
        self.jobs[job.id] = job
        
        logger.info(f"Added aggregation rule: {rule_id}")
        return rule_id
    
    def remove_aggregation_rule(self, organization_id: str, source_metric: str, 
                               target_metric: str, level: AggregationLevel) -> bool:
        """Remove an aggregation rule"""
        rules = self.aggregation_rules[organization_id]
        
        for i, rule in enumerate(rules):
            if (rule.source_metric == source_metric and 
                rule.target_metric == target_metric and 
                rule.level == level):
                
                rules.pop(i)
                
                # Remove associated jobs
                jobs_to_remove = [
                    job_id for job_id, job in self.jobs.items()
                    if job.rule == rule
                ]
                for job_id in jobs_to_remove:
                    del self.jobs[job_id]
                
                logger.info(f"Removed aggregation rule: {source_metric} -> {target_metric}")
                return True
        
        return False
    
    def get_aggregated_data(self, metric_name: str, organization_id: str,
                           level: AggregationLevel, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           tags: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Retrieve aggregated data from the time-series database
        
        Args:
            metric_name: Name of the aggregated metric
            organization_id: Organization ID
            level: Aggregation level (hour, day, etc.)
            start_time: Start time for query
            end_time: End time for query
            tags: Optional tag filters
            
        Returns:
            DataFrame with aggregated data
        """
        # Check cache first
        cache_key = f"{organization_id}:{metric_name}:{level.value}:{start_time}:{end_time}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']
        
        # Query from time-series database
        aggregated_metric_name = f"{metric_name}_{level.value}_agg"
        df = self.ts_db.query(
            aggregated_metric_name,
            organization_id,
            start_time,
            end_time,
            tags
        )
        
        # Cache the result
        self.cache[cache_key] = {
            'data': df,
            'timestamp': datetime.now()
        }
        
        return df
    
    def run_aggregation_now(self, organization_id: str, metric_name: str, 
                           level: AggregationLevel) -> Dict[str, Any]:
        """
        Run aggregation immediately for a specific metric
        
        Args:
            organization_id: Organization ID
            metric_name: Metric to aggregate
            level: Aggregation level
            
        Returns:
            Aggregation results summary
        """
        # Find matching rules
        matching_rules = [
            rule for rule in self.aggregation_rules[organization_id]
            if rule.source_metric == metric_name and rule.level == level
        ]
        
        if not matching_rules:
            return {'error': f'No aggregation rules found for {metric_name} at {level.value} level'}
        
        results = []
        for rule in matching_rules:
            try:
                result = self._execute_aggregation(rule)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running aggregation for {rule.target_metric}: {e}")
                results.append({'error': str(e), 'rule': rule.target_metric})
        
        return {
            'status': 'completed',
            'rules_processed': len(results),
            'results': results
        }
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics"""
        return {
            'processed_metrics': self.processed_metrics,
            'error_count': self.error_count,
            'active_rules': sum(len(rules) for rules in self.aggregation_rules.values()),
            'pending_jobs': len([j for j in self.jobs.values() if j.status == 'pending']),
            'running_jobs': len([j for j in self.jobs.values() if j.status == 'running']),
            'avg_processing_time_ms': np.mean(self.processing_times) * 1000 if self.processing_times else 0,
            'cache_entries': len(self.cache),
            'uptime_seconds': (datetime.now() - self.last_performance_log).total_seconds()
        }
    
    def _setup_default_rules(self):
        """Setup default aggregation rules for common metrics"""
        default_organizations = ['demo-org-1', 'demo-org-2']  # Would come from config
        
        for org_id in default_organizations:
            # Churn prediction aggregations
            self.add_aggregation_rule(AggregationRule(
                source_metric='churn_predictions',
                target_metric='churn_predictions_hourly',
                level=AggregationLevel.HOUR,
                function=AggregationFunction.COUNT,
                organization_id=org_id,
                tags_to_group_by=['model_version', 'risk_level']
            ))
            
            self.add_aggregation_rule(AggregationRule(
                source_metric='churn_risk_score',
                target_metric='avg_churn_risk_hourly',
                level=AggregationLevel.HOUR,
                function=AggregationFunction.AVG,
                organization_id=org_id,
                tags_to_group_by=['customer_segment']
            ))
            
            # Customer activity aggregations
            self.add_aggregation_rule(AggregationRule(
                source_metric='customer_activity',
                target_metric='customer_activity_daily',
                level=AggregationLevel.DAY,
                function=AggregationFunction.SUM,
                organization_id=org_id,
                tags_to_group_by=['activity_type']
            ))
            
            # Revenue impact aggregations
            self.add_aggregation_rule(AggregationRule(
                source_metric='revenue_at_risk',
                target_metric='revenue_at_risk_daily',
                level=AggregationLevel.DAY,
                function=AggregationFunction.SUM,
                organization_id=org_id,
                tags_to_group_by=['customer_tier']
            ))
    
    def _scheduler_loop(self):
        """Main scheduler loop for running aggregation jobs"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Find jobs ready to run
                ready_jobs = [
                    job for job in self.jobs.values()
                    if (job.status == 'pending' and 
                        job.next_run and 
                        job.next_run <= current_time)
                ]
                
                if ready_jobs:
                    # Submit jobs to thread pool
                    future_to_job = {
                        self.executor.submit(self._execute_job, job): job
                        for job in ready_jobs[:self.max_workers]
                    }
                    
                    # Process completed jobs
                    for future in as_completed(future_to_job, timeout=1):
                        job = future_to_job[future]
                        try:
                            result = future.result()
                            job.status = 'completed'
                            job.last_run = current_time
                            job.next_run = self._calculate_next_run(job.rule)
                            
                            # Track performance
                            self.processed_metrics += result.get('points_processed', 0)
                            
                        except Exception as e:
                            job.status = 'failed'
                            job.error_message = str(e)
                            job.next_run = current_time + timedelta(minutes=5)  # Retry in 5 minutes
                            self.error_count += 1
                            logger.error(f"Job {job.id} failed: {e}")
                
                # Cleanup old completed jobs
                self._cleanup_old_jobs()
                
                # Log performance periodically
                self._log_performance()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(30)  # Back off on error
    
    def _execute_job(self, job: AggregationJob) -> Dict[str, Any]:
        """Execute a single aggregation job"""
        start_time = time.time()
        job.status = 'running'
        
        try:
            result = self._execute_aggregation(job.rule)
            
            # Track processing time
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing aggregation job {job.id}: {e}")
            raise
    
    def _execute_aggregation(self, rule: AggregationRule) -> Dict[str, Any]:
        """Execute a specific aggregation rule"""
        # Determine time window for aggregation
        end_time = datetime.now()
        
        if rule.level == AggregationLevel.MINUTE:
            start_time = end_time - timedelta(minutes=rule.window_size)
            interval = '1min'
        elif rule.level == AggregationLevel.HOUR:
            start_time = end_time - timedelta(hours=rule.window_size)
            interval = '1h'
        elif rule.level == AggregationLevel.DAY:
            start_time = end_time - timedelta(days=rule.window_size)
            interval = '1d'
        elif rule.level == AggregationLevel.WEEK:
            start_time = end_time - timedelta(weeks=rule.window_size)
            interval = '1w'
        elif rule.level == AggregationLevel.MONTH:
            start_time = end_time - timedelta(days=30 * rule.window_size)
            interval = '1M'
        else:
            raise ValueError(f"Unsupported aggregation level: {rule.level}")
        
        # Query source data
        source_df = self.ts_db.query(
            rule.source_metric,
            rule.organization_id,
            start_time,
            end_time
        )
        
        if source_df.empty:
            return {'points_processed': 0, 'points_generated': 0, 'message': 'No source data'}
        
        # Apply aggregation function
        aggregated_points = self._apply_aggregation_function(
            source_df, rule.function, rule.tags_to_group_by, 
            interval, rule.percentile_value
        )
        
        # Write aggregated points back to time-series database
        target_metric = f"{rule.target_metric}_{rule.level.value}_agg"
        
        for point_data in aggregated_points:
            point = TimeSeriesPoint(
                timestamp=point_data['timestamp'],
                metric_name=target_metric,
                value=point_data['value'],
                organization_id=rule.organization_id,
                tags={
                    **point_data.get('tags', {}),
                    'aggregation_level': rule.level.value,
                    'aggregation_function': rule.function.value,
                    'source_metric': rule.source_metric
                }
            )
            self.ts_db.write_point(point)
        
        # Track metrics in real-time engine
        track_metric(
            f"aggregation_job_completed",
            1.0,
            rule.organization_id,
            source_metric=rule.source_metric,
            target_metric=rule.target_metric,
            level=rule.level.value
        )
        
        return {
            'points_processed': len(source_df),
            'points_generated': len(aggregated_points),
            'time_window': f"{start_time} to {end_time}",
            'aggregation_function': rule.function.value
        }
    
    def _apply_aggregation_function(self, df: pd.DataFrame, 
                                   function: AggregationFunction,
                                   group_by_tags: List[str],
                                   interval: str,
                                   percentile_value: Optional[float] = None) -> List[Dict[str, Any]]:
        """Apply the specified aggregation function to the data"""
        if df.empty:
            return []
        
        # Set timestamp as index for resampling
        df = df.set_index('timestamp')
        
        # Group by tags if specified
        if group_by_tags:
            # This would require extracting tags from the data
            # For now, we'll aggregate without grouping
            pass
        
        # Apply aggregation function
        if function == AggregationFunction.COUNT:
            resampled = df['value'].resample(interval).count()
        elif function == AggregationFunction.SUM:
            resampled = df['value'].resample(interval).sum()
        elif function == AggregationFunction.AVG:
            resampled = df['value'].resample(interval).mean()
        elif function == AggregationFunction.MIN:
            resampled = df['value'].resample(interval).min()
        elif function == AggregationFunction.MAX:
            resampled = df['value'].resample(interval).max()
        elif function == AggregationFunction.PERCENTILE:
            if percentile_value is None:
                percentile_value = 50.0  # Default to median
            resampled = df['value'].resample(interval).quantile(percentile_value / 100.0)
        elif function == AggregationFunction.STDDEV:
            resampled = df['value'].resample(interval).std()
        elif function == AggregationFunction.VARIANCE:
            resampled = df['value'].resample(interval).var()
        else:
            raise ValueError(f"Unsupported aggregation function: {function}")
        
        # Convert to list of points
        points = []
        for timestamp, value in resampled.items():
            if pd.notna(value):  # Skip NaN values
                points.append({
                    'timestamp': timestamp.to_pydatetime(),
                    'value': float(value),
                    'tags': {}
                })
        
        return points
    
    def _calculate_next_run(self, rule: AggregationRule) -> datetime:
        """Calculate the next run time for an aggregation rule"""
        now = datetime.now()
        
        if rule.level == AggregationLevel.MINUTE:
            return now + timedelta(minutes=1)
        elif rule.level == AggregationLevel.HOUR:
            return now + timedelta(hours=1)
        elif rule.level == AggregationLevel.DAY:
            # Run at midnight
            next_day = now + timedelta(days=1)
            return next_day.replace(hour=0, minute=0, second=0, microsecond=0)
        elif rule.level == AggregationLevel.WEEK:
            # Run at midnight on Monday
            days_until_monday = 7 - now.weekday()
            next_monday = now + timedelta(days=days_until_monday)
            return next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        elif rule.level == AggregationLevel.MONTH:
            # Run on the first day of next month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return next_month
        else:
            return now + timedelta(hours=1)  # Default fallback
    
    def _cleanup_old_jobs(self):
        """Clean up old completed jobs to prevent memory leaks"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        jobs_to_remove = [
            job_id for job_id, job in self.jobs.items()
            if (job.status in ['completed', 'failed'] and 
                job.last_run and 
                job.last_run < cutoff_time)
        ]
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
    
    def _log_performance(self):
        """Log performance metrics periodically"""
        now = datetime.now()
        if (now - self.last_performance_log).total_seconds() > 300:  # Every 5 minutes
            stats = self.get_pipeline_stats()
            logger.info(f"Aggregation Pipeline Performance: {stats}")
            self.last_performance_log = now

# Global aggregation pipeline instance
aggregation_pipeline = DataAggregationPipeline()

def get_aggregation_pipeline() -> DataAggregationPipeline:
    """Get the global aggregation pipeline instance"""
    if not aggregation_pipeline.running:
        aggregation_pipeline.start()
    return aggregation_pipeline

# Convenience functions
def aggregate_metric_now(organization_id: str, metric_name: str, 
                        level: AggregationLevel) -> Dict[str, Any]:
    """Run aggregation immediately for a specific metric"""
    pipeline = get_aggregation_pipeline()
    return pipeline.run_aggregation_now(organization_id, metric_name, level)

def get_aggregated_metrics(metric_name: str, organization_id: str, 
                          level: AggregationLevel, hours_back: int = 24) -> pd.DataFrame:
    """Get aggregated metrics for the specified time window"""
    pipeline = get_aggregation_pipeline()
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    return pipeline.get_aggregated_data(metric_name, organization_id, level, start_time, end_time)