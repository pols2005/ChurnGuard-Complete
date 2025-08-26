# ChurnGuard Predictive Customer Lifetime Value System
# Epic 4 Phase 4 - Customer Intelligence Tools

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict
import math

from .time_series_db import get_time_series_db
from .statistical_analysis import get_stats_service
from .customer_journey import get_journey_mapper, JourneyStage
from .behavioral_analysis import get_behavior_engine, BehaviorSegment

logger = logging.getLogger(__name__)

class LTVModelType(Enum):
    SIMPLE_AVERAGE = "simple_average"
    COHORT_BASED = "cohort_based"
    BEHAVIORAL_PREDICTIVE = "behavioral_predictive"
    MACHINE_LEARNING = "machine_learning"
    PROBABILISTIC = "probabilistic"
    ENSEMBLE = "ensemble"

class ValueComponent(Enum):
    SUBSCRIPTION_REVENUE = "subscription_revenue"
    TRANSACTION_FEES = "transaction_fees"
    UPSELL_REVENUE = "upsell_revenue"
    REFERRAL_VALUE = "referral_value"
    DATA_VALUE = "data_value"
    SUPPORT_COSTS = "support_costs"
    ACQUISITION_COSTS = "acquisition_costs"

class LTVSegment(Enum):
    VERY_HIGH_VALUE = "very_high_value"      # Top 5%
    HIGH_VALUE = "high_value"                # Top 20%
    MEDIUM_VALUE = "medium_value"            # Middle 60%
    LOW_VALUE = "low_value"                  # Bottom 20%
    NEGATIVE_VALUE = "negative_value"        # Loss-generating customers

@dataclass
class LTVPrediction:
    """Customer lifetime value prediction"""
    customer_id: str
    organization_id: str
    prediction_date: datetime
    model_type: LTVModelType
    predicted_ltv: float
    confidence_interval: Tuple[float, float]
    confidence_score: float
    time_horizon_months: int
    value_components: Dict[ValueComponent, float]
    risk_factors: Dict[str, float]
    ltv_segment: LTVSegment
    contributing_factors: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LTVCohortAnalysis:
    """Cohort-based LTV analysis"""
    organization_id: str
    cohort_definition: str
    cohort_date: datetime
    customer_count: int
    periods_tracked: int
    revenue_by_period: List[float]
    cumulative_ltv: List[float]
    retention_rates: List[float]
    average_ltv: float
    ltv_percentiles: Dict[str, float]
    projected_ltv: float
    maturity_months: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LTVInsight:
    """Actionable insight about customer lifetime value"""
    insight_id: str
    organization_id: str
    insight_type: str
    title: str
    description: str
    affected_customers: int
    potential_value_impact: float
    confidence: float
    recommendations: List[str]
    data: Dict[str, Any]
    created_at: datetime

