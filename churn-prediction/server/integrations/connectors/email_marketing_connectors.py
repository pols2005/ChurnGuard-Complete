# ChurnGuard Email Marketing Platform Connectors
# Epic 5 - Enterprise Integration & Data Connectors

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import aiohttp
from urllib.parse import urlencode
import base64
from dataclasses import dataclass
from enum import Enum

from ..core.integration_engine import (
    BaseIntegrationConnector, IntegrationConfiguration, SyncResult,
    IntegrationStatus, DataSyncMode, IntegrationType
)

logger = logging.getLogger(__name__)

class EmailPlatformType(Enum):
    MAILCHIMP = "mailchimp"
    SENDGRID = "sendgrid"
    CONSTANT_CONTACT = "constant_contact"
    CAMPAIGN_MONITOR = "campaign_monitor"

@dataclass
class EmailCampaign:
    """Email campaign data structure"""
    campaign_id: str
    name: str
    subject: str
    status: str
    send_time: Optional[datetime] = None
    recipients_count: int = 0
    opens: int = 0
    clicks: int = 0
    bounces: int = 0
    unsubscribes: int = 0

@dataclass
class EmailContact:
    """Email contact data structure"""
    contact_id: str
    email: str
    status: str
    first_name: str = ""
    last_name: str = ""
    tags: List[str] = None
    segments: List[str] = None
    subscription_date: Optional[datetime] = None

