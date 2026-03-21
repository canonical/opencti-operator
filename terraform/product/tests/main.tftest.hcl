# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

provider "juju" {
  alias = "opencti_db"
}

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  command = plan

  variables {
    model_uuid    = run.setup_tests.model_uuid
    db_model_uuid = run.setup_tests.db_model_uuid
    model_user    = run.setup_tests.model_user
    db_model_user = run.setup_tests.db_model_user
    opencti = {
      channel = "latest/edge"
      # renovate: depName="opencti"
      revision = 83
    }
    opensearch = {
      channel = "2/edge"
      # renovate: depName="opensearch"
      revision = 337
    }
    self_signed_certificates = {
      channel = "latest/edge"
      # renovate: depName="self-signed-certificates"
      revision = 601
    }
    rabbitmq_server = {
      channel = "3.9/edge"
      # renovate: depName="rabbitmq-server"
      revision = 190
    }
    redis_k8s = {
      channel = "latest/edge"
      # renovate: depName="redis-k8s"
      revision = 42
    }
    s3_integrator = {
      channel = "latest/edge"
      # renovate: depName="s3-integrator"
      revision = 188
    }
    s3_integrator_opensearch = {
      channel = "latest/edge"
      # renovate: depName="s3-integrator"
      revision = 188
    }
    sysconfig = {
      channel = "latest/edge"
      # renovate: depName="sysconfig"
      revision = 158
    }
  }

  assert {
    condition     = output.app_name == "opencti"
    error_message = "opencti app_name did not match expected"
  }
}
