# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.rabbitmq_server.name
}

output "requires" {
  value = {
    hacluster        = "hacluster"
    tls_certificates = "tls-certificates"
  }
}

output "provides" {
  value = {
    grafana_dashboard    = "grafana-dashboard"
    http                 = "http"
    nrpe_external_master = "nrpe-external-master"
    prometheus_rules     = "prometheus-rules"
    amqp                 = "amqp"
  }
}