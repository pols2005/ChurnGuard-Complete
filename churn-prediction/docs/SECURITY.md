# ChurnGuard Security Documentation

## 🔒 Security Overview

ChurnGuard implements enterprise-grade security measures across all layers of the platform, including data protection, access controls, secure communications, and compliance with industry standards.

## 🛡️ Security Architecture

### Defense in Depth Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    Edge Security                        │
│  WAF, DDoS Protection, Rate Limiting, SSL/TLS         │
├─────────────────────────────────────────────────────────┤
│                  Network Security                      │
│  VPC, Security Groups, Network Policies, VPN          │
├─────────────────────────────────────────────────────────┤
│                Application Security                     │
│  Authentication, Authorization, Input Validation       │
├─────────────────────────────────────────────────────────┤
│                   Data Security                        │
│  Encryption at Rest, Encryption in Transit, Masking   │
├─────────────────────────────────────────────────────────┤
│                Infrastructure Security                  │
│  Container Security, Secret Management, Monitoring     │
└─────────────────────────────────────────────────────────┘
```

## 🔐 Authentication & Authorization

### Multi-Factor Authentication (MFA)

ChurnGuard supports multiple MFA methods:

```javascript
// MFA Configuration
const mfaConfig = {
  methods: ['totp', 'sms', 'email', 'webauthn'],
  required: process.env.MFA_REQUIRED === 'true',
  backupCodes: {
    enabled: true,
    count: 8,
    length: 8
  },
  trustedDevices: {
    enabled: true,
    duration: 30 * 24 * 60 * 60 * 1000 // 30 days
  }
};

// TOTP Implementation
class TOTPAuthenticator {
  generateSecret(userEmail) {
    const secret = speakeasy.generateSecret({
      name: `ChurnGuard (${userEmail})`,
      issuer: 'ChurnGuard',
      length: 32
    });
    return secret;
  }
  
  verifyToken(token, secret) {
    return speakeasy.totp.verify({
      secret: secret,
      encoding: 'base32',
      token: token,
      window: 2 // Allow 2 time periods variance
    });
  }
}
```

### Role-Based Access Control (RBAC)

```javascript
// Role Definitions
const roles = {
  SUPER_ADMIN: {
    name: 'Super Admin',
    permissions: ['*'] // All permissions
  },
  ORG_ADMIN: {
    name: 'Organization Admin',
    permissions: [
      'org:read', 'org:write', 'org:delete',
      'user:read', 'user:write', 'user:invite',
      'analytics:read', 'analytics:write',
      'experiment:read', 'experiment:write',
      'theme:read', 'theme:write'
    ]
  },
  ANALYST: {
    name: 'Data Analyst',
    permissions: [
      'analytics:read', 'analytics:export',
      'experiment:read', 'experiment:analyze',
      'dashboard:read', 'dashboard:create'
    ]
  },
  VIEWER: {
    name: 'Read-Only User',
    permissions: [
      'analytics:read', 'dashboard:read',
      'experiment:read'
    ]
  }
};

// Permission Middleware
const requirePermission = (permission) => {
  return async (req, res, next) => {
    const user = req.user;
    const orgId = req.headers['x-organization-id'];
    
    if (await hasPermission(user, orgId, permission)) {
      next();
    } else {
      res.status(403).json({ error: 'Insufficient permissions' });
    }
  };
};
```

### JWT Token Security

```javascript
// JWT Configuration
const jwtConfig = {
  accessToken: {
    expiresIn: '15m',
    algorithm: 'RS256',
    issuer: 'churnguard.ai',
    audience: 'churnguard-api'
  },
  refreshToken: {
    expiresIn: '7d',
    algorithm: 'HS256',
    rotateOnRefresh: true
  }
};

