# ChurnGuard Deployment Guide

## 🚀 Production Deployment

This guide covers deploying ChurnGuard Analytics Platform to production environments with high availability, security, and performance optimization.

## 📋 Prerequisites

### System Requirements

**Minimum Production Requirements:**
- **CPU**: 8 cores (16 vCPUs recommended)
- **Memory**: 32 GB RAM (64 GB recommended)
- **Storage**: 500 GB SSD (1 TB+ recommended)
- **Network**: 1 Gbps bandwidth

**Recommended Production Setup:**
- **Load Balancers**: 2x instances (HA setup)
- **Application Servers**: 3x instances (auto-scaling group)
- **Database**: Multi-AZ deployment with read replicas
- **Cache**: Redis Cluster (3+ nodes)
- **Message Queue**: RabbitMQ/Apache Kafka cluster

### Infrastructure Dependencies

1. **Time-Series Database**:
   - InfluxDB 2.0+ or TimescaleDB 2.5+
   - 3-node cluster for high availability

2. **Primary Database**:
   - PostgreSQL 14+ or MySQL 8.0+
   - Master-replica setup with automated failover

3. **Cache Layer**:
   - Redis 6.0+ cluster
   - Minimum 3 nodes with sentinel

4. **Message Queue**:
   - Apache Kafka 3.0+ or RabbitMQ 3.10+
   - Multi-broker setup for fault tolerance

5. **Container Orchestration**:
   - Kubernetes 1.24+ or Docker Swarm
   - Container registry (DockerHub, ECR, GCR)

## 🐳 Docker Deployment

### Build Production Images

```bash
# Build application image
docker build -t churnguard-app:latest .

# Build with specific version tag
docker build -t churnguard-app:v1.0.0 .

# Push to registry
docker tag churnguard-app:latest your-registry.com/churnguard-app:v1.0.0
docker push your-registry.com/churnguard-app:v1.0.0
```

### Docker Compose Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - app
    restart: unless-stopped

  # Application Servers
  app:
    image: churnguard-app:v1.0.0
    deploy:
      replicas: 3
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@postgres-cluster:5432/churnguard
      - REDIS_URL=redis://redis-cluster:6379
      - INFLUXDB_URL=http://influxdb-cluster:8086
      - JWT_SECRET=${JWT_SECRET}
      - API_RATE_LIMIT=5000
    depends_on:
      - postgres
      - redis
      - influxdb
    restart: unless-stopped

  # PostgreSQL Primary Database
  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=churnguard
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # InfluxDB Time-Series Database
  influxdb:
    image: influxdb:2.5
    environment:
      - INFLUXDB_DB=churnguard_metrics
      - INFLUXDB_ADMIN_USER=${INFLUX_USER}
      - INFLUXDB_ADMIN_PASSWORD=${INFLUX_PASSWORD}
    volumes:
      - influxdb_data:/var/lib/influxdb2
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  influxdb_data:

networks:
  default:
    driver: overlay
    attachable: true
```

### Environment Variables

Create `.env.production`:

```bash
# Database Configuration
DB_USER=churnguard_user
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://churnguard_user:your_secure_password@postgres-cluster:5432/churnguard

# Redis Configuration
REDIS_PASSWORD=your_redis_password
REDIS_URL=redis://:your_redis_password@redis-cluster:6379

# InfluxDB Configuration
INFLUX_USER=churnguard_admin
INFLUX_PASSWORD=your_influx_password
INFLUXDB_URL=http://influxdb-cluster:8086
INFLUXDB_TOKEN=your_influxdb_token

# Application Configuration
NODE_ENV=production
JWT_SECRET=your_jwt_secret_key_min_32_chars
API_RATE_LIMIT=5000
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Analytics Configuration
ANALYTICS_BATCH_SIZE=1000
ANALYTICS_FLUSH_INTERVAL=5000
ANOMALY_DETECTION_ENABLED=true

# Theming Configuration
CSS_VALIDATION_LEVEL=strict
CUSTOM_DOMAINS_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=info
METRICS_ENABLED=true
```

## ☸️ Kubernetes Deployment

### Namespace and Resources

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: churnguard
  labels:
    name: churnguard
---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: churnguard-config
  namespace: churnguard
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  ANALYTICS_BATCH_SIZE: "1000"
  API_RATE_LIMIT: "5000"
```

### Application Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churnguard-app
  namespace: churnguard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: churnguard-app
  template:
    metadata:
      labels:
        app: churnguard-app
    spec:
      containers:
      - name: churnguard-app
        image: churnguard-app:v1.0.0
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: churnguard-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: churnguard-secrets
              key: jwt-secret
        envFrom:
        - configMapRef:
            name: churnguard-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service and Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: churnguard-app-service
  namespace: churnguard
spec:
  selector:
    app: churnguard-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: ClusterIP
---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: churnguard-ingress
  namespace: churnguard
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.churnguard.ai
    - app.churnguard.ai
    secretName: churnguard-tls
  rules:
  - host: api.churnguard.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: churnguard-app-service
            port:
              number: 80
  - host: app.churnguard.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: churnguard-app-service
            port:
              number: 80
```

### Database Deployment

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: churnguard
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: churnguard
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 100Gi
```

## 🔒 Security Configuration

### SSL/TLS Certificate Setup

