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
      revision = 138
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
      revision = 291
    }
    valkey = {}
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

  assert {
    condition     = module.valkey.app_name == "valkey"
    error_message = "valkey app_name did not match expected"
  }
}

run "offers_have_no_admin_grant_by_default" {
  command = plan

  variables {
    model_uuid    = run.setup_tests.model_uuid
    db_model_uuid = run.setup_tests.db_model_uuid
    model_user    = run.setup_tests.model_user
    db_model_user = run.setup_tests.db_model_user
    opencti = {
      channel = "latest/edge"
      # renovate: depName="opencti"
      revision = 138
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
      revision = 291
    }
    valkey = {}
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
    condition     = juju_access_offer.opensearch.admin == null
    error_message = "opensearch offer must not grant admin access by default"
  }

  assert {
    condition     = juju_access_offer.rabbitmq_server.admin == null
    error_message = "rabbitmq_server offer must not grant admin access by default"
  }
}

run "offers_grant_admin_to_offer_admin_users" {
  command = plan

  variables {
    model_uuid        = run.setup_tests.model_uuid
    db_model_uuid     = run.setup_tests.db_model_uuid
    model_user        = run.setup_tests.model_user
    db_model_user     = run.setup_tests.db_model_user
    offer_admin_users = ["someuser"]
    opencti = {
      channel = "latest/edge"
      # renovate: depName="opencti"
      revision = 138
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
      revision = 291
    }
    valkey = {}
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
    condition     = juju_access_offer.opensearch.admin == toset(["someuser"])
    error_message = "opensearch offer admin users did not match expected"
  }

  assert {
    condition     = juju_access_offer.rabbitmq_server.admin == toset(["someuser"])
    error_message = "rabbitmq_server offer admin users did not match expected"
  }
}
