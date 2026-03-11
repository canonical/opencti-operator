# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

terraform {
  required_version = "~> 1.12"
  required_providers {
    juju = {
      version = "~> 1.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

resource "juju_model" "k8s_model" {
  name = "tf-testing-${formatdate("YYYYMMDDhhmmss", timestamp())}"
}

resource "juju_model" "db_model" {
  name = "tf-testing-db-${formatdate("YYYYMMDDhhmmss", timestamp())}"
}

output "model_uuid" {
  value = juju_model.k8s_model.uuid
}

output "db_model_uuid" {
  value = juju_model.db_model.uuid
}

output "model_user" {
  value = "admin"
}

output "db_model_user" {
  value = "admin"
}
