# ChurnGuard Authentication Middleware
# Epic 3 - Enterprise Features & Multi-Tenancy

import functools
import logging
import json
import time
from typing import Optional, List, Callable, Any, Dict
from flask import request, jsonify, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import redis
import hashlib

from .authentication_service import AuthenticationService
from .organization_service import OrganizationService

logger = logging.getLogger(__name__)

# Initialize rate limiter with Redis backend
def get_redis_client():
    """Get Redis client for rate limiting"""
    try:
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        return redis.Redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Using in-memory rate limiting.")
        return None

def get_rate_limit_key():
    """Get rate limiting key based on authenticated user or IP"""
    if hasattr(g, 'current_user') and g.current_user:
        return f"user:{g.current_user.id}"
    elif hasattr(g, 'api_key') and g.api_key:
        return f"api_key:{g.api_key['id']}"
    else:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        return f"ip:{ip_address}"

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["1000 per day", "100 per hour", "20 per minute"],
    storage_uri="redis://localhost:6379/1",
    strategy="fixed-window-elastic-expiry"
)

class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    def __init__(self, message: str, retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, code: str = "AUTHENTICATION_ERROR", status_code: int = 401):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class AuthorizationError(Exception):
    """Custom exception for authorization errors"""
    def __init__(self, message: str, code: str = "AUTHORIZATION_ERROR", status_code: int = 403):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class EnhancedRateLimiter:
    """Enhanced rate limiter with Redis backend and custom logic"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self.memory_cache = {}  # Fallback for when Redis is unavailable
        
    def is_allowed(self, key: str, limit: int, window: int) -> tuple:
        """
        Check if request is within rate limits
        Returns (allowed: bool, remaining: int, reset_time: int)
        """
        if self.redis:
            return self._redis_rate_limit(key, limit, window)
        else:
            return self._memory_rate_limit(key, limit, window)
    
    def _redis_rate_limit(self, key: str, limit: int, window: int) -> tuple:
        """Redis-based sliding window rate limiting"""
        try:
            pipe = self.redis.pipeline()
            now = time.time()
            window_start = now - window
            
            # Remove expired entries
            pipe.zremrangebyscore(key, '-inf', window_start)
            # Count current requests
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for current request
            
            if current_count <= limit:
                remaining = limit - current_count
                reset_time = int(now + window)
                return True, remaining, reset_time
            else:
                # Remove the request we just added since it's not allowed
                self.redis.zrem(key, str(now))
                remaining = 0
                reset_time = int(now + window)
                return False, remaining, reset_time
                
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return self._memory_rate_limit(key, limit, window)
    
    def _memory_rate_limit(self, key: str, limit: int, window: int) -> tuple:
        """Memory-based rate limiting fallback"""
        now = time.time()
        
        if key not in self.memory_cache:
            self.memory_cache[key] = []
        
        # Clean expired entries
        self.memory_cache[key] = [
            timestamp for timestamp in self.memory_cache[key] 
            if now - timestamp < window
        ]
        
        current_count = len(self.memory_cache[key])
        
        if current_count < limit:
            self.memory_cache[key].append(now)
            remaining = limit - current_count - 1
            reset_time = int(now + window)
            return True, remaining, reset_time
        else:
            remaining = 0
            reset_time = int(now + window)
            return False, remaining, reset_time

# Global rate limiter instance
rate_limiter = EnhancedRateLimiter()

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
        try:
            token = self.extract_token()
            if not token:
                raise AuthenticationError("Missing authentication token", "TOKEN_REQUIRED")
            
            valid, payload, error = self.auth_service.verify_token(token)
            if not valid:
                if "expired" in str(error).lower():
                    raise AuthenticationError("Token has expired", "TOKEN_EXPIRED")
                else:
                    raise AuthenticationError("Invalid token", "TOKEN_INVALID")
            
            # Get fresh user and organization data
            user = self.org_service.get_user(payload['user_id'])
            org = self.org_service.get_organization(payload['organization_id'])
            
            if not user or not user.is_active:
                raise AuthenticationError("User account is inactive", "USER_INACTIVE")
            
            if not org or not org.is_active:
                raise AuthenticationError("Organization is inactive", "ORGANIZATION_INACTIVE")
            
            # Set organization context for RLS
            with self.org_service.organization_context(org.id):
                # Store user and org in Flask's g object for request duration
                g.current_user = user
                g.current_organization = org
                g.user_permissions = user.permissions
            
            return user, org, None
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError("Authentication failed", "INTERNAL_ERROR", 500)

def handle_auth_errors(f: Callable) -> Callable:
    """Decorator to handle authentication and authorization errors"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AuthenticationError as e:
            return jsonify({
                'error': e.message,
                'code': e.code,
                'timestamp': datetime.utcnow().isoformat()
            }), e.status_code
        except AuthorizationError as e:
            return jsonify({
                'error': e.message,
                'code': e.code,
                'timestamp': datetime.utcnow().isoformat()
            }), e.status_code
        except RateLimitError as e:
            return jsonify({
                'error': e.message,
                'code': 'RATE_LIMIT_EXCEEDED',
                'retry_after': e.retry_after,
                'timestamp': datetime.utcnow().isoformat()
            }), 429
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    return decorated

