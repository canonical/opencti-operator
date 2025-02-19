# OpenCTI Terraform module

This folder contains a base [Terraform][Terraform] module for the OpenCTI charm.

The module uses the [Terraform Juju provider][Terraform Juju provider] to model the charm
deployment onto any Kubernetes environment managed by [Juju][Juju].

The base module is not intended to be deployed in separation (it is possible though), but should
rather serve as a building block for higher level modules.

## Module structure

- **main.tf** - Defines the Juju application to be deployed.
- **variables.tf** - Allows customization of the deployment. Except for exposing the deployment
  options (Juju model name, channel or application name) also models the charm configuration.
- **output.tf** - Responsible for integrating the module with other Terraform modules, primarily
  by defining potential integration endpoints (charm integrations), but also by exposing
  the application name.
- **versions.tf** - Defines the Terraform provider version.
- 
## Using opencti base module in higher level modules

If you want to use `opencti` base module as part of your Terraform module, import it
like shown below:

```text
data "juju_model" "my_model" {
  name = var.model
}

module "amf" {
  source = "git::https://github.com/canonical/opencti-operator//terraform"
  
  model = juju_model.my_model.name
  (Customize configuration variables here if needed)
}
```

Create integrations, for instance:

```text
resource "juju_integration" "amf-nrf" {
  model = juju_model.my_model.name
  application {
    name     = module.opencti.app_name
    endpoint = module.opencti.requires.logging
  }
  application {
    name     = "loki-k8s"
    endpoint = "logging"
  }
}
```

The complete list of available integrations can be found [here][opencti-integrations].

[Terraform]: https://www.terraform.io/
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
[opencti-integrations]: https://charmhub.io/opencti/integrations
