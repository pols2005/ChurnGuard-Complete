# ChurnGuard Analytics API Reference

## Overview

The ChurnGuard Analytics API provides comprehensive access to advanced analytics, AI-powered insights, recommendations, and anomaly detection capabilities. This document provides detailed API specifications for all analytics endpoints.

## Base URL

```
https://api.churnguard.com/v1/analytics
```

## Authentication

All API requests require authentication using JWT tokens in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

## Rate Limits

- Standard tier: 1,000 requests/hour
- Professional tier: 10,000 requests/hour  
- Enterprise tier: 100,000 requests/hour

## Content Types

All requests and responses use JSON format:

```http
Content-Type: application/json
Accept: application/json
```

---

## Metrics API

### Write Metrics

#### POST /metrics/write

Write metric data points to the time-series database.

**Request Body:**
```json
{
  "points": [
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "metric_name": "churn_predictions",
      "value": 0.157,
      "organization_id": "org-123",
      "tags": {
        "model_version": "v2.1",
        "segment": "enterprise",
        "region": "us-east"
      },
      "metadata": {
        "confidence": 0.89,
        "model_type": "ensemble"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "points_written": 1,
  "processing_time_ms": 45
}
```

**cURL Example:**
```bash
curl -X POST "https://api.churnguard.com/v1/analytics/metrics/write" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "points": [{
      "timestamp": "2025-01-15T10:30:00Z",
      "metric_name": "churn_predictions",
      "value": 0.157,
      "organization_id": "org-123",
      "tags": {"model_version": "v2.1"}
    }]
  }'
```

### Query Metrics

#### GET /metrics/query

Query metric data with flexible filtering and aggregation.

**Query Parameters:**
- `metric_name` (required): Name of the metric to query
- `organization_id` (required): Organization identifier
- `start_time` (optional): ISO 8601 start time (default: 24 hours ago)
- `end_time` (optional): ISO 8601 end time (default: now)
- `tags` (optional): JSON-encoded tag filters
- `aggregation` (optional): Aggregation function (mean, sum, count, min, max)
- `interval` (optional): Aggregation interval (1m, 5m, 1h, 1d)
- `limit` (optional): Maximum number of data points (default: 1000)

**Example Request:**
```http
GET /metrics/query?metric_name=churn_predictions&organization_id=org-123&start_time=2025-01-15T00:00:00Z&aggregation=mean&interval=1h&limit=24
```

**Response:**
```json
{
  "data": [
    {
      "timestamp": "2025-01-15T10:00:00Z",
      "value": 0.145,
      "metric_name": "churn_predictions",
      "organization_id": "org-123"
    },
    {
      "timestamp": "2025-01-15T11:00:00Z", 
      "value": 0.157,
      "metric_name": "churn_predictions",
      "organization_id": "org-123"
    }
  ],
  "total_points": 24,
  "query_time_ms": 89
}
```

#### GET /metrics/{metric_name}/latest

Get the latest value for a specific metric.

**Path Parameters:**
- `metric_name`: Name of the metric

**Query Parameters:**
- `organization_id` (required): Organization identifier
- `tags` (optional): JSON-encoded tag filters

**Response:**
```json
{
  "metric_name": "churn_predictions",
  "organization_id": "org-123",
  "latest_value": 0.157,
  "timestamp": "2025-01-15T10:30:00Z",
  "tags": {
    "model_version": "v2.1",
    "segment": "enterprise"
  }
}
```

#### GET /metrics/{metric_name}/stats

Get statistical summary for a metric over a time window.

**Path Parameters:**
- `metric_name`: Name of the metric

**Query Parameters:**
- `organization_id` (required): Organization identifier
- `window_hours` (optional): Time window in hours (default: 1)
- `tags` (optional): JSON-encoded tag filters

