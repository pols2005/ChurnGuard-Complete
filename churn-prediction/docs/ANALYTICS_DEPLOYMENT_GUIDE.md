# ChurnGuard Analytics Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Service Deployment](#service-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Scaling & Performance](#scaling--performance)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive instructions for deploying the ChurnGuard Advanced Analytics & AI Insights platform in production environments.

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer                           │
├─────────────────────────────────────────────────────────────┤
│  API Gateway (nginx/Kong)                                  │
├─────────────────────────────────────────────────────────────┤
│  Analytics Services                                         │
│  ├── FastAPI Application Server                            │
│  ├── Real-Time Analytics Engine                            │
│  ├── Data Aggregation Pipeline                             │
│  └── Background Services                                   │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                │
│  ├── Time-Series Database (InfluxDB/TimescaleDB)           │
│  ├── Cache Layer (Redis)                                   │
│  └── Message Queue (RabbitMQ/Redis)                        │
└─────────────────────────────────────────────────────────────┘
```

## System Requirements

### Minimum Requirements (Development)
- **CPU**: 4 cores, 2.4 GHz
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04 LTS, CentOS 8, or macOS 10.15+

### Recommended Requirements (Production)
- **CPU**: 8+ cores, 3.0 GHz
- **RAM**: 32 GB
- **Storage**: 500 GB SSD (with additional storage for time-series data)
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS or CentOS 8

### Enterprise Requirements (High-Scale)
- **CPU**: 16+ cores, 3.5 GHz
- **RAM**: 64+ GB
- **Storage**: 2+ TB NVMe SSD
- **Network**: 10 Gbps
- **Database**: Dedicated database servers with clustering

### Software Dependencies
- Python 3.9+
- PostgreSQL 13+ (for TimescaleDB) or InfluxDB 2.0+
- Redis 6.0+
- Docker 20.10+ (optional)
- Docker Compose 1.29+ (optional)

## Installation

### Method 1: Docker Deployment (Recommended)

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/churnguard-analytics.git
cd churnguard-analytics
```

#### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Database Configuration
ANALYTICS_DB_BACKEND=timescaledb
TIMESCALEDB_URL=postgresql://analytics_user:secure_password@timescaledb:5432/analytics_db

# InfluxDB Alternative
# ANALYTICS_DB_BACKEND=influxdb
# INFLUXDB_URL=http://influxdb:8086
# INFLUXDB_TOKEN=your-super-secret-admin-token
# INFLUXDB_ORG=churnguard
# INFLUXDB_BUCKET=analytics

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
API_KEY_HEADER=X-API-Key

# Performance Settings
ANALYTICS_MAX_WORKERS=4
ANALYTICS_CACHE_TTL=300
ANALYTICS_MONITORING_INTERVAL=60

# Resource Limits
MAX_POINTS_PER_METRIC=50000
MAX_INSIGHTS_PER_ORG=100
MAX_RECOMMENDATIONS=50
```

#### 3. Deploy with Docker Compose
```bash
# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f analytics-api
```

#### 4. Initialize Database
```bash
# Run database migrations
docker-compose exec analytics-api python -m alembic upgrade head

# Create initial data
docker-compose exec analytics-api python scripts/init_database.py
```

### Method 2: Manual Installation

#### 1. Install System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3.9-dev \
    postgresql-13 postgresql-contrib redis-server \
    nginx supervisor git curl

# CentOS/RHEL
sudo dnf install -y python39 python39-devel postgresql13-server \
    redis nginx supervisor git curl
```

#### 2. Setup Python Environment
```bash
# Create virtual environment
python3.9 -m venv /opt/churnguard-analytics/venv
source /opt/churnguard-analytics/venv/bin/activate

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 3. Setup TimescaleDB
```bash
# Install TimescaleDB extension
sudo apt install -y timescaledb-2-postgresql-13

