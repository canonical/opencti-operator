# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed opencti application."
  value       = module.opencti.app_name
}

output "metadata" {
  description = "Metadata describing this product deployment."
  value = {
    version     = var.metadata_version
    deployed_at = timestamp()
    updated_at  = timestamp()
  }
}

output "models" {
  description = "Map of the deployed models and the components deployed in each of them."
  value = {
    opencti = {
      model_uuid = data.juju_model.opencti.uuid
      components = {
        opencti       = module.opencti.application
        redis_k8s     = module.redis_k8s.application
        s3_integrator = module.s3_integrator.application
      }
    }
    opencti_db = {
      model_uuid = data.juju_model.opencti_db.uuid
      components = {
        rabbitmq_server = module.rabbitmq_server.application
        sysconfig       = juju_application.sysconfig
      }
    }
  }
}
