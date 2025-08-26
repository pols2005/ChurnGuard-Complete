# ChurnGuard Customer Journey Mapping System
# Epic 4 Phase 4 - Customer Intelligence Tools

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import networkx as nx

from .time_series_db import get_time_series_db
from .statistical_analysis import get_stats_service

logger = logging.getLogger(__name__)

class TouchpointType(Enum):
    WEBSITE_VISIT = "website_visit"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    SUPPORT_TICKET = "support_ticket"
    PURCHASE = "purchase"
    LOGIN = "login"
    FEATURE_USE = "feature_use"
    SUBSCRIPTION_CHANGE = "subscription_change"
    PAYMENT = "payment"
    CHURN_EVENT = "churn_event"
    REACTIVATION = "reactivation"
    REFERRAL = "referral"
    FEEDBACK = "feedback"
    TRIAL_START = "trial_start"
    TRIAL_END = "trial_end"

class JourneyStage(Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    TRIAL = "trial"
    ONBOARDING = "onboarding"
    ACTIVE_USE = "active_use"
    EXPANSION = "expansion"
    RENEWAL = "renewal"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    REACTIVATION = "reactivation"

@dataclass
class CustomerTouchpoint:
    """Individual customer touchpoint event"""
    id: str
    customer_id: str
    organization_id: str
    touchpoint_type: TouchpointType
    timestamp: datetime
    channel: str
    properties: Dict[str, Any]
    value: Optional[float] = None
    duration: Optional[int] = None  # seconds
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class JourneySegment:
    """A segment of customer journey between two stages"""
    from_stage: JourneyStage
    to_stage: JourneyStage
    touchpoints: List[CustomerTouchpoint]
    duration_days: float
    conversion_rate: float
    average_touchpoint_count: int
    common_paths: List[str]

@dataclass
class CustomerJourney:
    """Complete customer journey representation"""
    customer_id: str
    organization_id: str
    journey_start: datetime
    journey_end: Optional[datetime]
    current_stage: JourneyStage
    touchpoints: List[CustomerTouchpoint]
    stage_transitions: List[Dict[str, Any]]
    journey_score: float
    churn_risk: float
    predicted_ltv: float
    key_moments: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class JourneyInsight:
    """Insight derived from journey analysis"""
    insight_type: str
    title: str
    description: str
    affected_customers: int
    improvement_opportunity: str
    confidence: float
    data: Dict[str, Any]

class CustomerJourneyMapper:
    """
    Advanced customer journey mapping and analysis system
    
    Features:
    - Multi-touchpoint journey reconstruction
    - Stage-based journey segmentation
    - Journey pattern analysis and optimization
    - Predictive journey modeling
    - Journey-based churn prediction
    - Customer experience optimization insights
    """
    
    def __init__(self):
        self.ts_db = get_time_series_db()
        self.stats_service = get_stats_service()
        
        # Journey configuration
        self.stage_definitions = self._load_stage_definitions()
        self.touchpoint_weights = self._load_touchpoint_weights()
        self.transition_rules = self._load_transition_rules()
        
        # Journey analysis cache
        self.journey_cache: Dict[str, CustomerJourney] = {}
        self.pattern_cache: Dict[str, Any] = {}
        
    def map_customer_journey(self, customer_id: str, organization_id: str,
                           lookback_days: int = 365) -> CustomerJourney:
        """
        Map complete customer journey from touchpoint data
        
        Args:
            customer_id: Customer identifier
            organization_id: Organization identifier
            lookback_days: Days to look back for journey data
            
        Returns:
            CustomerJourney object with complete journey mapping
        """
        cache_key = f"{customer_id}:{organization_id}"
        if cache_key in self.journey_cache:
            return self.journey_cache[cache_key]
        
        # Collect all touchpoints for customer
        touchpoints = self._collect_customer_touchpoints(
            customer_id, organization_id, lookback_days
        )
        
        if not touchpoints:
            return self._create_empty_journey(customer_id, organization_id)
        
        # Sort touchpoints chronologically
        touchpoints.sort(key=lambda t: t.timestamp)
        
        # Analyze journey stages and transitions
        stage_transitions = self._analyze_stage_transitions(touchpoints)
        current_stage = self._determine_current_stage(touchpoints, stage_transitions)
        
        # Calculate journey metrics
        journey_score = self._calculate_journey_score(touchpoints, stage_transitions)
        churn_risk = self._calculate_journey_churn_risk(touchpoints, stage_transitions)
        predicted_ltv = self._predict_customer_ltv(touchpoints, stage_transitions)
        
        # Identify key moments
        key_moments = self._identify_key_moments(touchpoints, stage_transitions)
        
        journey = CustomerJourney(
            customer_id=customer_id,
            organization_id=organization_id,
            journey_start=touchpoints[0].timestamp,
            journey_end=touchpoints[-1].timestamp,
            current_stage=current_stage,
            touchpoints=touchpoints,
            stage_transitions=stage_transitions,
            journey_score=journey_score,
            churn_risk=churn_risk,
            predicted_ltv=predicted_ltv,
            key_moments=key_moments,
            metadata={
                'total_touchpoints': len(touchpoints),
                'journey_duration_days': (touchpoints[-1].timestamp - touchpoints[0].timestamp).days,
                'unique_channels': len(set(t.channel for t in touchpoints)),
                'last_activity': touchpoints[-1].timestamp.isoformat()
            }
        )
        
        # Cache the journey
        self.journey_cache[cache_key] = journey
        
        return journey
    
    def analyze_journey_patterns(self, organization_id: str,
                                segment_filters: Optional[Dict[str, Any]] = None,
                                min_customers: int = 10) -> Dict[str, Any]:
        """
        Analyze common journey patterns across customer base
        
        Args:
            organization_id: Organization identifier
            segment_filters: Optional filters for customer segmentation
            min_customers: Minimum customers required for pattern analysis
            
        Returns:
            Journey pattern analysis results
        """
        # Get customer journeys for analysis
        journeys = self._get_organization_journeys(organization_id, segment_filters)
        
        if len(journeys) < min_customers:
            return {'error': f'Insufficient data: {len(journeys)} customers (minimum: {min_customers})'}
        
        # Analyze common paths
        common_paths = self._analyze_common_paths(journeys)
        
        # Analyze stage conversion rates
        conversion_rates = self._analyze_conversion_rates(journeys)
        
        # Analyze journey segments
        journey_segments = self._analyze_journey_segments(journeys)
        
        # Identify bottlenecks and opportunities
        bottlenecks = self._identify_journey_bottlenecks(journeys, conversion_rates)
        opportunities = self._identify_optimization_opportunities(journeys, journey_segments)
        
        # Calculate journey health metrics
        health_metrics = self._calculate_journey_health_metrics(journeys)
        
        return {
            'organization_id': organization_id,
            'analysis_date': datetime.now().isoformat(),
            'customer_count': len(journeys),
            'common_paths': common_paths,
            'conversion_rates': conversion_rates,
            'journey_segments': journey_segments,
            'bottlenecks': bottlenecks,
            'opportunities': opportunities,
            'health_metrics': health_metrics,
            'insights': self._generate_journey_insights(journeys, common_paths, bottlenecks)
        }
    
    def get_journey_recommendations(self, customer_id: str, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get personalized journey recommendations for a customer
        
        Args:
            customer_id: Customer identifier
            organization_id: Organization identifier
            
        Returns:
            List of personalized journey recommendations
        """
        journey = self.map_customer_journey(customer_id, organization_id)
        
        recommendations = []
        
        # Stage-based recommendations
        stage_recs = self._get_stage_recommendations(journey)
        recommendations.extend(stage_recs)
        
        # Churn risk recommendations
        if journey.churn_risk > 0.7:
            churn_recs = self._get_churn_prevention_recommendations(journey)
            recommendations.extend(churn_recs)
        
        # Engagement recommendations
        engagement_recs = self._get_engagement_recommendations(journey)
        recommendations.extend(engagement_recs)
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda r: (r['priority'], -r['confidence']), reverse=True)
        
        return recommendations
    
    def create_journey_cohorts(self, organization_id: str,
                              cohort_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create customer cohorts based on journey characteristics
        
        Args:
            organization_id: Organization identifier
            cohort_criteria: Criteria for cohort segmentation
            
        Returns:
            Journey-based cohort analysis
        """
        journeys = self._get_organization_journeys(organization_id)
        
        cohorts = defaultdict(list)
        
        for journey in journeys:
            # Assign to cohorts based on criteria
            cohort_keys = self._assign_journey_cohorts(journey, cohort_criteria)
            
            for key in cohort_keys:
                cohorts[key].append(journey)
        
        # Analyze each cohort
        cohort_analysis = {}
        for cohort_name, cohort_journeys in cohorts.items():
            cohort_analysis[cohort_name] = self._analyze_cohort_journeys(cohort_journeys)
        
        return {
            'organization_id': organization_id,
            'cohort_criteria': cohort_criteria,
            'cohorts': cohort_analysis,
            'insights': self._generate_cohort_insights(cohort_analysis)
        }
    
    def _collect_customer_touchpoints(self, customer_id: str, organization_id: str,
                                     lookback_days: int) -> List[CustomerTouchpoint]:
        """Collect all touchpoints for a customer from various data sources"""
        touchpoints = []
        
        # Query touchpoint data from time-series database
        end_time = datetime.now()
        start_time = end_time - timedelta(days=lookback_days)
        
        # Get various touchpoint metrics
        touchpoint_metrics = [
            'website_visits', 'email_opens', 'email_clicks', 'support_tickets',
            'purchases', 'logins', 'feature_usage', 'subscription_changes'
        ]
        
        for metric in touchpoint_metrics:
            try:
                data = self.ts_db.query(
                    metric_name=metric,
                    organization_id=organization_id,
                    start_time=start_time,
                    end_time=end_time,
                    tags={'customer_id': customer_id}
                )
                
                for _, row in data.iterrows():
                    touchpoint = CustomerTouchpoint(
                        id=f"{metric}_{customer_id}_{int(row['timestamp'].timestamp())}",
                        customer_id=customer_id,
                        organization_id=organization_id,
                        touchpoint_type=TouchpointType(metric.rstrip('s')),  # Remove plural
                        timestamp=pd.to_datetime(row['timestamp']),
                        channel=self._infer_channel(metric),
                        properties={'metric': metric, 'value': row['value']},
                        value=row['value']
                    )
                    touchpoints.append(touchpoint)
                    
            except Exception as e:
                logger.warning(f"Error collecting {metric} touchpoints: {e}")
        
        return touchpoints
    
    def _analyze_stage_transitions(self, touchpoints: List[CustomerTouchpoint]) -> List[Dict[str, Any]]:
        """Analyze customer journey stage transitions"""
        transitions = []
        current_stage = JourneyStage.AWARENESS
        stage_start = touchpoints[0].timestamp
        
        for i, touchpoint in enumerate(touchpoints):
            # Determine if this touchpoint triggers a stage transition
            new_stage = self._determine_stage_from_touchpoint(touchpoint, current_stage)
            
            if new_stage != current_stage:
                # Record transition
                transition = {
                    'from_stage': current_stage.value,
                    'to_stage': new_stage.value,
                    'transition_date': touchpoint.timestamp.isoformat(),
                    'trigger_touchpoint': touchpoint.touchpoint_type.value,
                    'days_in_stage': (touchpoint.timestamp - stage_start).days,
                    'touchpoints_in_stage': self._count_touchpoints_in_stage(
                        touchpoints[:i], stage_start, touchpoint.timestamp
                    )
                }
                transitions.append(transition)
                
                current_stage = new_stage
                stage_start = touchpoint.timestamp
        
        return transitions
    
    def _determine_current_stage(self, touchpoints: List[CustomerTouchpoint],
                                transitions: List[Dict[str, Any]]) -> JourneyStage:
        """Determine customer's current journey stage"""
        if not transitions:
            return JourneyStage.AWARENESS
        
        # Get the most recent transition
        latest_transition = transitions[-1]
        current_stage = JourneyStage(latest_transition['to_stage'])
        
        # Check if customer might have churned
        last_activity = touchpoints[-1].timestamp
        days_since_activity = (datetime.now() - last_activity).days
        
        if days_since_activity > 30 and current_stage != JourneyStage.CHURNED:
            # Check for churn indicators
            if self._has_churn_indicators(touchpoints[-10:]):  # Last 10 touchpoints
                return JourneyStage.AT_RISK
        
        return current_stage
    
    def _calculate_journey_score(self, touchpoints: List[CustomerTouchpoint],
                               transitions: List[Dict[str, Any]]) -> float:
        """Calculate overall journey health score (0-100)"""
        if not touchpoints:
            return 0.0
        
        scores = []
        
        # Engagement score based on touchpoint frequency and recency
        engagement_score = self._calculate_engagement_score(touchpoints)
        scores.append(('engagement', engagement_score, 0.3))
        
        # Progression score based on stage advancement
        progression_score = self._calculate_progression_score(transitions)
        scores.append(('progression', progression_score, 0.25))
        
        # Value realization score based on feature usage and outcomes
        value_score = self._calculate_value_realization_score(touchpoints)
        scores.append(('value_realization', value_score, 0.25))
        
        # Satisfaction indicators from touchpoints
        satisfaction_score = self._calculate_satisfaction_score(touchpoints)
        scores.append(('satisfaction', satisfaction_score, 0.2))
        
        # Weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        
        return min(max(total_score * 100, 0), 100)
    
    def _calculate_journey_churn_risk(self, touchpoints: List[CustomerTouchpoint],
                                    transitions: List[Dict[str, Any]]) -> float:
        """Calculate churn risk based on journey patterns"""
        if not touchpoints:
            return 0.5
        
        risk_factors = []
        
        # Recency risk
        last_activity = touchpoints[-1].timestamp
        days_since_activity = (datetime.now() - last_activity).days
        recency_risk = min(days_since_activity / 30.0, 1.0)  # Max risk after 30 days
        risk_factors.append(('recency', recency_risk, 0.3))
        
        # Engagement decline risk
        engagement_trend = self._analyze_engagement_trend(touchpoints)
        engagement_risk = max(0, -engagement_trend)  # Negative trend = risk
        risk_factors.append(('engagement_decline', engagement_risk, 0.25))
        
        # Stage regression risk
        regression_risk = self._analyze_stage_regression_risk(transitions)
        risk_factors.append(('stage_regression', regression_risk, 0.2))
        
        # Negative touchpoint risk (support tickets, complaints)
        negative_touchpoint_risk = self._calculate_negative_touchpoint_risk(touchpoints)
        risk_factors.append(('negative_touchpoints', negative_touchpoint_risk, 0.15))
        
        # Journey completion risk
        completion_risk = self._calculate_journey_completion_risk(touchpoints, transitions)
        risk_factors.append(('completion', completion_risk, 0.1))
        
        # Weighted risk score
        total_risk = sum(risk * weight for _, risk, weight in risk_factors)
        
        return min(max(total_risk, 0), 1.0)
    
    def _predict_customer_ltv(self, touchpoints: List[CustomerTouchpoint],
                            transitions: List[Dict[str, Any]]) -> float:
        """Predict customer lifetime value based on journey patterns"""
        # This is a simplified LTV prediction model
        # In production, this would use more sophisticated ML models
        
        base_ltv = 1000.0  # Base LTV assumption
        
        # Journey quality multiplier
        journey_score = self._calculate_journey_score(touchpoints, transitions) / 100.0
        quality_multiplier = 1.0 + (journey_score - 0.5)  # -0.5 to +0.5 range
        
        # Engagement multiplier
        engagement_level = self._calculate_engagement_level(touchpoints)
        engagement_multiplier = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.8,
            'very_high': 2.5
        }.get(engagement_level, 1.0)
        
        # Stage progression bonus
        advanced_stages = [t for t in transitions if t['to_stage'] in ['expansion', 'renewal']]
        stage_bonus = len(advanced_stages) * 0.3
        
        predicted_ltv = base_ltv * quality_multiplier * engagement_multiplier * (1 + stage_bonus)
        
        return max(predicted_ltv, 0)
    
    def _identify_key_moments(self, touchpoints: List[CustomerTouchpoint],
                            transitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key moments in customer journey"""
        key_moments = []
        
        # First touchpoint
        if touchpoints:
            key_moments.append({
                'moment_type': 'first_contact',
                'timestamp': touchpoints[0].timestamp.isoformat(),
                'touchpoint_type': touchpoints[0].touchpoint_type.value,
                'significance': 'Journey beginning',
                'impact_score': 0.9
            })
        
        # Stage transitions
        for transition in transitions:
            if transition['to_stage'] in ['trial', 'active_use', 'expansion', 'churned']:
                key_moments.append({
                    'moment_type': 'stage_transition',
                    'timestamp': transition['transition_date'],
                    'from_stage': transition['from_stage'],
                    'to_stage': transition['to_stage'],
                    'significance': f"Progression to {transition['to_stage']}",
                    'impact_score': self._calculate_transition_impact(transition)
                })
        
        # High-value touchpoints
        value_touchpoints = [t for t in touchpoints if t.value and t.value > 100]
        for touchpoint in value_touchpoints:
            key_moments.append({
                'moment_type': 'high_value_interaction',
                'timestamp': touchpoint.timestamp.isoformat(),
                'touchpoint_type': touchpoint.touchpoint_type.value,
                'value': touchpoint.value,
                'significance': 'High-value customer interaction',
                'impact_score': min(touchpoint.value / 1000.0, 1.0)
            })
        
        # Sort by impact score
        key_moments.sort(key=lambda m: m['impact_score'], reverse=True)
        
        return key_moments[:10]  # Top 10 key moments
    
    def _load_stage_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load journey stage definitions and criteria"""
        return {
            'awareness': {
                'description': 'Customer becomes aware of the product',
                'trigger_touchpoints': ['website_visit', 'email_open'],
                'min_touchpoints': 1,
                'max_duration_days': 30
            },
            'consideration': {
                'description': 'Customer evaluates the product',
                'trigger_touchpoints': ['email_click', 'feature_use'],
                'min_touchpoints': 3,
                'max_duration_days': 60
            },
            'trial': {
                'description': 'Customer starts trial or evaluation',
                'trigger_touchpoints': ['trial_start', 'subscription_change'],
                'min_touchpoints': 5,
                'max_duration_days': 30
            },
            'onboarding': {
                'description': 'Customer goes through initial setup',
                'trigger_touchpoints': ['login', 'feature_use'],
                'min_touchpoints': 10,
                'max_duration_days': 14
            },
            'active_use': {
                'description': 'Customer actively uses the product',
                'trigger_touchpoints': ['feature_use', 'login'],
                'min_touchpoints': 20,
                'max_duration_days': None
            },
            'expansion': {
                'description': 'Customer expands usage or upgrades',
                'trigger_touchpoints': ['subscription_change', 'purchase'],
                'min_touchpoints': 5,
                'max_duration_days': None
            },
            'renewal': {
                'description': 'Customer renews subscription',
                'trigger_touchpoints': ['payment', 'subscription_change'],
                'min_touchpoints': 1,
                'max_duration_days': None
            },
            'at_risk': {
                'description': 'Customer showing signs of potential churn',
                'trigger_touchpoints': ['support_ticket', 'low_activity'],
                'min_touchpoints': 1,
                'max_duration_days': None
            },
            'churned': {
                'description': 'Customer has churned',
                'trigger_touchpoints': ['churn_event', 'no_activity'],
                'min_touchpoints': 0,
                'max_duration_days': None
            }
        }
    
    def _load_touchpoint_weights(self) -> Dict[str, float]:
        """Load touchpoint importance weights for scoring"""
        return {
            'website_visit': 0.1,
            'email_open': 0.2,
            'email_click': 0.4,
            'support_ticket': -0.1,  # Negative weight
            'purchase': 1.0,
            'login': 0.6,
            'feature_use': 0.8,
            'subscription_change': 0.9,
            'payment': 1.0,
            'churn_event': -2.0,
            'reactivation': 1.2,
            'referral': 0.7,
            'feedback': 0.3,
            'trial_start': 0.8,
            'trial_end': 0.5
        }
    
    def _load_transition_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load stage transition rules and logic"""
        return {
            'awareness_to_consideration': {
                'min_touchpoints': 3,
                'required_types': ['email_click', 'website_visit'],
                'max_days': 7
            },
            'consideration_to_trial': {
                'min_touchpoints': 1,
                'required_types': ['trial_start'],
                'max_days': None
            },
            'trial_to_active': {
                'min_touchpoints': 5,
                'required_types': ['login', 'feature_use'],
                'max_days': 14
            }
        }
    
    # Additional helper methods for journey analysis...
    def _infer_channel(self, metric: str) -> str:
        """Infer communication channel from metric type"""
        channel_mapping = {
            'website_visits': 'website',
            'email_opens': 'email',
            'email_clicks': 'email',
            'support_tickets': 'support',
            'purchases': 'product',
            'logins': 'product',
            'feature_usage': 'product',
            'subscription_changes': 'billing'
        }
        return channel_mapping.get(metric, 'unknown')
    
    def _determine_stage_from_touchpoint(self, touchpoint: CustomerTouchpoint,
                                       current_stage: JourneyStage) -> JourneyStage:
        """Determine new stage based on touchpoint and current stage"""
        # Simplified stage transition logic
        touchpoint_type = touchpoint.touchpoint_type.value
        
        if touchpoint_type == 'trial_start':
            return JourneyStage.TRIAL
        elif touchpoint_type == 'purchase':
            return JourneyStage.ACTIVE_USE
        elif touchpoint_type == 'subscription_change' and touchpoint.value and touchpoint.value > 0:
            return JourneyStage.EXPANSION
        elif touchpoint_type == 'churn_event':
            return JourneyStage.CHURNED
        
        return current_stage
    
    def _count_touchpoints_in_stage(self, touchpoints: List[CustomerTouchpoint],
                                   stage_start: datetime, stage_end: datetime) -> int:
        """Count touchpoints within a stage timeframe"""
        return len([t for t in touchpoints 
                   if stage_start <= t.timestamp <= stage_end])
    
    def _has_churn_indicators(self, recent_touchpoints: List[CustomerTouchpoint]) -> bool:
        """Check if recent touchpoints indicate churn risk"""
        if not recent_touchpoints:
            return True  # No activity is a churn indicator
        
        # Check for support tickets or negative indicators
        negative_touchpoints = [t for t in recent_touchpoints 
                              if t.touchpoint_type in [TouchpointType.SUPPORT_TICKET]]
        
        return len(negative_touchpoints) > len(recent_touchpoints) * 0.3
    
    def _create_empty_journey(self, customer_id: str, organization_id: str) -> CustomerJourney:
        """Create empty journey for customers with no touchpoints"""
        return CustomerJourney(
            customer_id=customer_id,
            organization_id=organization_id,
            journey_start=datetime.now(),
            journey_end=None,
            current_stage=JourneyStage.AWARENESS,
            touchpoints=[],
            stage_transitions=[],
            journey_score=0.0,
            churn_risk=1.0,  # High risk if no data
            predicted_ltv=0.0,
            key_moments=[],
            metadata={'no_data': True}
        )
    
    # Placeholder methods for complex calculations
    def _calculate_engagement_score(self, touchpoints: List[CustomerTouchpoint]) -> float:
        """Calculate customer engagement score"""
        if not touchpoints:
            return 0.0
        
        # Simple engagement calculation based on frequency and recency
        recent_touchpoints = [t for t in touchpoints 
                            if (datetime.now() - t.timestamp).days <= 30]
        
        frequency_score = min(len(recent_touchpoints) / 10.0, 1.0)  # 10 touchpoints = max
        recency_score = 1.0 if recent_touchpoints else 0.0
        
        return (frequency_score + recency_score) / 2
    
    def _calculate_progression_score(self, transitions: List[Dict[str, Any]]) -> float:
        """Calculate journey progression score"""
        if not transitions:
            return 0.0
        
        # Score based on advanced stages reached
        advanced_stages = ['active_use', 'expansion', 'renewal']
        reached_advanced = len([t for t in transitions 
                              if t['to_stage'] in advanced_stages])
        
        return min(reached_advanced / len(advanced_stages), 1.0)
    
    def _calculate_value_realization_score(self, touchpoints: List[CustomerTouchpoint]) -> float:
        """Calculate value realization score"""
        # Score based on feature usage and valuable interactions
        valuable_touchpoints = [t for t in touchpoints 
                              if t.touchpoint_type in [TouchpointType.FEATURE_USE, 
                                                      TouchpointType.PURCHASE]]
        
        if not touchpoints:
            return 0.0
        
        return min(len(valuable_touchpoints) / len(touchpoints), 1.0)
    
    def _calculate_satisfaction_score(self, touchpoints: List[CustomerTouchpoint]) -> float:
        """Calculate satisfaction score from touchpoint patterns"""
        if not touchpoints:
            return 0.5
        
        # Simple heuristic: fewer support tickets = higher satisfaction
        support_touchpoints = [t for t in touchpoints 
                             if t.touchpoint_type == TouchpointType.SUPPORT_TICKET]
        
        if not touchpoints:
            return 0.5
        
        negative_ratio = len(support_touchpoints) / len(touchpoints)
        return max(1.0 - negative_ratio * 2, 0.0)  # Support tickets reduce satisfaction
    
    # Additional placeholder methods would be implemented here for:
    # - _get_organization_journeys()
    # - _analyze_common_paths()
    # - _analyze_conversion_rates()
    # - _identify_journey_bottlenecks()
    # - _generate_journey_insights()
    # - etc.
    
    def _get_organization_journeys(self, organization_id: str, 
                                  filters: Optional[Dict[str, Any]] = None) -> List[CustomerJourney]:
        """Get all journeys for organization (placeholder implementation)"""
        # This would query the database for all customers and build their journeys
        # For now, return empty list
        return []

# Global customer journey mapper instance
journey_mapper = CustomerJourneyMapper()

def get_journey_mapper() -> CustomerJourneyMapper:
    """Get the global customer journey mapper instance"""
    return journey_mapper

# Convenience functions
def map_customer_journey(customer_id: str, organization_id: str) -> CustomerJourney:
    """Map complete customer journey"""
    mapper = get_journey_mapper()
    return mapper.map_customer_journey(customer_id, organization_id)

def analyze_organization_journeys(organization_id: str) -> Dict[str, Any]:
    """Analyze journey patterns for organization"""
    mapper = get_journey_mapper()
    return mapper.analyze_journey_patterns(organization_id)

def get_journey_recommendations(customer_id: str, organization_id: str) -> List[Dict[str, Any]]:
    """Get personalized journey recommendations"""
    mapper = get_journey_mapper()
    return mapper.get_journey_recommendations(customer_id, organization_id)