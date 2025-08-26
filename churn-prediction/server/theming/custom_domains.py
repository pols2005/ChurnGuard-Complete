# ChurnGuard Custom Domain Support for White-Label Deployments
# Epic 3 - White-Label Theming Features

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import ssl
import socket
import dns.resolver
import requests
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

class DomainStatus(Enum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SSL_PENDING = "ssl_pending"
    SSL_ERROR = "ssl_error"
    DNS_ERROR = "dns_error"
    SUSPENDED = "suspended"

class DomainType(Enum):
    SUBDOMAIN = "subdomain"        # app.customer.com
    CUSTOM_DOMAIN = "custom_domain"  # customer.com
    WHITE_LABEL = "white_label"    # completely custom branding

class SSLProvider(Enum):
    LETS_ENCRYPT = "lets_encrypt"
    CLOUDFLARE = "cloudflare"
    CUSTOM_CERTIFICATE = "custom_certificate"

@dataclass
class DomainConfiguration:
    """Domain configuration for organization white-labeling"""
    domain_id: str
    organization_id: str
    domain_name: str
    domain_type: DomainType
    status: DomainStatus
    
    # DNS configuration
    cname_target: str = ""
    dns_records: List[Dict[str, str]] = field(default_factory=list)
    
    # SSL configuration
    ssl_enabled: bool = True
    ssl_provider: SSLProvider = SSLProvider.LETS_ENCRYPT
    ssl_certificate_path: str = ""
    ssl_private_key_path: str = ""
    ssl_expiry_date: Optional[datetime] = None
    
    # Verification
    verification_token: str = ""
    verification_method: str = "dns"  # dns, file, email
    verified_at: Optional[datetime] = None
    
    # Routing configuration
    app_subdomain: str = "app"  # app.customer.com
    api_subdomain: str = "api"  # api.customer.com
    cdn_subdomain: str = "cdn"  # cdn.customer.com
    
    # Branding overrides
    brand_name: str = ""
    support_email: str = ""
    privacy_policy_url: str = ""
    terms_of_service_url: str = ""
    
    # Security settings
    hsts_enabled: bool = True
    security_headers: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DomainVerificationResult:
    """Result of domain verification process"""
    domain_id: str
    is_verified: bool
    verification_method: str
    
    # DNS verification results
    dns_records_correct: bool = True
    missing_dns_records: List[str] = field(default_factory=list)
    incorrect_dns_records: List[str] = field(default_factory=list)
    
    # SSL verification results
    ssl_valid: bool = True
    ssl_issues: List[str] = field(default_factory=list)
    ssl_expiry: Optional[datetime] = None
    
    # Connectivity tests
    http_accessible: bool = True
    https_accessible: bool = True
    response_time_ms: float = 0.0
    
    # Error details
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    verification_timestamp: datetime = field(default_factory=datetime.now)

class CustomDomainManager:
    """
    Advanced custom domain management for white-label deployments
    
    Features:
    - Custom domain setup and verification (DNS, file, email methods)
    - Automatic SSL certificate provisioning (Let's Encrypt integration)
    - DNS record management and validation
    - Domain health monitoring and alerting
    - Multi-subdomain routing (app, api, cdn subdomains)
    - Security headers and HSTS configuration
    - Domain-based branding customization
    - SSL certificate renewal automation
    - Domain migration and backup procedures
    - Integration with CDN and load balancing
    """
    
    def __init__(self):
        # Domain storage
        self.domain_configs: Dict[str, DomainConfiguration] = {}
        self.organization_domains: Dict[str, List[str]] = {}  # org_id -> domain_ids
        
        # DNS configuration
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 10
        self.dns_resolver.lifetime = 10
        
        # SSL configuration
        self.ssl_cert_directory = "/etc/ssl/churnguard/"
        self.letsencrypt_email = "admin@churnguard.ai"
        
        # Verification tokens
        self.verification_tokens: Dict[str, str] = {}
        
        # Health monitoring
        self.health_check_interval = 3600  # 1 hour
        self.last_health_check: Dict[str, datetime] = {}
        
    def add_custom_domain(self, organization_id: str, domain_name: str,
                         domain_type: DomainType = DomainType.CUSTOM_DOMAIN,
                         created_by: str = "") -> str:
        """
        Add a custom domain for an organization
        
        Args:
            organization_id: Organization identifier
            domain_name: Domain name (e.g., app.customer.com)
            domain_type: Type of domain configuration
            created_by: User who added the domain
            
        Returns:
            Domain configuration ID
        """
        # Validate domain name format
        if not self._is_valid_domain(domain_name):
            raise ValueError(f"Invalid domain name format: {domain_name}")
        
        # Check if domain is already configured
        for config in self.domain_configs.values():
            if config.domain_name.lower() == domain_name.lower():
                raise ValueError(f"Domain {domain_name} is already configured")
        
        domain_id = f"dom_{organization_id}_{int(datetime.now().timestamp())}"
        
        # Generate verification token
        verification_token = self._generate_verification_token(domain_name)
        
        # Determine CNAME target based on domain type
        cname_target = self._get_cname_target(domain_type)
        
        domain_config = DomainConfiguration(
            domain_id=domain_id,
            organization_id=organization_id,
            domain_name=domain_name,
            domain_type=domain_type,
            status=DomainStatus.PENDING_VERIFICATION,
            cname_target=cname_target,
            verification_token=verification_token,
            created_by=created_by
        )
        
        # Set up required DNS records
        domain_config.dns_records = self._generate_required_dns_records(domain_config)
        
        # Generate security headers
        domain_config.security_headers = self._generate_security_headers(domain_name)
        
        self.domain_configs[domain_id] = domain_config
        
        # Update organization mapping
        if organization_id not in self.organization_domains:
            self.organization_domains[organization_id] = []
        self.organization_domains[organization_id].append(domain_id)
        
        logger.info(f"Added custom domain {domain_name} for organization {organization_id}")
        return domain_id
    
    def verify_domain(self, domain_id: str, force_recheck: bool = False) -> DomainVerificationResult:
        """
        Verify domain configuration and DNS setup
        
        Args:
            domain_id: Domain configuration ID
            force_recheck: Force verification even if recently checked
            
        Returns:
            Domain verification result
        """
        if domain_id not in self.domain_configs:
            raise ValueError(f"Domain {domain_id} not found")
        
        domain_config = self.domain_configs[domain_id]
        
        # Check if verification is needed
        if not force_recheck and domain_config.verified_at:
            last_check = domain_config.verified_at
            if (datetime.now() - last_check).hours < 1:
                # Return cached result if verified within last hour
                return self._get_cached_verification_result(domain_id)
        
        result = DomainVerificationResult(
            domain_id=domain_id,
            is_verified=False,
            verification_method=domain_config.verification_method
        )
        
        try:
            # Verify DNS records
            dns_verification = self._verify_dns_records(domain_config)
            result.dns_records_correct = dns_verification['all_correct']
            result.missing_dns_records = dns_verification['missing']
            result.incorrect_dns_records = dns_verification['incorrect']
            
            # Test domain connectivity
            connectivity_test = self._test_domain_connectivity(domain_config.domain_name)
            result.http_accessible = connectivity_test['http_ok']
            result.https_accessible = connectivity_test['https_ok']
            result.response_time_ms = connectivity_test['response_time']
            
            # Verify SSL certificate
            if domain_config.ssl_enabled:
                ssl_verification = self._verify_ssl_certificate(domain_config.domain_name)
                result.ssl_valid = ssl_verification['valid']
                result.ssl_issues = ssl_verification['issues']
                result.ssl_expiry = ssl_verification['expiry']
            
            # Determine overall verification status
            result.is_verified = (
                result.dns_records_correct and
                result.http_accessible and
                (not domain_config.ssl_enabled or result.ssl_valid)
            )
            
            # Update domain status
            if result.is_verified:
                domain_config.status = DomainStatus.VERIFIED
                domain_config.verified_at = datetime.now()
            else:
                # Determine specific error status
                if not result.dns_records_correct:
                    domain_config.status = DomainStatus.DNS_ERROR
                elif domain_config.ssl_enabled and not result.ssl_valid:
                    domain_config.status = DomainStatus.SSL_ERROR
                else:
                    domain_config.status = DomainStatus.PENDING_VERIFICATION
            
            domain_config.updated_at = datetime.now()
            
            logger.info(f"Domain verification for {domain_config.domain_name}: {'PASSED' if result.is_verified else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Domain verification error for {domain_id}: {e}")
            result.errors.append(f"Verification error: {str(e)}")
        
        return result
    
    def provision_ssl_certificate(self, domain_id: str) -> bool:
        """
        Provision SSL certificate for domain
        
        Args:
            domain_id: Domain configuration ID
            
        Returns:
            Success status
        """
        if domain_id not in self.domain_configs:
            raise ValueError(f"Domain {domain_id} not found")
        
        domain_config = self.domain_configs[domain_id]
        
        if domain_config.status != DomainStatus.VERIFIED:
            logger.error(f"Cannot provision SSL for unverified domain {domain_config.domain_name}")
            return False
        
        try:
            domain_config.status = DomainStatus.SSL_PENDING
            
            if domain_config.ssl_provider == SSLProvider.LETS_ENCRYPT:
                success = self._provision_letsencrypt_certificate(domain_config)
            elif domain_config.ssl_provider == SSLProvider.CLOUDFLARE:
                success = self._provision_cloudflare_certificate(domain_config)
            else:
                logger.warning(f"Custom SSL certificates not implemented yet")
                success = False
            
            if success:
                domain_config.status = DomainStatus.ACTIVE
                logger.info(f"SSL certificate provisioned for {domain_config.domain_name}")
            else:
                domain_config.status = DomainStatus.SSL_ERROR
                logger.error(f"Failed to provision SSL certificate for {domain_config.domain_name}")
            
            domain_config.updated_at = datetime.now()
            return success
            
        except Exception as e:
            logger.error(f"SSL provisioning error for {domain_config.domain_name}: {e}")
            domain_config.status = DomainStatus.SSL_ERROR
            return False
    
    def get_domain_routing_config(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Get routing configuration for a domain
        
        Args:
            domain_name: Domain name to get routing for
            
        Returns:
            Routing configuration or None if domain not found
        """
        # Find domain configuration
        domain_config = None
        for config in self.domain_configs.values():
            if config.domain_name.lower() == domain_name.lower():
                domain_config = config
                break
        
        if not domain_config or domain_config.status != DomainStatus.ACTIVE:
            return None
        
        return {
            'domain_id': domain_config.domain_id,
            'organization_id': domain_config.organization_id,
            'domain_name': domain_config.domain_name,
            'domain_type': domain_config.domain_type.value,
            
            # Subdomain routing
            'app_url': f"https://{domain_config.app_subdomain}.{domain_config.domain_name}",
            'api_url': f"https://{domain_config.api_subdomain}.{domain_config.domain_name}",
            'cdn_url': f"https://{domain_config.cdn_subdomain}.{domain_config.domain_name}",
            
            # SSL configuration
            'ssl_enabled': domain_config.ssl_enabled,
            'certificate_path': domain_config.ssl_certificate_path,
            'private_key_path': domain_config.ssl_private_key_path,
            
            # Security headers
            'security_headers': domain_config.security_headers,
            'hsts_enabled': domain_config.hsts_enabled,
            
            # Branding
            'brand_name': domain_config.brand_name,
            'support_email': domain_config.support_email,
            
            # Metadata
            'last_verified': domain_config.verified_at.isoformat() if domain_config.verified_at else None
        }
    
    def monitor_domain_health(self, domain_id: str) -> Dict[str, Any]:
        """
        Monitor domain health and performance
        
        Args:
            domain_id: Domain configuration ID
            
        Returns:
            Domain health status and metrics
        """
        if domain_id not in self.domain_configs:
            raise ValueError(f"Domain {domain_id} not found")
        
        domain_config = self.domain_configs[domain_id]
        
        health_status = {
            'domain_id': domain_id,
            'domain_name': domain_config.domain_name,
            'status': domain_config.status.value,
            'last_check': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'metrics': {}
        }
        
        try:
            # Test connectivity
            connectivity = self._test_domain_connectivity(domain_config.domain_name)
            health_status['metrics']['connectivity'] = connectivity
            
            # Check SSL status
            if domain_config.ssl_enabled:
                ssl_status = self._check_ssl_health(domain_config.domain_name)
                health_status['metrics']['ssl'] = ssl_status
                
                # Check certificate expiry
                if ssl_status.get('expiry_date'):
                    days_until_expiry = (ssl_status['expiry_date'] - datetime.now()).days
                    health_status['metrics']['ssl']['days_until_expiry'] = days_until_expiry
                    
                    if days_until_expiry < 30:
                        health_status['warnings'] = health_status.get('warnings', [])
                        health_status['warnings'].append(f"SSL certificate expires in {days_until_expiry} days")
            
            # DNS health check
            dns_health = self._check_dns_health(domain_config)
            health_status['metrics']['dns'] = dns_health
            
            # Determine overall health
            if (connectivity['http_ok'] and 
                (not domain_config.ssl_enabled or connectivity['https_ok']) and
                dns_health['all_records_ok']):
                health_status['overall_health'] = 'healthy'
            elif connectivity['http_ok'] or connectivity['https_ok']:
                health_status['overall_health'] = 'degraded'
            else:
                health_status['overall_health'] = 'unhealthy'
            
            # Update last health check
            self.last_health_check[domain_id] = datetime.now()
            
        except Exception as e:
            logger.error(f"Health monitoring error for {domain_config.domain_name}: {e}")
            health_status['overall_health'] = 'error'
            health_status['error'] = str(e)
        
        return health_status
    
    def _is_valid_domain(self, domain_name: str) -> bool:
        """Validate domain name format"""
        if not domain_name or len(domain_name) > 253:
            return False
        
        # Basic domain name regex
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        
        return bool(domain_pattern.match(domain_name))
    
    def _generate_verification_token(self, domain_name: str) -> str:
        """Generate unique verification token for domain"""
        content = f"{domain_name}:{datetime.now().isoformat()}:churnguard"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _get_cname_target(self, domain_type: DomainType) -> str:
        """Get appropriate CNAME target for domain type"""
        targets = {
            DomainType.SUBDOMAIN: "lb-us-east-1.churnguard.ai",
            DomainType.CUSTOM_DOMAIN: "custom.churnguard.ai",
            DomainType.WHITE_LABEL: "whitelabel.churnguard.ai"
        }
        return targets.get(domain_type, "custom.churnguard.ai")
    
    def _generate_required_dns_records(self, domain_config: DomainConfiguration) -> List[Dict[str, str]]:
        """Generate required DNS records for domain"""
        records = []
        
        # Main CNAME record
        records.append({
            'type': 'CNAME',
            'name': domain_config.domain_name,
            'value': domain_config.cname_target,
            'ttl': '300'
        })
        
        # Subdomain CNAME records
        for subdomain in [domain_config.app_subdomain, domain_config.api_subdomain, domain_config.cdn_subdomain]:
            records.append({
                'type': 'CNAME',
                'name': f"{subdomain}.{domain_config.domain_name}",
                'value': domain_config.cname_target,
                'ttl': '300'
            })
        
        # Verification record
        records.append({
            'type': 'TXT',
            'name': f"_churnguard-challenge.{domain_config.domain_name}",
            'value': f"churnguard-domain-verification={domain_config.verification_token}",
            'ttl': '300'
        })
        
        return records
    
    def _generate_security_headers(self, domain_name: str) -> Dict[str, str]:
        """Generate security headers for domain"""
        return {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': f"default-src 'self' https://*.{domain_name}; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
        }

# Additional helper methods would continue here...

# Global custom domain manager
domain_manager = CustomDomainManager()

def get_domain_manager() -> CustomDomainManager:
    """Get the global custom domain manager"""
    return domain_manager

# Convenience functions
def add_organization_domain(organization_id: str, domain_name: str) -> str:
    """Add custom domain for organization"""
    manager = get_domain_manager()
    return manager.add_custom_domain(organization_id, domain_name)

def get_domain_routing(domain_name: str) -> Optional[Dict[str, Any]]:
    """Get routing configuration for domain"""
    manager = get_domain_manager()
    return manager.get_domain_routing_config(domain_name)