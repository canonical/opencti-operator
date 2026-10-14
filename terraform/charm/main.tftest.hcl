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
    revision = 123
  }

  assert {
    condition     = output.app_name == "opencti"
    error_message = "opencti app_name did not match expected"
  }

  assert {
    condition     = output.application.name == "opencti"
    error_message = "opencti application output did not match expected"
  }
}
