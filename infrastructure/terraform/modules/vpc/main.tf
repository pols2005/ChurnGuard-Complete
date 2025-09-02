# ChurnGuard VPC Module
# Creates VPC with public, private, and database subnets across 3 availability zones

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
  
  # Calculate number of AZs to use
  max_azs = length(var.azs)
  
  # Create tags for subnets
  public_subnet_tags = merge(
    var.tags,
    {
      Name = "${local.name}-public"
      Type = "Public"
      "kubernetes.io/role/elb" = "1"
    }
  )
  
  private_subnet_tags = merge(
    var.tags,
    {
      Name = "${local.name}-private"
      Type = "Private"
      "kubernetes.io/role/internal-elb" = "1"
    }
  )
  
  database_subnet_tags = merge(
    var.tags,
    {
      Name = "${local.name}-database"
      Type = "Database"
    }
  )
}

#===============================================================================
# VPC
#===============================================================================

resource "aws_vpc" "main" {
  cidr_block           = var.cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support
  
  tags = merge(
    var.tags,
    {
      Name = local.name
    }
  )
}

#===============================================================================
# Internet Gateway
#===============================================================================

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-igw"
    }
  )
}

#===============================================================================
# Public Subnets
#===============================================================================

resource "aws_subnet" "public" {
  count = length(var.public_subnets)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(
    local.public_subnet_tags,
    {
      Name = "${local.name}-public-${var.azs[count.index]}"
    }
  )
}

#===============================================================================
# Private Subnets
#===============================================================================

resource "aws_subnet" "private" {
  count = length(var.private_subnets)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.azs[count.index]
  
  tags = merge(
    local.private_subnet_tags,
    {
      Name = "${local.name}-private-${var.azs[count.index]}"
    }
  )
}

#===============================================================================
# Database Subnets
#===============================================================================

resource "aws_subnet" "database" {
  count = length(var.database_subnets)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_subnets[count.index]
  availability_zone = var.azs[count.index]
  
  tags = merge(
    local.database_subnet_tags,
    {
      Name = "${local.name}-database-${var.azs[count.index]}"
    }
  )
}

#===============================================================================
# Elastic IPs for NAT Gateways
#===============================================================================

resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? local.max_azs : 0
  
  domain = "vpc"
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-nat-${var.azs[count.index]}"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

#===============================================================================
# NAT Gateways
#===============================================================================

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? local.max_azs : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-nat-${var.azs[count.index]}"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

#===============================================================================
# Route Tables
#===============================================================================

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-public"
    }
  )
}

# Private Route Tables (one per AZ)
resource "aws_route_table" "private" {
  count = local.max_azs
  
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-private-${var.azs[count.index]}"
    }
  )
}

# Database Route Table
resource "aws_route_table" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0
  
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-database"
    }
  )
}

#===============================================================================
# Routes
#===============================================================================

# Public route to Internet Gateway
resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
  
  timeouts {
    create = "5m"
  }
}

# Private routes to NAT Gateways
resource "aws_route" "private_nat_gateway" {
  count = var.enable_nat_gateway ? local.max_azs : 0
  
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
  
  timeouts {
    create = "5m"
  }
}

#===============================================================================
# Route Table Associations
#===============================================================================

# Public subnet associations
resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private subnet associations
resource "aws_route_table_association" "private" {
  count = length(var.private_subnets)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Database subnet associations
resource "aws_route_table_association" "database" {
  count = length(var.database_subnets)
  
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[0].id
}

#===============================================================================
# Database Subnet Group
#===============================================================================

resource "aws_db_subnet_group" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0
  
  name       = "${local.name}-database"
  subnet_ids = aws_subnet.database[*].id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-database-subnet-group"
    }
  )
}

#===============================================================================
# ElastiCache Subnet Group
#===============================================================================

resource "aws_elasticache_subnet_group" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0
  
  name       = "${local.name}-elasticache"
  subnet_ids = aws_subnet.database[*].id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-elasticache-subnet-group"
    }
  )
}

#===============================================================================
# VPC Flow Logs (Optional)
#===============================================================================

resource "aws_flow_log" "vpc" {
  count = var.enable_flow_log ? 1 : 0
  
  iam_role_arn    = var.create_flow_log_cloudwatch_iam_role ? aws_iam_role.flow_log[0].arn : var.flow_log_cloudwatch_iam_role_arn
  log_destination = var.create_flow_log_cloudwatch_log_group ? aws_cloudwatch_log_group.vpc[0].arn : var.flow_log_cloudwatch_log_group_arn
  traffic_type    = var.flow_log_traffic_type
  vpc_id          = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${local.name}-flow-log"
    }
  )
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_log_group ? 1 : 0
  
  name              = "/aws/vpc/flowlog/${local.name}"
  retention_in_days = var.flow_log_cloudwatch_log_group_retention_in_days
  
  tags = var.tags
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_iam_role ? 1 : 0
  
  name = "${local.name}-flow-log-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# IAM Role Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_iam_role ? 1 : 0
  
  name = "${local.name}-flow-log-policy"
  role = aws_iam_role.flow_log[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}