// Token Generation
class JWTManager {
  generateAccessToken(user, permissions) {
    const payload = {
      sub: user.id,
      email: user.email,
      org_id: user.organization_id,
      permissions: permissions,
      iat: Math.floor(Date.now() / 1000),
      jti: uuidv4() // Unique token ID
    };
    
    return jwt.sign(payload, this.privateKey, {
      algorithm: 'RS256',
      expiresIn: '15m',
      issuer: 'churnguard.ai',
      audience: 'churnguard-api'
    });
  }
  
  validateToken(token) {
    try {
      return jwt.verify(token, this.publicKey, {
        algorithms: ['RS256'],
        issuer: 'churnguard.ai',
        audience: 'churnguard-api'
      });
    } catch (error) {
      throw new Error('Invalid token');
    }
  }
}
```

## 🔒 Data Protection

### Encryption at Rest

All sensitive data is encrypted using AES-256 encryption:

```javascript
// Database Encryption Configuration
const encryptionConfig = {
  algorithm: 'aes-256-gcm',
  keyDerivation: 'pbkdf2',
  keyLength: 32,
  ivLength: 16,
  tagLength: 16,
  iterations: 100000
};

class DataEncryption {
  encrypt(plaintext, key) {
    const salt = crypto.randomBytes(32);
    const iv = crypto.randomBytes(16);
    const derivedKey = crypto.pbkdf2Sync(key, salt, 100000, 32, 'sha256');
    
    const cipher = crypto.createCipher('aes-256-gcm', derivedKey, iv);
    let ciphertext = cipher.update(plaintext, 'utf8', 'base64');
    ciphertext += cipher.final('base64');
    
    const tag = cipher.getAuthTag();
    
    return {
      ciphertext,
      salt: salt.toString('base64'),
      iv: iv.toString('base64'),
      tag: tag.toString('base64')
    };
  }
  
  decrypt(encryptedData, key) {
    const salt = Buffer.from(encryptedData.salt, 'base64');
    const iv = Buffer.from(encryptedData.iv, 'base64');
    const tag = Buffer.from(encryptedData.tag, 'base64');
    const derivedKey = crypto.pbkdf2Sync(key, salt, 100000, 32, 'sha256');
    
    const decipher = crypto.createDecipher('aes-256-gcm', derivedKey, iv);
    decipher.setAuthTag(tag);
    
    let plaintext = decipher.update(encryptedData.ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');
    
    return plaintext;
  }
}
```

### Encryption in Transit

All communications use TLS 1.2+ with strong cipher suites:

```nginx
# SSL/TLS Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
```

### Data Masking and Anonymization

```javascript
// Data Masking for PII
class DataMasker {
  maskEmail(email) {
    const [username, domain] = email.split('@');
    const maskedUsername = username.substring(0, 2) + '*'.repeat(username.length - 2);
    return `${maskedUsername}@${domain}`;
  }
  
  maskPhone(phone) {
    return phone.replace(/(\d{3})\d{3}(\d{4})/, '$1***$2');
  }
  
  maskCreditCard(cardNumber) {
    return cardNumber.replace(/\d(?=\d{4})/g, '*');
  }
  
