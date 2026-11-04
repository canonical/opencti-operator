# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.opencti.name
}

output "application" {
  description = "The deployed opencti Juju application resource."
  value       = juju_application.opencti
}

output "provides" {
  description = "Provides endpoints of the opencti charm."
  value = {
    grafana_dashboard = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "grafana-dashboard"
    }
    metrics_endpoint = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "metrics-endpoint"
    }
  }
}

output "requires" {
  description = "Requires endpoints of the opencti charm."
  value = {
    amqp = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "amqp"
    }
    ingress = {
      kind       = "endpoint"
      name       = juju_application.opencti.name
      endpoint   = "ingress"
      controller = null
    }
    logging = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "logging"
    }
    opencti_connector = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "opencti-connector"
    }
    opensearch_client = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "opensearch-client"
    }
    redis = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "redis"
    }
    s3 = {
      kind     = "endpoint"
      name     = juju_application.opencti.name
      endpoint = "s3"
    }
  }
}
