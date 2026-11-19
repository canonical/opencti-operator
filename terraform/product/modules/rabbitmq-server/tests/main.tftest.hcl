# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

mock_provider "juju" {}

run "basic_deploy" {
  variables {
    model_uuid = "00000000-0000-0000-0000-000000000000"
  }

  assert {
    condition     = output.app_name == "rabbitmq-server"
    error_message = "rabbitmq-server app_name did not match expected"
  }

  assert {
    condition     = output.application.name == "rabbitmq-server"
    error_message = "rabbitmq-server application output did not match expected"
  }

  assert {
    condition     = output.provides.amqp.endpoint == "amqp"
    error_message = "rabbitmq-server provides.amqp endpoint did not match expected"
  }
}
