# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Copyright 2024 Canonical Ltd.
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
    opencti-connector = "opencti-connector"
    opensearch-client = "opensearch-client"
    redis             = "redis"
    s3                = "s3"
  }
}

output "provides" {
  value = {
    grafana-dashboard = "grafana-dashboard"
    metrics-endpoint  = "metrics-endpoint"
  }
}
