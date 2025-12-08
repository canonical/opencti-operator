# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "rabbitmq_server" {
  name       = var.app_name
  model_uuid = var.model_uuid
  units      = var.units

  charm {
    name     = "rabbitmq-server"
    channel  = var.channel
    revision = var.revision
    base     = var.base
  }

  config      = var.config
  constraints = var.constraints

  expose {}
}
