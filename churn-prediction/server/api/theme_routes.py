# ChurnGuard Theme API Routes
# Epic 3 - Enterprise Features & Multi-Tenancy

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging

from ..enterprise.theme_service import ThemeService
from ..enterprise.organization_service import OrganizationService
from ..auth.jwt_auth import verify_jwt_token

logger = logging.getLogger(__name__)

theme_bp = Blueprint('theme', __name__, url_prefix='/api/organizations')

def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_jwt_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'user') or request.user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

@theme_bp.route('/<org_id>/theme', methods=['GET'])
@require_auth
def get_organization_theme(org_id):
    """Get organization's theme configuration"""
    
    try:
        # Verify user has access to organization
        if request.user.get('organization_id') != org_id and request.user.get('role') != 'super_admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Get database connection from app context
        db = current_app.config['database']
        org_service = OrganizationService(db)
        theme_service = ThemeService(db, org_service)
        
        theme_data = theme_service.get_organization_theme(org_id)
        
        return jsonify(theme_data)
        
    except Exception as e:
        logger.error(f"Error getting theme for organization {org_id}: {e}")
        return jsonify({'error': 'Failed to get theme'}), 500

@theme_bp.route('/<org_id>/theme', methods=['PUT'])
@require_auth
@require_admin
def update_organization_theme(org_id):
    """Update organization's theme configuration"""
    
    try:
        # Verify user has access to organization
        if request.user.get('organization_id') != org_id and request.user.get('role') != 'super_admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        theme_config = data.get('theme')
        custom_css = data.get('customCSS')
        
        if not theme_config:
            return jsonify({'error': 'Theme configuration required'}), 400
        
        # Get database connection from app context
        db = current_app.config['database']
        org_service = OrganizationService(db)
        theme_service = ThemeService(db, org_service)
        
        success = theme_service.update_organization_theme(
            org_id=org_id,
            theme_config=theme_config,
            custom_css=custom_css,
            updated_by=request.user.get('user_id')
        )
        
        if success:
            # Return updated theme
            updated_theme = theme_service.get_organization_theme(org_id)
            return jsonify({
                'success': True,
                'message': 'Theme updated successfully',
                'theme': updated_theme
            })
        else:
            return jsonify({'error': 'Failed to update theme'}), 500
            
    except Exception as e:
        logger.error(f"Error updating theme for organization {org_id}: {e}")
        return jsonify({'error': 'Failed to update theme'}), 500

@theme_bp.route('/<org_id>/theme/reset', methods=['POST'])
@require_auth
@require_admin
def reset_organization_theme(org_id):
    """Reset organization theme to default"""
    
    try:
        # Verify user has access to organization
        if request.user.get('organization_id') != org_id and request.user.get('role') != 'super_admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Get database connection from app context
        db = current_app.config['database']
        org_service = OrganizationService(db)
        theme_service = ThemeService(db, org_service)
        
        success = theme_service.reset_theme(
            org_id=org_id,
            reset_by=request.user.get('user_id')
        )
        
        if success:
            # Return default theme
            default_theme = theme_service.get_organization_theme(org_id)
            return jsonify({
                'success': True,
                'message': 'Theme reset to default',
                'theme': default_theme
            })
        else:
            return jsonify({'error': 'Failed to reset theme'}), 500
            
    except Exception as e:
        logger.error(f"Error resetting theme for organization {org_id}: {e}")
        return jsonify({'error': 'Failed to reset theme'}), 500

@theme_bp.route('/upload/logo', methods=['POST'])
@require_auth
@require_admin
def upload_organization_logo():
    """Upload organization logo"""
    
    try:
        org_id = request.user.get('organization_id')
        if not org_id:
            return jsonify({'error': 'Organization ID required'}), 400
        
        if 'logo' not in request.files:
            return jsonify({'error': 'Logo file required'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get database connection from app context
        db = current_app.config['database']
        org_service = OrganizationService(db)
        theme_service = ThemeService(db, org_service)
        
        logo_url = theme_service.upload_logo(
            org_id=org_id,
            file=file,
            uploaded_by=request.user.get('user_id')
        )
        
        if logo_url:
            return jsonify({
                'success': True,
                'message': 'Logo uploaded successfully',
                'logoUrl': logo_url
            })
        else:
            return jsonify({'error': 'Failed to upload logo'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading logo: {e}")
        return jsonify({'error': 'Failed to upload logo'}), 500

@theme_bp.route('/theme/presets', methods=['GET'])
@require_auth
def get_theme_presets():
    """Get available theme presets"""
    
    try:
        # Get database connection from app context
        db = current_app.config['database']
        org_service = OrganizationService(db)
        theme_service = ThemeService(db, org_service)
        
        presets = theme_service.get_theme_presets()
        
        return jsonify({
            'success': True,
            'presets': presets
        })
        
    except Exception as e:
        logger.error(f"Error getting theme presets: {e}")
        return jsonify({'error': 'Failed to get theme presets'}), 500

# Health check endpoint
@theme_bp.route('/theme/health', methods=['GET'])
def theme_health_check():
    """Theme service health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'theme',
        'timestamp': str(datetime.now())
    })