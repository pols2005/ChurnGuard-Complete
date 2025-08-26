# ChurnGuard Epic 5: Enterprise Integration & Data Connectors - Complete Guide

## 🚀 Overview

Epic 5 delivers comprehensive enterprise integration capabilities, enabling ChurnGuard to seamlessly connect with external systems and data sources. This epic provides robust data ingestion, real-time processing, and unified management of all integration workflows.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Integration Engine](#core-integration-engine)
- [Supported Connectors](#supported-connectors)
- [Real-Time Data Ingestion](#real-time-data-ingestion)
- [Streaming Pipelines](#streaming-pipelines)
- [Integration Dashboard](#integration-dashboard)
- [Configuration Guide](#configuration-guide)
- [API Reference](#api-reference)
- [Deployment Instructions](#deployment-instructions)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

## 🏗️ Architecture Overview

Epic 5 follows a layered architecture designed for scalability, reliability, and extensibility:

```
ChurnGuard Integration Platform (Epic 5)
├── Integration Engine (Core Framework)
│   ├── Connector SDK
│   ├── Authentication Manager
│   ├── Rate Limiting
│   ├── Sync Management
│   └── Error Handling
├── Data Connectors
│   ├── CRM (Salesforce, HubSpot)
│   ├── Payment (Stripe)
│   ├── Database (MySQL, PostgreSQL, MongoDB)
│   ├── Email Marketing (Mailchimp, SendGrid)
│   └── Custom Connectors
├── Real-Time Ingestion
│   ├── Webhook Processing
│   ├── REST API Ingestion
│   ├── Event Validation
│   └── Duplicate Detection
├── Streaming Pipelines
│   ├── Kafka Integration
│   ├── Redis Streams
│   ├── WebSocket Streams
│   └── Custom Streams
├── Management Dashboard
│   ├── Real-Time Monitoring
│   ├── Configuration Management
│   ├── Health Checks
│   └── Alert System
└── Analytics Integration
    ├── Data Transformation
    ├── Schema Validation
    └── ChurnGuard Analytics API
```

## 🔧 Core Integration Engine

### Location: `server/integrations/core/integration_engine.py`

The Integration Engine provides the foundation for all data connections:

#### Key Features

1. **Unified Integration Management**
   - Centralized configuration and lifecycle management
   - Multi-tenant isolation and security
   - Automatic credential rotation and management

2. **Flexible Synchronization Modes**
   - Full sync: Complete data refresh
   - Incremental: Only new/changed data
   - Real-time: Continuous streaming
   - Scheduled: Periodic batch sync

3. **Advanced Error Handling**
   - Automatic retry with exponential backoff
   - Circuit breaker patterns
   - Comprehensive error logging and alerting

4. **Performance Optimization**
   - Connection pooling and reuse
   - Intelligent batching and pagination
   - Rate limiting compliance

### Basic Usage

```python
from server.integrations.core.integration_engine import (
    IntegrationEngine, IntegrationConfiguration, IntegrationCredentials,
    IntegrationType, DataSyncMode
)

# Initialize engine
engine = IntegrationEngine()

# Create integration configuration
config = IntegrationConfiguration(
    integration_id="salesforce_main",
    organization_id="org_123",
    integration_name="Salesforce CRM",
    integration_type=IntegrationType.CRM,
    provider_name="salesforce",
    credentials=IntegrationCredentials(
        credential_type="oauth2",
        access_token="your_access_token",
        refresh_token="your_refresh_token"
    )
)

# Register integration
integration_id = await engine.register_integration(config)

# Start data synchronization
sync_id = await engine.start_sync(integration_id)

# Monitor sync status
status = await engine.get_sync_status(integration_id)
```

## 📊 Supported Connectors

### 1. Salesforce CRM Connector

**Location**: `server/integrations/connectors/salesforce_connector.py`

**Features**:
- OAuth 2.0 authentication with automatic token refresh
- SOQL query execution for flexible data retrieval
- Bulk API support for large data sets
- Real-time data sync via Salesforce Streaming API
- Comprehensive object mapping (Leads, Contacts, Accounts, Opportunities)
- Custom field support and field mapping
- Sandbox and production environment support

**Configuration Example**:
```python
salesforce_config = IntegrationConfiguration(
    integration_name="Salesforce Production",
    provider_name="salesforce",
    integration_type=IntegrationType.CRM,
    base_url="https://your-instance.salesforce.com",
    credentials=IntegrationCredentials(
        credential_type="oauth2",
        access_token="your_access_token",
        refresh_token="your_refresh_token",
        custom_fields={
            "client_id": "your_client_id",
            "client_secret": "your_client_secret",
            "instance_url": "https://your-instance.salesforce.com"
        }
    ),
    sync_config=SyncConfiguration(
        sync_mode=DataSyncMode.INCREMENTAL,
        sync_frequency=3600,  # 1 hour
        batch_size=1000
    )
)
```

**Supported Objects**:
- Account: Complete account information with custom fields
- Contact: Contact details with relationship mapping
- Lead: Lead management with conversion tracking
- Opportunity: Sales pipeline and deal tracking
- Case: Customer support ticket management
- Task: Activity and engagement tracking

### 2. HubSpot CRM Connector

**Location**: `server/integrations/connectors/hubspot_connector.py`

**Features**:
- OAuth 2.0 and API Key authentication
- CRM objects sync (Contacts, Companies, Deals, Tickets)
- Custom properties and fields support
- Real-time webhooks for instant updates
- Association tracking between objects
- Marketing events and analytics integration

**Configuration Example**:
```python
hubspot_config = IntegrationConfiguration(
    integration_name="HubSpot CRM",
    provider_name="hubspot",
    credentials=IntegrationCredentials(
        credential_type="oauth2",
        api_key="your_api_key",
        access_token="your_access_token"
    )
)
```

### 3. Stripe Payment Processor

**Location**: `server/integrations/connectors/stripe_connector.py`

**Features**:
- Complete payment data synchronization
- Customer lifecycle and subscription analytics
- Revenue recognition and MRR calculations
- Churn analysis from subscription events
- Multi-currency support with conversion
- Webhook processing for real-time updates

**Configuration Example**:
```python
stripe_config = IntegrationConfiguration(
    integration_name="Stripe Payments",
    provider_name="stripe",
    integration_type=IntegrationType.PAYMENT,
    credentials=IntegrationCredentials(
        credential_type="api_key",
        api_key="sk_live_your_stripe_key"
    )
)
```

### 4. Database Connectors

**Location**: `server/integrations/connectors/database_connectors.py`

**Supported Databases**:
- **MySQL**: Connection pooling, incremental sync, binary log parsing
- **PostgreSQL**: Async operations, JSON/JSONB support, logical replication
- **MongoDB**: Change streams, aggregation pipelines, GridFS support

**Configuration Example**:
```python
mysql_config = IntegrationConfiguration(
    integration_name="Customer Database",
    provider_name="mysql",
    base_url="mysql.company.com:3306",
    credentials=IntegrationCredentials(
        credential_type="basic_auth",
        username="db_user",
        password="db_password",
        custom_fields={"database": "customer_data"}
    )
)
```

### 5. Email Marketing Connectors

**Location**: `server/integrations/connectors/email_marketing_connectors.py`

**Supported Platforms**:
- **Mailchimp**: Complete campaign performance analytics, contact management
- **SendGrid**: Email sending statistics, suppression list monitoring

**Configuration Example**:
```python
mailchimp_config = IntegrationConfiguration(
    integration_name="Mailchimp Campaigns",
    provider_name="mailchimp",
    credentials=IntegrationCredentials(
        credential_type="api_key",
        api_key="your_mailchimp_api_key"
    )
)
```

## 🔄 Real-Time Data Ingestion

### Location: `server/integrations/api/webhook_ingestion.py`

The webhook ingestion system processes real-time events from external systems:

### Key Features

1. **Multi-Provider Webhook Support**
   - Provider-specific webhook processing
   - Signature validation for security
   - Automatic event deduplication

2. **REST API Data Ingestion**
   - Scheduled API polling
   - Configurable data extraction
   - Authentication support (OAuth, API keys)

3. **Advanced Processing**
   - Rate limiting and payload validation
   - Event filtering and transformation
   - Retry mechanisms with exponential backoff

### Webhook Setup

```python
from server.integrations.api.webhook_ingestion import start_webhook_server

# Start webhook server
await start_webhook_server(host="0.0.0.0", port=8080)

# Webhook endpoints will be available at:
# POST /webhooks/stripe/{organization_id}
# POST /webhooks/salesforce/{organization_id}
# POST /webhooks/hubspot/{organization_id}
```

### API Ingestion Rules

```python
from server.integrations.api.webhook_ingestion import APIIngestionRule

rule = APIIngestionRule(
    rule_id="customer_api_sync",
    organization_id="org_123",
    name="Customer API Sync",
    description="Sync customer data from external API",
    endpoint_url="https://api.external.com/customers",
    http_method="GET",
    headers={"Authorization": "Bearer your_token"},
    response_format="json",
    data_path="customers",
    sync_frequency=1800,  # 30 minutes
    field_mappings={
        "customer_id": "external_customer_id",
        "email": "customer_email",
        "created_at": "registration_date"
    }
)
```

## 🌊 Streaming Pipelines

### Location: `server/integrations/streaming/data_pipelines.py`

Real-time streaming data processing for high-volume, low-latency scenarios:

### Supported Stream Types

1. **Apache Kafka**
   - High-throughput message processing
   - Partition-based scaling
   - Consumer group management

2. **Redis Streams**
   - Lightweight streaming with Redis
   - Consumer group support
   - Message acknowledgment

3. **WebSocket Streams**
   - Real-time bidirectional communication
   - Custom message protocols
   - Automatic reconnection

### Stream Configuration

```python
from server.integrations.streaming.data_pipelines import (
    StreamConfiguration, StreamType, DataFormat, create_kafka_stream
)

# Create Kafka stream
stream_config = StreamConfiguration(
    stream_id="user_events_stream",
    organization_id="org_123",
    name="User Events Stream",
    stream_type=StreamType.KAFKA,
    topics=["user.events", "user.actions"],
    data_format=DataFormat.JSON,
    processing_mode=ProcessingMode.AT_LEAST_ONCE,
    batch_size=100,
    connection_config={
        "bootstrap_servers": "kafka.company.com:9092"
    },
    field_mappings={
        "user_id": "customer_id",
        "event_name": "action_type",
        "timestamp": "event_timestamp"
    }
)

# Start stream processing
await streaming_manager.create_stream(stream_config)
```

### Stream Metrics

```python
# Get stream metrics
metrics = await streaming_manager.get_stream_metrics("user_events_stream")

print(f"Messages/sec: {metrics.messages_per_second}")
print(f"Processing time: {metrics.avg_processing_time_ms}ms")
print(f"Error rate: {metrics.error_rate}")
```

## 📊 Integration Dashboard

### Location: `server/integrations/dashboard/integration_dashboard.py`

Comprehensive management interface for all integrations:

### Key Features

1. **Real-Time Monitoring**
   - Integration health and status
   - Performance metrics and trends
   - Error tracking and diagnostics

2. **Configuration Management**
   - Integration setup and configuration
   - Sync scheduling and management
   - Credential management

3. **Alert System**
   - Automated health checks
   - Configurable alert thresholds
   - Multi-channel notifications

### Starting the Dashboard

```python
from server.integrations.dashboard.integration_dashboard import start_integration_dashboard

# Start dashboard server
await start_integration_dashboard(host="0.0.0.0", port=8090)

# Dashboard will be available at:
# http://localhost:8090/dashboard
```

### Dashboard API Endpoints

- `GET /api/dashboard/metrics` - Overall system metrics
- `GET /api/dashboard/integrations` - Integration summaries
- `GET /api/dashboard/integration/{id}` - Detailed integration info
- `GET /api/dashboard/alerts` - Current alerts
- `POST /api/integrations/{id}/sync` - Start integration sync
- `GET /api/integrations/{id}/sync/status` - Sync status

## ⚙️ Configuration Guide

### Integration Configuration Structure

```python
@dataclass
class IntegrationConfiguration:
    integration_id: str
    organization_id: str
    integration_name: str
    integration_type: IntegrationType
    provider_name: str
    
    # Status and credentials
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    credentials: Optional[IntegrationCredentials] = None
    
    # Sync configuration
    sync_config: SyncConfiguration = field(default_factory=SyncConfiguration)
    
    # Connection settings
    base_url: str = ""
    api_version: str = ""
    webhook_url: str = ""
    
    # Data mapping and transformation
    entity_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: List[str] = field(default_factory=list)
```

### Sync Configuration Options

```python
@dataclass
class SyncConfiguration:
    sync_mode: DataSyncMode
    sync_frequency: int = 3600  # seconds
    batch_size: int = 1000
    retry_attempts: int = 3
    retry_backoff: int = 60  # seconds
    
    # Data filtering and mapping
    data_filters: Dict[str, Any] = field(default_factory=dict)
    field_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Incremental sync settings
    incremental_field: str = "updated_at"
    last_sync_timestamp: Optional[datetime] = None
    
    # Rate limiting
    requests_per_minute: int = 60
    concurrent_requests: int = 5
```

### Environment Variables

```bash
# Integration Engine
INTEGRATION_ENGINE_LOG_LEVEL=INFO
INTEGRATION_DEFAULT_RETRY_ATTEMPTS=3
INTEGRATION_DEFAULT_BATCH_SIZE=1000

# Webhook Server
WEBHOOK_SERVER_HOST=0.0.0.0
WEBHOOK_SERVER_PORT=8080
WEBHOOK_RATE_LIMIT_PER_MINUTE=1000
WEBHOOK_MAX_PAYLOAD_SIZE=1048576

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8090
DASHBOARD_UPDATE_INTERVAL=60

# Security
INTEGRATION_ENCRYPTION_KEY=your_encryption_key_here
WEBHOOK_SIGNATURE_VALIDATION=true
API_RATE_LIMITING_ENABLED=true
```

## 🔗 API Reference

### Integration Management APIs

#### Create Integration
```http
POST /api/integrations
Content-Type: application/json

{
    "organization_id": "org_123",
    "integration_name": "Salesforce Production",
    "provider_name": "salesforce",
    "integration_type": "crm",
    "credentials": {
        "credential_type": "oauth2",
        "access_token": "your_access_token",
        "refresh_token": "your_refresh_token"
    },
    "sync_config": {
        "sync_mode": "incremental",
        "sync_frequency": 3600,
        "batch_size": 1000
    }
}
```

#### Start Integration Sync
```http
POST /api/integrations/{integration_id}/sync

Response:
{
    "sync_id": "sync_456",
    "status": "started",
    "estimated_duration": "10 minutes"
}
```

#### Get Sync Status
```http
GET /api/integrations/{integration_id}/sync/status

Response:
{
    "integration_id": "int_123",
    "status": "syncing",
    "progress": 0.75,
    "records_processed": 7500,
    "estimated_remaining": "2 minutes"
}
```

### Webhook Processing APIs

#### Process Generic Webhook
```http
POST /webhooks/{provider}/{organization_id}
Content-Type: application/json

{
    "event_type": "customer.updated",
    "data": {
        "customer_id": "cust_123",
        "email": "customer@example.com",
        "updated_at": "2024-01-15T10:30:00Z"
    }
}
```

#### Create Webhook Endpoint
```http
POST /api/webhooks/endpoints
Content-Type: application/json

{
    "organization_id": "org_123",
    "url_path": "/webhooks/custom/org_123",
    "provider": "custom",
    "secret_key": "webhook_secret",
    "allowed_events": ["user.created", "user.updated"]
}
```

### Streaming Pipeline APIs

#### Create Stream
```http
POST /api/streaming/streams
Content-Type: application/json

{
    "organization_id": "org_123",
    "name": "User Events Stream",
    "stream_type": "kafka",
    "topics": ["user.events"],
    "connection_config": {
        "bootstrap_servers": "kafka.company.com:9092"
    },
    "processing_config": {
        "batch_size": 100,
        "processing_mode": "at_least_once"
    }
}
```

#### Get Stream Metrics
```http
GET /api/streaming/streams/{stream_id}/metrics

Response:
{
    "stream_id": "stream_123",
    "messages_per_second": 150.5,
    "avg_processing_time_ms": 12.3,
    "error_rate": 0.01,
    "buffer_utilization": 0.45
}
```

## 🚀 Deployment Instructions

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8080 8090

# Start services
CMD ["python", "-m", "server.integrations.main"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  integration-engine:
    build: .
    ports:
      - "8080:8080"  # Webhook server
      - "8090:8090"  # Dashboard
    environment:
      - WEBHOOK_SERVER_HOST=0.0.0.0
      - DASHBOARD_HOST=0.0.0.0
      - INTEGRATION_ENCRYPTION_KEY=${ENCRYPTION_KEY}
    volumes:
      - ./config:/app/config
    depends_on:
      - redis
      - kafka
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

volumes:
  redis_data:
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churnguard-integrations
  namespace: churnguard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: churnguard-integrations
  template:
    metadata:
      labels:
        app: churnguard-integrations
    spec:
      containers:
      - name: integration-engine
        image: churnguard/integrations:latest
        ports:
        - containerPort: 8080
        - containerPort: 8090
        env:
        - name: WEBHOOK_SERVER_HOST
          value: "0.0.0.0"
        - name: DASHBOARD_HOST
          value: "0.0.0.0"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /webhooks/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/dashboard/health
            port: 8090
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📈 Monitoring and Troubleshooting

### Health Monitoring

The integration system provides comprehensive health monitoring:

1. **Integration Health Scores**
   - Connection status and performance
   - Sync success rates and reliability
   - Error frequency and patterns

2. **System Metrics**
   - Overall health score calculation
   - Resource utilization tracking
   - Performance trend analysis

3. **Alert Conditions**
   - Integration failures and connection issues
   - Performance degradation
   - Rate limiting and quota exhaustion

### Common Issues and Solutions

#### Connection Failures

**Symptoms**: Integration status shows "authentication_failed" or "error"

**Solutions**:
1. Verify credentials are correct and not expired
2. Check API rate limits and quotas
3. Validate network connectivity and firewall rules
4. Review provider-specific authentication requirements

**Diagnostic Commands**:
```bash
# Test integration connection
curl -X POST http://localhost:8090/api/system/test-connections

# Check integration details
curl http://localhost:8090/api/dashboard/integration/{integration_id}

# View recent alerts
curl http://localhost:8090/api/dashboard/alerts
```

#### Sync Performance Issues

**Symptoms**: Slow sync times or frequent timeouts

**Solutions**:
1. Adjust batch size and concurrency settings
2. Implement incremental sync for large datasets
3. Optimize field mappings and filters
4. Review rate limiting configuration

**Performance Tuning**:
```python
# Optimize sync configuration
sync_config = SyncConfiguration(
    sync_mode=DataSyncMode.INCREMENTAL,
    batch_size=500,  # Reduce for better performance
    concurrent_requests=3,  # Limit concurrency
    requests_per_minute=120,  # Respect rate limits
    retry_attempts=2  # Reduce retry overhead
)
```

#### Webhook Processing Errors

**Symptoms**: High error rates in webhook processing

**Solutions**:
1. Verify webhook signatures and validation
2. Check payload size limits
3. Review event filtering and transformation logic
4. Monitor queue sizes and processing capacity

**Debug Webhook Issues**:
```bash
# Check webhook health
curl http://localhost:8080/webhooks/health

# Monitor webhook events
curl http://localhost:8090/api/dashboard/metrics

# Review webhook configuration
curl http://localhost:8090/api/webhooks/endpoints/{endpoint_id}
```

### Logging and Debugging

Enable detailed logging for troubleshooting:

```python
import logging

# Set up integration logging
logging.getLogger('server.integrations').setLevel(logging.DEBUG)

# Enable connector-specific logging
logging.getLogger('server.integrations.connectors.salesforce').setLevel(logging.DEBUG)

# Enable webhook processing logging
logging.getLogger('server.integrations.api.webhook_ingestion').setLevel(logging.DEBUG)
```

### Performance Optimization

1. **Connection Pooling**
   - Reuse HTTP connections across requests
   - Configure appropriate pool sizes
   - Monitor connection utilization

2. **Batch Processing**
   - Optimize batch sizes for different connectors
   - Use parallel processing where appropriate
   - Implement intelligent pagination

3. **Caching**
   - Cache frequently accessed configuration data
   - Implement response caching for read-heavy operations
   - Use Redis for distributed caching

4. **Resource Management**
   - Monitor memory usage and garbage collection
   - Configure appropriate worker pool sizes
   - Implement backpressure mechanisms

---

## 🎯 Epic 5 Summary

Epic 5: Enterprise Integration & Data Connectors delivers a comprehensive integration platform that enables ChurnGuard to seamlessly connect with external systems and process real-time data at scale. The implementation includes:

### ✅ Completed Features

1. **Core Integration Engine** - Unified framework for all integrations
2. **CRM Connectors** - Salesforce and HubSpot with full feature support
3. **Payment Processing** - Stripe integration with subscription analytics
4. **Database Connectors** - MySQL, PostgreSQL, and MongoDB support
5. **Email Marketing** - Mailchimp and SendGrid integrations
6. **Real-Time Ingestion** - Webhook and REST API data processing
7. **Streaming Pipelines** - Kafka, Redis Streams, and WebSocket support
8. **Management Dashboard** - Comprehensive monitoring and configuration interface

### 🔧 Key Technical Achievements

- **Scalable Architecture**: Microservices-based design supporting high throughput
- **Security First**: OAuth 2.0, API key management, and signature validation
- **Real-Time Processing**: Sub-second webhook processing and streaming analytics
- **Enterprise Ready**: Multi-tenant isolation, comprehensive monitoring, and alerting
- **Developer Friendly**: Extensive APIs, SDKs, and configuration options

### 📈 Business Impact

- **Reduced Integration Time**: From weeks to hours for new connector deployment
- **Improved Data Quality**: Real-time validation and transformation
- **Enhanced Visibility**: Comprehensive monitoring and health tracking
- **Operational Efficiency**: Automated sync management and error recovery
- **Scalable Growth**: Support for high-volume, real-time data processing

The ChurnGuard platform now provides enterprise-grade integration capabilities that enable customers to unify their data landscape and unlock powerful analytics insights across their entire tech stack.