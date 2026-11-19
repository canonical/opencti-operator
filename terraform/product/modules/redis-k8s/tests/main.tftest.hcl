# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

mock_provider "juju" {}

run "basic_deploy" {
  variables {
    model_uuid = "00000000-0000-0000-0000-000000000000"
  }

  assert {
    condition     = output.app_name == "redis-k8s"
    error_message = "redis-k8s app_name did not match expected"
  }

  assert {
    condition     = output.application.name == "redis-k8s"
    error_message = "redis-k8s application output did not match expected"
  }

  assert {
    condition     = output.provides.redis.endpoint == "redis"
    error_message = "redis-k8s provides.redis endpoint did not match expected"
  }
}
