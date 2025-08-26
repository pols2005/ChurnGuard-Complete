# ChurnGuard Enterprise Models
# Epic 3 - Enterprise Features & Multi-Tenancy

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import json

# ==================== ENUMS ====================

class SubscriptionTier(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class CustomerStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"

class ChurnRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SSOProvider(Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    AZURE = "azure"
    SAML = "saml"

# ==================== CORE MODELS ====================

@dataclass
class Organization:
    """Multi-tenant organization model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    slug: str = ""
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    
    # Subscription
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER
    subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    billing_email: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    
    # Branding
    logo_url: Optional[str] = None
    primary_color: str = "#DAA520"
    secondary_color: str = "#B8860B"
    custom_css: Optional[str] = None
    custom_domain: Optional[str] = None
    
    # Limits & features
    max_users: int = 5
    max_customers: int = 10000
    features: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['subscription_tier'] = self.subscription_tier.value
        data['subscription_status'] = self.subscription_status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Organization':
        """Create from dictionary"""
        # Convert enum fields
        if 'subscription_tier' in data:
            data['subscription_tier'] = SubscriptionTier(data['subscription_tier'])
        if 'subscription_status' in data:
            data['subscription_status'] = SubscriptionStatus(data['subscription_status'])
        
        # Convert datetime fields
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def has_feature(self, feature: str) -> bool:
        """Check if organization has a specific feature"""
        tier_features = {
            SubscriptionTier.STARTER: {
                'basic_analytics', 'standard_support'
            },
            SubscriptionTier.PROFESSIONAL: {
                'basic_analytics', 'advanced_analytics', 'data_export',
                'custom_colors', 'logo_upload', 'priority_support'
            },
            SubscriptionTier.ENTERPRISE: {
                'basic_analytics', 'advanced_analytics', 'data_export',
                'custom_colors', 'logo_upload', 'custom_css', 'white_label',
                'sso', 'api_access', 'dedicated_support', 'custom_domain'
            }
        }
        
        tier_features_set = tier_features.get(self.subscription_tier, set())
        return feature in tier_features_set or feature in self.features

@dataclass
class User:
    """Multi-tenant user model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    # Authentication
    email: str = ""
    password_hash: Optional[str] = None
    email_verified: bool = False
    
    # Profile
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en"
    
    # Authorization
    role: UserRole = UserRole.USER
    permissions: List[str] = field(default_factory=list)
    is_admin: bool = False
    is_active: bool = True
    
    # SSO
    sso_provider: Optional[SSOProvider] = None
    sso_id: Optional[str] = None
    sso_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Session & security
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts))
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        return self.full_name or self.email
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.is_admin:
            return True
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding sensitive data"""
        data = asdict(self)
        # Remove sensitive fields
        data.pop('password_hash', None)
        
        # Convert enums
        data['role'] = self.role.value
        if self.sso_provider:
            data['sso_provider'] = self.sso_provider.value
        
        # Convert datetimes
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_login_at:
            data['last_login_at'] = self.last_login_at.isoformat()
        if self.locked_until:
            data['locked_until'] = self.locked_until.isoformat()
        
        return data

@dataclass
class Customer:
    """Multi-tenant customer model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    # Customer identification
    external_id: Optional[str] = None  # Client's customer ID
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    
    # Churn prediction features
    credit_score: Optional[int] = None
    age: Optional[int] = None
    tenure: Optional[int] = None
    balance: Optional[float] = None
    num_products: Optional[int] = None
    has_credit_card: Optional[bool] = None
    is_active_member: Optional[bool] = None
    estimated_salary: Optional[float] = None
    geography: Optional[str] = None
    gender: Optional[str] = None
    
    # Prediction results
    churn_probability: Optional[float] = None
    churn_risk_level: Optional[ChurnRiskLevel] = None
    last_prediction_at: Optional[datetime] = None
    prediction_model: Optional[str] = None
    
    # Status & metadata
    status: CustomerStatus = CustomerStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get customer's full name"""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts))
    
    @property
    def display_name(self) -> str:
        """Get customer's display name"""
        return self.full_name or self.email or self.external_id or f"Customer {self.id[:8]}"
    
    def get_features_dict(self) -> Dict[str, Any]:
        """Get features dictionary for ML prediction"""
        return {
            'CreditScore': self.credit_score or 0,
            'Age': self.age or 0,
            'Tenure': self.tenure or 0,
            'Balance': self.balance or 0.0,
            'NumOfProducts': self.num_products or 0,
            'HasCrCard': int(self.has_credit_card or False),
            'IsActiveMember': int(self.is_active_member or False),
            'EstimatedSalary': self.estimated_salary or 0.0,
            'Geography_France': 1 if self.geography == 'France' else 0,
            'Geography_Germany': 1 if self.geography == 'Germany' else 0,
            'Geography_Spain': 1 if self.geography == 'Spain' else 0,
            'Gender_Male': 1 if self.gender == 'Male' else 0,
            'Gender_Female': 1 if self.gender == 'Female' else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        
        # Convert enums
        data['status'] = self.status.value
        if self.churn_risk_level:
            data['churn_risk_level'] = self.churn_risk_level.value
        
        # Convert datetimes
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_prediction_at:
            data['last_prediction_at'] = self.last_prediction_at.isoformat()
        
        return data

@dataclass
class Role:
    """RBAC role model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    name: str = ""
    description: str = ""
    permissions: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

@dataclass
class APIKey:
    """API key model for programmatic access"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    name: str = ""
    key_hash: str = ""  # Hashed API key
    key_prefix: str = ""  # First few chars for identification
    
    # Permissions & limits
    permissions: List[str] = field(default_factory=list)
    rate_limit_per_hour: int = 1000
    allowed_ips: List[str] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

@dataclass
class AuditLog:
    """Audit log model for compliance"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    # Event details
    event_type: str = ""  # 'user_login', 'prediction_made', 'data_export', etc.
    resource_type: Optional[str] = None  # 'customer', 'user', 'prediction', etc.
    resource_id: Optional[str] = None
    
    # Actor information
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Event data
    event_data: Dict[str, Any] = field(default_factory=dict)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    occurred_at: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None

@dataclass
class SSOConfiguration:
    """SSO configuration model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    # Provider details
    provider: SSOProvider = SSOProvider.SAML
    provider_name: str = ""
    is_active: bool = True
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # SAML specific
    entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    certificate: Optional[str] = None
    
    # OAuth/OIDC specific
    client_id: Optional[str] = None
    client_secret_encrypted: Optional[str] = None
    discovery_url: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

# ==================== UTILITY FUNCTIONS ====================

def get_subscription_limits(tier: SubscriptionTier) -> Dict[str, Union[int, bool]]:
    """Get subscription limits for a tier"""
    limits = {
        SubscriptionTier.STARTER: {
            'max_users': 5,
            'max_customers': 1000,
            'api_calls_per_month': 10000,
            'data_exports_per_month': 5,
            'custom_colors': False,
            'logo_upload': False,
            'custom_css': False,
            'white_label': False,
            'sso': False,
            'api_access': False,
            'priority_support': False
        },
        SubscriptionTier.PROFESSIONAL: {
            'max_users': 25,
            'max_customers': 10000,
            'api_calls_per_month': 100000,
            'data_exports_per_month': 50,
            'custom_colors': True,
            'logo_upload': True,
            'custom_css': False,
            'white_label': True,
            'sso': False,
            'api_access': True,
            'priority_support': True
        },
        SubscriptionTier.ENTERPRISE: {
            'max_users': float('inf'),
            'max_customers': float('inf'),
            'api_calls_per_month': float('inf'),
            'data_exports_per_month': float('inf'),
            'custom_colors': True,
            'logo_upload': True,
            'custom_css': True,
            'white_label': True,
            'sso': True,
            'api_access': True,
            'priority_support': True,
            'dedicated_support': True,
            'custom_domain': True
        }
    }
    
    return limits.get(tier, limits[SubscriptionTier.STARTER])

def get_default_permissions(role: UserRole) -> List[str]:
    """Get default permissions for a role"""
    permissions = {
        UserRole.ADMIN: [
            'user.create', 'user.read', 'user.update', 'user.delete',
            'customer.create', 'customer.read', 'customer.update', 'customer.delete',
            'prediction.create', 'prediction.read',
            'analytics.read', 'organization.read', 'organization.update',
            'api.manage', 'export.create', 'audit.read'
        ],
        UserRole.MANAGER: [
            'user.read', 'user.update',
            'customer.create', 'customer.read', 'customer.update',
            'prediction.create', 'prediction.read',
            'analytics.read', 'export.create'
        ],
        UserRole.USER: [
            'customer.read', 'customer.update',
            'prediction.create', 'prediction.read',
            'analytics.read'
        ],
        UserRole.VIEWER: [
            'customer.read', 'prediction.read', 'analytics.read'
        ]
    }
    
    return permissions.get(role, permissions[UserRole.USER])