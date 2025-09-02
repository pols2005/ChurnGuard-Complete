# ChurnGuard Infrastructure Outputs
# Terraform outputs for resource information and connection details

#===============================================================================
# VPC Outputs
#===============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "database_subnets" {
  description = "List of database subnet IDs"
  value       = module.vpc.database_subnets
}

output "nat_gateway_ips" {
  description = "List of NAT Gateway public IPs"
  value       = module.vpc.nat_public_ips
}

#===============================================================================
# Security Group Outputs
#===============================================================================

output "alb_security_group_id" {
  description = "Application Load Balancer security group ID"
  value       = module.security_groups.alb_security_group_id
}

output "eks_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.security_groups.eks_security_group_id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = module.security_groups.rds_security_group_id
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = module.security_groups.redis_security_group_id
}

#===============================================================================
# IAM Outputs
#===============================================================================

output "eks_cluster_role_arn" {
  description = "EKS cluster IAM role ARN"
  value       = module.iam.eks_cluster_role_arn
}

output "eks_node_group_role_arn" {
  description = "EKS node group IAM role ARN"
  value       = module.iam.eks_node_group_role_arn
}

output "eks_pod_execution_role_arn" {
  description = "EKS pod execution IAM role ARN"
  value       = module.iam.eks_pod_execution_role_arn
}

#===============================================================================
# S3 Outputs
#===============================================================================

output "app_storage_bucket" {
  description = "Application storage S3 bucket name"
  value       = module.s3.app_storage_bucket
}

output "logs_bucket" {
  description = "Logs S3 bucket name"
  value       = module.s3.logs_bucket
}

output "backup_bucket" {
  description = "Backup S3 bucket name"
  value       = module.s3.backup_bucket
}

output "terraform_state_bucket" {
  description = "Terraform state S3 bucket name"
  value       = module.s3.terraform_state_bucket
}

#===============================================================================
# RDS Outputs
#===============================================================================

output "rds_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.db_instance_identifier
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.db_instance_name
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "rds_instance_arn" {
  description = "RDS instance ARN"
  value       = module.rds.db_instance_arn
}

#===============================================================================
# ElastiCache Redis Outputs
#===============================================================================

output "redis_cluster_endpoint" {
  description = "ElastiCache Redis cluster endpoint"
  value       = module.redis.redis_cluster_endpoint
  sensitive   = true
}

output "redis_cluster_id" {
  description = "ElastiCache Redis cluster ID"
  value       = module.redis.redis_cluster_id
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = module.redis.redis_port
}

output "redis_parameter_group_name" {
  description = "ElastiCache parameter group name"
  value       = module.redis.redis_parameter_group_name
}

#===============================================================================
# ALB Outputs
#===============================================================================

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Application Load Balancer zone ID"
  value       = module.alb.alb_zone_id
}

output "alb_arn" {
  description = "Application Load Balancer ARN"
  value       = module.alb.alb_arn
}

output "alb_listener_arn" {
  description = "Application Load Balancer listener ARN"
  value       = module.alb.alb_listener_arn
}

#===============================================================================
# EKS Outputs
#===============================================================================

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "eks_cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = module.eks.cluster_version
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_node_groups" {
  description = "EKS node groups information"
  value       = module.eks.node_groups
}

output "eks_oidc_issuer_url" {
  description = "EKS OIDC issuer URL"
  value       = module.eks.cluster_oidc_issuer_url
}

#===============================================================================
# CloudWatch Outputs
#===============================================================================

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = module.monitoring.cloudwatch_log_group_name
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = module.monitoring.cloudwatch_log_group_arn
}

#===============================================================================
# Route53 Outputs (Optional)
#===============================================================================

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.domain_name != "" ? module.route53[0].zone_id : null
}

output "route53_zone_name" {
  description = "Route53 hosted zone name"
  value       = var.domain_name != "" ? module.route53[0].zone_name : null
}

output "route53_name_servers" {
  description = "Route53 name servers"
  value       = var.domain_name != "" ? module.route53[0].name_servers : null
}

#===============================================================================
# Connection Information
#===============================================================================

output "connection_info" {
  description = "Connection information for accessing infrastructure"
  value = {
    application_url = var.domain_name != "" ? "https://${var.domain_name}" : "https://${module.alb.alb_dns_name}"
    
    database = {
      host     = module.rds.db_instance_address
      port     = module.rds.db_instance_port
      database = module.rds.db_instance_name
    }
    
    redis = {
      host = module.redis.redis_cluster_address
      port = module.redis.redis_port
    }
    
    kubernetes = {
      cluster_name = module.eks.cluster_name
      endpoint     = module.eks.cluster_endpoint
    }
  }
  sensitive = true
}

#===============================================================================
# Environment Information
#===============================================================================

output "environment_info" {
  description = "Environment and deployment information"
  value = {
    environment    = var.environment
    region        = var.aws_region
    project       = var.project_name
    deployment_time = timestamp()
    terraform_version = "~> 1.5.0"
  }
}

#===============================================================================
# Cost Estimation Tags
#===============================================================================

output "cost_center_tags" {
  description = "Tags for cost center tracking"
  value = {
    Project     = "ChurnGuard"
    Environment = var.environment
    CostCenter  = "Engineering"
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}

#===============================================================================
# kubectl Configuration Command
#===============================================================================

output "kubectl_config_command" {
  description = "Command to configure kubectl for EKS cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}