**Response:**
```json
{
  "metric_name": "churn_predictions",
  "organization_id": "org-123", 
  "window_hours": 24,
  "statistics": {
    "count": 144,
    "mean": 0.152,
    "std": 0.023,
    "min": 0.089,
    "max": 0.234,
    "sum": 21.89,
    "rate_per_hour": 6.0,
    "p50": 0.149,
    "p95": 0.189,
    "p99": 0.212
  },
  "computed_at": "2025-01-15T10:30:00Z"
}
```

---

## Real-Time Analytics API

### Real-Time Statistics

#### GET /realtime/stats/{metric_name}

Get real-time statistics for a metric using sliding window calculations.

**Path Parameters:**
- `metric_name`: Name of the metric

**Query Parameters:**
- `organization_id` (required): Organization identifier
- `window_minutes` (optional): Sliding window size in minutes (default: 5)
- `tags` (optional): JSON-encoded tag filters

**Response:**
```json
{
  "metric_name": "customer_activity",
  "organization_id": "org-123",
  "window_minutes": 5,
  "statistics": {
    "count": 47,
    "avg": 142.5,
    "sum": 6697.5,
    "min": 89.2,
    "max": 234.7,
    "rate_per_minute": 9.4,
    "last_value": 156.3,
    "std_dev": 23.4,
    "p50": 138.9,
    "p95": 187.2,
    "p99": 210.5
  },
  "last_updated": "2025-01-15T10:30:00Z"
}
```

### Real-Time Anomalies

#### GET /realtime/anomalies/{metric_name}

Detect real-time anomalies in metric data.

**Path Parameters:**
- `metric_name`: Name of the metric

**Query Parameters:**
- `organization_id` (required): Organization identifier
- `sensitivity` (optional): Detection sensitivity (0.5-5.0, default: 2.0)
- `window_hours` (optional): Analysis window in hours (default: 24)

**Response:**
```json
{
  "metric_name": "churn_predictions",
  "organization_id": "org-123",
  "anomalies": [
    {
      "timestamp": "2025-01-15T09:45:00Z",
      "value": 0.287,
      "expected_value": 0.152,
      "z_score": 3.2,
      "severity": "high",
      "type": "statistical_outlier"
    }
  ],
  "detection_summary": {
    "total_points_analyzed": 144,
    "anomaly_count": 1,
    "anomaly_rate": 0.007,
    "detection_method": "rolling_zscore"
  }
}
```

### Configure Alerts

#### POST /realtime/alerts

Configure real-time alerting for metrics.

**Request Body:**
```json
{
  "metric_name": "churn_risk_score",
  "organization_id": "org-123",
  "threshold_type": "above",
  "threshold_value": 0.8,
  "severity": "high",
  "window_minutes": 5,
  "notification_channels": ["email", "slack"],
  "enabled": true
}
```