```bash
# Install cert-manager for automatic SSL certificates
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.10.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Secrets Management

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: churnguard-secrets
  namespace: churnguard
type: Opaque
stringData:
  database-url: "postgresql://user:password@postgres:5432/churnguard"
  jwt-secret: "your-jwt-secret-min-32-characters"
  redis-password: "your-redis-password"
  influxdb-token: "your-influxdb-token"
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: churnguard
type: Opaque
stringData:
  username: "churnguard_user"
  password: "your-secure-postgres-password"
```

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: churnguard-network-policy
  namespace: churnguard
spec:
  podSelector:
    matchLabels:
      app: churnguard-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

## 📊 Monitoring and Observability

### Prometheus Monitoring

```yaml
# monitoring.yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: churnguard-metrics
  namespace: churnguard
spec:
  selector:
    matchLabels:
      app: churnguard-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Logging Configuration

```yaml
# logging-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: churnguard
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/churnguard-app-*.log
      pos_file /var/log/fluentd-churnguard.log.pos
      tag churnguard.*
      format json
    </source>
    
    <match churnguard.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name churnguard-logs
    </match>
```

### Health Check Endpoints

```javascript
// Health check implementation in app
app.get('/health', (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION,
    checks: {
      database: checkDatabase(),
      redis: checkRedis(),
      influxdb: checkInfluxDB()
    }
  };
  
  const isHealthy = Object.values(health.checks).every(check => check.status === 'healthy');
  res.status(isHealthy ? 200 : 503).json(health);
});

app.get('/ready', (req, res) => {
  // Readiness probe - can accept traffic
  res.status(200).json({ status: 'ready' });
});

app.get('/metrics', (req, res) => {
  // Prometheus metrics endpoint
  res.set('Content-Type', register.contentType);
  res.end(register.metrics());
});
```

## 🗄️ Database Migration and Backup

### Database Migration

```bash
# Run database migrations
kubectl exec -it deployment/churnguard-app -n churnguard -- npm run migrate

# Or using init containers
apiVersion: apps/v1
kind: Job
metadata:
  name: churnguard-migration
  namespace: churnguard
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: churnguard-app:v1.0.0
        command: ['npm', 'run', 'migrate']
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: churnguard-secrets
              key: database-url
      restartPolicy: Never
```

### Automated Backup

```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: churnguard
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:14-alpine
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL | gzip > /backup/churnguard-$(date +%Y%m%d-%H%M%S).sql.gz
              aws s3 cp /backup/churnguard-$(date +%Y%m%d-%H%M%S).sql.gz s3://your-backup-bucket/
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: churnguard-secrets
                  key: database-url
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          volumes:
          - name: backup-volume
            emptyDir: {}
          restartPolicy: OnFailure
```

## 🔧 Performance Optimization

### Application Optimization

```javascript
// Production performance configuration
const config = {
  // Node.js cluster mode
  cluster: {
    enabled: true,
    workers: require('os').cpus().length
  },
  
  // Cache configuration
  cache: {
    redis: {
      host: process.env.REDIS_HOST,
      port: process.env.REDIS_PORT,
      password: process.env.REDIS_PASSWORD,
      maxRetriesPerRequest: 3,
      retryDelayOnFailover: 100,
      lazyConnect: true
    },
    ttl: {
      analytics: 300,     // 5 minutes
      insights: 1800,     // 30 minutes
      experiments: 3600   // 1 hour
    }
  },
  
  // Rate limiting
  rateLimit: {
    windowMs: 60 * 1000, // 1 minute
    max: process.env.API_RATE_LIMIT || 1000,
    standardHeaders: true,
    legacyHeaders: false
  },
  
  // Database connection pooling
  database: {
    pool: {
      min: 10,
      max: 100,
      acquire: 30000,
      idle: 10000
    }
  }
};
```

### Load Balancer Configuration

```nginx
# nginx.conf
upstream churnguard_backend {
    least_conn;
    server churnguard-app-1:3000 max_fails=3 fail_timeout=30s;
    server churnguard-app-2:3000 max_fails=3 fail_timeout=30s;
    server churnguard-app-3:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.churnguard.ai;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/churnguard.crt;
    ssl_certificate_key /etc/ssl/private/churnguard.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://churnguard_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
    }
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🚨 Disaster Recovery

### Backup Strategy

1. **Database Backups**:
   - Automated daily backups to S3/GCS
   - Point-in-time recovery enabled
   - Cross-region replication

2. **Time-Series Data**:
   - InfluxDB snapshots every 6 hours
   - Retention policy: 90 days full, 1 year aggregated

3. **Configuration Backups**:
   - Kubernetes manifests in git repository
   - Secrets backed up to encrypted storage

### Recovery Procedures

```bash
# Database Recovery
kubectl apply -f disaster-recovery/postgres-restore-job.yaml

# Application Recovery
kubectl rollout restart deployment/churnguard-app -n churnguard

# DNS Failover (if using Route 53)
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://failover-dns.json
```

## 📞 Support and Troubleshooting

### Common Issues

1. **High Memory Usage**:
   ```bash
   # Check memory usage
   kubectl top pods -n churnguard
   
   # Scale up if needed
   kubectl scale deployment churnguard-app --replicas=5 -n churnguard
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database connectivity
   kubectl exec -it deployment/churnguard-app -n churnguard -- pg_isready -h postgres -p 5432
   ```

3. **SSL Certificate Issues**:
   ```bash
   # Check certificate status
   kubectl describe certificate churnguard-tls -n churnguard
   
   # Renew certificate if needed
   kubectl delete certificate churnguard-tls -n churnguard
   ```

### Support Contacts

- **Emergency**: DevOps on-call rotation
- **General Support**: support@churnguard.ai
- **Documentation**: https://docs.churnguard.ai/deployment