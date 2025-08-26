# ChurnGuard A/B Testing & Experiment Management System  
# Epic 4 Phase 5 - A/B Testing Framework

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import numpy as np
import pandas as pd
from collections import defaultdict
import hashlib
import random

from .time_series_db import get_time_series_db
from .statistical_analysis import get_stats_service
from .behavioral_analysis import get_behavior_engine

logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class ExperimentType(Enum):
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    SEQUENTIAL = "sequential"
    BANDIT = "bandit"
    FEATURE_FLAG = "feature_flag"

class TrafficAllocation(Enum):
    EQUAL = "equal"
    WEIGHTED = "weighted"
    ADAPTIVE = "adaptive"
    CUSTOM = "custom"

class StatisticalMethod(Enum):
    FREQUENTIST = "frequentist"
    BAYESIAN = "bayesian"
    SEQUENTIAL = "sequential"

class MetricType(Enum):
    BINARY = "binary"           # Conversion rate, signup rate
    CONTINUOUS = "continuous"   # Revenue, session duration
    COUNT = "count"             # Page views, clicks
    RATIO = "ratio"             # Click-through rate
    TIME_TO_EVENT = "time_to_event"  # Time to conversion

@dataclass
class ExperimentMetric:
    """Definition of a metric to be tracked in an experiment"""
    metric_id: str
    name: str
    description: str
    metric_type: MetricType
    is_primary: bool
    expected_effect_size: Optional[float] = None
    minimum_detectable_effect: float = 0.05
    direction: str = "increase"  # "increase", "decrease", "any"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentVariant:
    """A variant in an A/B test experiment"""
    variant_id: str
    name: str
    description: str
    traffic_allocation: float
    configuration: Dict[str, Any]
    is_control: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentConfiguration:
    """Configuration parameters for an experiment"""
    sample_size_per_variant: Optional[int] = None
    minimum_runtime_days: int = 7
    maximum_runtime_days: int = 30
    significance_level: float = 0.05
    statistical_power: float = 0.8
    traffic_ramp_up_days: int = 1
    early_stopping_enabled: bool = True
    sequential_testing: bool = False
    guardrail_metrics: List[str] = field(default_factory=list)

@dataclass
class Experiment:
    """Complete experiment definition and state"""
    experiment_id: str
    organization_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    owner: str
    created_at: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    
    # Experiment design
    variants: List[ExperimentVariant] = field(default_factory=list)
    metrics: List[ExperimentMetric] = field(default_factory=list)
    configuration: ExperimentConfiguration = field(default_factory=ExperimentConfiguration)
    
    # Targeting and segmentation
    target_criteria: Dict[str, Any] = field(default_factory=dict)
    exclusion_criteria: Dict[str, Any] = field(default_factory=dict)
    segment_filters: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tracking
    total_participants: int = 0
    variant_participants: Dict[str, int] = field(default_factory=dict)
    
    # Results (populated during analysis)
    results: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParticipantAssignment:
    """Record of a participant's assignment to an experiment variant"""
    assignment_id: str
    experiment_id: str
    participant_id: str
    variant_id: str
    assignment_date: datetime
    organization_id: str
    segment_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentEvent:
    """Event tracked for experiment analysis"""
    event_id: str
    experiment_id: str
    participant_id: str
    variant_id: str
    metric_id: str
    event_timestamp: datetime
    event_value: Union[float, int, bool, str]
    organization_id: str
    properties: Dict[str, Any] = field(default_factory=dict)

