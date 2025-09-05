# Route53 Outputs

# Hosted Zone Outputs
output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : null
}

output "hosted_zone_name_servers" {
  description = "Route53 hosted zone name servers"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : null
}

output "hosted_zone_arn" {
  description = "Route53 hosted zone ARN"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].arn : null
}

# SSL Certificate Outputs
output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = var.create_ssl_certificate ? aws_acm_certificate.main[0].arn : null
}

output "certificate_status" {
  description = "ACM certificate status"
  value       = var.create_ssl_certificate ? aws_acm_certificate.main[0].status : null
}

output "certificate_domain_validation_options" {
  description = "Certificate domain validation options"
  value       = var.create_ssl_certificate ? aws_acm_certificate.main[0].domain_validation_options : null
  sensitive   = true
}

output "validated_certificate_arn" {
  description = "Validated ACM certificate ARN"
  value       = var.create_ssl_certificate && var.create_hosted_zone ? aws_acm_certificate_validation.main[0].certificate_arn : null
}

# DNS Record Outputs
output "domain_name" {
  description = "Primary domain name"
  value       = var.domain_name
}

output "main_record_name" {
  description = "Main A record name"
  value       = var.create_hosted_zone && var.alb_dns_name != null ? aws_route53_record.alb[0].name : null
}

output "main_record_fqdn" {
  description = "Main A record FQDN"
  value       = var.create_hosted_zone && var.alb_dns_name != null ? aws_route53_record.alb[0].fqdn : null
}

output "www_record_name" {
  description = "WWW A record name"
  value       = var.create_hosted_zone && var.alb_dns_name != null && var.create_www_redirect ? aws_route53_record.www[0].name : null
}

output "www_record_fqdn" {
  description = "WWW A record FQDN"
  value       = var.create_hosted_zone && var.alb_dns_name != null && var.create_www_redirect ? aws_route53_record.www[0].fqdn : null
}

output "api_record_name" {
  description = "API A record name"
  value       = var.create_hosted_zone && var.alb_dns_name != null && var.create_api_subdomain ? aws_route53_record.api[0].name : null
}

output "api_record_fqdn" {
  description = "API A record FQDN"
  value       = var.create_hosted_zone && var.alb_dns_name != null && var.create_api_subdomain ? aws_route53_record.api[0].fqdn : null
}

# Health Check Outputs
output "health_check_id" {
  description = "Route53 health check ID"
  value       = var.create_health_check ? aws_route53_health_check.main[0].id : null
}

output "health_check_arn" {
  description = "Route53 health check ARN"
  value       = var.create_health_check ? aws_route53_health_check.main[0].arn : null
}

output "health_check_cloudwatch_alarm_name" {
  description = "CloudWatch alarm name for health check"
  value       = var.create_health_check ? aws_cloudwatch_metric_alarm.health_check[0].alarm_name : null
}

# Configuration Summary
output "dns_configuration" {
  description = "DNS configuration summary"
  value = var.create_hosted_zone ? {
    domain_name           = var.domain_name
    hosted_zone_id        = aws_route53_zone.main[0].zone_id
    name_servers          = aws_route53_zone.main[0].name_servers
    certificate_arn       = var.create_ssl_certificate ? aws_acm_certificate.main[0].arn : null
    health_check_enabled  = var.create_health_check
    www_redirect_enabled  = var.create_www_redirect
    api_subdomain_enabled = var.create_api_subdomain
    ipv6_enabled          = var.enable_ipv6
  } : null
}

# Name Server Instructions
output "dns_setup_instructions" {
  description = "Instructions for setting up DNS"
  value = var.create_hosted_zone ? {
    message = "Update your domain registrar's name servers to the following:"
    name_servers = aws_route53_zone.main[0].name_servers
    verification_command = "dig NS ${var.domain_name}"
  } : null
}