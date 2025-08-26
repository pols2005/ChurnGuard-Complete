# ChurnGuard Behavioral Analysis Engine
# Epic 4 Phase 4 - Customer Intelligence Tools

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import networkx as nx
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA

from .time_series_db import get_time_series_db
from .statistical_analysis import get_stats_service
from .customer_journey import get_journey_mapper, CustomerJourney, TouchpointType

logger = logging.getLogger(__name__)

class BehaviorType(Enum):
    ENGAGEMENT = "engagement"
    USAGE_PATTERN = "usage_pattern"
    FEATURE_ADOPTION = "feature_adoption"
    PAYMENT_BEHAVIOR = "payment_behavior"
    SUPPORT_INTERACTION = "support_interaction"
    SOCIAL_BEHAVIOR = "social_behavior"
    CONTENT_CONSUMPTION = "content_consumption"
    NAVIGATION_PATTERN = "navigation_pattern"

class BehaviorSegment(Enum):
    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"
    TRIAL_USER = "trial_user"
    DORMANT_USER = "dormant_user"
    CHURNED_USER = "churned_user"
    NEW_USER = "new_user"
    EXPANDING_USER = "expanding_user"
    AT_RISK_USER = "at_risk_user"

class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class BehaviorPattern:
    """Individual behavior pattern analysis"""
    pattern_id: str
    customer_id: str
    organization_id: str
    behavior_type: BehaviorType
    pattern_name: str
    frequency: float
    strength: float
    confidence: float
    start_date: datetime
    end_date: Optional[datetime]
    characteristics: Dict[str, Any]
    triggers: List[str]
    outcomes: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehaviorCluster:
    """Cluster of similar behavioral patterns"""
    cluster_id: str
    organization_id: str
    cluster_name: str
    behavior_types: List[BehaviorType]
    customer_count: int
    characteristics: Dict[str, Any]
    representative_patterns: List[str]
    churn_risk: float
    value_score: float
    recommendations: List[str]

@dataclass
class CustomerBehaviorProfile:
    """Comprehensive behavioral profile for a customer"""
    customer_id: str
    organization_id: str
    profile_date: datetime
    behavior_segment: BehaviorSegment
    engagement_score: float
    usage_intensity: float
    feature_adoption_rate: float
    behavior_consistency: float
    risk_indicators: Dict[str, float]
    behavior_patterns: List[BehaviorPattern]
    predicted_actions: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehaviorInsight:
    """Actionable insight derived from behavioral analysis"""
    insight_id: str
    organization_id: str
    insight_type: str
    title: str
    description: str
    affected_customers: int
    potential_impact: str
    confidence: float
    recommendations: List[str]
    data: Dict[str, Any]
    created_at: datetime

