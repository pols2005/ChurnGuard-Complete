# ChurnGuard Enterprise Authentication Service
# Epic 3 - Enterprise Features & Multi-Tenancy

import jwt
import secrets
import hashlib
import logging
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
import xml.etree.ElementTree as ET
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from .models import (
    User, Organization, SSOProvider, SSOConfiguration,
    UserRole, get_default_permissions
)
from .organization_service import OrganizationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationService:
    """Enterprise-grade authentication service supporting SSO, SAML, and RBAC"""
    
    def __init__(self, db_connection, org_service: OrganizationService):
        self.db = db_connection
        self.org_service = org_service
        self.jwt_secret = self._get_jwt_secret()
        self.session_timeout = timedelta(hours=8)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def _get_jwt_secret(self) -> str:
        """Get or create JWT secret"""
        # In production, this should come from environment variables
        return "your-enterprise-jwt-secret-key-change-in-production"
    
    # ==================== LOCAL AUTHENTICATION ====================
    
    def authenticate_user(
        self, 
        email: str, 
        password: str, 
        organization_slug: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate user with email/password"""
        
        # Find organization
        if organization_slug:
            org = self.org_service.get_organization_by_slug(organization_slug)
            if not org:
                return False, None, "Organization not found"
            org_id = org.id
        else:
            # For backwards compatibility, find user across all orgs
            user = self._find_user_by_email(email)
            if not user:
                return False, None, "Invalid credentials"
            org_id = user.organization_id
            org = self.org_service.get_organization(org_id)
        
        # Get user within organization context
        with self.org_service.organization_context(org_id):
            user = self.org_service.get_user_by_email(org_id, email)
            
            if not user:
                # Log failed attempt
                self._log_auth_event(org_id, 'login_failed', email=email, 
                                   ip_address=ip_address, reason='user_not_found')
                return False, None, "Invalid credentials"
            
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.now():
                remaining_minutes = int((user.locked_until - datetime.now()).total_seconds() / 60)
                self._log_auth_event(org_id, 'login_blocked_locked', user_id=user.id,
                                   email=email, ip_address=ip_address)
                return False, None, f"Account locked. Try again in {remaining_minutes} minutes"
            
            # Check if account is active
            if not user.is_active:
                self._log_auth_event(org_id, 'login_failed', user_id=user.id,
                                   email=email, ip_address=ip_address, reason='account_inactive')
                return False, None, "Account is inactive"
            
            # Verify password
            if not user.password_hash or not self.org_service._verify_password(password, user.password_hash):
                self._handle_failed_login(user, ip_address)
                return False, None, "Invalid credentials"
            
            # Reset failed attempts on successful login
            self._reset_failed_attempts(user.id)
            
            # Update last login
            self._update_last_login(user.id, ip_address)
            
            # Generate session token
            session_data = self._create_session(user, org, ip_address, user_agent)
            
            # Log successful login
            self._log_auth_event(org_id, 'login_success', user_id=user.id,
                               email=email, ip_address=ip_address)
            
            logger.info(f"Successful login: {email} from {ip_address}")
            
            return True, session_data, None
    
    def _find_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email across all organizations"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id, organization_id FROM users 
                WHERE email = %s AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """, (email,))
            
            row = cursor.fetchone()
            if row:
                return self.org_service.get_user(row[0])
        
        return None
    
    def _handle_failed_login(self, user: User, ip_address: Optional[str]):
        """Handle failed login attempt"""
        new_attempts = user.failed_login_attempts + 1
        
        # Lock account if too many failures
        locked_until = None
        if new_attempts >= self.max_failed_attempts:
            locked_until = datetime.now() + self.lockout_duration
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = %s, locked_until = %s
                WHERE id = %s
            """, (new_attempts, locked_until, user.id))
            
            self.db.commit()
        
        # Log failed attempt
        self._log_auth_event(
            user.organization_id, 'login_failed', user_id=user.id,
            email=user.email, ip_address=ip_address,
            event_data={'failed_attempts': new_attempts, 'locked': locked_until is not None}
        )
        
        if locked_until:
            logger.warning(f"Account locked due to failed attempts: {user.email}")
    
    def _reset_failed_attempts(self, user_id: str):
        """Reset failed login attempts"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL
                WHERE id = %s
            """, (user_id,))
            
            self.db.commit()
    
    def _update_last_login(self, user_id: str, ip_address: Optional[str]):
        """Update user's last login timestamp"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET last_login_at = %s, last_login_ip = %s
                WHERE id = %s
            """, (datetime.now(), ip_address, user_id))
            
            self.db.commit()
    
    # ==================== SSO AUTHENTICATION ====================
    
    def initiate_sso_login(
        self, 
        org_id: str, 
        provider: SSOProvider,
        redirect_uri: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Initiate SSO login flow"""
        
        # Get SSO configuration
        sso_config = self.get_sso_configuration(org_id, provider)
        if not sso_config or not sso_config.is_active:
            return False, None, "SSO not configured for this organization"
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session/cache
        self._store_sso_state(state, org_id, provider.value, redirect_uri)
        
        if provider == SSOProvider.GOOGLE:
            auth_url = self._build_google_auth_url(sso_config, redirect_uri, state)
        elif provider == SSOProvider.MICROSOFT:
            auth_url = self._build_microsoft_auth_url(sso_config, redirect_uri, state)
        elif provider == SSOProvider.OKTA:
            auth_url = self._build_okta_auth_url(sso_config, redirect_uri, state)
        elif provider == SSOProvider.SAML:
            auth_url = self._build_saml_auth_url(sso_config, redirect_uri, state)
        else:
            return False, None, f"Unsupported SSO provider: {provider.value}"
        
        return True, auth_url, None
    
    def _build_google_auth_url(self, config: SSOConfiguration, redirect_uri: str, state: str) -> str:
        """Build Google OAuth2 authorization URL"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': config.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state,
            'access_type': 'offline'
        }
        return f"{base_url}?{urlencode(params)}"
    
    def _build_microsoft_auth_url(self, config: SSOConfiguration, redirect_uri: str, state: str) -> str:
        """Build Microsoft Azure AD authorization URL"""
        tenant_id = config.config.get('tenant_id', 'common')
        base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        params = {
            'client_id': config.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state,
            'response_mode': 'query'
        }
        return f"{base_url}?{urlencode(params)}"
    
    def _build_okta_auth_url(self, config: SSOConfiguration, redirect_uri: str, state: str) -> str:
        """Build Okta authorization URL"""
        domain = config.config.get('domain')
        if not domain:
            raise ValueError("Okta domain not configured")
        
        base_url = f"https://{domain}/oauth2/v1/authorize"
        params = {
            'client_id': config.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state
        }
        return f"{base_url}?{urlencode(params)}"
    
    def _build_saml_auth_url(self, config: SSOConfiguration, redirect_uri: str, state: str) -> str:
        """Build SAML SSO URL"""
        # For SAML, we typically redirect to the configured SSO URL
        # with our service as the RelayState
        sso_url = config.sso_url
        if not sso_url:
            raise ValueError("SAML SSO URL not configured")
        
        # Add RelayState for post-auth redirect
        separator = '&' if '?' in sso_url else '?'
        return f"{sso_url}{separator}RelayState={state}"
    
    def handle_sso_callback(
        self, 
        provider: SSOProvider,
        auth_code: Optional[str] = None,
        state: Optional[str] = None,
        saml_response: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Handle SSO callback and complete authentication"""
        
        if not state:
            return False, None, "Missing state parameter"
        
        # Verify and retrieve stored state
        stored_state = self._get_sso_state(state)
        if not stored_state:
            return False, None, "Invalid or expired state parameter"
        
        org_id = stored_state['org_id']
        redirect_uri = stored_state['redirect_uri']
        
        try:
            if provider in [SSOProvider.GOOGLE, SSOProvider.MICROSOFT, SSOProvider.OKTA]:
                if not auth_code:
                    return False, None, "Missing authorization code"
                
                user_info = self._exchange_oauth_code(provider, org_id, auth_code, redirect_uri)
            elif provider == SSOProvider.SAML:
                if not saml_response:
                    return False, None, "Missing SAML response"
                
                user_info = self._process_saml_response(org_id, saml_response)
            else:
                return False, None, f"Unsupported provider: {provider.value}"
            
            # Create or update user
            user, org = self._create_or_update_sso_user(org_id, provider, user_info)
            
            # Create session
            session_data = self._create_session(user, org, ip_address, user_agent)
            
            # Log successful SSO login
            self._log_auth_event(org_id, 'sso_login_success', user_id=user.id,
                               email=user.email, ip_address=ip_address,
                               event_data={'provider': provider.value})
            
            # Clean up state
            self._cleanup_sso_state(state)
            
            return True, session_data, None
            
        except Exception as e:
            logger.error(f"SSO callback error: {e}")
            self._log_auth_event(org_id, 'sso_login_failed', 
                               ip_address=ip_address,
                               event_data={'provider': provider.value, 'error': str(e)})
            return False, None, "SSO authentication failed"
    
    def _exchange_oauth_code(
        self, 
        provider: SSOProvider, 
        org_id: str, 
        auth_code: str, 
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange OAuth authorization code for user info"""
        import requests
        
        config = self.get_sso_configuration(org_id, provider)
        if not config:
            raise ValueError("SSO configuration not found")
        
        # Get token endpoint
        if provider == SSOProvider.GOOGLE:
            token_url = "https://oauth2.googleapis.com/token"
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        elif provider == SSOProvider.MICROSOFT:
            tenant_id = config.config.get('tenant_id', 'common')
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            userinfo_url = "https://graph.microsoft.com/v1.0/me"
        elif provider == SSOProvider.OKTA:
            domain = config.config.get('domain')
            token_url = f"https://{domain}/oauth2/v1/token"
            userinfo_url = f"https://{domain}/oauth2/v1/userinfo"
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider.value}")
        
        # Exchange code for token
        token_data = {
            'client_id': config.client_id,
            'client_secret': self._decrypt_client_secret(config.client_secret_encrypted),
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()
        
        # Get user info
        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        user_response = requests.get(userinfo_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Normalize user info across providers
        return self._normalize_oauth_user_info(provider, user_info)
    
    def _process_saml_response(self, org_id: str, saml_response: str) -> Dict[str, Any]:
        """Process SAML response and extract user info"""
        # This is a simplified SAML processor
        # In production, use a proper SAML library like python3-saml
        
        try:
            # Decode and parse SAML response
            import base64
            decoded = base64.b64decode(saml_response)
            root = ET.fromstring(decoded)
            
            # Extract user attributes (simplified)
            email = None
            first_name = None
            last_name = None
            
            # Find assertion attributes
            for attr in root.findall(".//saml:Attribute", {"saml": "urn:oasis:names:tc:SAML:2.0:assertion"}):
                attr_name = attr.get("Name")
                attr_values = [v.text for v in attr.findall(".//saml:AttributeValue", {"saml": "urn:oasis:names:tc:SAML:2.0:assertion"})]
                
                if attr_name in ["email", "emailaddress", "mail"] and attr_values:
                    email = attr_values[0]
                elif attr_name in ["firstname", "givenname"] and attr_values:
                    first_name = attr_values[0]
                elif attr_name in ["lastname", "surname"] and attr_values:
                    last_name = attr_values[0]
            
            if not email:
                raise ValueError("Email not found in SAML response")
            
            return {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'sso_id': email  # Use email as SSO ID for SAML
            }
            
        except Exception as e:
            raise ValueError(f"Invalid SAML response: {e}")
    
    def _normalize_oauth_user_info(self, provider: SSOProvider, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize user info from different OAuth providers"""
        if provider == SSOProvider.GOOGLE:
            return {
                'email': user_info.get('email'),
                'first_name': user_info.get('given_name'),
                'last_name': user_info.get('family_name'),
                'avatar_url': user_info.get('picture'),
                'sso_id': user_info.get('id')
            }
        elif provider == SSOProvider.MICROSOFT:
            return {
                'email': user_info.get('mail') or user_info.get('userPrincipalName'),
                'first_name': user_info.get('givenName'),
                'last_name': user_info.get('surname'),
                'sso_id': user_info.get('id')
            }
        elif provider == SSOProvider.OKTA:
            return {
                'email': user_info.get('email'),
                'first_name': user_info.get('given_name'),
                'last_name': user_info.get('family_name'),
                'sso_id': user_info.get('sub')
            }
        
        return user_info
    
    def _create_or_update_sso_user(
        self, 
        org_id: str, 
        provider: SSOProvider, 
        user_info: Dict[str, Any]
    ) -> Tuple[User, Organization]:
        """Create or update user from SSO authentication"""
        
        email = user_info.get('email')
        sso_id = user_info.get('sso_id')
        
        if not email:
            raise ValueError("Email required for SSO user creation")
        
        org = self.org_service.get_organization(org_id)
        if not org:
            raise ValueError("Organization not found")
        
        with self.org_service.organization_context(org_id):
            # Try to find existing user by email or SSO ID
            user = self.org_service.get_user_by_email(org_id, email)
            
            if not user:
                # Check by SSO ID
                with self.db.cursor() as cursor:
                    cursor.execute("""
                        SELECT id FROM users 
                        WHERE organization_id = %s AND sso_provider = %s AND sso_id = %s
                    """, (org_id, provider.value, sso_id))
                    
                    row = cursor.fetchone()
                    if row:
                        user = self.org_service.get_user(row[0])
            
            if user:
                # Update existing user
                self._update_user_from_sso(user, provider, user_info)
            else:
                # Create new user
                user = self._create_sso_user(org_id, provider, user_info)
        
        return user, org
    
    def _create_sso_user(self, org_id: str, provider: SSOProvider, user_info: Dict[str, Any]) -> User:
        """Create new SSO user"""
        user_data = {
            'first_name': user_info.get('first_name'),
            'last_name': user_info.get('last_name'),
            'avatar_url': user_info.get('avatar_url'),
            'sso_provider': provider,
            'sso_id': user_info.get('sso_id'),
            'sso_metadata': user_info,
            'email_verified': True  # SSO emails are considered verified
        }
        
        return self.org_service.create_user(
            org_id=org_id,
            email=user_info['email'],
            password=None,  # No password for SSO users
            role=UserRole.USER,
            **user_data
        )
    
    def _update_user_from_sso(self, user: User, provider: SSOProvider, user_info: Dict[str, Any]):
        """Update existing user with SSO info"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, avatar_url = %s,
                    sso_provider = %s, sso_id = %s, sso_metadata = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                user_info.get('first_name'), user_info.get('last_name'),
                user_info.get('avatar_url'), provider.value, user_info.get('sso_id'),
                json.dumps(user_info), datetime.now(), user.id
            ))
            
            self.db.commit()
    
    # ==================== SESSION MANAGEMENT ====================
    
    def _create_session(
        self, 
        user: User, 
        org: Organization, 
        ip_address: Optional[str], 
        user_agent: Optional[str]
    ) -> Dict[str, Any]:
        """Create session data and JWT token"""
        
        # Session payload
        payload = {
            'user_id': user.id,
            'organization_id': org.id,
            'organization_slug': org.slug,
            'email': user.email,
            'role': user.role.value,
            'permissions': user.permissions,
            'is_admin': user.is_admin,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + self.session_timeout
        }
        
        # Generate JWT token
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
        return {
            'token': token,
            'user': user.to_dict(),
            'organization': org.to_dict(),
            'expires_at': payload['exp'].isoformat(),
            'permissions': user.permissions
        }
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify JWT token and return session data"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check if user and org still exist and are active
            user = self.org_service.get_user(payload['user_id'])
            org = self.org_service.get_organization(payload['organization_id'])
            
            if not user or not user.is_active:
                return False, None, "User account is inactive"
            
            if not org or not org.is_active:
                return False, None, "Organization is inactive"
            
            return True, payload, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError:
            return False, None, "Invalid token"
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, None, "Token verification failed"
    
    def refresh_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Refresh JWT token"""
        valid, payload, error = self.verify_token(token)
        
        if not valid:
            return False, None, error
        
        # Get fresh user and org data
        user = self.org_service.get_user(payload['user_id'])
        org = self.org_service.get_organization(payload['organization_id'])
        
        if not user or not org:
            return False, None, "User or organization not found"
        
        # Create new session
        session_data = self._create_session(user, org, None, None)
        
        return True, session_data['token'], None
    
    def logout(self, token: str, ip_address: Optional[str] = None):
        """Logout user and invalidate token"""
        valid, payload, _ = self.verify_token(token)
        
        if valid and payload:
            # Log logout event
            self._log_auth_event(
                payload['organization_id'], 'logout', 
                user_id=payload['user_id'], email=payload['email'],
                ip_address=ip_address
            )
            
            # In a full implementation, you'd add token to a blacklist
            logger.info(f"User logged out: {payload['email']}")
    
    # ==================== SSO CONFIGURATION ====================
    
    def get_sso_configuration(self, org_id: str, provider: SSOProvider) -> Optional[SSOConfiguration]:
        """Get SSO configuration for organization and provider"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT id, organization_id, provider, provider_name, is_active,
                       config, metadata, entity_id, sso_url, certificate,
                       client_id, client_secret_encrypted, discovery_url,
                       created_at, updated_at, created_by
                FROM sso_configurations 
                WHERE organization_id = %s AND provider = %s AND is_active = TRUE
            """, (org_id, provider.value))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return SSOConfiguration(
                id=row[0], organization_id=row[1], provider=SSOProvider(row[2]),
                provider_name=row[3], is_active=row[4], config=row[5] or {},
                metadata=row[6] or {}, entity_id=row[7], sso_url=row[8],
                certificate=row[9], client_id=row[10], 
                client_secret_encrypted=row[11], discovery_url=row[12],
                created_at=row[13], updated_at=row[14], created_by=row[15]
            )
    
    def create_sso_configuration(
        self, 
        org_id: str, 
        provider: SSOProvider,
        provider_name: str,
        config_data: Dict[str, Any],
        created_by: str
    ) -> SSOConfiguration:
        """Create SSO configuration for organization"""
        
        config = SSOConfiguration(
            organization_id=org_id,
            provider=provider,
            provider_name=provider_name,
            config=config_data,
            created_by=created_by,
            **config_data
        )
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sso_configurations 
                (id, organization_id, provider, provider_name, is_active, config,
                 entity_id, sso_url, certificate, client_id, client_secret_encrypted,
                 discovery_url, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                config.id, config.organization_id, config.provider.value,
                config.provider_name, config.is_active, json.dumps(config.config),
                config.entity_id, config.sso_url, config.certificate,
                config.client_id, config.client_secret_encrypted, config.discovery_url,
                config.created_at, config.created_by
            ))
            
            self.db.commit()
        
        return config
    
    # ==================== RBAC METHODS ====================
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user = self.org_service.get_user(user_id)
        if not user:
            return False
        
        return user.has_permission(permission)
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for user"""
        user = self.org_service.get_user(user_id)
        if not user:
            return []
        
        if user.is_admin:
            # Admins have all permissions
            return [
                'user.create', 'user.read', 'user.update', 'user.delete',
                'customer.create', 'customer.read', 'customer.update', 'customer.delete',
                'prediction.create', 'prediction.read', 'analytics.read',
                'organization.read', 'organization.update', 'api.manage',
                'export.create', 'audit.read'
            ]
        
        return user.permissions
    
    def update_user_permissions(self, user_id: str, permissions: List[str], updated_by: str) -> bool:
        """Update user permissions"""
        with self.db.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET permissions = %s, updated_at = %s
                WHERE id = %s
            """, (json.dumps(permissions), datetime.now(), user_id))
            
            if cursor.rowcount > 0:
                self.db.commit()
                
                # Get user for audit log
                user = self.org_service.get_user(user_id)
                if user:
                    self._log_auth_event(
                        user.organization_id, 'permissions_updated',
                        user_id=updated_by, resource_type='user', resource_id=user_id,
                        event_data={'new_permissions': permissions}
                    )
                
                return True
        
        return False
    
    # ==================== UTILITY METHODS ====================
    
    def _store_sso_state(self, state: str, org_id: str, provider: str, redirect_uri: str):
        """Store SSO state (in production, use Redis or similar)"""
        # Simple in-memory storage for demo
        # In production, use Redis with expiration
        if not hasattr(self, '_sso_states'):
            self._sso_states = {}
        
        self._sso_states[state] = {
            'org_id': org_id,
            'provider': provider,
            'redirect_uri': redirect_uri,
            'created_at': datetime.now()
        }
    
    def _get_sso_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Get stored SSO state"""
        if not hasattr(self, '_sso_states'):
            return None
        
        stored_state = self._sso_states.get(state)
        if not stored_state:
            return None
        
        # Check expiration (5 minutes)
        if datetime.now() - stored_state['created_at'] > timedelta(minutes=5):
            self._sso_states.pop(state, None)
            return None
        
        return stored_state
    
    def _cleanup_sso_state(self, state: str):
        """Clean up SSO state"""
        if hasattr(self, '_sso_states'):
            self._sso_states.pop(state, None)
    
    def _decrypt_client_secret(self, encrypted_secret: str) -> str:
        """Decrypt client secret (implement proper encryption)"""
        # This is a placeholder - implement proper encryption/decryption
        # In production, use proper key management
        return encrypted_secret
    
    def _log_auth_event(
        self, 
        org_id: str, 
        event_type: str, 
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ):
        """Log authentication event"""
        if reason and event_data:
            event_data['reason'] = reason
        elif reason:
            event_data = {'reason': reason}
        
        self.org_service._log_audit_event(
            org_id=org_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            event_data=event_data
        )

import json