# Configure PostgreSQL
sudo -u postgres createuser -d -r -s analytics_user
sudo -u postgres createdb -O analytics_user analytics_db
sudo -u postgres psql -d analytics_db -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Set password
sudo -u postgres psql -c "ALTER USER analytics_user PASSWORD 'secure_password';"
```

#### 4. Configure Services
Create systemd service files:

**/etc/systemd/system/churnguard-analytics.service**
```ini
[Unit]
Description=ChurnGuard Analytics API
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=forking
User=churnguard
Group=churnguard
WorkingDirectory=/opt/churnguard-analytics
Environment=PATH=/opt/churnguard-analytics/venv/bin
ExecStart=/opt/churnguard-analytics/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/churnguard-analytics-worker.service**
```ini
[Unit]
Description=ChurnGuard Analytics Background Worker
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=churnguard
Group=churnguard
WorkingDirectory=/opt/churnguard-analytics
Environment=PATH=/opt/churnguard-analytics/venv/bin
ExecStart=/opt/churnguard-analytics/venv/bin/python -m server.workers.analytics_worker
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 5. Start Services
```bash
# Enable and start services
sudo systemctl enable churnguard-analytics churnguard-analytics-worker
sudo systemctl start churnguard-analytics churnguard-analytics-worker

# Check status
sudo systemctl status churnguard-analytics
```

### Method 3: Kubernetes Deployment

#### 1. Create Kubernetes Manifests

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: churnguard-analytics
  labels:
    name: churnguard-analytics
```

**configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: analytics-config
  namespace: churnguard-analytics
data:
  ANALYTICS_DB_BACKEND: "timescaledb"
  REDIS_URL: "redis://redis:6379/0"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  ANALYTICS_MAX_WORKERS: "4"
  ANALYTICS_CACHE_TTL: "300"
  MAX_POINTS_PER_METRIC: "50000"
```

**secret.yaml**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: analytics-secrets
  namespace: churnguard-analytics
type: Opaque
data:
  TIMESCALEDB_URL: <base64-encoded-database-url>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  API_KEY: <base64-encoded-api-key>
```

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-api
  namespace: churnguard-analytics
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-api
  template:
    metadata:
      labels:
        app: analytics-api
    spec:
      containers:
      - name: analytics-api
        image: churnguard/analytics:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: analytics-config
        - secretRef:
            name: analytics-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: analytics-api-service
  namespace: churnguard-analytics
spec:
  selector:
    app: analytics-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: analytics-ingress
  namespace: churnguard-analytics
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - analytics.churnguard.com
    secretName: analytics-tls
  rules:
  - host: analytics.churnguard.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: analytics-api-service
            port:
              number: 80
```

#### 2. Deploy to Kubernetes
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n churnguard-analytics
kubectl get services -n churnguard-analytics

# View logs
kubectl logs -f deployment/analytics-api -n churnguard-analytics
```

## Configuration

### Application Configuration

**config/analytics.yaml**
```yaml
database:
  backend: "timescaledb"  # timescaledb, influxdb, memory
  connection_pool_size: 20
  connection_timeout: 30
  query_timeout: 60
  
  # TimescaleDB specific
  timescaledb:
    host: "localhost"
    port: 5432
    database: "analytics_db"
    username: "analytics_user"
    password: "secure_password"
    ssl_mode: "require"
    
  # InfluxDB specific  
  influxdb:
    url: "http://localhost:8086"
    token: "your-token"
    org: "churnguard"
    bucket: "analytics"

redis:
  url: "redis://localhost:6379/0"
  connection_pool_size: 10
  socket_timeout: 5
  retry_on_timeout: true

real_time_engine:
  max_points_per_metric: 10000
  processing_interval_seconds: 1
  cleanup_interval_seconds: 300
  performance_logging: true
  
  alert_thresholds:
    churn_risk_score:
      above: 0.8
      severity: "high"
    customer_activity:
      below: 50
      severity: "medium"

data_aggregation:
  max_workers: 4
  batch_size: 1000
  processing_interval_seconds: 60
  retention_policy:
    raw_data: "7d"
    hourly_aggregates: "30d"
    daily_aggregates: "365d"
    
anomaly_detection:
  monitoring_interval_seconds: 60
  default_sensitivity: 2.0
  ensemble_voting_threshold: 2
  
  methods:
    statistical:
      enabled: true
      default_method: "zscore"
    isolation_forest:
      enabled: true
      contamination: 0.1
    local_outlier_factor:
      enabled: true
      n_neighbors: 20

insights:
  max_insights_per_org: 100
  confidence_threshold: 0.6
  cache_ttl_seconds: 300
  narrative_templates: "templates/insights/"
  
recommendations:
  max_recommendations: 50
  confidence_threshold: 0.5
  roi_calculation_enabled: true
  business_rules: "rules/recommendations.json"

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  timeout: 60
  cors_origins: ["https://app.churnguard.com"]
  
  rate_limits:
    default: "1000/hour"
    premium: "10000/hour"
    enterprise: "100000/hour"

logging:
  level: "INFO"
  format: "structured"
  file: "/var/log/churnguard-analytics/app.log"
  max_size_mb: 100
  backup_count: 5
  
monitoring:
  metrics_enabled: true
  health_check_interval: 30
  performance_monitoring: true
  alert_on_errors: true
```

