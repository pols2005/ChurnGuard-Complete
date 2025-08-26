# ChurnGuard Experiment Results Analysis & Reporting
# Epic 4 Phase 5 - A/B Testing Framework

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from .experiment_management import get_experiment_manager, Experiment, ExperimentStatus
from .statistical_testing import get_testing_engine, StatisticalTestResult, ExperimentAnalysis
from .time_series_db import get_time_series_db

logger = logging.getLogger(__name__)

class ReportType(Enum):
    SUMMARY = "summary"
    DETAILED = "detailed"  
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    REAL_TIME = "real_time"

class VisualizationType(Enum):
    CONVERSION_FUNNEL = "conversion_funnel"
    TIME_SERIES = "time_series" 
    DISTRIBUTION = "distribution"
    CONFIDENCE_INTERVALS = "confidence_intervals"
    EFFECT_SIZE = "effect_size"
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    SEGMENT_BREAKDOWN = "segment_breakdown"

@dataclass
class ExperimentVisualization:
    """Visualization data for experiment results"""
    viz_id: str
    viz_type: VisualizationType
    title: str
    description: str
    chart_data: Dict[str, Any]
    chart_config: Dict[str, Any]
    base64_image: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentReport:
    """Comprehensive experiment results report"""
    report_id: str
    experiment_id: str
    organization_id: str
    report_type: ReportType
    generated_at: datetime
    generated_by: str
    
    # Executive summary
    executive_summary: Dict[str, Any]
    
    # Key findings
    key_findings: List[str]
    business_impact: Dict[str, Any]
    recommendations: List[str]
    
    # Detailed results
    statistical_analysis: ExperimentAnalysis
    visualizations: List[ExperimentVisualization]
    
    # Appendices
    methodology: Dict[str, Any]
    assumptions: List[str]
    limitations: List[str]
    
    # Export data
    raw_data: Optional[Dict[str, Any]] = None
    export_formats: List[str] = field(default_factory=lambda: ['pdf', 'html', 'json'])
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class ExperimentReportGenerator:
    """
    Advanced experiment results analysis and reporting system
    
    Features:
    - Multiple report types (executive, technical, real-time dashboards)
    - Interactive visualizations with statistical overlays
    - Automated insights generation and business impact analysis
    - Multi-format export (PDF, HTML, JSON, CSV)
    - Real-time monitoring dashboards
    - Segment-based analysis and drill-downs
    - Statistical rigor validation and assumption checking
    - Collaborative commenting and sharing
    """
    
    def __init__(self):
        self.experiment_manager = get_experiment_manager()
        self.testing_engine = get_testing_engine()
        self.ts_db = get_time_series_db()
        
        # Report templates and styling
        self.report_templates = self._load_report_templates()
        self.visualization_config = self._load_visualization_config()
        
        # Generated reports cache
        self.reports_cache: Dict[str, ExperimentReport] = {}
        
    def generate_experiment_report(self, experiment_id: str, report_type: ReportType = ReportType.DETAILED,
                                 requester: str = "system", 
                                 include_visualizations: bool = True,
                                 include_raw_data: bool = False) -> ExperimentReport:
        """
        Generate comprehensive experiment results report
        
        Args:
            experiment_id: Experiment identifier
            report_type: Type of report to generate
            requester: Person requesting the report
            include_visualizations: Whether to generate visualizations
            include_raw_data: Whether to include raw data export
            
        Returns:
            Complete experiment report with analysis and visualizations
        """
        if experiment_id not in self.experiment_manager.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiment_manager.experiments[experiment_id]
        
        # Perform statistical analysis
        statistical_analysis = self.testing_engine.analyze_experiment(experiment_id)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(experiment, statistical_analysis)
        
        # Extract key findings
        key_findings = self._extract_key_findings(statistical_analysis)
        
        # Calculate business impact
        business_impact = self._calculate_business_impact(experiment, statistical_analysis)
        
        # Generate recommendations
        recommendations = self._generate_business_recommendations(
            experiment, statistical_analysis, report_type
        )
        
        # Create visualizations
        visualizations = []
        if include_visualizations:
            visualizations = self._generate_visualizations(experiment, statistical_analysis)
        
        # Compile methodology and assumptions
        methodology = self._compile_methodology(experiment, statistical_analysis)
        assumptions = self._list_statistical_assumptions(statistical_analysis)
        limitations = self._identify_limitations(experiment, statistical_analysis)
        
        # Include raw data if requested
        raw_data = None
        if include_raw_data:
            raw_data = self._extract_raw_data(experiment_id)
        
        report_id = f"rpt_{experiment_id}_{int(datetime.now().timestamp())}"
        
        report = ExperimentReport(
            report_id=report_id,
            experiment_id=experiment_id,
            organization_id=experiment.organization_id,
            report_type=report_type,
            generated_at=datetime.now(),
            generated_by=requester,
            executive_summary=executive_summary,
            key_findings=key_findings,
            business_impact=business_impact,
            recommendations=recommendations,
            statistical_analysis=statistical_analysis,
            visualizations=visualizations,
            methodology=methodology,
            assumptions=assumptions,
            limitations=limitations,
            raw_data=raw_data,
            metadata={
                'experiment_name': experiment.name,
                'experiment_status': experiment.status.value,
                'runtime_days': statistical_analysis.runtime_days,
                'total_participants': statistical_analysis.total_participants,
                'report_version': '1.0'
            }
        )
        
        # Cache the report
        self.reports_cache[report_id] = report
        
        logger.info(f"Generated {report_type.value} report {report_id} for experiment {experiment_id}")
        return report
    
    def create_real_time_dashboard(self, experiment_id: str) -> Dict[str, Any]:
        """
        Create real-time monitoring dashboard data
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Real-time dashboard configuration and data
        """
        if experiment_id not in self.experiment_manager.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiment_manager.experiments[experiment_id]
        
        # Get current experiment status
        experiment_status = self.experiment_manager.get_experiment_status(experiment_id)
        
        # Generate quick statistical snapshot (lightweight analysis)
        quick_analysis = self._generate_quick_analysis(experiment_id)
        
        # Create time-series data for real-time charts
        time_series_data = self._get_time_series_data(experiment_id)
        
        # Calculate key performance indicators
        kpis = self._calculate_real_time_kpis(experiment, quick_analysis)
        
        # Check for any alerts or important changes
        alerts = self._check_real_time_alerts(experiment, quick_analysis)
        
        dashboard = {
            'experiment_id': experiment_id,
            'experiment_name': experiment.name,
            'last_updated': datetime.now().isoformat(),
            'status': experiment_status,
            'kpis': kpis,
            'time_series_data': time_series_data,
            'quick_analysis': quick_analysis,
            'alerts': alerts,
            'refresh_interval_seconds': 300,  # 5 minutes
            'dashboard_config': {
                'auto_refresh': True,
                'show_confidence_intervals': True,
                'show_statistical_significance': True,
                'alert_thresholds': self._get_alert_thresholds(experiment)
            }
        }
        
        return dashboard
    
    def export_report(self, report_id: str, format: str = 'html') -> Dict[str, Any]:
        """
        Export report in specified format
        
        Args:
            report_id: Report identifier
            format: Export format ('html', 'pdf', 'json', 'csv')
            
        Returns:
            Exported report data
        """
        if report_id not in self.reports_cache:
            raise ValueError(f"Report {report_id} not found")
        
        report = self.reports_cache[report_id]
        
        if format.lower() == 'json':
            return self._export_json(report)
        elif format.lower() == 'html':
            return self._export_html(report)
        elif format.lower() == 'pdf':
            return self._export_pdf(report)
        elif format.lower() == 'csv':
            return self._export_csv(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _generate_executive_summary(self, experiment: Experiment, 
                                   analysis: ExperimentAnalysis) -> Dict[str, Any]:
        """Generate executive summary of experiment results"""
        primary_results = analysis.primary_metric_results
        
        # Determine overall outcome
        significant_results = [r for r in primary_results if r.is_significant]
        
        if significant_results:
            winning_variant = max(significant_results, key=lambda r: r.effect_size)
            outcome = "significant_improvement"
            winner = winning_variant.treatment_variant
            improvement = winning_variant.relative_improvement
        elif analysis.overall_conclusion.value == "inconclusive":
            outcome = "inconclusive"
            winner = None
            improvement = 0.0
        else:
            outcome = "no_significant_difference"
            winner = None
            improvement = 0.0
        
        # Calculate confidence level
        confidence_level = "high" if analysis.confidence_score > 0.8 else "medium" if analysis.confidence_score > 0.6 else "low"
        
        return {
            'outcome': outcome,
            'winning_variant': winner,
            'improvement_percentage': improvement * 100 if improvement else 0,
            'confidence_level': confidence_level,
            'confidence_score': analysis.confidence_score,
            'experiment_duration_days': analysis.runtime_days,
            'total_participants': analysis.total_participants,
            'primary_metric_count': len(primary_results),
            'significant_results_count': len(significant_results),
            'recommendation': analysis.recommended_action,
            'statistical_power': np.mean([r.power for r in primary_results]) if primary_results else 0.0
        }
    
    def _extract_key_findings(self, analysis: ExperimentAnalysis) -> List[str]:
        """Extract key findings from statistical analysis"""
        findings = []
        
        # Primary metric findings
        for result in analysis.primary_metric_results:
            if result.is_significant:
                direction = "increased" if result.relative_improvement > 0 else "decreased"
                findings.append(
                    f"{result.metric_name} {direction} by {abs(result.relative_improvement):.1%} "
                    f"(p={result.p_value:.3f}, effect size={result.effect_size:.3f})"
                )
            else:
                findings.append(
                    f"No significant difference found in {result.metric_name} "
                    f"(p={result.p_value:.3f})"
                )
        
        # Sample size and power findings
        if analysis.power_analysis:
            avg_power = analysis.power_analysis.get('average_power', 0)
            if avg_power < 0.8:
                findings.append(
                    f"Statistical power was below recommended level ({avg_power:.1%} vs 80%)"
                )
        
        # Guardrail violations
        if analysis.guardrail_violations:
            findings.append(
                f"{len(analysis.guardrail_violations)} guardrail metric violations detected"
            )
        
        # Segment insights
        if analysis.segment_results:
            significant_segments = sum(
                1 for segment_results in analysis.segment_results.values()
                for result in segment_results if result.is_significant
            )
            if significant_segments > 0:
                findings.append(
                    f"Significant effects found in {significant_segments} customer segments"
                )
        
        return findings[:10]  # Limit to top 10 findings
    
    def _generate_visualizations(self, experiment: Experiment, 
                               analysis: ExperimentAnalysis) -> List[ExperimentVisualization]:
        """Generate visualizations for experiment results"""
        visualizations = []
        
        # Conversion rate comparison
        if analysis.primary_metric_results:
            conv_viz = self._create_conversion_comparison_chart(analysis.primary_metric_results)
            visualizations.append(conv_viz)
        
        # Time series of key metrics
        time_series_viz = self._create_time_series_chart(experiment.experiment_id)
        if time_series_viz:
            visualizations.append(time_series_viz)
        
        # Confidence intervals visualization
        if analysis.primary_metric_results:
            ci_viz = self._create_confidence_intervals_chart(analysis.primary_metric_results)
            visualizations.append(ci_viz)
        
        # Effect size visualization
        if analysis.primary_metric_results:
            effect_viz = self._create_effect_size_chart(analysis.primary_metric_results)
            visualizations.append(effect_viz)
        
        # Segment breakdown (if available)
        if analysis.segment_results:
            segment_viz = self._create_segment_breakdown_chart(analysis.segment_results)
            visualizations.append(segment_viz)
        
        return visualizations
    
    def _create_conversion_comparison_chart(self, results: List[StatisticalTestResult]) -> ExperimentVisualization:
        """Create conversion rate comparison chart"""
        
        chart_data = {
            'metrics': [],
            'control_rates': [],
            'treatment_rates': [],
            'significance': [],
            'confidence_intervals': []
        }
        
        for result in results:
            chart_data['metrics'].append(result.metric_name)
            chart_data['control_rates'].append(result.control_mean)
            chart_data['treatment_rates'].append(result.treatment_mean)
            chart_data['significance'].append(result.is_significant)
            chart_data['confidence_intervals'].append(result.confidence_interval)
        
        # Generate matplotlib visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(chart_data['metrics']))
        width = 0.35
        
        control_bars = ax.bar(x - width/2, chart_data['control_rates'], width, 
                            label='Control', alpha=0.8, color='#2E86C1')
        treatment_bars = ax.bar(x + width/2, chart_data['treatment_rates'], width,
                              label='Treatment', alpha=0.8, color='#28B463')
        
        # Highlight significant results
        for i, significant in enumerate(chart_data['significance']):
            if significant:
                control_bars[i].set_edgecolor('red')
                control_bars[i].set_linewidth(2)
                treatment_bars[i].set_edgecolor('red')  
                treatment_bars[i].set_linewidth(2)
        
        ax.set_xlabel('Metrics')
        ax.set_ylabel('Conversion Rate')
        ax.set_title('Conversion Rate Comparison by Variant')
        ax.set_xticks(x)
        ax.set_xticklabels(chart_data['metrics'])
        ax.legend()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return ExperimentVisualization(
            viz_id=f"conv_comparison_{int(datetime.now().timestamp())}",
            viz_type=VisualizationType.CONVERSION_FUNNEL,
            title="Conversion Rate Comparison",
            description="Comparison of conversion rates between control and treatment variants",
            chart_data=chart_data,
            chart_config={
                'chart_type': 'bar',
                'show_significance': True,
                'show_confidence_intervals': True
            },
            base64_image=base64_image
        )
    
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load report templates and formatting"""
        return {
            'executive': {
                'sections': ['executive_summary', 'key_findings', 'recommendations'],
                'visualizations': ['conversion_comparison', 'effect_size'],
                'style': 'business'
            },
            'technical': {
                'sections': ['methodology', 'statistical_analysis', 'assumptions', 'limitations'],
                'visualizations': ['confidence_intervals', 'statistical_significance', 'time_series'],
                'style': 'scientific'  
            },
            'detailed': {
                'sections': ['executive_summary', 'statistical_analysis', 'visualizations', 'methodology'],
                'visualizations': 'all',
                'style': 'comprehensive'
            }
        }
    
    def _load_visualization_config(self) -> Dict[str, Any]:
        """Load visualization styling and configuration"""
        return {
            'color_palette': ['#2E86C1', '#28B463', '#F39C12', '#E74C3C', '#8E44AD'],
            'significance_color': '#E74C3C',
            'confidence_level': 0.95,
            'chart_dimensions': {
                'width': 10,
                'height': 6,
                'dpi': 300
            },
            'fonts': {
                'title': 14,
                'axis': 12,
                'label': 10
            }
        }

# Additional helper methods would continue here...

# Global experiment report generator
report_generator = ExperimentReportGenerator()

def get_report_generator() -> ExperimentReportGenerator:
    """Get the global experiment report generator"""
    return report_generator

# Convenience functions
def generate_experiment_report(experiment_id: str, report_type: ReportType = ReportType.DETAILED) -> ExperimentReport:
    """Generate comprehensive experiment report"""
    generator = get_report_generator()
    return generator.generate_experiment_report(experiment_id, report_type)

def create_real_time_dashboard(experiment_id: str) -> Dict[str, Any]:
    """Create real-time experiment monitoring dashboard"""
    generator = get_report_generator()
    return generator.create_real_time_dashboard(experiment_id)

def export_experiment_report(report_id: str, format: str = 'html') -> Dict[str, Any]:
    """Export experiment report in specified format"""
    generator = get_report_generator()
    return generator.export_report(report_id, format)