class CustomerLTVPredictor:
    """
    Advanced customer lifetime value prediction system
    
    Features:
    - Multiple LTV prediction models (behavioral, cohort, ML-based)
    - Real-time LTV score updates based on customer behavior
    - Value component breakdown (revenue, costs, referral value)
    - Risk-adjusted LTV calculations
    - Cohort-based LTV analysis and benchmarking
    - LTV optimization recommendations
    - Integration with customer journey and behavioral analysis
    - Probabilistic LTV modeling with uncertainty quantification
    """
    
    def __init__(self):
        self.ts_db = get_time_series_db()
        self.stats_service = get_stats_service()
        self.journey_mapper = get_journey_mapper()
        self.behavior_engine = get_behavior_engine()
        
        # LTV calculation parameters
        self.ltv_parameters = self._load_ltv_parameters()
        self.value_weights = self._load_value_weights()
        self.discount_rates = self._load_discount_rates()
        
        # Prediction models cache
        self.model_cache: Dict[str, Any] = {}
        self.prediction_cache: Dict[str, LTVPrediction] = {}
        
        # Cohort analysis cache
        self.cohort_cache: Dict[str, List[LTVCohortAnalysis]] = {}
        
    def predict_customer_ltv(self, customer_id: str, organization_id: str,
                           model_type: LTVModelType = LTVModelType.ENSEMBLE,
                           time_horizon_months: int = 24) -> LTVPrediction:
        """
        Predict customer lifetime value using specified model
        
        Args:
            customer_id: Customer identifier
            organization_id: Organization identifier
            model_type: LTV prediction model to use
            time_horizon_months: Prediction time horizon
            
        Returns:
            LTVPrediction with detailed value breakdown and confidence
        """
        cache_key = f"{customer_id}:{organization_id}:{model_type.value}:{time_horizon_months}"
        if cache_key in self.prediction_cache:
            prediction = self.prediction_cache[cache_key]
            if (datetime.now() - prediction.prediction_date).hours < 6:
                return prediction
        
        # Get customer data
        customer_data = self._collect_customer_ltv_data(customer_id, organization_id)
        
        if not customer_data:
            return self._create_default_ltv_prediction(customer_id, organization_id, model_type)
        
        # Apply different LTV models
        if model_type == LTVModelType.SIMPLE_AVERAGE:
            ltv_result = self._calculate_simple_average_ltv(customer_data, time_horizon_months)
        elif model_type == LTVModelType.COHORT_BASED:
            ltv_result = self._calculate_cohort_based_ltv(customer_data, organization_id, time_horizon_months)
        elif model_type == LTVModelType.BEHAVIORAL_PREDICTIVE:
            ltv_result = self._calculate_behavioral_ltv(customer_data, time_horizon_months)
        elif model_type == LTVModelType.PROBABILISTIC:
            ltv_result = self._calculate_probabilistic_ltv(customer_data, time_horizon_months)
        elif model_type == LTVModelType.ENSEMBLE:
            ltv_result = self._calculate_ensemble_ltv(customer_data, organization_id, time_horizon_months)
        else:
            ltv_result = self._calculate_simple_average_ltv(customer_data, time_horizon_months)
        
        # Break down value components
        value_components = self._calculate_value_components(customer_data, ltv_result['base_ltv'])
        
        # Assess risk factors
        risk_factors = self._assess_ltv_risk_factors(customer_data)
        
        # Apply risk adjustment
        risk_adjusted_ltv = self._apply_risk_adjustment(ltv_result['base_ltv'], risk_factors)
        
        # Determine LTV segment
        ltv_segment = self._determine_ltv_segment(risk_adjusted_ltv, organization_id)
        
        # Generate contributing factors and recommendations
        contributing_factors = self._identify_ltv_contributing_factors(customer_data, ltv_result)
        recommendations = self._generate_ltv_recommendations(
            customer_data, risk_adjusted_ltv, ltv_segment, contributing_factors
        )
        
        prediction = LTVPrediction(
            customer_id=customer_id,
            organization_id=organization_id,
            prediction_date=datetime.now(),
            model_type=model_type,
            predicted_ltv=risk_adjusted_ltv,
            confidence_interval=ltv_result.get('confidence_interval', (risk_adjusted_ltv * 0.7, risk_adjusted_ltv * 1.3)),
            confidence_score=ltv_result.get('confidence_score', 0.75),
            time_horizon_months=time_horizon_months,
            value_components=value_components,
            risk_factors=risk_factors,
            ltv_segment=ltv_segment,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
            metadata={
                'model_details': ltv_result.get('model_details', {}),
                'calculation_date': datetime.now().isoformat(),
                'data_quality_score': customer_data.get('data_quality_score', 0.8)
            }
        )
        
        # Cache the prediction
        self.prediction_cache[cache_key] = prediction
        
        return prediction
    
    def analyze_ltv_cohorts(self, organization_id: str,
                          cohort_definitions: Optional[List[str]] = None,
                          lookback_months: int = 12) -> List[LTVCohortAnalysis]:
        """
        Analyze LTV by customer cohorts
        
        Args:
            organization_id: Organization identifier
            cohort_definitions: List of cohort criteria (None for default cohorts)
            lookback_months: How far back to analyze cohorts
            
        Returns:
            List of cohort LTV analyses
        """
        cache_key = f"{organization_id}:{lookback_months}"
        if cache_key in self.cohort_cache:
            cohorts = self.cohort_cache[cache_key]
            if cohorts and (datetime.now() - cohorts[0].cohort_date).hours < 12:
                return cohorts
        
        if cohort_definitions is None:
            cohort_definitions = [
                'monthly_signup', 'quarterly_signup', 'acquisition_channel',
                'initial_plan_type', 'geographic_region'
            ]
        
        cohort_analyses = []
        
        for cohort_def in cohort_definitions:
            try:
                cohort_data = self._get_cohort_data(organization_id, cohort_def, lookback_months)
                
                for cohort_name, customers in cohort_data.items():
                    if len(customers) < 10:  # Skip small cohorts
                        continue
                    
                    analysis = self._analyze_cohort_ltv(
                        customers, cohort_name, cohort_def, organization_id
                    )
                    cohort_analyses.append(analysis)
                    
            except Exception as e:
                logger.error(f"Error analyzing cohort {cohort_def}: {e}")
        
        # Sort by customer count and average LTV
        cohort_analyses.sort(key=lambda c: (c.customer_count, c.average_ltv), reverse=True)
        
        # Cache the results
        self.cohort_cache[cache_key] = cohort_analyses
        
        return cohort_analyses
    
    def generate_ltv_optimization_insights(self, organization_id: str) -> List[LTVInsight]:
        """
        Generate insights for optimizing customer lifetime value
        
        Args:
            organization_id: Organization identifier
            
        Returns:
            List of actionable LTV optimization insights
        """
        insights = []
        
        # Get LTV data for analysis
        customer_ltvs = self._get_organization_ltv_data(organization_id)
        cohort_analyses = self.analyze_ltv_cohorts(organization_id)
        
        # Generate different types of insights
        
        # 1. Segment-based insights
        segment_insights = self._generate_segment_ltv_insights(customer_ltvs, organization_id)
        insights.extend(segment_insights)
        
        # 2. Cohort performance insights
        cohort_insights = self._generate_cohort_ltv_insights(cohort_analyses, organization_id)
        insights.extend(cohort_insights)
        
        # 3. Value driver insights
        driver_insights = self._generate_value_driver_insights(customer_ltvs, organization_id)
        insights.extend(driver_insights)
        
        # 4. Risk factor insights
        risk_insights = self._generate_risk_factor_insights(customer_ltvs, organization_id)
        insights.extend(risk_insights)
        
        # 5. Optimization opportunity insights
        optimization_insights = self._generate_optimization_opportunity_insights(
            customer_ltvs, cohort_analyses, organization_id
        )
        insights.extend(optimization_insights)
        
        # Sort by potential impact
        insights.sort(key=lambda i: (i.potential_value_impact, i.confidence), reverse=True)
        
        return insights[:15]  # Return top 15 insights
    
    def calculate_customer_portfolio_value(self, organization_id: str,
                                         segment_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate total portfolio value and distribution
        
        Args:
            organization_id: Organization identifier
            segment_filters: Optional filters for customer segments
            
        Returns:
            Portfolio value analysis with breakdowns
        """
        # Get all customer LTV predictions
        customer_ltvs = self._get_organization_ltv_data(organization_id, segment_filters)
        
        if not customer_ltvs:
            return {'total_portfolio_value': 0, 'customer_count': 0}
        
        # Calculate aggregate metrics
        total_portfolio_value = sum(ltv['predicted_ltv'] for ltv in customer_ltvs)
        customer_count = len(customer_ltvs)
        average_ltv = total_portfolio_value / customer_count
        
        # Value distribution analysis
        ltv_values = [ltv['predicted_ltv'] for ltv in customer_ltvs]
        value_percentiles = {
            'p10': np.percentile(ltv_values, 10),
            'p25': np.percentile(ltv_values, 25),
            'p50': np.percentile(ltv_values, 50),
            'p75': np.percentile(ltv_values, 75),
            'p90': np.percentile(ltv_values, 90),
            'p99': np.percentile(ltv_values, 99)
        }
        
        # Segment breakdown
        segment_breakdown = defaultdict(lambda: {'count': 0, 'total_value': 0})
        for ltv in customer_ltvs:
            segment = ltv.get('ltv_segment', 'unknown')
            segment_breakdown[segment]['count'] += 1
            segment_breakdown[segment]['total_value'] += ltv['predicted_ltv']
        
        # Risk-adjusted portfolio value
        risk_adjusted_value = sum(
            ltv['predicted_ltv'] * (1 - ltv.get('risk_score', 0.2))
            for ltv in customer_ltvs
        )
        
        # Value concentration analysis
        top_20_percent = sorted(ltv_values, reverse=True)[:int(len(ltv_values) * 0.2)]
        value_concentration = sum(top_20_percent) / total_portfolio_value if total_portfolio_value > 0 else 0
        
        return {
            'organization_id': organization_id,
            'calculation_date': datetime.now().isoformat(),
            'total_portfolio_value': total_portfolio_value,
            'risk_adjusted_portfolio_value': risk_adjusted_value,
            'customer_count': customer_count,
            'average_ltv': average_ltv,
            'median_ltv': value_percentiles['p50'],
            'value_percentiles': value_percentiles,
            'segment_breakdown': dict(segment_breakdown),
            'value_concentration': value_concentration,
            'portfolio_quality_score': self._calculate_portfolio_quality_score(customer_ltvs),
            'growth_potential': self._estimate_portfolio_growth_potential(customer_ltvs),
            'recommendations': self._generate_portfolio_recommendations(customer_ltvs)
        }
    
    def _collect_customer_ltv_data(self, customer_id: str, organization_id: str) -> Dict[str, Any]:
        """Collect all data needed for LTV calculation"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365)  # 1 year of data
        
        customer_data = {
            'customer_id': customer_id,
            'organization_id': organization_id,
            'collection_date': end_time,
            'revenue_history': [],
            'transaction_history': [],
            'subscription_data': {},
            'behavior_data': {},
            'journey_data': {},
            'demographic_data': {},
            'engagement_metrics': {},
            'data_quality_score': 1.0
        }
        
        # Collect revenue data
        try:
            revenue_data = self.ts_db.query(
                metric_name='customer_revenue',
                organization_id=organization_id,
                start_time=start_time,
                end_time=end_time,
                tags={'customer_id': customer_id}
            )
            
            if not revenue_data.empty:
                customer_data['revenue_history'] = [
                    {
                        'date': pd.to_datetime(row['timestamp']).date(),
                        'amount': row['value'],
                        'type': row.get('revenue_type', 'subscription')
                    }
                    for _, row in revenue_data.iterrows()
                ]
        except Exception as e:
            logger.warning(f"Error collecting revenue data: {e}")
            customer_data['data_quality_score'] *= 0.8
        
        # Get behavioral analysis
        try:
            behavior_profile = self.behavior_engine.analyze_customer_behavior(
                customer_id, organization_id
            )
            customer_data['behavior_data'] = {
                'engagement_score': behavior_profile.engagement_score,
                'usage_intensity': behavior_profile.usage_intensity,
                'feature_adoption_rate': behavior_profile.feature_adoption_rate,
                'behavior_segment': behavior_profile.behavior_segment.value,
                'churn_risk': max(behavior_profile.risk_indicators.values()) if behavior_profile.risk_indicators else 0.3
            }
        except Exception as e:
            logger.warning(f"Error getting behavior data: {e}")
            customer_data['data_quality_score'] *= 0.9
        
        # Get journey data
        try:
            journey = self.journey_mapper.map_customer_journey(customer_id, organization_id)
            customer_data['journey_data'] = {
                'current_stage': journey.current_stage.value,
                'journey_score': journey.journey_score,
                'predicted_ltv': journey.predicted_ltv,
                'total_touchpoints': len(journey.touchpoints),
                'journey_duration_days': (journey.journey_end - journey.journey_start).days if journey.journey_end else 0
            }
        except Exception as e:
            logger.warning(f"Error getting journey data: {e}")
            customer_data['data_quality_score'] *= 0.9
        
        return customer_data
    
    def _calculate_behavioral_ltv(self, customer_data: Dict[str, Any], 
                                time_horizon_months: int) -> Dict[str, Any]:
        """Calculate LTV based on behavioral patterns"""
        behavior_data = customer_data.get('behavior_data', {})
        journey_data = customer_data.get('journey_data', {})
        revenue_history = customer_data.get('revenue_history', [])
        
        # Calculate base monthly value
        if revenue_history:
            monthly_revenues = defaultdict(float)
            for revenue in revenue_history:
                month_key = f"{revenue['date'].year}-{revenue['date'].month:02d}"
                monthly_revenues[month_key] += revenue['amount']
            
            if monthly_revenues:
                base_monthly_value = np.mean(list(monthly_revenues.values()))
            else:
                base_monthly_value = 100.0  # Default assumption
        else:
            base_monthly_value = 100.0
        
        # Apply behavioral multipliers
        engagement_multiplier = 1 + (behavior_data.get('engagement_score', 50) - 50) / 100
        usage_multiplier = 1 + behavior_data.get('usage_intensity', 0.5)
        adoption_multiplier = 1 + behavior_data.get('feature_adoption_rate', 0.3)
        
        # Apply journey stage multiplier
        stage_multipliers = {
            'awareness': 0.2,
            'consideration': 0.4,
            'trial': 0.6,
            'onboarding': 0.8,
            'active_use': 1.2,
            'expansion': 1.8,
            'renewal': 1.5,
            'at_risk': 0.4,
            'churned': 0.0
        }
        stage_multiplier = stage_multipliers.get(journey_data.get('current_stage', 'active_use'), 1.0)
        
        # Calculate adjusted monthly value
        adjusted_monthly_value = (
            base_monthly_value * 
            engagement_multiplier * 
            usage_multiplier * 
            adoption_multiplier * 
            stage_multiplier
        )
        
        # Apply churn risk discount
        churn_risk = behavior_data.get('churn_risk', 0.3)
        retention_probability = 1 - churn_risk
        
        # Calculate expected lifetime (months)
        if retention_probability > 0.9:
            expected_lifetime_months = min(time_horizon_months, 36)
        elif retention_probability > 0.7:
            expected_lifetime_months = min(time_horizon_months, 24)
        elif retention_probability > 0.5:
            expected_lifetime_months = min(time_horizon_months, 12)
        else:
            expected_lifetime_months = min(time_horizon_months, 6)
        
        # Apply discount rate for future value
        monthly_discount_rate = 0.01  # 1% monthly discount
        
        # Calculate present value of future cash flows
        ltv = 0
        for month in range(1, expected_lifetime_months + 1):
            month_retention = retention_probability ** month
            month_value = adjusted_monthly_value * month_retention
            discounted_value = month_value / ((1 + monthly_discount_rate) ** month)
            ltv += discounted_value
        
        # Calculate confidence based on data quality and model assumptions
        confidence_score = (
            customer_data.get('data_quality_score', 0.8) * 0.4 +
            (1 - churn_risk) * 0.3 +
            min(len(revenue_history) / 12, 1.0) * 0.3
        )
        
        return {
            'base_ltv': ltv,
            'confidence_score': confidence_score,
            'confidence_interval': (ltv * 0.6, ltv * 1.4),
            'model_details': {
                'base_monthly_value': base_monthly_value,
                'adjusted_monthly_value': adjusted_monthly_value,
                'expected_lifetime_months': expected_lifetime_months,
                'retention_probability': retention_probability,
                'engagement_multiplier': engagement_multiplier,
                'usage_multiplier': usage_multiplier,
                'adoption_multiplier': adoption_multiplier,
                'stage_multiplier': stage_multiplier
            }
        }
    
    def _calculate_ensemble_ltv(self, customer_data: Dict[str, Any],
                              organization_id: str, time_horizon_months: int) -> Dict[str, Any]:
        """Calculate LTV using ensemble of multiple models"""
        models_results = []
        
        # Simple average model
        try:
            simple_result = self._calculate_simple_average_ltv(customer_data, time_horizon_months)
            models_results.append(('simple', simple_result, 0.2))
        except Exception as e:
            logger.warning(f"Simple model failed: {e}")
        
        # Behavioral model
        try:
            behavioral_result = self._calculate_behavioral_ltv(customer_data, time_horizon_months)
            models_results.append(('behavioral', behavioral_result, 0.4))
        except Exception as e:
            logger.warning(f"Behavioral model failed: {e}")
        
        # Cohort model
        try:
            cohort_result = self._calculate_cohort_based_ltv(customer_data, organization_id, time_horizon_months)
            models_results.append(('cohort', cohort_result, 0.3))
        except Exception as e:
            logger.warning(f"Cohort model failed: {e}")
        
        # Probabilistic model
        try:
            prob_result = self._calculate_probabilistic_ltv(customer_data, time_horizon_months)
            models_results.append(('probabilistic', prob_result, 0.1))
        except Exception as e:
            logger.warning(f"Probabilistic model failed: {e}")
        
        if not models_results:
            # Fallback to simple calculation
            return self._calculate_simple_average_ltv(customer_data, time_horizon_months)
        
        # Weighted ensemble
        total_weight = sum(weight for _, _, weight in models_results)
        weighted_ltv = sum(
            result['base_ltv'] * weight for _, result, weight in models_results
        ) / total_weight
        
        # Average confidence
        avg_confidence = sum(
            result['confidence_score'] * weight for _, result, weight in models_results
        ) / total_weight
        
        # Calculate ensemble confidence interval
        ltv_values = [result['base_ltv'] for _, result, _ in models_results]
        ensemble_std = np.std(ltv_values)
        confidence_interval = (
            weighted_ltv - 1.96 * ensemble_std,
            weighted_ltv + 1.96 * ensemble_std
        )
        
        return {
            'base_ltv': weighted_ltv,
            'confidence_score': avg_confidence,
            'confidence_interval': confidence_interval,
            'model_details': {
                'ensemble_models': [name for name, _, _ in models_results],
                'model_weights': {name: weight for name, _, weight in models_results},
                'model_results': {name: result['base_ltv'] for name, result, _ in models_results},
                'ensemble_std': ensemble_std
            }
        }
    
    def _load_ltv_parameters(self) -> Dict[str, Any]:
        """Load LTV calculation parameters"""
        return {
            'default_monthly_revenue': 100.0,
            'default_retention_rate': 0.85,
            'discount_rate_monthly': 0.01,
            'max_projection_months': 36,
            'min_data_points_for_prediction': 3,
            'confidence_threshold': 0.6
        }
    
    def _load_value_weights(self) -> Dict[ValueComponent, float]:
        """Load value component weights"""
        return {
            ValueComponent.SUBSCRIPTION_REVENUE: 1.0,
            ValueComponent.TRANSACTION_FEES: 0.3,
            ValueComponent.UPSELL_REVENUE: 1.2,
            ValueComponent.REFERRAL_VALUE: 0.5,
            ValueComponent.DATA_VALUE: 0.1,
            ValueComponent.SUPPORT_COSTS: -0.2,
            ValueComponent.ACQUISITION_COSTS: -0.3
        }
    
    def _calculate_value_components(self, customer_data: Dict[str, Any], 
                                  base_ltv: float) -> Dict[ValueComponent, float]:
        """Break down LTV into value components"""
        components = {}
        
        # Primary revenue (80% of base LTV)
        components[ValueComponent.SUBSCRIPTION_REVENUE] = base_ltv * 0.8
        
        # Transaction fees (estimated from behavior)
        usage_intensity = customer_data.get('behavior_data', {}).get('usage_intensity', 0.5)
        components[ValueComponent.TRANSACTION_FEES] = base_ltv * 0.1 * usage_intensity
        
        # Upsell potential (based on feature adoption and engagement)
        feature_adoption = customer_data.get('behavior_data', {}).get('feature_adoption_rate', 0.3)
        engagement_score = customer_data.get('behavior_data', {}).get('engagement_score', 50)
        upsell_multiplier = (feature_adoption + engagement_score / 100) / 2
        components[ValueComponent.UPSELL_REVENUE] = base_ltv * 0.15 * upsell_multiplier
        
        # Referral value (based on engagement and satisfaction indicators)
        referral_potential = min(engagement_score / 100, 0.8) if engagement_score else 0.3
        components[ValueComponent.REFERRAL_VALUE] = base_ltv * 0.05 * referral_potential
        
        # Support costs (higher for customers with more support interactions)
        # This would be negative value
        support_interaction_level = 0.3  # This would come from support data
        components[ValueComponent.SUPPORT_COSTS] = -base_ltv * 0.1 * support_interaction_level
        
        return components

    def _determine_ltv_segment(self, ltv_value: float, organization_id: str) -> LTVSegment:
        """Determine LTV segment for a customer"""
        # These thresholds would typically be organization-specific
        # and derived from analyzing the customer base distribution
        
        if ltv_value >= 5000:
            return LTVSegment.VERY_HIGH_VALUE
        elif ltv_value >= 2000:
            return LTVSegment.HIGH_VALUE
        elif ltv_value >= 500:
            return LTVSegment.MEDIUM_VALUE
        elif ltv_value >= 0:
            return LTVSegment.LOW_VALUE
        else:
            return LTVSegment.NEGATIVE_VALUE

# Additional helper methods would continue here...

# Global LTV predictor instance
ltv_predictor = CustomerLTVPredictor()

def get_ltv_predictor() -> CustomerLTVPredictor:
    """Get the global customer LTV predictor"""
    return ltv_predictor

# Convenience functions
def predict_customer_ltv(customer_id: str, organization_id: str) -> LTVPrediction:
    """Predict customer lifetime value"""
    predictor = get_ltv_predictor()
    return predictor.predict_customer_ltv(customer_id, organization_id)

def analyze_ltv_cohorts(organization_id: str) -> List[LTVCohortAnalysis]:
    """Analyze LTV by customer cohorts"""
    predictor = get_ltv_predictor()
    return predictor.analyze_ltv_cohorts(organization_id)

def calculate_portfolio_value(organization_id: str) -> Dict[str, Any]:
    """Calculate total customer portfolio value"""
    predictor = get_ltv_predictor()
    return predictor.calculate_customer_portfolio_value(organization_id)