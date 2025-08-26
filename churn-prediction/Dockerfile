# ChurnGuard Frontend Dockerfile (Create React App)
# Multi-stage build for production optimization
# Epic 1 - CG-001: Docker Containerization

# Stage 1: Build stage
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code and configuration files
COPY src/ ./src/
COPY public/ ./public/
COPY tailwind.config.js ./

# Build the application
RUN npm run build

# Stage 2: Production stage
FROM nginx:alpine AS production

# Install security updates and curl for health checks
RUN apk update && apk upgrade && apk add --no-cache curl

# Copy built application from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Create custom nginx configuration for SPA routing
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen       80;
    server_name  localhost;
    root   /usr/share/nginx/html;
    index  index.html index.htm;

    # Handle client-side routing for React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
}
EOF

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S churnguard -u 1001

# Change ownership of nginx directories
RUN chown -R churnguard:nodejs /var/cache/nginx && \
    chown -R churnguard:nodejs /var/log/nginx && \
    chown -R churnguard:nodejs /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R churnguard:nodejs /var/run/nginx.pid

# Switch to non-root user
USER churnguard

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]