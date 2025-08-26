# ChurnGuard Compliance Service
# Epic 3 - Enterprise Features & Multi-Tenancy

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .organization_service import OrganizationService

logger = logging.getLogger(__name__)

class DataSubjectRights(Enum):
    """GDPR Data Subject Rights"""
    ACCESS = "access"  # Right to access personal data
    RECTIFICATION = "rectification"  # Right to rectify inaccurate data
    ERASURE = "erasure"  # Right to erasure ("right to be forgotten")
    PORTABILITY = "portability"  # Right to data portability
    RESTRICTION = "restriction"  # Right to restrict processing
    OBJECTION = "objection"  # Right to object to processing

class RequestStatus(Enum):
    """Data subject request status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class DataSubjectRequest:
    """Data subject request model"""
    id: str
    organization_id: str
    customer_email: str
    request_type: DataSubjectRights
    status: RequestStatus
    description: Optional[str] = None
    requested_at: datetime = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    expiry_date: Optional[datetime] = None
    verification_token: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

@dataclass
class DataRetentionPolicy:
    """Data retention policy model"""
    id: str
    organization_id: str
    data_category: str  # customer_data, prediction_history, audit_logs, etc.
    retention_period_days: int
    auto_delete: bool = True
    legal_basis: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

class ComplianceService:
    """Service for GDPR compliance and data protection"""
    
    def __init__(self, db_connection, org_service: OrganizationService):
        self.db = db_connection
        self.org_service = org_service
    
    # GDPR Data Subject Rights Implementation
    
    def create_data_subject_request(
        self,
        org_id: str,
        customer_email: str,
        request_type: DataSubjectRights,
        description: Optional[str] = None,
        verification_token: Optional[str] = None
    ) -> str:
        """Create a new data subject request"""
        
        request_id = f"dsr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{org_id[:8]}"
        expiry_date = datetime.now() + timedelta(days=30)  # GDPR requires response within 30 days
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO data_subject_requests 
                (id, organization_id, customer_email, request_type, status, 
                 description, requested_at, expiry_date, verification_token)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request_id, org_id, customer_email, request_type.value,
                RequestStatus.PENDING.value, description, datetime.now(),
                expiry_date, verification_token
            ))
            
            self.db.commit()
            
            # Log the request
            self.org_service._log_audit_event(
                org_id, 'data_subject_request_created', 'compliance', request_id,
                event_data={
                    'request_type': request_type.value,
                    'customer_email': customer_email,
                    'expiry_date': expiry_date.isoformat()
                }
            )
            
            logger.info(f"Created data subject request {request_id} for {customer_email}")
            
        return request_id
    
    def process_data_access_request(self, request_id: str, processed_by: str) -> Dict[str, Any]:
        """Process a data access request (GDPR Article 15)"""
        
        with self.db.cursor() as cursor:
            # Get request details
            cursor.execute("""
                SELECT organization_id, customer_email, request_type, status
                FROM data_subject_requests 
                WHERE id = %s
            """, (request_id,))
            
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Request not found'}
            
            org_id, customer_email, request_type, status = row
            
            if request_type != DataSubjectRights.ACCESS.value:
                return {'success': False, 'error': 'Invalid request type'}
            
            if status != RequestStatus.PENDING.value:
                return {'success': False, 'error': 'Request already processed'}
            
            # Update request status
            cursor.execute("""
                UPDATE data_subject_requests 
                SET status = %s, processed_at = %s, processed_by = %s
                WHERE id = %s
            """, (RequestStatus.IN_PROGRESS.value, datetime.now(), processed_by, request_id))
            
            # Gather all personal data for this customer
            personal_data = self._gather_customer_data(org_id, customer_email, cursor)
            
            # Update request with response data
            cursor.execute("""
                UPDATE data_subject_requests 
                SET status = %s, response_data = %s, processed_at = %s
                WHERE id = %s
            """, (
                RequestStatus.COMPLETED.value,
                json.dumps(personal_data),
                datetime.now(),
                request_id
            ))
            
            self.db.commit()
            
            # Log completion
            self.org_service._log_audit_event(
                org_id, 'data_access_request_completed', 'compliance', request_id,
                user_id=processed_by,
                event_data={
                    'customer_email': customer_email,
                    'data_categories': list(personal_data.keys())
                }
            )
            
            logger.info(f"Completed data access request {request_id}")
            
            return {
                'success': True,
                'data': personal_data,
                'export_url': f'/api/compliance/export/{request_id}'
            }
    
    def process_data_erasure_request(self, request_id: str, processed_by: str) -> Dict[str, Any]:
        """Process a data erasure request (GDPR Article 17 - Right to be forgotten)"""
        
        with self.db.cursor() as cursor:
            # Get request details
            cursor.execute("""
                SELECT organization_id, customer_email, request_type, status
                FROM data_subject_requests 
                WHERE id = %s
            """, (request_id,))
            
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Request not found'}
            
            org_id, customer_email, request_type, status = row
            
            if request_type != DataSubjectRights.ERASURE.value:
                return {'success': False, 'error': 'Invalid request type'}
            
            if status != RequestStatus.PENDING.value:
                return {'success': False, 'error': 'Request already processed'}
            
            # Update request status
            cursor.execute("""
                UPDATE data_subject_requests 
                SET status = %s, processed_at = %s, processed_by = %s
                WHERE id = %s
            """, (RequestStatus.IN_PROGRESS.value, datetime.now(), processed_by, request_id))
            
            # Find customer ID
            cursor.execute("""
                SELECT id FROM customers 
                WHERE organization_id = %s AND email = %s
            """, (org_id, customer_email))
            
            customer_row = cursor.fetchone()
            if not customer_row:
                # Update request as completed if no customer found
                cursor.execute("""
                    UPDATE data_subject_requests 
                    SET status = %s, notes = %s, processed_at = %s
                    WHERE id = %s
                """, (
                    RequestStatus.COMPLETED.value,
                    "No customer data found for the specified email address",
                    datetime.now(),
                    request_id
                ))
                self.db.commit()
                return {'success': True, 'message': 'No data found to erase'}
            
            customer_id = customer_row[0]
            
            # Perform data erasure
            erasure_results = self._erase_customer_data(org_id, customer_id, cursor)
            
            # Update request as completed
            cursor.execute("""
                UPDATE data_subject_requests 
                SET status = %s, response_data = %s, processed_at = %s, notes = %s
                WHERE id = %s
            """, (
                RequestStatus.COMPLETED.value,
                json.dumps(erasure_results),
                datetime.now(),
                "Customer data has been successfully erased",
                request_id
            ))
            
            self.db.commit()
            
            # Log completion
            self.org_service._log_audit_event(
                org_id, 'data_erasure_completed', 'compliance', request_id,
                user_id=processed_by,
                event_data={
                    'customer_email': customer_email,
                    'records_erased': erasure_results
                }
            )
            
            logger.info(f"Completed data erasure request {request_id}")
            
            return {'success': True, 'erasure_results': erasure_results}
    
    def get_data_subject_requests(
        self,
        org_id: str,
        status: Optional[RequestStatus] = None,
        limit: int = 100
    ) -> List[DataSubjectRequest]:
        """Get data subject requests for an organization"""
        
        with self.db.cursor() as cursor:
            if status:
                cursor.execute("""
                    SELECT id, organization_id, customer_email, request_type, status,
                           description, requested_at, processed_at, processed_by,
                           expiry_date, notes
                    FROM data_subject_requests 
                    WHERE organization_id = %s AND status = %s
                    ORDER BY requested_at DESC
                    LIMIT %s
                """, (org_id, status.value, limit))
            else:
                cursor.execute("""
                    SELECT id, organization_id, customer_email, request_type, status,
                           description, requested_at, processed_at, processed_by,
                           expiry_date, notes
                    FROM data_subject_requests 
                    WHERE organization_id = %s
                    ORDER BY requested_at DESC
                    LIMIT %s
                """, (org_id, limit))
            
            requests = []
            for row in cursor.fetchall():
                request = DataSubjectRequest(
                    id=row[0],
                    organization_id=row[1],
                    customer_email=row[2],
                    request_type=DataSubjectRights(row[3]),
                    status=RequestStatus(row[4]),
                    description=row[5],
                    requested_at=row[6],
                    processed_at=row[7],
                    processed_by=row[8],
                    expiry_date=row[9],
                    notes=row[10]
                )
                requests.append(request)
            
            return requests
    
    # Data Retention Policies
    
    def create_retention_policy(
        self,
        org_id: str,
        data_category: str,
        retention_period_days: int,
        auto_delete: bool = True,
        legal_basis: Optional[str] = None
    ) -> str:
        """Create a data retention policy"""
        
        policy_id = f"rp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{org_id[:8]}"
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO data_retention_policies 
                (id, organization_id, data_category, retention_period_days, 
                 auto_delete, legal_basis, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                policy_id, org_id, data_category, retention_period_days,
                auto_delete, legal_basis, datetime.now(), datetime.now()
            ))
            
            self.db.commit()
            
            # Log policy creation
            self.org_service._log_audit_event(
                org_id, 'retention_policy_created', 'compliance', policy_id,
                event_data={
                    'data_category': data_category,
                    'retention_days': retention_period_days,
                    'auto_delete': auto_delete
                }
            )
            
            logger.info(f"Created retention policy {policy_id} for {data_category}")
            
        return policy_id
    
    def apply_retention_policies(self, org_id: str) -> Dict[str, int]:
        """Apply data retention policies and delete expired data"""
        
        deletion_results = {}
        
        with self.db.cursor() as cursor:
            # Get all retention policies for the organization
            cursor.execute("""
                SELECT id, data_category, retention_period_days, auto_delete
                FROM data_retention_policies 
                WHERE organization_id = %s AND auto_delete = TRUE
            """, (org_id,))
            
            policies = cursor.fetchall()
            
            for policy_id, data_category, retention_days, auto_delete in policies:
                if not auto_delete:
                    continue
                
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                deleted_count = 0
                
                # Apply retention based on data category
                if data_category == 'customer_data':
                    cursor.execute("""
                        DELETE FROM customers 
                        WHERE organization_id = %s 
                        AND created_at < %s 
                        AND id NOT IN (
                            SELECT DISTINCT customer_id 
                            FROM prediction_history 
                            WHERE created_at >= %s
                        )
                    """, (org_id, cutoff_date, cutoff_date))
                    deleted_count = cursor.rowcount
                    
                elif data_category == 'prediction_history':
                    cursor.execute("""
                        DELETE FROM prediction_history 
                        WHERE organization_id = %s AND created_at < %s
                    """, (org_id, cutoff_date))
                    deleted_count = cursor.rowcount
                    
                elif data_category == 'audit_logs':
                    cursor.execute("""
                        DELETE FROM audit_logs 
                        WHERE organization_id = %s AND occurred_at < %s
                        AND event_type NOT IN ('data_subject_request_created', 'data_erasure_completed')
                    """, (org_id, cutoff_date))
                    deleted_count = cursor.rowcount
                
                deletion_results[data_category] = deleted_count
                
                if deleted_count > 0:
                    # Log retention policy application
                    self.org_service._log_audit_event(
                        org_id, 'retention_policy_applied', 'compliance', policy_id,
                        event_data={
                            'data_category': data_category,
                            'records_deleted': deleted_count,
                            'cutoff_date': cutoff_date.isoformat()
                        }
                    )
            
            self.db.commit()
            logger.info(f"Applied retention policies for organization {org_id}: {deletion_results}")
            
        return deletion_results
    
    # Privacy Impact Assessment
    
    def generate_privacy_impact_report(self, org_id: str) -> Dict[str, Any]:
        """Generate a privacy impact assessment report"""
        
        with self.db.cursor() as cursor:
            report = {
                'organization_id': org_id,
                'generated_at': datetime.now().isoformat(),
                'data_processing_summary': {},
                'data_subject_requests': {},
                'retention_policies': {},
                'compliance_status': {}
            }
            
            # Data processing summary
            cursor.execute("""
                SELECT COUNT(*) FROM customers WHERE organization_id = %s
            """, (org_id,))
            report['data_processing_summary']['total_customers'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM prediction_history WHERE organization_id = %s
            """, (org_id,))
            report['data_processing_summary']['total_predictions'] = cursor.fetchone()[0]
            
            # Data subject requests summary
            cursor.execute("""
                SELECT request_type, status, COUNT(*)
                FROM data_subject_requests 
                WHERE organization_id = %s
                GROUP BY request_type, status
            """, (org_id,))
            
            dsr_summary = {}
            for request_type, status, count in cursor.fetchall():
                if request_type not in dsr_summary:
                    dsr_summary[request_type] = {}
                dsr_summary[request_type][status] = count
            
            report['data_subject_requests'] = dsr_summary
            
            # Retention policies summary
            cursor.execute("""
                SELECT data_category, retention_period_days, auto_delete
                FROM data_retention_policies 
                WHERE organization_id = %s
            """, (org_id,))
            
            retention_summary = []
            for category, retention_days, auto_delete in cursor.fetchall():
                retention_summary.append({
                    'category': category,
                    'retention_days': retention_days,
                    'auto_delete': auto_delete
                })
            
            report['retention_policies'] = retention_summary
            
            # Compliance status checks
            report['compliance_status'] = self._assess_compliance_status(org_id, cursor)
            
            return report
    
    def _gather_customer_data(self, org_id: str, customer_email: str, cursor) -> Dict[str, Any]:
        """Gather all personal data for a customer"""
        
        data = {}
        
        # Customer profile data
        cursor.execute("""
            SELECT id, external_id, email, first_name, last_name, phone, 
                   company, created_at, updated_at
            FROM customers 
            WHERE organization_id = %s AND email = %s
        """, (org_id, customer_email))
        
        customer_row = cursor.fetchone()
        if customer_row:
            customer_id = customer_row[0]
            data['profile'] = {
                'id': customer_row[0],
                'external_id': customer_row[1],
                'email': customer_row[2],
                'first_name': customer_row[3],
                'last_name': customer_row[4],
                'phone': customer_row[5],
                'company': customer_row[6],
                'created_at': customer_row[7].isoformat() if customer_row[7] else None,
                'updated_at': customer_row[8].isoformat() if customer_row[8] else None
            }
            
            # Prediction history
            cursor.execute("""
                SELECT prediction_value, model_name, predicted_at, features_used
                FROM prediction_history 
                WHERE organization_id = %s AND customer_id = %s
                ORDER BY predicted_at DESC
            """, (org_id, customer_id))
            
            predictions = []
            for row in cursor.fetchall():
                predictions.append({
                    'prediction_value': float(row[0]) if row[0] else None,
                    'model_name': row[1],
                    'predicted_at': row[2].isoformat() if row[2] else None,
                    'features_used': row[3]
                })
            
            data['predictions'] = predictions
            
            # Audit trail
            cursor.execute("""
                SELECT event_type, occurred_at, event_data
                FROM audit_logs 
                WHERE organization_id = %s 
                AND (event_data->>'customer_id' = %s OR event_data->>'customer_email' = %s)
                ORDER BY occurred_at DESC
            """, (org_id, customer_id, customer_email))
            
            audit_trail = []
            for row in cursor.fetchall():
                audit_trail.append({
                    'event_type': row[0],
                    'occurred_at': row[1].isoformat() if row[1] else None,
                    'event_data': row[2]
                })
            
            data['audit_trail'] = audit_trail
        
        return data
    
    def _erase_customer_data(self, org_id: str, customer_id: str, cursor) -> Dict[str, int]:
        """Erase all customer data"""
        
        results = {}
        
        # Delete prediction history
        cursor.execute("""
            DELETE FROM prediction_history 
            WHERE organization_id = %s AND customer_id = %s
        """, (org_id, customer_id))
        results['prediction_history'] = cursor.rowcount
        
        # Delete customer profile (keep audit trail for compliance)
        cursor.execute("""
            UPDATE customers 
            SET email = 'erased@privacy.local',
                first_name = '[ERASED]',
                last_name = '[ERASED]',
                phone = NULL,
                external_id = NULL,
                updated_at = %s
            WHERE organization_id = %s AND id = %s
        """, (datetime.now(), org_id, customer_id))
        results['customer_profile'] = cursor.rowcount
        
        return results
    
    def _assess_compliance_status(self, org_id: str, cursor) -> Dict[str, Any]:
        """Assess GDPR compliance status"""
        
        status = {
            'overall_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        score = 100
        
        # Check for overdue data subject requests
        cursor.execute("""
            SELECT COUNT(*) FROM data_subject_requests 
            WHERE organization_id = %s 
            AND status = 'pending' 
            AND expiry_date < %s
        """, (org_id, datetime.now()))
        
        overdue_requests = cursor.fetchone()[0]
        if overdue_requests > 0:
            score -= 20
            status['issues'].append(f"{overdue_requests} overdue data subject requests")
            status['recommendations'].append("Process overdue data subject requests immediately")
        
        # Check for data retention policies
        cursor.execute("""
            SELECT COUNT(*) FROM data_retention_policies 
            WHERE organization_id = %s
        """, (org_id,))
        
        policy_count = cursor.fetchone()[0]
        if policy_count == 0:
            score -= 15
            status['issues'].append("No data retention policies defined")
            status['recommendations'].append("Create data retention policies for different data categories")
        
        # Check for recent privacy impact assessment
        # This would check if a PIA has been conducted recently
        # For now, we'll assume it's needed if score is not perfect
        if score < 100:
            status['recommendations'].append("Conduct regular privacy impact assessments")
        
        status['overall_score'] = max(0, score)
        
        return status

def create_compliance_tables(db_connection):
    """Create compliance-related tables"""
    
    with db_connection.cursor() as cursor:
        # Data subject requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_subject_requests (
                id VARCHAR(255) PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                customer_email VARCHAR(255) NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL,
                description TEXT,
                requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                processed_at TIMESTAMP WITH TIME ZONE,
                processed_by UUID REFERENCES users(id),
                expiry_date TIMESTAMP WITH TIME ZONE,
                verification_token VARCHAR(255),
                response_data JSONB,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Data retention policies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_retention_policies (
                id VARCHAR(255) PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                data_category VARCHAR(100) NOT NULL,
                retention_period_days INTEGER NOT NULL,
                auto_delete BOOLEAN DEFAULT TRUE,
                legal_basis TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dsr_organization_status 
            ON data_subject_requests(organization_id, status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dsr_expiry 
            ON data_subject_requests(expiry_date) WHERE status = 'pending'
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_retention_org 
            ON data_retention_policies(organization_id)
        """)
        
        db_connection.commit()
        logger.info("Created compliance tables")