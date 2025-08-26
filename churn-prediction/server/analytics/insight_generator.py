# ChurnGuard Natural Language Insight Generator  
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
import re

from .statistical_analysis import get_stats_service, TrendAnalysis, SeasonalityAnalysis, AnomalyDetectionResult
from .data_aggregator import get_aggregation_pipeline, AggregationLevel
from .time_series_db import get_time_series_db

logger = logging.getLogger(__name__)

class InsightType(Enum):
    TREND = "trend"
    ANOMALY = "anomaly"
    SEASONAL = "seasonal"
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"

class InsightSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Insight:
    """A natural language insight generated from data analysis"""
    id: str
    type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    narrative: str
    data_points: Dict[str, Any]
    confidence_score: float
    organization_id: str
    metric_name: str
    timestamp: datetime
    recommendations: List[str]
    related_metrics: List[str]
    metadata: Dict[str, Any]

class NaturalLanguageInsightGenerator:
    """
    AI-powered insight generator that creates human-readable insights from analytics data
    
    Features:
    - Natural language generation for complex data patterns
    - Contextual business insights and recommendations
    - Multi-metric correlation analysis
    - Trend interpretation and forecasting insights
    - Anomaly explanation and impact assessment
    - Seasonal pattern recognition and planning insights
    - Automated insight prioritization and scoring
    """
    
    def __init__(self):
        self.stats_service = get_stats_service()
        self.aggregation_pipeline = get_aggregation_pipeline()
        self.ts_db = get_time_series_db()
        
        # Insight templates for different types
        self.insight_templates = self._load_insight_templates()
        
        # Business context mappings
        self.business_context = self._load_business_context()
        
        # Generated insights cache
        self.insights_cache: Dict[str, List[Insight]] = defaultdict(list)
        
    def generate_insights(self, organization_id: str, 
                         metrics: Optional[List[str]] = None,
                         time_window_hours: int = 24) -> List[Insight]:
        """
        Generate comprehensive insights for an organization's metrics
        
        Args:
            organization_id: Organization ID
            metrics: List of specific metrics to analyze (None for all)
            time_window_hours: Time window for analysis
            
        Returns:
            List of generated insights sorted by severity and confidence
        """
        insights = []
        
        # Get available metrics for organization
        if metrics is None:
            metrics = self._get_available_metrics(organization_id)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        for metric_name in metrics:
            try:
                # Get metric data
                metric_data = self.ts_db.query(
                    metric_name, organization_id, start_time, end_time
                )
                
                if metric_data.empty:
                    continue
                
                # Generate different types of insights
                metric_insights = []
                
                # Trend insights
                trend_insights = self._generate_trend_insights(
                    metric_name, organization_id, metric_data
                )
                metric_insights.extend(trend_insights)
                
                # Anomaly insights
                anomaly_insights = self._generate_anomaly_insights(
                    metric_name, organization_id, metric_data
                )
                metric_insights.extend(anomaly_insights)
                
                # Seasonal insights
                seasonal_insights = self._generate_seasonal_insights(
                    metric_name, organization_id, metric_data
                )
                metric_insights.extend(seasonal_insights)
                
                # Prediction insights
                prediction_insights = self._generate_prediction_insights(
                    metric_name, organization_id, metric_data
                )
                metric_insights.extend(prediction_insights)
                
                insights.extend(metric_insights)
                
            except Exception as e:
                logger.error(f"Error generating insights for {metric_name}: {e}")
        
        # Generate correlation insights across metrics
        if len(metrics) > 1:
            correlation_insights = self._generate_correlation_insights(
                organization_id, metrics, start_time, end_time
            )
            insights.extend(correlation_insights)
        
        # Score and sort insights
        insights = self._score_and_sort_insights(insights)
        
        # Cache insights
        cache_key = f"{organization_id}:{time_window_hours}:{','.join(sorted(metrics))}"
        self.insights_cache[cache_key] = insights
        
        return insights
    
    def get_insight_by_id(self, insight_id: str) -> Optional[Insight]:
        """Get a specific insight by ID"""
        for insights_list in self.insights_cache.values():
            for insight in insights_list:
                if insight.id == insight_id:
                    return insight
        return None
    
    def generate_summary_report(self, organization_id: str, 
                              time_period: str = "24h") -> Dict[str, Any]:
        """
        Generate a comprehensive summary report with key insights
        
        Args:
            organization_id: Organization ID
            time_period: Time period for analysis ("24h", "7d", "30d")
            
        Returns:
            Summary report with key insights and recommendations
        """
        # Parse time period
        if time_period == "24h":
            hours = 24
        elif time_period == "7d":
            hours = 168
        elif time_period == "30d":
            hours = 720
        else:
            hours = 24
        
        insights = self.generate_insights(organization_id, time_window_hours=hours)
        
        # Categorize insights
        categorized = {
            'critical_alerts': [i for i in insights if i.severity == InsightSeverity.CRITICAL],
            'high_priority': [i for i in insights if i.severity == InsightSeverity.HIGH],
            'trends': [i for i in insights if i.type == InsightType.TREND],
            'anomalies': [i for i in insights if i.type == InsightType.ANOMALY],
            'recommendations': [i for i in insights if i.type == InsightType.RECOMMENDATION]
        }
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(categorized)
        
        # Key metrics summary
        key_metrics = self._generate_key_metrics_summary(organization_id, hours)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'time_period': time_period,
            'organization_id': organization_id,
            'executive_summary': executive_summary,
            'key_metrics': key_metrics,
            'insights_by_category': categorized,
            'total_insights': len(insights),
            'confidence_distribution': self._calculate_confidence_distribution(insights)
        }
    
    def _generate_trend_insights(self, metric_name: str, organization_id: str, 
                                data: pd.DataFrame) -> List[Insight]:
        """Generate trend-based insights"""
        insights = []
        
        if len(data) < 3:
            return insights
        
        # Analyze trend
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        values = data['value'].tolist()
        
        trend_analysis = self.stats_service.trend_analysis(timestamps, values)
        
        # Generate insight based on trend direction
        business_impact = self._get_business_impact(metric_name, trend_analysis.direction.value)
        
        if trend_analysis.p_value < 0.05:  # Statistically significant trend
            severity = self._determine_severity_from_trend(metric_name, trend_analysis)
            
            narrative = self._generate_trend_narrative(
                metric_name, trend_analysis, business_impact
            )
            
            recommendations = self._generate_trend_recommendations(
                metric_name, trend_analysis
            )
            
            insight = Insight(
                id=f"trend_{organization_id}_{metric_name}_{int(timestamps[-1].timestamp())}",
                type=InsightType.TREND,
                severity=severity,
                title=f"{self._format_metric_name(metric_name)} Shows {trend_analysis.direction.value.title()} Trend",
                description=f"Statistically significant {trend_analysis.direction.value} trend detected",
                narrative=narrative,
                data_points={
                    'slope': trend_analysis.slope,
                    'r_squared': trend_analysis.r_squared,
                    'p_value': trend_analysis.p_value,
                    'trend_strength': trend_analysis.trend_strength,
                    'direction': trend_analysis.direction.value,
                    'confidence_interval': trend_analysis.confidence_interval
                },
                confidence_score=min(trend_analysis.trend_strength * (1 - trend_analysis.p_value), 1.0),
                organization_id=organization_id,
                metric_name=metric_name,
                timestamp=datetime.now(),
                recommendations=recommendations,
                related_metrics=self._get_related_metrics(metric_name),
                metadata={'analysis_type': 'linear_regression', 'business_impact': business_impact}
            )
            
            insights.append(insight)
        
        return insights
    
    def _generate_anomaly_insights(self, metric_name: str, organization_id: str,
                                  data: pd.DataFrame) -> List[Insight]:
        """Generate anomaly-based insights"""
        insights = []
        
        if len(data) < 10:
            return insights
        
        values = data['value'].tolist()
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        
        # Detect anomalies using multiple methods
        methods = ['zscore', 'iqr', 'statistical']
        
        for method in methods:
            try:
                anomaly_result = self.stats_service.anomaly_detection(
                    values, method=method, sensitivity=2.0
                )
                
                if anomaly_result.anomalies:
                    severity = self._determine_anomaly_severity(
                        metric_name, anomaly_result.anomalies
                    )
                    
                    narrative = self._generate_anomaly_narrative(
                        metric_name, anomaly_result, timestamps
                    )
                    
                    recommendations = self._generate_anomaly_recommendations(
                        metric_name, anomaly_result
                    )
                    
                    insight = Insight(
                        id=f"anomaly_{method}_{organization_id}_{metric_name}_{int(time.time())}",
                        type=InsightType.ANOMALY,
                        severity=severity,
                        title=f"Unusual Activity Detected in {self._format_metric_name(metric_name)}",
                        description=f"{len(anomaly_result.anomalies)} anomalies detected using {method} method",
                        narrative=narrative,
                        data_points={
                            'method': method,
                            'anomaly_count': len(anomaly_result.anomalies),
                            'anomaly_rate': anomaly_result.summary['anomaly_rate'],
                            'threshold': anomaly_result.threshold,
                            'avg_anomaly_score': anomaly_result.summary['avg_anomaly_score'],
                            'anomalies': anomaly_result.anomalies[:5]  # Limit to first 5
                        },
                        confidence_score=min(anomaly_result.summary['avg_anomaly_score'] / 10.0, 1.0),
                        organization_id=organization_id,
                        metric_name=metric_name,
                        timestamp=datetime.now(),
                        recommendations=recommendations,
                        related_metrics=self._get_related_metrics(metric_name),
                        metadata={'detection_method': method}
                    )
                    
                    insights.append(insight)
                    break  # Only use the first method that finds anomalies
                    
            except Exception as e:
                logger.error(f"Error detecting anomalies with {method}: {e}")
        
        return insights
    
    def _generate_seasonal_insights(self, metric_name: str, organization_id: str,
                                   data: pd.DataFrame) -> List[Insight]:
        """Generate seasonality-based insights"""
        insights = []
        
        if len(data) < 14:  # Need minimum data for seasonality
            return insights
        
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        values = data['value'].tolist()
        
        seasonality_analysis = self.stats_service.seasonality_analysis(timestamps, values)
        
        if seasonality_analysis.seasonal_strength > 0.3:  # Significant seasonality
            severity = InsightSeverity.MEDIUM
            
            narrative = self._generate_seasonality_narrative(
                metric_name, seasonality_analysis
            )
            
            recommendations = self._generate_seasonality_recommendations(
                metric_name, seasonality_analysis
            )
            
            insight = Insight(
                id=f"seasonal_{organization_id}_{metric_name}_{int(time.time())}",
                type=InsightType.SEASONAL,
                severity=severity,
                title=f"Seasonal Pattern Identified in {self._format_metric_name(metric_name)}",
                description=f"{seasonality_analysis.seasonality_type.value.title()} seasonality detected",
                narrative=narrative,
                data_points={
                    'seasonality_type': seasonality_analysis.seasonality_type.value,
                    'seasonal_strength': seasonality_analysis.seasonal_strength,
                    'period': seasonality_analysis.period,
                    'seasonal_components': seasonality_analysis.seasonal_components[:12]  # Limit display
                },
                confidence_score=seasonality_analysis.seasonal_strength,
                organization_id=organization_id,
                metric_name=metric_name,
                timestamp=datetime.now(),
                recommendations=recommendations,
                related_metrics=self._get_related_metrics(metric_name),
                metadata={'seasonality_type': seasonality_analysis.seasonality_type.value}
            )
            
            insights.append(insight)
        
        return insights
    
    def _generate_prediction_insights(self, metric_name: str, organization_id: str,
                                     data: pd.DataFrame) -> List[Insight]:
        """Generate prediction-based insights"""
        insights = []
        
        # Simple trend-based prediction
        if len(data) < 5:
            return insights
        
        timestamps = pd.to_datetime(data['timestamp']).tolist()
        values = data['value'].tolist()
        
        # Predict next few values based on trend
        trend_analysis = self.stats_service.trend_analysis(timestamps, values)
        
        if abs(trend_analysis.slope) > 0.01:  # Significant trend for prediction
            # Simple linear prediction
            last_time = timestamps[-1]
            future_times = [
                last_time + timedelta(hours=i) for i in range(1, 25)  # Next 24 hours
            ]
            
            future_predictions = []
            for future_time in future_times:
                hours_diff = (future_time - timestamps[0]).total_seconds() / 3600
                predicted_value = trend_analysis.slope * hours_diff + values[0]
                future_predictions.append(predicted_value)
            
            # Determine if prediction is concerning
            current_avg = np.mean(values[-5:])  # Last 5 values average
            predicted_24h = future_predictions[-1]
            
            change_percent = ((predicted_24h - current_avg) / current_avg * 100) if current_avg != 0 else 0
            
            if abs(change_percent) > 10:  # Significant predicted change
                severity = InsightSeverity.HIGH if abs(change_percent) > 25 else InsightSeverity.MEDIUM
                
                narrative = self._generate_prediction_narrative(
                    metric_name, trend_analysis, change_percent, predicted_24h, current_avg
                )
                
                recommendations = self._generate_prediction_recommendations(
                    metric_name, change_percent, trend_analysis.direction.value
                )
                
                insight = Insight(
                    id=f"prediction_{organization_id}_{metric_name}_{int(time.time())}",
                    type=InsightType.PREDICTION,
                    severity=severity,
                    title=f"Forecast Alert for {self._format_metric_name(metric_name)}",
                    description=f"Predicted {abs(change_percent):.1f}% change in next 24 hours",
                    narrative=narrative,
                    data_points={
                        'current_average': current_avg,
                        'predicted_24h': predicted_24h,
                        'change_percent': change_percent,
                        'trend_slope': trend_analysis.slope,
                        'prediction_confidence': trend_analysis.r_squared
                    },
                    confidence_score=trend_analysis.r_squared,
                    organization_id=organization_id,
                    metric_name=metric_name,
                    timestamp=datetime.now(),
                    recommendations=recommendations,
                    related_metrics=self._get_related_metrics(metric_name),
                    metadata={'prediction_horizon': '24h', 'method': 'linear_trend'}
                )
                
                insights.append(insight)
        
        return insights
    
    def _generate_correlation_insights(self, organization_id: str, metrics: List[str],
                                     start_time: datetime, end_time: datetime) -> List[Insight]:
        """Generate insights about correlations between metrics"""
        insights = []
        
        if len(metrics) < 2:
            return insights
        
        # Collect data for all metrics
        metric_data = {}
        for metric_name in metrics:
            data = self.ts_db.query(metric_name, organization_id, start_time, end_time)
            if not data.empty:
                metric_data[metric_name] = data['value'].tolist()
        
        if len(metric_data) < 2:
            return insights
        
        # Calculate correlation matrix
        correlation_matrix = self.stats_service.correlation_analysis(metric_data)
        
        # Find strong correlations
        for metric1 in correlation_matrix:
            for metric2 in correlation_matrix[metric1]:
                if metric1 != metric2:
                    correlation = correlation_matrix[metric1][metric2]
                    
                    if abs(correlation) > 0.7:  # Strong correlation
                        severity = InsightSeverity.MEDIUM
                        
                        narrative = self._generate_correlation_narrative(
                            metric1, metric2, correlation
                        )
                        
                        recommendations = self._generate_correlation_recommendations(
                            metric1, metric2, correlation
                        )
                        
                        insight = Insight(
                            id=f"correlation_{organization_id}_{metric1}_{metric2}_{int(time.time())}",
                            type=InsightType.CORRELATION,
                            severity=severity,
                            title=f"Strong Correlation Between {self._format_metric_name(metric1)} and {self._format_metric_name(metric2)}",
                            description=f"{abs(correlation):.2f} correlation coefficient detected",
                            narrative=narrative,
                            data_points={
                                'correlation_coefficient': correlation,
                                'correlation_strength': 'strong' if abs(correlation) > 0.8 else 'moderate',
                                'relationship_type': 'positive' if correlation > 0 else 'negative'
                            },
                            confidence_score=abs(correlation),
                            organization_id=organization_id,
                            metric_name=metric1,
                            timestamp=datetime.now(),
                            recommendations=recommendations,
                            related_metrics=[metric2],
                            metadata={'correlated_metric': metric2, 'correlation': correlation}
                        )
                        
                        insights.append(insight)
        
        return insights
    
    def _load_insight_templates(self) -> Dict[str, Dict[str, str]]:
        """Load insight narrative templates"""
        return {
            'trend': {
                'increasing': "The {metric} has been showing a consistent upward trend with a slope of {slope:.4f} per hour. This {direction} pattern has an R-squared value of {r_squared:.3f}, indicating {strength} predictability.",
                'decreasing': "The {metric} has been experiencing a downward trend with a slope of {slope:.4f} per hour. This decline shows {strength} statistical significance with an R-squared of {r_squared:.3f}.",
                'volatile': "The {metric} is exhibiting high volatility, making it difficult to establish a clear trend. The data suggests unstable patterns that require immediate attention.",
                'stable': "The {metric} has remained relatively stable over the analyzed period, showing no statistically significant trend."
            },
            'anomaly': {
                'high_impact': "Critical anomalies detected in {metric}. {count} data points deviate significantly from normal patterns, with the most severe anomaly showing a z-score of {max_score:.2f}.",
                'medium_impact': "Notable anomalies identified in {metric}. {count} unusual data points detected using {method} analysis, suggesting potential issues that warrant investigation.",
                'low_impact': "Minor anomalies observed in {metric}. While not immediately concerning, these {count} outliers should be monitored for pattern development."
            },
            'seasonal': {
                'daily': "The {metric} exhibits a clear daily seasonal pattern with {strength:.1%} consistency. Peak activity typically occurs during {peak_period}.",
                'weekly': "Weekly seasonality detected in {metric} with {strength:.1%} regularity. Understanding this pattern can help optimize resource allocation.",
                'monthly': "Monthly seasonal trends identified in {metric}. This {strength:.1%} consistent pattern suggests cyclical business factors at play."
            }
        }
    
    def _load_business_context(self) -> Dict[str, Dict[str, str]]:
        """Load business context for different metrics"""
        return {
            'churn_predictions': {
                'increasing': 'high_risk',
                'decreasing': 'positive',
                'business_area': 'customer_retention',
                'kpi_type': 'leading_indicator'
            },
            'customer_activity': {
                'increasing': 'positive',
                'decreasing': 'concerning',
                'business_area': 'engagement',
                'kpi_type': 'engagement_metric'
            },
            'revenue_at_risk': {
                'increasing': 'high_risk',
                'decreasing': 'positive',
                'business_area': 'revenue',
                'kpi_type': 'financial_metric'
            }
        }
    
    # Template helper methods
    def _format_metric_name(self, metric_name: str) -> str:
        """Format metric name for display"""
        return metric_name.replace('_', ' ').title()
    
    def _get_business_impact(self, metric_name: str, direction: str) -> str:
        """Get business impact assessment"""
        context = self.business_context.get(metric_name, {})
        return context.get(direction, 'neutral')
    
    def _determine_severity_from_trend(self, metric_name: str, trend: TrendAnalysis) -> InsightSeverity:
        """Determine insight severity based on trend analysis"""
        business_impact = self._get_business_impact(metric_name, trend.direction.value)
        
        if business_impact == 'high_risk' and trend.trend_strength > 0.8:
            return InsightSeverity.CRITICAL
        elif business_impact in ['high_risk', 'concerning'] and trend.trend_strength > 0.6:
            return InsightSeverity.HIGH
        elif trend.trend_strength > 0.4:
            return InsightSeverity.MEDIUM
        else:
            return InsightSeverity.LOW
    
    def _generate_trend_narrative(self, metric_name: str, trend: TrendAnalysis, 
                                 business_impact: str) -> str:
        """Generate narrative for trend insights"""
        template = self.insight_templates['trend'].get(trend.direction.value, 
                                                      self.insight_templates['trend']['stable'])
        
        strength_desc = 'strong' if trend.trend_strength > 0.8 else 'moderate' if trend.trend_strength > 0.5 else 'weak'
        
        return template.format(
            metric=self._format_metric_name(metric_name),
            slope=abs(trend.slope),
            r_squared=trend.r_squared,
            direction=trend.direction.value,
            strength=strength_desc
        )
    
    def _generate_trend_recommendations(self, metric_name: str, trend: TrendAnalysis) -> List[str]:
        """Generate recommendations based on trend analysis"""
        recommendations = []
        
        business_impact = self._get_business_impact(metric_name, trend.direction.value)
        
        if business_impact == 'high_risk':
            recommendations.append("Implement immediate intervention strategies to address this concerning trend")
            recommendations.append("Monitor related metrics for cascading effects")
            recommendations.append("Consider adjusting business processes to counteract this trend")
        elif business_impact == 'positive':
            recommendations.append("Analyze factors contributing to this positive trend for replication")
            recommendations.append("Maintain current strategies that support this favorable direction")
        else:
            recommendations.append("Continue monitoring this metric for any significant changes")
            recommendations.append("Establish alert thresholds to catch future trend changes early")
        
        return recommendations
    
    def _generate_anomaly_narrative(self, metric_name: str, result: AnomalyDetectionResult,
                                   timestamps: List[datetime]) -> str:
        """Generate narrative for anomaly insights"""
        anomaly_count = len(result.anomalies)
        method = result.method
        
        most_recent = max(result.anomalies, key=lambda x: x['index'])
        recent_time = timestamps[most_recent['index']].strftime('%Y-%m-%d %H:%M')
        
        return f"Detected {anomaly_count} anomalous data points in {self._format_metric_name(metric_name)} using {method} analysis. The most recent anomaly occurred at {recent_time} with a value of {most_recent['value']:.2f}. These outliers represent {result.summary['anomaly_rate']:.1%} of all data points and may indicate underlying issues requiring investigation."
    
    def _generate_anomaly_recommendations(self, metric_name: str, 
                                        result: AnomalyDetectionResult) -> List[str]:
        """Generate recommendations for anomaly insights"""
        recommendations = [
            "Investigate the root causes of these anomalous data points",
            "Check for external factors that might have influenced these outliers",
            "Verify data quality and collection processes during anomaly periods"
        ]
        
        if result.summary['anomaly_rate'] > 0.1:  # High anomaly rate
            recommendations.append("Consider adjusting data collection or processing methods")
            recommendations.append("Review business processes for potential systemic issues")
        
        return recommendations
    
    def _get_available_metrics(self, organization_id: str) -> List[str]:
        """Get list of available metrics for an organization"""
        # This would typically query the time-series database for available metrics
        # For demo purposes, return common churn-related metrics
        return [
            'churn_predictions',
            'churn_risk_score', 
            'customer_activity',
            'revenue_at_risk',
            'model_accuracy',
            'prediction_confidence'
        ]
    
    def _get_related_metrics(self, metric_name: str) -> List[str]:
        """Get related metrics for a given metric"""
        relations = {
            'churn_predictions': ['churn_risk_score', 'customer_activity'],
            'churn_risk_score': ['churn_predictions', 'revenue_at_risk'],
            'customer_activity': ['churn_predictions', 'engagement_score'],
            'revenue_at_risk': ['churn_risk_score', 'customer_value']
        }
        return relations.get(metric_name, [])
    
    def _score_and_sort_insights(self, insights: List[Insight]) -> List[Insight]:
        """Score and sort insights by importance"""
        # Score insights based on severity and confidence
        severity_weights = {
            InsightSeverity.CRITICAL: 4,
            InsightSeverity.HIGH: 3,
            InsightSeverity.MEDIUM: 2,
            InsightSeverity.LOW: 1
        }
        
        for insight in insights:
            severity_score = severity_weights[insight.severity]
            insight.metadata['composite_score'] = severity_score * insight.confidence_score
        
        # Sort by composite score descending
        return sorted(insights, key=lambda x: x.metadata['composite_score'], reverse=True)
    
    # Additional helper methods for other insight types...
    def _determine_anomaly_severity(self, metric_name: str, anomalies: List[Dict]) -> InsightSeverity:
        """Determine severity of anomaly insight"""
        if len(anomalies) > 5:
            return InsightSeverity.HIGH
        elif len(anomalies) > 2:
            return InsightSeverity.MEDIUM
        else:
            return InsightSeverity.LOW
    
    def _generate_seasonality_narrative(self, metric_name: str, 
                                       seasonality: SeasonalityAnalysis) -> str:
        """Generate narrative for seasonality insights"""
        return f"The {self._format_metric_name(metric_name)} shows {seasonality.seasonal_strength:.1%} {seasonality.seasonality_type.value} seasonality with a period of {seasonality.period} data points. This regular pattern can be leveraged for better forecasting and resource planning."
    
    def _generate_seasonality_recommendations(self, metric_name: str,
                                            seasonality: SeasonalityAnalysis) -> List[str]:
        """Generate recommendations for seasonality insights"""
        return [
            f"Use {seasonality.seasonality_type.value} seasonal patterns for capacity planning",
            "Adjust forecasting models to account for seasonal components",
            "Plan resource allocation based on predictable seasonal variations",
            "Monitor for deviations from established seasonal patterns"
        ]
    
    def _generate_prediction_narrative(self, metric_name: str, trend: TrendAnalysis,
                                     change_percent: float, predicted_value: float,
                                     current_avg: float) -> str:
        """Generate narrative for prediction insights"""
        direction = "increase" if change_percent > 0 else "decrease"
        return f"Based on current trends, {self._format_metric_name(metric_name)} is projected to {direction} by {abs(change_percent):.1f}% over the next 24 hours, from an average of {current_avg:.2f} to approximately {predicted_value:.2f}. This prediction has a confidence level of {trend.r_squared:.1%} based on trend analysis."
    
    def _generate_prediction_recommendations(self, metric_name: str, 
                                           change_percent: float,
                                           direction: str) -> List[str]:
        """Generate recommendations for prediction insights"""
        recommendations = []
        
        if abs(change_percent) > 25:
            recommendations.append("Take immediate action to prepare for this significant predicted change")
            recommendations.append("Alert relevant stakeholders about the forecasted impact")
        
        if direction == "increasing" and "churn" in metric_name.lower():
            recommendations.append("Activate customer retention programs proactively")
            recommendations.append("Review recent changes that might be driving increased churn risk")
        elif direction == "decreasing" and "activity" in metric_name.lower():
            recommendations.append("Investigate potential causes of declining customer activity")
            recommendations.append("Consider engagement campaigns to maintain activity levels")
        
        recommendations.append("Monitor actual values against predictions to validate forecast accuracy")
        
        return recommendations
    
    def _generate_correlation_narrative(self, metric1: str, metric2: str, 
                                       correlation: float) -> str:
        """Generate narrative for correlation insights"""
        relationship = "positive" if correlation > 0 else "negative"
        strength = "strong" if abs(correlation) > 0.8 else "moderate"
        
        return f"A {strength} {relationship} correlation ({correlation:.3f}) exists between {self._format_metric_name(metric1)} and {self._format_metric_name(metric2)}. This relationship suggests that changes in one metric tend to be accompanied by {'similar' if correlation > 0 else 'opposite'} changes in the other."
    
    def _generate_correlation_recommendations(self, metric1: str, metric2: str,
                                            correlation: float) -> List[str]:
        """Generate recommendations for correlation insights"""
        return [
            f"Monitor both {self._format_metric_name(metric1)} and {self._format_metric_name(metric2)} together for comprehensive insights",
            "Consider the relationship between these metrics when making business decisions",
            "Use one metric to predict potential changes in the other",
            "Investigate the underlying business processes that link these metrics"
        ]
    
    def _generate_executive_summary(self, categorized_insights: Dict[str, List[Insight]]) -> str:
        """Generate executive summary from categorized insights"""
        critical_count = len(categorized_insights['critical_alerts'])
        high_count = len(categorized_insights['high_priority'])
        
        if critical_count > 0:
            summary = f"URGENT: {critical_count} critical issue(s) detected requiring immediate attention. "
        else:
            summary = "No critical issues detected. "
        
        if high_count > 0:
            summary += f"{high_count} high-priority insight(s) identified for review. "
        
        trend_insights = categorized_insights['trends']
        if trend_insights:
            summary += f"Key trends: {len(trend_insights)} significant patterns detected in customer metrics. "
        
        return summary
    
    def _generate_key_metrics_summary(self, organization_id: str, hours: int) -> Dict[str, Any]:
        """Generate summary of key metrics"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        key_metrics = {}
        
        # Get stats for important metrics
        important_metrics = ['churn_predictions', 'customer_activity', 'revenue_at_risk']
        
        for metric in important_metrics:
            try:
                stats = self.ts_db.get_metric_stats(metric, organization_id, hours)
                key_metrics[metric] = {
                    'current_value': stats.get('mean', 0),
                    'trend': 'stable',  # Would calculate from trend analysis
                    'change_percent': 0,  # Would calculate from comparison
                    'status': 'normal'  # Would determine from thresholds
                }
            except:
                key_metrics[metric] = {'error': 'Data not available'}
        
        return key_metrics
    
    def _calculate_confidence_distribution(self, insights: List[Insight]) -> Dict[str, int]:
        """Calculate distribution of confidence scores"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for insight in insights:
            if insight.confidence_score >= 0.8:
                distribution['high'] += 1
            elif insight.confidence_score >= 0.5:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution

# Global insight generator instance
insight_generator = NaturalLanguageInsightGenerator()

def get_insight_generator() -> NaturalLanguageInsightGenerator:
    """Get the global insight generator instance"""
    return insight_generator

# Convenience functions
def generate_insights_for_org(organization_id: str, hours: int = 24) -> List[Insight]:
    """Generate insights for an organization"""
    generator = get_insight_generator()
    return generator.generate_insights(organization_id, time_window_hours=hours)

def get_insights_summary(organization_id: str, period: str = "24h") -> Dict[str, Any]:
    """Get comprehensive insights summary"""
    generator = get_insight_generator()
    return generator.generate_summary_report(organization_id, period)