# General Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "churnguard"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with a letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN gateway"
  type        = bool
  default     = false
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in VPC"
  type        = bool
  default     = true
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

# Security Groups Configuration
variable "create_bastion_host" {
  description = "Create bastion host security group"
  type        = bool
  default     = false
}

# S3 Configuration
variable "s3_enable_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_enable_lifecycle_rules" {
  description = "Enable lifecycle rules for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_expiration_days" {
  description = "Number of days after which objects expire"
  type        = number
  default     = 365
}

variable "s3_lifecycle_noncurrent_version_expiration_days" {
  description = "Number of days after which noncurrent versions expire"
  type        = number
  default     = 30
}

variable "s3_backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 2555  # 7 years
}

variable "s3_log_retention_days" {
  description = "Number of days to retain logs in S3"
  type        = number
  default     = 90
}

variable "s3_enable_log_bucket" {
  description = "Create separate S3 bucket for logs"
  type        = bool
  default     = true
}

variable "s3_create_terraform_state_bucket" {
  description = "Create S3 bucket for Terraform state"
  type        = bool
  default     = false
}

# RDS Configuration
variable "rds_postgres_version" {
  description = "PostgreSQL version for RDS"
  type        = string
  default     = "15.4"
}

variable "rds_postgres_major_version" {
  description = "PostgreSQL major version for parameter group"
  type        = string
  default     = "15"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "Initial storage allocation in GB"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "Maximum storage allocation for autoscaling in GB"
  type        = number
  default     = 100
}

variable "rds_storage_encrypted" {
  description = "Enable RDS storage encryption"
  type        = bool
  default     = true
}

variable "rds_db_name" {
  description = "Name of the database"
  type        = string
  default     = "churnguard"
}

variable "rds_db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "rds_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "rds_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 0
}

variable "rds_performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = false
}

variable "rds_deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "rds_create_read_replica" {
  description = "Create read replica"
  type        = bool
  default     = false
}

# ElastiCache Configuration
variable "elasticache_redis_version" {
  description = "Redis version for ElastiCache"
  type        = string
  default     = "7.0"
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "elasticache_num_cache_clusters" {
  description = "Number of cache clusters"
  type        = number
  default     = 2
}

variable "elasticache_cluster_mode_enabled" {
  description = "Enable cluster mode for Redis"
  type        = bool
  default     = false
}

variable "elasticache_multi_az_enabled" {
  description = "Enable Multi-AZ for ElastiCache"
  type        = bool
  default     = false
}

variable "elasticache_automatic_failover_enabled" {
  description = "Enable automatic failover for ElastiCache"
  type        = bool
  default     = false
}

variable "elasticache_at_rest_encryption_enabled" {
  description = "Enable encryption at rest for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_transit_encryption_enabled" {
  description = "Enable encryption in transit for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_auth_token_enabled" {
  description = "Enable auth token for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_snapshot_retention_limit" {
  description = "Number of days to retain snapshots"
  type        = number
  default     = 5
}

# ALB Configuration
variable "alb_internal" {
  description = "Create internal ALB"
  type        = bool
  default     = false
}

variable "alb_enable_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = false
}

variable "alb_enable_https" {
  description = "Enable HTTPS listener for ALB"
  type        = bool
  default     = true
}

variable "alb_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = null
}

variable "alb_ssl_policy" {
  description = "SSL policy for HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS-1-2-2017-01"
}

variable "alb_enable_access_logs" {
  description = "Enable access logs for ALB"
  type        = bool
  default     = false
}

variable "alb_health_check_path" {
  description = "Health check path for ALB"
  type        = string
  default     = "/health"
}

# EKS Configuration
variable "eks_kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "eks_node_groups" {
  description = "EKS node group configurations"
  type = map(object({
    instance_types = list(string)
    capacity_type  = string
    desired_size   = number
    max_size       = number
    min_size       = number
    disk_size      = number
  }))
  default = {
    main = {
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
      desired_size   = 2
      max_size       = 5
      min_size       = 1
      disk_size      = 20
    }
  }
}

variable "enable_aws_load_balancer_controller" {
  description = "Enable AWS Load Balancer Controller"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "monitoring_alert_emails" {
  description = "List of email addresses for monitoring alerts"
  type        = list(string)
  default     = []
}

# Route53 DNS Configuration
variable "enable_dns" {
  description = "Enable DNS management with Route53"
  type        = bool
  default     = false
}

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

variable "create_ssl_certificate" {
  description = "Create ACM SSL certificate"
  type        = bool
  default     = false
}

variable "ssl_subject_alternative_names" {
  description = "Additional domain names for the SSL certificate"
  type        = list(string)
  default     = []
}

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

# Additional Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}