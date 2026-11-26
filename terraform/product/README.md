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
- **terraform.tf** - Defines the Terraform provider.

[Terraform]: https://www.terraform.io/
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
[OpenCTI charm]: https://charmhub.io/opencti

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.12 |
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | ~> 2.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | ~> 2.0 |
| <a name="provider_juju.opencti_db"></a> [juju.opencti\_db](#provider\_juju.opencti\_db) | ~> 2.0 |
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_opencti"></a> [opencti](#module\_opencti) | ../charm | n/a |
| <a name="module_opensearch"></a> [opensearch](#module\_opensearch) | git::https://github.com/canonical/opensearch-operator//terraform/machine/product/simple_deployment | opensearch/rev405&depth=1 |
| <a name="module_rabbitmq_server"></a> [rabbitmq\_server](#module\_rabbitmq\_server) | ./modules/rabbitmq-server | n/a |
| <a name="module_s3_integrator"></a> [s3\_integrator](#module\_s3\_integrator) | ./modules/s3-integrator | n/a |
| <a name="module_valkey"></a> [valkey](#module\_valkey) | git::https://github.com/canonical/valkey-operator.git//terraform/charm | 9/edge |

## Resources

| Name | Type |
|------|------|
| [juju_access_offer.opensearch](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/access_offer) | resource |
| [juju_access_offer.rabbitmq_server](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/access_offer) | resource |
| [juju_application.sysconfig](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_integration.amqp](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.ingress](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.logging](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.opensearch_client](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.opensearch_sysconfig](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.s3](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.valkey](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_offer.opensearch](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/offer) | resource |
| [juju_offer.rabbitmq_server](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/offer) | resource |
| [terraform_data.deployed_at](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/resources/data) | resource |
| [juju_model.opencti](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |
| [juju_model.opencti_db](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_azure_storage_secret_uri"></a> [azure\_storage\_secret\_uri](#input\_azure\_storage\_secret\_uri) | URI of an existing Juju secret that holds the Azure Storage account key of the OpenSearch backup integrator. | `string` | `null` | no |
| <a name="input_db_model_user"></a> [db\_model\_user](#input\_db\_model\_user) | Juju user to grant admin access to the OpenSearch and RabbitMQ offers. Leave unset when the user that applies the module created the offers, as it already has admin access. | `string` | `null` | no |
| <a name="input_db_model_uuid"></a> [db\_model\_uuid](#input\_db\_model\_uuid) | Reference to the VM Juju model to deploy database charms to. | `string` | n/a | yes |
| <a name="input_gcs_secret_uri"></a> [gcs\_secret\_uri](#input\_gcs\_secret\_uri) | URI of an existing Juju secret that holds the GCS credentials of the OpenSearch backup integrator. | `string` | `null` | no |
| <a name="input_ingress"></a> [ingress](#input\_ingress) | Optional ingress endpoint or cross-model offer to integrate opencti with. When unset, opencti's ingress relation is left unwired. | <pre>object({<br/>    endpoint = optional(string)<br/>    kind     = string<br/>    name     = optional(string)<br/>    url      = optional(string)<br/>  })</pre> | `null` | no |
| <a name="input_logging"></a> [logging](#input\_logging) | Optional logging endpoint or cross-model offer to integrate opencti with. When unset, opencti's logging relation is left unwired. | <pre>object({<br/>    endpoint = optional(string)<br/>    kind     = string<br/>    name     = optional(string)<br/>    url      = optional(string)<br/>  })</pre> | `null` | no |
| <a name="input_metadata_version"></a> [metadata\_version](#input\_metadata\_version) | Version string reported in the product module 'metadata' output. | `string` | `"1.0.0"` | no |
| <a name="input_model_user"></a> [model\_user](#input\_model\_user) | Juju user used for deploying the application. | `string` | n/a | yes |
| <a name="input_model_uuid"></a> [model\_uuid](#input\_model\_uuid) | Reference to the k8s Juju model to deploy application to. | `string` | n/a | yes |
| <a name="input_opencti"></a> [opencti](#input\_opencti) | OpenCTI charm settings. When channel is unset it defaults to latest/<risk>. | <pre>object({<br/>    app_name    = optional(string, "opencti")<br/>    channel     = optional(string)<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@24.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_opensearch"></a> [opensearch](#input\_opensearch) | n/a | <pre>object({<br/>    app_name    = optional(string, "opensearch")<br/>    channel     = optional(string, "2/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 3)<br/>  })</pre> | n/a | yes |
| <a name="input_rabbitmq_server"></a> [rabbitmq\_server](#input\_rabbitmq\_server) | n/a | <pre>object({<br/>    app_name    = optional(string, "rabbitmq-server")<br/>    channel     = optional(string, "3.9/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_redis_k8s"></a> [redis\_k8s](#input\_redis\_k8s) | Removed. OpenCTI now uses Valkey, set the valkey variable instead. | `any` | `null` | no |
| <a name="input_risk"></a> [risk](#input\_risk) | Risk level of the bundled components. It sets the default channel (latest/<risk>) of the opencti, s3\_integrator and s3\_integrator\_opensearch charms; an explicit channel on those variables takes precedence. Other charms track a fixed channel. | `string` | `"edge"` | no |
| <a name="input_s3_integrator"></a> [s3\_integrator](#input\_s3\_integrator) | S3 integrator charm settings. When channel is unset it defaults to latest/<risk>. | <pre>object({<br/>    app_name    = optional(string, "s3-integrator")<br/>    channel     = optional(string)<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_s3_integrator_opensearch"></a> [s3\_integrator\_opensearch](#input\_s3\_integrator\_opensearch) | S3 integrator charm settings for OpenSearch backups. When channel is unset it defaults to latest/<risk>. | <pre>object({<br/>    storage_type = optional(string, "s3")<br/>    channel      = optional(string)<br/>    config       = optional(map(string), {})<br/>    constraints  = optional(string, "arch=amd64")<br/>    revision     = optional(number)<br/>    base         = optional(string, "ubuntu@22.04")<br/>    units        = optional(number, 1)<br/>  })</pre> | n/a | yes |
| <a name="input_s3_secret_uri"></a> [s3\_secret\_uri](#input\_s3\_secret\_uri) | URI of an existing Juju secret that holds the S3 credentials of the OpenSearch backup integrator. | `string` | `null` | no |
| <a name="input_self_signed_certificates"></a> [self\_signed\_certificates](#input\_self\_signed\_certificates) | n/a | <pre>object({<br/>    app_name    = optional(string, "self-signed-certificates")<br/>    channel     = optional(string, "latest/stable")<br/>    config      = optional(map(string), {})<br/>    constraints = optional(string, "arch=amd64")<br/>    revision    = optional(number)<br/>    base        = optional(string, "ubuntu@22.04")<br/>    units       = optional(number, 3)<br/>  })</pre> | n/a | yes |
| <a name="input_sysconfig"></a> [sysconfig](#input\_sysconfig) | n/a | <pre>object({<br/>    app_name = optional(string, "sysconfig")<br/>    channel  = optional(string, "latest/stable")<br/>    revision = optional(number)<br/>  })</pre> | n/a | yes |
| <a name="input_valkey"></a> [valkey](#input\_valkey) | n/a | <pre>object({<br/>    app_name           = optional(string, "valkey")<br/>    channel            = optional(string, "9/edge")<br/>    config             = optional(map(string), {})<br/>    revision           = optional(number)<br/>    base               = optional(string, "ubuntu@26.04")<br/>    units              = optional(number, 1)<br/>    storage_directives = optional(map(string), {})<br/>  })</pre> | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_app_name"></a> [app\_name](#output\_app\_name) | Name of the deployed opencti application. |
| <a name="output_metadata"></a> [metadata](#output\_metadata) | Metadata describing this product deployment. |
| <a name="output_models"></a> [models](#output\_models) | Map of the deployed models and the components deployed in each of them. |
<!-- END_TF_DOCS -->