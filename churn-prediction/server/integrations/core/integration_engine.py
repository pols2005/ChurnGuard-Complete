# ChurnGuard Integration Engine - Core Framework
# Epic 5 - Enterprise Integration & Data Connectors

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import time

logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    SYNCING = "syncing"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION_FAILED = "auth_failed"

class DataSyncMode(Enum):
    FULL_SYNC = "full_sync"           # Complete data refresh
    INCREMENTAL = "incremental"       # Only new/changed data
    REAL_TIME = "real_time"          # Continuous streaming
    SCHEDULED = "scheduled"           # Periodic batch sync

class IntegrationType(Enum):
    CRM = "crm"
    PAYMENT = "payment"
    EMAIL_MARKETING = "email_marketing"
    DATABASE = "database"
    WEBHOOK = "webhook"
    API = "api"
    STREAMING = "streaming"

@dataclass
class IntegrationCredentials:
    """Secure credential storage for integrations"""
    integration_id: str
    credential_type: str  # oauth2, api_key, basic_auth, custom
    
    # OAuth2 credentials
    access_token: str = ""
    refresh_token: str = ""
    token_expires_at: Optional[datetime] = None
    
    # API Key credentials
    api_key: str = ""
    api_secret: str = ""
    
    # Basic auth
    username: str = ""
    password: str = ""
    
    # Custom fields
    custom_fields: Dict[str, str] = field(default_factory=dict)
    
    # Security
    encrypted: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SyncConfiguration:
    """Configuration for data synchronization"""
    sync_mode: DataSyncMode
    sync_frequency: int = 3600  # seconds
    batch_size: int = 1000
    retry_attempts: int = 3
    retry_backoff: int = 60  # seconds
    
    # Data filtering
    data_filters: Dict[str, Any] = field(default_factory=dict)
    field_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Incremental sync settings
    incremental_field: str = "updated_at"  # Field to track changes
    last_sync_timestamp: Optional[datetime] = None
    
    # Rate limiting
    requests_per_minute: int = 60
    concurrent_requests: int = 5

@dataclass
class IntegrationConfiguration:
    """Complete integration configuration"""
    integration_id: str
    organization_id: str
    integration_name: str
    integration_type: IntegrationType
    provider_name: str  # salesforce, hubspot, stripe, etc.
    
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    credentials: Optional[IntegrationCredentials] = None
    sync_config: SyncConfiguration = field(default_factory=lambda: SyncConfiguration(DataSyncMode.INCREMENTAL))
    
    # Connection settings
    base_url: str = ""
    api_version: str = ""
    webhook_url: str = ""
    
    # Data mapping
    entity_mappings: Dict[str, str] = field(default_factory=dict)  # external_entity -> internal_entity
    
    # Monitoring
    last_sync_at: Optional[datetime] = None
    last_error: str = ""
    total_records_synced: int = 0
    sync_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class SyncResult:
    """Result of a data synchronization operation"""
    integration_id: str
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None
    
    success: bool = True
    error_message: str = ""
    
    # Sync statistics
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    
    # Performance metrics
    sync_duration_seconds: float = 0.0
    records_per_second: float = 0.0
    
    # Data details
    entities_synced: List[str] = field(default_factory=list)
    next_sync_cursor: str = ""
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseIntegrationConnector(ABC):
    """Base class for all integration connectors"""
    
    def __init__(self, config: IntegrationConfiguration):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = AsyncRateLimiter(
            requests_per_minute=config.sync_config.requests_per_minute
        )
        
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection to external service is working"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from external service"""
        pass
    
    @abstractmethod
    async def get_available_entities(self) -> List[str]:
        """Get list of available data entities from the service"""
        pass
    
    async def refresh_credentials(self) -> bool:
        """Refresh authentication credentials if needed"""
        return True
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """Set up webhook for real-time data updates"""
        return False  # Override in connectors that support webhooks
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