def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for endpoints"""
    @functools.wraps(f)
    @handle_auth_errors
    def decorated(*args, **kwargs):
        middleware = current_app.auth_middleware
        user, org, error = middleware.authenticate_request()
        
        if error:
            raise AuthenticationError(error)
        
        return f(*args, **kwargs)
    
    return decorated

def require_permission(*required_permissions: str):
    """Decorator to require specific permissions"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        @handle_auth_errors
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
                raise AuthorizationError(
                    f"Insufficient permissions. Required: {', '.join(required_permissions)}",
                    "PERMISSION_DENIED"
                )
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_role(*required_roles: str):
    """Decorator to require specific roles"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        @handle_auth_errors
        def decorated(*args, **kwargs):
            user = g.current_user
            
            if user.role.value not in required_roles and not user.is_admin:
                logger.warning(f"Role access denied for user {user.email}: required {required_roles}")
                raise AuthorizationError(
                    f"Insufficient role. Required: {', '.join(required_roles)}",
                    "ROLE_ACCESS_DENIED"
                )
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_admin(f: Callable) -> Callable:
    """Decorator to require admin privileges"""
    @functools.wraps(f)
    @require_auth
    @handle_auth_errors
    def decorated(*args, **kwargs):
        user = g.current_user
        
        if not user.is_admin:
            logger.warning(f"Admin access denied for user {user.email}")
            raise AuthorizationError(
                "Admin privileges required",
                "ADMIN_ACCESS_REQUIRED"
            )
        
        return f(*args, **kwargs)
    
    return decorated

def require_subscription_tier(*required_tiers: str):
    """Decorator to require specific subscription tiers"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        @handle_auth_errors
        def decorated(*args, **kwargs):
            org = g.current_organization
            
            if org.subscription_tier.value not in required_tiers:
                raise AuthorizationError(
                    f"Feature requires subscription tier: {', '.join(required_tiers)}",
                    "SUBSCRIPTION_TIER_REQUIRED",
                    402  # Payment Required
                )
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_feature(feature_name: str):
    """Decorator to require specific organization feature"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @require_auth
        @handle_auth_errors
        def decorated(*args, **kwargs):
            org = g.current_organization
            
            if not org.has_feature(feature_name):
                raise AuthorizationError(
                    f"Feature '{feature_name}' not available for your subscription",
                    "FEATURE_NOT_AVAILABLE",
                    402  # Payment Required
                )
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def optional_auth(f: Callable) -> Callable:
    """Decorator for optional authentication (public endpoints that can benefit from auth)"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            middleware = current_app.auth_middleware
            user, org, error = middleware.authenticate_request()
        except:
            # Don't fail if authentication fails, just set user/org to None
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

