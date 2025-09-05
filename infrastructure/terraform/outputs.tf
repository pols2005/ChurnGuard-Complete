# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.vpc.database_subnet_ids
}

# Security Groups Outputs
output "security_groups" {
  description = "Security group IDs"
  value = {
    alb         = module.security_groups.alb_security_group_id
    eks_cluster = module.security_groups.eks_cluster_security_group_id
    eks_nodes   = module.security_groups.eks_nodes_security_group_id
    rds         = module.security_groups.rds_security_group_id
    redis       = module.security_groups.redis_security_group_id
  }
}

# S3 Outputs
output "s3_buckets" {
  description = "S3 bucket information"
  value = {
    app_storage = module.s3.app_storage_bucket_id
    backups     = module.s3.backups_bucket_id
    logs        = module.s3.logs_bucket_id
  }
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "rds_db_name" {
  description = "RDS database name"
  value       = module.rds.db_instance_name
}

output "rds_password_secret_arn" {
  description = "ARN of the secret containing RDS password"
  value       = module.rds.db_password_secret_arn
}

# ElastiCache Outputs
output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.port
}

output "redis_auth_token_secret_arn" {
  description = "ARN of the secret containing Redis auth token"
  value       = module.elasticache.auth_token_secret_arn
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.load_balancer_dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID of the load balancer"
  value       = module.alb.load_balancer_zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = module.alb.load_balancer_arn
}

output "alb_target_group_arn" {
  description = "ARN of the default target group"
  value       = module.alb.default_target_group_arn
}

# EKS Outputs
output "eks_cluster_id" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_id
}

output "eks_cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "eks_cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_primary_security_group_id
}

output "eks_cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "eks_cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks.cluster_version
}

output "eks_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = module.eks.cluster_oidc_issuer_url
}

output "eks_node_groups" {
  description = "EKS node groups"
  value       = module.eks.node_groups
}

# Monitoring Outputs
output "monitoring_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = var.enable_monitoring ? module.monitoring[0].dashboard_url : null
}

output "monitoring_sns_topic_arn" {
  description = "SNS topic ARN for monitoring alerts"
  value       = var.enable_monitoring ? module.monitoring[0].sns_topic_arn : null
}

# kubectl Configuration
output "kubectl_config" {
  description = "kubectl configuration command"
  value = {
    command = "aws eks update-kubeconfig --region ${var.aws_region} --name ${var.project_name}-${var.environment}-cluster"
    region  = var.aws_region
    cluster = "${var.project_name}-${var.environment}-cluster"
  }
}

# Connection Information
output "connection_info" {
  description = "Connection information for services"
  value = {
    database = {
      endpoint = module.rds.db_instance_endpoint
      port     = module.rds.db_instance_port
      name     = module.rds.db_instance_name
      secret_arn = module.rds.db_password_secret_arn
    }
    redis = {
      endpoint = module.elasticache.primary_endpoint_address
      port     = module.elasticache.port
      secret_arn = module.elasticache.auth_token_secret_arn
    }
    load_balancer = {
      dns_name = module.alb.load_balancer_dns_name
      zone_id  = module.alb.load_balancer_zone_id
      https_endpoint = module.alb.https_endpoint
    }
  }
  sensitive = true
}

# Deployment Information
output "deployment_info" {
  description = "Information needed for application deployment"
  value = {
    project_name       = var.project_name
    environment        = var.environment
    region            = var.aws_region
    vpc_id            = module.vpc.vpc_id
    private_subnets   = module.vpc.private_subnet_ids
    security_groups = {
      alb       = module.security_groups.alb_security_group_id
      eks_nodes = module.security_groups.eks_nodes_security_group_id
    }
    target_group_arn = module.alb.default_target_group_arn
  }
}

# Resource ARNs for IAM Policies
output "resource_arns" {
  description = "ARNs of created resources for IAM policy references"
  value = {
    s3_buckets = {
      app_storage = module.s3.app_storage_bucket_arn
      backups     = module.s3.backups_bucket_arn
      logs        = module.s3.logs_bucket_arn
    }
    secrets_manager = {
      rds_password = module.rds.db_password_secret_arn
      redis_token  = module.elasticache.auth_token_secret_arn
    }
  }
}

# Route53 DNS Outputs
output "dns_configuration" {
  description = "DNS configuration information"
  value       = var.enable_dns ? module.route53[0].dns_configuration : null
}

output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.enable_dns ? module.route53[0].hosted_zone_id : null
}

output "hosted_zone_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = var.enable_dns ? module.route53[0].hosted_zone_name_servers : null
}

output "ssl_certificate_arn" {
  description = "ACM SSL certificate ARN"
  value       = var.enable_dns ? module.route53[0].validated_certificate_arn : null
}

output "domain_endpoints" {
  description = "Domain endpoints for the application"
  value = var.enable_dns && var.domain_name != null ? {
    main_domain = var.domain_name
    www_domain  = var.create_www_redirect ? "www.${var.domain_name}" : null
    api_domain  = var.create_api_subdomain ? "api.${var.domain_name}" : null
    https_main  = var.create_ssl_certificate ? "https://${var.domain_name}" : null
    https_www   = var.create_ssl_certificate && var.create_www_redirect ? "https://www.${var.domain_name}" : null
    https_api   = var.create_ssl_certificate && var.create_api_subdomain ? "https://api.${var.domain_name}" : null
  } : null
}

output "dns_setup_instructions" {
  description = "Instructions for setting up DNS"
  value       = var.enable_dns ? module.route53[0].dns_setup_instructions : null
}