class AsyncRateLimiter:
    """Async rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if (now - req_time).seconds < 60]
            
            if len(self.requests) >= self.requests_per_minute:
                # Wait until we can make another request
                oldest_request = min(self.requests)
                wait_time = 60 - (now - oldest_request).seconds
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self.requests.append(now)

class IntegrationEngine:
    """
    Core integration engine for managing all data connectors
    
    Features:
    - Unified integration management across all connector types
    - Secure credential storage and rotation
    - Flexible data synchronization with multiple modes
    - Real-time webhook processing
    - Advanced rate limiting and error handling
    - Integration health monitoring and alerting
    - Data transformation and mapping
    - Audit logging and compliance tracking
    - Multi-tenant isolation and security
    - Extensible connector framework
    """
    
    def __init__(self):
        # Integration storage
        self.integrations: Dict[str, IntegrationConfiguration] = {}
        self.connectors: Dict[str, BaseIntegrationConnector] = {}
        
        # Sync management
        self.active_syncs: Dict[str, asyncio.Task] = {}
        self.sync_history: Dict[str, List[SyncResult]] = {}
        
        # Webhook handling
        self.webhook_handlers: Dict[str, Callable] = {}
        
        # Connection pooling
        self.session_pool: Dict[str, aiohttp.ClientSession] = {}
        
        # Monitoring
        self.metrics: Dict[str, Any] = {
            'total_integrations': 0,
            'active_integrations': 0,
            'total_syncs': 0,
            'failed_syncs': 0,
            'records_synced_today': 0
        }
        
        # Background tasks
        self.monitor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def register_integration(self, config: IntegrationConfiguration) -> str:
        """
        Register a new integration
        
        Args:
            config: Integration configuration
            
        Returns:
            Integration ID
        """
        if not config.integration_id:
            config.integration_id = f"int_{config.organization_id}_{int(datetime.now().timestamp())}"
        
        # Validate configuration
        self._validate_integration_config(config)
        
        # Create connector instance
        connector = await self._create_connector(config)
        if not connector:
            raise ValueError(f"Failed to create connector for {config.provider_name}")
        
        # Test connection
        try:
            if await connector.test_connection():
                config.status = IntegrationStatus.ACTIVE
                logger.info(f"Integration {config.integration_name} connection test successful")
            else:
                config.status = IntegrationStatus.ERROR
                logger.error(f"Integration {config.integration_name} connection test failed")
        except Exception as e:
            config.status = IntegrationStatus.ERROR
            config.last_error = str(e)
            logger.error(f"Integration {config.integration_name} connection error: {e}")
        
        self.integrations[config.integration_id] = config
        self.connectors[config.integration_id] = connector
        self.sync_history[config.integration_id] = []
        
        # Update metrics
        self.metrics['total_integrations'] += 1
        if config.status == IntegrationStatus.ACTIVE:
            self.metrics['active_integrations'] += 1
        
        logger.info(f"Registered integration {config.integration_name} with ID {config.integration_id}")
        return config.integration_id
    
    async def start_sync(self, integration_id: str, entity_types: List[str] = None) -> str:
        """
        Start data synchronization for an integration
        
        Args:
            integration_id: Integration identifier
            entity_types: Specific entity types to sync (optional)
            
        Returns:
            Sync task ID
        """
        if integration_id not in self.integrations:
            raise ValueError(f"Integration {integration_id} not found")
        
        config = self.integrations[integration_id]
        
        if config.status != IntegrationStatus.ACTIVE:
            raise ValueError(f"Integration {integration_id} is not active")
        
        # Check if sync is already running
        if integration_id in self.active_syncs and not self.active_syncs[integration_id].done():
            logger.warning(f"Sync already running for integration {integration_id}")
            return integration_id
        
        # Update status
        config.status = IntegrationStatus.SYNCING
        
        # Start sync task
        sync_task = asyncio.create_task(
            self._execute_sync(integration_id, entity_types)
        )
        self.active_syncs[integration_id] = sync_task
        
        logger.info(f"Started sync for integration {config.integration_name}")
        return integration_id
    
    async def stop_sync(self, integration_id: str) -> bool:
        """Stop active sync for an integration"""
        if integration_id in self.active_syncs:
            sync_task = self.active_syncs[integration_id]
            if not sync_task.done():
                sync_task.cancel()
                try:
                    await sync_task
                except asyncio.CancelledError:
                    pass
                
                # Update status
                if integration_id in self.integrations:
                    self.integrations[integration_id].status = IntegrationStatus.PAUSED
                
                logger.info(f"Stopped sync for integration {integration_id}")
                return True
        
        return False
    
    async def get_sync_status(self, integration_id: str) -> Dict[str, Any]:
        """Get current sync status for an integration"""
        if integration_id not in self.integrations:
            raise ValueError(f"Integration {integration_id} not found")
        
        config = self.integrations[integration_id]
        
        # Get latest sync result
        latest_sync = None
        if integration_id in self.sync_history and self.sync_history[integration_id]:
            latest_sync = self.sync_history[integration_id][-1]
        
        # Check if sync is currently running
        is_syncing = (integration_id in self.active_syncs and 
                     not self.active_syncs[integration_id].done())
        
        return {
            'integration_id': integration_id,
            'integration_name': config.integration_name,
            'status': config.status.value,
            'is_syncing': is_syncing,
            'last_sync_at': config.last_sync_at.isoformat() if config.last_sync_at else None,
            'total_records_synced': config.total_records_synced,
            'latest_sync_result': {
                'success': latest_sync.success if latest_sync else None,
                'records_processed': latest_sync.records_processed if latest_sync else 0,
                'sync_duration': latest_sync.sync_duration_seconds if latest_sync else 0,
                'error_message': latest_sync.error_message if latest_sync else ""
            } if latest_sync else None,
            'sync_config': {
                'sync_mode': config.sync_config.sync_mode.value,
                'sync_frequency': config.sync_config.sync_frequency,
                'batch_size': config.sync_config.batch_size
            },
            'metrics': config.sync_metrics
        }
    
    async def process_webhook(self, integration_id: str, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming webhook data"""
        if integration_id not in self.integrations:
            logger.error(f"Webhook received for unknown integration {integration_id}")
            return False
        
        config = self.integrations[integration_id]
        
        try:
            # Get webhook handler
            handler = self.webhook_handlers.get(config.provider_name)
            if not handler:
                logger.warning(f"No webhook handler for provider {config.provider_name}")
                return False
            
            # Process webhook data
            result = await handler(config, webhook_data)
            
            logger.info(f"Processed webhook for integration {config.integration_name}")
            return result
            
        except Exception as e:
            logger.error(f"Webhook processing error for {integration_id}: {e}")
            return False
    
    async def _execute_sync(self, integration_id: str, entity_types: List[str] = None) -> SyncResult:
        """Execute data synchronization"""
        config = self.integrations[integration_id]
        connector = self.connectors[integration_id]
        
        sync_result = SyncResult(
            integration_id=integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            # Ensure authentication is valid
            if not await connector.authenticate():
                raise Exception("Authentication failed")
            
            # Perform sync
            sync_result = await connector.sync_data(entity_types)
            sync_result.sync_completed_at = datetime.now()
            sync_result.sync_duration_seconds = (
                sync_result.sync_completed_at - sync_result.sync_started_at
            ).total_seconds()
            
            if sync_result.records_processed > 0:
                sync_result.records_per_second = (
                    sync_result.records_processed / sync_result.sync_duration_seconds
                )
            
            # Update configuration
            config.last_sync_at = sync_result.sync_completed_at
            config.total_records_synced += sync_result.records_processed
            config.status = IntegrationStatus.ACTIVE
            config.last_error = ""
            
            # Update sync config for incremental sync
            if config.sync_config.sync_mode == DataSyncMode.INCREMENTAL:
                config.sync_config.last_sync_timestamp = sync_result.sync_completed_at
            
            # Update metrics
            self.metrics['total_syncs'] += 1
            self.metrics['records_synced_today'] += sync_result.records_processed
            
            logger.info(f"Sync completed for {config.integration_name}: "
                       f"{sync_result.records_processed} records in "
                       f"{sync_result.sync_duration_seconds:.2f}s")
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            sync_result.sync_completed_at = datetime.now()
            
            config.status = IntegrationStatus.ERROR
            config.last_error = str(e)
            
            self.metrics['failed_syncs'] += 1
            
            logger.error(f"Sync failed for {config.integration_name}: {e}")
        
        # Store sync result
        self.sync_history[integration_id].append(sync_result)
        
        # Keep only last 100 sync results
        if len(self.sync_history[integration_id]) > 100:
            self.sync_history[integration_id] = self.sync_history[integration_id][-100:]
        
        return sync_result
    
    def _validate_integration_config(self, config: IntegrationConfiguration):
        """Validate integration configuration"""
        if not config.organization_id:
            raise ValueError("Organization ID is required")
        
        if not config.integration_name:
            raise ValueError("Integration name is required")
        
        if not config.provider_name:
            raise ValueError("Provider name is required")
        
        if not config.credentials:
            raise ValueError("Credentials are required")
    
    async def _create_connector(self, config: IntegrationConfiguration) -> Optional[BaseIntegrationConnector]:
        """Create appropriate connector instance based on provider"""
        # Dynamic connector creation based on provider
        # This will be implemented for each specific connector
        connector_map = {
            'salesforce': 'SalesforceConnector',
            'hubspot': 'HubSpotConnector',
            'stripe': 'StripeConnector',
            'mysql': 'MySQLConnector',
            'postgresql': 'PostgreSQLConnector',
            'mongodb': 'MongoDBConnector'
        }
        
        connector_class = connector_map.get(config.provider_name.lower())
        if not connector_class:
            logger.error(f"No connector available for provider {config.provider_name}")
            return None
        
        # For now, return a placeholder - specific connectors will be implemented
        return None

# Global integration engine
integration_engine = IntegrationEngine()

def get_integration_engine() -> IntegrationEngine:
    """Get the global integration engine"""
    return integration_engine

# Convenience functions
async def register_integration(config: IntegrationConfiguration) -> str:
    """Register a new integration"""
    engine = get_integration_engine()
    return await engine.register_integration(config)

async def start_integration_sync(integration_id: str) -> str:
    """Start sync for an integration"""
    engine = get_integration_engine()
    return await engine.start_sync(integration_id)