class ExperimentManager:
    """
    Comprehensive A/B testing and experiment management system
    
    Features:
    - Multiple experiment types (A/B, multivariate, bandit, feature flags)
    - Advanced participant assignment with consistent hashing
    - Real-time experiment monitoring and analysis
    - Statistical power calculations and sample size estimation
    - Early stopping rules and guardrail monitoring
    - Integration with customer segmentation and behavioral analysis
    - Experiment lifecycle management and collaboration tools
    - Results analysis with multiple statistical methods
    """
    
    def __init__(self):
        self.ts_db = get_time_series_db()
        self.stats_service = get_stats_service()
        self.behavior_engine = get_behavior_engine()
        
        # Experiment storage
        self.experiments: Dict[str, Experiment] = {}
        self.assignments: Dict[str, List[ParticipantAssignment]] = defaultdict(list)
        self.events: Dict[str, List[ExperimentEvent]] = defaultdict(list)
        
        # Configuration
        self.default_config = ExperimentConfiguration()
        self.hash_seed = "churnguard_experiments_2024"
        
    def create_experiment(self, name: str, description: str, organization_id: str,
                         owner: str, experiment_type: ExperimentType = ExperimentType.AB_TEST) -> str:
        """
        Create a new experiment
        
        Args:
            name: Experiment name
            description: Detailed description
            organization_id: Organization identifier
            owner: Experiment owner/creator
            experiment_type: Type of experiment
            
        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        experiment = Experiment(
            experiment_id=experiment_id,
            organization_id=organization_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            status=ExperimentStatus.DRAFT,
            owner=owner,
            created_at=datetime.now()
        )
        
        self.experiments[experiment_id] = experiment
        
        logger.info(f"Created experiment {experiment_id}: {name}")
        return experiment_id
    
    def add_variant(self, experiment_id: str, name: str, description: str,
                   configuration: Dict[str, Any], traffic_allocation: float = 0.5,
                   is_control: bool = False) -> str:
        """
        Add a variant to an experiment
        
        Args:
            experiment_id: Experiment identifier
            name: Variant name
            description: Variant description
            configuration: Variant configuration parameters
            traffic_allocation: Percentage of traffic (0.0-1.0)
            is_control: Whether this is the control variant
            
        Returns:
            Variant ID
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status not in [ExperimentStatus.DRAFT, ExperimentStatus.READY]:
            raise ValueError(f"Cannot add variants to {experiment.status.value} experiment")
        
        variant_id = f"var_{uuid.uuid4().hex[:8]}"
        
        variant = ExperimentVariant(
            variant_id=variant_id,
            name=name,
            description=description,
            traffic_allocation=traffic_allocation,
            configuration=configuration,
            is_control=is_control
        )
        
        experiment.variants.append(variant)
        
        # Initialize participant tracking
        experiment.variant_participants[variant_id] = 0
        
        logger.info(f"Added variant {variant_id} to experiment {experiment_id}")
        return variant_id
    
    def add_metric(self, experiment_id: str, name: str, description: str,
                  metric_type: MetricType, is_primary: bool = False,
                  minimum_detectable_effect: float = 0.05, direction: str = "increase") -> str:
        """
        Add a metric to track in an experiment
        
        Args:
            experiment_id: Experiment identifier
            name: Metric name
            description: Metric description
            metric_type: Type of metric
            is_primary: Whether this is the primary metric
            minimum_detectable_effect: Minimum effect size to detect
            direction: Expected direction of change
            
        Returns:
            Metric ID
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        metric_id = f"met_{uuid.uuid4().hex[:8]}"
        
        metric = ExperimentMetric(
            metric_id=metric_id,
            name=name,
            description=description,
            metric_type=metric_type,
            is_primary=is_primary,
            minimum_detectable_effect=minimum_detectable_effect,
            direction=direction
        )
        
        experiment.metrics.append(metric)
        
        logger.info(f"Added metric {metric_id} to experiment {experiment_id}")
        return metric_id
    
    def configure_experiment(self, experiment_id: str, 
                           config: ExperimentConfiguration) -> bool:
        """
        Configure experiment parameters
        
        Args:
            experiment_id: Experiment identifier
            config: Configuration parameters
            
        Returns:
            Success status
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        experiment.configuration = config
        
        # Calculate sample size if not provided
        if config.sample_size_per_variant is None:
            primary_metrics = [m for m in experiment.metrics if m.is_primary]
            if primary_metrics:
                sample_size = self._calculate_required_sample_size(primary_metrics[0], config)
                config.sample_size_per_variant = sample_size
        
        return True
    
    def start_experiment(self, experiment_id: str, start_date: Optional[datetime] = None) -> bool:
        """
        Start running an experiment
        
        Args:
            experiment_id: Experiment identifier
            start_date: When to start (None for immediate)
            
        Returns:
            Success status
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        # Validate experiment is ready to start
        validation_errors = self._validate_experiment_ready(experiment)
        if validation_errors:
            logger.error(f"Experiment validation failed: {validation_errors}")
            return False
        
        # Set start date
        if start_date is None:
            start_date = datetime.now()
        
        experiment.start_date = start_date
        experiment.status = ExperimentStatus.RUNNING
        
        # Calculate end date
        experiment.end_date = start_date + timedelta(days=experiment.configuration.maximum_runtime_days)
        
        # Normalize traffic allocations if needed
        self._normalize_traffic_allocations(experiment)
        
        logger.info(f"Started experiment {experiment_id} at {start_date}")
        return True
    
    def assign_participant(self, experiment_id: str, participant_id: str,
                         organization_id: str, participant_attributes: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Assign a participant to an experiment variant
        
        Args:
            experiment_id: Experiment identifier
            participant_id: Participant (user/customer) identifier
            organization_id: Organization identifier
            participant_attributes: Attributes for targeting/segmentation
            
        Returns:
            Variant ID if assigned, None if not eligible
        """
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        # Check if experiment is running
        if experiment.status != ExperimentStatus.RUNNING:
            return None
        
        # Check if participant already assigned
        existing_assignment = self._get_participant_assignment(experiment_id, participant_id)
        if existing_assignment:
            return existing_assignment.variant_id
        
        # Check targeting criteria
        if not self._check_participant_eligibility(experiment, participant_id, participant_attributes):
            return None
        
        # Assign to variant using consistent hashing
        variant_id = self._assign_variant(experiment, participant_id, participant_attributes)
        
        if variant_id:
            # Record assignment
            assignment = ParticipantAssignment(
                assignment_id=f"asg_{uuid.uuid4().hex[:8]}",
                experiment_id=experiment_id,
                participant_id=participant_id,
                variant_id=variant_id,
                assignment_date=datetime.now(),
                organization_id=organization_id,
                segment_info=participant_attributes or {}
            )
            
            self.assignments[experiment_id].append(assignment)
            experiment.total_participants += 1
            experiment.variant_participants[variant_id] += 1
            
            logger.debug(f"Assigned participant {participant_id} to variant {variant_id} in experiment {experiment_id}")
        
        return variant_id
    
    def track_event(self, experiment_id: str, participant_id: str,
                   metric_id: str, value: Union[float, int, bool, str],
                   event_timestamp: Optional[datetime] = None,
                   properties: Optional[Dict[str, Any]] = None) -> str:
        """
        Track an event for experiment analysis
        
        Args:
            experiment_id: Experiment identifier
            participant_id: Participant identifier
            metric_id: Metric identifier
            value: Event value
            event_timestamp: When the event occurred
            properties: Additional event properties
            
        Returns:
            Event ID
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        # Get participant assignment
        assignment = self._get_participant_assignment(experiment_id, participant_id)
        if not assignment:
            logger.warning(f"No assignment found for participant {participant_id} in experiment {experiment_id}")
            return ""
        
        # Create event
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        
        event = ExperimentEvent(
            event_id=event_id,
            experiment_id=experiment_id,
            participant_id=participant_id,
            variant_id=assignment.variant_id,
            metric_id=metric_id,
            event_timestamp=event_timestamp or datetime.now(),
            event_value=value,
            organization_id=experiment.organization_id,
            properties=properties or {}
        )
        
        self.events[experiment_id].append(event)
        
        # Store in time-series database for analysis
        self._store_event_in_timeseries(event)
        
        return event_id
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get current status and progress of an experiment
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Experiment status information
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        assignments = self.assignments[experiment_id]
        events = self.events[experiment_id]
        
        # Calculate progress metrics
        total_required_sample = (experiment.configuration.sample_size_per_variant or 100) * len(experiment.variants)
        sample_progress = min(experiment.total_participants / total_required_sample, 1.0) if total_required_sample > 0 else 0
        
        # Time progress
        if experiment.start_date and experiment.end_date:
            total_duration = (experiment.end_date - experiment.start_date).total_seconds()
            elapsed_duration = (datetime.now() - experiment.start_date).total_seconds()
            time_progress = min(elapsed_duration / total_duration, 1.0) if total_duration > 0 else 0
        else:
            time_progress = 0
        
        # Variant breakdown
        variant_breakdown = {}
        for variant in experiment.variants:
            variant_participants = experiment.variant_participants.get(variant.variant_id, 0)
            variant_events = len([e for e in events if e.variant_id == variant.variant_id])
            
            variant_breakdown[variant.variant_id] = {
                'name': variant.name,
                'participants': variant_participants,
                'events': variant_events,
                'allocation': variant.traffic_allocation,
                'actual_allocation': variant_participants / max(experiment.total_participants, 1)
            }
        
        return {
            'experiment_id': experiment_id,
            'name': experiment.name,
            'status': experiment.status.value,
            'type': experiment.experiment_type.value,
            'start_date': experiment.start_date.isoformat() if experiment.start_date else None,
            'end_date': experiment.end_date.isoformat() if experiment.end_date else None,
            'total_participants': experiment.total_participants,
            'total_events': len(events),
            'sample_progress': sample_progress,
            'time_progress': time_progress,
            'variant_breakdown': variant_breakdown,
            'metrics_count': len(experiment.metrics),
            'runtime_days': (datetime.now() - experiment.start_date).days if experiment.start_date else 0,
            'is_significant': self._check_statistical_significance(experiment_id) if experiment.status == ExperimentStatus.RUNNING else False
        }
    
    def stop_experiment(self, experiment_id: str, reason: str = "") -> bool:
        """
        Stop a running experiment
        
        Args:
            experiment_id: Experiment identifier
            reason: Reason for stopping
            
        Returns:
            Success status
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.RUNNING:
            return False
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.actual_end_date = datetime.now()
        
        if reason:
            experiment.metadata['stop_reason'] = reason
        
        logger.info(f"Stopped experiment {experiment_id}: {reason}")
        return True
    
    def _calculate_required_sample_size(self, metric: ExperimentMetric, 
                                      config: ExperimentConfiguration) -> int:
        """Calculate required sample size per variant"""
        # Simplified sample size calculation
        # In practice, this would use more sophisticated power analysis
        
        effect_size = metric.minimum_detectable_effect
        alpha = config.significance_level
        power = config.statistical_power
        
        # Cohen's formula approximation for binary metrics
        if metric.metric_type == MetricType.BINARY:
            # Assuming baseline conversion rate of 10%
            baseline_rate = 0.1
            improved_rate = baseline_rate * (1 + effect_size)
            
            # Simplified calculation
            sample_size = int(16 * ((baseline_rate * (1 - baseline_rate) + 
                                  improved_rate * (1 - improved_rate)) / 
                                 (improved_rate - baseline_rate) ** 2))
        else:
            # For continuous metrics, assume standardized effect size
            sample_size = int(16 / (effect_size ** 2))
        
        # Apply safety margin
        return max(sample_size, 100)
    
    def _assign_variant(self, experiment: Experiment, participant_id: str,
                       participant_attributes: Optional[Dict[str, Any]]) -> Optional[str]:
        """Assign participant to variant using consistent hashing"""
        # Create hash input
        hash_input = f"{experiment.experiment_id}:{participant_id}:{self.hash_seed}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Normalize to 0-1
        normalized_hash = (hash_value % 10000) / 10000.0
        
        # Assign based on cumulative traffic allocation
        cumulative_allocation = 0
        for variant in experiment.variants:
            cumulative_allocation += variant.traffic_allocation
            if normalized_hash <= cumulative_allocation:
                return variant.variant_id
        
        # Fallback to last variant
        return experiment.variants[-1].variant_id if experiment.variants else None

# Additional helper methods would continue here...

# Global experiment manager instance
experiment_manager = ExperimentManager()

def get_experiment_manager() -> ExperimentManager:
    """Get the global experiment manager"""
    return experiment_manager

# Convenience functions
def create_experiment(name: str, description: str, organization_id: str, owner: str) -> str:
    """Create a new A/B test experiment"""
    manager = get_experiment_manager()
    return manager.create_experiment(name, description, organization_id, owner)

def assign_participant(experiment_id: str, participant_id: str, organization_id: str) -> Optional[str]:
    """Assign participant to experiment variant"""
    manager = get_experiment_manager()
    return manager.assign_participant(experiment_id, participant_id, organization_id)

def track_conversion(experiment_id: str, participant_id: str, metric_id: str, value: bool) -> str:
    """Track a conversion event"""
    manager = get_experiment_manager()
    return manager.track_event(experiment_id, participant_id, metric_id, value)