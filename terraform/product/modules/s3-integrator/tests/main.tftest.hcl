# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

mock_provider "juju" {}

run "basic_deploy" {
  variables {
    model_uuid = "00000000-0000-0000-0000-000000000000"
  }

  assert {
    condition     = output.app_name == "s3-integrator"
    error_message = "s3-integrator app_name did not match expected"
  }

  assert {
    condition     = output.application.name == "s3-integrator"
    error_message = "s3-integrator application output did not match expected"
  }

  assert {
    condition     = output.provides.s3_credentials.endpoint == "s3-credentials"
    error_message = "s3-integrator provides.s3_credentials endpoint did not match expected"
  }
}
