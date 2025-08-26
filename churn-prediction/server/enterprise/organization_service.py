# ChurnGuard Organization Management Service
# Epic 3 - Enterprise Features & Multi-Tenancy

import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from .models import (
    Organization, User, Customer, Role, APIKey, AuditLog,
    SubscriptionTier, SubscriptionStatus, UserRole, 
    get_subscription_limits, get_default_permissions
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for managing multi-tenant organizations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_org_id = None
    
    @contextmanager
    def organization_context(self, org_id: str):
        """Context manager for setting organization scope"""
        previous_org = self.current_org_id
        try:
            self.current_org_id = org_id
            # Set PostgreSQL RLS context
            with self.db.cursor() as cursor:
                cursor.execute("SELECT set_organization_context(%s)", (org_id,))
            yield
        finally:
            self.current_org_id = previous_org
    
    # ==================== ORGANIZATION MANAGEMENT ====================
    
    def create_organization(
        self,
        name: str,
        admin_email: str,
        admin_password: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.STARTER,
        **kwargs
    ) -> Tuple[Organization, User]:
        """Create a new organization with admin user"""
        
        # Generate unique slug
        base_slug = name.lower().replace(' ', '-').replace('_', '-')
        slug = base_slug
        counter = 1
        
        while self.get_organization_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create organization
        org = Organization(
            name=name,
            slug=slug,
            subdomain=slug,
            subscription_tier=subscription_tier,
            **kwargs
        )
        
        with self.db.cursor() as cursor:
            # Insert organization
            cursor.execute("""
                INSERT INTO organizations 
                (id, name, slug, subdomain, subscription_tier, subscription_status,
                 primary_color, secondary_color, max_users, max_customers, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                org.id, org.name, org.slug, org.subdomain,
                org.subscription_tier.value, org.subscription_status.value,
                org.primary_color, org.secondary_color,
                org.max_users, org.max_customers, org.created_at
            ))
            
            org_id = cursor.fetchone()[0]
            
            # Create default roles
            cursor.execute("SELECT create_default_roles(%s)", (org_id,))
            
            # Create admin user
            password_hash = self._hash_password(admin_password)
            admin_user = User(
                organization_id=org_id,
                email=admin_email,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                is_admin=True,
                permissions=get_default_permissions(UserRole.ADMIN),
                email_verified=True
            )
            
            cursor.execute("""
                INSERT INTO users 
                (id, organization_id, email, password_hash, role, is_admin, 
                 permissions, email_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                admin_user.id, admin_user.organization_id, admin_user.email,
                admin_user.password_hash, admin_user.role.value, admin_user.is_admin,
                json.dumps(admin_user.permissions), admin_user.email_verified,
                admin_user.created_at
            ))
            
            self.db.commit()
            
            # Log organization creation
            self._log_audit_event(
                org_id, 'organization_created', 'organization', org_id,
                user_id=admin_user.id, user_email=admin_user.email,
                event_data={'organization_name': name, 'admin_email': admin_email}
            )
            
            logger.info(f"Created organization {name} ({org.slug}) with admin {admin_email}")
            
        return org, admin_user
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, slug, subdomain, domain, subscription_tier, 
                       subscription_status, billing_email, logo_url, primary_color, 
                       secondary_color, custom_css, custom_domain, max_users, 
                       max_customers, features, settings, created_at, updated_at,
                       created_by, is_active
                FROM organizations WHERE id = %s AND is_active = TRUE
            """, (org_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return Organization(
                id=row[0], name=row[1], slug=row[2], subdomain=row[3],
                domain=row[4], subscription_tier=SubscriptionTier(row[5]),
                subscription_status=SubscriptionStatus(row[6]),
                billing_email=row[7], logo_url=row[8], primary_color=row[9],
                secondary_color=row[10], custom_css=row[11], custom_domain=row[12],
                max_users=row[13], max_customers=row[14], features=row[15] or {},
                settings=row[16] or {}, created_at=row[17], updated_at=row[18],
                created_by=row[19], is_active=row[20]
            )
    
    def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM organizations WHERE slug = %s AND is_active = TRUE
            """, (slug,))
            
            row = cursor.fetchone()
            if row:
                return self.get_organization(row[0])
        
        return None
    
    def get_organization_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by custom domain"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM organizations 
                WHERE (domain = %s OR subdomain = %s) AND is_active = TRUE
            """, (domain, domain))
            
            row = cursor.fetchone()
            if row:
                return self.get_organization(row[0])
        
        return None
    
    def update_organization(
        self, 
        org_id: str, 
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """Update organization"""
        if not updates:
            return True
        
        # Build SET clause
        set_clauses = []
        values = []
        
        allowed_fields = {
            'name', 'logo_url', 'primary_color', 'secondary_color',
            'custom_css', 'custom_domain', 'billing_email', 'settings'
        }
        
        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = %s")
                values.append(value)
        
        if not set_clauses:
            return True
        
        set_clauses.append("updated_at = %s")
        values.extend([datetime.now(), org_id])
        
        with self.db.cursor() as cursor:
            cursor.execute(f"""
                UPDATE organizations 
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """, values)
            
            affected = cursor.rowcount
            if affected > 0:
                self.db.commit()
                
                # Log update
                self._log_audit_event(
                    org_id, 'organization_updated', 'organization', org_id,
                    user_id=updated_by, new_values=updates
                )
                
                return True
        
        return False
    
    # ==================== USER MANAGEMENT ====================
    
    def create_user(
        self,
        org_id: str,
        email: str,
        password: Optional[str] = None,
        role: UserRole = UserRole.USER,
        **user_data
    ) -> User:
        """Create a new user in organization"""
        
        # Check user limit
        org = self.get_organization(org_id)
        if not org:
            raise ValueError("Organization not found")
        
        current_users = self.get_user_count(org_id)
        if current_users >= org.max_users:
            raise ValueError(f"User limit exceeded ({org.max_users} users)")
        
        # Check if email already exists in organization
        existing_user = self.get_user_by_email(org_id, email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create user
        user = User(
            organization_id=org_id,
            email=email,
            password_hash=self._hash_password(password) if password else None,
            role=role,
            permissions=get_default_permissions(role),
            **user_data
        )
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users 
                (id, organization_id, email, password_hash, first_name, last_name,
                 role, permissions, is_admin, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user.id, user.organization_id, user.email, user.password_hash,
                user.first_name, user.last_name, user.role.value,
                json.dumps(user.permissions), user.is_admin, user.is_active,
                user.created_at
            ))
            
            self.db.commit()
            
            # Log user creation
            self._log_audit_event(
                org_id, 'user_created', 'user', user.id,
                event_data={'email': email, 'role': role.value}
            )
            
            logger.info(f"Created user {email} in organization {org_id}")
            
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id, organization_id, email, password_hash, first_name, 
                       last_name, avatar_url, phone, timezone, locale, role, 
                       permissions, is_admin, is_active, sso_provider, sso_id,
                       last_login_at, created_at, updated_at
                FROM users WHERE id = %s AND is_active = TRUE
            """, (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return User(
                id=row[0], organization_id=row[1], email=row[2],
                password_hash=row[3], first_name=row[4], last_name=row[5],
                avatar_url=row[6], phone=row[7], timezone=row[8], locale=row[9],
                role=UserRole(row[10]), permissions=row[11] or [], is_admin=row[12],
                is_active=row[13], sso_provider=row[14], sso_id=row[15],
                last_login_at=row[16], created_at=row[17], updated_at=row[18]
            )
    
    def get_user_by_email(self, org_id: str, email: str) -> Optional[User]:
        """Get user by email within organization"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM users 
                WHERE organization_id = %s AND email = %s AND is_active = TRUE
            """, (org_id, email))
            
            row = cursor.fetchone()
            if row:
                return self.get_user(row[0])
        
        return None
    
    def get_organization_users(
        self, 
        org_id: str, 
        limit: int = 100, 
        offset: int = 0,
        role: Optional[UserRole] = None
    ) -> List[User]:
        """Get users in organization"""
        with self.organization_context(org_id):
            with self.db.cursor() as cursor:
                where_clause = "WHERE organization_id = %s AND is_active = TRUE"
                params = [org_id]
                
                if role:
                    where_clause += " AND role = %s"
                    params.append(role.value)
                
                cursor.execute(f"""
                    SELECT id FROM users {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                
                user_ids = [row[0] for row in cursor.fetchall()]
                return [self.get_user(uid) for uid in user_ids if self.get_user(uid)]
    
    def get_user_count(self, org_id: str) -> int:
        """Get user count in organization"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE organization_id = %s AND is_active = TRUE
            """, (org_id,))
            
            return cursor.fetchone()[0]
    
    # ==================== CUSTOMER MANAGEMENT ====================
    
    def create_customer(self, org_id: str, customer_data: Dict[str, Any]) -> Customer:
        """Create customer in organization"""
        customer = Customer(organization_id=org_id, **customer_data)
        
        with self.organization_context(org_id):
            with self.db.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO customers 
                    (id, organization_id, external_id, email, first_name, last_name,
                     company, credit_score, age, tenure, balance, num_products,
                     has_credit_card, is_active_member, estimated_salary,
                     geography, gender, status, tags, custom_fields, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    customer.id, customer.organization_id, customer.external_id,
                    customer.email, customer.first_name, customer.last_name,
                    customer.company, customer.credit_score, customer.age,
                    customer.tenure, customer.balance, customer.num_products,
                    customer.has_credit_card, customer.is_active_member,
                    customer.estimated_salary, customer.geography, customer.gender,
                    customer.status.value, json.dumps(customer.tags),
                    json.dumps(customer.custom_fields), customer.created_at
                ))
                
                self.db.commit()
                
        return customer
    
    def get_organization_customers(
        self,
        org_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Customer]:
        """Get customers in organization with optional filters"""
        with self.organization_context(org_id):
            with self.db.cursor() as cursor:
                where_clauses = ["organization_id = %s"]
                params = [org_id]
                
                # Apply filters
                if filters:
                    if 'churn_risk_level' in filters:
                        where_clauses.append("churn_risk_level = %s")
                        params.append(filters['churn_risk_level'])
                    
                    if 'status' in filters:
                        where_clauses.append("status = %s")
                        params.append(filters['status'])
                
                cursor.execute(f"""
                    SELECT id, organization_id, external_id, email, first_name, 
                           last_name, company, churn_probability, churn_risk_level,
                           status, created_at, updated_at
                    FROM customers 
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                
                customers = []
                for row in cursor.fetchall():
                    customer = Customer(
                        id=row[0], organization_id=row[1], external_id=row[2],
                        email=row[3], first_name=row[4], last_name=row[5],
                        company=row[6], churn_probability=row[7],
                        churn_risk_level=row[8], status=row[9],
                        created_at=row[10], updated_at=row[11]
                    )
                    customers.append(customer)
                
                return customers
    
    # ==================== API KEY MANAGEMENT ====================
    
    def create_api_key(
        self,
        org_id: str,
        name: str,
        permissions: List[str],
        created_by: str,
        expires_in_days: Optional[int] = None
    ) -> Tuple[str, APIKey]:
        """Create API key for organization"""
        
        # Generate API key
        raw_key = f"cg_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10] + "..."
        
        api_key = APIKey(
            organization_id=org_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions,
            created_by=created_by,
            expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None
        )
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO api_keys 
                (id, organization_id, name, key_hash, key_prefix, permissions,
                 rate_limit_per_hour, is_active, expires_at, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                api_key.id, api_key.organization_id, api_key.name,
                api_key.key_hash, api_key.key_prefix,
                json.dumps(api_key.permissions), api_key.rate_limit_per_hour,
                api_key.is_active, api_key.expires_at, api_key.created_at,
                api_key.created_by
            ))
            
            self.db.commit()
            
            # Log API key creation
            self._log_audit_event(
                org_id, 'api_key_created', 'api_key', api_key.id,
                user_id=created_by,
                event_data={'name': name, 'permissions': permissions}
            )
            
        return raw_key, api_key
    
    # ==================== UTILITY METHODS ====================
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _log_audit_event(
        self,
        org_id: str,
        event_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """Log audit event"""
        audit_log = AuditLog(
            organization_id=org_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            event_data=event_data or {},
            old_values=old_values or {},
            new_values=new_values or {},
            session_id=session_id
        )
        
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO audit_logs 
                    (id, organization_id, event_type, resource_type, resource_id,
                     user_id, user_email, ip_address, user_agent, event_data,
                     old_values, new_values, occurred_at, session_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    audit_log.id, audit_log.organization_id, audit_log.event_type,
                    audit_log.resource_type, audit_log.resource_id,
                    audit_log.user_id, audit_log.user_email, audit_log.ip_address,
                    audit_log.user_agent, json.dumps(audit_log.event_data),
                    json.dumps(audit_log.old_values), json.dumps(audit_log.new_values),
                    audit_log.occurred_at, audit_log.session_id
                ))
                
                self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

import json