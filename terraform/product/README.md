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
