# Route53 Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# Domain Configuration
variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = null
}

variable "create_hosted_zone" {
  description = "Create Route53 hosted zone"
  type        = bool
  default     = false
}

variable "subject_alternative_names" {
  description = "Additional domain names for the SSL certificate"
  type        = list(string)
  default     = []
}

# SSL Certificate
variable "create_ssl_certificate" {
  description = "Create ACM SSL certificate"
  type        = bool
  default     = false
}

# Load Balancer Integration
variable "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  type        = string
  default     = null
}

variable "alb_zone_id" {
  description = "Hosted zone ID of the Application Load Balancer"
  type        = string
  default     = null
}

# DNS Records
variable "create_www_redirect" {
  description = "Create www subdomain pointing to main domain"
  type        = bool
  default     = true
}

variable "create_api_subdomain" {
  description = "Create api subdomain pointing to load balancer"
  type        = bool
  default     = true
}

variable "enable_ipv6" {
  description = "Enable IPv6 AAAA records"
  type        = bool
  default     = false
}

# Health Checks
variable "create_health_check" {
  description = "Create Route53 health check"
  type        = bool
  default     = false
}

variable "health_check_path" {
  description = "Path for health check"
  type        = string
  default     = "/health"
}

variable "health_check_failure_threshold" {
  description = "Number of consecutive health check failures before considering unhealthy"
  type        = number
  default     = 3
}

variable "health_check_request_interval" {
  description = "Interval between health checks (30 or 10 seconds)"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([10, 30], var.health_check_request_interval)
    error_message = "Health check request interval must be either 10 or 30 seconds."
  }
}

variable "health_check_measure_latency" {
  description = "Enable latency measurement for health checks"
  type        = bool
  default     = false
}

# CloudWatch Alarms for Health Checks
variable "health_check_alarm_datapoints" {
  description = "Number of datapoints that must be breaching to trigger alarm"
  type        = number
  default     = 2
}

variable "health_check_alarm_evaluation_periods" {
  description = "Number of periods to evaluate for the alarm"
  type        = number
  default     = 2
}

variable "health_check_alarm_actions" {
  description = "List of actions to execute when alarm transitions into an ALARM state"
  type        = list(string)
  default     = []
}

# Tags
variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}