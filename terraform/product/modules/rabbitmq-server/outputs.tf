# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.rabbitmq_server.name
}

output "application" {
  description = "The deployed rabbitmq-server Juju application resource."
  value       = juju_application.rabbitmq_server
}

output "provides" {
  description = "Provides endpoints of the rabbitmq-server charm."
  value = {
    amqp = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "amqp"
    }
    grafana_dashboard = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "grafana-dashboard"
    }
    http = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "http"
    }
    nrpe_external_master = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "nrpe-external-master"
    }
    prometheus_rules = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "prometheus-rules"
    }
  }
}

output "requires" {
  description = "Requires endpoints of the rabbitmq-server charm."
  value = {
    hacluster = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "hacluster"
    }
    tls_certificates = {
      kind     = "endpoint"
      name     = juju_application.rabbitmq_server.name
      endpoint = "tls-certificates"
    }
  }
}
