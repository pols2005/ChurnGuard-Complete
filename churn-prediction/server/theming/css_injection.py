# ChurnGuard Custom CSS Injection System
# Epic 3 - White-Label Theming Features

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import hashlib
import cssutils
from cssutils import log as cssutils_log
import bleach
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

# Suppress CSS utils verbose logging
cssutils_log.setLevel(logging.ERROR)

class CSSScope(Enum):
    GLOBAL = "global"
    DASHBOARD = "dashboard"
    REPORTS = "reports"
    LOGIN = "login"
    ANALYTICS = "analytics"
    COMPONENT = "component"

class CSSPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValidationLevel(Enum):
    STRICT = "strict"      # Block potentially dangerous CSS
    MODERATE = "moderate"  # Warn but allow most CSS
    PERMISSIVE = "permissive"  # Allow all valid CSS

@dataclass
class CSSRule:
    """Individual CSS rule with metadata"""
    rule_id: str
    organization_id: str
    selector: str
    declarations: Dict[str, str]
    scope: CSSScope
    priority: CSSPriority
    created_at: datetime
    created_by: str
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CSSTheme:
    """Complete CSS theme configuration"""
    theme_id: str
    organization_id: str
    theme_name: str
    description: str
    
    # CSS rules organized by scope
    global_css: str = ""
    dashboard_css: str = ""
    reports_css: str = ""
    login_css: str = ""
    analytics_css: str = ""
    component_overrides: Dict[str, str] = field(default_factory=dict)
    
    # Theme metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    version: str = "1.0"
    active: bool = True
    
    # Validation results
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CSSValidationResult:
    """Result of CSS validation and sanitization"""
    is_valid: bool
    sanitized_css: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    blocked_properties: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)

