# ChurnGuard Deployment Guide

## 🚀 Production Deployment

### Prerequisites
- Node.js 18+ (LTS recommended)
- npm 8+ or yarn 1.22+
- 2GB+ RAM for build process
- SSL certificate for production

### Build Configuration

#### Environment Variables
Create `.env.production` file:
```env
# Theme Configuration
REACT_APP_THEME_STORAGE_KEY=churnguard-theme
REACT_APP_DEFAULT_THEME=system

# Organization Settings
REACT_APP_ORG_STORAGE_KEY=churnguard-organization
REACT_APP_ALLOW_CUSTOM_CSS=true

# Subscription Management
REACT_APP_SUBSCRIPTION_API_ENDPOINT=https://api.yourapp.com/subscriptions
REACT_APP_BILLING_PROVIDER=stripe

# Performance Monitoring
REACT_APP_PERFORMANCE_MONITORING=true
REACT_APP_PERFORMANCE_ENDPOINT=https://analytics.yourapp.com/performance

# Security
REACT_APP_CSP_ENABLED=true
REACT_APP_CSS_SANITIZATION=true

# API Configuration
REACT_APP_API_BASE_URL=https://api.yourapp.com
REACT_APP_API_TIMEOUT=10000
```

#### Build Script
```bash
#!/bin/bash
set -e

echo "🏗️  Building ChurnGuard for production..."

# Clean previous builds
rm -rf build/

# Install dependencies
npm ci --only=production

# Run tests
npm run test -- --coverage --watchAll=false

# Build application
npm run build

# Analyze bundle size
npm run build -- --analyze

echo "✅ Build completed successfully!"
```

---

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY yarn.lock* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Set build environment
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Install security updates
RUN apk update && apk upgrade

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'; frame-ancestors 'self';" always;
    
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html index.htm;
        
        # Security
        server_tokens off;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Static assets caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
        
        # API proxy (if needed)
        location /api/ {
            proxy_pass https://your-api-server.com/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }
        
        # SPA routing
        location / {
            try_files $uri $uri/ /index.html;
            
            # Cache control for HTML
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
        
        # Error pages
        error_page 404 /index.html;
        error_page 500 502 503 504 /50x.html;
        
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

### Docker Compose
```yaml
version: '3.8'

services:
  churnguard-ui:
    build: .
    ports:
      - "80:80"
      - "443:443"
    environment:
      - NODE_ENV=production
    volumes:
      - ./ssl:/etc/ssl/certs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      - api-server
      
  api-server:
    image: your-api-server:latest
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=churnguard
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## ☁️ Cloud Platform Deployment

### Vercel Deployment
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod

# Set environment variables
vercel env add REACT_APP_API_BASE_URL
vercel env add REACT_APP_SUBSCRIPTION_API_ENDPOINT
```

**vercel.json**:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "buildCommand": "npm run build",
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "headers": { "cache-control": "s-maxage=31536000,immutable" },
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "REACT_APP_API_BASE_URL": "@api_base_url",
    "REACT_APP_SUBSCRIPTION_API_ENDPOINT": "@subscription_endpoint"
  }
}
```

### Netlify Deployment
**netlify.toml**:
```toml
[build]
  publish = "build"
  command = "npm run build"

[build.environment]
  NODE_VERSION = "18"
  NPM_VERSION = "8"

[[redirects]]
  from = "/api/*"
  to = "https://your-api-server.com/:splat"
  status = 200

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/static/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.js"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.css"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

### AWS S3 + CloudFront
```bash
#!/bin/bash
# Deploy script for AWS

# Build application
npm run build

# Upload to S3
aws s3 sync build/ s3://your-churnguard-bucket --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"

echo "✅ Deployed to AWS successfully!"
```

**CloudFront Configuration**:
```json
{
  "Origins": [
    {
      "DomainName": "your-bucket.s3.amazonaws.com",
      "Id": "S3-churnguard",
      "S3OriginConfig": {
        "OriginAccessIdentity": ""
      }
    }
  ],
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-churnguard",
    "ViewerProtocolPolicy": "redirect-to-https",
    "Compress": true,
    "CachePolicyId": "your-cache-policy-id"
  },
  "CustomErrorResponses": [
    {
      "ErrorCode": 404,
      "ResponsePagePath": "/index.html",
      "ResponseCode": 200
    }
  ]
}
```

---

## 🔧 Configuration Management

