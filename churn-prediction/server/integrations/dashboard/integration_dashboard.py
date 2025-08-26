# ChurnGuard Integration Management Dashboard
# Epic 5 - Enterprise Integration & Data Connectors

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from collections import defaultdict

from aiohttp import web, web_request
from aiohttp_cors import setup as cors_setup, ResourceOptions

from ..core.integration_engine import (
    IntegrationEngine, IntegrationConfiguration, IntegrationStatus,
    IntegrationType, DataSyncMode, get_integration_engine
)
from ..api.webhook_ingestion import get_webhook_engine, WebhookIngestionEngine
from ..streaming.data_pipelines import get_streaming_manager, StreamingDataPipelineManager

logger = logging.getLogger(__name__)

@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure"""
    # Integration metrics
    total_integrations: int = 0
    active_integrations: int = 0
    failed_integrations: int = 0
    
    # Sync metrics
    total_syncs_today: int = 0
    successful_syncs_today: int = 0
    failed_syncs_today: int = 0
    avg_sync_duration_minutes: float = 0.0
    
    # Data metrics
    total_records_synced_today: int = 0
    total_records_synced_week: int = 0
    total_records_synced_month: int = 0
    
    # Webhook metrics
    total_webhooks_received_today: int = 0
    webhook_success_rate: float = 1.0
    avg_webhook_processing_time_ms: float = 0.0
    
    # Streaming metrics
    active_streams: int = 0
    total_stream_messages_today: int = 0
    avg_stream_processing_time_ms: float = 0.0
    
    # Performance metrics
    overall_health_score: float = 1.0
    system_load: float = 0.0
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class IntegrationSummary:
    """Integration summary for dashboard"""
    integration_id: str
    name: str
    provider: str
    type: str
    status: str
    
    # Sync information
    last_sync_at: Optional[str] = None
    next_sync_at: Optional[str] = None
    sync_frequency_hours: float = 0.0
    
    # Performance metrics
    total_records_synced: int = 0
    success_rate: float = 1.0
    avg_sync_duration_minutes: float = 0.0
    
    # Health indicators
    health_score: float = 1.0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Activity
    last_activity_at: Optional[str] = None
    activity_trend: str = "stable"  # increasing, stable, decreasing
    
    # Connection info
    connection_status: str = "connected"
    connection_test_at: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class IntegrationDashboard:
    """
    Comprehensive integration management dashboard
    
    Features:
    - Real-time integration monitoring and status
    - Performance metrics and analytics
    - Integration health scoring and alerts
    - Visual data flow mapping
    - Historical trend analysis
    - Error tracking and diagnostics
    - Configuration management interface
    - Sync scheduling and management
    - Webhook activity monitoring
    - Streaming pipeline oversight
    - Resource utilization tracking
    - Automated alerting and notifications
    """
    
    def __init__(self):
        # Core engines
        self.integration_engine = get_integration_engine()
        self.webhook_engine = get_webhook_engine()
        self.streaming_manager = get_streaming_manager()
        
        # Dashboard state
        self.metrics = DashboardMetrics()
        self.integration_summaries: Dict[str, IntegrationSummary] = {}
        
        # Metrics history for trending
        self.metrics_history: List[DashboardMetrics] = []
        self.max_history_length = 1440  # 24 hours of minute-by-minute data
        
        # Alert system
        self.alerts: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            'health_score_warning': 0.8,
            'health_score_critical': 0.6,
            'error_rate_warning': 0.05,
            'error_rate_critical': 0.1,
            'sync_failure_threshold': 3
        }
        
        # Web application
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        
        # Background tasks
        self.metrics_update_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up dashboard HTTP routes"""
        # Dashboard pages
        self.app.router.add_get('/', self._dashboard_home)
        self.app.router.add_get('/dashboard', self._dashboard_home)
        self.app.router.add_get('/integrations', self._integrations_page)
        self.app.router.add_get('/metrics', self._metrics_page)
        self.app.router.add_get('/alerts', self._alerts_page)
        
        # API endpoints
        self.app.router.add_get('/api/dashboard/metrics', self._get_dashboard_metrics)
        self.app.router.add_get('/api/dashboard/integrations', self._get_integration_summaries)
        self.app.router.add_get('/api/dashboard/integration/{integration_id}', self._get_integration_details)
        self.app.router.add_get('/api/dashboard/alerts', self._get_alerts)
        self.app.router.add_get('/api/dashboard/health', self._get_health_status)
        
        # Integration management
        self.app.router.add_post('/api/integrations', self._create_integration)
        self.app.router.add_get('/api/integrations/{integration_id}', self._get_integration)
        self.app.router.add_put('/api/integrations/{integration_id}', self._update_integration)
        self.app.router.add_delete('/api/integrations/{integration_id}', self._delete_integration)
        
        # Sync management
        self.app.router.add_post('/api/integrations/{integration_id}/sync', self._start_sync)
        self.app.router.add_delete('/api/integrations/{integration_id}/sync', self._stop_sync)
        self.app.router.add_get('/api/integrations/{integration_id}/sync/status', self._get_sync_status)
        self.app.router.add_get('/api/integrations/{integration_id}/sync/history', self._get_sync_history)
        
        # System management
        self.app.router.add_post('/api/system/test-connections', self._test_all_connections)
        self.app.router.add_get('/api/system/stats', self._get_system_stats)
        
        # Static files (would serve dashboard UI files)
        self.app.router.add_static('/', path='static/', name='static')
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8090):
        """Start dashboard HTTP server"""
        try:
            # Set up CORS
            cors = cors_setup(self.app, defaults={
                "*": ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            # Add CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            site = web.TCPSite(self.runner, host, port)
            await site.start()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info(f"Integration dashboard started on {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to start dashboard server: {e}")
            raise
    
    async def stop_server(self):
        """Stop dashboard HTTP server"""
        # Stop background tasks
        if self.metrics_update_task:
            self.metrics_update_task.cancel()
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Stop server
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        self.metrics_update_task = asyncio.create_task(self._update_metrics_loop())
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _update_metrics_loop(self):
        """Background task to update metrics"""
        while True:
            try:
                await self._update_dashboard_metrics()
                await self._update_integration_summaries()
                await self._check_alerts()
                
                await asyncio.sleep(60)  # Update every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating dashboard metrics: {e}")
                await asyncio.sleep(10)
    
    async def _health_check_loop(self):
        """Background task for health checking"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(30)
    
    async def _update_dashboard_metrics(self):
        """Update main dashboard metrics"""
        try:
            # Get integration engine metrics
            engine_metrics = self.integration_engine.metrics
            
            # Count integrations by status
            active_count = 0
            failed_count = 0
            for config in self.integration_engine.integrations.values():
                if config.status == IntegrationStatus.ACTIVE:
                    active_count += 1
                elif config.status in [IntegrationStatus.ERROR, IntegrationStatus.AUTHENTICATION_FAILED]:
                    failed_count += 1
            
            # Update metrics
            self.metrics.total_integrations = len(self.integration_engine.integrations)
            self.metrics.active_integrations = active_count
            self.metrics.failed_integrations = failed_count
            
            # Sync metrics from today
            today = datetime.now().date()
            today_syncs = []
            successful_syncs = 0
            failed_syncs = 0
            total_duration = 0
            
            for integration_id, sync_history in self.integration_engine.sync_history.items():
                for sync_result in sync_history:
                    if sync_result.sync_started_at.date() == today:
                        today_syncs.append(sync_result)
                        if sync_result.success:
                            successful_syncs += 1
                        else:
                            failed_syncs += 1
                        total_duration += sync_result.sync_duration_seconds
            
            self.metrics.total_syncs_today = len(today_syncs)
            self.metrics.successful_syncs_today = successful_syncs
            self.metrics.failed_syncs_today = failed_syncs
            self.metrics.avg_sync_duration_minutes = (total_duration / 60) / max(len(today_syncs), 1)
            
            # Records synced
            self.metrics.total_records_synced_today = engine_metrics.get('records_synced_today', 0)
            
            # Get webhook metrics
            if hasattr(self.webhook_engine, 'webhook_events'):
                webhook_events_today = [
                    event for event in self.webhook_engine.webhook_events.values()
                    if event.received_at.date() == today
                ]
                self.metrics.total_webhooks_received_today = len(webhook_events_today)
                
                if webhook_events_today:
                    successful_webhooks = len([e for e in webhook_events_today if e.processed])
                    self.metrics.webhook_success_rate = successful_webhooks / len(webhook_events_today)
            
            # Get streaming metrics
            streaming_metrics = await self.streaming_manager.get_global_metrics()
            self.metrics.active_streams = streaming_metrics.get('active_streams', 0)
            self.metrics.avg_stream_processing_time_ms = streaming_metrics.get('avg_processing_time_ms', 0.0)
            
            # Calculate overall health score
            self.metrics.overall_health_score = self._calculate_health_score()
            self.metrics.last_updated = datetime.now()
            
            # Store in history
            self.metrics_history.append(self.metrics)
            if len(self.metrics_history) > self.max_history_length:
                self.metrics_history.pop(0)
            
        except Exception as e:
            logger.error(f"Error updating dashboard metrics: {e}")
    
    async def _update_integration_summaries(self):
        """Update integration summaries"""
        try:
            for integration_id, config in self.integration_engine.integrations.items():
                # Get sync history
                sync_history = self.integration_engine.sync_history.get(integration_id, [])
                last_sync = sync_history[-1] if sync_history else None
                
                # Calculate success rate
                if sync_history:
                    successful_syncs = len([s for s in sync_history if s.success])
                    success_rate = successful_syncs / len(sync_history)
                else:
                    success_rate = 1.0
                
                # Calculate average sync duration
                if sync_history:
                    total_duration = sum(s.sync_duration_seconds for s in sync_history)
                    avg_duration = (total_duration / len(sync_history)) / 60  # minutes
                else:
                    avg_duration = 0.0
                
                # Determine health score
                health_score = self._calculate_integration_health_score(config, sync_history)
                
                # Identify issues and warnings
                issues = []
                warnings = []
                
                if config.status == IntegrationStatus.ERROR:
                    issues.append(f"Integration error: {config.last_error}")
                elif config.status == IntegrationStatus.AUTHENTICATION_FAILED:
                    issues.append("Authentication failed")
                elif config.status == IntegrationStatus.RATE_LIMITED:
                    warnings.append("Rate limited")
                
                if success_rate < 0.9:
                    warnings.append(f"Low success rate: {success_rate:.1%}")
                
                if last_sync and not last_sync.success:
                    issues.append(f"Last sync failed: {last_sync.error_message}")
                
                # Calculate sync frequency
                sync_frequency_hours = config.sync_config.sync_frequency / 3600
                
                # Create summary
                summary = IntegrationSummary(
                    integration_id=integration_id,
                    name=config.integration_name,
                    provider=config.provider_name,
                    type=config.integration_type.value,
                    status=config.status.value,
                    last_sync_at=last_sync.sync_started_at.isoformat() if last_sync else None,
                    sync_frequency_hours=sync_frequency_hours,
                    total_records_synced=config.total_records_synced,
                    success_rate=success_rate,
                    avg_sync_duration_minutes=avg_duration,
                    health_score=health_score,
                    issues=issues,
                    warnings=warnings,
                    last_activity_at=config.last_sync_at.isoformat() if config.last_sync_at else None,
                    connection_status="connected" if config.status == IntegrationStatus.ACTIVE else "disconnected"
                )
                
                self.integration_summaries[integration_id] = summary
                
        except Exception as e:
            logger.error(f"Error updating integration summaries: {e}")
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score"""
        try:
            scores = []
            
            # Integration health (40% weight)
            if self.metrics.total_integrations > 0:
                integration_health = self.metrics.active_integrations / self.metrics.total_integrations
                scores.append((integration_health, 0.4))
            
            # Sync success rate (30% weight)
            if self.metrics.total_syncs_today > 0:
                sync_health = self.metrics.successful_syncs_today / self.metrics.total_syncs_today
                scores.append((sync_health, 0.3))
            
            # Webhook success rate (20% weight)
            webhook_health = self.metrics.webhook_success_rate
            scores.append((webhook_health, 0.2))
            
            # System load (10% weight)
            load_health = max(0, 1.0 - (self.metrics.system_load / 100))
            scores.append((load_health, 0.1))
            
            if not scores:
                return 1.0
            
            # Calculate weighted average
            total_weight = sum(weight for _, weight in scores)
            weighted_sum = sum(score * weight for score, weight in scores)
            
            return weighted_sum / total_weight if total_weight > 0 else 1.0
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.5  # Default to medium health on error
    
    def _calculate_integration_health_score(self, config: IntegrationConfiguration, 
                                          sync_history: List) -> float:
        """Calculate health score for individual integration"""
        try:
            score = 1.0
            
            # Status penalties
            if config.status == IntegrationStatus.ERROR:
                score -= 0.4
            elif config.status == IntegrationStatus.AUTHENTICATION_FAILED:
                score -= 0.5
            elif config.status == IntegrationStatus.RATE_LIMITED:
                score -= 0.2
            elif config.status == IntegrationStatus.PAUSED:
                score -= 0.3
            
            # Sync success rate impact
            if sync_history:
                recent_syncs = sync_history[-10:]  # Last 10 syncs
                failures = len([s for s in recent_syncs if not s.success])
                if failures > 0:
                    score -= (failures / len(recent_syncs)) * 0.3
            
            # Time since last successful sync
            if config.last_sync_at:
                hours_since_sync = (datetime.now() - config.last_sync_at).total_seconds() / 3600
                expected_frequency_hours = config.sync_config.sync_frequency / 3600
                
                if hours_since_sync > expected_frequency_hours * 2:
                    score -= 0.2
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating integration health score: {e}")
            return 0.5
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        try:
            current_time = datetime.now()
            
            # Health score alerts
            if self.metrics.overall_health_score < self.alert_thresholds['health_score_critical']:
                self._add_alert(
                    'critical',
                    'System Health Critical',
                    f'Overall health score is {self.metrics.overall_health_score:.2f}',
                    current_time
                )
            elif self.metrics.overall_health_score < self.alert_thresholds['health_score_warning']:
                self._add_alert(
                    'warning',
                    'System Health Low',
                    f'Overall health score is {self.metrics.overall_health_score:.2f}',
                    current_time
                )
            
            # Individual integration alerts
            for integration_id, summary in self.integration_summaries.items():
                if summary.issues:
                    self._add_alert(
                        'error',
                        f'Integration Issues: {summary.name}',
                        f'Issues found: {", ".join(summary.issues)}',
                        current_time,
                        integration_id
                    )
                
                if summary.health_score < 0.5:
                    self._add_alert(
                        'critical',
                        f'Integration Health Critical: {summary.name}',
                        f'Health score is {summary.health_score:.2f}',
                        current_time,
                        integration_id
                    )
            
            # Clean up old alerts (keep last 100)
            self.alerts = self.alerts[-100:]
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _add_alert(self, severity: str, title: str, message: str, 
                  timestamp: datetime, integration_id: str = None):
        """Add alert to the alert list"""
        alert = {
            'id': len(self.alerts) + 1,
            'severity': severity,
            'title': title,
            'message': message,
            'timestamp': timestamp.isoformat(),
            'integration_id': integration_id,
            'acknowledged': False
        }
        
        # Check for duplicates in recent alerts
        recent_alerts = [a for a in self.alerts 
                        if datetime.fromisoformat(a['timestamp']) > timestamp - timedelta(minutes=30)]
        
        duplicate = any(
            a['title'] == title and a['integration_id'] == integration_id
            for a in recent_alerts
        )
        
        if not duplicate:
            self.alerts.append(alert)
            logger.warning(f"Alert: [{severity}] {title} - {message}")
    
    async def _perform_health_checks(self):
        """Perform health checks on integrations"""
        try:
            for integration_id, config in self.integration_engine.integrations.items():
                if config.status == IntegrationStatus.ACTIVE:
                    # Test connection for active integrations
                    connector = self.integration_engine.connectors.get(integration_id)
                    if connector:
                        try:
                            is_healthy = await connector.test_connection()
                            if not is_healthy:
                                config.status = IntegrationStatus.ERROR
                                config.last_error = "Connection test failed"
                                logger.warning(f"Health check failed for integration {config.integration_name}")
                        except Exception as e:
                            config.status = IntegrationStatus.ERROR
                            config.last_error = f"Health check error: {str(e)}"
                            logger.error(f"Health check error for {config.integration_name}: {e}")
            
        except Exception as e:
            logger.error(f"Error in health checks: {e}")
    
    # HTTP Route Handlers
    
    async def _dashboard_home(self, request: web_request.Request) -> web.Response:
        """Dashboard home page"""
        # This would serve the main dashboard HTML
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ChurnGuard Integration Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
                .metric-label { color: #666; margin-top: 5px; }
                .status-active { color: #28a745; }
                .status-error { color: #dc3545; }
                .status-warning { color: #ffc107; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ChurnGuard Integration Dashboard</h1>
                    <p>Real-time monitoring and management of data integrations</p>
                </div>
                
                <div class="metrics" id="metrics">
                    <div class="metric-card">
                        <div class="metric-value" id="total-integrations">Loading...</div>
                        <div class="metric-label">Total Integrations</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value status-active" id="active-integrations">Loading...</div>
                        <div class="metric-label">Active Integrations</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="total-syncs">Loading...</div>
                        <div class="metric-label">Syncs Today</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="health-score">Loading...</div>
                        <div class="metric-label">Health Score</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3>Recent Integrations</h3>
                        <div id="integrations-list">Loading...</div>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3>Recent Alerts</h3>
                        <div id="alerts-list">Loading...</div>
                    </div>
                </div>
            </div>
            
            <script>
                async function loadDashboard() {
                    try {
                        const metrics = await fetch('/api/dashboard/metrics').then(r => r.json());
                        const integrations = await fetch('/api/dashboard/integrations').then(r => r.json());
                        const alerts = await fetch('/api/dashboard/alerts').then(r => r.json());
                        
                        document.getElementById('total-integrations').textContent = metrics.total_integrations;
                        document.getElementById('active-integrations').textContent = metrics.active_integrations;
                        document.getElementById('total-syncs').textContent = metrics.total_syncs_today;
                        document.getElementById('health-score').textContent = (metrics.overall_health_score * 100).toFixed(1) + '%';
                        
                        const integrationsHtml = integrations.slice(0, 5).map(i => 
                            `<div style="padding: 10px; border-left: 3px solid ${i.status === 'active' ? '#28a745' : '#dc3545'}; margin-bottom: 10px;">
                                <strong>${i.name}</strong> (${i.provider})<br>
                                <small>Status: ${i.status}, Health: ${(i.health_score * 100).toFixed(1)}%</small>
                            </div>`
                        ).join('');
                        document.getElementById('integrations-list').innerHTML = integrationsHtml;
                        
                        const alertsHtml = alerts.slice(0, 5).map(a => 
                            `<div style="padding: 10px; border-left: 3px solid ${a.severity === 'critical' ? '#dc3545' : a.severity === 'warning' ? '#ffc107' : '#007bff'}; margin-bottom: 10px;">
                                <strong>${a.title}</strong><br>
                                <small>${a.message}</small>
                            </div>`
                        ).join('');
                        document.getElementById('alerts-list').innerHTML = alertsHtml || '<div>No recent alerts</div>';
                        
                    } catch (error) {
                        console.error('Error loading dashboard:', error);
                    }
                }
                
                loadDashboard();
                setInterval(loadDashboard, 30000); // Refresh every 30 seconds
            </script>
        </body>
        </html>
        """
        
        return web.Response(text=dashboard_html, content_type='text/html')
    
    async def _get_dashboard_metrics(self, request: web_request.Request) -> web.Response:
        """Get dashboard metrics API"""
        return web.json_response(asdict(self.metrics))
    
    async def _get_integration_summaries(self, request: web_request.Request) -> web.Response:
        """Get integration summaries API"""
        summaries = [asdict(summary) for summary in self.integration_summaries.values()]
        return web.json_response(summaries)
    
    async def _get_integration_details(self, request: web_request.Request) -> web.Response:
        """Get detailed integration information"""
        integration_id = request.match_info['integration_id']
        
        # Get basic integration info
        config = self.integration_engine.integrations.get(integration_id)
        if not config:
            return web.json_response({'error': 'Integration not found'}, status=404)
        
        # Get sync history
        sync_history = self.integration_engine.sync_history.get(integration_id, [])
        recent_syncs = [
            {
                'sync_started_at': sync.sync_started_at.isoformat(),
                'success': sync.success,
                'records_processed': sync.records_processed,
                'sync_duration_seconds': sync.sync_duration_seconds,
                'error_message': sync.error_message
            }
            for sync in sync_history[-20:]  # Last 20 syncs
        ]
        
        # Get summary
        summary = self.integration_summaries.get(integration_id)
        
        details = {
            'integration_id': integration_id,
            'config': {
                'name': config.integration_name,
                'provider': config.provider_name,
                'type': config.integration_type.value,
                'status': config.status.value,
                'sync_frequency_seconds': config.sync_config.sync_frequency,
                'batch_size': config.sync_config.batch_size,
                'created_at': config.created_at.isoformat() if config.created_at else None
            },
            'summary': asdict(summary) if summary else None,
            'recent_syncs': recent_syncs,
            'total_records_synced': config.total_records_synced,
            'last_sync_at': config.last_sync_at.isoformat() if config.last_sync_at else None,
            'last_error': config.last_error
        }
        
        return web.json_response(details)
    
    async def _get_alerts(self, request: web_request.Request) -> web.Response:
        """Get current alerts"""
        return web.json_response(self.alerts)
    
    async def _get_health_status(self, request: web_request.Request) -> web.Response:
        """Get system health status"""
        health = {
            'status': 'healthy' if self.metrics.overall_health_score > 0.8 else 'degraded' if self.metrics.overall_health_score > 0.6 else 'unhealthy',
            'health_score': self.metrics.overall_health_score,
            'total_integrations': self.metrics.total_integrations,
            'active_integrations': self.metrics.active_integrations,
            'failed_integrations': self.metrics.failed_integrations,
            'critical_alerts': len([a for a in self.alerts if a['severity'] == 'critical' and not a['acknowledged']]),
            'last_updated': self.metrics.last_updated.isoformat()
        }
        
        return web.json_response(health)
    
    async def _start_sync(self, request: web_request.Request) -> web.Response:
        """Start sync for integration"""
        integration_id = request.match_info['integration_id']
        
        try:
            sync_id = await self.integration_engine.start_sync(integration_id)
            return web.json_response({'sync_id': sync_id, 'status': 'started'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _get_sync_status(self, request: web_request.Request) -> web.Response:
        """Get sync status for integration"""
        integration_id = request.match_info['integration_id']
        
        try:
            status = await self.integration_engine.get_sync_status(integration_id)
            return web.json_response(status)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _test_all_connections(self, request: web_request.Request) -> web.Response:
        """Test connections for all integrations"""
        results = {}
        
        for integration_id, connector in self.integration_engine.connectors.items():
            try:
                is_connected = await connector.test_connection()
                results[integration_id] = {
                    'connected': is_connected,
                    'tested_at': datetime.now().isoformat()
                }
            except Exception as e:
                results[integration_id] = {
                    'connected': False,
                    'error': str(e),
                    'tested_at': datetime.now().isoformat()
                }
        
        return web.json_response(results)
    
    # Additional route handlers would continue here...
    
    async def _integrations_page(self, request: web_request.Request) -> web.Response:
        """Integrations management page"""
        return web.Response(text="<h1>Integrations Management</h1><p>Integration management interface would go here</p>", content_type='text/html')
    
    async def _metrics_page(self, request: web_request.Request) -> web.Response:
        """Metrics and analytics page"""
        return web.Response(text="<h1>Metrics & Analytics</h1><p>Detailed metrics and charts would go here</p>", content_type='text/html')
    
    async def _alerts_page(self, request: web_request.Request) -> web.Response:
        """Alerts management page"""
        return web.Response(text="<h1>Alerts</h1><p>Alert management interface would go here</p>", content_type='text/html')

# Global dashboard instance
integration_dashboard = IntegrationDashboard()

def get_integration_dashboard() -> IntegrationDashboard:
    """Get the global integration dashboard"""
    return integration_dashboard

# Convenience functions
async def start_integration_dashboard(host: str = "0.0.0.0", port: int = 8090):
    """Start the integration dashboard server"""
    dashboard = get_integration_dashboard()
    await dashboard.start_server(host, port)

async def stop_integration_dashboard():
    """Stop the integration dashboard server"""
    dashboard = get_integration_dashboard()
    await dashboard.stop_server()