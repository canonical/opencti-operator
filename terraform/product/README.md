<!-- vale Canonical.007-Headings-sentence-case = NO -->
# SD-Core Terraform Modules
<!-- vale Canonical.007-Headings-sentence-case = YES -->

This project contains the [Terraform][Terraform] modules to deploy the 
[OpenCTI charm][OpenCTI charm] with its dependencies.

The modules use the [Terraform Juju provider][Terraform Juju provider] to model
the bundle deployment onto any Kubernetes environment managed by [Juju][Juju].

## Module structure

- **main.tf** - Defines the Juju application to be deployed.
- **variables.tf** - Allows customization of the deployment including Juju model name, charm's channel and configuration.
- **output.tf** - Responsible for integrating the module with other Terraform modules, primarily by defining potential integration endpoints (charm integrations).
- **versions.tf** - Defines the Terraform provider.

[Terraform]: https://www.terraform.io/
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
[OpenCTI charm]: https://charmhub.io/opencti

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.6.6 |
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | >= 1.1.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | >= 1.1.1 |
| <a name="provider_juju.opencti_db"></a> [juju.opencti\_db](#provider\_juju.opencti\_db) | >= 1.1.1 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_opencti"></a> [opencti](#module\_opencti) | ../charm | n/a |
| <a name="module_opensearch"></a> [opensearch](#module\_opensearch) | git::https://github.com/canonical/opensearch-operator//terraform/product/simple_deployment | rev315&depth=1 |
| <a name="module_rabbitmq_server"></a> [rabbitmq\_server](#module\_rabbitmq\_server) | ./modules/rabbitmq-server | n/a |
| <a name="module_redis_k8s"></a> [redis\_k8s](#module\_redis\_k8s) | ./modules/redis-k8s | n/a |
| <a name="module_s3_integrator"></a> [s3\_integrator](#module\_s3\_integrator) | ./modules/s3-integrator | n/a |

## Resources

| Name | Type |
|------|------|
| [juju_access_offer.opensearch](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/access_offer) | resource |
| [juju_access_offer.rabbitmq_server](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/access_offer) | resource |
| [juju_application.sysconfig](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_integration.amqp](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.opensearch_client](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.opensearch_sysconfig](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.redis](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.s3](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_offer.opensearch](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/offer) | resource |
| [juju_offer.rabbitmq_server](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/offer) | resource |
| [juju_model.opencti](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |
| [juju_model.opencti_db](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_db_model_user"></a> [db\_model\_user](#input\_db\_model\_user) | Juju user used for deploying database charms. | `string` | n/a | yes |
| <a name="input_db_model_uuid"></a> [db\_model\_uuid](#input\_db\_model\_uuid) | Reference to the VM Juju model to deploy database charms to. | `string` | n/a | yes |
| <a name="input_model_user"></a> [model\_user](#input\_model\_user) | Juju user used for deploying the application. | `string` | n/a | yes |
| <a name="input_model_uuid"></a> [model\_uuid](#input\_model\_uuid) | Reference to the k8s Juju model to deploy application to. | `string` | n/a | yes |
| <a name="input_opencti"></a> [opencti](#input\_opencti) | n/a | <pre>object({<br/>    app_name    = optional(string, "opencti")<br/>    channel     = optional(string, "latest/edge")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@24.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_opensearch"></a> [opensearch](#input\_opensearch) | n/a | <pre>object({<br/>    app_name    = optional(string, "opensearch")<br/>    channel     = optional(string, "2/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 3)<br/>  })</pre> | n/a | yes |
| <a name="input_rabbitmq_server"></a> [rabbitmq\_server](#input\_rabbitmq\_server) | n/a | <pre>object({<br/>    app_name    = optional(string, "rabbitmq-server")<br/>    channel     = optional(string, "3.9/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_redis_k8s"></a> [redis\_k8s](#input\_redis\_k8s) | n/a | <pre>object({<br/>    app_name    = optional(string, "redis-k8s")<br/>    channel     = optional(string, "latest/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 1)<br/>    storage     = optional(map(string), {})<br/>  })</pre> | n/a | yes |
| <a name="input_s3_integrator"></a> [s3\_integrator](#input\_s3\_integrator) | n/a | <pre>object({<br/>    app_name    = optional(string, "s3-integrator")<br/>    channel     = optional(string, "latest/edge")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_s3_integrator_opensearch"></a> [s3\_integrator\_opensearch](#input\_s3\_integrator\_opensearch) | n/a | <pre>object({<br/>    storage_type = optional(string, "s3")<br/>    channel      = optional(string, "latest/edge")<br/>    config       = optional(map(string), {})<br/>    constraints  = optional(string, "arch=amd64")<br/>    revision     = optional(number)<br/>    base         = optional(string, "ubuntu@22.04")<br/>    units        = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_self_signed_certificates"></a> [self\_signed\_certificates](#input\_self\_signed\_certificates) | n/a | <pre>object({<br/>    app_name    = optional(string, "self-signed-certificates")<br/>    channel     = optional(string, "latest/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 3)<br/>  })</pre> | n/a | yes |
| <a name="input_sysconfig"></a> [sysconfig](#input\_sysconfig) | n/a | <pre>object({<br/>    app_name = optional(string, "sysconfig")<br/>    channel  = optional(string, "latest/stable")<br/>    revision = optional(number)<br/>  })</pre> | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_app_name"></a> [app\_name](#output\_app\_name) | Name of the deployed opencti application. |
| <a name="output_provides"></a> [provides](#output\_provides) | n/a |
| <a name="output_requires"></a> [requires](#output\_requires) | n/a |
<!-- END_TF_DOCS -->