### Feature Flags
```javascript
// config/features.js
export const FEATURE_FLAGS = {
  DARK_MODE: process.env.REACT_APP_DARK_MODE_ENABLED !== 'false',
  WHITE_LABELING: process.env.REACT_APP_WHITE_LABELING_ENABLED !== 'false',
  CUSTOM_CSS: process.env.REACT_APP_CUSTOM_CSS_ENABLED !== 'false',
  PERFORMANCE_MONITORING: process.env.REACT_APP_PERFORMANCE_MONITORING === 'true',
  ADVANCED_ANALYTICS: process.env.REACT_APP_ADVANCED_ANALYTICS !== 'false',
  LAYOUT_CUSTOMIZATION: process.env.REACT_APP_LAYOUT_CUSTOMIZATION !== 'false',
};

// Usage
import { FEATURE_FLAGS } from './config/features';

if (FEATURE_FLAGS.DARK_MODE) {
  // Enable dark mode
}
```

### Security Configuration
```javascript
// config/security.js
export const SECURITY_CONFIG = {
  CSP_ENABLED: process.env.REACT_APP_CSP_ENABLED === 'true',
  CSS_SANITIZATION: process.env.REACT_APP_CSS_SANITIZATION !== 'false',
  MAX_LOGO_SIZE: parseInt(process.env.REACT_APP_MAX_LOGO_SIZE) || 2097152, // 2MB
  ALLOWED_ORIGINS: process.env.REACT_APP_ALLOWED_ORIGINS?.split(',') || ['localhost'],
  XSS_PROTECTION: process.env.REACT_APP_XSS_PROTECTION !== 'false',
};
```

### API Configuration
```javascript
// config/api.js
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001',
  TIMEOUT: parseInt(process.env.REACT_APP_API_TIMEOUT) || 10000,
  RETRY_ATTEMPTS: parseInt(process.env.REACT_APP_API_RETRY_ATTEMPTS) || 3,
  RETRY_DELAY: parseInt(process.env.REACT_APP_API_RETRY_DELAY) || 1000,
};
```

---

## 📊 Performance Optimization

### Build Optimization
```javascript
// webpack.config.js (if ejected)
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
        },
        theme: {
          test: /[\\/]contexts[\\/]/,
          name: 'theme',
          priority: 20,
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
};
```

### Lazy Loading
```javascript
// components/LazyComponents.js
import { lazy, Suspense } from 'react';

const OrganizationSettings = lazy(() => import('./OrganizationSettings'));
const PremiumAnalytics = lazy(() => import('./PremiumAnalytics'));
const CustomizableLayout = lazy(() => import('./CustomizableLayout'));

export const LazyOrganizationSettings = (props) => (
  <Suspense fallback={<div>Loading settings...</div>}>
    <OrganizationSettings {...props} />
  </Suspense>
);

export const LazyPremiumAnalytics = (props) => (
  <Suspense fallback={<div>Loading analytics...</div>}>
    <PremiumAnalytics {...props} />
  </Suspense>
);
```

### CDN Configuration
```javascript
// config/cdn.js
export const CDN_CONFIG = {
  LOGO_CDN: process.env.REACT_APP_LOGO_CDN || 'https://cdn.yourapp.com/logos',
  ASSETS_CDN: process.env.REACT_APP_ASSETS_CDN || 'https://cdn.yourapp.com/assets',
  CACHE_DURATION: process.env.REACT_APP_CACHE_DURATION || '31536000', // 1 year
};
```

---

## 🔍 Monitoring & Logging

### Error Tracking
```javascript
// utils/errorTracking.js
import * as Sentry from "@sentry/react";

export const initErrorTracking = () => {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_DSN,
    environment: process.env.NODE_ENV,
    integrations: [
      new Sentry.BrowserTracing(),
    ],
    tracesSampleRate: 0.1,
  });
};

export const trackError = (error, context = {}) => {
  Sentry.captureException(error, { extra: context });
};
```

### Performance Monitoring
```javascript
// utils/performance.js
export const trackPerformance = (metricName, value) => {
  if (window.gtag) {
    window.gtag('event', 'timing_complete', {
      name: metricName,
      value: Math.round(value),
    });
  }
  
  if (window.analytics) {
    window.analytics.track('Performance Metric', {
      metric: metricName,
      value,
      timestamp: Date.now(),
    });
  }
};

export const measureThemeSwitch = (callback) => {
  const start = performance.now();
  callback();
  const end = performance.now();
  trackPerformance('theme_switch_duration', end - start);
};
```