def rate_limit(max_requests: int = 100, per_minutes: int = 60, error_message: str = None):
    """Enhanced rate limiting decorator"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        @handle_auth_errors
        def decorated(*args, **kwargs):
            # Get rate limit key
            key = get_rate_limit_key()
            window = per_minutes * 60  # Convert to seconds
            
            # Check rate limit
            allowed, remaining, reset_time = rate_limiter.is_allowed(
                f"rate_limit:{f.__name__}:{key}", 
                max_requests, 
                window
            )
            
            if not allowed:
                retry_after = max(1, reset_time - int(time.time()))
                message = error_message or f"Rate limit exceeded. Max {max_requests} requests per {per_minutes} minutes."
                
                logger.warning(f"Rate limit exceeded for {key}: {f.__name__}")
                raise RateLimitError(message, retry_after)
            
            # Add rate limit headers to response
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(reset_time)
            
            return response
        
        return decorated
    return decorator

# Specific rate limit decorators for common patterns
def auth_rate_limit(f: Callable) -> Callable:
    """Rate limit for authentication endpoints"""
    return rate_limit(
        max_requests=5, 
        per_minutes=15,
        error_message="Too many authentication attempts. Please try again later."
    )(f)

def api_rate_limit(f: Callable) -> Callable:
    """Standard API rate limit"""
    return rate_limit(
        max_requests=100,
        per_minutes=60,
        error_message="API rate limit exceeded. Please reduce request frequency."
    )(f)

def strict_rate_limit(f: Callable) -> Callable:
    """Strict rate limit for sensitive operations"""
    return rate_limit(
        max_requests=3,
        per_minutes=60,
        error_message="Rate limit for sensitive operations exceeded."
    )(f)

class APIKeyAuth:
    """API Key authentication for programmatic access"""
    
    def __init__(self, org_service: OrganizationService):
        self.org_service = org_service
    
    def authenticate_api_key(self, api_key: str) -> tuple:
        """Authenticate API key and return organization/permissions"""
        try:
            if not api_key or not api_key.startswith('cg_'):
                raise AuthenticationError("Invalid API key format", "API_KEY_INVALID")
            
            # Hash the API key
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
                    raise AuthenticationError("Invalid API key", "API_KEY_INVALID")
                
                # Check if API key is active and not expired
                if not row[4]:  # is_active
                    raise AuthenticationError("API key is disabled", "API_KEY_DISABLED")
                
                if row[5] and row[5] < datetime.now():  # expires_at
                    raise AuthenticationError("API key has expired", "API_KEY_EXPIRED")
                
                if not row[9]:  # org_active
                    raise AuthenticationError("Organization is inactive", "ORGANIZATION_INACTIVE")
                
                # Check hourly rate limit for API key
                if row[3]:  # rate_limit_per_hour
                    hourly_key = f"api_key_hourly:{row[0]}:{datetime.now().strftime('%Y%m%d%H')}"
                    allowed, remaining, reset_time = rate_limiter.is_allowed(
                        hourly_key, row[3], 3600  # 1 hour window
                    )
                    
                    if not allowed:
                        retry_after = max(1, reset_time - int(time.time()))
                        raise RateLimitError(
                            f"API key hourly rate limit exceeded. Limit: {row[3]} requests/hour",
                            retry_after
                        )
                
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
                
        except (AuthenticationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            raise AuthenticationError("API key authentication failed", "INTERNAL_ERROR", 500)

def require_api_key(f: Callable) -> Callable:
    """Decorator to require API key authentication"""
    @functools.wraps(f)
    @handle_auth_errors
    def decorated(*args, **kwargs):
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            raise AuthenticationError("API key required", "API_KEY_REQUIRED")
        
        api_key_auth = APIKeyAuth(current_app.org_service)
        api_key_data, org_id, error = api_key_auth.authenticate_api_key(api_key)
        
        if error:
            raise AuthenticationError(error, "API_KEY_INVALID")
        
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
        @handle_auth_errors
        def decorated(*args, **kwargs):
            api_key = g.api_key
            
            if permission not in api_key['permissions']:
                raise AuthorizationError(
                    f"API key missing permission: {permission}",
                    "API_PERMISSION_DENIED"
                )
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def log_security_event(event_type: str, details: Dict[str, Any] = None):
    """Log security-related events for monitoring"""
    try:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        user_id = getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') else None
        org_id = getattr(g, 'current_organization', {}).get('id') if hasattr(g, 'current_organization') else None
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'user_id': user_id,
            'organization_id': org_id,
            'details': details or {}
        }
        
        logger.info(f"Security event: {json.dumps(log_data)}")
        
        # In production, send to SIEM or security monitoring system
        
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")

# Initialize error handlers for Flask app
def init_auth_error_handlers(app):
    """Initialize authentication error handlers for Flask app"""
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'code': 'RATE_LIMIT_EXCEEDED',
            'timestamp': datetime.utcnow().isoformat()
        }), 429
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        return jsonify({
            'error': 'Authentication required',
            'code': 'AUTHENTICATION_REQUIRED',
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        return jsonify({
            'error': 'Access forbidden',
            'code': 'ACCESS_FORBIDDEN',
            'timestamp': datetime.utcnow().isoformat()
        }), 403