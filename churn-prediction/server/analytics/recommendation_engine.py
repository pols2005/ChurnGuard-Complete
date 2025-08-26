# ChurnGuard AI-Powered Recommendation Engine
# Epic 4 - Advanced Analytics & AI Insights

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict
import math

from .statistical_analysis import get_stats_service
from .insight_generator import get_insight_generator, InsightType, InsightSeverity
from .time_series_db import get_time_series_db
from .data_aggregator import get_aggregation_pipeline, AggregationLevel

logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    IMMEDIATE_ACTION = "immediate_action"
    PROCESS_IMPROVEMENT = "process_improvement"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    PREDICTIVE_INTERVENTION = "predictive_intervention"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_MITIGATION = "risk_mitigation"

class RecommendationPriority(Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RecommendationCategory(Enum):
    CUSTOMER_RETENTION = "customer_retention"
    REVENUE_OPTIMIZATION = "revenue_optimization"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    CUSTOMER_EXPERIENCE = "customer_experience"
    DATA_QUALITY = "data_quality"

@dataclass
class Recommendation:
    """AI-generated business recommendation"""
    id: str
    type: RecommendationType
    priority: RecommendationPriority
    category: RecommendationCategory
    title: str
    description: str
    detailed_explanation: str
    rationale: str
    expected_impact: str
    implementation_steps: List[str]
    estimated_effort: str  # "low", "medium", "high"
    time_to_implement: str  # "days", "weeks", "months"
    success_metrics: List[str]
    confidence_score: float
    organization_id: str
    triggered_by_insights: List[str]  # Insight IDs
    related_metrics: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class RecommendationRule:
    """Rule for generating recommendations"""
    id: str
    conditions: Dict[str, Any]
    recommendation_template: Dict[str, Any]
    enabled: bool = True

class AIRecommendationEngine:
    """
    AI-powered recommendation engine for ChurnGuard analytics
    
    Features:
    - Context-aware business recommendations
    - Multi-criteria decision making (ROI, effort, impact)
    - Predictive intervention recommendations
    - Process optimization suggestions
    - Resource allocation recommendations
    - Risk mitigation strategies
    - Implementation roadmaps with success metrics
    """
    
    def __init__(self):
        self.stats_service = get_stats_service()
        self.insight_generator = get_insight_generator()
        self.ts_db = get_time_series_db()
        self.aggregation_pipeline = get_aggregation_pipeline()
        
        # Load recommendation rules and templates
        self.recommendation_rules = self._load_recommendation_rules()
        self.impact_models = self._load_impact_models()
        
        # Cache for generated recommendations
        self.recommendations_cache: Dict[str, List[Recommendation]] = defaultdict(list)
        
        # Business context for different industries/use cases
        self.business_contexts = self._load_business_contexts()
        
    def generate_recommendations(self, organization_id: str,
                               time_window_hours: int = 24,
                               max_recommendations: int = 20) -> List[Recommendation]:
        """
        Generate comprehensive AI-powered recommendations
        
        Args:
            organization_id: Organization ID
            time_window_hours: Time window for analysis
            max_recommendations: Maximum number of recommendations to generate
            
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        # Get recent insights as input for recommendations
        insights = self.insight_generator.generate_insights(
            organization_id, time_window_hours=time_window_hours
        )
        
        # Generate recommendations based on insights
        insight_based_recs = self._generate_insight_based_recommendations(
            organization_id, insights
        )
        recommendations.extend(insight_based_recs)
        
        # Generate proactive recommendations based on patterns
        pattern_based_recs = self._generate_pattern_based_recommendations(
            organization_id, time_window_hours
        )
        recommendations.extend(pattern_based_recs)
        
        # Generate optimization recommendations
        optimization_recs = self._generate_optimization_recommendations(
            organization_id, insights
        )
        recommendations.extend(optimization_recs)
        
        # Score and prioritize recommendations
        recommendations = self._score_and_prioritize_recommendations(recommendations)
        
        # Apply business rules and filters
        recommendations = self._apply_business_filters(recommendations, organization_id)
        
        # Limit to requested number
        recommendations = recommendations[:max_recommendations]
        
        # Cache recommendations
        cache_key = f"{organization_id}:{time_window_hours}h"
        self.recommendations_cache[cache_key] = recommendations
        
        logger.info(f"Generated {len(recommendations)} recommendations for organization {organization_id}")
        
        return recommendations
    
    def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """Get a specific recommendation by ID"""
        for rec_list in self.recommendations_cache.values():
            for rec in rec_list:
                if rec.id == recommendation_id:
                    return rec
        return None
    
    def generate_action_plan(self, organization_id: str, 
                           selected_recommendation_ids: List[str]) -> Dict[str, Any]:
        """
        Generate implementation action plan for selected recommendations
        
        Args:
            organization_id: Organization ID
            selected_recommendation_ids: List of recommendation IDs to implement
            
        Returns:
            Comprehensive action plan with timeline and resource allocation
        """
        selected_recommendations = []
        
        for rec_id in selected_recommendation_ids:
            rec = self.get_recommendation_by_id(rec_id)
            if rec:
                selected_recommendations.append(rec)
        
        if not selected_recommendations:
            return {'error': 'No valid recommendations found'}
        
        # Sort by priority and dependencies
        sorted_recs = self._sort_recommendations_by_dependencies(selected_recommendations)
        
        # Create timeline
        timeline = self._create_implementation_timeline(sorted_recs)
        
        # Estimate resource requirements
        resource_requirements = self._estimate_resource_requirements(sorted_recs)
        
        # Calculate expected ROI
        expected_roi = self._calculate_expected_roi(sorted_recs)
        
        # Generate success metrics
        success_metrics = self._consolidate_success_metrics(sorted_recs)
        
        return {
            'action_plan_id': f"plan_{organization_id}_{int(datetime.now().timestamp())}",
            'organization_id': organization_id,
            'created_at': datetime.now().isoformat(),
            'selected_recommendations': len(selected_recommendations),
            'implementation_timeline': timeline,
            'resource_requirements': resource_requirements,
            'expected_roi': expected_roi,
            'success_metrics': success_metrics,
            'total_estimated_effort': self._calculate_total_effort(sorted_recs),
            'implementation_phases': self._create_implementation_phases(sorted_recs),
            'risk_assessment': self._assess_implementation_risks(sorted_recs)
        }
    
    def _generate_insight_based_recommendations(self, organization_id: str,
                                              insights: List) -> List[Recommendation]:
        """Generate recommendations based on insights"""
        recommendations = []
        
        for insight in insights:
            if insight.severity in [InsightSeverity.CRITICAL, InsightSeverity.HIGH]:
                # Generate urgent action recommendations
                if insight.type == InsightType.TREND:
                    trend_recs = self._generate_trend_recommendations(organization_id, insight)
                    recommendations.extend(trend_recs)
                
                elif insight.type == InsightType.ANOMALY:
                    anomaly_recs = self._generate_anomaly_recommendations(organization_id, insight)
                    recommendations.extend(anomaly_recs)
                
                elif insight.type == InsightType.PREDICTION:
                    prediction_recs = self._generate_prediction_recommendations(organization_id, insight)
                    recommendations.extend(prediction_recs)
        
        return recommendations
    
    def _generate_trend_recommendations(self, organization_id: str, insight) -> List[Recommendation]:
        """Generate recommendations based on trend insights"""
        recommendations = []
        
        if 'churn' in insight.metric_name.lower():
            if insight.data_points['direction'] == 'increasing':
                # High-priority churn intervention
                rec = Recommendation(
                    id=f"trend_churn_intervention_{organization_id}_{int(datetime.now().timestamp())}",
                    type=RecommendationType.IMMEDIATE_ACTION,
                    priority=RecommendationPriority.URGENT,
                    category=RecommendationCategory.CUSTOMER_RETENTION,
                    title="Implement Immediate Churn Intervention Program",
                    description="Deploy targeted retention campaigns for at-risk customers",
                    detailed_explanation=f"The increasing trend in {insight.metric_name} (slope: {insight.data_points['slope']:.4f}) indicates escalating churn risk. Immediate intervention is required to prevent customer loss.",
                    rationale=f"Statistical analysis shows {insight.data_points['trend_strength']:.1%} confidence in the upward trend. Early intervention can reduce churn by 15-25%.",
                    expected_impact="Potential 20-30% reduction in customer churn within 30 days",
                    implementation_steps=[
                        "Identify customers with highest churn risk scores",
                        "Deploy personalized retention offers and communications",
                        "Assign dedicated account managers to high-value at-risk customers",
                        "Implement proactive customer success outreach",
                        "Monitor daily churn metrics and adjust strategies"
                    ],
                    estimated_effort="medium",
                    time_to_implement="days",
                    success_metrics=[
                        "Daily churn rate reduction",
                        "Customer retention rate improvement", 
                        "Revenue at risk decrease",
                        "Customer satisfaction scores"
                    ],
                    confidence_score=insight.confidence_score,
                    organization_id=organization_id,
                    triggered_by_insights=[insight.id],
                    related_metrics=[insight.metric_name, 'customer_retention_rate', 'revenue_at_risk'],
                    timestamp=datetime.now(),
                    metadata={
                        'trend_slope': insight.data_points['slope'],
                        'trend_strength': insight.data_points['trend_strength'],
                        'business_impact': 'high_priority'
                    }
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_anomaly_recommendations(self, organization_id: str, insight) -> List[Recommendation]:
        """Generate recommendations based on anomaly insights"""
        recommendations = []
        
        # Data quality investigation recommendation
        rec = Recommendation(
            id=f"anomaly_investigation_{organization_id}_{int(datetime.now().timestamp())}",
            type=RecommendationType.IMMEDIATE_ACTION,
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.DATA_QUALITY,
            title="Investigate Data Anomalies and Quality Issues",
            description="Conduct thorough investigation of detected anomalies to ensure data integrity",
            detailed_explanation=f"Multiple anomalies detected in {insight.metric_name} using {insight.data_points['method']} analysis. These outliers may indicate data collection issues, system problems, or genuine business events requiring attention.",
            rationale=f"Anomaly rate of {insight.data_points['anomaly_rate']:.1%} exceeds normal thresholds. Quick resolution prevents cascading data quality issues.",
            expected_impact="Improved data reliability and more accurate analytics",
            implementation_steps=[
                "Review data collection processes during anomaly periods",
                "Check system logs for errors or unusual events",
                "Validate data sources and integration points",
                "Interview stakeholders about business events during anomaly times",
                "Implement additional data validation rules if needed"
            ],
            estimated_effort="low",
            time_to_implement="days",
            success_metrics=[
                "Anomaly rate reduction",
                "Data quality score improvement",
                "System reliability metrics",
                "Stakeholder confidence in analytics"
            ],
            confidence_score=insight.confidence_score,
            organization_id=organization_id,
            triggered_by_insights=[insight.id],
            related_metrics=[insight.metric_name],
            timestamp=datetime.now(),
            metadata={
                'anomaly_count': insight.data_points['anomaly_count'],
                'detection_method': insight.data_points['method']
            }
        )
        recommendations.append(rec)
        
        return recommendations
    
    def _generate_prediction_recommendations(self, organization_id: str, insight) -> List[Recommendation]:
        """Generate recommendations based on prediction insights"""
        recommendations = []
        
        change_percent = abs(insight.data_points['change_percent'])
        
        if change_percent > 20:  # Significant predicted change
            rec = Recommendation(
                id=f"prediction_prep_{organization_id}_{int(datetime.now().timestamp())}",
                type=RecommendationType.PREDICTIVE_INTERVENTION,
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.PREDICTIVE_ANALYTICS,
                title="Prepare for Predicted Metric Changes",
                description=f"Proactive measures for predicted {change_percent:.1f}% change in {insight.metric_name}",
                detailed_explanation=f"Forecasting models predict a {change_percent:.1f}% change in {insight.metric_name} within 24 hours. Proactive preparation can minimize negative impact or maximize positive outcomes.",
                rationale=f"Prediction confidence of {insight.data_points['prediction_confidence']:.1%} warrants preventive action.",
                expected_impact="Reduced impact of predicted changes through proactive measures",
                implementation_steps=[
                    "Alert relevant teams about predicted changes",
                    "Prepare contingency plans and resources",
                    "Monitor leading indicators for early confirmation",
                    "Adjust operational capacity if needed",
                    "Communicate with stakeholders about potential impacts"
                ],
                estimated_effort="medium",
                time_to_implement="days",
                success_metrics=[
                    "Actual vs predicted variance",
                    "Response time to changes",
                    "Impact mitigation effectiveness",
                    "Stakeholder satisfaction"
                ],
                confidence_score=insight.confidence_score,
                organization_id=organization_id,
                triggered_by_insights=[insight.id],
                related_metrics=[insight.metric_name],
                timestamp=datetime.now(),
                metadata={
                    'predicted_change': insight.data_points['change_percent'],
                    'prediction_horizon': '24h'
                }
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_pattern_based_recommendations(self, organization_id: str,
                                              time_window_hours: int) -> List[Recommendation]:
        """Generate recommendations based on data patterns"""
        recommendations = []
        
        # Analyze metric patterns
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        # Check for optimization opportunities
        metrics = ['customer_activity', 'model_accuracy', 'prediction_confidence']
        
        for metric_name in metrics:
            try:
                data = self.ts_db.query(metric_name, organization_id, start_time, end_time)
                
                if not data.empty and len(data) > 5:
                    stats = self.stats_service.descriptive_statistics(data['value'].tolist())
                    
                    # Generate recommendations based on statistical patterns
                    if stats.std > stats.mean * 0.5:  # High variability
                        rec = self._create_variability_recommendation(
                            organization_id, metric_name, stats
                        )
                        if rec:
                            recommendations.append(rec)
                    
                    # Check for suboptimal performance
                    if metric_name == 'model_accuracy' and stats.mean < 0.8:
                        rec = self._create_model_improvement_recommendation(
                            organization_id, stats
                        )
                        if rec:
                            recommendations.append(rec)
            
            except Exception as e:
                logger.error(f"Error analyzing pattern for {metric_name}: {e}")
        
        return recommendations
    
    def _generate_optimization_recommendations(self, organization_id: str,
                                             insights: List) -> List[Recommendation]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Process optimization recommendation
        rec = Recommendation(
            id=f"process_optimization_{organization_id}_{int(datetime.now().timestamp())}",
            type=RecommendationType.PROCESS_IMPROVEMENT,
            priority=RecommendationPriority.MEDIUM,
            category=RecommendationCategory.OPERATIONAL_EFFICIENCY,
            title="Optimize Analytics and Prediction Workflows",
            description="Streamline analytical processes for better efficiency and accuracy",
            detailed_explanation="Based on current performance patterns, optimizing analytical workflows can improve prediction accuracy, reduce processing time, and enhance decision-making speed.",
            rationale="Regular process optimization maintains competitive advantage and operational efficiency.",
            expected_impact="15-25% improvement in analytical efficiency and accuracy",
            implementation_steps=[
                "Audit current analytical workflows and bottlenecks",
                "Implement automated data quality checks",
                "Optimize model training and prediction pipelines",
                "Establish regular model performance reviews",
                "Create automated alerting for performance degradation"
            ],
            estimated_effort="high",
            time_to_implement="weeks",
            success_metrics=[
                "Analytics processing time reduction",
                "Model accuracy improvement",
                "User satisfaction with analytics tools",
                "Cost per prediction reduction"
            ],
            confidence_score=0.8,
            organization_id=organization_id,
            triggered_by_insights=[],
            related_metrics=['model_accuracy', 'prediction_confidence', 'processing_time'],
            timestamp=datetime.now(),
            metadata={'recommendation_type': 'proactive_optimization'}
        )
        recommendations.append(rec)
        
        return recommendations
    
    def _create_variability_recommendation(self, organization_id: str, 
                                         metric_name: str, stats) -> Optional[Recommendation]:
        """Create recommendation for high variability metrics"""
        return Recommendation(
            id=f"variability_reduction_{organization_id}_{metric_name}_{int(datetime.now().timestamp())}",
            type=RecommendationType.PROCESS_IMPROVEMENT,
            priority=RecommendationPriority.MEDIUM,
            category=RecommendationCategory.OPERATIONAL_EFFICIENCY,
            title=f"Reduce Variability in {metric_name.replace('_', ' ').title()}",
            description="Implement process improvements to reduce metric variability",
            detailed_explanation=f"High variability (std: {stats.std:.3f}, mean: {stats.mean:.3f}) in {metric_name} indicates inconsistent processes that can be optimized for better predictability.",
            rationale="Consistent processes lead to more reliable predictions and better business outcomes.",
            expected_impact="20-30% reduction in process variability",
            implementation_steps=[
                "Identify root causes of variability",
                "Standardize processes and procedures",
                "Implement quality control measures",
                "Train team members on consistent practices",
                "Monitor variability metrics regularly"
            ],
            estimated_effort="medium",
            time_to_implement="weeks",
            success_metrics=[
                f"{metric_name}_variability_reduction",
                "Process consistency score",
                "Prediction reliability improvement"
            ],
            confidence_score=0.7,
            organization_id=organization_id,
            triggered_by_insights=[],
            related_metrics=[metric_name],
            timestamp=datetime.now(),
            metadata={'variability_ratio': stats.std / stats.mean}
        )
    
    def _create_model_improvement_recommendation(self, organization_id: str, 
                                               stats) -> Optional[Recommendation]:
        """Create recommendation for improving model accuracy"""
        return Recommendation(
            id=f"model_improvement_{organization_id}_{int(datetime.now().timestamp())}",
            type=RecommendationType.STRATEGY_OPTIMIZATION,
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.PREDICTIVE_ANALYTICS,
            title="Improve Machine Learning Model Performance",
            description="Enhance model accuracy through optimization and retraining",
            detailed_explanation=f"Current model accuracy of {stats.mean:.1%} is below optimal performance. Implementing model improvements can significantly enhance prediction quality.",
            rationale="Higher model accuracy directly translates to better business decisions and outcomes.",
            expected_impact="10-15% improvement in model accuracy and prediction reliability",
            implementation_steps=[
                "Conduct comprehensive model performance analysis",
                "Gather additional training data if needed",
                "Experiment with different algorithms and hyperparameters",
                "Implement feature engineering improvements",
                "Set up automated model retraining pipeline",
                "Establish model performance monitoring"
            ],
            estimated_effort="high",
            time_to_implement="weeks",
            success_metrics=[
                "Model accuracy improvement",
                "Prediction precision and recall",
                "Business outcome correlation",
                "Model confidence scores"
            ],
            confidence_score=0.9,
            organization_id=organization_id,
            triggered_by_insights=[],
            related_metrics=['model_accuracy', 'prediction_confidence'],
            timestamp=datetime.now(),
            metadata={'current_accuracy': stats.mean}
        )
    
    def _score_and_prioritize_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Score and prioritize recommendations"""
        # Priority weights
        priority_weights = {
            RecommendationPriority.URGENT: 4,
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 1
        }
        
        # Effort weights (lower effort = higher score)
        effort_weights = {
            'low': 3,
            'medium': 2,
            'high': 1
        }
        
        # Calculate composite scores
        for rec in recommendations:
            priority_score = priority_weights[rec.priority]
            effort_score = effort_weights.get(rec.estimated_effort, 2)
            confidence_score = rec.confidence_score
            
            # Composite score: (priority * confidence * effort_factor)
            rec.metadata['composite_score'] = priority_score * confidence_score * effort_score
        
        # Sort by composite score descending
        return sorted(recommendations, key=lambda x: x.metadata['composite_score'], reverse=True)
    
    def _apply_business_filters(self, recommendations: List[Recommendation],
                               organization_id: str) -> List[Recommendation]:
        """Apply business-specific filters"""
        # Remove duplicates by category and type
        seen_combinations = set()
        filtered_recommendations = []
        
        for rec in recommendations:
            combination = (rec.category, rec.type)
            if combination not in seen_combinations:
                seen_combinations.add(combination)
                filtered_recommendations.append(rec)
        
        return filtered_recommendations
    
    def _sort_recommendations_by_dependencies(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Sort recommendations considering dependencies"""
        # Simple dependency sorting - immediate actions first, then strategic
        priority_order = [
            RecommendationType.IMMEDIATE_ACTION,
            RecommendationType.PREDICTIVE_INTERVENTION,
            RecommendationType.RISK_MITIGATION,
            RecommendationType.PROCESS_IMPROVEMENT,
            RecommendationType.STRATEGY_OPTIMIZATION,
            RecommendationType.RESOURCE_ALLOCATION
        ]
        
        sorted_recs = []
        for rec_type in priority_order:
            type_recs = [r for r in recommendations if r.type == rec_type]
            sorted_recs.extend(sorted(type_recs, key=lambda x: x.metadata['composite_score'], reverse=True))
        
        return sorted_recs
    
    def _create_implementation_timeline(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Create implementation timeline for recommendations"""
        timeline = {
            'immediate': [],  # 1-7 days
            'short_term': [], # 1-4 weeks
            'medium_term': [], # 1-3 months
            'long_term': []   # 3+ months
        }
        
        for rec in recommendations:
            if rec.time_to_implement == 'days':
                timeline['immediate'].append({
                    'id': rec.id,
                    'title': rec.title,
                    'estimated_duration': '1-7 days'
                })
            elif rec.time_to_implement == 'weeks':
                timeline['short_term'].append({
                    'id': rec.id,
                    'title': rec.title,
                    'estimated_duration': '1-4 weeks'
                })
            else:
                timeline['medium_term'].append({
                    'id': rec.id,
                    'title': rec.title,
                    'estimated_duration': '1-3 months'
                })
        
        return timeline
    
    def _estimate_resource_requirements(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Estimate resource requirements"""
        effort_counts = {'low': 0, 'medium': 0, 'high': 0}
        
        for rec in recommendations:
            effort_counts[rec.estimated_effort] += 1
        
        return {
            'total_recommendations': len(recommendations),
            'effort_distribution': effort_counts,
            'estimated_team_weeks': effort_counts['low'] * 0.5 + effort_counts['medium'] * 2 + effort_counts['high'] * 8,
            'recommended_team_size': min(max(2, len(recommendations) // 3), 8)
        }
    
    def _calculate_expected_roi(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Calculate expected ROI for recommendations"""
        # Simplified ROI calculation based on impact categories
        impact_values = {
            RecommendationCategory.CUSTOMER_RETENTION: 50000,  # Expected annual value
            RecommendationCategory.REVENUE_OPTIMIZATION: 75000,
            RecommendationCategory.OPERATIONAL_EFFICIENCY: 25000,
            RecommendationCategory.PREDICTIVE_ANALYTICS: 30000,
            RecommendationCategory.CUSTOMER_EXPERIENCE: 40000,
            RecommendationCategory.DATA_QUALITY: 15000
        }
        
        total_expected_value = sum(
            impact_values.get(rec.category, 20000) * rec.confidence_score
            for rec in recommendations
        )
        
        estimated_investment = len(recommendations) * 5000  # Average cost per recommendation
        
        roi_ratio = total_expected_value / estimated_investment if estimated_investment > 0 else 0
        
        return {
            'estimated_total_value': total_expected_value,
            'estimated_investment': estimated_investment,
            'roi_ratio': roi_ratio,
            'payback_period_months': 12 / roi_ratio if roi_ratio > 0 else 'undefined'
        }
    
    def _consolidate_success_metrics(self, recommendations: List[Recommendation]) -> List[str]:
        """Consolidate success metrics from all recommendations"""
        all_metrics = []
        for rec in recommendations:
            all_metrics.extend(rec.success_metrics)
        
        # Remove duplicates and return unique metrics
        return list(set(all_metrics))
    
    def _calculate_total_effort(self, recommendations: List[Recommendation]) -> Dict[str, int]:
        """Calculate total effort breakdown"""
        effort_counts = {'low': 0, 'medium': 0, 'high': 0}
        
        for rec in recommendations:
            effort_counts[rec.estimated_effort] += 1
        
        return effort_counts
    
    def _create_implementation_phases(self, recommendations: List[Recommendation]) -> List[Dict[str, Any]]:
        """Create implementation phases"""
        phases = []
        
        # Phase 1: Immediate actions
        immediate_recs = [r for r in recommendations if r.type == RecommendationType.IMMEDIATE_ACTION]
        if immediate_recs:
            phases.append({
                'phase': 1,
                'name': 'Immediate Actions',
                'duration': '1-2 weeks',
                'recommendations': [{'id': r.id, 'title': r.title} for r in immediate_recs],
                'key_outcomes': ['Stabilize critical issues', 'Prevent immediate risks']
            })
        
        # Phase 2: Process improvements
        process_recs = [r for r in recommendations if r.type == RecommendationType.PROCESS_IMPROVEMENT]
        if process_recs:
            phases.append({
                'phase': 2,
                'name': 'Process Improvements',
                'duration': '4-8 weeks',
                'recommendations': [{'id': r.id, 'title': r.title} for r in process_recs],
                'key_outcomes': ['Improve operational efficiency', 'Standardize processes']
            })
        
        # Phase 3: Strategic optimizations
        strategy_recs = [r for r in recommendations if r.type == RecommendationType.STRATEGY_OPTIMIZATION]
        if strategy_recs:
            phases.append({
                'phase': 3,
                'name': 'Strategic Optimizations',
                'duration': '2-6 months',
                'recommendations': [{'id': r.id, 'title': r.title} for r in strategy_recs],
                'key_outcomes': ['Long-term competitive advantage', 'Scalable improvements']
            })
        
        return phases
    
    def _assess_implementation_risks(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Assess risks in implementing recommendations"""
        risks = {
            'low_risk_count': 0,
            'medium_risk_count': 0,
            'high_risk_count': 0,
            'risk_factors': []
        }
        
        for rec in recommendations:
            if rec.estimated_effort == 'high':
                risks['high_risk_count'] += 1
                risks['risk_factors'].append(f"High implementation effort for {rec.title}")
            elif rec.confidence_score < 0.6:
                risks['medium_risk_count'] += 1
                risks['risk_factors'].append(f"Lower confidence in {rec.title}")
            else:
                risks['low_risk_count'] += 1
        
        return risks
    
    def _load_recommendation_rules(self) -> List[RecommendationRule]:
        """Load recommendation generation rules"""
        # In production, this would load from configuration files or database
        return []
    
    def _load_impact_models(self) -> Dict[str, Any]:
        """Load impact estimation models"""
        # In production, this would load trained models for impact estimation
        return {}
    
    def _load_business_contexts(self) -> Dict[str, Any]:
        """Load business context configurations"""
        return {
            'default': {
                'churn_threshold': 0.05,
                'revenue_impact_threshold': 10000,
                'customer_value_tiers': ['low', 'medium', 'high', 'enterprise']
            }
        }

# Global recommendation engine instance
recommendation_engine = AIRecommendationEngine()

def get_recommendation_engine() -> AIRecommendationEngine:
    """Get the global recommendation engine instance"""
    return recommendation_engine

# Convenience functions
def generate_recommendations(organization_id: str, hours: int = 24) -> List[Recommendation]:
    """Generate recommendations for an organization"""
    engine = get_recommendation_engine()
    return engine.generate_recommendations(organization_id, time_window_hours=hours)

def create_action_plan(organization_id: str, recommendation_ids: List[str]) -> Dict[str, Any]:
    """Create implementation action plan"""
    engine = get_recommendation_engine()
    return engine.generate_action_plan(organization_id, recommendation_ids)