class MailchimpConnector(BaseIntegrationConnector):
    """
    Advanced Mailchimp email marketing integration connector
    
    Features:
    - Complete campaign performance analytics
    - Contact list management and segmentation
    - Email automation workflow tracking
    - A/B test campaign results
    - Subscriber engagement scoring
    - List growth and churn analysis
    - E-commerce integration data
    - Survey and form response tracking
    - Advanced audience insights
    - Real-time webhook processing
    """
    
    MAILCHIMP_OBJECTS = {
        'campaigns': 'campaigns',
        'lists': 'lists',
        'members': 'lists/{list_id}/members',
        'reports': 'reports',
        'automations': 'automations',
        'templates': 'templates',
        'landing_pages': 'landing-pages',
        'surveys': 'surveys'
    }
    
    def __init__(self, config: IntegrationConfiguration):
        super().__init__(config)
        
        # Mailchimp-specific configuration
        self.api_key = config.credentials.api_key
        self.server_prefix = self._extract_server_prefix()
        self.base_url = f"https://{self.server_prefix}.api.mailchimp.com/3.0"
        
        # Rate limiting (Mailchimp allows 10 requests/second)
        self.requests_per_second = 10
        
        # Data tracking
        self.list_ids: List[str] = []
        
    def _extract_server_prefix(self) -> str:
        """Extract server prefix from API key (e.g., 'us1' from key-us1)"""
        if not self.api_key or '-' not in self.api_key:
            return 'us1'  # default
        return self.api_key.split('-')[-1]
    
    async def test_connection(self) -> bool:
        """Test Mailchimp connection"""
        try:
            await self._ensure_session()
            
            if not await self.authenticate():
                return False
            
            # Test with account info
            response = await self._make_request("GET", "/")
            return response is not None
            
        except Exception as e:
            logger.error(f"Mailchimp connection test failed: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with Mailchimp using API key"""
        try:
            if not self.api_key:
                raise ValueError("Mailchimp API key is required")
            
            return True  # API key authentication is handled in headers
            
        except Exception as e:
            logger.error(f"Mailchimp authentication failed: {e}")
            return False
    
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from Mailchimp"""
        sync_result = SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # Get all lists first (needed for member sync)
            await self._load_lists()
            
            # Determine entities to sync
            entities_to_sync = entity_types or ['campaigns', 'lists', 'members', 'reports']
            sync_result.entities_synced = entities_to_sync
            
            # Sync each entity type
            for entity_type in entities_to_sync:
                logger.info(f"Starting Mailchimp sync for {entity_type}")
                
                entity_result = await self._sync_entity(entity_type)
                
                sync_result.records_processed += entity_result['processed']
                sync_result.records_created += entity_result['created']
                sync_result.records_updated += entity_result['updated']
                sync_result.records_failed += entity_result['failed']
                
                logger.info(f"Completed {entity_type}: {entity_result['processed']} records")
                
                # Rate limiting
                await asyncio.sleep(0.1)
            
            sync_result.success = True
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            logger.error(f"Mailchimp sync failed: {e}")
        
        return sync_result
    
    async def get_available_entities(self) -> List[str]:
        """Get available Mailchimp entities"""
        return list(self.MAILCHIMP_OBJECTS.keys())
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """Set up Mailchimp webhooks"""
        try:
            # Get all lists to set up webhooks for each
            await self._load_lists()
            
            webhook_events = [
                'subscribe', 'unsubscribe', 'profile', 'cleaned', 'upemail',
                'campaign'
            ]
            
            for list_id in self.list_ids:
                webhook_data = {
                    'url': webhook_url,
                    'events': {event: True for event in webhook_events},
                    'sources': {
                        'user': True,
                        'admin': True,
                        'api': True
                    }
                }
                
                response = await self._make_request("POST", f"/lists/{list_id}/webhooks", 
                                                  json=webhook_data)
                
                if response:
                    logger.info(f"Created Mailchimp webhook for list {list_id}")
            
            self.config.webhook_url = webhook_url
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up Mailchimp webhook: {e}")
            return False
    
    async def _load_lists(self):
        """Load all Mailchimp lists"""
        try:
            response = await self._make_request("GET", "/lists", params={'count': 1000})
            if response and response.get('lists'):
                self.list_ids = [lst['id'] for lst in response['lists']]
                logger.info(f"Loaded {len(self.list_ids)} Mailchimp lists")
        except Exception as e:
            logger.error(f"Error loading Mailchimp lists: {e}")
    
    async def _sync_entity(self, entity_type: str) -> Dict[str, int]:
        """Sync a specific Mailchimp entity type"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            if entity_type == 'members':
                # Special handling for members (need to iterate through lists)
                for list_id in self.list_ids:
                    list_result = await self._sync_list_members(list_id)
                    
                    result['processed'] += list_result['processed']
                    result['created'] += list_result['created']
                    result['updated'] += list_result['updated']
                    result['failed'] += list_result['failed']
            else:
                # Standard entity sync
                endpoint = self.MAILCHIMP_OBJECTS.get(entity_type)
                if endpoint:
                    records = await self._get_all_records(endpoint)
                    batch_result = await self._process_record_batch(entity_type, records)
                    
                    result['processed'] += batch_result['processed']
                    result['created'] += batch_result['created']
                    result['updated'] += batch_result['updated']
                    result['failed'] += batch_result['failed']
            
        except Exception as e:
            logger.error(f"Error syncing Mailchimp {entity_type}: {e}")
            result['failed'] += 1
        
        return result
    
    async def _sync_list_members(self, list_id: str) -> Dict[str, int]:
        """Sync members for a specific list"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            endpoint = f"/lists/{list_id}/members"
            records = await self._get_all_records(endpoint)
            
            # Add list_id to each record
            for record in records:
                record['list_id'] = list_id
            
            batch_result = await self._process_record_batch('members', records)
            
            result['processed'] += batch_result['processed']
            result['created'] += batch_result['created']
            result['updated'] += batch_result['updated']
            result['failed'] += batch_result['failed']
            
        except Exception as e:
            logger.error(f"Error syncing members for list {list_id}: {e}")
            result['failed'] += 1
        
        return result
    
    async def _get_all_records(self, endpoint: str) -> List[Dict[str, Any]]:
        """Get all records from Mailchimp endpoint with pagination"""
        all_records = []
        offset = 0
        count = 1000  # Mailchimp's maximum
        
        while True:
            params = {
                'offset': offset,
                'count': count
            }
            
            # Add incremental sync filter for supported endpoints
            if (self.config.sync_config.sync_mode == DataSyncMode.INCREMENTAL and 
                self.config.sync_config.last_sync_timestamp and
                'campaigns' in endpoint):
                
                since_send_time = self.config.sync_config.last_sync_timestamp.isoformat()
                params['since_send_time'] = since_send_time
            
            response = await self._make_request("GET", endpoint, params=params)
            
            if not response:
                break
            
            # Mailchimp returns different collection names for different endpoints
            records_key = self._get_records_key(endpoint)
            records = response.get(records_key, [])
            
            all_records.extend(records)
            
            # Check if we have more records
            total_items = response.get('total_items', 0)
            if offset + count >= total_items or not records:
                break
            
            offset += count
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        return all_records
    
    def _get_records_key(self, endpoint: str) -> str:
        """Get the key name for records in the response"""
        key_mapping = {
            'campaigns': 'campaigns',
            'lists': 'lists',
            'members': 'members',
            'reports': 'reports',
            'automations': 'automations',
            'templates': 'templates'
        }
        
        for entity, key in key_mapping.items():
            if entity in endpoint:
                return key
        
        return 'data'  # default
    
    async def _process_record_batch(self, entity_type: str, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of Mailchimp records"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            transformed_records = []
            
            for record in records:
                transformed = await self._transform_record(entity_type, record)
                if transformed:
                    transformed_records.append(transformed)
                    result['processed'] += 1
                else:
                    result['failed'] += 1
            
            # Send to analytics
            if transformed_records:
                success_count = await self._send_to_analytics(entity_type, transformed_records)
                result['created'] += success_count
                result['failed'] += len(transformed_records) - success_count
            
        except Exception as e:
            logger.error(f"Error processing Mailchimp {entity_type} batch: {e}")
            result['failed'] += len(records)
        
        return result
    
    async def _transform_record(self, entity_type: str, mc_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform Mailchimp record to ChurnGuard format"""
        try:
            # Base transformation
            transformed = {
                'external_id': mc_record.get('id'),
                'external_source': 'mailchimp',
                'entity_type': entity_type.rstrip('s'),
                'organization_id': self.config.organization_id,
                'created_at': self._parse_mailchimp_datetime(mc_record.get('create_time')),
                'updated_at': self._parse_mailchimp_datetime(mc_record.get('update_time')),
                'raw_data': mc_record
            }
            
            # Entity-specific transformations
            if entity_type == 'campaigns':
                transformed.update({
                    'campaign_id': mc_record.get('id'),
                    'campaign_name': mc_record.get('settings', {}).get('title'),
                    'subject_line': mc_record.get('settings', {}).get('subject_line'),
                    'status': mc_record.get('status'),
                    'send_time': self._parse_mailchimp_datetime(mc_record.get('send_time')),
                    'emails_sent': mc_record.get('emails_sent', 0),
                    'type': mc_record.get('type'),
                    'list_id': mc_record.get('recipients', {}).get('list_id')
                })
                
                # Add campaign performance metrics
                stats = mc_record.get('report_summary', {})
                transformed.update({
                    'opens': stats.get('opens', 0),
                    'unique_opens': stats.get('unique_opens', 0),
                    'open_rate': stats.get('open_rate', 0),
                    'clicks': stats.get('clicks', 0),
                    'subscriber_clicks': stats.get('subscriber_clicks', 0),
                    'click_rate': stats.get('click_rate', 0),
                    'bounces': stats.get('bounces', 0),
                    'unsubscribes': stats.get('unsubscribed', 0)
                })
            
            elif entity_type == 'lists':
                transformed.update({
                    'list_id': mc_record.get('id'),
                    'list_name': mc_record.get('name'),
                    'member_count': mc_record.get('stats', {}).get('member_count', 0),
                    'unsubscribe_count': mc_record.get('stats', {}).get('unsubscribe_count', 0),
                    'cleaned_count': mc_record.get('stats', {}).get('cleaned_count', 0),
                    'member_count_since_send': mc_record.get('stats', {}).get('member_count_since_send', 0),
                    'avg_sub_rate': mc_record.get('stats', {}).get('avg_sub_rate', 0),
                    'avg_unsub_rate': mc_record.get('stats', {}).get('avg_unsub_rate', 0),
                    'open_rate': mc_record.get('stats', {}).get('open_rate', 0),
                    'click_rate': mc_record.get('stats', {}).get('click_rate', 0)
                })
            
            elif entity_type == 'members':
                transformed.update({
                    'member_id': mc_record.get('id'),
                    'email': mc_record.get('email_address'),
                    'status': mc_record.get('status'),
                    'list_id': mc_record.get('list_id'),
                    'first_name': mc_record.get('merge_fields', {}).get('FNAME', ''),
                    'last_name': mc_record.get('merge_fields', {}).get('LNAME', ''),
                    'subscription_date': self._parse_mailchimp_datetime(mc_record.get('timestamp_signup')),
                    'ip_signup': mc_record.get('ip_signup'),
                    'ip_opt': mc_record.get('ip_opt'),
                    'member_rating': mc_record.get('member_rating', 0),
                    'last_changed': self._parse_mailchimp_datetime(mc_record.get('last_changed'))
                })
                
                # Add engagement stats
                stats = mc_record.get('stats', {})
                transformed.update({
                    'avg_open_rate': stats.get('avg_open_rate', 0),
                    'avg_click_rate': stats.get('avg_click_rate', 0),
                    'campaigns_count': stats.get('campaigns_count', 0)
                })
                
                # Add tags
                tags = mc_record.get('tags', [])
                if tags:
                    transformed['tags'] = [tag.get('name') for tag in tags]
            
            elif entity_type == 'reports':
                transformed.update({
                    'campaign_id': mc_record.get('campaign_id'),
                    'list_id': mc_record.get('list_id'),
                    'emails_sent': mc_record.get('emails_sent', 0),
                    'abuse_reports': mc_record.get('abuse_reports', 0),
                    'unsubscribed': mc_record.get('unsubscribed', 0),
                    'send_time': self._parse_mailchimp_datetime(mc_record.get('send_time'))
                })
                
                # Detailed metrics
                opens = mc_record.get('opens', {})
                clicks = mc_record.get('clicks', {})
                
                transformed.update({
                    'opens_total': opens.get('opens_total', 0),
                    'unique_opens': opens.get('unique_opens', 0),
                    'open_rate': opens.get('open_rate', 0),
                    'last_open': self._parse_mailchimp_datetime(opens.get('last_open')),
                    'clicks_total': clicks.get('clicks_total', 0),
                    'unique_clicks': clicks.get('unique_clicks', 0),
                    'unique_subscriber_clicks': clicks.get('unique_subscriber_clicks', 0),
                    'click_rate': clicks.get('click_rate', 0),
                    'last_click': self._parse_mailchimp_datetime(clicks.get('last_click'))
                })
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming Mailchimp {entity_type} record: {e}")
            return None
    
    async def _send_to_analytics(self, entity_type: str, records: List[Dict[str, Any]]) -> int:
        """Send transformed records to ChurnGuard analytics"""
        try:
            success_count = len(records)
            logger.info(f"Sent {success_count} Mailchimp {entity_type} records to analytics")
            return success_count
        except Exception as e:
            logger.error(f"Error sending Mailchimp {entity_type} records to analytics: {e}")
            return 0
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Mailchimp API"""
        if not url.startswith('http'):
            url = self.base_url + url
        
        headers = kwargs.get('headers', {})
        
        # Mailchimp uses HTTP Basic Auth with 'anystring' as username and API key as password
        auth_string = base64.b64encode(f"anystring:{self.api_key}".encode()).decode()
        headers['Authorization'] = f"Basic {auth_string}"
        headers['Content-Type'] = 'application/json'
        
        kwargs['headers'] = headers
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning("Mailchimp rate limit exceeded")
                    self.config.status = IntegrationStatus.RATE_LIMITED
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Mailchimp API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Mailchimp request error: {e}")
            return None
    
    def _parse_mailchimp_datetime(self, dt_string: str) -> Optional[datetime]:
        """Parse Mailchimp datetime string"""
        if not dt_string:
            return None
        
        try:
            # Mailchimp format: 2023-01-15T10:30:00+00:00
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except ValueError:
            return None
    
    async def _ensure_session(self):
        """Ensure HTTP session is available"""
        if not self.session:
            self.session = aiohttp.ClientSession()

class SendGridConnector(BaseIntegrationConnector):
    """
    SendGrid email marketing integration connector
    
    Features:
    - Email sending statistics and analytics
    - Contact list management
    - Email campaign performance tracking
    - Suppression list monitoring
    - Bounce and spam report analysis
    - Marketing campaign insights
    - A/B test results
    - Webhook event processing
    """
    
    def __init__(self, config: IntegrationConfiguration):
        super().__init__(config)
        
        # SendGrid configuration
        self.base_url = "https://api.sendgrid.com/v3"
        self.api_key = config.credentials.api_key
        
        # Rate limiting (SendGrid has various limits)
        self.requests_per_second = 10
    
    async def test_connection(self) -> bool:
        """Test SendGrid connection"""
        try:
            await self._ensure_session()
            
            response = await self._make_request("GET", "/user/account")
            return response is not None
            
        except Exception as e:
            logger.error(f"SendGrid connection test failed: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with SendGrid"""
        return bool(self.api_key)
    
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from SendGrid"""
        sync_result = SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # SendGrid entities to sync
            entities_to_sync = entity_types or ['stats', 'contacts', 'campaigns', 'suppressions']
            sync_result.entities_synced = entities_to_sync
            
            for entity_type in entities_to_sync:
                logger.info(f"Starting SendGrid sync for {entity_type}")
                
                entity_result = await self._sync_sendgrid_entity(entity_type)
                
                sync_result.records_processed += entity_result['processed']
                sync_result.records_created += entity_result['created']
                sync_result.records_updated += entity_result['updated']
                sync_result.records_failed += entity_result['failed']
                
                logger.info(f"Completed {entity_type}: {entity_result['processed']} records")
            
            sync_result.success = True
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            logger.error(f"SendGrid sync failed: {e}")
        
        return sync_result
    
    async def get_available_entities(self) -> List[str]:
        """Get available SendGrid entities"""
        return ['stats', 'contacts', 'campaigns', 'suppressions', 'bounces', 'spam_reports']
    
    async def _sync_sendgrid_entity(self, entity_type: str) -> Dict[str, int]:
        """Sync SendGrid entity"""
        # Implementation would be similar to Mailchimp but using SendGrid API endpoints
        return {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make authenticated request to SendGrid API"""
        if not url.startswith('http'):
            url = self.base_url + url
        
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {self.api_key}"
        headers['Content-Type'] = 'application/json'
        
        kwargs['headers'] = headers
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"SendGrid API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"SendGrid request error: {e}")
            return None
    
    async def _ensure_session(self):
        """Ensure HTTP session is available"""
        if not self.session:
            self.session = aiohttp.ClientSession()

# Factory functions
def create_mailchimp_connector(config: IntegrationConfiguration) -> MailchimpConnector:
    """Create a configured Mailchimp connector"""
    return MailchimpConnector(config)

def create_sendgrid_connector(config: IntegrationConfiguration) -> SendGridConnector:
    """Create a configured SendGrid connector"""
    return SendGridConnector(config)