class CSSInjectionEngine:
    """
    Advanced CSS injection and theming system for white-label customization
    
    Features:
    - Safe CSS validation and sanitization
    - Scoped CSS injection (global, dashboard, reports, etc.)
    - CSS priority management and conflict resolution
    - Theme versioning and rollback capabilities
    - Real-time CSS preview and testing
    - Security validation against XSS and malicious CSS
    - CSS minification and optimization
    - Integration with component-specific styling
    - Multi-tenant CSS isolation
    - Custom CSS editor with syntax highlighting
    """
    
    def __init__(self):
        # CSS security and validation configuration
        self.allowed_properties = self._load_allowed_properties()
        self.blocked_properties = self._load_blocked_properties()
        self.dangerous_patterns = self._load_dangerous_patterns()
        
        # CSS storage
        self.themes: Dict[str, CSSTheme] = {}
        self.active_themes: Dict[str, str] = {}  # org_id -> theme_id
        
        # CSS generation cache
        self.css_cache: Dict[str, str] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Default theme templates
        self.default_templates = self._load_default_templates()
        
    def create_theme(self, organization_id: str, theme_name: str, 
                    description: str, created_by: str) -> str:
        """
        Create a new CSS theme for an organization
        
        Args:
            organization_id: Organization identifier
            theme_name: Human-readable theme name
            description: Theme description
            created_by: Creator identifier
            
        Returns:
            Theme ID
        """
        theme_id = f"theme_{organization_id}_{int(datetime.now().timestamp())}"
        
        theme = CSSTheme(
            theme_id=theme_id,
            organization_id=organization_id,
            theme_name=theme_name,
            description=description,
            created_by=created_by
        )
        
        # Initialize with default template
        default_template = self.default_templates.get('modern_corporate', {})
        theme.global_css = default_template.get('global_css', '')
        theme.dashboard_css = default_template.get('dashboard_css', '')
        theme.reports_css = default_template.get('reports_css', '')
        
        self.themes[theme_id] = theme
        
        logger.info(f"Created CSS theme {theme_id} for organization {organization_id}")
        return theme_id
    
    def update_css_scope(self, theme_id: str, scope: CSSScope, 
                        css_content: str, validation_level: ValidationLevel = ValidationLevel.MODERATE) -> CSSValidationResult:
        """
        Update CSS for a specific scope within a theme
        
        Args:
            theme_id: Theme identifier
            scope: CSS scope to update
            css_content: CSS content to inject
            validation_level: Level of CSS validation
            
        Returns:
            CSS validation result
        """
        if theme_id not in self.themes:
            raise ValueError(f"Theme {theme_id} not found")
        
        theme = self.themes[theme_id]
        
        # Validate and sanitize CSS
        validation_result = self.validate_css(css_content, validation_level)
        
        if validation_result.is_valid:
            # Apply scoped CSS
            sanitized_css = self._apply_css_scoping(validation_result.sanitized_css, scope)
            
            # Update theme
            if scope == CSSScope.GLOBAL:
                theme.global_css = sanitized_css
            elif scope == CSSScope.DASHBOARD:
                theme.dashboard_css = sanitized_css
            elif scope == CSSScope.REPORTS:
                theme.reports_css = sanitized_css
            elif scope == CSSScope.LOGIN:
                theme.login_css = sanitized_css
            elif scope == CSSScope.ANALYTICS:
                theme.analytics_css = sanitized_css
            
            # Update validation results
            theme.validation_results[scope.value] = {
                'validated_at': datetime.now().isoformat(),
                'warnings': validation_result.warnings,
                'validation_level': validation_level.value
            }
            
            # Clear cache for this organization
            self._clear_organization_cache(theme.organization_id)
            
            logger.info(f"Updated {scope.value} CSS for theme {theme_id}")
        
        return validation_result
    
    def validate_css(self, css_content: str, validation_level: ValidationLevel = ValidationLevel.MODERATE) -> CSSValidationResult:
        """
        Validate and sanitize CSS content
        
        Args:
            css_content: Raw CSS content
            validation_level: Validation strictness level
            
        Returns:
            Validation result with sanitized CSS
        """
        warnings = []
        errors = []
        blocked_properties = []
        security_issues = []
        
        try:
            # Parse CSS using cssutils
            sheet = cssutils.parseString(css_content)
            
            # Security validation
            security_result = self._check_css_security(css_content)
            security_issues.extend(security_result['issues'])
            
            if validation_level == ValidationLevel.STRICT and security_issues:
                return CSSValidationResult(
                    is_valid=False,
                    sanitized_css="",
                    security_issues=security_issues,
                    errors=["CSS blocked due to security concerns"]
                )
            
            # Sanitize CSS rules
            sanitized_rules = []
            
            for rule in sheet:
                if rule.type == rule.STYLE_RULE:
                    sanitized_rule = self._sanitize_css_rule(rule, validation_level)
                    if sanitized_rule['blocked_properties']:
                        blocked_properties.extend(sanitized_rule['blocked_properties'])
                    if sanitized_rule['warnings']:
                        warnings.extend(sanitized_rule['warnings'])
                    if sanitized_rule['css']:
                        sanitized_rules.append(sanitized_rule['css'])
                
                elif rule.type == rule.MEDIA_RULE:
                    # Handle media queries
                    media_css = self._sanitize_media_rule(rule, validation_level)
                    if media_css:
                        sanitized_rules.append(media_css)
                        
                elif rule.type == rule.IMPORT_RULE:
                    # Block @import rules for security
                    if validation_level in [ValidationLevel.STRICT, ValidationLevel.MODERATE]:
                        warnings.append("@import rules are not allowed")
                    else:
                        sanitized_rules.append(rule.cssText)
            
            sanitized_css = '\n'.join(sanitized_rules)
            
            # Final minification
            if sanitized_css:
                sanitized_css = self._minify_css(sanitized_css)
            
            is_valid = len(errors) == 0 and (
                validation_level == ValidationLevel.PERMISSIVE or 
                len(security_issues) == 0
            )
            
            return CSSValidationResult(
                is_valid=is_valid,
                sanitized_css=sanitized_css,
                warnings=warnings,
                errors=errors,
                blocked_properties=blocked_properties,
                security_issues=security_issues
            )
            
        except Exception as e:
            logger.error(f"CSS validation error: {e}")
            return CSSValidationResult(
                is_valid=False,
                sanitized_css="",
                errors=[f"CSS parsing error: {str(e)}"]
            )
    
    def generate_organization_css(self, organization_id: str, scope: Optional[CSSScope] = None) -> str:
        """
        Generate complete CSS for an organization
        
        Args:
            organization_id: Organization identifier
            scope: Optional scope filter
            
        Returns:
            Generated CSS content
        """
        # Check cache first
        cache_key = f"{organization_id}:{scope.value if scope else 'all'}"
        if cache_key in self.css_cache:
            cache_time = self.cache_timestamps.get(cache_key, datetime.min)
            if (datetime.now() - cache_time).seconds < 300:  # 5 minute cache
                return self.css_cache[cache_key]
        
        # Get active theme for organization
        active_theme_id = self.active_themes.get(organization_id)
        if not active_theme_id or active_theme_id not in self.themes:
            return ""  # No active theme
        
        theme = self.themes[active_theme_id]
        css_parts = []
        
        # Add scope-specific CSS
        if not scope or scope == CSSScope.GLOBAL:
            if theme.global_css:
                css_parts.append(f"/* Global CSS */\n{theme.global_css}")
        
        if not scope or scope == CSSScope.DASHBOARD:
            if theme.dashboard_css:
                css_parts.append(f"/* Dashboard CSS */\n{theme.dashboard_css}")
        
        if not scope or scope == CSSScope.REPORTS:
            if theme.reports_css:
                css_parts.append(f"/* Reports CSS */\n{theme.reports_css}")
        
        if not scope or scope == CSSScope.LOGIN:
            if theme.login_css:
                css_parts.append(f"/* Login CSS */\n{theme.login_css}")
        
        if not scope or scope == CSSScope.ANALYTICS:
            if theme.analytics_css:
                css_parts.append(f"/* Analytics CSS */\n{theme.analytics_css}")
        
        # Add component overrides
        if not scope or scope == CSSScope.COMPONENT:
            for component, css in theme.component_overrides.items():
                if css:
                    css_parts.append(f"/* {component} Component CSS */\n{css}")
        
        # Combine and optimize
        combined_css = '\n\n'.join(css_parts)
        
        if combined_css:
            # Add organization-specific CSS scoping
            combined_css = self._add_organization_scoping(combined_css, organization_id)
            
            # Final optimization
            combined_css = self._optimize_css(combined_css)
        
        # Cache the result
        self.css_cache[cache_key] = combined_css
        self.cache_timestamps[cache_key] = datetime.now()
        
        return combined_css
    
    def activate_theme(self, organization_id: str, theme_id: str) -> bool:
        """
        Activate a theme for an organization
        
        Args:
            organization_id: Organization identifier
            theme_id: Theme to activate
            
        Returns:
            Success status
        """
        if theme_id not in self.themes:
            logger.error(f"Theme {theme_id} not found")
            return False
        
        theme = self.themes[theme_id]
        if theme.organization_id != organization_id:
            logger.error(f"Theme {theme_id} does not belong to organization {organization_id}")
            return False
        
        # Deactivate current theme
        if organization_id in self.active_themes:
            old_theme_id = self.active_themes[organization_id]
            if old_theme_id in self.themes:
                self.themes[old_theme_id].active = False
        
        # Activate new theme
        self.active_themes[organization_id] = theme_id
        theme.active = True
        
        # Clear cache
        self._clear_organization_cache(organization_id)
        
        logger.info(f"Activated theme {theme_id} for organization {organization_id}")
        return True
    
    def get_css_for_injection(self, organization_id: str, page_context: str = "") -> Dict[str, str]:
        """
        Get CSS ready for injection into HTML pages
        
        Args:
            organization_id: Organization identifier
            page_context: Page context (dashboard, reports, etc.)
            
        Returns:
            Dictionary of CSS content by injection point
        """
        # Determine scope based on page context
        scope_mapping = {
            'dashboard': CSSScope.DASHBOARD,
            'reports': CSSScope.REPORTS,  
            'login': CSSScope.LOGIN,
            'analytics': CSSScope.ANALYTICS
        }
        
        scope = scope_mapping.get(page_context.lower())
        
        # Get CSS content
        css_content = self.generate_organization_css(organization_id, scope)
        
        if not css_content:
            return {}
        
        # Add CSS integrity hash for security
        css_hash = hashlib.sha256(css_content.encode()).hexdigest()[:16]
        
        return {
            'inline_css': css_content,
            'css_hash': css_hash,
            'injection_points': {
                'head': f'<style data-theme-hash="{css_hash}">{css_content}</style>',
                'body_start': f'<!-- ChurnGuard Theme: {css_hash} -->',
                'body_end': f'<!-- End ChurnGuard Theme -->'
            },
            'metadata': {
                'organization_id': organization_id,
                'page_context': page_context,
                'generated_at': datetime.now().isoformat(),
                'theme_id': self.active_themes.get(organization_id, '')
            }
        }
    
    def _check_css_security(self, css_content: str) -> Dict[str, Any]:
        """Check CSS for potential security issues"""
        issues = []
        
        # Check for dangerous patterns
        for pattern_name, pattern in self.dangerous_patterns.items():
            if re.search(pattern, css_content, re.IGNORECASE):
                issues.append(f"Potentially dangerous pattern detected: {pattern_name}")
        
        # Check for external resource references
        external_refs = re.findall(r'url\s*\(\s*["\']?(https?://[^"\')\s]+)', css_content, re.IGNORECASE)
        if external_refs:
            issues.append(f"External resource references found: {len(external_refs)} URLs")
        
        # Check for JavaScript execution attempts
        js_patterns = [
            r'javascript\s*:',
            r'expression\s*\(',
            r'@import.*javascript',
            r'vbscript\s*:',
            r'data\s*:\s*text/html'
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, css_content, re.IGNORECASE):
                issues.append("Potential JavaScript execution attempt detected")
                break
        
        return {
            'issues': issues,
            'risk_level': 'high' if issues else 'low'
        }
    
    def _sanitize_css_rule(self, rule, validation_level: ValidationLevel) -> Dict[str, Any]:
        """Sanitize individual CSS rule"""
        warnings = []
        blocked_properties = []
        
        try:
            selector = rule.selectorText
            declarations = {}
            
            for prop in rule.style:
                prop_name = prop.name.lower()
                prop_value = prop.value
                
                # Check against blocked properties
                if prop_name in self.blocked_properties:
                    blocked_properties.append(prop_name)
                    if validation_level == ValidationLevel.STRICT:
                        continue
                    else:
                        warnings.append(f"Property '{prop_name}' is potentially unsafe")
                
                # Sanitize property value
                sanitized_value = self._sanitize_css_value(prop_value)
                if sanitized_value != prop_value:
                    warnings.append(f"Property value sanitized: {prop_name}")
                
                declarations[prop_name] = sanitized_value
            
            # Rebuild CSS rule
            if declarations:
                css_text = f"{selector} {{\n"
                for prop, value in declarations.items():
                    css_text += f"  {prop}: {value};\n"
                css_text += "}"
            else:
                css_text = ""
            
            return {
                'css': css_text,
                'warnings': warnings,
                'blocked_properties': blocked_properties
            }
            
        except Exception as e:
            logger.warning(f"Error sanitizing CSS rule: {e}")
            return {
                'css': "",
                'warnings': [f"Rule sanitization error: {str(e)}"],
                'blocked_properties': []
            }
    
    def _load_allowed_properties(self) -> Set[str]:
        """Load list of allowed CSS properties"""
        return {
            # Layout
            'display', 'position', 'top', 'right', 'bottom', 'left', 'z-index',
            'float', 'clear', 'overflow', 'overflow-x', 'overflow-y',
            
            # Box model  
            'width', 'height', 'min-width', 'max-width', 'min-height', 'max-height',
            'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
            'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
            'border', 'border-width', 'border-style', 'border-color',
            'border-radius', 'box-sizing',
            
            # Typography
            'font', 'font-family', 'font-size', 'font-weight', 'font-style',
            'line-height', 'text-align', 'text-decoration', 'text-transform',
            'letter-spacing', 'word-spacing',
            
            # Colors and backgrounds
            'color', 'background', 'background-color', 'background-image',
            'background-repeat', 'background-position', 'background-size',
            'opacity',
            
            # Flexbox
            'flex', 'flex-direction', 'flex-wrap', 'justify-content', 'align-items',
            'align-content', 'flex-grow', 'flex-shrink', 'flex-basis',
            
            # Grid
            'grid', 'grid-template-columns', 'grid-template-rows', 'grid-gap',
            'grid-column', 'grid-row',
            
            # Transitions and animations
            'transition', 'transition-property', 'transition-duration',
            'transition-timing-function', 'transition-delay',
            'transform', 'transform-origin'
        }
    
    def _load_blocked_properties(self) -> Set[str]:
        """Load list of blocked/dangerous CSS properties"""
        return {
            'behavior',  # IE-specific, can execute scripts
            'binding',   # Mozilla-specific, can execute scripts  
            'expression',  # IE expression() function
            'filter',    # Can be used for attacks in older IE
            'javascript',  # Direct JavaScript
            'vbscript',   # VBScript execution
            'mozbinding'  # Mozilla binding
        }
    
    def _load_dangerous_patterns(self) -> Dict[str, str]:
        """Load patterns that indicate potentially dangerous CSS"""
        return {
            'javascript_execution': r'javascript\s*:',
            'vbscript_execution': r'vbscript\s*:',
            'data_uri_html': r'data\s*:\s*text/html',
            'css_expression': r'expression\s*\(',
            'css_behavior': r'behavior\s*:',
            'import_javascript': r'@import.*javascript',
            'unicode_escape': r'\\[0-9a-f]{1,6}',  # Excessive unicode escaping
        }

# Global CSS injection engine
css_engine = CSSInjectionEngine()

def get_css_engine() -> CSSInjectionEngine:
    """Get the global CSS injection engine"""
    return css_engine

# Convenience functions
def create_organization_theme(organization_id: str, theme_name: str, created_by: str) -> str:
    """Create new CSS theme for organization"""
    engine = get_css_engine()
    return engine.create_theme(organization_id, theme_name, f"Custom theme for {organization_id}", created_by)

def inject_organization_css(organization_id: str, page_context: str = "") -> Dict[str, str]:
    """Get CSS ready for injection into pages"""
    engine = get_css_engine()
    return engine.get_css_for_injection(organization_id, page_context)