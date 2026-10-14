# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.redis_k8s.name
}

output "application" {
  description = "The deployed redis-k8s Juju application resource."
  value       = juju_application.redis_k8s
}

output "provides" {
  description = "Provides endpoints of the redis-k8s charm."
  value = {
    redis = {
      kind     = "endpoint"
      name     = juju_application.redis_k8s.name
      endpoint = "redis"
    }
  }
}

output "requires" {
  description = "Requires endpoints of the redis-k8s charm."
  value       = {}
}