### Environment Variables

Create environment-specific configurations:

**environments/production.env**
```bash
# Database
ANALYTICS_DB_BACKEND=timescaledb
TIMESCALEDB_URL=postgresql://analytics_user:${DB_PASSWORD}@${DB_HOST}:5432/analytics_db?sslmode=require

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:6379/0

# Application
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=${JWT_SECRET}
API_KEY_HEADER=X-API-Key
CORS_ORIGINS=https://app.churnguard.com,https://dashboard.churnguard.com

# Performance
ANALYTICS_MAX_WORKERS=8
ANALYTICS_CACHE_TTL=300
MAX_POINTS_PER_METRIC=100000

# Features
ANALYTICS_MONITORING_ENABLED=true
ANOMALY_DETECTION_ENABLED=true
INSIGHTS_GENERATION_ENABLED=true
RECOMMENDATIONS_ENABLED=true

# External Services
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=587
SMTP_USERNAME=${SMTP_USERNAME}
SMTP_PASSWORD=${SMTP_PASSWORD}

SLACK_WEBHOOK_URL=${SLACK_WEBHOOK}
```

## Database Setup

### TimescaleDB Setup (Recommended)

#### 1. Install TimescaleDB
```bash
# Add TimescaleDB repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update

# Install TimescaleDB
sudo apt install -y timescaledb-2-postgresql-13 timescaledb-tools
```

#### 2. Configure PostgreSQL
```bash
# Tune PostgreSQL for TimescaleDB
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 3. Setup Database
```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Create user and database
CREATE USER analytics_user WITH PASSWORD 'secure_password';
CREATE DATABASE analytics_db OWNER analytics_user;

-- Connect to analytics database
\c analytics_db

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE analytics_db TO analytics_user;
GRANT ALL ON SCHEMA public TO analytics_user;
```

#### 4. Initialize Schema
```bash
# Run database migrations
python -m alembic upgrade head

