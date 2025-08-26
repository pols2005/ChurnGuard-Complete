# ChurnGuard Statistical Testing Engine for A/B Tests
# Epic 4 Phase 5 - A/B Testing Framework

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict
import math
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu, beta
import warnings

from .experiment_management import get_experiment_manager, Experiment, ExperimentEvent, MetricType
from .statistical_analysis import get_stats_service

logger = logging.getLogger(__name__)

class TestType(Enum):
    TTEST = "t_test"
    WELCH_TTEST = "welch_t_test"
    MANN_WHITNEY = "mann_whitney_u"
    CHI_SQUARE = "chi_square"
    FISHER_EXACT = "fisher_exact"
    PROPORTIONS_Z_TEST = "proportions_z_test"
    BAYESIAN = "bayesian"
    BOOTSTRAP = "bootstrap"

class TestResult(Enum):
    SIGNIFICANT = "significant"
    NOT_SIGNIFICANT = "not_significant"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENT_DATA = "insufficient_data"

class EffectDirection(Enum):
    POSITIVE = "positive"  # Treatment > Control
    NEGATIVE = "negative"  # Treatment < Control
    NO_EFFECT = "no_effect"

@dataclass
class StatisticalTestResult:
    """Results of a statistical test"""
    test_type: TestType
    metric_name: str
    control_variant: str
    treatment_variant: str
    
    # Sample statistics
    control_sample_size: int
    treatment_sample_size: int
    control_mean: float
    treatment_mean: float
    control_std: Optional[float] = None
    treatment_std: Optional[float] = None
    
    # Test results
    test_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    effect_direction: EffectDirection
    
    # Interpretation
    is_significant: bool
    significance_level: float
    power: float
    minimum_detectable_effect: float
    
    # Additional metrics
    relative_improvement: float
    absolute_improvement: float
    
    # Bayesian results (if applicable)
    probability_better: Optional[float] = None
    credible_interval: Optional[Tuple[float, float]] = None
    
    # Metadata
    test_date: datetime = field(default_factory=datetime.now)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentAnalysis:
    """Complete analysis of an experiment"""
    experiment_id: str
    analysis_date: datetime
    experiment_status: str
    runtime_days: int
    
    # Overall statistics
    total_participants: int
    total_events: int
    
    # Primary metric results
    primary_metric_results: List[StatisticalTestResult]
    secondary_metric_results: List[StatisticalTestResult]
    
    # Guardrail metrics
    guardrail_violations: List[Dict[str, Any]]
    
    # Overall conclusions
    overall_conclusion: TestResult
    recommended_action: str
    confidence_score: float
    
    # Sample size and power analysis
    sample_size_adequacy: Dict[str, Any]
    power_analysis: Dict[str, Any]
    
    # Segment analysis
    segment_results: Dict[str, List[StatisticalTestResult]]
    
    # Recommendations
    recommendations: List[str]
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class StatisticalTestingEngine:
    """
    Advanced statistical testing engine for A/B test analysis
    
    Features:
    - Multiple statistical tests (frequentist and Bayesian)
    - Power analysis and sample size calculations
    - Sequential testing with early stopping
    - Multiple comparisons correction
    - Effect size calculations and practical significance
    - Confidence intervals and credible intervals
    - Segment-based analysis
    - Guardrail monitoring
    - False discovery rate control
    """
    
    def __init__(self):
        self.experiment_manager = get_experiment_manager()
        self.stats_service = get_stats_service()
        
        # Default testing parameters
        self.default_alpha = 0.05
        self.default_power = 0.8
        self.min_sample_size = 100
        
        # Multiple comparisons adjustments
        self.multiple_comparisons_methods = {
            'bonferroni': self._bonferroni_correction,
            'holm': self._holm_correction,
            'benjamini_hochberg': self._benjamini_hochberg_correction
        }
        
    def analyze_experiment(self, experiment_id: str, 
                         significance_level: float = 0.05,
                         include_segments: bool = True,
                         correction_method: Optional[str] = 'benjamini_hochberg') -> ExperimentAnalysis:
        """
        Perform comprehensive statistical analysis of an experiment
        
        Args:
            experiment_id: Experiment identifier
            significance_level: Alpha level for hypothesis testing
            include_segments: Whether to include segment analysis
            correction_method: Method for multiple comparisons correction
            
        Returns:
            Complete experiment analysis with statistical results
        """
        if experiment_id not in self.experiment_manager.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiment_manager.experiments[experiment_id]
        events = self.experiment_manager.events[experiment_id]
        
        # Analyze each metric
        primary_results = []
        secondary_results = []
        
        for metric in experiment.metrics:
            metric_events = [e for e in events if e.metric_id == metric.metric_id]
            
            if len(metric_events) < self.min_sample_size:
                continue
            
            # Test each treatment variant against control
            control_variant = next((v for v in experiment.variants if v.is_control), experiment.variants[0])
            
            for variant in experiment.variants:
                if variant.variant_id == control_variant.variant_id:
                    continue
                
                test_result = self._test_metric(
                    metric_events, metric, control_variant.variant_id, 
                    variant.variant_id, significance_level
                )
                
                if metric.is_primary:
                    primary_results.append(test_result)
                else:
                    secondary_results.append(test_result)
        
        # Apply multiple comparisons correction
        if correction_method and (primary_results or secondary_results):
            all_results = primary_results + secondary_results
            corrected_results = self._apply_multiple_comparisons_correction(
                all_results, correction_method
            )
            
            # Update significance flags
            for i, result in enumerate(corrected_results):
                if i < len(primary_results):
                    primary_results[i] = result
                else:
                    secondary_results[i - len(primary_results)] = result
        
        # Check guardrail violations
        guardrail_violations = self._check_guardrail_violations(
            experiment, events, significance_level
        )
        
        # Determine overall conclusion
        overall_conclusion = self._determine_overall_conclusion(
            primary_results, secondary_results, guardrail_violations
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            primary_results, secondary_results, experiment
        )
        
        # Power and sample size analysis
        sample_size_adequacy = self._analyze_sample_size_adequacy(experiment, events)
        power_analysis = self._analyze_statistical_power(primary_results, experiment)
        
        # Segment analysis
        segment_results = {}
        if include_segments:
            segment_results = self._analyze_segments(experiment, events, significance_level)
        
        # Generate recommendations
        recommendations = self._generate_analysis_recommendations(
            primary_results, secondary_results, guardrail_violations, 
            sample_size_adequacy, overall_conclusion
        )
        
        # Calculate runtime
        runtime_days = 0
        if experiment.start_date:
            runtime_days = (datetime.now() - experiment.start_date).days
        
        analysis = ExperimentAnalysis(
            experiment_id=experiment_id,
            analysis_date=datetime.now(),
            experiment_status=experiment.status.value,
            runtime_days=runtime_days,
            total_participants=experiment.total_participants,
            total_events=len(events),
            primary_metric_results=primary_results,
            secondary_metric_results=secondary_results,
            guardrail_violations=guardrail_violations,
            overall_conclusion=overall_conclusion,
            recommended_action=self._get_recommended_action(overall_conclusion, guardrail_violations),
            confidence_score=confidence_score,
            sample_size_adequacy=sample_size_adequacy,
            power_analysis=power_analysis,
            segment_results=segment_results,
            recommendations=recommendations,
            metadata={
                'significance_level': significance_level,
                'correction_method': correction_method,
                'analysis_timestamp': datetime.now().isoformat()
            }
        )
        
        return analysis
    
    def perform_sequential_analysis(self, experiment_id: str, 
                                  alpha_spending_function: str = 'obrien_fleming') -> Dict[str, Any]:
        """
        Perform sequential analysis to check for early stopping
        
        Args:
            experiment_id: Experiment identifier  
            alpha_spending_function: Method for controlling Type I error
            
        Returns:
            Sequential analysis results with stopping recommendations
        """
        if experiment_id not in self.experiment_manager.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiment_manager.experiments[experiment_id]
        events = self.experiment_manager.events[experiment_id]
        
        # Get primary metrics only for sequential testing
        primary_metrics = [m for m in experiment.metrics if m.is_primary]
        
        if not primary_metrics:
            return {'error': 'No primary metrics defined for sequential analysis'}
        
        sequential_results = {}
        
        for metric in primary_metrics:
            metric_events = [e for e in events if e.metric_id == metric.metric_id]
            
            # Calculate current test statistics over time
            timeline_results = self._calculate_timeline_statistics(
                metric_events, metric, experiment
            )
            
            # Apply alpha spending function
            stopping_boundaries = self._calculate_stopping_boundaries(
                timeline_results, alpha_spending_function, self.default_alpha
            )
            
            # Check stopping criteria
            stopping_recommendation = self._check_stopping_criteria(
                timeline_results, stopping_boundaries
            )
            
            sequential_results[metric.metric_id] = {
                'metric_name': metric.name,
                'timeline_results': timeline_results,
                'stopping_boundaries': stopping_boundaries,
                'stopping_recommendation': stopping_recommendation,
                'current_p_value': timeline_results[-1]['p_value'] if timeline_results else 1.0,
                'current_effect_size': timeline_results[-1]['effect_size'] if timeline_results else 0.0
            }
        
        # Overall stopping recommendation
        stop_for_efficacy = any(
            r['stopping_recommendation']['stop_for_efficacy'] 
            for r in sequential_results.values()
        )
        stop_for_futility = all(
            r['stopping_recommendation']['stop_for_futility'] 
            for r in sequential_results.values()
        )
        
        return {
            'experiment_id': experiment_id,
            'analysis_date': datetime.now().isoformat(),
            'sequential_results': sequential_results,
            'overall_recommendation': {
                'continue': not (stop_for_efficacy or stop_for_futility),
                'stop_for_efficacy': stop_for_efficacy,
                'stop_for_futility': stop_for_futility,
                'reason': self._get_stopping_reason(stop_for_efficacy, stop_for_futility)
            },
            'next_analysis_date': (datetime.now() + timedelta(days=1)).isoformat()
        }
    
    def calculate_sample_size_requirements(self, baseline_rate: float, 
                                         minimum_detectable_effect: float,
                                         significance_level: float = 0.05,
                                         statistical_power: float = 0.8,
                                         metric_type: MetricType = MetricType.BINARY) -> Dict[str, Any]:
        """
        Calculate required sample size for experiment design
        
        Args:
            baseline_rate: Expected baseline conversion/metric rate
            minimum_detectable_effect: Minimum effect size to detect
            significance_level: Type I error rate
            statistical_power: Statistical power (1 - Type II error rate)
            metric_type: Type of metric being tested
            
        Returns:
            Sample size requirements and power analysis
        """
        if metric_type == MetricType.BINARY:
            # Binary/conversion rate metrics
            control_rate = baseline_rate
            treatment_rate = baseline_rate * (1 + minimum_detectable_effect)
            
            # Use normal approximation for proportions
            pooled_rate = (control_rate + treatment_rate) / 2
            pooled_variance = pooled_rate * (1 - pooled_rate)
            
            # Z-scores for alpha and beta
            z_alpha = stats.norm.ppf(1 - significance_level / 2)
            z_beta = stats.norm.ppf(statistical_power)
            
            # Sample size calculation
            numerator = (z_alpha * math.sqrt(2 * pooled_variance) + 
                        z_beta * math.sqrt(control_rate * (1 - control_rate) + 
                                          treatment_rate * (1 - treatment_rate))) ** 2
            denominator = (treatment_rate - control_rate) ** 2
            
            sample_size_per_variant = int(math.ceil(numerator / denominator))
            
        else:
            # Continuous metrics - use Cohen's formula
            effect_size = minimum_detectable_effect  # Assume standardized effect size
            
            # Degrees of freedom approximation
            z_alpha = stats.norm.ppf(1 - significance_level / 2)
            z_beta = stats.norm.ppf(statistical_power)
            
            sample_size_per_variant = int(math.ceil(
                2 * ((z_alpha + z_beta) / effect_size) ** 2
            ))
        
        total_sample_size = sample_size_per_variant * 2  # Assuming 2 variants
        
        # Calculate runtime estimates
        estimated_runtime = self._estimate_experiment_runtime(
            total_sample_size, baseline_rate
        )
        
        return {
            'sample_size_per_variant': sample_size_per_variant,
            'total_sample_size': total_sample_size,
            'estimated_runtime_days': estimated_runtime['days'],
            'estimated_runtime_weeks': estimated_runtime['weeks'],
            'parameters': {
                'baseline_rate': baseline_rate,
                'minimum_detectable_effect': minimum_detectable_effect,
                'significance_level': significance_level,
                'statistical_power': statistical_power,
                'metric_type': metric_type.value
            },
            'assumptions': [
                f"Equal traffic allocation (50/50 split)",
                f"Baseline {metric_type.value} rate: {baseline_rate:.1%}",
                f"Minimum detectable effect: {minimum_detectable_effect:.1%}",
                f"Two-tailed test with α = {significance_level}",
                f"Statistical power: {statistical_power:.1%}"
            ]
        }
    
    def _test_metric(self, events: List[ExperimentEvent], metric, 
                    control_variant_id: str, treatment_variant_id: str,
                    significance_level: float) -> StatisticalTestResult:
        """Perform statistical test for a specific metric"""
        
        # Separate events by variant
        control_events = [e for e in events if e.variant_id == control_variant_id]
        treatment_events = [e for e in events if e.variant_id == treatment_variant_id]
        
        # Extract values
        control_values = [float(e.event_value) for e in control_events]
        treatment_values = [float(e.event_value) for e in treatment_events]
        
        if len(control_values) < 10 or len(treatment_values) < 10:
            return self._create_insufficient_data_result(
                metric, control_variant_id, treatment_variant_id
            )
        
        # Choose appropriate test based on metric type
        if metric.metric_type == MetricType.BINARY:
            test_result = self._perform_proportions_test(
                control_values, treatment_values, significance_level
            )
            test_type = TestType.PROPORTIONS_Z_TEST
        else:
            # Check assumptions for t-test vs non-parametric test
            if self._check_normality_assumptions(control_values, treatment_values):
                test_result = self._perform_t_test(
                    control_values, treatment_values, significance_level
                )
                test_type = TestType.WELCH_TTEST
            else:
                test_result = self._perform_mann_whitney_test(
                    control_values, treatment_values, significance_level
                )
                test_type = TestType.MANN_WHITNEY
        
        # Calculate effect size
        effect_size = self._calculate_effect_size(
            control_values, treatment_values, metric.metric_type
        )
        
        # Determine effect direction
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)
        
        if treatment_mean > control_mean:
            effect_direction = EffectDirection.POSITIVE
        elif treatment_mean < control_mean:
            effect_direction = EffectDirection.NEGATIVE
        else:
            effect_direction = EffectDirection.NO_EFFECT
        
        # Calculate improvements
        if control_mean > 0:
            relative_improvement = (treatment_mean - control_mean) / control_mean
        else:
            relative_improvement = 0.0
        
        absolute_improvement = treatment_mean - control_mean
        
        # Calculate statistical power
        power = self._calculate_post_hoc_power(
            control_values, treatment_values, significance_level, effect_size
        )
        
        return StatisticalTestResult(
            test_type=test_type,
            metric_name=metric.name,
            control_variant=control_variant_id,
            treatment_variant=treatment_variant_id,
            control_sample_size=len(control_values),
            treatment_sample_size=len(treatment_values),
            control_mean=control_mean,
            treatment_mean=treatment_mean,
            control_std=np.std(control_values, ddof=1) if len(control_values) > 1 else 0,
            treatment_std=np.std(treatment_values, ddof=1) if len(treatment_values) > 1 else 0,
            test_statistic=test_result['statistic'],
            p_value=test_result['p_value'],
            confidence_interval=test_result['confidence_interval'],
            effect_size=effect_size,
            effect_direction=effect_direction,
            is_significant=test_result['p_value'] < significance_level,
            significance_level=significance_level,
            power=power,
            minimum_detectable_effect=metric.minimum_detectable_effect,
            relative_improvement=relative_improvement,
            absolute_improvement=absolute_improvement
        )
    
    def _perform_proportions_test(self, control_values: List[float], 
                                 treatment_values: List[float],
                                 significance_level: float) -> Dict[str, Any]:
        """Perform two-proportion z-test"""
        # Convert to binary if needed
        control_successes = sum(1 for v in control_values if v > 0)
        treatment_successes = sum(1 for v in treatment_values if v > 0)
        
        n1, n2 = len(control_values), len(treatment_values)
        p1, p2 = control_successes / n1, treatment_successes / n2
        
        # Pooled proportion
        p_pool = (control_successes + treatment_successes) / (n1 + n2)
        
        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        
        # Test statistic
        if se > 0:
            z_stat = (p2 - p1) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            z_stat = 0
            p_value = 1.0
        
        # Confidence interval for difference
        se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        z_crit = stats.norm.ppf(1 - significance_level / 2)
        diff = p2 - p1
        
        ci_lower = diff - z_crit * se_diff
        ci_upper = diff + z_crit * se_diff
        
        return {
            'statistic': z_stat,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper)
        }
    
    def _perform_t_test(self, control_values: List[float], 
                       treatment_values: List[float],
                       significance_level: float) -> Dict[str, Any]:
        """Perform Welch's t-test (unequal variances)"""
        statistic, p_value = stats.ttest_ind(
            control_values, treatment_values, equal_var=False
        )
        
        # Calculate confidence interval for difference in means
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)
        
        # Welch-Satterthwaite degrees of freedom
        s1_sq = np.var(control_values, ddof=1)
        s2_sq = np.var(treatment_values, ddof=1)
        n1, n2 = len(control_values), len(treatment_values)
        
        se_diff = math.sqrt(s1_sq/n1 + s2_sq/n2)
        
        # Degrees of freedom
        df = (s1_sq/n1 + s2_sq/n2)**2 / ((s1_sq/n1)**2/(n1-1) + (s2_sq/n2)**2/(n2-1))
        
        t_crit = stats.t.ppf(1 - significance_level / 2, df)
        diff = treatment_mean - control_mean
        
        ci_lower = diff - t_crit * se_diff
        ci_upper = diff + t_crit * se_diff
        
        return {
            'statistic': statistic,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper)
        }

# Additional helper methods would continue here...

# Global statistical testing engine
testing_engine = StatisticalTestingEngine()

def get_testing_engine() -> StatisticalTestingEngine:
    """Get the global statistical testing engine"""
    return testing_engine

# Convenience functions
def analyze_experiment(experiment_id: str) -> ExperimentAnalysis:
    """Analyze A/B test experiment results"""
    engine = get_testing_engine()
    return engine.analyze_experiment(experiment_id)

def check_early_stopping(experiment_id: str) -> Dict[str, Any]:
    """Check if experiment should be stopped early"""
    engine = get_testing_engine()
    return engine.perform_sequential_analysis(experiment_id)