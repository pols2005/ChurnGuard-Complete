# Route53 DNS Module for ChurnGuard
# Optional DNS management for custom domains

locals {
  name = "${var.project_name}-${var.environment}"
}

# Route53 Hosted Zone
resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0
  
  name = var.domain_name
  
  tags = merge(var.tags, {
    Name = "${local.name}-hosted-zone"
  })
}

# ACM Certificate for the domain
resource "aws_acm_certificate" "main" {
  count = var.create_ssl_certificate ? 1 : 0
  
  domain_name       = var.domain_name
  subject_alternative_names = var.subject_alternative_names
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = merge(var.tags, {
    Name = "${local.name}-certificate"
  })
}

# Certificate validation records
resource "aws_route53_record" "cert_validation" {
  for_each = var.create_ssl_certificate && var.create_hosted_zone ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main[0].zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "main" {
  count = var.create_ssl_certificate && var.create_hosted_zone ? 1 : 0
  
  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
  
  timeouts {
    create = "5m"
  }
}

# A record pointing to ALB
resource "aws_route53_record" "alb" {
  count = var.create_hosted_zone && var.alb_dns_name != null ? 1 : 0
  
  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# AAAA record for IPv6 (optional)
resource "aws_route53_record" "alb_ipv6" {
  count = var.create_hosted_zone && var.alb_dns_name != null && var.enable_ipv6 ? 1 : 0
  
  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "AAAA"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# WWW subdomain redirect
resource "aws_route53_record" "www" {
  count = var.create_hosted_zone && var.alb_dns_name != null && var.create_www_redirect ? 1 : 0
  
  zone_id = aws_route53_zone.main[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# API subdomain
resource "aws_route53_record" "api" {
  count = var.create_hosted_zone && var.alb_dns_name != null && var.create_api_subdomain ? 1 : 0
  
  zone_id = aws_route53_zone.main[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Health check for the main domain
resource "aws_route53_health_check" "main" {
  count = var.create_health_check ? 1 : 0
  
  fqdn                            = var.domain_name
  port                            = 443
  type                            = "HTTPS"
  resource_path                   = var.health_check_path
  failure_threshold               = var.health_check_failure_threshold
  request_interval                = var.health_check_request_interval
  measure_latency                 = var.health_check_measure_latency
  cloudwatch_logs_region          = var.aws_region
  insufficient_data_health_status = "Failure"
  
  tags = merge(var.tags, {
    Name = "${local.name}-health-check"
  })
}

# CloudWatch alarm for health check
resource "aws_cloudwatch_metric_alarm" "health_check" {
  count = var.create_health_check ? 1 : 0
  
  alarm_name          = "${local.name}-health-check-alarm"
  comparison_operator = "LessThanThreshold"
  datapoints_to_alarm = var.health_check_alarm_datapoints
  evaluation_periods  = var.health_check_alarm_evaluation_periods
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "This metric monitors ${var.domain_name} health check"
  alarm_actions       = var.health_check_alarm_actions
  ok_actions          = var.health_check_alarm_actions
  treat_missing_data  = "breaching"
  
  dimensions = {
    HealthCheckId = aws_route53_health_check.main[0].id
  }
  
  tags = var.tags
}