# Or manually create tables
python scripts/create_timescale_tables.py
```

**scripts/create_timescale_tables.py**
```python
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def create_timescale_schema():
    conn = psycopg2.connect(os.getenv('TIMESCALEDB_URL'))
    
    with conn.cursor() as cursor:
        # Create time-series data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_series_data (
                timestamp TIMESTAMPTZ NOT NULL,
                metric_name TEXT NOT NULL,
                organization_id UUID NOT NULL,
                value DOUBLE PRECISION NOT NULL,
                tags JSONB,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create hypertable
        cursor.execute("""
            SELECT create_hypertable(
                'time_series_data', 
                'timestamp',
                chunk_time_interval => INTERVAL '1 hour',
                if_not_exists => TRUE
            );
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ts_metric_org_time 
            ON time_series_data(metric_name, organization_id, timestamp DESC);
            
            CREATE INDEX IF NOT EXISTS idx_ts_org_time 
            ON time_series_data(organization_id, timestamp DESC);
            
            CREATE INDEX IF NOT EXISTS idx_ts_tags 
            ON time_series_data USING GIN (tags);
        """)
        
        # Create compression policy
        cursor.execute("""
            SELECT add_compression_policy('time_series_data', INTERVAL '7 days');
        """)
        
        # Create retention policy
        cursor.execute("""
            SELECT add_retention_policy('time_series_data', INTERVAL '1 year');
        """)
        
        # Create continuous aggregates
        cursor.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_metrics
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('1 hour', timestamp) AS bucket,
                metric_name,
                organization_id,
                COUNT(*) as count,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                STDDEV(value) as std_value
            FROM time_series_data
            GROUP BY bucket, metric_name, organization_id
            WITH NO DATA;
        """)
        
        # Add refresh policy
        cursor.execute("""
            SELECT add_continuous_aggregate_policy(
                'hourly_metrics',
                start_offset => INTERVAL '1 day',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour'
            );
        """)
        
    conn.commit()
    conn.close()
    print("TimescaleDB schema created successfully")

if __name__ == "__main__":
    create_timescale_schema()
```

### InfluxDB Setup (Alternative)

#### 1. Install InfluxDB
```bash
# Download and install InfluxDB
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
echo "deb https://repos.influxdata.com/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt update && sudo apt install -y influxdb2
```

#### 2. Configure InfluxDB
```bash
# Start InfluxDB
sudo systemctl enable influxdb
sudo systemctl start influxdb

# Setup initial user and organization
influx setup \
  --username admin \
  --password secure_password_here \
  --org churnguard \
  --bucket analytics \
  --retention 8760h \
  --force

# Create API token
influx auth create \
  --org churnguard \
  --all-access \
  --description "Analytics API Token"
```

#### 3. Configure Retention Policies
```bash
# Create bucket with retention policy
influx bucket create \
  --name analytics_raw \
  --org churnguard \
  --retention 168h  # 7 days

influx bucket create \
  --name analytics_aggregated \
  --org churnguard \
  --retention 8760h  # 1 year
```

### Redis Setup

#### 1. Install and Configure Redis
```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis
sudo tee /etc/redis/redis.conf > /dev/null <<EOF
# Basic configuration
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 300

# Memory configuration
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Security
requirepass your_redis_password

# Log level
loglevel notice
logfile /var/log/redis/redis-server.log
EOF

# Restart Redis
sudo systemctl restart redis-server
```

#### 2. Redis Clustering (High Availability)
```bash
# Create Redis cluster configuration
mkdir -p /etc/redis/cluster

# Node 1 configuration
sudo tee /etc/redis/cluster/redis-7001.conf > /dev/null <<EOF
port 7001
cluster-enabled yes
cluster-config-file nodes-7001.conf
cluster-node-timeout 5000
appendonly yes
EOF

# Create systemd service for cluster nodes
sudo tee /etc/systemd/system/redis-cluster@.service > /dev/null <<EOF
[Unit]
Description=Redis cluster node %i
After=network.target

[Service]
Type=forking
ExecStart=/usr/bin/redis-server /etc/redis/cluster/redis-%i.conf
PIDFile=/var/run/redis/redis-%i.pid
TimeoutStopSec=0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start cluster nodes
sudo systemctl enable redis-cluster@7001
sudo systemctl start redis-cluster@7001
```

## Service Deployment

### Application Server Setup

#### 1. FastAPI Application
**main.py**
```python
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from server.analytics.insight_generator import get_insight_generator
from server.analytics.recommendation_engine import get_recommendation_engine
from server.analytics.anomaly_detection import get_anomaly_system
from server.analytics.real_time_engine import get_analytics_engine
from server.api.routes import analytics_router, insights_router, recommendations_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/churnguard-analytics/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ChurnGuard Analytics Platform")
    
    # Initialize services
    get_analytics_engine()
    get_anomaly_system()
    get_insight_generator()
    get_recommendation_engine()
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")

app = FastAPI(
    title="ChurnGuard Analytics Platform",
    description="Advanced Analytics & AI Insights API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.churnguard.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(insights_router, prefix="/insights", tags=["Insights"]) 
app.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])

@app.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        # Check all service health
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "analytics_engine": "healthy",
                "anomaly_detection": "healthy", 
                "insight_generator": "healthy",
                "recommendation_engine": "healthy"
            }
        }
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info",
        access_log=True
    )
```

#### 2. Background Workers
**workers/analytics_worker.py**
```python
import asyncio
import logging
import signal
import sys
from datetime import datetime

from server.analytics.data_aggregator import get_aggregation_pipeline
from server.analytics.anomaly_detection import get_anomaly_system
from server.analytics.real_time_engine import get_analytics_engine

logger = logging.getLogger(__name__)

class AnalyticsWorker:
    def __init__(self):
        self.running = False
        self.aggregation_pipeline = get_aggregation_pipeline()
        self.anomaly_system = get_anomaly_system()
        self.analytics_engine = get_analytics_engine()
    
    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self):
        """Start background worker"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("Starting ChurnGuard Analytics Worker")
        
        # Start all services
        self.aggregation_pipeline.start()
        self.anomaly_system.start_monitoring()
        
        self.running = True
        
        try:
            while self.running:
                # Perform periodic maintenance tasks
                await self.run_maintenance_tasks()
                await asyncio.sleep(300)  # 5 minutes
                
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            # Cleanup
            self.aggregation_pipeline.stop()
            self.anomaly_system.stop_monitoring()
            logger.info("Analytics worker stopped")
    
    async def run_maintenance_tasks(self):
        """Run periodic maintenance tasks"""
        try:
            # Log performance metrics
            engine_metrics = self.analytics_engine.get_performance_metrics()
            logger.info(f"Analytics Engine Metrics: {engine_metrics}")
            
            pipeline_stats = self.aggregation_pipeline.get_pipeline_stats()
            logger.info(f"Aggregation Pipeline Stats: {pipeline_stats}")
            
        except Exception as e:
            logger.error(f"Maintenance task error: {e}")

