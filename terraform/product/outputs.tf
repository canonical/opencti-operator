# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed opencti application."
  value       = module.opencti.app_name
}

output "requires" {
  value = {
    ingress           = "ingress"
    logging           = "logging"
    opencti_connector = "opencti-connector"
  }
}

output "provides" {
  value = {
    grafana_dashboard = "grafana-dashboard"
    metrics_endpoint  = "metrics-endpoint"
  }
}
