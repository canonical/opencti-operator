# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    channel    = "latest/edge"
    # renovate: depName="opencti"
    revision = 137
  }

  assert {
    condition     = output.app_name == "opencti"
    error_message = "opencti app_name did not match expected"
  }

  assert {
    condition     = output.application.name == "opencti"
    error_message = "opencti application output did not match expected"
  }

  assert {
    condition     = output.requires.valkey.endpoint == "valkey"
    error_message = "valkey endpoint did not match expected"
  }

  assert {
    condition     = output.requires.redis.endpoint == "redis"
    error_message = "redis endpoint did not match expected"
  }
}