class BehavioralAnalysisEngine:
    """
    Advanced behavioral analysis engine for customer intelligence
    
    Features:
    - Multi-dimensional behavior pattern recognition
    - Customer segmentation based on behavioral characteristics
    - Predictive behavior modeling
    - Churn risk assessment through behavioral indicators
    - Feature adoption and usage pattern analysis
    - Social behavior and network effects analysis
    - Real-time behavior monitoring and alerts
    - Personalized behavior-based recommendations
    """
    
    def __init__(self):
        self.ts_db = get_time_series_db()
        self.stats_service = get_stats_service()
        self.journey_mapper = get_journey_mapper()
        
        # Behavior analysis configuration
        self.behavior_weights = self._load_behavior_weights()
        self.segment_definitions = self._load_segment_definitions()
        self.pattern_templates = self._load_pattern_templates()
        
        # Analysis cache
        self.behavior_cache: Dict[str, CustomerBehaviorProfile] = {}
        self.cluster_cache: Dict[str, List[BehaviorCluster]] = {}
        
        # Pattern recognition models
        self.clustering_models = {}
        self.prediction_models = {}
        
    def analyze_customer_behavior(self, customer_id: str, organization_id: str,
                                 analysis_period_days: int = 90) -> CustomerBehaviorProfile:
        """
        Comprehensive behavioral analysis for a single customer
        
        Args:
            customer_id: Customer identifier
            organization_id: Organization identifier
            analysis_period_days: Period for behavioral analysis
            
        Returns:
            CustomerBehaviorProfile with complete behavioral insights
        """
        cache_key = f"{customer_id}:{organization_id}"
        if cache_key in self.behavior_cache:
            profile = self.behavior_cache[cache_key]
            if (datetime.now() - profile.profile_date).days < 1:
                return profile
        
        # Get customer journey data
        journey = self.journey_mapper.map_customer_journey(customer_id, organization_id)
        
        # Collect behavioral data from multiple sources
        behavior_data = self._collect_behavioral_data(
            customer_id, organization_id, analysis_period_days
        )
        
        if not behavior_data:
            return self._create_minimal_profile(customer_id, organization_id)
        
        # Analyze different behavioral dimensions
        engagement_metrics = self._analyze_engagement_behavior(behavior_data, journey)
        usage_patterns = self._analyze_usage_patterns(behavior_data)
        feature_adoption = self._analyze_feature_adoption(behavior_data)
        temporal_patterns = self._analyze_temporal_behavior(behavior_data)
        social_behavior = self._analyze_social_behavior(behavior_data)
        
        # Extract behavior patterns
        behavior_patterns = self._extract_behavior_patterns(
            behavior_data, customer_id, organization_id
        )
        
        # Calculate composite scores
        engagement_score = self._calculate_engagement_score(engagement_metrics)
        usage_intensity = self._calculate_usage_intensity(usage_patterns)
        feature_adoption_rate = self._calculate_feature_adoption_rate(feature_adoption)
        behavior_consistency = self._calculate_behavior_consistency(temporal_patterns)
        
        # Assess risk indicators
        risk_indicators = self._assess_risk_indicators(
            behavior_data, journey, engagement_metrics, usage_patterns
        )
        
        # Determine behavior segment
        behavior_segment = self._determine_behavior_segment(
            engagement_score, usage_intensity, feature_adoption_rate, risk_indicators
        )
        
        # Generate predictions and recommendations
        predicted_actions = self._predict_customer_actions(behavior_patterns, journey)
        recommendations = self._generate_behavior_recommendations(
            behavior_segment, behavior_patterns, risk_indicators
        )
        
        profile = CustomerBehaviorProfile(
            customer_id=customer_id,
            organization_id=organization_id,
            profile_date=datetime.now(),
            behavior_segment=behavior_segment,
            engagement_score=engagement_score,
            usage_intensity=usage_intensity,
            feature_adoption_rate=feature_adoption_rate,
            behavior_consistency=behavior_consistency,
            risk_indicators=risk_indicators,
            behavior_patterns=behavior_patterns,
            predicted_actions=predicted_actions,
            recommendations=recommendations,
            metadata={
                'analysis_period_days': analysis_period_days,
                'total_touchpoints': len(journey.touchpoints),
                'unique_behavior_types': len(set(p.behavior_type for p in behavior_patterns)),
                'journey_stage': journey.current_stage.value
            }
        )
        
        # Cache the profile
        self.behavior_cache[cache_key] = profile
        
        return profile
    
    def segment_customers_by_behavior(self, organization_id: str,
                                    min_customers: int = 50,
                                    n_clusters: Optional[int] = None) -> List[BehaviorCluster]:
        """
        Segment customers based on behavioral patterns using clustering
        
        Args:
            organization_id: Organization identifier
            min_customers: Minimum customers for analysis
            n_clusters: Number of clusters (auto-determined if None)
            
        Returns:
            List of behavior-based customer clusters
        """
        cache_key = organization_id
        if cache_key in self.cluster_cache:
            clusters = self.cluster_cache[cache_key]
            # Check if clusters are recent (within 24 hours)
            if clusters and (datetime.now() - datetime.fromisoformat(clusters[0].characteristics.get('created_at', '2000-01-01'))).hours < 24:
                return clusters
        
        # Get behavioral profiles for all customers
        customer_profiles = self._get_organization_behavior_profiles(organization_id)
        
        if len(customer_profiles) < min_customers:
            logger.warning(f"Insufficient customers for clustering: {len(customer_profiles)} < {min_customers}")
            return []
        
        # Extract behavioral features for clustering
        feature_matrix, feature_names, customer_ids = self._extract_clustering_features(customer_profiles)
        
        # Determine optimal number of clusters
        if n_clusters is None:
            n_clusters = self._determine_optimal_clusters(feature_matrix)
        
        # Perform clustering using multiple algorithms
        clustering_results = self._perform_multi_algorithm_clustering(
            feature_matrix, n_clusters, customer_ids
        )
        
        # Analyze each cluster
        clusters = []
        for cluster_id, cluster_customers in clustering_results.items():
            cluster_profiles = [p for p in customer_profiles if p.customer_id in cluster_customers]
            
            if len(cluster_profiles) < 5:  # Skip very small clusters
                continue
            
            cluster_analysis = self._analyze_behavior_cluster(cluster_profiles, cluster_id, organization_id)
            clusters.append(cluster_analysis)
        
        # Sort clusters by size and value
        clusters.sort(key=lambda c: (c.customer_count, c.value_score), reverse=True)
        
        # Cache the results
        for cluster in clusters:
            cluster.characteristics['created_at'] = datetime.now().isoformat()
        self.cluster_cache[cache_key] = clusters
        
        return clusters
    
    def detect_behavior_anomalies(self, organization_id: str,
                                 time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect anomalous behavioral patterns that might indicate issues
        
        Args:
            organization_id: Organization identifier
            time_window_hours: Time window for anomaly detection
            
        Returns:
            List of detected behavioral anomalies
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        anomalies = []
        
        # Get recent behavioral metrics
        behavior_metrics = [
            'user_engagement_rate', 'feature_adoption_rate', 'session_duration',
            'page_views_per_session', 'support_ticket_rate', 'churn_indicators'
        ]
        
        for metric in behavior_metrics:
            try:
                # Get metric data
                data = self.ts_db.query(
                    metric_name=metric,
                    organization_id=organization_id,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if data.empty or len(data) < 5:
                    continue
                
                # Detect behavioral anomalies
                metric_anomalies = self._detect_metric_behavior_anomalies(
                    data, metric, organization_id
                )
                anomalies.extend(metric_anomalies)
                
            except Exception as e:
                logger.error(f"Error detecting anomalies in {metric}: {e}")
        
        # Detect pattern-based anomalies
        pattern_anomalies = self._detect_pattern_anomalies(organization_id, time_window_hours)
        anomalies.extend(pattern_anomalies)
        
        return sorted(anomalies, key=lambda x: x['severity'], reverse=True)
    
    def generate_behavior_insights(self, organization_id: str,
                                 insight_types: Optional[List[str]] = None) -> List[BehaviorInsight]:
        """
        Generate actionable insights from behavioral analysis
        
        Args:
            organization_id: Organization identifier
            insight_types: Specific types of insights to generate
            
        Returns:
            List of behavioral insights with recommendations
        """
        if insight_types is None:
            insight_types = [
                'engagement_trends', 'feature_adoption', 'churn_risk', 
                'user_segments', 'behavior_patterns', 'optimization_opportunities'
            ]
        
        insights = []
        
        # Get organization-wide behavioral data
        customer_profiles = self._get_organization_behavior_profiles(organization_id)
        behavior_clusters = self.segment_customers_by_behavior(organization_id)
        
        # Generate different types of insights
        if 'engagement_trends' in insight_types:
            engagement_insights = self._generate_engagement_insights(customer_profiles, organization_id)
            insights.extend(engagement_insights)
        
        if 'feature_adoption' in insight_types:
            adoption_insights = self._generate_feature_adoption_insights(customer_profiles, organization_id)
            insights.extend(adoption_insights)
        
        if 'churn_risk' in insight_types:
            churn_insights = self._generate_churn_risk_insights(customer_profiles, organization_id)
            insights.extend(churn_insights)
        
        if 'user_segments' in insight_types:
            segment_insights = self._generate_segment_insights(behavior_clusters, organization_id)
            insights.extend(segment_insights)
        
        if 'behavior_patterns' in insight_types:
            pattern_insights = self._generate_pattern_insights(customer_profiles, organization_id)
            insights.extend(pattern_insights)
        
        if 'optimization_opportunities' in insight_types:
            optimization_insights = self._generate_optimization_insights(
                customer_profiles, behavior_clusters, organization_id
            )
            insights.extend(optimization_insights)
        
        # Sort insights by potential impact and confidence
        insights.sort(key=lambda i: (i.confidence, i.affected_customers), reverse=True)
        
        return insights[:20]  # Return top 20 insights
    
    def predict_customer_behavior(self, customer_id: str, organization_id: str,
                                prediction_horizon_days: int = 30) -> Dict[str, Any]:
        """
        Predict customer behavior over the specified time horizon
        
        Args:
            customer_id: Customer identifier
            organization_id: Organization identifier
            prediction_horizon_days: Days to predict ahead
            
        Returns:
            Behavioral predictions with confidence intervals
        """
        # Get customer behavioral profile
        profile = self.analyze_customer_behavior(customer_id, organization_id)
        
        # Get historical behavioral data
        behavior_data = self._collect_behavioral_data(
            customer_id, organization_id, analysis_period_days=180
        )
        
        predictions = {
            'customer_id': customer_id,
            'organization_id': organization_id,
            'prediction_date': datetime.now().isoformat(),
            'prediction_horizon_days': prediction_horizon_days,
            'current_segment': profile.behavior_segment.value,
            'predictions': {}
        }
        
        # Predict engagement levels
        engagement_prediction = self._predict_engagement_trajectory(
            profile, behavior_data, prediction_horizon_days
        )
        predictions['predictions']['engagement'] = engagement_prediction
        
        # Predict feature usage
        feature_prediction = self._predict_feature_usage(
            profile, behavior_data, prediction_horizon_days
        )
        predictions['predictions']['feature_usage'] = feature_prediction
        
        # Predict churn probability
        churn_prediction = self._predict_churn_probability(
            profile, behavior_data, prediction_horizon_days
        )
        predictions['predictions']['churn_risk'] = churn_prediction
        
        # Predict value generation
        value_prediction = self._predict_customer_value(
            profile, behavior_data, prediction_horizon_days
        )
        predictions['predictions']['value_generation'] = value_prediction
        
        # Predict likely actions
        action_predictions = self._predict_customer_actions(
            profile.behavior_patterns, profile.customer_id
        )
        predictions['predictions']['likely_actions'] = action_predictions
        
        return predictions
    
    def _collect_behavioral_data(self, customer_id: str, organization_id: str,
                                analysis_period_days: int) -> Dict[str, Any]:
        """Collect behavioral data from various sources"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=analysis_period_days)
        
        behavior_data = {
            'customer_id': customer_id,
            'organization_id': organization_id,
            'period_start': start_time,
            'period_end': end_time,
            'touchpoints': [],
            'sessions': [],
            'feature_usage': {},
            'engagement_metrics': {},
            'temporal_data': defaultdict(list)
        }
        
        # Collect touchpoint data
        touchpoint_metrics = [
            'login_events', 'page_views', 'feature_clicks', 'session_duration',
            'email_interactions', 'support_interactions', 'purchase_events'
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
                
                if not data.empty:
                    for _, row in data.iterrows():
                        touchpoint = {
                            'timestamp': pd.to_datetime(row['timestamp']),
                            'metric': metric,
                            'value': row['value'],
                            'properties': row.get('properties', {})
                        }
                        behavior_data['touchpoints'].append(touchpoint)
                        
                        # Organize by time periods
                        hour = touchpoint['timestamp'].hour
                        day = touchpoint['timestamp'].strftime('%A')
                        behavior_data['temporal_data'][f'{day}_{hour}'].append(touchpoint)
                        
            except Exception as e:
                logger.warning(f"Error collecting {metric} data: {e}")
        
        # Sort touchpoints by timestamp
        behavior_data['touchpoints'].sort(key=lambda x: x['timestamp'])
        
        return behavior_data
    
    def _analyze_engagement_behavior(self, behavior_data: Dict[str, Any],
                                   journey: CustomerJourney) -> Dict[str, Any]:
        """Analyze customer engagement patterns"""
        touchpoints = behavior_data['touchpoints']
        
        if not touchpoints:
            return {'engagement_score': 0.0, 'patterns': []}
        
        # Calculate engagement metrics
        total_touchpoints = len(touchpoints)
        unique_days = len(set(t['timestamp'].date() for t in touchpoints))
        avg_daily_touchpoints = total_touchpoints / max(unique_days, 1)
        
        # Analyze engagement consistency
        daily_counts = defaultdict(int)
        for touchpoint in touchpoints:
            daily_counts[touchpoint['timestamp'].date()] += 1
        
        engagement_consistency = np.std(list(daily_counts.values())) if daily_counts else 0
        
        # Analyze engagement depth (session duration, page views)
        session_metrics = [t for t in touchpoints if t['metric'] in ['session_duration', 'page_views']]
        avg_session_depth = np.mean([t['value'] for t in session_metrics]) if session_metrics else 0
        
        # Recent engagement trend
        recent_touchpoints = [t for t in touchpoints 
                            if (datetime.now() - t['timestamp']).days <= 7]
        recent_engagement = len(recent_touchpoints)
        
        return {
            'total_touchpoints': total_touchpoints,
            'unique_active_days': unique_days,
            'avg_daily_touchpoints': avg_daily_touchpoints,
            'engagement_consistency': engagement_consistency,
            'avg_session_depth': avg_session_depth,
            'recent_engagement': recent_engagement,
            'engagement_trend': self._calculate_engagement_trend(touchpoints),
            'peak_usage_hours': self._identify_peak_usage_hours(touchpoints),
            'engagement_patterns': self._identify_engagement_patterns(touchpoints)
        }
    
    def _analyze_usage_patterns(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze usage patterns and habits"""
        touchpoints = behavior_data['touchpoints']
        temporal_data = behavior_data['temporal_data']
        
        # Analyze temporal patterns
        hourly_usage = defaultdict(int)
        daily_usage = defaultdict(int)
        
        for touchpoint in touchpoints:
            hour = touchpoint['timestamp'].hour
            day = touchpoint['timestamp'].strftime('%A')
            hourly_usage[hour] += 1
            daily_usage[day] += 1
        
        # Identify usage patterns
        peak_hours = sorted(hourly_usage.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_days = sorted(daily_usage.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate usage intensity
        total_time_span = (max(t['timestamp'] for t in touchpoints) - 
                          min(t['timestamp'] for t in touchpoints)).days if touchpoints else 1
        usage_intensity = len(touchpoints) / max(total_time_span, 1)
        
        # Analyze session patterns
        session_analysis = self._analyze_session_patterns(touchpoints)
        
        return {
            'hourly_distribution': dict(hourly_usage),
            'daily_distribution': dict(daily_usage),
            'peak_hours': [h[0] for h in peak_hours],
            'peak_days': [d[0] for d in peak_days],
            'usage_intensity': usage_intensity,
            'session_patterns': session_analysis,
            'usage_regularity': self._calculate_usage_regularity(temporal_data),
            'binge_usage_events': self._identify_binge_usage(touchpoints)
        }
    
    def _analyze_feature_adoption(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feature adoption and usage patterns"""
        touchpoints = behavior_data['touchpoints']
        
        # Group touchpoints by feature/functionality
        feature_usage = defaultdict(list)
        for touchpoint in touchpoints:
            if touchpoint['metric'] in ['feature_clicks', 'page_views']:
                feature = touchpoint['properties'].get('feature', 'unknown')
                feature_usage[feature].append(touchpoint)
        
        # Calculate adoption metrics
        total_features_available = 20  # This would come from product configuration
        adopted_features = len([f for f in feature_usage if len(feature_usage[f]) >= 3])
        adoption_rate = adopted_features / total_features_available
        
        # Analyze adoption timeline
        adoption_timeline = {}
        for feature, usage_events in feature_usage.items():
            if usage_events:
                first_use = min(e['timestamp'] for e in usage_events)
                adoption_timeline[feature] = first_use
        
        # Calculate feature stickiness (repeated usage)
        feature_stickiness = {}
        for feature, usage_events in feature_usage.items():
            unique_days = len(set(e['timestamp'].date() for e in usage_events))
            total_days = (max(e['timestamp'] for e in usage_events) - 
                         min(e['timestamp'] for e in usage_events)).days + 1 if usage_events else 1
            feature_stickiness[feature] = unique_days / total_days
        
        return {
            'total_features_used': len(feature_usage),
            'adoption_rate': adoption_rate,
            'feature_usage_counts': {f: len(events) for f, events in feature_usage.items()},
            'adoption_timeline': adoption_timeline,
            'feature_stickiness': feature_stickiness,
            'power_features': self._identify_power_features(feature_usage),
            'abandoned_features': self._identify_abandoned_features(feature_usage)
        }
    
    def _calculate_engagement_score(self, engagement_metrics: Dict[str, Any]) -> float:
        """Calculate overall engagement score (0-100)"""
        if not engagement_metrics:
            return 0.0
        
        # Normalize individual metrics
        touchpoint_score = min(engagement_metrics.get('avg_daily_touchpoints', 0) / 10, 1.0)
        consistency_score = 1.0 - min(engagement_metrics.get('engagement_consistency', 0) / 5, 1.0)
        depth_score = min(engagement_metrics.get('avg_session_depth', 0) / 20, 1.0)
        recency_score = min(engagement_metrics.get('recent_engagement', 0) / 5, 1.0)
        
        # Weighted combination
        weights = [0.3, 0.2, 0.3, 0.2]
        scores = [touchpoint_score, consistency_score, depth_score, recency_score]
        
        engagement_score = sum(score * weight for score, weight in zip(scores, weights)) * 100
        return min(max(engagement_score, 0), 100)
    
    def _load_behavior_weights(self) -> Dict[str, float]:
        """Load behavior importance weights"""
        return {
            'engagement': 0.25,
            'usage_pattern': 0.20,
            'feature_adoption': 0.20,
            'payment_behavior': 0.15,
            'support_interaction': 0.10,
            'social_behavior': 0.05,
            'content_consumption': 0.05
        }
    
    def _load_segment_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load customer segment definitions"""
        return {
            'power_user': {
                'min_engagement_score': 80,
                'min_usage_intensity': 0.8,
                'min_feature_adoption': 0.7,
                'max_churn_risk': 0.2
            },
            'casual_user': {
                'min_engagement_score': 40,
                'max_engagement_score': 80,
                'min_usage_intensity': 0.3,
                'max_usage_intensity': 0.8
            },
            'at_risk_user': {
                'min_churn_risk': 0.7,
                'max_engagement_score': 60
            },
            'new_user': {
                'max_days_since_first_touchpoint': 30,
                'min_engagement_score': 20
            }
        }
    
    def _load_pattern_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load behavior pattern templates for recognition"""
        return {
            'daily_routine': {
                'description': 'Regular daily usage pattern',
                'indicators': ['consistent_hourly_usage', 'weekday_pattern'],
                'min_occurrences': 7
            },
            'weekend_warrior': {
                'description': 'Primarily weekend usage',
                'indicators': ['weekend_heavy_usage', 'weekday_light_usage'],
                'min_occurrences': 4
            },
            'binge_user': {
                'description': 'Intensive usage followed by quiet periods',
                'indicators': ['usage_spikes', 'quiet_periods'],
                'min_occurrences': 3
            },
            'exploration_phase': {
                'description': 'High feature exploration activity',
                'indicators': ['diverse_feature_usage', 'increasing_adoption'],
                'min_occurrences': 5
            }
        }
    
    # Additional helper methods would continue here...
    # For brevity, I'm including key methods but the full implementation would have more

    def _create_minimal_profile(self, customer_id: str, organization_id: str) -> CustomerBehaviorProfile:
        """Create minimal profile for customers with no data"""
        return CustomerBehaviorProfile(
            customer_id=customer_id,
            organization_id=organization_id,
            profile_date=datetime.now(),
            behavior_segment=BehaviorSegment.NEW_USER,
            engagement_score=0.0,
            usage_intensity=0.0,
            feature_adoption_rate=0.0,
            behavior_consistency=0.0,
            risk_indicators={'no_data': 1.0},
            behavior_patterns=[],
            predicted_actions=[],
            recommendations=[{
                'type': 'onboarding',
                'title': 'Welcome and onboard new customer',
                'description': 'No behavioral data available - prioritize onboarding',
                'priority': 'high'
            }],
            metadata={'no_data': True}
        )

# Global behavioral analysis engine
behavior_engine = BehavioralAnalysisEngine()

def get_behavior_engine() -> BehavioralAnalysisEngine:
    """Get the global behavioral analysis engine"""
    return behavior_engine

# Convenience functions
def analyze_customer_behavior(customer_id: str, organization_id: str) -> CustomerBehaviorProfile:
    """Analyze customer behavioral patterns"""
    engine = get_behavior_engine()
    return engine.analyze_customer_behavior(customer_id, organization_id)

def segment_customers_by_behavior(organization_id: str) -> List[BehaviorCluster]:
    """Segment customers based on behavioral patterns"""
    engine = get_behavior_engine()
    return engine.segment_customers_by_behavior(organization_id)

def generate_behavior_insights(organization_id: str) -> List[BehaviorInsight]:
    """Generate behavioral insights for organization"""
    engine = get_behavior_engine()
    return engine.generate_behavior_insights(organization_id)

def predict_customer_behavior(customer_id: str, organization_id: str) -> Dict[str, Any]:
    """Predict customer behavior patterns"""
    engine = get_behavior_engine()
    return engine.predict_customer_behavior(customer_id, organization_id)