# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

terraform {
  required_providers {
    juju = {
      source                = "juju/juju"
      version               = ">= 0.16.0"
      configuration_aliases = [juju.opencti_db]
    }
  }
}
