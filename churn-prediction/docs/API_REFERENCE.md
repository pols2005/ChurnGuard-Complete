# ChurnGuard API Reference

## 🌐 Overview

The ChurnGuard API provides comprehensive access to advanced analytics, customer intelligence, A/B testing, and white-label theming features. All APIs follow REST principles with JSON request/response formats.

## 🔑 Authentication

All API requests require authentication using API keys:

```http
Authorization: Bearer YOUR_API_KEY
X-Organization-ID: your-org-id
Content-Type: application/json
```

## 📊 Analytics APIs

### Real-Time Metrics

#### Track Event
Record customer events for real-time analysis.

```http
POST /api/v1/analytics/events
```

**Request Body:**
```json
{
  "customer_id": "user123",
  "event_type": "page_view",
  "timestamp": "2024-01-15T10:30:00Z",
  "properties": {
    "page": "/dashboard",
    "duration": 45,
    "source": "organic"
  }
}
```

**Response:**
```json
{
  "event_id": "evt_12345",
  "status": "processed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Query Metrics
Retrieve aggregated metrics data.

```http
GET /api/v1/analytics/metrics/{metric_name}
```

**Query Parameters:**
- `start_time` (ISO 8601): Start of time range
- `end_time` (ISO 8601): End of time range
- `aggregation` (string): hour, day, week, month
- `filters` (object): Additional filtering criteria

**Response:**
```json
{
  "metric_name": "conversion_rate",
  "time_series": [
    {
      "timestamp": "2024-01-15T00:00:00Z",
      "value": 0.045,
      "count": 1250
    }
  ],
  "summary": {
    "average": 0.043,
    "total": 0.045,
    "trend": "increasing"
  }
}
```

### Customer Intelligence

#### Customer Journey Analysis
Analyze individual customer journeys.

```http
GET /api/v1/intelligence/journey/{customer_id}
```

**Response:**
```json
{
  "customer_id": "user123",
  "journey_score": 85.2,
  "current_stage": "active_use",
  "churn_risk": 0.15,
  "predicted_ltv": 2450.00,
  "touchpoints": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "type": "website_visit",
      "channel": "organic",
      "value": 1
    }
  ],
  "key_moments": [
    {
      "moment_type": "first_contact",
      "timestamp": "2024-01-01T14:22:00Z",
      "significance": "Journey beginning",
      "impact_score": 0.9
    }
  ]
}
```

#### Behavioral Analysis
Get comprehensive behavioral profile for a customer.

```http
GET /api/v1/intelligence/behavior/{customer_id}
```

**Response:**
```json
{
  "customer_id": "user123",
  "behavior_segment": "power_user",
  "engagement_score": 78.5,
  "usage_intensity": 0.85,
  "feature_adoption_rate": 0.67,
  "risk_indicators": {
    "churn_risk": 0.12,
    "engagement_decline": 0.05
  },
  "predicted_actions": [
    {
      "action": "feature_expansion",
      "probability": 0.78,
      "timeframe_days": 14
    }
  ],
  "recommendations": [
    {
      "type": "engagement",
      "title": "Introduce advanced features",
      "priority": "high",
      "confidence": 0.82
    }
  ]
}
```

#### Customer LTV Prediction
Predict customer lifetime value using ensemble models.

```http
GET /api/v1/intelligence/ltv/{customer_id}
```

**Query Parameters:**
- `model_type` (string): ensemble, behavioral_predictive, cohort_based
- `time_horizon_months` (integer): 12, 24, 36

**Response:**
```json
{
  "customer_id": "user123",
  "predicted_ltv": 2450.00,
  "confidence_interval": [1800.00, 3100.00],
  "confidence_score": 0.78,
  "ltv_segment": "high_value",
  "value_components": {
    "subscription_revenue": 1960.00,
    "upsell_revenue": 340.00,
    "referral_value": 150.00
  },
  "contributing_factors": [
    {
      "factor": "high_engagement",
      "impact": 0.23,
      "description": "Above-average product usage"
    }
  ]
}
```

## 🧪 A/B Testing APIs

### Experiment Management

#### Create Experiment
Create a new A/B test experiment.

```http
POST /api/v1/experiments
```

**Request Body:**
```json
{
  "name": "Landing Page CTA Test",
  "description": "Test different call-to-action buttons",
  "experiment_type": "ab_test",
  "variants": [
    {
      "name": "Control",
      "description": "Current blue button",
      "traffic_allocation": 0.5,
      "configuration": {
        "button_color": "blue",
        "button_text": "Get Started"
      },
      "is_control": true
    },
    {
      "name": "Treatment",
      "description": "New green button",
      "traffic_allocation": 0.5,
      "configuration": {
        "button_color": "green",
        "button_text": "Start Free Trial"
      }
    }
  ],
  "metrics": [
    {
      "name": "conversion_rate",
      "type": "binary",
      "is_primary": true,
      "minimum_detectable_effect": 0.05
    }
  ]
}
```

**Response:**
```json
{
  "experiment_id": "exp_abc123",
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z",
  "sample_size_per_variant": 2500,
  "estimated_runtime_days": 14
}
```

#### Start Experiment
Begin running an experiment.

```http
POST /api/v1/experiments/{experiment_id}/start
```

**Response:**
```json
{
  "experiment_id": "exp_abc123",
  "status": "running",
  "start_date": "2024-01-15T10:30:00Z",
  "estimated_end_date": "2024-01-29T10:30:00Z"
}
```

#### Statistical Analysis
Get comprehensive statistical analysis of experiment results.

```http
GET /api/v1/experiments/{experiment_id}/analysis
```

**Response:**
```json
{
  "experiment_id": "exp_abc123",
  "analysis_date": "2024-01-20T10:30:00Z",
  "runtime_days": 5,
  "total_participants": 1250,
  "primary_metric_results": [
    {
      "metric_name": "conversion_rate",
      "control_mean": 0.042,
      "treatment_mean": 0.051,
      "relative_improvement": 0.214,
      "p_value": 0.003,
      "is_significant": true,
      "confidence_interval": [0.002, 0.016],
      "statistical_power": 0.85
    }
  ],
  "overall_conclusion": "significant",
  "recommended_action": "deploy_treatment",
  "confidence_score": 0.89
}
```

## 🎨 Theming APIs

### CSS Customization

#### Create Theme
Create a new CSS theme for organization.

```http
POST /api/v1/theming/themes
```

**Request Body:**
```json
{
  "theme_name": "Corporate Blue Theme",
  "description": "Professional theme with corporate branding"
}
```

**Response:**
```json
{
  "theme_id": "theme_xyz789",
  "theme_name": "Corporate Blue Theme",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Update CSS Scope
Update CSS for specific application scope.

```http
PUT /api/v1/theming/themes/{theme_id}/css/{scope}
```

**Request Body:**
```json
{
  "css_content": ".header { background-color: #007bff; color: white; }",
  "validation_level": "moderate"
}
```

**Response:**
```json
{
  "is_valid": true,
  "sanitized_css": ".header { background-color: #007bff; color: white; }",
  "warnings": [],
  "blocked_properties": []
}
```

### Color Scheme Management

#### Generate Color Palette
Create organization-specific color scheme.

```http
POST /api/v1/theming/colors/palette
```

**Request Body:**
```json
{
  "palette_name": "Acme Corp Brand Colors",
  "primary_color": "#007bff",
  "secondary_color": "#6c757d",
  "theme_type": "light"
}
```

**Response:**
```json
{
  "palette_id": "pal_def456",
  "primary": "#007bff",
  "secondary": "#6c757d",
  "accent": "#fd7e14",
  "color_variants": {
    "primary_100": "#cce7ff",
    "primary_500": "#007bff",
    "primary_900": "#003d7a"
  },
  "accessibility": {
    "wcag_aa_compliant": true,
    "contrast_ratios": {
      "text_on_primary": 4.8
    }
  }
}
```

### Custom Domain Management

#### Add Custom Domain
Configure custom domain for white-label deployment.

```http
POST /api/v1/theming/domains
```

**Request Body:**
```json
{
  "domain_name": "app.acme.com",
  "domain_type": "custom_domain",
  "ssl_enabled": true,
  "brand_name": "Acme Analytics"
}
```

**Response:**
```json
{
  "domain_id": "dom_ghi789",
  "domain_name": "app.acme.com",
  "status": "pending_verification",
  "verification_token": "churnguard-domain-verification=abc123...",
  "required_dns_records": [
    {
      "type": "CNAME",
      "name": "app.acme.com",
      "value": "custom.churnguard.ai",
      "ttl": "300"
    },
    {
      "type": "TXT",
      "name": "_churnguard-challenge.app.acme.com",
      "value": "churnguard-domain-verification=abc123...",
      "ttl": "300"
    }
  ]
}
```

## 📚 SDKs & Libraries

### Python SDK
```bash
pip install churnguard-python
```

```python
import churnguard

client = churnguard.Client(api_key="your-key", organization_id="your-org")

# Track events
client.track_event("user123", "page_view", {"page": "/dashboard"})

# Analyze customer
profile = client.analyze_customer_behavior("user123")

# Create A/B test
experiment = client.create_experiment("Button Color Test", ["blue", "green"])
```

### JavaScript SDK
```bash
npm install @churnguard/sdk
```

```javascript
import ChurnGuard from '@churnguard/sdk';

const client = new ChurnGuard({
  apiKey: 'your-key',
  organizationId: 'your-org'
});

// Track events
await client.trackEvent('user123', 'page_view', {
  page: '/dashboard'
});

// Get customer insights
const insights = await client.getCustomerInsights('user123');
```

## 🚨 Error Handling

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request body contains invalid parameters",
    "details": {
      "field": "customer_id",
      "reason": "Customer ID is required"
    },
    "request_id": "req_789abc"
  }
}
```

### Common Error Codes

- `INVALID_REQUEST` (400): Malformed request
- `UNAUTHORIZED` (401): Invalid or missing API key
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `RATE_LIMITED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error

## 🔒 Rate Limits

API rate limits are enforced per organization:

- **Standard**: 1,000 requests/minute
- **Professional**: 5,000 requests/minute  
- **Enterprise**: 25,000 requests/minute

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## 📞 Support

- **API Documentation**: https://docs.churnguard.ai
- **Status Page**: https://status.churnguard.ai
- **Support**: support@churnguard.ai