### Health Checks
```javascript
// utils/healthCheck.js
export const performHealthCheck = async () => {
  const checks = [];
  
  // API connectivity
  try {
    const response = await fetch('/api/health', { timeout: 5000 });
    checks.push({ 
      name: 'api', 
      status: response.ok ? 'healthy' : 'unhealthy',
      responseTime: response.headers.get('x-response-time')
    });
  } catch (error) {
    checks.push({ name: 'api', status: 'unhealthy', error: error.message });
  }
  
  // Theme system
  const themeElements = document.querySelectorAll('[class*="dark:"]');
  checks.push({
    name: 'theme_system',
    status: themeElements.length > 0 ? 'healthy' : 'unhealthy',
    elementCount: themeElements.length
  });
  
  // Local storage
  try {
    localStorage.setItem('health_check', 'test');
    localStorage.removeItem('health_check');
    checks.push({ name: 'local_storage', status: 'healthy' });
  } catch (error) {
    checks.push({ name: 'local_storage', status: 'unhealthy' });
  }
  
  return {
    timestamp: new Date().toISOString(),
    overall: checks.every(check => check.status === 'healthy') ? 'healthy' : 'unhealthy',
    checks
  };
};
```

---

## 🔒 Security Checklist

### Pre-deployment Security Audit
- [ ] CSP headers configured
- [ ] XSS protection enabled  
- [ ] HTTPS enforced
- [ ] Sensitive data not in localStorage
- [ ] API endpoints secured
- [ ] Custom CSS sanitization enabled
- [ ] File upload validation implemented
- [ ] Rate limiting configured
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies scanned for vulnerabilities

### Security Headers
```nginx
# Add to nginx config
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https:; media-src 'self'; object-src 'none'; child-src 'none'; worker-src 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'self';" always;
```

---

## 🚨 Troubleshooting

### Common Deployment Issues

**Theme not working in production:**
```bash
# Check if CSS custom properties are supported
# Verify dark mode classes are included in build
# Ensure localStorage is accessible
```

**Performance issues:**
```bash
# Analyze bundle size
npm run build -- --analyze

# Check for unused dependencies
npx depcheck

# Optimize images
npm install --save-dev imagemin imagemin-webp
```

**API connectivity issues:**
```bash
# Verify CORS settings
# Check environment variables
# Test API endpoints manually
# Verify SSL certificates
```

### Rollback Strategy
```bash
#!/bin/bash
# rollback.sh

# Get previous deployment
PREVIOUS_VERSION=$(git describe --tags --abbrev=0 HEAD~1)

echo "Rolling back to version: $PREVIOUS_VERSION"

# Checkout previous version
git checkout $PREVIOUS_VERSION

# Rebuild and deploy
npm run build
./deploy.sh

echo "✅ Rollback completed"
```

---

## 📈 Scaling Considerations

### Load Balancing
```nginx
# nginx load balancer config
upstream churnguard_app {
    server app1.example.com:80 weight=3;
    server app2.example.com:80 weight=2;
    server app3.example.com:80 backup;
}

server {
    location / {
        proxy_pass http://churnguard_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### CDN Setup
```bash
# CloudFlare configuration
{
  "cache_level": "aggressive",
  "browser_cache_ttl": 31536000,
  "edge_cache_ttl": 86400,
  "cache_everything": true
}
```

### Database Scaling
```yaml
# docker-compose.production.yml
services:
  postgres-master:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=master
      - POSTGRES_REPLICATION_USER=replicator
      
  postgres-slave:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_HOST=postgres-master
```

---

## 📞 Support & Maintenance

### Monitoring Dashboard
- **Uptime**: 99.9% target
- **Response Time**: <200ms average
- **Error Rate**: <0.1%
- **Theme Switch Performance**: <100ms

### Maintenance Schedule
- **Weekly**: Dependency updates, security patches
- **Monthly**: Performance review, bundle size analysis
- **Quarterly**: Security audit, penetration testing
- **Annually**: Major version upgrades, architecture review

### Emergency Contacts
- **DevOps Team**: devops@yourcompany.com
- **Security Team**: security@yourcompany.com
- **Product Team**: product@yourcompany.com

### Backup Strategy
- **Code**: Git repository with multiple remotes
- **Configuration**: Environment variables backed up
- **Assets**: CDN with redundancy
- **Database**: Daily automated backups with point-in-time recovery

---

This deployment guide ensures a robust, secure, and scalable production deployment of the enhanced ChurnGuard platform with all UI enhancements and SaaS features properly configured.