async def main():
    worker = AnalyticsWorker()
    await worker.start()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
```

### Load Balancer Configuration

#### Nginx Configuration
**/etc/nginx/sites-available/churnguard-analytics**
```nginx
upstream analytics_backend {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=health:10m rate=10r/s;

server {
    listen 80;
    server_name analytics.churnguard.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name analytics.churnguard.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/analytics.churnguard.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/analytics.churnguard.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Logging
    access_log /var/log/nginx/analytics.access.log;
    error_log /var/log/nginx/analytics.error.log;
    
    # Health check endpoint (no rate limiting)
    location /health {
        limit_req zone=health burst=5 nodelay;
        proxy_pass http://analytics_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check specific settings
        proxy_connect_timeout 5s;
        proxy_read_timeout 10s;
    }
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://analytics_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_read_timeout 300s;
        proxy_send_timeout 30s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
        proxy_busy_buffers_size 16k;
        
        # Keep-alive
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # WebSocket endpoints (for real-time features)
    location /ws/ {
        proxy_pass http://analytics_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/churnguard-analytics/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/churnguard-analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Monitoring & Maintenance

### Prometheus Monitoring

#### 1. Add Prometheus Metrics to Application
**monitoring/prometheus.py**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Metrics
REQUEST_COUNT = Counter(
    'churnguard_requests_total', 
    'Total requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'churnguard_request_duration_seconds',
    'Request duration'
)

ACTIVE_CONNECTIONS = Gauge(
    'churnguard_active_connections',
    'Active connections'
)

INSIGHTS_GENERATED = Counter(
    'churnguard_insights_generated_total',
    'Total insights generated',
    ['organization_id', 'severity']
)

ANOMALIES_DETECTED = Counter(
    'churnguard_anomalies_detected_total',
    'Total anomalies detected',
    ['organization_id', 'severity', 'method']
)

DATABASE_QUERY_DURATION = Histogram(
    'churnguard_database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

class PrometheusMetrics:
    @staticmethod
    def track_request(method: str, endpoint: str, status: int, duration: float):
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.observe(duration)
    
    @staticmethod
    def track_insight_generated(org_id: str, severity: str):
        INSIGHTS_GENERATED.labels(organization_id=org_id, severity=severity).inc()
    
    @staticmethod
    def track_anomaly_detected(org_id: str, severity: str, method: str):
        ANOMALIES_DETECTED.labels(
            organization_id=org_id, 
            severity=severity, 
            method=method
        ).inc()
    
    @staticmethod
    def track_database_query(query_type: str, duration: float):
        DATABASE_QUERY_DURATION.labels(query_type=query_type).observe(duration)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### 2. Prometheus Configuration
**prometheus.yml**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'churnguard-analytics'
    static_configs:
      - targets: ['analytics-api:8000']
    scrape_interval: 15s
    metrics_path: /metrics
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### 3. Grafana Dashboard
**grafana/dashboards/churnguard-analytics.json**
```json
{
  "dashboard": {
    "id": null,
    "title": "ChurnGuard Analytics Dashboard",
    "tags": ["churnguard", "analytics"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(churnguard_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(churnguard_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Insights Generated",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(churnguard_insights_generated_total[1h])",
            "legendFormat": "Last Hour"
          }
        ]
      },
      {
        "title": "Anomalies Detected",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(churnguard_anomalies_detected_total[1h])",
            "legendFormat": "Last Hour"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### Log Management

#### 1. Structured Logging Configuration
**logging_config.yaml**
```yaml
version: 1
disable_existing_loggers: False

formatters:
  standard:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  json:
    format: "%(asctime)s"
    class: pythonjsonlogger.jsonlogger.JsonFormatter

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
    
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /var/log/churnguard-analytics/app.log
    maxBytes: 104857600  # 100MB
    backupCount: 10
    
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: /var/log/churnguard-analytics/error.log
    maxBytes: 104857600
    backupCount: 5

loggers:
  server.analytics:
    level: INFO
    handlers: [console, file]
    propagate: no
    
  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: no

root:
  level: INFO
  handlers: [console, file, error_file]
```

#### 2. ELK Stack Integration
**filebeat.yml**
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/churnguard-analytics/*.log
  json.keys_under_root: true
  json.add_error_key: true
  fields:
    service: churnguard-analytics
    environment: production

output.logstash:
  hosts: ["logstash:5044"]

processors:
- add_host_metadata:
    when.not.contains.tags: forwarded
- add_docker_metadata: ~
```

### Backup Strategy

#### 1. Database Backup Script
**scripts/backup_timescaledb.sh**
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/backups/timescaledb"
DB_NAME="analytics_db"
DB_USER="analytics_user"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/analytics_db_$TIMESTAMP.sql.gz"

# Create backup
echo "Starting database backup..."
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_FILE

# Check if backup was successful
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Upload to S3 (optional)
    if [ -n "$AWS_S3_BUCKET" ]; then
        aws s3 cp $BACKUP_FILE s3://$AWS_S3_BUCKET/timescaledb-backups/
        echo "Backup uploaded to S3"
    fi
    
    # Clean up old backups
    find $BACKUP_DIR -name "analytics_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
```

#### 2. Automated Backup Cron
```bash
# Add to crontab
0 2 * * * /opt/churnguard-analytics/scripts/backup_timescaledb.sh >> /var/log/backup.log 2>&1
```

## Scaling & Performance

### Horizontal Scaling

#### 1. Application Scaling
```yaml
# docker-compose.override.yml for scaling
version: '3.8'
services:
  analytics-api:
    deploy:
      replicas: 4
    environment:
      - WORKER_CONNECTIONS=1000
      
  analytics-worker:
    deploy:
      replicas: 2
```

#### 2. Database Scaling

**TimescaleDB Multi-Node Setup**
```sql
-- On access node
SELECT add_data_node('data_node_1', host => 'timescale-node-1.internal');
SELECT add_data_node('data_node_2', host => 'timescale-node-2.internal');

-- Create distributed hypertable
SELECT create_distributed_hypertable('time_series_data', 'timestamp');
```

#### 3. Redis Scaling
```bash
# Redis Cluster Setup
redis-cli --cluster create \
  127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 \
  127.0.0.1:7004 127.0.0.1:7005 127.0.0.1:7006 \
  --cluster-replicas 1
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Optimize TimescaleDB settings
ALTER SYSTEM SET shared_preload_libraries = 'timescaledb';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET effective_cache_size = '24GB';
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 500;

-- Reload configuration
SELECT pg_reload_conf();

-- Create additional indexes for common queries
CREATE INDEX CONCURRENTLY idx_ts_recent 
ON time_series_data(timestamp DESC) 
WHERE timestamp > NOW() - INTERVAL '24 hours';

CREATE INDEX CONCURRENTLY idx_ts_metric_recent
ON time_series_data(metric_name, timestamp DESC)
WHERE timestamp > NOW() - INTERVAL '7 days';
```

#### 2. Application Optimization
```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Async processing
import asyncio
from concurrent.futures import ProcessPoolExecutor

class OptimizedAnalyticsEngine:
    def __init__(self):
        self.executor = ProcessPoolExecutor(max_workers=4)
        
    async def process_metrics_batch(self, metrics_batch):
        loop = asyncio.get_event_loop()
        
        # Process in parallel
        tasks = []
        for batch in self.chunk_metrics(metrics_batch, 1000):
            task = loop.run_in_executor(
                self.executor, 
                self.process_metric_chunk, 
                batch
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return self.merge_results(results)
```

## Security

### SSL/TLS Configuration

#### 1. Certificate Management
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d analytics.churnguard.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### 2. Application Security
```python
# Security middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["analytics.churnguard.com"]
)

# JWT Authentication
from fastapi_users.authentication import JWTAuthentication

jwt_authentication = JWTAuthentication(
    secret=JWT_SECRET,
    lifetime_seconds=3600,
    tokenUrl="/auth/jwt/login"
)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/data")
@limiter.limit("100/minute")
async def get_data(request: Request):
    return {"data": "example"}
```

### Network Security

#### 1. Firewall Configuration
```bash
# UFW Firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 'Nginx Full'

# Allow database connections (restrict to app servers)
sudo ufw allow from 10.0.1.0/24 to any port 5432
sudo ufw allow from 10.0.1.0/24 to any port 6379

# Enable firewall
sudo ufw enable
```

#### 2. Database Security
```sql
-- PostgreSQL security
-- Create read-only user for monitoring
CREATE USER monitoring_user WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE analytics_db TO monitoring_user;
GRANT USAGE ON SCHEMA public TO monitoring_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

-- Row Level Security (if needed)
ALTER TABLE time_series_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation_policy ON time_series_data
FOR ALL TO analytics_user
USING (organization_id = current_setting('rls.organization_id'));
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage
free -h
top -p $(pgrep -f churnguard-analytics)

# Analyze memory leaks
python -m memory_profiler your_script.py

# Solutions:
# - Reduce buffer sizes
# - Implement pagination
# - Add memory limits to Docker containers
# - Optimize queries to reduce result sets
```

#### 2. Slow Database Queries
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM time_series_data 
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

#### 3. Service Connection Issues
```bash
# Check service status
sudo systemctl status churnguard-analytics
sudo systemctl status postgresql
sudo systemctl status redis

# Check ports
sudo netstat -tlnp | grep -E ':(8000|5432|6379)'

# Check logs
sudo journalctl -u churnguard-analytics -f
tail -f /var/log/churnguard-analytics/app.log
```

#### 4. High CPU Usage
```bash
# Identify CPU-intensive processes
top -H
htop

# Profile Python application
python -m cProfile -o profile.stats your_script.py
python -c "
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
"

# Solutions:
# - Optimize algorithms
# - Use async processing
# - Implement caching
# - Scale horizontally
```

### Recovery Procedures

#### 1. Database Recovery
```bash
# Restore from backup
gunzip -c /backups/timescaledb/analytics_db_20250115_020000.sql.gz | \
psql -h localhost -U analytics_user -d analytics_db

# Point-in-time recovery (if WAL archiving enabled)
pg_basebackup -h localhost -U postgres -D /var/lib/postgresql/recovery
```

#### 2. Service Recovery
```bash
# Restart services in order
sudo systemctl restart redis
sudo systemctl restart postgresql
sudo systemctl restart churnguard-analytics

# Check service dependencies
systemctl list-dependencies churnguard-analytics
```

### Health Checks

#### 1. Automated Health Monitoring
**scripts/health_check.py**
```python
import requests
import sys
import time
import logging
from datetime import datetime

def check_api_health():
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        return response.status_code == 200
    except:
        return False

def check_database_health():
    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv('TIMESCALEDB_URL'))
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        return True
    except:
        return False

def check_redis_health():
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL'))
        return r.ping()
    except:
        return False

def main():
    checks = [
        ('API', check_api_health),
        ('Database', check_database_health),
        ('Redis', check_redis_health)
    ]
    
    all_healthy = True
    
    for name, check_func in checks:
        healthy = check_func()
        status = "HEALTHY" if healthy else "UNHEALTHY"
        print(f"{datetime.now().isoformat()} - {name}: {status}")
        
        if not healthy:
            all_healthy = False
    
    sys.exit(0 if all_healthy else 1)

if __name__ == "__main__":
    main()
```

#### 2. Kubernetes Liveness Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

This deployment guide provides comprehensive instructions for setting up, configuring, and maintaining the ChurnGuard Analytics platform in production environments. Follow the sections relevant to your deployment method and scale requirements.