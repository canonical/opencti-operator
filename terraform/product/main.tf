# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

data "juju_model" "opencti" {
  name = var.model
}

data "juju_model" "opencti_db" {
  name = var.db_model

  provider = juju.opencti_db
}

module "opencti" {
  source      = "../charm"
  app_name    = var.opencti.app_name
  channel     = var.opencti.channel
  config      = var.opencti.config
  constraints = var.opencti.constraints
  model       = data.juju_model.opencti.name
  revision    = var.opencti.revision
  base        = var.opencti.base
  units       = var.opencti.units
}

module "opensearch" {
  source = "git::https://github.com/canonical/opensearch-operator//terraform/product/simple_deployment?ref=2/edge"
  opensearch = {
    app_name    = var.opensearch.app_name
    channel     = var.opensearch.channel
    config      = var.opensearch.config
    constraints = var.opensearch.constraints
    model       = data.juju_model.opencti_db.name
    revision    = var.opensearch.revision
    base        = var.opensearch.base
    units       = var.opensearch.units
  }
  self-signed-certificates = var.self_signed_certificates
  backups-integrator       = var.s3_integrator_opensearch

  providers = {
    juju = juju.opencti_db
  }
}

module "rabbitmq_server" {
  source      = "./modules/rabbitmq-server"
  app_name    = var.rabbitmq_server.app_name
  channel     = var.rabbitmq_server.channel
  config      = var.rabbitmq_server.config
  constraints = var.rabbitmq_server.constraints
  model       = data.juju_model.opencti_db.name
  revision    = var.rabbitmq_server.revision
  base        = var.rabbitmq_server.base
  units       = var.rabbitmq_server.units

  providers = {
    juju = juju.opencti_db
  }
}

module "redis_k8s" {
  source      = "./modules/redis-k8s"
  app_name    = var.redis_k8s.app_name
  channel     = var.redis_k8s.channel
  config      = var.redis_k8s.config
  constraints = var.redis_k8s.constraints
  model       = data.juju_model.opencti.name
  revision    = var.redis_k8s.revision
  base        = var.redis_k8s.base
  units       = var.redis_k8s.units
  storage     = var.redis_k8s.storage
}

module "s3_integrator" {
  source      = "./modules/s3-integrator"
  app_name    = var.s3_integrator.app_name
  channel     = var.s3_integrator.channel
  config      = var.s3_integrator.config
  constraints = var.s3_integrator.constraints
  model       = data.juju_model.opencti.name
  revision    = var.s3_integrator.revision
  base        = var.s3_integrator.base
  units       = var.s3_integrator.units
}


resource "juju_access_offer" "opensearch" {
  offer_url = juju_offer.opensearch.url
  admin     = [var.db_model_user]
  consume   = [var.model_user]

  provider = juju.opencti_db
}

resource "juju_access_offer" "rabbitmq_server" {
  offer_url = juju_offer.rabbitmq_server.url
  admin     = [var.db_model_user]
  consume   = [var.model_user]

  provider = juju.opencti_db
}

resource "juju_integration" "amqp" {
  model = data.juju_model.opencti.name

  application {
    name     = module.opencti.app_name
    endpoint = module.opencti.requires.amqp
  }

  application {
    offer_url = juju_offer.rabbitmq_server.url
  }
}

resource "juju_integration" "opensearch_client" {
  model = data.juju_model.opencti.name

  application {
    name     = module.opencti.app_name
    endpoint = module.opencti.requires.opensearch_client
  }

  application {
    offer_url = juju_offer.opensearch.url
  }
}

resource "juju_integration" "redis" {
  model = data.juju_model.opencti.name

  application {
    name     = module.opencti.app_name
    endpoint = module.opencti.requires.redis
  }

  application {
    name     = module.redis_k8s.app_name
    endpoint = module.redis_k8s.provides.redis
  }
}

resource "juju_integration" "s3" {
  model = data.juju_model.opencti.name

  application {
    name     = module.opencti.app_name
    endpoint = module.opencti.requires.s3
  }

  application {
    name     = module.s3_integrator.app_name
    endpoint = module.s3_integrator.provides.s3_credentials
  }
}

resource "juju_offer" "opensearch" {
  model            = data.juju_model.opencti_db.name
  application_name = module.opensearch.app_names.opensearch
  endpoints        = [module.opensearch.provides.opensearch_client]

  provider = juju.opencti_db
}

resource "juju_offer" "rabbitmq_server" {
  model            = data.juju_model.opencti_db.name
  application_name = module.rabbitmq_server.app_name
  endpoints        = [module.rabbitmq_server.provides.amqp]

  provider = juju.opencti_db
}


resource "juju_integration" "s3_opensearch" {
  model = data.juju_model.opencti_db.name

  application {
    name     = module.opensearch.app_names.opensearch
    endpoint = module.opensearch.requires.s3_credentials
  }

  application {
    name     = module.s3_integrator_opensearch.app_name
    endpoint = module.s3_integrator_opensearch.provides.s3_credentials
  }

  provider = juju.opencti_db
}

resource "juju_application" "sysconfig" {
  name  = var.sysconfig.app_name
  model = data.juju_model.opencti_db.name

  charm {
    name     = "sysconfig"
    revision = var.sysconfig.revision
    channel  = var.sysconfig.channel
  }

  config = {
    sysctl = "{vm.max_map_count: 262144, vm.swappiness: 0, net.ipv4.tcp_retries2: 5, fs.file-max: 1048576}"
  }

  provider = juju.opencti_db
}

resource "juju_integration" "opensearch_sysconfig" {
  model = data.juju_model.opencti_db.name

  application {
    name     = module.opensearch.app_names.opensearch
    endpoint = "juju-info"
  }
  application {
    name     = juju_application.sysconfig.name
    endpoint = "juju-info"
  }

  provider = juju.opencti_db
}
