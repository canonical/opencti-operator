# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model" {
  description = "Reference to the k8s Juju model to deploy application to."
  type        = string
}

variable "db_model" {
  description = "Reference to the VM Juju model to deploy database charms to."
  type        = string
}

variable "model_user" {
  description = "Juju user used for deploying the application."
  type        = string
}

variable "db_model_user" {
  description = "Juju user used for deploying database charms."
  type        = string
}

variable "opencti" {
  type = object({
    app_name    = optional(string, "opencti")
    channel     = optional(string, "latest/edge")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@24.04")
    units       = optional(number, 1)
  })
}

variable "opensearch" {
  type = object({
    app_name    = optional(string, "opensearch")
    channel     = optional(string, "2/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@22.04")
    units       = optional(number, 3)
  })
}

variable "self_signed_certificates" {
  type = object({
    app_name    = optional(string, "self-signed-certificates")
    channel     = optional(string, "latest/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@22.04")
    units       = optional(number, 3)
  })
}

variable "rabbitmq_server" {
  type = object({
    app_name    = optional(string, "rabbitmq-server")
    channel     = optional(string, "3.9/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@22.04")
    units       = optional(number, 1)
  })

  validation {
    condition     = var.rabbitmq_server.units == 1
    error_message = "OpenCTI doesn't support multi-unit RabbitMQ charm deployment"
  }
}

variable "redis_k8s" {
  type = object({
    app_name    = optional(string, "redis-k8s")
    channel     = optional(string, "latest/stable")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@22.04")
    units       = optional(number, 1)
    storage     = optional(map(string), {})
  })

  validation {
    condition     = var.redis_k8s.units == 1
    error_message = "OpenCTI Charm doesn't support multi-unit Redis deployment"
  }
}

variable "s3_integrator" {
  type = object({
    app_name    = optional(string, "s3-integrator")
    channel     = optional(string, "latest/edge")
    config      = optional(map(string), {})
    constraints = optional(string, "arch=amd64")
    revision    = optional(number)
    base        = optional(string, "ubuntu@22.04")
    units       = optional(number, 1)
  })
}

variable "s3_integrator_opensearch" {
  type = object({
    storage_type = optional(string, "s3")
    channel      = optional(string, "latest/edge")
    config       = optional(map(string), {})
    constraints  = optional(string, "arch=amd64")
    revision     = optional(number)
    base         = optional(string, "ubuntu@22.04")
    units        = optional(number, 1)
  })
}

variable "sysconfig" {
  type = object({
    app_name = optional(string, "sysconfig")
    channel  = optional(string, "latest/stable")
    revision = optional(number)
  })
}
