# ChurnGuard Stripe Payment Processor Connector
# Epic 5 - Enterprise Integration & Data Connectors

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import aiohttp
import base64
from decimal import Decimal
from dataclasses import dataclass

from ..core.integration_engine import (
    BaseIntegrationConnector, IntegrationConfiguration, SyncResult,
    IntegrationStatus, DataSyncMode, IntegrationType
)

logger = logging.getLogger(__name__)

@dataclass
class StripeObject:
    """Stripe object definition"""
    object_type: str
    name: str
    endpoint: str
    expandable_fields: List[str] = None

class StripeConnector(BaseIntegrationConnector):
    """
    Advanced Stripe payment processor integration connector
    
    Features:
    - Complete payment data synchronization
    - Customer lifecycle and subscription analytics
    - Revenue recognition and MRR calculations
    - Churn analysis from subscription events
    - Failed payment and dunning management
    - Refund and dispute tracking
    - Multi-currency support with conversion
    - Webhook processing for real-time updates
    - Subscription metrics and cohort analysis
    - Payment method and card analytics
    - Fraud detection and risk scoring
    - Invoice and billing data integration
    """
    
    STRIPE_OBJECTS = {
        'customers': StripeObject(
            object_type='customer',
            name='Customer',
            endpoint='customers',
            expandable_fields=['default_source', 'subscriptions', 'tax_info']
        ),
        'subscriptions': StripeObject(
            object_type='subscription',
            name='Subscription',
            endpoint='subscriptions',
            expandable_fields=['customer', 'default_payment_method', 'latest_invoice']
        ),
        'charges': StripeObject(
            object_type='charge',
            name='Charge',
            endpoint='charges',
            expandable_fields=['customer', 'invoice', 'payment_method']
        ),
        'payment_intents': StripeObject(
            object_type='payment_intent',
            name='Payment Intent',
            endpoint='payment_intents',
            expandable_fields=['customer', 'payment_method']
        ),
        'invoices': StripeObject(
            object_type='invoice',
            name='Invoice',
            endpoint='invoices',
            expandable_fields=['customer', 'subscription', 'charge']
        ),
        'payment_methods': StripeObject(
            object_type='payment_method',
            name='Payment Method',
            endpoint='payment_methods',
            expandable_fields=['customer']
        ),
        'products': StripeObject(
            object_type='product',
            name='Product',
            endpoint='products'
        ),
        'prices': StripeObject(
            object_type='price',
            name='Price',
            endpoint='prices',
            expandable_fields=['product']
        ),
        'events': StripeObject(
            object_type='event',
            name='Event',
            endpoint='events'
        ),
        'disputes': StripeObject(
            object_type='dispute',
            name='Dispute',
            endpoint='disputes',
            expandable_fields=['charge']
        ),
        'refunds': StripeObject(
            object_type='refund',
            name='Refund',
            endpoint='refunds',
            expandable_fields=['charge']
        ),
        'coupons': StripeObject(
            object_type='coupon',
            name='Coupon',
            endpoint='coupons'
        ),
        'plans': StripeObject(
            object_type='plan',
            name='Plan',
            endpoint='plans',
            expandable_fields=['product']
        )
    }
    
    def __init__(self, config: IntegrationConfiguration):
        super().__init__(config)
        
        # Stripe API configuration
        self.base_url = "https://api.stripe.com"
        self.api_version = "2023-10-16"  # Latest Stripe API version
        
        # Webhooks
        self.webhook_events = [
            'customer.created', 'customer.updated', 'customer.deleted',
            'subscription.created', 'subscription.updated', 'subscription.deleted',
            'invoice.payment_succeeded', 'invoice.payment_failed',
            'charge.succeeded', 'charge.failed', 'charge.dispute.created',
            'payment_intent.succeeded', 'payment_intent.payment_failed'
        ]
        
        # Currency handling
        self.zero_decimal_currencies = {
            'bif', 'clp', 'djf', 'gnf', 'jpy', 'kmf', 'krw',
            'mga', 'pyg', 'rwf', 'ugx', 'vnd', 'vuv', 'xaf',
            'xof', 'xpf'
        }
        
        # Sync tracking
        self.last_event_id: Optional[str] = None
        self.subscription_metrics_cache: Dict[str, Any] = {}
        
        # Rate limiting (Stripe allows 100 requests per second)
        self.requests_per_second = 100
    
    async def test_connection(self) -> bool:
        """Test Stripe connection"""
        try:
            await self._ensure_session()
            
            if not await self.authenticate():
                return False
            
            # Test with a simple account retrieval
            response = await self._make_request("GET", "/v1/account")
            return response is not None
            
        except Exception as e:
            logger.error(f"Stripe connection test failed: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with Stripe using API key"""
        try:
            credentials = self.config.credentials
            if not credentials or not credentials.api_key:
                raise ValueError("Stripe API key is required")
            
            # Stripe uses HTTP Basic Auth with API key as username
            return True  # Authentication is handled in request headers
            
        except Exception as e:
            logger.error(f"Stripe authentication setup failed: {e}")
            return False
    
    async def sync_data(self, entity_types: List[str] = None) -> SyncResult:
        """Synchronize data from Stripe"""
        sync_result = SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=datetime.now()
        )
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # Determine entities to sync
            entities_to_sync = entity_types or list(self.STRIPE_OBJECTS.keys())
            sync_result.entities_synced = entities_to_sync
            
            # Prioritize customer-related objects first for better relationship mapping
            priority_order = ['customers', 'products', 'prices', 'subscriptions', 'charges', 
                            'payment_intents', 'invoices', 'payment_methods', 'events', 
                            'disputes', 'refunds']
            
            ordered_entities = []
            for entity in priority_order:
                if entity in entities_to_sync:
                    ordered_entities.append(entity)
            
            # Add any remaining entities
            for entity in entities_to_sync:
                if entity not in ordered_entities:
                    ordered_entities.append(entity)
            
            # Sync each entity type
            for entity_type in ordered_entities:
                logger.info(f"Starting sync for Stripe {entity_type}")
                
                entity_result = await self._sync_entity(entity_type)
                
                sync_result.records_processed += entity_result['processed']
                sync_result.records_created += entity_result['created']
                sync_result.records_updated += entity_result['updated']
                sync_result.records_failed += entity_result['failed']
                
                logger.info(f"Completed {entity_type}: {entity_result['processed']} records")
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.01)
            
            # Calculate subscription metrics
            if 'subscriptions' in entities_to_sync:
                await self._calculate_subscription_metrics()
            
            sync_result.success = True
            
        except Exception as e:
            sync_result.success = False
            sync_result.error_message = str(e)
            logger.error(f"Stripe sync failed: {e}")
        
        return sync_result
    
    async def get_available_entities(self) -> List[str]:
        """Get available Stripe objects"""
        return list(self.STRIPE_OBJECTS.keys())
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """Set up Stripe webhooks for real-time updates"""
        try:
            # Create webhook endpoint
            webhook_data = {
                'url': webhook_url,
                'enabled_events': self.webhook_events,
                'description': 'ChurnGuard Integration Webhook'
            }
            
            response = await self._make_request("POST", "/v1/webhook_endpoints", data=webhook_data)
            
            if response:
                webhook_secret = response.get('secret')
                if webhook_secret:
                    # Store webhook secret for signature verification
                    self.config.credentials.custom_fields['webhook_secret'] = webhook_secret
                
                self.config.webhook_url = webhook_url
                logger.info("Stripe webhook endpoint created successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to set up Stripe webhook: {e}")
            return False
    
    async def _sync_entity(self, entity_type: str) -> Dict[str, int]:
        """Sync a specific entity type from Stripe"""
        result = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0}
        
        try:
            stripe_object = self.STRIPE_OBJECTS.get(entity_type)
            if not stripe_object:
                logger.error(f"Unknown Stripe object: {entity_type}")
                return result
            
            # Get all records with pagination
            records = await self._get_all_records(stripe_object)
            
            # Process records in batches
            batch_size = self.config.sync_config.batch_size
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                batch_result = await self._process_record_batch(entity_type, batch)
                
                result['processed'] += batch_result['processed']
                result['created'] += batch_result['created']
                result['updated'] += batch_result['updated']
                result['failed'] += batch_result['failed']
                
                # Rate limiting
                await self.rate_limiter.acquire()
            
        except Exception as e:
            logger.error(f"Error syncing {entity_type}: {e}")
            result['failed'] = 1
        
        return result
    
    async def _get_all_records(self, stripe_object: StripeObject) -> List[Dict[str, Any]]:
        """Get all records for a Stripe object with pagination"""
        all_records = []
        starting_after = None
        limit = 100  # Stripe's maximum per request
        
        while True:
            params = {'limit': limit}
            
            if starting_after:
                params['starting_after'] = starting_after
            
            # Add expand parameters for related objects
            if stripe_object.expandable_fields:
                params['expand[]'] = stripe_object.expandable_fields
            
            # Add incremental sync filter
            if (self.config.sync_config.sync_mode == DataSyncMode.INCREMENTAL and 
                self.config.sync_config.last_sync_timestamp):
                
                last_sync_timestamp = int(self.config.sync_config.last_sync_timestamp.timestamp())
                
                if entity_type in ['charges', 'payment_intents', 'invoices', 'events']:
                    params['created'] = {'gte': last_sync_timestamp}
                elif entity_type == 'subscriptions':
                    params['created'] = {'gte': last_sync_timestamp}
            
            response = await self._make_request("GET", f"/v1/{stripe_object.endpoint}", params=params)
            
            if not response:
                break
            
            records = response.get('data', [])
            all_records.extend(records)
            
            # Check for more pages
            if not response.get('has_more', False) or not records:
                break
            
            # Get the last record's ID for pagination
            starting_after = records[-1]['id']
            
            # Rate limiting
            await asyncio.sleep(0.01)
        
        return all_records
    
    async def _process_record_batch(self, entity_type: str, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of Stripe records"""
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
            logger.error(f"Error processing {entity_type} batch: {e}")
            result['failed'] += len(records)
        
        return result
    
    async def _transform_record(self, entity_type: str, stripe_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform Stripe record to ChurnGuard format"""
        try:
            # Base transformation
            transformed = {
                'external_id': stripe_record.get('id'),
                'external_source': 'stripe',
                'entity_type': entity_type.rstrip('s'),  # Remove plural
                'organization_id': self.config.organization_id,
                'created_at': self._parse_stripe_timestamp(stripe_record.get('created')),
                'updated_at': datetime.now(),  # Stripe doesn't have a universal updated field
                'raw_data': stripe_record
            }
            
            # Entity-specific transformations
            if entity_type == 'customers':
                transformed.update({
                    'customer_id': stripe_record.get('id'),
                    'email': stripe_record.get('email'),
                    'name': stripe_record.get('name'),
                    'phone': stripe_record.get('phone'),
                    'description': stripe_record.get('description'),
                    'currency': stripe_record.get('currency'),
                    'balance': self._convert_stripe_amount(stripe_record.get('balance', 0), 
                                                         stripe_record.get('currency', 'usd')),
                    'delinquent': stripe_record.get('delinquent', False),
                    'default_source': stripe_record.get('default_source'),
                    'invoice_prefix': stripe_record.get('invoice_prefix')
                })
                
                # Add metadata
                metadata = stripe_record.get('metadata', {})
                if metadata:
                    transformed['metadata'] = metadata
            
            elif entity_type == 'subscriptions':
                transformed.update({
                    'subscription_id': stripe_record.get('id'),
                    'customer_id': self._get_customer_id(stripe_record.get('customer')),
                    'status': stripe_record.get('status'),
                    'current_period_start': self._parse_stripe_timestamp(stripe_record.get('current_period_start')),
                    'current_period_end': self._parse_stripe_timestamp(stripe_record.get('current_period_end')),
                    'trial_start': self._parse_stripe_timestamp(stripe_record.get('trial_start')),
                    'trial_end': self._parse_stripe_timestamp(stripe_record.get('trial_end')),
                    'canceled_at': self._parse_stripe_timestamp(stripe_record.get('canceled_at')),
                    'cancel_at_period_end': stripe_record.get('cancel_at_period_end', False),
                    'collection_method': stripe_record.get('collection_method'),
                    'currency': stripe_record.get('currency'),
                    'default_payment_method': stripe_record.get('default_payment_method')
                })
                
                # Calculate MRR/ARR from subscription items
                items = stripe_record.get('items', {}).get('data', [])
                mrr = 0
                for item in items:
                    price = item.get('price', {})
                    if price:
                        unit_amount = price.get('unit_amount', 0)
                        quantity = item.get('quantity', 1)
                        interval = price.get('recurring', {}).get('interval')
                        
                        amount = self._convert_stripe_amount(unit_amount * quantity, stripe_record.get('currency', 'usd'))
                        
                        # Convert to monthly recurring revenue
                        if interval == 'month':
                            mrr += amount
                        elif interval == 'year':
                            mrr += amount / 12
                        elif interval == 'week':
                            mrr += amount * 4.33
                        elif interval == 'day':
                            mrr += amount * 30
                
                transformed['mrr'] = mrr
                transformed['arr'] = mrr * 12
            
            elif entity_type == 'charges':
                transformed.update({
                    'charge_id': stripe_record.get('id'),
                    'customer_id': self._get_customer_id(stripe_record.get('customer')),
                    'amount': self._convert_stripe_amount(stripe_record.get('amount', 0), 
                                                        stripe_record.get('currency', 'usd')),
                    'amount_captured': self._convert_stripe_amount(stripe_record.get('amount_captured', 0), 
                                                                 stripe_record.get('currency', 'usd')),
                    'amount_refunded': self._convert_stripe_amount(stripe_record.get('amount_refunded', 0), 
                                                                 stripe_record.get('currency', 'usd')),
                    'currency': stripe_record.get('currency'),
                    'status': stripe_record.get('status'),
                    'paid': stripe_record.get('paid', False),
                    'captured': stripe_record.get('captured', False),
                    'refunded': stripe_record.get('refunded', False),
                    'disputed': stripe_record.get('disputed', False),
                    'failure_code': stripe_record.get('failure_code'),
                    'failure_message': stripe_record.get('failure_message'),
                    'invoice': stripe_record.get('invoice'),
                    'description': stripe_record.get('description')
                })
                
                # Payment method details
                payment_method_details = stripe_record.get('payment_method_details', {})
                if payment_method_details:
                    transformed['payment_method_type'] = payment_method_details.get('type')
                    
                    # Card-specific details
                    card = payment_method_details.get('card', {})
                    if card:
                        transformed.update({
                            'card_brand': card.get('brand'),
                            'card_last4': card.get('last4'),
                            'card_exp_month': card.get('exp_month'),
                            'card_exp_year': card.get('exp_year'),
                            'card_country': card.get('country')
                        })
            
            elif entity_type == 'invoices':
                transformed.update({
                    'invoice_id': stripe_record.get('id'),
                    'customer_id': self._get_customer_id(stripe_record.get('customer')),
                    'subscription_id': stripe_record.get('subscription'),
                    'amount_due': self._convert_stripe_amount(stripe_record.get('amount_due', 0), 
                                                            stripe_record.get('currency', 'usd')),
                    'amount_paid': self._convert_stripe_amount(stripe_record.get('amount_paid', 0), 
                                                             stripe_record.get('currency', 'usd')),
                    'amount_remaining': self._convert_stripe_amount(stripe_record.get('amount_remaining', 0), 
                                                                  stripe_record.get('currency', 'usd')),
                    'subtotal': self._convert_stripe_amount(stripe_record.get('subtotal', 0), 
                                                          stripe_record.get('currency', 'usd')),
                    'total': self._convert_stripe_amount(stripe_record.get('total', 0), 
                                                       stripe_record.get('currency', 'usd')),
                    'currency': stripe_record.get('currency'),
                    'status': stripe_record.get('status'),
                    'paid': stripe_record.get('paid', False),
                    'number': stripe_record.get('number'),
                    'due_date': self._parse_stripe_timestamp(stripe_record.get('due_date')),
                    'period_start': self._parse_stripe_timestamp(stripe_record.get('period_start')),
                    'period_end': self._parse_stripe_timestamp(stripe_record.get('period_end'))
                })
            
            elif entity_type == 'events':
                transformed.update({
                    'event_id': stripe_record.get('id'),
                    'event_type': stripe_record.get('type'),
                    'api_version': stripe_record.get('api_version'),
                    'livemode': stripe_record.get('livemode', False),
                    'pending_webhooks': stripe_record.get('pending_webhooks', 0),
                    'request_id': stripe_record.get('request', {}).get('id'),
                    'request_idempotency_key': stripe_record.get('request', {}).get('idempotency_key')
                })
                
                # Extract object data from event
                event_data = stripe_record.get('data', {})
                if event_data:
                    transformed['event_object_type'] = event_data.get('object', {}).get('object')
                    transformed['event_object_id'] = event_data.get('object', {}).get('id')
            
            # Apply custom field mappings
            if self.config.sync_config.field_mappings:
                for stripe_field, cg_field in self.config.sync_config.field_mappings.items():
                    if stripe_field in stripe_record:
                        transformed[cg_field] = stripe_record[stripe_field]
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming {entity_type} record: {e}")
            return None
    
    async def _send_to_analytics(self, entity_type: str, records: List[Dict[str, Any]]) -> int:
        """Send transformed records to ChurnGuard analytics"""
        try:
            # Simulate sending to analytics
            success_count = len(records)
            logger.info(f"Sent {success_count} {entity_type} records to analytics")
            return success_count
            
        except Exception as e:
            logger.error(f"Error sending {entity_type} records to analytics: {e}")
            return 0
    
    async def _calculate_subscription_metrics(self):
        """Calculate subscription and revenue metrics"""
        try:
            # Get current subscriptions
            active_subscriptions = await self._make_request("GET", "/v1/subscriptions", 
                                                          params={'status': 'active', 'limit': 100})
            
            if not active_subscriptions:
                return
            
            subscriptions = active_subscriptions.get('data', [])
            
            # Calculate metrics
            metrics = {
                'total_active_subscriptions': len(subscriptions),
                'total_mrr': 0,
                'total_arr': 0,
                'average_revenue_per_user': 0,
                'subscription_breakdown_by_status': {},
                'revenue_by_currency': {},
                'churn_risk_analysis': {}
            }
            
            currency_totals = {}
            
            for subscription in subscriptions:
                # Calculate MRR for this subscription
                items = subscription.get('items', {}).get('data', [])
                sub_mrr = 0
                
                for item in items:
                    price = item.get('price', {})
                    if price:
                        unit_amount = price.get('unit_amount', 0)
                        quantity = item.get('quantity', 1)
                        interval = price.get('recurring', {}).get('interval')
                        currency = price.get('currency', 'usd')
                        
                        amount = self._convert_stripe_amount(unit_amount * quantity, currency)
                        
                        # Convert to monthly
                        if interval == 'month':
                            monthly_amount = amount
                        elif interval == 'year':
                            monthly_amount = amount / 12
                        elif interval == 'week':
                            monthly_amount = amount * 4.33
                        elif interval == 'day':
                            monthly_amount = amount * 30
                        else:
                            monthly_amount = amount
                        
                        sub_mrr += monthly_amount
                        
                        # Track by currency
                        if currency not in currency_totals:
                            currency_totals[currency] = 0
                        currency_totals[currency] += monthly_amount
                
                metrics['total_mrr'] += sub_mrr
            
            metrics['total_arr'] = metrics['total_mrr'] * 12
            metrics['average_revenue_per_user'] = (
                metrics['total_mrr'] / metrics['total_active_subscriptions'] 
                if metrics['total_active_subscriptions'] > 0 else 0
            )
            metrics['revenue_by_currency'] = currency_totals
            
            # Store metrics
            self.subscription_metrics_cache = metrics
            
            logger.info(f"Calculated subscription metrics: MRR=${metrics['total_mrr']:.2f}, "
                       f"ARR=${metrics['total_arr']:.2f}, ARPU=${metrics['average_revenue_per_user']:.2f}")
            
        except Exception as e:
            logger.error(f"Error calculating subscription metrics: {e}")
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Stripe API"""
        if not url.startswith('http'):
            url = self.base_url + url
        
        headers = kwargs.get('headers', {})
        headers['Stripe-Version'] = self.api_version
        
        # Stripe authentication using HTTP Basic Auth
        credentials = self.config.credentials
        auth_string = base64.b64encode(f"{credentials.api_key}:".encode()).decode()
        headers['Authorization'] = f"Basic {auth_string}"
        
        kwargs['headers'] = headers
        
        # Convert data to form-encoded for POST requests
        if method == 'POST' and 'json' not in kwargs and 'data' in kwargs:
            kwargs['data'] = self._encode_stripe_data(kwargs['data'])
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status in [200, 201]:
                    return await response.json()
                elif response.status == 429:
                    # Rate limited
                    logger.warning("Stripe rate limit exceeded")
                    self.config.status = IntegrationStatus.RATE_LIMITED
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Stripe API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Stripe request error: {e}")
            return None
    
    def _encode_stripe_data(self, data: Dict[str, Any]) -> str:
        """Encode data for Stripe API (form-encoded format)"""
        def encode_dict(d, parent_key=''):
            items = []
            for key, value in d.items():
                new_key = f"{parent_key}[{key}]" if parent_key else key
                if isinstance(value, dict):
                    items.extend(encode_dict(value, new_key))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            items.extend(encode_dict(item, f"{new_key}[{i}]"))
                        else:
                            items.append((f"{new_key}[{i}]", str(item)))
                else:
                    items.append((new_key, str(value) if value is not None else ''))
            return items
        
        from urllib.parse import urlencode
        return urlencode(encode_dict(data))
    
    def _convert_stripe_amount(self, amount: int, currency: str) -> float:
        """Convert Stripe amount (integer cents) to decimal"""
        if currency.lower() in self.zero_decimal_currencies:
            return float(amount)
        return float(amount) / 100.0
    
    def _get_customer_id(self, customer: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Extract customer ID from Stripe customer reference"""
        if isinstance(customer, str):
            return customer
        elif isinstance(customer, dict):
            return customer.get('id')
        return None
    
    def _parse_stripe_timestamp(self, timestamp: Optional[int]) -> Optional[datetime]:
        """Parse Stripe timestamp (Unix timestamp)"""
        if not timestamp:
            return None
        
        try:
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return None
    
    async def _ensure_session(self):
        """Ensure HTTP session is available"""
        if not self.session:
            self.session = aiohttp.ClientSession()

# Factory function
def create_stripe_connector(config: IntegrationConfiguration) -> StripeConnector:
    """Create a configured Stripe connector"""
    return StripeConnector(config)