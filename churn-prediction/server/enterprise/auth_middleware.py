# ChurnGuard Authentication Middleware
# Epic 3 - Enterprise Features & Multi-Tenancy

import functools
import logging
from typing import Optional, List, Callable, Any
from flask import request, jsonify, g
from datetime import datetime

from .authentication_service import AuthenticationService
from .organization_service import OrganizationService

logger = logging.getLogger(__name__)

class AuthenticationMiddleware:
    """Flask middleware for handling authentication and authorization"""
    
    def __init__(self, auth_service: AuthenticationService, org_service: OrganizationService):
        self.auth_service = auth_service
        self.org_service = org_service
    
    def extract_token(self) -> Optional[str]:
        """Extract JWT token from request headers"""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Also check for token in cookies for web clients
        return request.cookies.get('auth_token')
    
    def get_client_info(self) -> tuple:
        """Get client IP and user agent"""
        # Handle proxy headers
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        user_agent = request.headers.get('User-Agent', '')
        
        return ip_address, user_agent
    
    def authenticate_request(self) -> tuple:
        """Authenticate current request and return user/org data"""
        token = self.extract_token()
        if not token:
            return None, None, "Missing authentication token"
        
        valid, payload, error = self.auth_service.verify_token(token)
        if not valid:
            return None, None, error
        
        # Get fresh user and organization data
        user = self.org_service.get_user(payload['user_id'])
        org = self.org_service.get_organization(payload['organization_id'])
        
        if not user or not user.is_active:
            return None, None, "User account is inactive"
        
        if not org or not org.is_active:
            return None, None, "Organization is inactive"
        
        # Set organization context for RLS
        with self.org_service.organization_context(org.id):
            # Store user and org in Flask's g object for request duration
            g.current_user = user
            g.current_organization = org
            g.user_permissions = user.permissions
        
        return user, org, None

