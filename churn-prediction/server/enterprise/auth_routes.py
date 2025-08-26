# ChurnGuard Authentication API Routes
# Epic 3 - Enterprise Features & Multi-Tenancy

from flask import Blueprint, request, jsonify, make_response, redirect, url_for, g
from datetime import datetime, timedelta
import logging

from .authentication_service import AuthenticationService
from .organization_service import OrganizationService
from .models import SSOProvider, UserRole, SubscriptionTier
from .auth_middleware import (
    require_auth, require_admin, require_permission, 
    get_organization_from_request, rate_limit
)

logger = logging.getLogger(__name__)

def create_auth_blueprint(auth_service: AuthenticationService, org_service: OrganizationService) -> Blueprint:
    """Create authentication blueprint with all auth routes"""
    
    bp = Blueprint('auth', __name__, url_prefix='/api/auth')
    
    # ==================== LOCAL AUTHENTICATION ====================
    
    @bp.route('/login', methods=['POST'])
    @rate_limit(max_requests=5, per_minutes=15)  # Stricter rate limit for login
    def login():
        """Local email/password authentication"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            organization_slug = data.get('organization')
            
            if not email or not password:
                return jsonify({'error': 'Email and password required'}), 400
            
            # If no organization provided, try to detect from request
            if not organization_slug:
                organization_slug = get_organization_from_request()
            
            # Get client info
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')
            
            # Authenticate
            success, session_data, error = auth_service.authenticate_user(
                email=email,
                password=password,
                organization_slug=organization_slug,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if not success:
                return jsonify({'error': error, 'code': 'AUTHENTICATION_FAILED'}), 401
            
            # Set HTTP-only cookie for web clients
            response = make_response(jsonify({
                'success': True,
                'user': session_data['user'],
                'organization': session_data['organization'],
                'permissions': session_data['permissions'],
                'expires_at': session_data['expires_at']
            }))
            
            # Set secure cookie
            response.set_cookie(
                'auth_token',
                session_data['token'],
                max_age=int(timedelta(hours=8).total_seconds()),
                secure=request.is_secure,
                httponly=True,
                samesite='Lax'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Authentication failed', 'code': 'INTERNAL_ERROR'}), 500
    
    @bp.route('/logout', methods=['POST'])
    @require_auth
    def logout():
        """Logout user and invalidate session"""
        try:
            # Get token from header or cookie
            token = None
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = request.cookies.get('auth_token')
            
            if token:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                auth_service.logout(token, ip_address)
            
            # Clear cookie
            response = make_response(jsonify({'success': True, 'message': 'Logged out successfully'}))
            response.set_cookie('auth_token', '', expires=0, httponly=True, samesite='Lax')
            
            return response
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({'error': 'Logout failed'}), 500
    
    @bp.route('/refresh', methods=['POST'])
    def refresh_token():
        """Refresh JWT token"""
        try:
            # Get current token
            token = None
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = request.cookies.get('auth_token')
            
            if not token:
                return jsonify({'error': 'No token provided', 'code': 'TOKEN_REQUIRED'}), 401
            
            success, new_token, error = auth_service.refresh_token(token)
            
            if not success:
                return jsonify({'error': error, 'code': 'TOKEN_REFRESH_FAILED'}), 401
            
            # Update cookie with new token
            response = make_response(jsonify({'success': True, 'message': 'Token refreshed'}))
            response.set_cookie(
                'auth_token',
                new_token,
                max_age=int(timedelta(hours=8).total_seconds()),
                secure=request.is_secure,
                httponly=True,
                samesite='Lax'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return jsonify({'error': 'Token refresh failed'}), 500
    
    @bp.route('/me', methods=['GET'])
    @require_auth
    def get_current_user():
        """Get current user information"""
        user = g.current_user
        org = g.current_organization
        
        return jsonify({
            'user': user.to_dict(),
            'organization': org.to_dict(),
            'permissions': user.permissions
        })
    
    # ==================== SSO AUTHENTICATION ====================
    
    @bp.route('/sso/<provider>/login', methods=['GET'])
    def sso_login(provider):
        """Initiate SSO login"""
        try:
            # Validate provider
            try:
                sso_provider = SSOProvider(provider.lower())
            except ValueError:
                return jsonify({'error': f'Unsupported SSO provider: {provider}'}), 400
            
            # Get organization
            org_slug = request.args.get('org') or get_organization_from_request()
            if not org_slug:
                return jsonify({'error': 'Organization required for SSO'}), 400
            
            org = org_service.get_organization_by_slug(org_slug)
            if not org:
                return jsonify({'error': 'Organization not found'}), 404
            
            # Check if SSO is enabled for this org
            if not org.has_feature('sso'):
                return jsonify({
                    'error': 'SSO not available for your subscription',
                    'code': 'SSO_NOT_AVAILABLE'
                }), 402
            
            # Get redirect URI
            redirect_uri = request.args.get('redirect_uri', request.url_root.rstrip('/') + f'/api/auth/sso/{provider}/callback')
            
            # Initiate SSO
            success, auth_url, error = auth_service.initiate_sso_login(
                org_id=org.id,
                provider=sso_provider,
                redirect_uri=redirect_uri
            )
            
            if not success:
                return jsonify({'error': error}), 400
            
            # Redirect to SSO provider
            return redirect(auth_url)
            
        except Exception as e:
            logger.error(f"SSO login initiation error: {e}")
            return jsonify({'error': 'SSO login failed'}), 500
    
    @bp.route('/sso/<provider>/callback', methods=['GET', 'POST'])
    def sso_callback(provider):
        """Handle SSO callback"""
        try:
            # Validate provider
            try:
                sso_provider = SSOProvider(provider.lower())
            except ValueError:
                return jsonify({'error': f'Unsupported SSO provider: {provider}'}), 400
            
            # Get callback parameters
            if request.method == 'GET':
                auth_code = request.args.get('code')
                state = request.args.get('state')
                saml_response = None
            else:  # POST for SAML
                auth_code = None
                state = request.form.get('RelayState')
                saml_response = request.form.get('SAMLResponse')
            
            # Get client info
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')
            
            # Handle SSO callback
            success, session_data, error = auth_service.handle_sso_callback(
                provider=sso_provider,
                auth_code=auth_code,
                state=state,
                saml_response=saml_response,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if not success:
                return jsonify({'error': error}), 401
            
            # Set cookie and redirect
            response = make_response(redirect('/dashboard'))  # Adjust redirect as needed
            response.set_cookie(
                'auth_token',
                session_data['token'],
                max_age=int(timedelta(hours=8).total_seconds()),
                secure=request.is_secure,
                httponly=True,
                samesite='Lax'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"SSO callback error: {e}")
            return jsonify({'error': 'SSO authentication failed'}), 500
    
    # ==================== SSO CONFIGURATION (Admin Only) ====================
    
    @bp.route('/sso/config', methods=['GET'])
    @require_permission('organization.read')
    def get_sso_configurations():
        """Get SSO configurations for organization"""
        org = g.current_organization
        
        with org_service.db.cursor() as cursor:
            cursor.execute("""
                SELECT provider, provider_name, is_active, created_at
                FROM sso_configurations 
                WHERE organization_id = %s
                ORDER BY created_at DESC
            """, (org.id,))
            
            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'provider': row[0],
                    'provider_name': row[1],
                    'is_active': row[2],
                    'created_at': row[3].isoformat()
                })
        
        return jsonify({'configurations': configs})
    
    @bp.route('/sso/config', methods=['POST'])
    @require_admin
    def create_sso_configuration():
        """Create SSO configuration"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            org = g.current_organization
            user = g.current_user
            
            # Check if enterprise tier
            if org.subscription_tier != SubscriptionTier.ENTERPRISE:
                return jsonify({
                    'error': 'SSO configuration requires Enterprise subscription',
                    'code': 'SUBSCRIPTION_REQUIRED'
                }), 402
            
            provider = data.get('provider')
            provider_name = data.get('provider_name')
            config_data = data.get('config', {})
            
            if not provider or not provider_name:
                return jsonify({'error': 'Provider and provider name required'}), 400
            
            try:
                sso_provider = SSOProvider(provider.lower())
            except ValueError:
                return jsonify({'error': f'Unsupported provider: {provider}'}), 400
            
            # Create configuration
            config = auth_service.create_sso_configuration(
                org_id=org.id,
                provider=sso_provider,
                provider_name=provider_name,
                config_data=config_data,
                created_by=user.id
            )
            
            return jsonify({
                'success': True,
                'message': 'SSO configuration created',
                'configuration': {
                    'id': config.id,
                    'provider': config.provider.value,
                    'provider_name': config.provider_name,
                    'is_active': config.is_active
                }
            })
            
        except Exception as e:
            logger.error(f"SSO configuration creation error: {e}")
            return jsonify({'error': 'Failed to create SSO configuration'}), 500
    
    # ==================== USER MANAGEMENT ====================
    
    @bp.route('/users', methods=['GET'])
    @require_permission('user.read')
    def list_users():
        """List users in organization"""
        org = g.current_organization
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        role = request.args.get('role')
        
        role_filter = UserRole(role) if role else None
        
        users = org_service.get_organization_users(
            org_id=org.id,
            limit=per_page,
            offset=(page - 1) * per_page,
            role=role_filter
        )
        
        user_count = org_service.get_user_count(org.id)
        
        return jsonify({
            'users': [user.to_dict() for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': user_count,
                'pages': (user_count + per_page - 1) // per_page
            }
        })
    
    @bp.route('/users', methods=['POST'])
    @require_permission('user.create')
    def create_user():
        """Create new user"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            org = g.current_organization
            current_user = g.current_user
            
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            role = data.get('role', 'user')
            
            if not email:
                return jsonify({'error': 'Email required'}), 400
            
            try:
                user_role = UserRole(role)
            except ValueError:
                return jsonify({'error': f'Invalid role: {role}'}), 400
            
            # Create user
            user = org_service.create_user(
                org_id=org.id,
                email=email,
                password=password,
                role=user_role,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                phone=data.get('phone'),
                timezone=data.get('timezone', 'UTC'),
                locale=data.get('locale', 'en')
            )
            
            return jsonify({
                'success': True,
                'message': 'User created successfully',
                'user': user.to_dict()
            }), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return jsonify({'error': 'Failed to create user'}), 500
    
    @bp.route('/users/<user_id>/permissions', methods=['PUT'])
    @require_admin
    def update_user_permissions(user_id):
        """Update user permissions"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            permissions = data.get('permissions', [])
            if not isinstance(permissions, list):
                return jsonify({'error': 'Permissions must be a list'}), 400
            
            current_user = g.current_user
            
            success = auth_service.update_user_permissions(
                user_id=user_id,
                permissions=permissions,
                updated_by=current_user.id
            )
            
            if not success:
                return jsonify({'error': 'Failed to update permissions'}), 400
            
            return jsonify({
                'success': True,
                'message': 'Permissions updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Permission update error: {e}")
            return jsonify({'error': 'Failed to update permissions'}), 500
    
    # ==================== ORGANIZATION MANAGEMENT ====================
    
    @bp.route('/organization', methods=['GET'])
    @require_auth
    def get_organization():
        """Get current organization details"""
        org = g.current_organization
        
        return jsonify({
            'organization': org.to_dict(),
            'features': {
                'sso': org.has_feature('sso'),
                'custom_colors': org.has_feature('custom_colors'),
                'logo_upload': org.has_feature('logo_upload'),
                'custom_css': org.has_feature('custom_css'),
                'white_label': org.has_feature('white_label'),
                'api_access': org.has_feature('api_access')
            }
        })
    
    @bp.route('/organization', methods=['PUT'])
    @require_permission('organization.update')
    def update_organization():
        """Update organization settings"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            org = g.current_organization
            user = g.current_user
            
            # Filter allowed updates based on subscription
            allowed_updates = {}
            
            # Basic updates for all tiers
            if 'billing_email' in data:
                allowed_updates['billing_email'] = data['billing_email']
            
            # Professional+ features
            if org.has_feature('custom_colors'):
                if 'primary_color' in data:
                    allowed_updates['primary_color'] = data['primary_color']
                if 'secondary_color' in data:
                    allowed_updates['secondary_color'] = data['secondary_color']
            
            if org.has_feature('logo_upload') and 'logo_url' in data:
                allowed_updates['logo_url'] = data['logo_url']
            
            # Enterprise features
            if org.has_feature('custom_css') and 'custom_css' in data:
                allowed_updates['custom_css'] = data['custom_css']
            
            if org.has_feature('custom_domain') and 'custom_domain' in data:
                allowed_updates['custom_domain'] = data['custom_domain']
            
            if allowed_updates:
                success = org_service.update_organization(
                    org_id=org.id,
                    updates=allowed_updates,
                    updated_by=user.id
                )
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Organization updated successfully'
                    })
            
            return jsonify({'error': 'No valid updates provided'}), 400
            
        except Exception as e:
            logger.error(f"Organization update error: {e}")
            return jsonify({'error': 'Failed to update organization'}), 500
    
    # ==================== RBAC ENDPOINTS ====================
    
    @bp.route('/permissions/check', methods=['POST'])
    @require_auth
    def check_permissions():
        """Check if current user has specific permissions"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            permissions = data.get('permissions', [])
            if not isinstance(permissions, list):
                return jsonify({'error': 'Permissions must be a list'}), 400
            
            user = g.current_user
            
            results = {}
            for permission in permissions:
                results[permission] = auth_service.check_permission(user.id, permission)
            
            return jsonify({
                'permissions': results,
                'is_admin': user.is_admin
            })
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return jsonify({'error': 'Permission check failed'}), 500
    
    return bp