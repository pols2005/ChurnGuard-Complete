# Epic 6: Production Operations & DevOps Excellence
## Comprehensive Implementation Guide

### 🎯 Epic Overview

Epic 6 represents the critical operational foundation that transforms ChurnGuard from a feature-complete platform into a production-ready, enterprise-scale SaaS solution. This epic focuses on automated deployment pipelines, comprehensive monitoring, disaster recovery, and operational excellence practices.

### 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [CI/CD Pipeline Implementation](#cicd-pipeline-implementation)
3. [Infrastructure as Code](#infrastructure-as-code)
4. [Monitoring & Observability](#monitoring--observability)
5. [Disaster Recovery & Business Continuity](#disaster-recovery--business-continuity)
6. [Security Operations (SecOps)](#security-operations-secops)
7. [Performance Management](#performance-management)
8. [Cost Optimization](#cost-optimization)
9. [Incident Response](#incident-response)
10. [Deployment Guide](#deployment-guide)

---

## Architecture Overview

### Production Environment Strategy

Epic 6 implements a multi-environment strategy designed for enterprise reliability:

```
┌─────────────────────────────────────────────────────────────┐
│                Production Environment Architecture           │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer & CDN                                        │
│  ├── AWS CloudFront / CloudFlare                           │
│  ├── Route 53 DNS Management                               │
│  └── SSL/TLS Certificate Management                        │
├─────────────────────────────────────────────────────────────┤
│  Application Layer (Auto-Scaling)                          │
│  ├── Production Cluster (3+ nodes)                         │
│  ├── Staging Environment                                    │
│  ├── Development Environment                               │
│  └── Feature Branch Environments                           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (High Availability)                            │
│  ├── PostgreSQL Primary/Replica Setup                     │
│  ├── Redis Cluster (Session & Cache)                      │
│  ├── Object Storage (S3-compatible)                       │
│  └── Backup & Disaster Recovery                           │
├─────────────────────────────────────────────────────────────┤
│  Monitoring & Observability                                │
│  ├── Application Performance Monitoring (APM)             │
│  ├── Infrastructure Monitoring                            │
│  ├── Log Aggregation & Analysis                          │
│  ├── Security Information Event Management (SIEM)         │
│  └── Business Intelligence Dashboard                      │
└─────────────────────────────────────────────────────────────┘
```

### Core Design Principles

1. **Zero Downtime Deployments**: Blue-green and rolling deployment strategies
2. **Infrastructure as Code**: All infrastructure versioned and reproducible
3. **Observability First**: Comprehensive monitoring, logging, and tracing
4. **Automated Recovery**: Self-healing systems with automated failover
5. **Security in Depth**: Multi-layer security with automated compliance checks
6. **Cost Optimization**: Resource scaling based on demand patterns

---

## CI/CD Pipeline Implementation

### Location: `.github/workflows/` and `ops/ci-cd/`

### Pipeline Architecture

```yaml
# .github/workflows/production-deployment.yml
name: Production Deployment Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scanning:
    runs-on: ubuntu-latest
    steps:
      - name: Security Code Scan
        run: |
          # SAST scanning with CodeQL
          # Dependency vulnerability scanning
          # Infrastructure security validation
          
  automated-testing:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [unit, integration, e2e, performance, security]
    steps:
      - name: Test Execution
        run: |
          # Comprehensive test suite execution
          # Performance regression testing
          # Security vulnerability testing
          
  build-and-push:
    needs: [security-scanning, automated-testing]
    runs-on: ubuntu-latest
    steps:
      - name: Docker Build & Push
        run: |
          # Multi-stage Docker builds
          # Image vulnerability scanning
          # Registry push with versioning
          
  infrastructure-deployment:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Terraform Apply
        run: |
          # Infrastructure provisioning
          # Configuration management
          # Health checks and validation
          
  application-deployment:
    needs: infrastructure-deployment
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]
    steps:
      - name: Rolling Deployment
        run: |
          # Blue-green deployment execution
          # Health check validation
          # Automated rollback on failure
          
  post-deployment:
    needs: application-deployment
    runs-on: ubuntu-latest
    steps:
      - name: Deployment Verification
        run: |
          # Smoke tests execution
          # Performance validation
          # Security posture verification
          # Notification to stakeholders
```

### Deployment Strategies

#### 1. Blue-Green Deployment
```bash
#!/bin/bash
# ops/scripts/blue-green-deploy.sh

CURRENT_ENV=$(kubectl get service churnguard-service -o jsonpath='{.spec.selector.version}')
NEW_ENV=$([ "$CURRENT_ENV" == "blue" ] && echo "green" || echo "blue")

echo "Deploying to $NEW_ENV environment..."

# Deploy new version to inactive environment
kubectl apply -f k8s/deployments/churnguard-$NEW_ENV.yml

# Wait for deployment readiness
kubectl rollout status deployment/churnguard-$NEW_ENV

# Run smoke tests
./ops/scripts/smoke-tests.sh $NEW_ENV

# Switch traffic if tests pass
if [ $? -eq 0 ]; then
    kubectl patch service churnguard-service -p '{"spec":{"selector":{"version":"'$NEW_ENV'"}}}'
    echo "Traffic switched to $NEW_ENV"
    
    # Clean up old environment after grace period
    sleep 300
    kubectl scale deployment churnguard-$CURRENT_ENV --replicas=0
else
    echo "Deployment failed, keeping current environment"
    exit 1
fi
```

#### 2. Canary Deployment
```python
# ops/scripts/canary-deployment.py
import time
import requests
from kubernetes import client, config

class CanaryDeployment:
    def __init__(self):
        config.load_incluster_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
    
    def deploy_canary(self, version, canary_percentage=10):
        """
        Deploy new version to small percentage of traffic
        Monitor key metrics and gradually increase traffic
        """
        # Deploy canary version
        self._deploy_version(f"churnguard-canary-{version}", version)
        
        # Gradually increase traffic
        traffic_steps = [10, 25, 50, 75, 100]
        
        for traffic in traffic_steps:
            self._adjust_traffic_split("canary", traffic)
            
            # Monitor for 10 minutes
            if self._monitor_health_metrics(duration=600):
                print(f"Canary at {traffic}% - metrics healthy")
                continue
            else:
                print(f"Canary failed at {traffic}% - rolling back")
                self._rollback_canary()
                return False
        
        # Promote canary to production
        self._promote_canary(version)
        return True
    
    def _monitor_health_metrics(self, duration):
        """Monitor error rate, latency, and business metrics"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            metrics = self._get_application_metrics()
            
            if (metrics['error_rate'] > 0.01 or  # 1% error rate threshold
                metrics['p99_latency'] > 2000 or  # 2s latency threshold
                metrics['business_metric_drop'] > 0.05):  # 5% business impact
                return False
            
            time.sleep(30)  # Check every 30 seconds
        
        return True
```

### Feature Flag Integration

```python
# server/core/feature_flags.py
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class FeatureFlag:
    name: str
    enabled: bool
    rollout_percentage: int = 100
    conditions: Dict[str, Any] = None
    
class FeatureFlagManager:
    def __init__(self):
        self.flags = self._load_feature_flags()
    
    def is_enabled(self, flag_name: str, user_context: Dict = None) -> bool:
        """
        Check if feature flag is enabled for given context
        Supports gradual rollouts and conditional enabling
        """
        flag = self.flags.get(flag_name)
        if not flag or not flag.enabled:
            return False
        
        # Check rollout percentage
        if user_context and 'user_id' in user_context:
            user_hash = hash(user_context['user_id']) % 100
            if user_hash >= flag.rollout_percentage:
                return False
        
        # Check additional conditions
        if flag.conditions and user_context:
            return self._evaluate_conditions(flag.conditions, user_context)
        
        return True
    
    def _load_feature_flags(self) -> Dict[str, FeatureFlag]:
        """Load feature flags from environment or external service"""
        return {
            'new_dashboard_ui': FeatureFlag(
                name='new_dashboard_ui',
                enabled=os.getenv('FF_NEW_DASHBOARD', 'false').lower() == 'true',
                rollout_percentage=int(os.getenv('FF_NEW_DASHBOARD_ROLLOUT', '10'))
            ),
            'advanced_analytics': FeatureFlag(
                name='advanced_analytics',
                enabled=True,
                conditions={'subscription_tier': ['professional', 'enterprise']}
            )
        }
```

---

## Infrastructure as Code

### Location: `ops/terraform/` and `ops/kubernetes/`

### Terraform Infrastructure

```hcl
# ops/terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  
  backend "s3" {
    bucket = "churnguard-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-west-2"
    
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

# Production EKS Cluster
resource "aws_eks_cluster" "churnguard_production" {
  name     = "churnguard-production"
  role_arn = aws_iam_role.cluster_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  encryption_config {
    resources = ["secrets"]
    provider {
      key_id = aws_kms_key.eks_encryption.arn
    }
  }

  enabled_cluster_log_types = [
    "api", "audit", "authenticator", "controllerManager", "scheduler"
  ]

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy,
    aws_iam_role_policy_attachment.service_policy,
  ]
}

# RDS PostgreSQL with Multi-AZ
resource "aws_db_instance" "churnguard_production" {
  identifier = "churnguard-production"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds_encryption.arn

  multi_az               = true
  publicly_accessible    = false
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  deletion_protection = true
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn

  tags = local.common_tags
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "churnguard_redis" {
  replication_group_id       = "churnguard-redis"
  description                = "ChurnGuard Redis Cluster"

  port                = 6379
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  node_type           = "cache.r7g.large"
  num_cache_clusters  = 3

  engine_version             = "7.0"
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = random_password.redis_auth.result

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  maintenance_window = "sun:05:00-sun:06:00"
  snapshot_window    = "06:00-08:00"
  snapshot_retention_limit = 7

  tags = local.common_tags
}
```

### Kubernetes Deployment Configuration

```yaml
# ops/kubernetes/production/churnguard-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churnguard-api
  namespace: churnguard-production
  labels:
    app: churnguard-api
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: churnguard-api
  template:
    metadata:
      labels:
        app: churnguard-api
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: churnguard-service-account
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: churnguard-api
        image: churnguard/api:latest
        ports:
        - containerPort: 5000
          name: http
        - containerPort: 8080
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: churnguard-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: churnguard-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: churnguard-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: churnguard-config
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: churnguard-service
  namespace: churnguard-production
  labels:
    app: churnguard-api
spec:
  selector:
    app: churnguard-api
  ports:
  - port: 80
    targetPort: 5000
    name: http
  - port: 8080
    targetPort: 8080
    name: metrics
  type: ClusterIP
```

### Horizontal Pod Autoscaling

```yaml
# ops/kubernetes/production/churnguard-hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: churnguard-api-hpa
  namespace: churnguard-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: churnguard-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 60
```

---

## Monitoring & Observability

### Location: `ops/monitoring/` and `server/monitoring/`

### Prometheus Configuration

```yaml
# ops/monitoring/prometheus/prometheus.yml
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
  - job_name: 'churnguard-api'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__

  - job_name: 'postgres-exporter'
    static_configs:
    - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
    - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - source_labels: [__address__]
      regex: '(.*):10250'
      replacement: '${1}:9100'
      target_label: __address__
```

### Application Metrics Implementation

```python
# server/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from functools import wraps
import time
from flask import request, g

# Application metrics
REQUEST_COUNT = Counter(
    'churnguard_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code', 'organization_id']
)

REQUEST_DURATION = Histogram(
    'churnguard_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'organization_id']
)

ACTIVE_USERS = Gauge(
    'churnguard_active_users',
    'Number of active users',
    ['organization_id', 'subscription_tier']
)

PREDICTION_COUNT = Counter(
    'churnguard_predictions_total',
    'Total number of churn predictions generated',
    ['organization_id', 'model_version', 'risk_level']
)

DATABASE_CONNECTIONS = Gauge(
    'churnguard_db_connections_active',
    'Active database connections'
)

GDPR_REQUEST_PROCESSING_TIME = Histogram(
    'churnguard_gdpr_request_duration_seconds',
    'Time to process GDPR requests',
    ['request_type', 'organization_id']
)

class MetricsCollector:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Register metrics endpoint
        @app.route('/metrics')
        def metrics():
            return generate_latest(), 200, {'Content-Type': 'text/plain'}
    
    def _before_request(self):
        g.start_time = time.time()
        g.organization_id = self._get_organization_id()
    
    def _after_request(self, response):
        duration = time.time() - g.start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status_code=response.status_code,
            organization_id=g.get('organization_id', 'unknown')
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            organization_id=g.get('organization_id', 'unknown')
        ).observe(duration)
        
        return response
    
    def _get_organization_id(self):
        """Extract organization ID from JWT token"""
        try:
            from flask_jwt_extended import get_jwt
            claims = get_jwt()
            return claims.get('organization_id', 'unknown')
        except:
            return 'unknown'

def track_prediction_metrics(func):
    """Decorator to track prediction generation metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            
            # Track successful prediction
            PREDICTION_COUNT.labels(
                organization_id=g.get('organization_id', 'unknown'),
                model_version=result.get('model_version', 'unknown'),
                risk_level=result.get('risk_level', 'unknown')
            ).inc()
            
            return result
        except Exception as e:
            # Track failed predictions
            PREDICTION_COUNT.labels(
                organization_id=g.get('organization_id', 'unknown'),
                model_version='unknown',
                risk_level='error'
            ).inc()
            raise
    return wrapper
```

### Custom Dashboard Creation

```python
# server/monitoring/dashboard.py
import json
from typing import Dict, List, Any

class GrafanaDashboardGenerator:
    def __init__(self):
        self.dashboard_template = {
            "dashboard": {
                "title": "ChurnGuard Production Monitoring",
                "tags": ["churnguard", "production"],
                "timezone": "browser",
                "refresh": "30s",
                "time": {"from": "now-1h", "to": "now"},
                "panels": []
            }
        }
    
    def generate_application_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive application monitoring dashboard"""
        panels = [
            self._create_request_rate_panel(),
            self._create_response_time_panel(),
            self._create_error_rate_panel(),
            self._create_active_users_panel(),
            self._create_prediction_metrics_panel(),
            self._create_database_panel(),
            self._create_gdpr_compliance_panel(),
            self._create_infrastructure_panel()
        ]
        
        dashboard = self.dashboard_template.copy()
        dashboard["dashboard"]["panels"] = panels
        return dashboard
    
    def _create_request_rate_panel(self) -> Dict[str, Any]:
        return {
            "title": "Request Rate",
            "type": "graph",
            "targets": [{
                "expr": "rate(churnguard_requests_total[5m])",
                "legendFormat": "{{ method }} {{ endpoint }}"
            }],
            "yAxes": [{"label": "Requests/sec"}],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
        }
    
    def _create_gdpr_compliance_panel(self) -> Dict[str, Any]:
        return {
            "title": "GDPR Request Processing",
            "type": "stat",
            "targets": [
                {
                    "expr": "avg(churnguard_gdpr_request_duration_seconds)",
                    "legendFormat": "Avg Processing Time"
                },
                {
                    "expr": "sum(rate(churnguard_gdpr_requests_overdue[1h]))",
                    "legendFormat": "Overdue Requests"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
        }
```

### Alerting Rules

```yaml
# ops/monitoring/prometheus/rules/churnguard-alerts.yml
groups:
- name: churnguard.rules
  rules:
  
  # Application Health Alerts
  - alert: HighErrorRate
    expr: rate(churnguard_requests_total{status_code=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
      team: platform
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} for {{ $labels.endpoint }}"
      runbook_url: "https://docs.churnguard.com/runbooks/high-error-rate"
  
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, churnguard_request_duration_seconds_bucket) > 2
    for: 5m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }}s"
  
  - alert: DatabaseConnectionsHigh
    expr: churnguard_db_connections_active > 80
    for: 2m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "Database connection pool nearly exhausted"
      description: "{{ $value }} connections active out of maximum"
  
  # GDPR Compliance Alerts
  - alert: GDPRRequestOverdue
    expr: churnguard_gdpr_requests_overdue > 0
    for: 1m
    labels:
      severity: critical
      team: compliance
    annotations:
      summary: "GDPR request overdue"
      description: "{{ $value }} GDPR requests are overdue (>30 days)"
      runbook_url: "https://docs.churnguard.com/runbooks/gdpr-overdue"
  
  - alert: ComplianceScoreLow
    expr: churnguard_compliance_score < 80
    for: 10m
    labels:
      severity: warning
      team: compliance
    annotations:
      summary: "Compliance score below threshold"
      description: "Compliance score is {{ $value }} for organization {{ $labels.organization_id }}"
  
  # Infrastructure Alerts
  - alert: PodCrashLooping
    expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
    for: 5m
    labels:
      severity: critical
      team: platform
    annotations:
      summary: "Pod crash looping"
      description: "Pod {{ $labels.pod }} is crash looping"
  
  - alert: NodeHighCPU
    expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
      team: infrastructure
    annotations:
      summary: "High CPU usage on node"
      description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"
```

---

## Disaster Recovery & Business Continuity

### Location: `ops/disaster-recovery/`

### Recovery Time Objectives (RTO) & Recovery Point Objectives (RPO)

| System Component | RTO | RPO | Strategy |
|------------------|-----|-----|----------|
| **Application Services** | 15 minutes | 5 minutes | Multi-AZ deployment with automated failover |
| **Database (PostgreSQL)** | 30 minutes | 15 minutes | Multi-AZ with automated backup/restore |
| **Cache Layer (Redis)** | 5 minutes | 1 minute | Redis Cluster with automatic failover |
| **File Storage** | 10 minutes | 1 hour | Cross-region replication |
| **Monitoring Systems** | 20 minutes | 30 minutes | Separate availability zone deployment |

### Backup Strategy Implementation

```python
# ops/disaster-recovery/backup_manager.py
import boto3
import psycopg2
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

@dataclass
class BackupPolicy:
    component: str
    frequency: str  # daily, hourly, weekly
    retention_days: int
    encryption_enabled: bool
    cross_region_replication: bool

class DisasterRecoveryManager:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.rds_client = boto3.client('rds')
        self.backup_bucket = 'churnguard-disaster-recovery'
        self.backup_policies = self._load_backup_policies()
        
    def _load_backup_policies(self) -> List[BackupPolicy]:
        return [
            BackupPolicy(
                component='database',
                frequency='hourly',
                retention_days=30,
                encryption_enabled=True,
                cross_region_replication=True
            ),
            BackupPolicy(
                component='application_data',
                frequency='daily',
                retention_days=90,
                encryption_enabled=True,
                cross_region_replication=False
            ),
            BackupPolicy(
                component='configuration',
                frequency='daily',
                retention_days=365,
                encryption_enabled=True,
                cross_region_replication=True
            )
        ]
    
    def execute_database_backup(self, database_identifier: str) -> str:
        """Create RDS snapshot with encryption"""
        snapshot_id = f"{database_identifier}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            response = self.rds_client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
                DBInstanceIdentifier=database_identifier,
                Tags=[
                    {'Key': 'Purpose', 'Value': 'DisasterRecovery'},
                    {'Key': 'CreatedBy', 'Value': 'AutomatedBackup'},
                    {'Key': 'RetentionDate', 'Value': (datetime.now() + timedelta(days=30)).isoformat()}
                ]
            )
            
            logging.info(f"Database backup created: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            logging.error(f"Database backup failed: {str(e)}")
            raise
    
    def restore_from_backup(self, backup_identifier: str, restore_target: str) -> bool:
        """Restore database from backup snapshot"""
        try:
            # Create new RDS instance from snapshot
            self.rds_client.restore_db_instance_from_db_snapshot(
                DBInstanceIdentifier=restore_target,
                DBSnapshotIdentifier=backup_identifier,
                DBInstanceClass='db.r6g.xlarge',  # Match production specs
                MultiAZ=True,
                VpcSecurityGroupIds=['sg-production-database'],
                DBSubnetGroupName='production-db-subnet-group',
                
                # Enable encryption
                StorageEncrypted=True,
                
                # Performance monitoring
                EnablePerformanceInsights=True,
                PerformanceInsightsRetentionPeriod=7
            )
            
            logging.info(f"Database restore initiated: {restore_target}")
            return True
            
        except Exception as e:
            logging.error(f"Database restore failed: {str(e)}")
            return False
    
    def test_backup_integrity(self, backup_identifier: str) -> Dict[str, bool]:
        """Test backup integrity and recoverability"""
        test_results = {
            'snapshot_exists': False,
            'can_restore': False,
            'data_integrity': False,
            'performance_acceptable': False
        }
        
        try:
            # Check if snapshot exists
            snapshots = self.rds_client.describe_db_snapshots(
                DBSnapshotIdentifier=backup_identifier
            )
            test_results['snapshot_exists'] = len(snapshots['DBSnapshots']) > 0
            
            # Test restore to temporary instance
            test_instance_id = f"test-restore-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if self.restore_from_backup(backup_identifier, test_instance_id):
                test_results['can_restore'] = True
                
                # Wait for instance to become available
                waiter = self.rds_client.get_waiter('db_instance_available')
                waiter.wait(DBInstanceIdentifier=test_instance_id)
                
                # Test data integrity
                test_results['data_integrity'] = self._validate_data_integrity(test_instance_id)
                
                # Test performance
                test_results['performance_acceptable'] = self._test_performance(test_instance_id)
                
                # Clean up test instance
                self.rds_client.delete_db_instance(
                    DBInstanceIdentifier=test_instance_id,
                    SkipFinalSnapshot=True
                )
            
        except Exception as e:
            logging.error(f"Backup integrity test failed: {str(e)}")
        
        return test_results
    
    def _validate_data_integrity(self, instance_id: str) -> bool:
        """Run data integrity checks on restored instance"""
        # Get connection details
        instance = self.rds_client.describe_db_instances(
            DBInstanceIdentifier=instance_id
        )['DBInstances'][0]
        
        endpoint = instance['Endpoint']['Address']
        
        try:
            # Connect and run integrity checks
            conn = psycopg2.connect(
                host=endpoint,
                port=5432,
                database='churnguard',
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            
            cursor = conn.cursor()
            
            # Check table counts
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins - n_tup_del as row_count
                FROM pg_stat_user_tables 
                ORDER BY schemaname, tablename;
            """)
            
            results = cursor.fetchall()
            
            # Validate against expected data ranges
            critical_tables = ['customers', 'users', 'organizations', 'predictions']
            
            for schema, table, count in results:
                if table in critical_tables and count == 0:
                    logging.error(f"Critical table {table} is empty")
                    return False
            
            # Check data consistency
            cursor.execute("""
                SELECT COUNT(*) FROM customers c
                LEFT JOIN organizations o ON c.organization_id = o.id
                WHERE o.id IS NULL;
            """)
            
            orphaned_customers = cursor.fetchone()[0]
            if orphaned_customers > 0:
                logging.error(f"Found {orphaned_customers} orphaned customer records")
                return False
            
            logging.info("Data integrity validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Data integrity validation failed: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
```

### Automated Disaster Recovery Testing

```bash
#!/bin/bash
# ops/disaster-recovery/test-dr-procedures.sh

set -euo pipefail

LOG_FILE="/var/log/disaster-recovery/dr-test-$(date +%Y%m%d-%H%M%S).log"
SLACK_WEBHOOK_URL="${SLACK_DR_WEBHOOK_URL:-}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

notify_slack() {
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 DR Test: $1\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# Test 1: Database Backup and Restore
test_database_recovery() {
    log "Starting database recovery test..."
    
    # Create test snapshot
    SNAPSHOT_ID="dr-test-$(date +%Y%m%d-%H%M%S)"
    
    aws rds create-db-snapshot \
        --db-instance-identifier churnguard-production \
        --db-snapshot-identifier "$SNAPSHOT_ID" \
        --tags Key=Purpose,Value=DRTesting
    
    # Wait for snapshot completion
    aws rds wait db-snapshot-completed --db-snapshot-identifier "$SNAPSHOT_ID"
    
    # Test restore
    TEST_INSTANCE="dr-test-instance-$(date +%Y%m%d%H%M%S)"
    
    aws rds restore-db-instance-from-db-snapshot \
        --db-instance-identifier "$TEST_INSTANCE" \
        --db-snapshot-identifier "$SNAPSHOT_ID" \
        --db-instance-class db.t3.micro
    
    # Wait for instance availability
    aws rds wait db-instance-available --db-instance-identifier "$TEST_INSTANCE"
    
    # Run data integrity tests
    python3 ops/disaster-recovery/validate_data_integrity.py --instance "$TEST_INSTANCE"
    
    # Cleanup
    aws rds delete-db-instance \
        --db-instance-identifier "$TEST_INSTANCE" \
        --skip-final-snapshot
    
    aws rds delete-db-snapshot --db-snapshot-identifier "$SNAPSHOT_ID"
    
    log "Database recovery test completed successfully"
}

# Test 2: Application Failover
test_application_failover() {
    log "Starting application failover test..."
    
    # Get current active deployment
    CURRENT_VERSION=$(kubectl get deployment churnguard-api -o jsonpath='{.spec.template.metadata.labels.version}')
    
    # Simulate failure by scaling down primary
    kubectl scale deployment churnguard-api --replicas=0
    
    # Wait for health checks to detect failure
    sleep 60
    
    # Verify automatic failover occurred
    HEALTHY_PODS=$(kubectl get pods -l app=churnguard-api --field-selector=status.phase=Running | wc -l)
    
    if [[ $HEALTHY_PODS -eq 0 ]]; then
        log "ERROR: No healthy pods after failover"
        notify_slack "Application failover test FAILED - no healthy pods"
        return 1
    fi
    
    # Restore normal operations
    kubectl scale deployment churnguard-api --replicas=3
    
    # Wait for all pods to be ready
    kubectl rollout status deployment/churnguard-api
    
    log "Application failover test completed successfully"
}

# Test 3: Cross-Region Recovery
test_cross_region_recovery() {
    log "Starting cross-region recovery test..."
    
    # Switch kubectl context to DR region
    kubectl config use-context dr-region-cluster
    
    # Deploy application to DR region
    kubectl apply -f ops/kubernetes/disaster-recovery/
    
    # Wait for deployment
    kubectl rollout status deployment/churnguard-api-dr
    
    # Run smoke tests against DR environment
    python3 ops/testing/smoke_tests.py --endpoint "https://dr.churnguard.com"
    
    # Verify database replication is working
    python3 ops/disaster-recovery/verify_replication.py
    
    # Clean up DR deployment
    kubectl delete -f ops/kubernetes/disaster-recovery/
    
    # Switch back to primary region
    kubectl config use-context production-cluster
    
    log "Cross-region recovery test completed successfully"
}

# Main execution
main() {
    log "Starting comprehensive disaster recovery testing..."
    notify_slack "Starting DR test procedures"
    
    # Create test results directory
    mkdir -p "/var/log/disaster-recovery"
    
    # Run all DR tests
    test_database_recovery
    test_application_failover
    test_cross_region_recovery
    
    # Generate test report
    python3 ops/disaster-recovery/generate_test_report.py --log-file "$LOG_FILE"
    
    log "All disaster recovery tests completed successfully"
    notify_slack "DR test procedures completed successfully ✅"
}

# Schedule this script to run weekly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## Security Operations (SecOps)

### Location: `ops/security/` and `server/security/`

### Security Monitoring Implementation

```python
# server/security/security_monitor.py
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class SecurityEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    source_ip: str
    user_id: Optional[str]
    organization_id: Optional[str]
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]
    
class SecurityEventAnalyzer:
    def __init__(self):
        self.threat_patterns = self._load_threat_patterns()
        self.recent_events = deque(maxlen=10000)  # Last 10k events
        self.ip_failure_counts = defaultdict(int)
        self.user_activity_patterns = defaultdict(list)
        
    def _load_threat_patterns(self) -> Dict[str, Dict]:
        return {
            'brute_force_login': {
                'pattern': 'login_failed',
                'threshold': 5,
                'time_window': 300,  # 5 minutes
                'severity': 'high'
            },
            'data_exfiltration': {
                'pattern': 'bulk_data_export',
                'threshold': 3,
                'time_window': 1800,  # 30 minutes
                'severity': 'critical'
            },
            'privilege_escalation': {
                'pattern': 'role_change',
                'conditions': {'new_role': ['admin', 'super_admin']},
                'severity': 'high'
            },
            'gdpr_violation_risk': {
                'pattern': 'data_subject_request_overdue',
                'threshold': 1,
                'time_window': 86400 * 30,  # 30 days
                'severity': 'critical'
            },
            'unusual_access_pattern': {
                'pattern': 'login_success',
                'conditions': {
                    'time_anomaly': True,
                    'location_anomaly': True
                },
                'severity': 'medium'
            }
        }
    
    def analyze_security_event(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """
        Analyze incoming security event for threat patterns
        Returns list of alerts generated
        """
        alerts = []
        self.recent_events.append(event)
        
        # Check each threat pattern
        for pattern_name, pattern_config in self.threat_patterns.items():
            alert = self._check_threat_pattern(event, pattern_name, pattern_config)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def _check_threat_pattern(self, event: SecurityEvent, pattern_name: str, config: Dict) -> Optional[Dict]:
        """Check if event matches specific threat pattern"""
        
        if pattern_name == 'brute_force_login' and event.event_type == 'login_failed':
            return self._check_brute_force(event, config)
        
        elif pattern_name == 'data_exfiltration' and 'export' in event.event_type:
            return self._check_data_exfiltration(event, config)
        
        elif pattern_name == 'privilege_escalation' and event.event_type == 'role_changed':
            return self._check_privilege_escalation(event, config)
        
        elif pattern_name == 'gdpr_violation_risk' and 'gdpr' in event.event_type:
            return self._check_gdpr_compliance_risk(event, config)
        
        elif pattern_name == 'unusual_access_pattern' and event.event_type == 'login_success':
            return self._check_unusual_access(event, config)
        
        return None
    
    def _check_brute_force(self, event: SecurityEvent, config: Dict) -> Optional[Dict]:
        """Detect brute force login attempts"""
        cutoff_time = datetime.now() - timedelta(seconds=config['time_window'])
        
        # Count recent failures from same IP
        recent_failures = sum(1 for e in self.recent_events
                             if e.source_ip == event.source_ip 
                             and e.event_type == 'login_failed'
                             and e.timestamp > cutoff_time)
        
        if recent_failures >= config['threshold']:
            return {
                'alert_type': 'brute_force_detected',
                'severity': config['severity'],
                'source_ip': event.source_ip,
                'failure_count': recent_failures,
                'time_window': config['time_window'],
                'recommended_action': 'Block IP address',
                'timestamp': event.timestamp
            }
        
        return None
    
    def _check_data_exfiltration(self, event: SecurityEvent, config: Dict) -> Optional[Dict]:
        """Detect potential data exfiltration"""
        cutoff_time = datetime.now() - timedelta(seconds=config['time_window'])
        
        # Count recent exports by user
        recent_exports = sum(1 for e in self.recent_events
                            if e.user_id == event.user_id
                            and 'export' in e.event_type
                            and e.timestamp > cutoff_time)
        
        # Check export volume
        export_size = event.details.get('export_size_mb', 0)
        
        if recent_exports >= config['threshold'] or export_size > 100:  # 100MB threshold
            return {
                'alert_type': 'data_exfiltration_risk',
                'severity': config['severity'],
                'user_id': event.user_id,
                'export_count': recent_exports,
                'export_size_mb': export_size,
                'recommended_action': 'Review user access and contact security team',
                'timestamp': event.timestamp
            }
        
        return None
    
    def generate_security_report(self, org_id: str) -> Dict[str, Any]:
        """Generate comprehensive security report for organization"""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        org_events = [e for e in self.recent_events 
                     if e.organization_id == org_id and e.timestamp > cutoff_time]
        
        report = {
            'organization_id': org_id,
            'report_period': '7_days',
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_events': len(org_events),
                'security_alerts': sum(1 for e in org_events if e.severity in ['high', 'critical']),
                'login_failures': sum(1 for e in org_events if e.event_type == 'login_failed'),
                'gdpr_requests': sum(1 for e in org_events if 'gdpr' in e.event_type),
                'data_exports': sum(1 for e in org_events if 'export' in e.event_type)
            },
            'risk_assessment': self._assess_security_risk(org_events),
            'recommendations': self._generate_security_recommendations(org_events)
        }
        
        return report
    
    def _assess_security_risk(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Assess overall security risk based on events"""
        risk_score = 0
        risk_factors = []
        
        # High-risk indicators
        critical_events = [e for e in events if e.severity == 'critical']
        high_events = [e for e in events if e.severity == 'high']
        
        if critical_events:
            risk_score += len(critical_events) * 25
            risk_factors.append(f"{len(critical_events)} critical security events")
        
        if high_events:
            risk_score += len(high_events) * 10
            risk_factors.append(f"{len(high_events)} high-severity security events")
        
        # Failed login attempts
        failed_logins = [e for e in events if e.event_type == 'login_failed']
        if len(failed_logins) > 50:
            risk_score += 15
            risk_factors.append(f"{len(failed_logins)} failed login attempts")
        
        # Overdue GDPR requests
        overdue_gdpr = [e for e in events if 'overdue' in e.event_type]
        if overdue_gdpr:
            risk_score += 30
            risk_factors.append(f"{len(overdue_gdpr)} overdue GDPR requests")
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': min(risk_score, 100),  # Cap at 100
            'risk_level': risk_level,
            'risk_factors': risk_factors
        }
```

### Vulnerability Management

```bash
#!/bin/bash
# ops/security/vulnerability-scan.sh

set -euo pipefail

SCAN_DATE=$(date +%Y%m%d)
REPORT_DIR="/var/log/security/vulnerability-scans/$SCAN_DATE"
SLACK_WEBHOOK="${SECURITY_SLACK_WEBHOOK:-}"

mkdir -p "$REPORT_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$REPORT_DIR/scan.log"
}

notify_security_team() {
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🔒 Security Scan: $1\"}" \
            "$SLACK_WEBHOOK"
    fi
}

# Scan container images for vulnerabilities
scan_container_images() {
    log "Scanning container images..."
    
    # Get all images used in production
    IMAGES=$(kubectl get pods -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | sort -u)
    
    for image in $IMAGES; do
        log "Scanning image: $image"
        
        # Use Trivy for vulnerability scanning
        trivy image --format json --output "$REPORT_DIR/$(basename $image)-vulns.json" "$image"
        
        # Check for critical vulnerabilities
        CRITICAL_VULNS=$(jq '.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL") | length' "$REPORT_DIR/$(basename $image)-vulns.json" 2>/dev/null | wc -l)
        
        if [[ $CRITICAL_VULNS -gt 0 ]]; then
            log "ALERT: Found $CRITICAL_VULNS critical vulnerabilities in $image"
            notify_security_team "Critical vulnerabilities found in $image"
        fi
    done
}

# Scan infrastructure for misconfigurations
scan_infrastructure() {
    log "Scanning infrastructure configuration..."
    
    # Scan Kubernetes configurations
    kube-score score ops/kubernetes/production/*.yml > "$REPORT_DIR/kubernetes-config-scan.txt"
    
    # Scan Terraform configurations
    tfsec ops/terraform/ --format json > "$REPORT_DIR/terraform-security-scan.json"
    
    # Check for exposed secrets
    truffleHog --json --regex --entropy=False . > "$REPORT_DIR/secret-scan.json"
    
    # Parse results for critical issues
    CRITICAL_ISSUES=$(jq '.results[] | select(.severity=="CRITICAL") | length' "$REPORT_DIR/terraform-security-scan.json" 2>/dev/null | wc -l)
    
    if [[ $CRITICAL_ISSUES -gt 0 ]]; then
        log "ALERT: Found $CRITICAL_ISSUES critical infrastructure issues"
        notify_security_team "Critical infrastructure security issues detected"
    fi
}

# Scan application dependencies
scan_dependencies() {
    log "Scanning application dependencies..."
    
    # Python dependencies
    safety check --json --output "$REPORT_DIR/python-deps-scan.json"
    
    # Node.js dependencies (if applicable)
    if [[ -f package.json ]]; then
        npm audit --json > "$REPORT_DIR/nodejs-deps-scan.json"
    fi
    
    # Check for high-severity vulnerabilities
    HIGH_VULN_COUNT=$(jq '.vulnerabilities[] | select(.severity=="high" or .severity=="critical") | length' "$REPORT_DIR/python-deps-scan.json" 2>/dev/null | wc -l)
    
    if [[ $HIGH_VULN_COUNT -gt 0 ]]; then
        log "ALERT: Found $HIGH_VULN_COUNT high/critical dependency vulnerabilities"
        notify_security_team "High-severity dependency vulnerabilities found"
    fi
}

# Generate comprehensive security report
generate_security_report() {
    log "Generating security report..."
    
    cat > "$REPORT_DIR/security-report.md" << EOF
# Security Vulnerability Scan Report
**Date**: $(date)
**Scan ID**: $SCAN_DATE

## Summary

### Container Images
$(find "$REPORT_DIR" -name "*-vulns.json" | wc -l) images scanned

### Infrastructure
- Kubernetes configuration scan completed
- Terraform security scan completed  
- Secret exposure scan completed

### Dependencies
- Python dependency scan completed
- Node.js dependency scan completed (if applicable)

## Critical Findings

### Container Vulnerabilities
$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL") | "- \(.VulnerabilityID): \(.Title)"' "$REPORT_DIR"/*-vulns.json 2>/dev/null | head -10)

### Infrastructure Issues
$(jq -r '.results[] | select(.severity=="CRITICAL") | "- \(.rule_description): \(.resource)"' "$REPORT_DIR/terraform-security-scan.json" 2>/dev/null | head -10)

### Dependency Vulnerabilities  
$(jq -r '.vulnerabilities[] | select(.severity=="critical") | "- \(.package_name): \(.vulnerability)"' "$REPORT_DIR/python-deps-scan.json" 2>/dev/null | head -10)

## Recommendations

1. **Immediate Actions Required**:
   - Update container base images with security patches
   - Apply infrastructure security fixes
   - Update vulnerable dependencies

2. **Process Improvements**:
   - Implement automated vulnerability scanning in CI/CD
   - Set up real-time security monitoring
   - Establish security patch management process

## Next Steps

- Review and prioritize critical findings
- Create remediation tickets for all high/critical issues
- Schedule follow-up scan in 7 days
- Update security policies based on findings
EOF

    log "Security report generated: $REPORT_DIR/security-report.md"
}

# Main execution
main() {
    log "Starting comprehensive security vulnerability scan..."
    
    scan_container_images
    scan_infrastructure  
    scan_dependencies
    generate_security_report
    
    # Upload report to security dashboard
    if command -v aws >/dev/null 2>&1; then
        aws s3 cp "$REPORT_DIR/" "s3://churnguard-security-reports/$SCAN_DATE/" --recursive
    fi
    
    log "Security vulnerability scan completed"
    notify_security_team "Security vulnerability scan completed - review required"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## Performance Management

### Location: `server/performance/` and `ops/performance/`

### Performance Monitoring & Optimization

```python
# server/performance/performance_monitor.py
import time
import psutil
import threading
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from collections import deque
import numpy as np

@dataclass  
class PerformanceMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_recv: int
    response_time_ms: float
    active_connections: int
    queue_depth: int

class PerformanceProfiler:
    def __init__(self, sample_interval: int = 60):
        self.sample_interval = sample_interval
        self.metrics_history = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.performance_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0, 
            'response_time_ms': 2000.0,
            'queue_depth': 100
        }
        self.monitoring_active = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            metrics = self._collect_system_metrics()
            self.metrics_history.append(metrics)
            
            # Check for performance alerts
            self._check_performance_alerts(metrics)
            
            time.sleep(self.sample_interval)
    
    def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Application-specific metrics (would need to be implemented)
        response_time_ms = self._get_average_response_time()
        active_connections = self._get_active_connections()
        queue_depth = self._get_queue_depth()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_io_read=disk_io.read_bytes if disk_io else 0,
            disk_io_write=disk_io.write_bytes if disk_io else 0,
            network_io_sent=network_io.bytes_sent if network_io else 0,
            network_io_recv=network_io.bytes_recv if network_io else 0,
            response_time_ms=response_time_ms,
            active_connections=active_connections,
            queue_depth=queue_depth
        )
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        
        for metric_name, threshold in self.performance_thresholds.items():
            current_value = getattr(metrics, metric_name)
            
            if current_value > threshold:
                alerts.append({
                    'alert_type': 'performance_threshold_exceeded',
                    'metric': metric_name,
                    'current_value': current_value,
                    'threshold': threshold,
                    'timestamp': metrics.timestamp,
                    'severity': self._calculate_severity(metric_name, current_value, threshold)
                })
        
        # Send alerts if any
        if alerts:
            self._send_performance_alerts(alerts)
    
    def _calculate_severity(self, metric: str, current: float, threshold: float) -> str:
        """Calculate alert severity based on how much threshold is exceeded"""
        ratio = current / threshold
        
        if ratio >= 1.5:
            return 'critical'
        elif ratio >= 1.25:
            return 'high'
        elif ratio >= 1.1:
            return 'medium'
        else:
            return 'low'
    
    def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {'error': 'No performance data available'}
        
        # Get metrics from specified time period
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {'error': f'No performance data available for last {hours} hours'}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        response_values = [m.response_time_ms for m in recent_metrics]
        
        report = {
            'report_period_hours': hours,
            'sample_count': len(recent_metrics),
            'generated_at': time.time(),
            
            'cpu_stats': {
                'average': np.mean(cpu_values),
                'max': np.max(cpu_values),
                'min': np.min(cpu_values),
                'p95': np.percentile(cpu_values, 95),
                'threshold_violations': sum(1 for v in cpu_values if v > self.performance_thresholds['cpu_percent'])
            },
            
            'memory_stats': {
                'average': np.mean(memory_values),
                'max': np.max(memory_values),
                'min': np.min(memory_values),
                'p95': np.percentile(memory_values, 95),
                'threshold_violations': sum(1 for v in memory_values if v > self.performance_thresholds['memory_percent'])
            },
            
            'response_time_stats': {
                'average_ms': np.mean(response_values),
                'max_ms': np.max(response_values),
                'min_ms': np.min(response_values),
                'p95_ms': np.percentile(response_values, 95),
                'p99_ms': np.percentile(response_values, 99),
                'threshold_violations': sum(1 for v in response_values if v > self.performance_thresholds['response_time_ms'])
            },
            
            'recommendations': self._generate_performance_recommendations(recent_metrics)
        }
        
        return report
    
    def _generate_performance_recommendations(self, metrics: List[PerformanceMetrics]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Analyze CPU usage patterns
        cpu_values = [m.cpu_percent for m in metrics]
        avg_cpu = np.mean(cpu_values)
        max_cpu = np.max(cpu_values)
        
        if avg_cpu > 60:
            recommendations.append("High average CPU usage detected. Consider scaling horizontally or optimizing CPU-intensive operations.")
        
        if max_cpu > 90:
            recommendations.append("CPU spikes detected. Investigate resource-intensive operations and consider implementing caching.")
        
        # Analyze memory usage
        memory_values = [m.memory_percent for m in metrics]
        avg_memory = np.mean(memory_values)
        
        if avg_memory > 70:
            recommendations.append("High memory usage detected. Review memory leaks and optimize data structures.")
        
        # Analyze response times
        response_values = [m.response_time_ms for m in metrics]
        avg_response = np.mean(response_values)
        p95_response = np.percentile(response_values, 95)
        
        if avg_response > 1000:
            recommendations.append("High average response time. Optimize database queries and implement caching.")
        
        if p95_response > 3000:
            recommendations.append("High response time spikes detected. Investigate slow queries and optimize critical paths.")
        
        # Analyze queue depth
        queue_values = [m.queue_depth for m in metrics]
        max_queue = np.max(queue_values)
        
        if max_queue > 50:
            recommendations.append("High queue depth detected. Consider increasing worker threads or implementing load balancing.")
        
        return recommendations
```

### Database Performance Optimization

```python
# ops/performance/database_optimizer.py
import psycopg2
from psycopg2.extras import DictCursor
import json
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class QueryPerformance:
    query_hash: str
    query_text: str
    calls: int
    total_exec_time_ms: float
    mean_exec_time_ms: float
    rows_examined: int
    rows_sent: int
    temp_tables_created: int

class DatabasePerformanceOptimizer:
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        
    def analyze_slow_queries(self, time_threshold_ms: float = 1000.0) -> List[QueryPerformance]:
        """Identify slow queries for optimization"""
        
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                
                # Enable pg_stat_statements if not already enabled
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
                
                # Get slow queries from pg_stat_statements
                cursor.execute("""
                    SELECT 
                        queryid,
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > %s
                    ORDER BY mean_exec_time DESC
                    LIMIT 50;
                """, (time_threshold_ms,))
                
                slow_queries = []
                for row in cursor.fetchall():
                    slow_queries.append(QueryPerformance(
                        query_hash=str(row['queryid']),
                        query_text=row['query'],
                        calls=row['calls'],
                        total_exec_time_ms=row['total_exec_time'],
                        mean_exec_time_ms=row['mean_exec_time'],
                        rows_examined=row['rows'],
                        rows_sent=row['rows'],
                        temp_tables_created=0  # Would need additional query
                    ))
                
                return slow_queries
    
    def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze index usage and suggest optimizations"""
        
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                
                # Check for unused indexes
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes
                    WHERE idx_tup_read = 0
                    AND idx_tup_fetch = 0
                    ORDER BY pg_relation_size(indexrelid) DESC;
                """)
                
                unused_indexes = [dict(row) for row in cursor.fetchall()]
                
                # Check for missing indexes (tables with high sequential scan ratio)
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        seq_tup_read::float / GREATEST(seq_scan, 1) as avg_seq_read
                    FROM pg_stat_user_tables
                    WHERE seq_scan > idx_scan 
                    AND seq_tup_read > 10000
                    ORDER BY seq_tup_read DESC;
                """)
                
                tables_needing_indexes = [dict(row) for row in cursor.fetchall()]
                
                # Check index bloat
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                        CASE 
                            WHEN pg_relation_size(indexrelid) > 0 THEN
                                pg_size_pretty(pg_relation_size(indexrelid) - 
                                              (relpages::bigint * 8192))
                            ELSE '0 bytes'
                        END as bloat_size
                    FROM pg_stat_user_indexes
                    JOIN pg_class ON pg_class.oid = indexrelid
                    WHERE pg_relation_size(indexrelid) > 1024 * 1024  -- > 1MB
                    ORDER BY pg_relation_size(indexrelid) DESC;
                """)
                
                index_bloat = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'unused_indexes': unused_indexes,
                    'tables_needing_indexes': tables_needing_indexes,
                    'index_bloat': index_bloat,
                    'recommendations': self._generate_index_recommendations(
                        unused_indexes, tables_needing_indexes, index_bloat
                    )
                }
    
    def optimize_table_statistics(self) -> Dict[str, int]:
        """Update table statistics for better query planning"""
        
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cursor:
                
                # Get all user tables
                cursor.execute("""
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog');
                """)
                
                tables = cursor.fetchall()
                optimized_count = 0
                
                for schema, table in tables:
                    try:
                        # Analyze table to update statistics
                        cursor.execute(f'ANALYZE "{schema}"."{table}";')
                        optimized_count += 1
                        
                    except Exception as e:
                        print(f"Failed to analyze {schema}.{table}: {e}")
                
                conn.commit()
                
                return {
                    'total_tables': len(tables),
                    'optimized_tables': optimized_count
                }
    
    def _generate_index_recommendations(self, unused: List, needs_indexes: List, bloat: List) -> List[str]:
        """Generate index optimization recommendations"""
        recommendations = []
        
        if unused:
            recommendations.append(f"Consider dropping {len(unused)} unused indexes to free up space and improve write performance.")
            
            # Recommend specific drops for large unused indexes
            large_unused = [idx for idx in unused if 'MB' in idx.get('index_size', '') or 'GB' in idx.get('index_size', '')]
            for idx in large_unused[:3]:  # Top 3
                recommendations.append(f"DROP INDEX {idx['schemaname']}.{idx['indexname']}; -- {idx['index_size']} unused")
        
        if needs_indexes:
            recommendations.append(f"Consider adding indexes to {len(needs_indexes)} tables with high sequential scan ratios.")
            
            # Recommend specific indexes for worst performers
            for table in needs_indexes[:3]:  # Top 3
                recommendations.append(f"Consider adding index on {table['schemaname']}.{table['tablename']} for frequently filtered columns.")
        
        if bloat:
            recommendations.append("Consider rebuilding bloated indexes to reclaim space:")
            for idx in bloat[:3]:  # Top 3 bloated
                recommendations.append(f"REINDEX INDEX {idx['schemaname']}.{idx['indexname']}; -- {idx['bloat_size']} bloat")
        
        return recommendations
```

---

## Cost Optimization

### Location: `ops/cost-optimization/`

### Resource Cost Analysis

```python
# ops/cost-optimization/cost_analyzer.py
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ResourceCost:
    resource_id: str
    resource_type: str
    service: str
    monthly_cost: float
    utilization: float
    tags: Dict[str, str]
    optimization_potential: float
    recommendations: List[str]

class CloudCostOptimizer:
    def __init__(self):
        self.ce_client = boto3.client('ce')  # Cost Explorer
        self.ec2_client = boto3.client('ec2')
        self.rds_client = boto3.client('rds')
        self.cloudwatch = boto3.client('cloudwatch')
        
    def analyze_compute_costs(self, days: int = 30) -> List[ResourceCost]:
        """Analyze EC2/EKS compute costs and optimization opportunities"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get cost and usage data
        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost', 'UsageQuantity'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}
            ],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Elastic Compute Cloud - Compute']
                }
            }
        )
        
        compute_resources = []
        
        for result_by_time in response['ResultsByTime']:
            for group in result_by_time['Groups']:
                service, instance_type = group['Keys']
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                usage = float(group['Metrics']['UsageQuantity']['Amount'])
                
                if cost > 10:  # Only analyze resources costing >$10/month
                    utilization = self._get_instance_utilization(instance_type)
                    recommendations = self._generate_compute_recommendations(
                        instance_type, cost, utilization
                    )
                    
                    compute_resources.append(ResourceCost(
                        resource_id=instance_type,
                        resource_type='EC2',
                        service='compute',
                        monthly_cost=cost,
                        utilization=utilization,
                        tags={},
                        optimization_potential=self._calculate_optimization_potential(cost, utilization),
                        recommendations=recommendations
                    ))
        
        return sorted(compute_resources, key=lambda x: x.optimization_potential, reverse=True)
    
    def analyze_database_costs(self, days: int = 30) -> List[ResourceCost]:
        """Analyze RDS costs and optimization opportunities"""
        
        # Get RDS instances
        rds_instances = self.rds_client.describe_db_instances()
        
        database_resources = []
        
        for instance in rds_instances['DBInstances']:
            instance_id = instance['DBInstanceIdentifier']
            instance_class = instance['DBInstanceClass']
            
            # Get cost data for this instance
            monthly_cost = self._get_rds_instance_cost(instance_id, days)
            
            if monthly_cost > 10:  # Only analyze resources costing >$10/month
                utilization = self._get_rds_utilization(instance_id)
                recommendations = self._generate_database_recommendations(
                    instance, monthly_cost, utilization
                )
                
                database_resources.append(ResourceCost(
                    resource_id=instance_id,
                    resource_type='RDS',
                    service='database',
                    monthly_cost=monthly_cost,
                    utilization=utilization,
                    tags=self._get_rds_tags(instance_id),
                    optimization_potential=self._calculate_optimization_potential(monthly_cost, utilization),
                    recommendations=recommendations
                ))
        
        return sorted(database_resources, key=lambda x: x.optimization_potential, reverse=True)
    
    def analyze_storage_costs(self) -> List[ResourceCost]:
        """Analyze storage costs and optimization opportunities"""
        
        # Get EBS volumes
        volumes = self.ec2_client.describe_volumes()
        
        storage_resources = []
        
        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            size_gb = volume['Size']
            volume_type = volume['VolumeType']
            
            # Calculate monthly cost based on volume type and size
            monthly_cost = self._calculate_ebs_cost(size_gb, volume_type)
            
            if monthly_cost > 5:  # Only analyze volumes costing >$5/month
                utilization = self._get_ebs_utilization(volume_id)
                recommendations = self._generate_storage_recommendations(
                    volume, monthly_cost, utilization
                )
                
                storage_resources.append(ResourceCost(
                    resource_id=volume_id,
                    resource_type='EBS',
                    service='storage',
                    monthly_cost=monthly_cost,
                    utilization=utilization,
                    tags=self._get_volume_tags(volume),
                    optimization_potential=self._calculate_optimization_potential(monthly_cost, utilization),
                    recommendations=recommendations
                ))
        
        return sorted(storage_resources, key=lambda x: x.optimization_potential, reverse=True)
    
    def generate_cost_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost optimization report"""
        
        compute_analysis = self.analyze_compute_costs()
        database_analysis = self.analyze_database_costs()
        storage_analysis = self.analyze_storage_costs()
        
        total_monthly_cost = (
            sum(r.monthly_cost for r in compute_analysis) +
            sum(r.monthly_cost for r in database_analysis) +
            sum(r.monthly_cost for r in storage_analysis)
        )
        
        total_optimization_potential = (
            sum(r.optimization_potential for r in compute_analysis) +
            sum(r.optimization_potential for r in database_analysis) +
            sum(r.optimization_potential for r in storage_analysis)
        )
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_monthly_cost': total_monthly_cost,
                'potential_monthly_savings': total_optimization_potential,
                'savings_percentage': (total_optimization_potential / total_monthly_cost * 100) if total_monthly_cost > 0 else 0,
                'resources_analyzed': len(compute_analysis) + len(database_analysis) + len(storage_analysis)
            },
            'cost_breakdown': {
                'compute': {
                    'monthly_cost': sum(r.monthly_cost for r in compute_analysis),
                    'optimization_potential': sum(r.optimization_potential for r in compute_analysis),
                    'resources': compute_analysis[:10]  # Top 10 for report
                },
                'database': {
                    'monthly_cost': sum(r.monthly_cost for r in database_analysis),
                    'optimization_potential': sum(r.optimization_potential for r in database_analysis),
                    'resources': database_analysis[:10]
                },
                'storage': {
                    'monthly_cost': sum(r.monthly_cost for r in storage_analysis),
                    'optimization_potential': sum(r.optimization_potential for r in storage_analysis),
                    'resources': storage_analysis[:10]
                }
            },
            'top_recommendations': self._get_top_recommendations(
                compute_analysis + database_analysis + storage_analysis
            ),
            'implementation_plan': self._create_implementation_plan(
                compute_analysis + database_analysis + storage_analysis
            )
        }
        
        return report
    
    def _generate_compute_recommendations(self, instance_type: str, cost: float, utilization: float) -> List[str]:
        """Generate compute optimization recommendations"""
        recommendations = []
        
        if utilization < 20:
            recommendations.append(f"Instance severely underutilized ({utilization:.1f}%). Consider downsizing or using Spot instances.")
        elif utilization < 40:
            recommendations.append(f"Instance underutilized ({utilization:.1f}%). Consider downsizing instance type.")
        
        if 'xlarge' in instance_type and utilization < 60:
            smaller_type = instance_type.replace('xlarge', 'large')
            potential_savings = cost * 0.5
            recommendations.append(f"Consider downsizing to {smaller_type} for ~${potential_savings:.2f}/month savings.")
        
        if cost > 100:
            recommendations.append("High-cost resource. Consider Reserved Instances for long-term workloads.")
        
        return recommendations
    
    def _generate_database_recommendations(self, instance: Dict, cost: float, utilization: float) -> List[str]:
        """Generate database optimization recommendations"""
        recommendations = []
        
        instance_class = instance['DBInstanceClass']
        multi_az = instance.get('MultiAZ', False)
        
        if utilization < 30:
            recommendations.append(f"Database underutilized ({utilization:.1f}%). Consider downsizing instance class.")
        
        if not multi_az and cost > 50:
            recommendations.append("Consider enabling Multi-AZ for production workloads.")
        
        if 'xlarge' in instance_class and utilization < 50:
            recommendations.append("Consider downsizing database instance class.")
        
        # Check backup retention
        backup_retention = instance.get('BackupRetentionPeriod', 0)
        if backup_retention > 7:
            recommendations.append(f"Backup retention is {backup_retention} days. Consider reducing if not required for compliance.")
        
        return recommendations
    
    def _create_implementation_plan(self, resources: List[ResourceCost]) -> List[Dict[str, Any]]:
        """Create prioritized implementation plan for cost optimizations"""
        
        # Sort by optimization potential
        high_impact_resources = [r for r in resources if r.optimization_potential > 20]
        medium_impact_resources = [r for r in resources if 5 < r.optimization_potential <= 20]
        
        plan = []
        
        # Phase 1: High impact, low risk changes
        if high_impact_resources:
            plan.append({
                'phase': 'Phase 1 - Quick Wins',
                'timeline': '1-2 weeks',
                'resources': high_impact_resources[:5],
                'estimated_savings': sum(r.optimization_potential for r in high_impact_resources[:5]),
                'risk_level': 'Low',
                'actions': [
                    'Resize underutilized instances',
                    'Clean up unused resources', 
                    'Switch to more cost-effective instance types'
                ]
            })
        
        # Phase 2: Medium impact changes
        if medium_impact_resources:
            plan.append({
                'phase': 'Phase 2 - Infrastructure Optimization',
                'timeline': '3-4 weeks',
                'resources': medium_impact_resources[:10],
                'estimated_savings': sum(r.optimization_potential for r in medium_impact_resources[:10]),
                'risk_level': 'Medium',
                'actions': [
                    'Implement Reserved Instances',
                    'Optimize storage types',
                    'Implement auto-scaling policies'
                ]
            })
        
        # Phase 3: Architectural changes
        plan.append({
            'phase': 'Phase 3 - Architectural Optimization',
            'timeline': '2-3 months',
            'estimated_savings': total_optimization_potential * 0.3,  # Additional 30%
            'risk_level': 'High',
            'actions': [
                'Implement spot instances for non-critical workloads',
                'Move to serverless architectures where appropriate',
                'Implement advanced caching strategies',
                'Optimize data transfer costs'
            ]
        })
        
        return plan
```

---

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Complete Epic 6: Production Operations & DevOps Excellence documentation", "status": "completed", "id": "79"}]