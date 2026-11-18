# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Keep resources of the previous OpenSearch Terraform module instead of recreating them.
moved {
  from = module.opensearch.module.opensearch.juju_application.self-signed-certificates["deployed"]
  to   = module.opensearch.juju_application.self_signed_certificates[0]
}
moved {
  from = module.opensearch.juju_application.backups-integrator
  to   = module.opensearch.juju_application.backups[0]
}
moved {
  from = module.opensearch.module.opensearch.juju_integration.tls-opensearch-same-model_integration["local"]
  to   = module.opensearch.juju_integration.this["tls_opensearch"]
}
moved {
  from = module.opensearch.juju_integration.backups_integrator-opensearch-integration
  to   = module.opensearch.juju_integration.this["backups_opensearch"]
}