  anonymizeUserId(userId) {
    return crypto.createHash('sha256').update(userId + process.env.ANONYMIZATION_SALT).digest('hex').substring(0, 16);
  }
}

// Analytics Data Anonymization
class AnalyticsAnonymizer {
  anonymizeEvent(event) {
    return {
      ...event,
      customer_id: this.dataMasker.anonymizeUserId(event.customer_id),
      ip_address: this.maskIpAddress(event.ip_address),
      user_agent: this.maskUserAgent(event.user_agent)
    };
  }
}
```

## 🛡️ Input Validation and Sanitization

### API Input Validation

```javascript
// Input Validation Schemas
const { body, query, param, validationResult } = require('express-validator');

// Customer ID validation
const customerIdValidation = [
  param('customer_id')
    .isUUID(4)
    .withMessage('Customer ID must be a valid UUID')
    .customSanitizer(value => validator.escape(value))
];

// Analytics event validation
const analyticsEventValidation = [
  body('event_type')
    .isIn(['page_view', 'click', 'conversion', 'signup', 'churn'])
    .withMessage('Invalid event type'),
  body('properties')
    .isObject()
    .custom((value) => {
      // Prevent prototype pollution
      if (Object.keys(value).some(key => ['__proto__', 'constructor', 'prototype'].includes(key))) {
        throw new Error('Invalid property name');
      }
      return true;
    }),
  body('timestamp')
    .isISO8601()
    .toDate()
    .withMessage('Timestamp must be valid ISO 8601 date')
];

// Validation middleware
const validateRequest = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: 'Validation failed',
      details: errors.array()
    });
  }
  next();
};
```

### CSS Security for Theming

```javascript
// CSS Sanitization for Theme Engine
class CSSSanitizer {
  constructor() {
    this.allowedProperties = new Set([
      'color', 'background-color', 'font-family', 'font-size',
      'margin', 'padding', 'border', 'border-radius',
      'width', 'height', 'display', 'position'
    ]);
    
    this.blockedPatterns = [
      /javascript:/i,
      /vbscript:/i,
      /data:text\/html/i,
      /expression\s*\(/i,
      /@import/i,
      /behavior\s*:/i
    ];
  }
  
  sanitizeCSS(css) {
    // Remove potentially dangerous patterns
    for (const pattern of this.blockedPatterns) {
      if (pattern.test(css)) {
        throw new Error('Potentially dangerous CSS detected');
      }
    }
    
    // Parse and validate CSS rules
    const ast = cssTree.parse(css);
    const sanitizedRules = [];
    
    cssTree.walk(ast, (node) => {
      if (node.type === 'Declaration') {
        if (this.allowedProperties.has(node.property)) {
          sanitizedRules.push(cssTree.generate(node));
        }
      }
    });
    
    return sanitizedRules.join('\n');
  }
}
```

## 🔍 Security Monitoring

### Real-time Security Monitoring

```javascript
// Security Event Monitoring
class SecurityMonitor {
  constructor() {
    this.suspiciousPatterns = [
      { name: 'SQL Injection', pattern: /(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b)/i },
      { name: 'XSS Attempt', pattern: /<script|javascript:|on\w+\s*=/i },
      { name: 'Path Traversal', pattern: /\.\.(\\|\/)/i },
      { name: 'Command Injection', pattern: /[;&|`$(){}]/i }
    ];
  }
  
  monitorRequest(req) {
    const requestData = {
      url: req.url,
      body: JSON.stringify(req.body),
      query: JSON.stringify(req.query),
      headers: JSON.stringify(req.headers),
      ip: req.ip,
      userAgent: req.get('user-agent')
    };
    
    // Check for suspicious patterns
    const threats = this.detectThreats(requestData);
    
    if (threats.length > 0) {
      this.logSecurityEvent({
        type: 'SUSPICIOUS_REQUEST',
        threats: threats,
        request: requestData,
        timestamp: new Date(),
        severity: this.calculateThreatSeverity(threats)
      });
      
      // Rate limit or block if high severity
      if (threats.some(t => t.severity === 'HIGH')) {
        throw new SecurityError('Request blocked due to security concerns');
      }
    }
  }
  
  detectThreats(data) {
    const threats = [];
    const dataString = JSON.stringify(data).toLowerCase();
    
    for (const pattern of this.suspiciousPatterns) {
      if (pattern.pattern.test(dataString)) {
        threats.push({
          name: pattern.name,
          severity: 'HIGH',
          pattern: pattern.pattern.source
        });
      }
    }
    
    return threats;
  }
}
```

### Audit Logging

```javascript
// Comprehensive Audit Logging
class AuditLogger {
  logAuthEvent(user, action, result, metadata = {}) {
    this.writeAuditLog({
      category: 'AUTHENTICATION',
      user_id: user?.id,
      email: user?.email,
      action: action,
      result: result,
      ip_address: metadata.ip,
      user_agent: metadata.userAgent,
      timestamp: new Date(),
      session_id: metadata.sessionId
    });
  }
  
  logDataAccess(user, resource, action, metadata = {}) {
    this.writeAuditLog({
      category: 'DATA_ACCESS',
      user_id: user.id,
      organization_id: user.organization_id,
      resource_type: resource.type,
      resource_id: resource.id,
      action: action,
      timestamp: new Date(),
      ip_address: metadata.ip,
      result: metadata.result || 'SUCCESS'
    });
  }
  
  logPrivilegedAction(user, action, target, metadata = {}) {
    this.writeAuditLog({
      category: 'PRIVILEGED_ACTION',
      user_id: user.id,
      action: action,
      target_type: target.type,
      target_id: target.id,
      timestamp: new Date(),
      justification: metadata.justification,
      approval_required: metadata.approvalRequired || false
    });
  }
  
  writeAuditLog(entry) {
    // Write to secure audit log with integrity protection
    const logEntry = {
      ...entry,
      id: uuidv4(),
      hash: this.calculateHash(entry)
    };
    
    // Store in tamper-proof log system
    this.auditStorage.append(logEntry);
    
    // Send to SIEM if high-risk event
    if (this.isHighRiskEvent(entry)) {
      this.siemConnector.sendAlert(logEntry);
    }
  }
}
```

## 🚨 Incident Response

### Automated Threat Response

```javascript
// Automated Security Response
class ThreatResponseSystem {
  constructor() {
    this.responseActions = {
      'BRUTE_FORCE': this.handleBruteForce.bind(this),
      'SQL_INJECTION': this.handleSQLInjection.bind(this),
      'XSS_ATTEMPT': this.handleXSSAttempt.bind(this),
      'UNUSUAL_ACCESS': this.handleUnusualAccess.bind(this)
    };
  }
  
  async handleSecurityEvent(event) {
    const handler = this.responseActions[event.type];
    if (handler) {
      await handler(event);
    }
    
    // Always log and alert
    await this.logIncident(event);
    await this.sendAlerts(event);
  }
  
  async handleBruteForce(event) {
    // Rate limit the IP
    await this.rateLimit.blockIP(event.ip_address, 3600); // 1 hour
    
    // Lock the account if too many attempts
    if (event.attempt_count > 5) {
      await this.userService.lockAccount(event.user_id, 1800); // 30 minutes
    }
    
    // Send security notification to user
    await this.notificationService.sendSecurityAlert(event.user_id, {
      type: 'SUSPICIOUS_LOGIN_ATTEMPTS',
      ip: event.ip_address,
      timestamp: event.timestamp
    });
  }
  
  async handleSQLInjection(event) {
    // Immediately block the IP
    await this.firewall.blockIP(event.ip_address);
    
    // Alert security team
    await this.alerting.sendCriticalAlert({
      title: 'SQL Injection Attempt Detected',
      severity: 'CRITICAL',
      details: event,
      action_required: true
    });
    
    // Log detailed forensic information
    await this.forensics.captureNetworkTrace(event);
  }
}
```

### Security Playbooks

```yaml
# security-playbooks.yaml
playbooks:
  data_breach:
    title: "Data Breach Response"
    severity: CRITICAL
    steps:
      - action: isolate_affected_systems
        timeout: 300 # 5 minutes
      - action: notify_security_team
        timeout: 600 # 10 minutes
      - action: preserve_evidence
        timeout: 1800 # 30 minutes
      - action: assess_impact
        timeout: 3600 # 1 hour
      - action: notify_customers
        condition: customer_data_affected
        timeout: 21600 # 6 hours
  
  account_compromise:
    title: "Account Compromise Response"
    severity: HIGH
    steps:
      - action: lock_affected_accounts
        timeout: 60 # 1 minute
      - action: invalidate_sessions
        timeout: 300 # 5 minutes
      - action: force_password_reset
        timeout: 600 # 10 minutes
      - action: notify_affected_users
        timeout: 1800 # 30 minutes
```

## 📋 Compliance and Standards

### SOC 2 Type II Compliance

ChurnGuard implements SOC 2 security controls:

1. **Security**: Logical and physical access controls
2. **Availability**: System operation and monitoring
3. **Processing Integrity**: System processing accuracy
4. **Confidentiality**: Information protection
5. **Privacy**: Personal information handling

### GDPR Compliance

```javascript
// GDPR Compliance Implementation
class GDPRCompliance {
  async handleDataSubjectRequest(requestType, userId) {
    switch (requestType) {
      case 'ACCESS':
        return await this.exportUserData(userId);
      case 'RECTIFICATION':
        return await this.updateUserData(userId);
      case 'ERASURE':
        return await this.deleteUserData(userId);
      case 'PORTABILITY':
        return await this.exportPortableData(userId);
      case 'RESTRICTION':
        return await this.restrictProcessing(userId);
      case 'OBJECTION':
        return await this.handleObjection(userId);
    }
  }
  
  async deleteUserData(userId) {
    // Anonymize analytics data
    await this.analytics.anonymizeUserData(userId);
    
    // Delete PII
    await this.userService.deletePII(userId);
    
    // Update audit logs
    await this.auditLogger.logDataDeletion(userId, 'GDPR_REQUEST');
    
    return { status: 'COMPLETED', timestamp: new Date() };
  }
}
```

### ISO 27001 Controls

Key security controls implemented:

- **A.9**: Access Control Management
- **A.10**: Cryptography
- **A.12**: Operations Security
- **A.13**: Communications Security
- **A.14**: System Acquisition, Development and Maintenance
- **A.16**: Information Security Incident Management

## 🔧 Security Configuration

### Environment Security

```bash
# Production Security Environment Variables
# Authentication
JWT_PRIVATE_KEY_PATH=/etc/ssl/private/jwt-private.key
JWT_PUBLIC_KEY_PATH=/etc/ssl/certs/jwt-public.key
MFA_REQUIRED=true
SESSION_TIMEOUT=900 # 15 minutes

# Encryption
ENCRYPTION_KEY_PATH=/etc/ssl/private/data-encryption.key
DATABASE_ENCRYPTION_ENABLED=true
BACKUP_ENCRYPTION_ENABLED=true

# Security Monitoring
SECURITY_MONITORING_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=2555 # 7 years
SIEM_ENDPOINT=https://siem.company.com/api/events
THREAT_INTELLIGENCE_ENABLED=true

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_SKIP_SUCCESSFUL_REQUESTS=false

# Content Security
CONTENT_SECURITY_POLICY_ENABLED=true
HSTS_ENABLED=true
X_FRAME_OPTIONS=SAMEORIGIN
X_CONTENT_TYPE_OPTIONS=nosniff
```

### Security Headers

```javascript
// Security Headers Middleware
const securityHeaders = (req, res, next) => {
  // HSTS
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  
  // Content Security Policy
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.churnguard.ai; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "font-src 'self' https://fonts.gstatic.com; " +
    "connect-src 'self' https://api.churnguard.ai; " +
    "frame-ancestors 'none';"
  );
  
  // Additional security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  
  next();
};
```

## 📞 Security Contacts

- **Security Team**: security@churnguard.ai
- **Vulnerability Reports**: security-reports@churnguard.ai
- **Emergency Hotline**: +1-555-SEC-RITY
- **PGP Key**: Available at https://churnguard.ai/.well-known/security.txt

## 🔍 Security Assessments

Regular security assessments include:

- **Penetration Testing**: Quarterly external penetration tests
- **Code Reviews**: Automated and manual security code reviews
- **Vulnerability Scanning**: Daily automated vulnerability scans
- **Red Team Exercises**: Semi-annual red team assessments
- **Compliance Audits**: Annual SOC 2 and ISO 27001 audits

---

**Security is a shared responsibility. All team members must follow security best practices and report security concerns immediately.**