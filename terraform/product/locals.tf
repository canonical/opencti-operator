# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

locals {
  opencti_channel                  = coalesce(var.opencti.channel, "latest/${var.risk}")
  s3_integrator_channel            = coalesce(var.s3_integrator.channel, "latest/${var.risk}")
  s3_integrator_opensearch_channel = coalesce(var.s3_integrator_opensearch.channel, "latest/${var.risk}")
}
