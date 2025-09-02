# ChurnGuard Infrastructure as Code
# Main Terraform configuration for AWS cloud deployment

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }

  # Backend configuration for remote state management
  backend "s3" {
    # These values should be provided via backend config file or CLI
    # bucket         = "churnguard-terraform-state-${environment}"
    # key            = "infrastructure/terraform.tfstate"
    # region         = var.aws_region
    # encrypt        = true
    # dynamodb_table = "churnguard-terraform-locks-${environment}"
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ChurnGuard"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}

# Configure Kubernetes provider
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# Configure Helm provider
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name = "churnguard-${var.environment}"
  
  # Calculate subnet CIDRs
  vpc_cidr = var.vpc_cidr
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)
  
  # Create subnet CIDRs dynamically
  public_subnets  = [for i in range(3) : cidrsubnet(local.vpc_cidr, 8, i)]
  private_subnets = [for i in range(3) : cidrsubnet(local.vpc_cidr, 8, i + 10)]
  database_subnets = [for i in range(3) : cidrsubnet(local.vpc_cidr, 8, i + 20)]
  
  tags = {
    Project     = "ChurnGuard"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

#===============================================================================
# VPC and Networking
#===============================================================================

module "vpc" {
  source = "./modules/vpc"
  
  name = local.name
  cidr = local.vpc_cidr
  
  azs                 = local.azs
  public_subnets      = local.public_subnets
  private_subnets     = local.private_subnets
  database_subnets    = local.database_subnets
  
  enable_nat_gateway     = true
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true
  
  # Enable VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
  
  tags = local.tags
}

#===============================================================================
# Security Groups
#===============================================================================

module "security_groups" {
  source = "./modules/security-groups"
  
  name   = local.name
  vpc_id = module.vpc.vpc_id
  
  tags = local.tags
}

#===============================================================================
# IAM Roles and Policies
#===============================================================================

module "iam" {
  source = "./modules/iam"
  
  name        = local.name
  environment = var.environment
  
  tags = local.tags
}

#===============================================================================
# S3 Buckets
#===============================================================================

module "s3" {
  source = "./modules/s3"
  
  name        = local.name
  environment = var.environment
  
  tags = local.tags
}

#===============================================================================
# RDS PostgreSQL Database
#===============================================================================

module "rds" {
  source = "./modules/rds"
  
  name        = local.name
  environment = var.environment
  
  vpc_id                = module.vpc.vpc_id
  db_subnet_group_name  = module.vpc.database_subnet_group
  security_group_ids    = [module.security_groups.rds_security_group_id]
  
  # Database configuration
  engine_version    = var.rds_engine_version
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  
  # High availability
  multi_az               = var.environment == "production"
  backup_retention_period = var.environment == "production" ? 30 : 7
  
  # Security
  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"
  
  tags = local.tags
}

#===============================================================================
# ElastiCache Redis Cluster
#===============================================================================

module "redis" {
  source = "./modules/redis"
  
  name        = local.name
  environment = var.environment
  
  subnet_group_name  = module.vpc.elasticache_subnet_group_name
  security_group_ids = [module.security_groups.redis_security_group_id]
  
  # Cluster configuration
  node_type               = var.redis_node_type
  num_cache_clusters      = var.redis_num_cache_clusters
  parameter_group_name    = var.redis_parameter_group_name
  engine_version         = var.redis_engine_version
  
  # High availability
  automatic_failover_enabled = var.environment == "production"
  multi_az_enabled          = var.environment == "production"
  
  tags = local.tags
}

#===============================================================================
# Application Load Balancer
#===============================================================================

module "alb" {
  source = "./modules/alb"
  
  name        = local.name
  environment = var.environment
  
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets
  security_group_ids = [module.security_groups.alb_security_group_id]
  
  # SSL configuration
  ssl_certificate_arn = var.ssl_certificate_arn
  
  tags = local.tags
}

#===============================================================================
# EKS Cluster
#===============================================================================

module "eks" {
  source = "./modules/eks"
  
  name        = local.name
  environment = var.environment
  
  vpc_id                    = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets
  
  # Cluster configuration
  cluster_version = var.eks_cluster_version
  
  # Node groups
  node_groups = var.eks_node_groups
  
  # Security
  cluster_security_group_additional_rules = {
    ingress_alb = {
      description = "ALB to cluster communication"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      type        = "ingress"
      source_security_group_id = module.security_groups.alb_security_group_id
    }
  }
  
  tags = local.tags
}

#===============================================================================
# CloudWatch Monitoring
#===============================================================================

module "monitoring" {
  source = "./modules/monitoring"
  
  name        = local.name
  environment = var.environment
  
  # EKS cluster info for monitoring
  cluster_name = module.eks.cluster_name
  
  # RDS instance info for monitoring
  db_instance_identifier = module.rds.db_instance_identifier
  
  # Redis cluster info for monitoring
  redis_cluster_id = module.redis.redis_cluster_id
  
  tags = local.tags
}

#===============================================================================
# Route53 DNS (Optional)
#===============================================================================

module "route53" {
  source = "./modules/route53"
  count  = var.domain_name != "" ? 1 : 0
  
  domain_name = var.domain_name
  alb_dns_name = module.alb.alb_dns_name
  alb_zone_id  = module.alb.alb_zone_id
  
  tags = local.tags
}