**Response:**
```json
{
  "alert_id": "alert-123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## Insights API

### Generate Insights

#### GET /insights/{organization_id}

Generate AI-powered insights for an organization's metrics.

**Path Parameters:**
- `organization_id`: Organization identifier

**Query Parameters:**
- `metrics` (optional): Comma-separated list of specific metrics to analyze
- `time_window_hours` (optional): Analysis time window in hours (default: 24)
- `min_confidence` (optional): Minimum confidence threshold (0.0-1.0, default: 0.6)
- `max_insights` (optional): Maximum number of insights to return (default: 50)

**Response:**
```json
{
  "organization_id": "org-123",
  "generated_at": "2025-01-15T10:30:00Z",
  "time_window_hours": 24,
  "insights": [
    {
      "id": "insight-123e4567-e89b-12d3-a456-426614174000",
      "type": "trend",
      "severity": "high",
      "title": "Churn Risk Score Shows Increasing Trend",
      "description": "Statistically significant increasing trend detected",
      "narrative": "The churn risk score has been showing a consistent upward trend with a slope of 0.0023 per hour. This increasing pattern has an R-squared value of 0.847, indicating strong predictability.",
      "confidence_score": 0.87,
      "metric_name": "churn_risk_score",
      "data_points": {
        "slope": 0.0023,
        "r_squared": 0.847,
        "p_value": 0.002,
        "trend_strength": 0.91,
        "direction": "increasing"
      },
      "recommendations": [
        "Implement immediate customer retention programs",
        "Analyze recent changes that might be driving increased churn risk",
        "Monitor related metrics for cascading effects"
      ],
      "related_metrics": ["customer_activity", "revenue_at_risk"],
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ],
  "total_insights": 12,
  "confidence_distribution": {
    "high": 4,
    "medium": 6, 
    "low": 2
  }
}
```

#### GET /insights/{insight_id}

Get detailed information about a specific insight.

**Path Parameters:**
- `insight_id`: Unique insight identifier

**Response:**
```json
{
  "id": "insight-123e4567-e89b-12d3-a456-426614174000",
  "type": "anomaly",
  "severity": "critical", 
  "title": "Unusual Activity Detected in Customer Activity",
  "description": "3 anomalies detected using ensemble analysis",
  "narrative": "Detected 3 anomalous data points in Customer Activity using ensemble analysis. The most recent anomaly occurred at 2025-01-15 09:45 with a value of 287.45. These outliers represent 2.1% of all data points and may indicate underlying issues requiring investigation.",
  "confidence_score": 0.94,
  "metric_name": "customer_activity",
  "data_points": {
    "method": "ensemble",
    "anomaly_count": 3,
    "anomaly_rate": 0.021,
    "threshold": 2.0,
    "avg_anomaly_score": 3.2,
    "anomalies": [
      {
        "index": 142,
        "value": 287.45,
        "expected": 142.3,
        "z_score": 3.2,
        "type": "point_anomaly"
      }
    ]
  },
  "recommendations": [
    "Investigate the root causes of these anomalous data points",
    "Check for external factors that might have influenced these outliers",
    "Verify data quality and collection processes during anomaly periods"
  ],
  "related_metrics": ["churn_predictions"],
  "timestamp": "2025-01-15T10:30:00Z",
  "metadata": {
    "detection_method": "ensemble",
    "composite_score": 3.76
  }
}
```

### Summary Report

#### GET /insights/{organization_id}/summary

Generate a comprehensive insights summary report.

**Path Parameters:**
- `organization_id`: Organization identifier

**Query Parameters:**
- `time_period` (optional): Analysis period (24h, 7d, 30d, default: 24h)

**Response:**
```json
{
  "generated_at": "2025-01-15T10:30:00Z",
  "time_period": "24h",
  "organization_id": "org-123",
  "executive_summary": "URGENT: 2 critical issue(s) detected requiring immediate attention. 5 high-priority insight(s) identified for review. Key trends: 8 significant patterns detected in customer metrics.",
  "key_metrics": {
    "churn_predictions": {
      "current_value": 0.157,
      "trend": "increasing",
      "change_percent": 12.5,
      "status": "concerning"
    },
    "customer_activity": {
      "current_value": 142.5,
      "trend": "stable",
      "change_percent": -2.1,
      "status": "normal"
    },
    "revenue_at_risk": {
      "current_value": 45780.25,
      "trend": "increasing", 
      "change_percent": 18.7,
      "status": "high_risk"
    }
  },
  "insights_by_category": {
    "critical_alerts": [
      {
        "id": "insight-critical-001",
        "title": "Revenue at Risk Exceeds Critical Threshold",
        "severity": "critical"
      }
    ],
    "high_priority": [
      {
        "id": "insight-high-001", 
        "title": "Churn Risk Score Shows Increasing Trend",
        "severity": "high"
      }
    ],
    "trends": [
      {
        "id": "insight-trend-001",
        "title": "Customer Activity Seasonality Pattern",
        "type": "seasonal"
      }
    ],
    "anomalies": [
      {
        "id": "insight-anomaly-001",
        "title": "Unusual Spike in Customer Activity",
        "type": "anomaly"
      }
    ]
  },
  "total_insights": 15,
  "confidence_distribution": {
    "high": 8,
    "medium": 5,
    "low": 2
  }
}
```

---

## Recommendations API

### Generate Recommendations

#### GET /recommendations/{organization_id}

Generate AI-powered business recommendations.

**Path Parameters:**
- `organization_id`: Organization identifier

**Query Parameters:**
- `time_window_hours` (optional): Analysis time window (default: 24)
- `max_recommendations` (optional): Maximum recommendations to return (default: 20)
- `min_confidence` (optional): Minimum confidence threshold (default: 0.5)
- `category` (optional): Filter by category (customer_retention, revenue_optimization, etc.)

**Response:**
```json
{
  "organization_id": "org-123",
  "generated_at": "2025-01-15T10:30:00Z",
  "recommendations": [
    {
      "id": "rec-123e4567-e89b-12d3-a456-426614174000",
      "type": "immediate_action",
      "priority": "urgent",
      "category": "customer_retention",
      "title": "Implement Immediate Churn Intervention Program",
      "description": "Deploy targeted retention campaigns for at-risk customers",
      "detailed_explanation": "The increasing trend in churn_predictions (slope: 0.0023) indicates escalating churn risk. Immediate intervention is required to prevent customer loss.",
      "rationale": "Statistical analysis shows 91.0% confidence in the upward trend. Early intervention can reduce churn by 15-25%.",
      "expected_impact": "Potential 20-30% reduction in customer churn within 30 days",
      "implementation_steps": [
        "Identify customers with highest churn risk scores",
        "Deploy personalized retention offers and communications", 
        "Assign dedicated account managers to high-value at-risk customers",
        "Implement proactive customer success outreach",
        "Monitor daily churn metrics and adjust strategies"
      ],
      "estimated_effort": "medium",
      "time_to_implement": "days",
      "success_metrics": [
        "Daily churn rate reduction",
        "Customer retention rate improvement",
        "Revenue at risk decrease",
        "Customer satisfaction scores"
      ],
      "confidence_score": 0.91,
      "triggered_by_insights": ["insight-123e4567-e89b-12d3-a456-426614174000"],
      "related_metrics": ["churn_predictions", "customer_retention_rate", "revenue_at_risk"],
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ],
  "total_recommendations": 8,
  "priority_distribution": {
    "urgent": 2,
    "high": 3,
    "medium": 2,
    "low": 1
  }
}
```

#### GET /recommendations/{recommendation_id}

Get detailed information about a specific recommendation.

**Path Parameters:**
- `recommendation_id`: Unique recommendation identifier

**Response:**
```json
{
  "id": "rec-123e4567-e89b-12d3-a456-426614174000",
  "type": "process_improvement",
  "priority": "high",
  "category": "predictive_analytics",
  "title": "Improve Machine Learning Model Performance",
  "description": "Enhance model accuracy through optimization and retraining",
  "detailed_explanation": "Current model accuracy of 78.5% is below optimal performance. Implementing model improvements can significantly enhance prediction quality.",
  "rationale": "Higher model accuracy directly translates to better business decisions and outcomes.",
  "expected_impact": "10-15% improvement in model accuracy and prediction reliability",
  "implementation_steps": [
    "Conduct comprehensive model performance analysis",
    "Gather additional training data if needed",
    "Experiment with different algorithms and hyperparameters",
    "Implement feature engineering improvements",
    "Set up automated model retraining pipeline",
    "Establish model performance monitoring"
  ],
  "estimated_effort": "high",
  "time_to_implement": "weeks",
  "success_metrics": [
    "Model accuracy improvement",
    "Prediction precision and recall",
    "Business outcome correlation",
    "Model confidence scores"
  ],
  "confidence_score": 0.89,
  "triggered_by_insights": [],
  "related_metrics": ["model_accuracy", "prediction_confidence"],
  "timestamp": "2025-01-15T10:30:00Z",
  "metadata": {
    "current_accuracy": 0.785,
    "composite_score": 2.67
  }
}
```

### Create Action Plan

#### POST /recommendations/{organization_id}/action-plan

Create an implementation action plan for selected recommendations.

**Path Parameters:**
- `organization_id`: Organization identifier

**Request Body:**
```json
{
  "recommendation_ids": [
    "rec-123e4567-e89b-12d3-a456-426614174000",
    "rec-456e7890-e89b-12d3-a456-426614174001"
  ]
}
```

**Response:**
```json
{
  "action_plan_id": "plan_org-123_1705399800",
  "organization_id": "org-123",
  "created_at": "2025-01-15T10:30:00Z",
  "selected_recommendations": 2,
  "implementation_timeline": {
    "immediate": [
      {
        "id": "rec-123e4567-e89b-12d3-a456-426614174000",
        "title": "Implement Immediate Churn Intervention Program",
        "estimated_duration": "1-7 days"
      }
    ],
    "short_term": [
      {
        "id": "rec-456e7890-e89b-12d3-a456-426614174001", 
        "title": "Optimize Analytics and Prediction Workflows",
        "estimated_duration": "1-4 weeks"
      }
    ],
    "medium_term": [],
    "long_term": []
  },
  "resource_requirements": {
    "total_recommendations": 2,
    "effort_distribution": {
      "low": 0,
      "medium": 1,
      "high": 1
    },
    "estimated_team_weeks": 8.5,
    "recommended_team_size": 3
  },
  "expected_roi": {
    "estimated_total_value": 112500,
    "estimated_investment": 10000,
    "roi_ratio": 11.25,
    "payback_period_months": 1.07
  },
  "success_metrics": [
    "Daily churn rate reduction",
    "Customer retention rate improvement", 
    "Revenue at risk decrease",
    "Analytics processing time reduction",
    "Model accuracy improvement"
  ],
  "total_estimated_effort": {
    "low": 0,
    "medium": 1,
    "high": 1
  },
  "implementation_phases": [
    {
      "phase": 1,
      "name": "Immediate Actions", 
      "duration": "1-2 weeks",
      "recommendations": [
        {
          "id": "rec-123e4567-e89b-12d3-a456-426614174000",
          "title": "Implement Immediate Churn Intervention Program"
        }
      ],
      "key_outcomes": [
        "Stabilize critical issues",
        "Prevent immediate risks"
      ]
    },
    {
      "phase": 2,
      "name": "Process Improvements",
      "duration": "4-8 weeks", 
      "recommendations": [
        {
          "id": "rec-456e7890-e89b-12d3-a456-426614174001",
          "title": "Optimize Analytics and Prediction Workflows"
        }
      ],
      "key_outcomes": [
        "Improve operational efficiency",
        "Standardize processes"
      ]
    }
  ],
  "risk_assessment": {
    "low_risk_count": 0,
    "medium_risk_count": 1,
    "high_risk_count": 1,
    "risk_factors": [
      "High implementation effort for Optimize Analytics and Prediction Workflows"
    ]
  }
}
```

---

## Anomaly Detection API

### Detect Anomalies

#### GET /anomalies/{organization_id}

Get detected anomalies for an organization.

**Path Parameters:**
- `organization_id`: Organization identifier

**Query Parameters:**
- `metric_name` (optional): Specific metric to analyze
- `time_window_hours` (optional): Analysis window (default: 24)
- `method` (optional): Detection method (statistical, isolation_forest, ensemble)
- `min_severity` (optional): Minimum severity (low, medium, high, critical)

**Response:**
```json
{
  "organization_id": "org-123",
  "generated_at": "2025-01-15T10:30:00Z", 
  "time_window_hours": 24,
  "anomalies": [
    {
      "id": "anomaly_org-123_customer_activity_1705399800",
      "timestamp": "2025-01-15T09:45:00Z",
      "metric_name": "customer_activity",
      "value": 287.45,
      "expected_value": 142.3,
      "deviation_score": 3.2,
      "anomaly_type": "point_anomaly",
      "severity": "high",
      "method": "ensemble",
      "confidence": 0.64,
      "explanation": "The customer activity value of 287.45 is 102.0% higher than expected (142.30). This anomaly was detected using ensemble with a deviation score of 3.20.",
      "recommendations": [
        "Investigate the root cause of this anomaly in customer activity",
        "Check for any system changes or external events during this time period",
        "Verify data quality and collection processes"
      ],
      "context": {
        "detection_method": "ensemble",
        "detector_metadata": {
          "ensemble_detectors": ["Statistical Detector", "Isolation Forest Detector"],
          "detector_count": 2
        }
      },
      "resolved": false
    }
  ],
  "total_anomalies": 5,
  "severity_distribution": {
    "critical": 0,
    "high": 2,
    "medium": 2,
    "low": 1
  }
}
```

#### POST /anomalies/{organization_id}/detect

Run anomaly detection for specific metrics and time windows.

**Path Parameters:**
- `organization_id`: Organization identifier

**Request Body:**
```json
{
  "metric_name": "churn_risk_score",
  "time_window_hours": 48,
  "method": "ensemble",
  "parameters": {
    "sensitivity": 2.0,
    "voting_threshold": 2
  }
}
```

**Response:**
```json
{
  "detection_id": "detect-123e4567-e89b-12d3-a456-426614174000",
  "metric_name": "churn_risk_score",
  "organization_id": "org-123",
  "method": "ensemble",
  "time_window_hours": 48,
  "detected_at": "2025-01-15T10:30:00Z",
  "anomalies": [
    {
      "timestamp": "2025-01-14T15:23:00Z",
      "value": 0.289,
      "expected_value": 0.152,
      "deviation_score": 2.8,
      "severity": "medium",
      "confidence": 0.72
    }
  ],
  "summary": {
    "total_anomalies": 1,
    "data_points_analyzed": 288,
    "anomaly_rate": 0.0035,
    "processing_time_ms": 1247
  }
}
```

### Anomaly Summary

#### GET /anomalies/{organization_id}/summary

Get summary statistics of anomalies for an organization.

**Path Parameters:**
- `organization_id`: Organization identifier

**Query Parameters:**
- `hours_back` (optional): Time window in hours (default: 24)

**Response:**
```json
{
  "organization_id": "org-123",
  "time_window_hours": 24,
  "summary": {
    "total_anomalies": 8,
    "unresolved_anomalies": 6,
    "detection_rate": 0.33,
    "severity_distribution": {
      "critical": 1,
      "high": 2,
      "medium": 3,
      "low": 2
    },
    "metric_distribution": {
      "customer_activity": 3,
      "churn_predictions": 2,
      "revenue_at_risk": 2,
      "model_accuracy": 1
    },
    "type_distribution": {
      "point_anomaly": 5,
      "contextual_anomaly": 2, 
      "trend_anomaly": 1
    },
    "most_anomalous_metrics": [
      ["customer_activity", 3],
      ["churn_predictions", 2],
      ["revenue_at_risk", 2]
    ]
  },
  "computed_at": "2025-01-15T10:30:00Z"
}
```

### Configure Detection Rules

#### POST /anomalies/rules

Add anomaly detection rule for automated monitoring.

**Request Body:**
```json
{
  "metric_name": "churn_predictions",
  "organization_id": "org-123",
  "method": "ensemble",
  "parameters": {
    "sensitivity": 2.0,
    "voting_threshold": 2,
    "min_data_points": 20
  },
  "enabled": true,
  "window_hours": 24,
  "notification_channels": ["email", "slack"]
}
```

**Response:**
```json
{
  "rule_id": "rule_org-123_churn_predictions_1705399800",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### PATCH /anomalies/{anomaly_id}/resolve

Mark an anomaly as resolved.

**Path Parameters:**
- `anomaly_id`: Unique anomaly identifier

**Request Body:**
```json
{
  "resolution_notes": "False positive - caused by scheduled maintenance window",
  "resolved_by": "admin@company.com"
}
```

**Response:**
```json
{
  "anomaly_id": "anomaly_org-123_customer_activity_1705399800",
  "resolved": true,
  "resolved_at": "2025-01-15T10:30:00Z",
  "resolved_by": "admin@company.com"
}
```

---

## Statistical Analysis API

### Descriptive Statistics

#### POST /statistics/descriptive

Calculate comprehensive descriptive statistics for data.

**Request Body:**
```json
{
  "data": [1.2, 1.5, 1.1, 1.8, 1.3, 1.6, 1.4, 1.7, 1.9, 1.2],
  "organization_id": "org-123"
}
```

**Response:**
```json
{
  "statistics": {
    "count": 10,
    "mean": 1.47,
    "std": 0.256,
    "min": 1.1,
    "max": 1.9,
    "median": 1.45,
    "q25": 1.25,
    "q75": 1.675,
    "skewness": 0.123,
    "kurtosis": -0.456
  },
  "computed_at": "2025-01-15T10:30:00Z"
}
```

### Trend Analysis

#### POST /statistics/trend-analysis

Analyze trends in time-series data.

**Request Body:**
```json
{
  "timestamps": ["2025-01-15T06:00:00Z", "2025-01-15T07:00:00Z", "2025-01-15T08:00:00Z"],
  "values": [0.12, 0.15, 0.18],
  "confidence_level": 0.95,
  "organization_id": "org-123"
}
```

**Response:**
```json
{
  "trend_analysis": {
    "direction": "increasing",
    "slope": 0.03,
    "r_squared": 0.95,
    "p_value": 0.001,
    "confidence_interval": [0.025, 0.035],
    "trend_strength": 0.97
  },
  "interpretation": "Strong increasing trend with high statistical significance",
  "computed_at": "2025-01-15T10:30:00Z"
}
```

### A/B Test Analysis

#### POST /statistics/ab-test

Perform statistical analysis of A/B test results.

**Request Body:**
```json
{
  "control_group": [0.12, 0.11, 0.13, 0.14, 0.12, 0.15, 0.11],
  "treatment_group": [0.18, 0.19, 0.17, 0.20, 0.18, 0.21, 0.19],
  "confidence_level": 0.95,
  "organization_id": "org-123"
}
```

**Response:**
```json
{
  "ab_test_results": {
    "control_stats": {
      "count": 7,
      "mean": 0.126,
      "std": 0.015
    },
    "treatment_stats": {
      "count": 7,
      "mean": 0.189,
      "std": 0.014
    },
    "mean_difference": 0.063,
    "relative_lift_percent": 50.0,
    "t_statistic": 8.45,
    "p_value": 0.0001,
    "is_significant": true,
    "cohens_d": 4.2,
    "confidence_interval": [0.045, 0.081],
    "confidence_level": 0.95,
    "sample_sizes": {
      "control": 7,
      "treatment": 7
    }
  },
  "interpretation": "Treatment group shows statistically significant improvement",
  "computed_at": "2025-01-15T10:30:00Z"
}
```

---

## System Health API

### Health Check

#### GET /health

Get comprehensive system health status.

**Response:**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "overall_status": "healthy",
  "components": {
    "timeseries_db": "healthy",
    "realtime_engine": "healthy",
    "anomaly_detection": "healthy",
    "insight_generator": "healthy",
    "recommendation_engine": "healthy"
  },
  "performance_metrics": {
    "avg_response_time_ms": 45,
    "requests_per_minute": 127,
    "error_rate": 0.001,
    "uptime_seconds": 2592000
  },
  "database_stats": {
    "total_metrics": 156,
    "total_data_points": 2847392,
    "disk_usage_gb": 15.7,
    "query_performance_ms": 23
  },
  "cache_stats": {
    "hit_rate": 0.87,
    "memory_usage_mb": 512,
    "eviction_rate": 0.02
  }
}
```

### Performance Metrics

#### GET /health/performance

Get detailed performance metrics for the analytics system.

**Response:**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "real_time_engine": {
    "total_metrics": 24,
    "total_data_points": 156789,
    "ingestion_count": 45234,
    "avg_processing_time_ms": 2.3,
    "active_alerts": 3,
    "memory_usage_mb": 234,
    "engine_uptime": 86400
  },
  "aggregation_pipeline": {
    "processed_metrics": 12456,
    "error_count": 2,
    "active_rules": 18,
    "pending_jobs": 5,
    "running_jobs": 2,
    "avg_processing_time_ms": 156,
    "cache_entries": 89
  },
  "anomaly_detection": {
    "detection_count": 234,
    "false_positive_rate": 0.05,
    "avg_detection_time_ms": 423,
    "active_rules": 12,
    "memory_usage_mb": 167
  }
}
```

---

## Error Codes

The API uses standard HTTP status codes and provides detailed error information:

### Success Codes
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for processing

### Client Error Codes
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded

### Server Error Codes
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - Database connection error
- `503 Service Unavailable` - Service temporarily unavailable
- `504 Gateway Timeout` - Request timeout

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid metric_name parameter",
    "details": {
      "field": "metric_name",
      "constraint": "must_not_be_empty"
    },
    "request_id": "req-123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### Common Error Codes

- `INVALID_PARAMETERS` - Request parameters are invalid
- `AUTHENTICATION_REQUIRED` - Valid authentication token required
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `RESOURCE_NOT_FOUND` - Requested resource does not exist
- `RATE_LIMIT_EXCEEDED` - API rate limit exceeded
- `VALIDATION_ERROR` - Request validation failed
- `DATABASE_ERROR` - Database operation failed
- `PROCESSING_ERROR` - Internal processing error
- `SERVICE_UNAVAILABLE` - Service temporarily unavailable

---

## SDKs and Libraries

### Python SDK

```python
from churnguard_analytics import AnalyticsClient

client = AnalyticsClient(
    base_url="https://api.churnguard.com/v1/analytics",
    token="your-jwt-token"
)

# Generate insights
insights = client.insights.generate("org-123", time_window_hours=24)

# Get recommendations  
recommendations = client.recommendations.generate("org-123")

# Create action plan
action_plan = client.recommendations.create_action_plan(
    "org-123", 
    [rec.id for rec in recommendations[:3]]
)
```

### JavaScript/Node.js SDK

```javascript
const { AnalyticsClient } = require('@churnguard/analytics-sdk');

const client = new AnalyticsClient({
  baseUrl: 'https://api.churnguard.com/v1/analytics',
  token: 'your-jwt-token'
});

// Generate insights
const insights = await client.insights.generate('org-123', { 
  timeWindowHours: 24 
});

// Get recommendations
const recommendations = await client.recommendations.generate('org-123');

// Create action plan
const actionPlan = await client.recommendations.createActionPlan('org-123', 
  recommendations.slice(0, 3).map(r => r.id)
);
```

### cURL Examples

```bash
# Generate insights
curl -X GET "https://api.churnguard.com/v1/analytics/insights/org-123?time_window_hours=24" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get recommendations
curl -X GET "https://api.churnguard.com/v1/analytics/recommendations/org-123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create action plan
curl -X POST "https://api.churnguard.com/v1/analytics/recommendations/org-123/action-plan" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recommendation_ids": ["rec-123", "rec-456"]}'
```

This completes the comprehensive API reference for the ChurnGuard Analytics platform. The documentation covers all endpoints, request/response formats, error handling, and integration examples.