def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for endpoints"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        
        middleware = current_app.auth_middleware
        user, org, error = middleware.authenticate_request()
        
        if error:
            return jsonify({'error': error, 'code': 'AUTHENTICATION_REQUIRED'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def require_permission(*required_permissions: str):
    """Decorator to require specific permissions"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            user = g.current_user
            
            # Check if user has any of the required permissions
            has_permission = False
            if user.is_admin:
                has_permission = True
            else:
                for permission in required_permissions:
                    if user.has_permission(permission):
                        has_permission = True
                        break
            
            if not has_permission:
                logger.warning(f"Permission denied for user {user.email}: required {required_permissions}")
                return jsonify({
                    'error': f"Insufficient permissions. Required: {', '.join(required_permissions)}",
                    'code': 'PERMISSION_DENIED'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_role(*required_roles: str):
    """Decorator to require specific roles"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            user = g.current_user
            
            if user.role.value not in required_roles and not user.is_admin:
                logger.warning(f"Role access denied for user {user.email}: required {required_roles}")
                return jsonify({
                    'error': f"Insufficient role. Required: {', '.join(required_roles)}",
                    'code': 'ROLE_ACCESS_DENIED'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_admin(f: Callable) -> Callable:
    """Decorator to require admin privileges"""
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        user = g.current_user
        
        if not user.is_admin:
            logger.warning(f"Admin access denied for user {user.email}")
            return jsonify({
                'error': "Admin privileges required",
                'code': 'ADMIN_ACCESS_REQUIRED'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated

def require_subscription_tier(*required_tiers: str):
    """Decorator to require specific subscription tiers"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            org = g.current_organization
            
            if org.subscription_tier.value not in required_tiers:
                return jsonify({
                    'error': f"Feature requires subscription tier: {', '.join(required_tiers)}",
                    'code': 'SUBSCRIPTION_TIER_REQUIRED',
                    'current_tier': org.subscription_tier.value,
                    'required_tiers': required_tiers
                }), 402  # Payment Required
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_feature(feature_name: str):
    """Decorator to require specific organization feature"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            org = g.current_organization
            
            if not org.has_feature(feature_name):
                return jsonify({
                    'error': f"Feature '{feature_name}' not available for your subscription",
                    'code': 'FEATURE_NOT_AVAILABLE',
                    'feature': feature_name,
                    'current_tier': org.subscription_tier.value
                }), 402  # Payment Required
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def optional_auth(f: Callable) -> Callable:
    """Decorator for optional authentication (public endpoints that can benefit from auth)"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        
        middleware = current_app.auth_middleware
        user, org, error = middleware.authenticate_request()
        
        # Don't fail if authentication fails, just set user/org to None
        if error:
            g.current_user = None
            g.current_organization = None
            g.user_permissions = []
        
        return f(*args, **kwargs)
    
    return decorated

def get_organization_from_request() -> Optional[str]:
    """Extract organization identifier from request (subdomain, domain, or slug)"""
    # Try subdomain first
    host = request.headers.get('Host', '').lower()
    
    # Check for custom domain
    if not host.endswith('.churnguard.com') and not host.startswith('localhost'):
        return host  # Custom domain
    
    # Check for subdomain
    if '.' in host:
        subdomain = host.split('.')[0]
        if subdomain not in ['www', 'api', 'app']:
            return subdomain
    
    # Check for organization slug in path or headers
    org_header = request.headers.get('X-Organization')
    if org_header:
        return org_header
    
    return None

def rate_limit(max_requests: int = 100, per_minutes: int = 60):
    """Rate limiting decorator (simplified implementation)"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            # In production, implement proper rate limiting with Redis
            # This is a simplified version
            
            # Get rate limit key (user ID or IP)
            if hasattr(g, 'current_user') and g.current_user:
                rate_limit_key = f"rate_limit:user:{g.current_user.id}"
            else:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                rate_limit_key = f"rate_limit:ip:{ip_address}"
            
            # For demo purposes, we'll skip actual rate limiting implementation
            # In production, use Redis with INCR and EXPIRE commands
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

class APIKeyAuth:
    """API Key authentication for programmatic access"""
    
    def __init__(self, org_service: OrganizationService):
        self.org_service = org_service
    
    def authenticate_api_key(self, api_key: str) -> tuple:
        """Authenticate API key and return organization/permissions"""
        if not api_key or not api_key.startswith('cg_'):
            return None, None, "Invalid API key format"
        
        # Hash the API key
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with self.org_service.db.cursor() as cursor:
            cursor.execute("""
                SELECT ak.id, ak.organization_id, ak.permissions, ak.rate_limit_per_hour,
                       ak.is_active, ak.expires_at, ak.usage_count,
                       o.name, o.subscription_tier, o.is_active as org_active
                FROM api_keys ak
                JOIN organizations o ON ak.organization_id = o.id
                WHERE ak.key_hash = %s
            """, (key_hash,))
            
            row = cursor.fetchone()
            if not row:
                return None, None, "Invalid API key"
            
            # Check if API key is active and not expired
            if not row[4]:  # is_active
                return None, None, "API key is disabled"
            
            if row[5] and row[5] < datetime.now():  # expires_at
                return None, None, "API key has expired"
            
            if not row[9]:  # org_active
                return None, None, "Organization is inactive"
            
            # Update usage count
            cursor.execute("""
                UPDATE api_keys 
                SET usage_count = usage_count + 1, last_used_at = %s
                WHERE id = %s
            """, (datetime.now(), row[0]))
            
            self.org_service.db.commit()
            
            api_key_data = {
                'id': row[0],
                'organization_id': row[1],
                'permissions': row[2] or [],
                'rate_limit_per_hour': row[3],
                'organization_name': row[7],
                'subscription_tier': row[8]
            }
            
            return api_key_data, row[1], None

def require_api_key(f: Callable) -> Callable:
    """Decorator to require API key authentication"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            return jsonify({
                'error': "API key required",
                'code': 'API_KEY_REQUIRED'
            }), 401
        
        api_key_auth = APIKeyAuth(current_app.org_service)
        api_key_data, org_id, error = api_key_auth.authenticate_api_key(api_key)
        
        if error:
            return jsonify({
                'error': error,
                'code': 'API_KEY_INVALID'
            }), 401
        
        # Set API key context
        g.api_key = api_key_data
        g.current_organization_id = org_id
        
        # Set organization context for RLS
        with current_app.org_service.organization_context(org_id):
            return f(*args, **kwargs)
    
    return decorated

def require_api_permission(permission: str):
    """Decorator to require specific API permission"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_api_key
        def decorated(*args, **kwargs):
            api_key = g.api_key
            
            if permission not in api_key['permissions']:
                return jsonify({
                    'error': f"API key missing permission: {permission}",
                    'code': 'API_PERMISSION_DENIED'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator