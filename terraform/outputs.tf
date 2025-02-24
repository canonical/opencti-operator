# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.opencti.name
}

output "requires" {
  value = {
    amqp              = "amqp"
    ingress           = "ingress"
    logging           = "logging"
    opencti_connector = "opencti-connector"
    opensearch_client = "opensearch-client"
    redis             = "redis"
    s3                = "s3"
  }
}

output "provides" {
  value = {
    grafana_dashboard = "grafana-dashboard"
    metrics_endpoint  = "metrics-endpoint"
  }
}
