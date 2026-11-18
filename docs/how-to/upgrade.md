# How to upgrade the OpenCTI charm

Use the [`juju refresh`](https://canonical.com/juju/docs/juju-cli/3.6/reference/juju-cli/list-of-juju-cli-commands/refresh/) 
command to upgrade the OpenCTI charm. No additional operations are required for
the upgrade process.

## Upgrade the Terraform product module

The product module deploys OpenSearch with the OpenSearch machine module, which requires
the Juju Terraform provider `~> 2.0`. Before applying the new module version:

- Update the Juju provider to `~> 2.0`.
- The existing certificates provider and backup integrator are kept: Terraform moves their
  state to the new module instead of recreating them.
- The optional OpenSearch Dashboards, Grafana agent and data integrator applications that
  the previous module deployed are no longer deployed, so Terraform destroys them.
- Set `s3_secret_uri` instead of `credentials` in `s3_integrator_opensearch.config`.
