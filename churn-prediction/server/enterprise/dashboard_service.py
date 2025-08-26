# ChurnGuard Dashboard Service
# Epic 3 - Enterprise Features & Multi-Tenancy

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from .organization_service import OrganizationService

logger = logging.getLogger(__name__)

@dataclass
class Dashboard:
    """Dashboard model"""
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    layout: List[Dict[str, Any]]
    widgets: List[Dict[str, Any]]
    is_default: bool = False
    is_public: bool = False
    created_by: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

class DashboardService:
    """Service for managing custom dashboards"""
    
    def __init__(self, db_connection, org_service: OrganizationService):
        self.db = db_connection
        self.org_service = org_service
    
    def create_dashboard(
        self,
        org_id: str,
        name: str,
        layout: List[Dict[str, Any]],
        widgets: List[Dict[str, Any]],
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dashboard:
        """Create a new dashboard"""
        
        dashboard = Dashboard(
            id=f"dash_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{org_id[:8]}",
            organization_id=org_id,
            name=name,
            description=description,
            layout=layout,
            widgets=widgets,
            created_by=created_by,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO dashboards 
                (id, organization_id, name, description, layout, widgets, 
                 is_default, is_public, created_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dashboard.id, dashboard.organization_id, dashboard.name,
                dashboard.description, json.dumps(dashboard.layout),
                json.dumps(dashboard.widgets), dashboard.is_default,
                dashboard.is_public, dashboard.created_by,
                dashboard.created_at, dashboard.updated_at
            ))
            
            self.db.commit()
            
            # Log dashboard creation
            self.org_service._log_audit_event(
                org_id, 'dashboard_created', 'dashboard', dashboard.id,
                user_id=created_by, event_data={'name': name, 'widgets': len(widgets)}
            )
            
            logger.info(f"Created dashboard {name} for organization {org_id}")
            
        return dashboard
    
    def get_dashboard(self, dashboard_id: str, org_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id, organization_id, name, description, layout, widgets,
                       is_default, is_public, created_by, created_at, updated_at
                FROM dashboards 
                WHERE id = %s AND organization_id = %s
            """, (dashboard_id, org_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return Dashboard(
                id=row[0], organization_id=row[1], name=row[2],
                description=row[3], layout=json.loads(row[4]),
                widgets=json.loads(row[5]), is_default=row[6],
                is_public=row[7], created_by=row[8],
                created_at=row[9], updated_at=row[10]
            )
    
    def list_dashboards(self, org_id: str, user_id: Optional[str] = None) -> List[Dashboard]:
        """List dashboards for organization"""
        with self.db.cursor() as cursor:
            if user_id:
                # User can see public dashboards and their own private dashboards
                cursor.execute("""
                    SELECT id, organization_id, name, description, layout, widgets,
                           is_default, is_public, created_by, created_at, updated_at
                    FROM dashboards 
                    WHERE organization_id = %s 
                    AND (is_public = TRUE OR created_by = %s)
                    ORDER BY is_default DESC, created_at DESC
                """, (org_id, user_id))
            else:
                # Admin can see all dashboards
                cursor.execute("""
                    SELECT id, organization_id, name, description, layout, widgets,
                           is_default, is_public, created_by, created_at, updated_at
                    FROM dashboards 
                    WHERE organization_id = %s
                    ORDER BY is_default DESC, created_at DESC
                """, (org_id,))
            
            dashboards = []
            for row in cursor.fetchall():
                dashboard = Dashboard(
                    id=row[0], organization_id=row[1], name=row[2],
                    description=row[3], layout=json.loads(row[4]),
                    widgets=json.loads(row[5]), is_default=row[6],
                    is_public=row[7], created_by=row[8],
                    created_at=row[9], updated_at=row[10]
                )
                dashboards.append(dashboard)
            
            return dashboards
    
    def update_dashboard(
        self,
        dashboard_id: str,
        org_id: str,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """Update dashboard"""
        
        # Build SET clause
        set_clauses = []
        values = []
        
        allowed_fields = {'name', 'description', 'layout', 'widgets', 'is_public'}
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field in ['layout', 'widgets']:
                    set_clauses.append(f"{field} = %s")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
        
        if not set_clauses:
            return True
        
        set_clauses.append("updated_at = %s")
        values.extend([datetime.now(), dashboard_id, org_id])
        
        with self.db.cursor() as cursor:
            cursor.execute(f"""
                UPDATE dashboards 
                SET {', '.join(set_clauses)}
                WHERE id = %s AND organization_id = %s
            """, values)
            
            affected = cursor.rowcount
            if affected > 0:
                self.db.commit()
                
                # Log update
                self.org_service._log_audit_event(
                    org_id, 'dashboard_updated', 'dashboard', dashboard_id,
                    user_id=updated_by, event_data={'updates': list(updates.keys())}
                )
                
                return True
        
        return False
    
    def delete_dashboard(
        self,
        dashboard_id: str,
        org_id: str,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Delete dashboard"""
        
        with self.db.cursor() as cursor:
            # Get dashboard info before deletion for audit log
            cursor.execute("""
                SELECT name FROM dashboards 
                WHERE id = %s AND organization_id = %s AND is_default = FALSE
            """, (dashboard_id, org_id))
            
            row = cursor.fetchone()
            if not row:
                return False  # Dashboard not found or is default
            
            dashboard_name = row[0]
            
            # Delete dashboard
            cursor.execute("""
                DELETE FROM dashboards 
                WHERE id = %s AND organization_id = %s AND is_default = FALSE
            """, (dashboard_id, org_id))
            
            affected = cursor.rowcount
            if affected > 0:
                self.db.commit()
                
                # Log deletion
                self.org_service._log_audit_event(
                    org_id, 'dashboard_deleted', 'dashboard', dashboard_id,
                    user_id=deleted_by, event_data={'name': dashboard_name}
                )
                
                return True
        
        return False
    
    def get_dashboard_analytics_data(
        self,
        org_id: str,
        widget_type: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get data for dashboard widgets"""
        
        config = config or {}
        
        try:
            if widget_type == 'kpi_cards':
                return self._get_kpi_data(org_id, config)
            elif widget_type == 'churn_summary':
                return self._get_churn_summary_data(org_id, config)
            elif widget_type == 'customer_list':
                return self._get_customer_list_data(org_id, config)
            elif widget_type == 'churn_trend':
                return self._get_churn_trend_data(org_id, config)
            elif widget_type == 'risk_distribution':
                return self._get_risk_distribution_data(org_id, config)
            elif widget_type == 'model_performance':
                return self._get_model_performance_data(org_id, config)
            elif widget_type == 'recent_predictions':
                return self._get_recent_predictions_data(org_id, config)
            elif widget_type == 'activity_feed':
                return self._get_activity_feed_data(org_id, config)
            elif widget_type == 'user_analytics':
                return self._get_user_analytics_data(org_id, config)
            else:
                return {'error': f'Unknown widget type: {widget_type}'}
                
        except Exception as e:
            logger.error(f"Error getting dashboard data for {widget_type}: {e}")
            return {'error': 'Failed to load widget data'}
    
    def _get_kpi_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get KPI data"""
        # Mock implementation - would query actual data in production
        return {
            'total_customers': {'value': 1250, 'change': 12, 'trend': 'up'},
            'churn_rate': {'value': 18.5, 'change': -2.3, 'trend': 'down'},
            'high_risk': {'value': 89, 'change': 5, 'trend': 'up'},
            'model_accuracy': {'value': 94.2, 'change': 1.1, 'trend': 'up'},
            'predictions_made': {'value': 542, 'change': 23, 'trend': 'up'},
            'active_users': {'value': 45, 'change': 3, 'trend': 'up'},
            'revenue_at_risk': {'value': 125000, 'change': -8000, 'trend': 'down'},
            'avg_customer_value': {'value': 2850, 'change': 120, 'trend': 'up'}
        }
    
    def _get_churn_summary_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get churn summary data"""
        return {
            'summary': {
                'total_customers': 1250,
                'churned_customers': 231,
                'churn_rate': 18.5,
                'predicted_churn': 89,
                'revenue_at_risk': 125000
            },
            'risk_levels': {
                'low': {'count': 825, 'percentage': 66},
                'medium': {'count': 336, 'percentage': 27},
                'high': {'count': 89, 'percentage': 7}
            },
            'trends': {
                'churn_rate_change': -2.3,
                'high_risk_change': 5,
                'revenue_change': -8000
            },
            'comparison': {
                'industry_avg': 22.1,
                'vs_industry': -3.6
            },
            'recent_activity': {
                'predictions_today': 15,
                'alerts_generated': 3,
                'customers_saved': 7
            }
        }
    
    def _get_customer_list_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get customer list data"""
        with self.db.cursor() as cursor:
            limit = config.get('pageSize', 10)
            
            cursor.execute("""
                SELECT id, external_id, email, first_name, last_name, company,
                       churn_probability, churn_risk_level, created_at, updated_at
                FROM customers 
                WHERE organization_id = %s
                ORDER BY churn_probability DESC
                LIMIT %s
            """, (org_id, limit))
            
            customers = []
            for row in cursor.fetchall():
                customers.append({
                    'id': row[0],
                    'name': f"{row[3] or ''} {row[4] or ''}".strip() or 'Unknown',
                    'email': row[2],
                    'company': row[5],
                    'churn_probability': float(row[6] or 0),
                    'churn_risk_level': row[7] or 'low',
                    'predicted_at': (row[9] or row[8]).isoformat(),
                    'value': 5000,  # Mock value
                    'tenure_months': 18,  # Mock tenure
                    'last_activity': (row[9] or row[8]).isoformat()
                })
            
            cursor.execute("SELECT COUNT(*) FROM customers WHERE organization_id = %s", (org_id,))
            total = cursor.fetchone()[0]
            
            return {
                'customers': customers,
                'total': total,
                'showing': len(customers)
            }
    
    def _get_churn_trend_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get churn trend data"""
        return {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'churnRate': [15.2, 18.1, 16.8, 19.5, 17.3, 18.5],
            'predictions': [20.1, 19.8, 18.9, 18.2, 17.8, 17.5],
            'customerCount': [1200, 1180, 1165, 1142, 1158, 1250]
        }
    
    def _get_risk_distribution_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get risk distribution data"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT churn_risk_level, COUNT(*) 
                FROM customers 
                WHERE organization_id = %s 
                GROUP BY churn_risk_level
            """, (org_id,))
            
            distribution = {'low': 0, 'medium': 0, 'high': 0}
            total = 0
            
            for row in cursor.fetchall():
                risk_level = row[0] or 'low'
                count = row[1]
                if risk_level in distribution:
                    distribution[risk_level] = count
                    total += count
            
            # Calculate percentages and add colors
            result = {}
            colors = {'low': '#10B981', 'medium': '#F59E0B', 'high': '#EF4444'}
            
            for level, count in distribution.items():
                percentage = round((count / total * 100) if total > 0 else 0)
                result[level] = {
                    'count': count,
                    'percentage': percentage,
                    'color': colors[level]
                }
            
            return result
    
    def _get_model_performance_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get model performance data"""
        return {
            'current': {
                'accuracy': 0.942,
                'precision': 0.889,
                'recall': 0.876,
                'f1_score': 0.882
            },
            'trend': {
                'accuracy': 0.011,
                'precision': -0.003,
                'recall': 0.008,
                'f1_score': 0.002
            },
            'model_info': {
                'name': 'XGBoost Ensemble',
                'version': 'v2.1.3',
                'last_trained': '2024-01-10T14:30:00Z',
                'training_samples': 15420
            }
        }
    
    def _get_recent_predictions_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent predictions data"""
        with self.db.cursor() as cursor:
            limit = config.get('limit', 20)
            
            cursor.execute("""
                SELECT ph.id, c.first_name, c.last_name, c.email,
                       ph.prediction_value, ph.model_name, ph.predicted_at
                FROM prediction_history ph
                JOIN customers c ON ph.customer_id = c.id
                WHERE ph.organization_id = %s
                ORDER BY ph.predicted_at DESC
                LIMIT %s
            """, (org_id, limit))
            
            predictions = []
            for row in cursor.fetchall():
                name = f"{row[1] or ''} {row[2] or ''}".strip() or row[3] or 'Unknown'
                probability = float(row[4] or 0)
                
                # Determine risk level
                if probability > 0.7:
                    risk_level = 'high'
                elif probability > 0.3:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                predictions.append({
                    'id': row[0],
                    'customer_name': name,
                    'probability': probability,
                    'risk_level': risk_level,
                    'predicted_at': row[6].isoformat(),
                    'model': row[5] or 'Unknown Model'
                })
            
            return {'predictions': predictions}
    
    def _get_activity_feed_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get activity feed data"""
        with self.db.cursor() as cursor:
            limit = config.get('limit', 50)
            
            cursor.execute("""
                SELECT event_type, user_email, occurred_at, event_data
                FROM audit_logs
                WHERE organization_id = %s
                ORDER BY occurred_at DESC
                LIMIT %s
            """, (org_id, limit))
            
            activities = []
            for row in cursor.fetchall():
                event_type = row[0]
                user = row[1] or 'System'
                timestamp = row[2]
                event_data = row[3] or {}
                
                # Create activity description
                description = self._get_activity_description(event_type, event_data)
                icon = self._get_activity_icon(event_type)
                
                activities.append({
                    'id': f"act_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                    'type': event_type,
                    'description': description,
                    'user': user,
                    'timestamp': timestamp.isoformat(),
                    'icon': icon
                })
            
            return {'activities': activities}
    
    def _get_user_analytics_data(self, org_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get user analytics data"""
        with self.db.cursor() as cursor:
            # Get user role breakdown
            cursor.execute("""
                SELECT role, COUNT(*)
                FROM users
                WHERE organization_id = %s AND is_active = TRUE
                GROUP BY role
            """, (org_id,))
            
            user_breakdown = {}
            for row in cursor.fetchall():
                user_breakdown[row[0]] = row[1]
            
            # Mock other analytics
            return {
                'active_users': {'current': 45, 'change': 3, 'trend': 'up'},
                'predictions_made': {'current': 542, 'change': 23, 'trend': 'up'},
                'dashboards_viewed': {'current': 1250, 'change': -15, 'trend': 'down'},
                'avg_session_duration': {'current': 18, 'change': 2, 'trend': 'up'},
                'user_breakdown': user_breakdown
            }
    
    def _get_activity_description(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Generate activity description"""
        descriptions = {
            'login_success': 'User logged in',
            'prediction_made': 'Prediction generated',
            'user_created': 'New user added',
            'dashboard_created': 'Dashboard created',
            'model_training': 'Model retrained',
            'data_export': 'Data exported'
        }
        
        base_description = descriptions.get(event_type, event_type.replace('_', ' ').title())
        
        # Add context from event_data if available
        if 'customer_name' in event_data:
            base_description += f" for {event_data['customer_name']}"
        elif 'name' in event_data:
            base_description += f": {event_data['name']}"
        
        return base_description
    
    def _get_activity_icon(self, event_type: str) -> str:
        """Get icon for activity type"""
        icons = {
            'login_success': '🔑',
            'prediction_made': '🔮',
            'user_created': '👤',
            'dashboard_created': '📊',
            'model_training': '🤖',
            'data_export': '📤',
            'user_login': '🔑',
            'user_logout': '🚪',
            'organization_updated': '⚙️'
        }
        
        return icons.get(event_type, '📝')

# Create database table if not exists
def create_dashboard_table(db_connection):
    """Create dashboard table"""
    with db_connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dashboards (
                id VARCHAR(255) PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                layout JSONB NOT NULL,
                widgets JSONB NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT FALSE,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dashboards_organization 
            ON dashboards(organization_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dashboards_created_by 
            ON dashboards(created_by)
        """)
        
        db_connection.commit()