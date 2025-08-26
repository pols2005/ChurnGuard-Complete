# ChurnGuard Theme Service
# Epic 3 - Enterprise Features & Multi-Tenancy

import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import os
from werkzeug.utils import secure_filename

from .organization_service import OrganizationService

logger = logging.getLogger(__name__)

@dataclass
class OrganizationTheme:
    """Organization theme model"""
    organization_id: str
    theme_config: Dict[str, Any]
    custom_css: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

class ThemeService:
    """Service for managing organization themes and white-label branding"""
    
    def __init__(self, db_connection, org_service: OrganizationService, upload_dir: str = '/tmp/uploads'):
        self.db = db_connection
        self.org_service = org_service
        self.upload_dir = upload_dir
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        # Default theme configuration
        self.default_theme = {
            'id': 'default',
            'name': 'ChurnGuard Default',
            'colors': {
                'primary': '#3B82F6',
                'primaryHover': '#2563EB',
                'secondary': '#6B7280',
                'accent': '#10B981',
                'danger': '#EF4444',
                'warning': '#F59E0B',
                'background': '#F9FAFB',
                'surface': '#FFFFFF',
                'text': '#111827',
                'textSecondary': '#6B7280',
                'border': '#E5E7EB'
            },
            'fonts': {
                'primary': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                'heading': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
            },
            'borderRadius': '0.375rem',
            'spacing': {
                'xs': '0.25rem',
                'sm': '0.5rem',
                'md': '1rem',
                'lg': '1.5rem',
                'xl': '3rem'
            }
        }

    def get_organization_theme(self, org_id: str) -> Dict[str, Any]:
        """Get organization's theme configuration"""
        
        with self.db.cursor() as cursor:
            cursor.execute("""
                SELECT theme_config, custom_css, logo_url, favicon_url, updated_at
                FROM organization_themes 
                WHERE organization_id = %s
            """, (org_id,))
            
            row = cursor.fetchone()
            if not row:
                # Return default theme if no custom theme exists
                return {
                    'theme': self.default_theme,
                    'customCSS': '',
                    'hasCustomTheme': False
                }
            
            theme_config = json.loads(row[0]) if row[0] else self.default_theme
            
            # Merge with default theme to ensure all properties exist
            merged_theme = {
                **self.default_theme,
                **theme_config,
                'colors': {**self.default_theme['colors'], **theme_config.get('colors', {})},
                'fonts': {**self.default_theme['fonts'], **theme_config.get('fonts', {})},
                'spacing': {**self.default_theme['spacing'], **theme_config.get('spacing', {})}
            }
            
            # Add logo and favicon URLs if they exist
            if row[2]:  # logo_url
                merged_theme['logo'] = row[2]
            if row[3]:  # favicon_url
                merged_theme['favicon'] = row[3]
            
            return {
                'theme': merged_theme,
                'customCSS': row[1] or '',
                'hasCustomTheme': True,
                'lastUpdated': row[4].isoformat() if row[4] else None
            }

    def update_organization_theme(
        self,
        org_id: str,
        theme_config: Dict[str, Any],
        custom_css: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> bool:
        """Update organization's theme configuration"""
        
        try:
            # Validate theme configuration
            validated_theme = self._validate_theme_config(theme_config)
            
            with self.db.cursor() as cursor:
                # Check if theme already exists
                cursor.execute(
                    "SELECT id FROM organization_themes WHERE organization_id = %s",
                    (org_id,)
                )
                
                theme_exists = cursor.fetchone() is not None
                
                if theme_exists:
                    # Update existing theme
                    cursor.execute("""
                        UPDATE organization_themes 
                        SET theme_config = %s, custom_css = %s, updated_at = %s
                        WHERE organization_id = %s
                    """, (
                        json.dumps(validated_theme),
                        custom_css,
                        datetime.now(),
                        org_id
                    ))
                else:
                    # Create new theme
                    cursor.execute("""
                        INSERT INTO organization_themes 
                        (organization_id, theme_config, custom_css, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        org_id,
                        json.dumps(validated_theme),
                        custom_css,
                        datetime.now(),
                        datetime.now()
                    ))
                
                self.db.commit()
                
                # Log theme update
                self.org_service._log_audit_event(
                    org_id, 'theme_updated', 'organization_theme', org_id,
                    user_id=updated_by,
                    event_data={
                        'has_custom_css': bool(custom_css and custom_css.strip()),
                        'theme_preset': validated_theme.get('id', 'custom')
                    }
                )
                
                logger.info(f"Updated theme for organization {org_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating theme for organization {org_id}: {e}")
            self.db.rollback()
            return False

    def upload_logo(self, org_id: str, file, uploaded_by: Optional[str] = None) -> Optional[str]:
        """Upload and save organization logo"""
        
        try:
            # Validate file
            if not file or not file.filename:
                return None
            
            # Check file size (max 2MB)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > 2 * 1024 * 1024:  # 2MB
                raise ValueError("File size exceeds 2MB limit")
            
            # Check file type
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                raise ValueError(f"File type {file_ext} not allowed")
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"logo_{org_id}_{timestamp}{file_ext}"
            file_path = os.path.join(self.upload_dir, new_filename)
            
            # Save file
            file.save(file_path)
            
            # Generate URL (assuming static file serving)
            logo_url = f"/uploads/{new_filename}"
            
            # Update database
            with self.db.cursor() as cursor:
                cursor.execute("""
                    UPDATE organization_themes 
                    SET logo_url = %s, updated_at = %s
                    WHERE organization_id = %s
                """, (logo_url, datetime.now(), org_id))
                
                if cursor.rowcount == 0:
                    # Create theme record if it doesn't exist
                    cursor.execute("""
                        INSERT INTO organization_themes 
                        (organization_id, theme_config, logo_url, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        org_id,
                        json.dumps(self.default_theme),
                        logo_url,
                        datetime.now(),
                        datetime.now()
                    ))
                
                self.db.commit()
            
            # Log logo upload
            self.org_service._log_audit_event(
                org_id, 'logo_uploaded', 'organization_theme', org_id,
                user_id=uploaded_by,
                event_data={'filename': filename, 'size': file_size}
            )
            
            logger.info(f"Uploaded logo for organization {org_id}: {new_filename}")
            return logo_url
            
        except Exception as e:
            logger.error(f"Error uploading logo for organization {org_id}: {e}")
            return None

    def reset_theme(self, org_id: str, reset_by: Optional[str] = None) -> bool:
        """Reset organization theme to default"""
        
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    UPDATE organization_themes 
                    SET theme_config = %s, custom_css = NULL, updated_at = %s
                    WHERE organization_id = %s
                """, (
                    json.dumps(self.default_theme),
                    datetime.now(),
                    org_id
                ))
                
                self.db.commit()
                
                # Log theme reset
                self.org_service._log_audit_event(
                    org_id, 'theme_reset', 'organization_theme', org_id,
                    user_id=reset_by
                )
                
                logger.info(f"Reset theme for organization {org_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error resetting theme for organization {org_id}: {e}")
            return False

    def get_theme_presets(self) -> list[Dict[str, Any]]:
        """Get available theme presets"""
        
        return [
            {
                'id': 'default',
                'name': 'ChurnGuard Blue',
                'colors': {
                    'primary': '#3B82F6',
                    'primaryHover': '#2563EB',
                    'accent': '#10B981'
                }
            },
            {
                'id': 'corporate-red',
                'name': 'Corporate Red',
                'colors': {
                    'primary': '#DC2626',
                    'primaryHover': '#B91C1C',
                    'accent': '#059669'
                }
            },
            {
                'id': 'modern-purple',
                'name': 'Modern Purple',
                'colors': {
                    'primary': '#7C3AED',
                    'primaryHover': '#6D28D9',
                    'accent': '#F59E0B'
                }
            },
            {
                'id': 'professional-gray',
                'name': 'Professional Gray',
                'colors': {
                    'primary': '#374151',
                    'primaryHover': '#1F2937',
                    'accent': '#059669'
                }
            },
            {
                'id': 'vibrant-green',
                'name': 'Vibrant Green',
                'colors': {
                    'primary': '#059669',
                    'primaryHover': '#047857',
                    'accent': '#F59E0B'
                }
            }
        ]

    def _validate_theme_config(self, theme_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize theme configuration"""
        
        validated = {
            **self.default_theme,
            **theme_config
        }
        
        # Validate colors (must be valid hex colors)
        if 'colors' in theme_config:
            validated_colors = {}
            for key, value in theme_config['colors'].items():
                if self._is_valid_hex_color(value):
                    validated_colors[key] = value
                else:
                    # Fall back to default color
                    validated_colors[key] = self.default_theme['colors'].get(key, '#000000')
            validated['colors'] = {**self.default_theme['colors'], **validated_colors}
        
        # Validate fonts (basic sanitization)
        if 'fonts' in theme_config:
            validated_fonts = {}
            for key, value in theme_config['fonts'].items():
                if isinstance(value, str) and len(value) < 200:
                    validated_fonts[key] = value
                else:
                    validated_fonts[key] = self.default_theme['fonts'].get(key, 'sans-serif')
            validated['fonts'] = {**self.default_theme['fonts'], **validated_fonts}
        
        return validated

    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color format"""
        if not isinstance(color, str):
            return False
        
        color = color.strip()
        if not color.startswith('#'):
            return False
        
        if len(color) not in [4, 7]:  # #RGB or #RRGGBB
            return False
        
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False

def create_theme_table(db_connection):
    """Create organization themes table"""
    
    with db_connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization_themes (
                id SERIAL PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                theme_config JSONB NOT NULL,
                custom_css TEXT,
                logo_url VARCHAR(500),
                favicon_url VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(organization_id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_organization_themes_org_id 
            ON organization_themes(organization_id)
        """)
        
        db_connection.commit()
        logger.info("Created organization_themes table")