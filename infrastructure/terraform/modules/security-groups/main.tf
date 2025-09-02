# ChurnGuard Security Groups Module
# Creates security groups for different application tiers

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  name = var.name
}

#===============================================================================
# Application Load Balancer Security Group
#===============================================================================

resource "aws_security_group" "alb" {
  name_prefix = "${local.name}-alb-"
  vpc_id      = var.vpc_id
  description = "Security group for Application Load Balancer"

  # HTTP from anywhere
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS from anywhere
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-alb-sg"
    Type = "ALB"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# EKS Cluster Security Group
#===============================================================================

resource "aws_security_group" "eks_cluster" {
  name_prefix = "${local.name}-eks-cluster-"
  vpc_id      = var.vpc_id
  description = "Security group for EKS cluster control plane"

  # HTTPS from ALB
  ingress {
    description     = "HTTPS from ALB"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # HTTPS from EKS nodes
  ingress {
    description     = "HTTPS from EKS nodes"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-eks-cluster-sg"
    Type = "EKS-Cluster"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# EKS Node Group Security Group
#===============================================================================

resource "aws_security_group" "eks_nodes" {
  name_prefix = "${local.name}-eks-nodes-"
  vpc_id      = var.vpc_id
  description = "Security group for EKS node groups"

  # Node to node communication
  ingress {
    description = "Node to node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Node to node communication (UDP)
  ingress {
    description = "Node to node communication UDP"
    from_port   = 0
    to_port     = 65535
    protocol    = "udp"
    self        = true
  }

  # Control plane to node groups (kubelet)
  ingress {
    description     = "Control plane to node groups"
    from_port       = 10250
    to_port         = 10250
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  # Control plane to node groups (extension API servers)
  ingress {
    description     = "Extension API servers"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  # ALB to node groups
  ingress {
    description     = "ALB to node groups"
    from_port       = 1024
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-eks-nodes-sg"
    Type = "EKS-Nodes"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# RDS Security Group
#===============================================================================

resource "aws_security_group" "rds" {
  name_prefix = "${local.name}-rds-"
  vpc_id      = var.vpc_id
  description = "Security group for RDS PostgreSQL database"

  # PostgreSQL from EKS nodes
  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  # PostgreSQL from bastion (if needed)
  dynamic "ingress" {
    for_each = var.enable_bastion_access ? [1] : []
    content {
      description     = "PostgreSQL from bastion"
      from_port       = 5432
      to_port         = 5432
      protocol        = "tcp"
      security_groups = [aws_security_group.bastion[0].id]
    }
  }

  # No outbound traffic needed for RDS
  egress {
    description = "No outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = []
  }

  tags = merge(var.tags, {
    Name = "${local.name}-rds-sg"
    Type = "Database"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# ElastiCache Redis Security Group
#===============================================================================

resource "aws_security_group" "redis" {
  name_prefix = "${local.name}-redis-"
  vpc_id      = var.vpc_id
  description = "Security group for ElastiCache Redis cluster"

  # Redis from EKS nodes
  ingress {
    description     = "Redis from EKS nodes"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  # Redis from bastion (if needed)
  dynamic "ingress" {
    for_each = var.enable_bastion_access ? [1] : []
    content {
      description     = "Redis from bastion"
      from_port       = 6379
      to_port         = 6379
      protocol        = "tcp"
      security_groups = [aws_security_group.bastion[0].id]
    }
  }

  # No outbound traffic needed for Redis
  egress {
    description = "No outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = []
  }

  tags = merge(var.tags, {
    Name = "${local.name}-redis-sg"
    Type = "Cache"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# Bastion Host Security Group (Optional)
#===============================================================================

resource "aws_security_group" "bastion" {
  count = var.enable_bastion_access ? 1 : 0
  
  name_prefix = "${local.name}-bastion-"
  vpc_id      = var.vpc_id
  description = "Security group for bastion host"

  # SSH from allowed CIDRs
  ingress {
    description = "SSH from allowed CIDRs"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.bastion_allowed_cidrs
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-bastion-sg"
    Type = "Bastion"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# VPC Endpoints Security Group (Optional)
#===============================================================================

resource "aws_security_group" "vpc_endpoints" {
  count = var.enable_vpc_endpoints ? 1 : 0
  
  name_prefix = "${local.name}-vpc-endpoints-"
  vpc_id      = var.vpc_id
  description = "Security group for VPC endpoints"

  # HTTPS from EKS nodes
  ingress {
    description     = "HTTPS from EKS nodes"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  # HTTPS from private subnets
  ingress {
    description = "HTTPS from private subnets"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.private_subnet_cidrs
  }

  # No outbound traffic needed for VPC endpoints
  egress {
    description = "No outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = []
  }

  tags = merge(var.tags, {
    Name = "${local.name}-vpc-endpoints-sg"
    Type = "VPC-Endpoints"
  })

  lifecycle {
    create_before_destroy = true
  }
}

#===============================================================================
# Additional Security Group Rules (Optional)
#===============================================================================

# Custom ingress rules for ALB
resource "aws_security_group_rule" "alb_custom_ingress" {
  count = length(var.alb_additional_ingress_rules)
  
  security_group_id = aws_security_group.alb.id
  type              = "ingress"
  
  from_port   = var.alb_additional_ingress_rules[count.index].from_port
  to_port     = var.alb_additional_ingress_rules[count.index].to_port
  protocol    = var.alb_additional_ingress_rules[count.index].protocol
  cidr_blocks = var.alb_additional_ingress_rules[count.index].cidr_blocks
  
  description = var.alb_additional_ingress_rules[count.index].description
}

# Custom ingress rules for EKS nodes
resource "aws_security_group_rule" "eks_nodes_custom_ingress" {
  count = length(var.eks_nodes_additional_ingress_rules)
  
  security_group_id = aws_security_group.eks_nodes.id
  type              = "ingress"
  
  from_port   = var.eks_nodes_additional_ingress_rules[count.index].from_port
  to_port     = var.eks_nodes_additional_ingress_rules[count.index].to_port
  protocol    = var.eks_nodes_additional_ingress_rules[count.index].protocol
  cidr_blocks = var.eks_nodes_additional_ingress_rules[count.index].cidr_blocks
  
  description = var.eks_nodes_additional_ingress_rules[count.index].description
}