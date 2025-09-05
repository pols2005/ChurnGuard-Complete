terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    # Backend configuration will be provided via backend config file
    # Example: terraform init -backend-config=backend-dev.conf
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedAt   = formatdate("YYYY-MM-DD", timestamp())
  }
}

# Module Calls
module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  cidr         = var.vpc_cidr
  azs          = var.availability_zones

  public_subnets   = var.public_subnet_cidrs
  private_subnets  = var.private_subnet_cidrs
  database_subnets = var.database_subnet_cidrs

  enable_nat_gateway   = var.enable_nat_gateway
  enable_vpn_gateway   = var.enable_vpn_gateway
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support
  enable_flow_log      = var.enable_vpc_flow_logs

  tags = local.common_tags
}

module "security_groups" {
  source = "./modules/security-groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id

  create_bastion_sg = var.create_bastion_host

  tags = local.common_tags
}

module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  enable_load_balancer_controller = var.enable_aws_load_balancer_controller

  tags = local.common_tags
}

module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment

  enable_versioning                             = var.s3_enable_versioning
  enable_lifecycle_rules                       = var.s3_enable_lifecycle_rules
  lifecycle_expiration_days                     = var.s3_lifecycle_expiration_days
  lifecycle_noncurrent_version_expiration_days  = var.s3_lifecycle_noncurrent_version_expiration_days
  backup_retention_days                         = var.s3_backup_retention_days
  log_retention_days                           = var.s3_log_retention_days
  enable_log_bucket                            = var.s3_enable_log_bucket
  create_terraform_state_bucket                = var.s3_create_terraform_state_bucket

  tags = local.common_tags
}

module "rds" {
  source = "./modules/rds"

  project_name         = var.project_name
  environment          = var.environment
  database_subnet_ids  = module.vpc.database_subnet_ids
  security_group_ids   = [module.security_groups.rds_security_group_id]

  postgres_version              = var.rds_postgres_version
  postgres_major_version        = var.rds_postgres_major_version
  instance_class                = var.rds_instance_class
  allocated_storage             = var.rds_allocated_storage
  max_allocated_storage         = var.rds_max_allocated_storage
  storage_encrypted             = var.rds_storage_encrypted
  db_name                       = var.rds_db_name
  db_username                   = var.rds_db_username
  backup_retention_period       = var.rds_backup_retention_period
  multi_az                      = var.rds_multi_az
  monitoring_interval           = var.rds_monitoring_interval
  performance_insights_enabled  = var.rds_performance_insights_enabled
  deletion_protection           = var.rds_deletion_protection
  create_read_replica           = var.rds_create_read_replica

  tags = local.common_tags
}

module "elasticache" {
  source = "./modules/elasticache"

  project_name       = var.project_name
  environment        = var.environment
  subnet_ids         = module.vpc.database_subnet_ids
  security_group_ids = [module.security_groups.redis_security_group_id]

  redis_version                = var.elasticache_redis_version
  node_type                    = var.elasticache_node_type
  num_cache_clusters           = var.elasticache_num_cache_clusters
  cluster_mode_enabled         = var.elasticache_cluster_mode_enabled
  multi_az_enabled             = var.elasticache_multi_az_enabled
  automatic_failover_enabled   = var.elasticache_automatic_failover_enabled
  at_rest_encryption_enabled   = var.elasticache_at_rest_encryption_enabled
  transit_encryption_enabled   = var.elasticache_transit_encryption_enabled
  auth_token_enabled           = var.elasticache_auth_token_enabled
  snapshot_retention_limit     = var.elasticache_snapshot_retention_limit

  tags = local.common_tags
}

module "alb" {
  source = "./modules/alb"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.alb_security_group_id]

  internal                    = var.alb_internal
  enable_deletion_protection  = var.alb_enable_deletion_protection
  enable_https                = var.alb_enable_https
  certificate_arn             = var.alb_certificate_arn
  ssl_policy                  = var.alb_ssl_policy
  enable_access_logs          = var.alb_enable_access_logs
  access_logs_bucket          = var.alb_enable_access_logs ? module.s3.logs_bucket_id : null
  health_check_path           = var.alb_health_check_path

  tags = local.common_tags
}

module "eks" {
  source = "./modules/eks"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids

  cluster_service_role_arn = module.iam.eks_cluster_role_arn
  node_group_role_arn      = module.iam.eks_node_group_role_arn

  kubernetes_version           = var.eks_kubernetes_version
  endpoint_private_access      = true
  endpoint_public_access       = true
  enable_irsa                  = true
  enable_aws_load_balancer_controller = var.enable_aws_load_balancer_controller
  aws_load_balancer_controller_policy_arn = module.iam.load_balancer_controller_role_arn

  node_groups = {
    for k, v in var.eks_node_groups : k => {
      capacity_type                = v.capacity_type
      instance_types               = v.instance_types
      ami_type                     = "AL2_x86_64"
      disk_size                    = v.disk_size
      desired_size                 = v.desired_size
      max_size                     = v.max_size
      min_size                     = v.min_size
      max_unavailable_percentage   = 25
      launch_template_id           = null
      launch_template_version      = null
      enable_remote_access         = false
      key_name                     = null
      source_security_group_ids    = []
      labels                       = {}
      taints                       = []
      tags                         = {}
    }
  }

  cluster_security_group_ids = [module.security_groups.eks_cluster_security_group_id]

  tags = local.common_tags
}

module "monitoring" {
  count = var.enable_monitoring ? 1 : 0

  source = "./modules/monitoring"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  alert_email_addresses = var.monitoring_alert_emails

  # EKS monitoring
  create_eks_log_groups = true
  create_eks_alarms     = true
  create_eks_widgets    = true
  cluster_name          = module.eks.cluster_id

  # RDS monitoring
  create_rds_alarms  = true
  create_rds_widgets = true
  rds_instance_id    = module.rds.db_instance_id

  # ElastiCache monitoring
  create_elasticache_alarms  = true
  create_elasticache_widgets = true
  elasticache_cluster_id     = module.elasticache.replication_group_id

  # ALB monitoring
  create_alb_alarms  = true
  create_alb_widgets = true
  alb_arn_suffix     = module.alb.load_balancer_arn_suffix

  # Application monitoring
  create_application_log_metrics = true
  create_log_insights_queries    = true
  create_composite_alarms        = true

  tags = local.common_tags
}