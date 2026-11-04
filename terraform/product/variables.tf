# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "db_model_user" {
  description = "Juju user used for deploying database charms."
  type        = string
}

variable "db_model_uuid" {
  description = "Reference to the VM Juju model to deploy database charms to."
  type        = string
}

variable "ingress" {
  description = "Optional ingress endpoint or cross-model offer to integrate opencti with. When unset, opencti's ingress relation is left unwired."
  type = object({
    endpoint = optional(string)
    kind     = string
    name     = optional(string)
    url      = optional(string)
  })
  default = null

  validation {
    condition     = var.ingress == null || contains(["endpoint", "offer"], var.ingress.kind)
    error_message = "ingress.kind must be either endpoint or offer."
  }

  validation {
    condition = var.ingress == null || (
      var.ingress.kind == "endpoint"
      ? var.ingress.name != null && var.ingress.endpoint != null && var.ingress.url == null
      : var.ingress.url != null && var.ingress.name == null && var.ingress.endpoint == null
    )
    error_message = "ingress endpoints require name and endpoint; ingress offers require url."
  }
}

variable "logging" {
  description = "Optional logging endpoint or cross-model offer to integrate opencti with. When unset, opencti's logging relation is left unwired."
  type = object({
    endpoint = optional(string)
    kind     = string
    name     = optional(string)
    url      = optional(string)
  })
  default = null

  validation {
    condition     = var.logging == null || contains(["endpoint", "offer"], var.logging.kind)
    error_message = "logging.kind must be either endpoint or offer."
  }

  validation {
    condition = var.logging == null || (
      var.logging.kind == "endpoint"
      ? var.logging.name != null && var.logging.endpoint != null && var.logging.url == null
      : var.logging.url != null && var.logging.name == null && var.logging.endpoint == null
    )
    error_message = "logging endpoints require name and endpoint; logging offers require url."
  }
}

variable "metadata_version" {
  description = "Version string reported in the product module 'metadata' output."
  type        = string
  default     = "1.0.0"
}

variable "model_user" {
  description = "Juju user used for deploying the application."
  type        = string
}

variable "model_uuid" {
  description = "Reference to the k8s Juju model to deploy application to."
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

# Risk currently only reflects the overall solution's intended release train in the
# metadata output; each bundled charm continues to pin its channel independently
# via its own variable.
# tflint-ignore: terraform_unused_declarations
variable "risk" {
  description = "Risk level controlling the channel risk of the bundled components."
  type        = string
  default     = "stable"
  nullable    = false

  validation {
    condition     = contains(["stable", "edge"], var.risk)
    error_message = "risk must be either \"stable\" or \"edge\"."
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

variable "sysconfig" {
  type = object({
    app_name = optional(string, "sysconfig")
    channel  = optional(string, "latest/stable")
    revision = optional(number)
  })
}
