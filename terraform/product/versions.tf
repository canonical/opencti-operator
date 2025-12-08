# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

terraform {
  required_providers {
    juju = {
      source                = "juju/juju"
      version               = "~> 1.0"
      configuration_aliases = [juju.opencti_db]
    }
  }
  required_version = "~> 1.6"
}
