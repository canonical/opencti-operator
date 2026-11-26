# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each revision is versioned by the date of the revision.

## 2026-11-26

### Changed

- Terraform: the `valkey` variable of the `terraform/product` module accepts an optional `storage_directives` map (for example `{ data = "20G" }`) to set the Valkey storage sizes. The default is unchanged.

## 2026-11-23

### Changed

- Terraform: `db_model_user` in the `terraform/product` module is now optional and `admin` access on the OpenSearch and RabbitMQ offers is granted to it only when it is set. With Juju provider 2.x, granting it to the user that created the offers failed with `user already has "admin" access or greater`, so stop setting it in that case.

## 2026-11-18

### Changed

- Migrated all Terraform modules (`terraform/charm`, `terraform/product` and
  its `rabbitmq-server`, `redis-k8s`, `s3-integrator` submodules) to the CC008
  Charm Terraform Standard: renamed `versions.tf` to `terraform.tf`, added
  a single shared `terraform/MAJOR_VERSION` file, normalized variable/output contracts, and added
  missing module tests.
- The `terraform/product` module's `requires`/`provides` outputs were replaced
  by new optional `ingress` and `logging` input variables, plus new mandatory
  `metadata` and `models` outputs.
- Charm module `base` and `constraints` variables now default to `null`
  instead of a concrete value; this only changes behavior for consumers
  invoking the charm modules standalone without an explicit value, since the
  product module always passes an explicit value.
- The `terraform/product` module's `risk` input (default `edge`) now sets the
  default channel (`latest/<risk>`) of the `opencti`, `s3_integrator` and
  `s3_integrator_opensearch` charms when no explicit channel is given.
  `metadata.deployed_at` is now persisted in state instead of changing on every
  apply.
- Terraform: the product module uses the OpenSearch machine module. All modules require the Juju provider `~> 2.0`, and `moved` blocks keep the existing certificates provider and backup integrator. The optional OpenSearch Dashboards, Grafana agent and data integrator applications are no longer deployed
- Terraform: bumped the major version of the Terraform modules to 2 because of the breaking changes above
- Terraform: added the `s3_secret_uri` variable for the OpenSearch backup integrator credentials
- Terraform: the product module deploys Valkey instead of `redis-k8s`. The `redis_k8s` variable was removed; see the Redis to Valkey migration guide
- Terraform: the charm module exposes the `valkey` endpoint
- Docs: document the `valkey` integration and add a Redis to Valkey migration guide

## 2026-11-16

### Fixed

- Upgrade TF OpenSearch product to rev349, which pins OpenSearch Dashboards to a tag instead of the floating `2/edge` branch (fixes `terraform init/validate` failures)

## 2026-11-12

### Changed

- Migrated the build, integration test and publish workflows to canonical/charm-ci

## 2026-06-25

### Added

- Added tutorial to the documentation set

## 2026-03-11

### Changed

- Upgraded OpenCTI to version 6.9.24
- Introduced terraform tests
- Now requires terraform 1.12

## 2026-02-03

### Changed

- Upgrade OpenCTI to version 6.9.15.

## 2026-01-22

### Changed

- Install ca-certificates in the OpenCTI rock.
- Cache peer secret content to improve performance.

## 2025-12-17

### Changed

- Upgrade TF OpenSearch product to rev315
- Moved charm-architecture.md from Explanation to Reference category.

## 2025-12-01

### Changed

- Pin the upstream TF OpenSearch product

## 2025-10-14

### Changed

- Use the upstream TF OpenSearch product

## 2025-09-23

### Changed

- Require ingresses without stripped path prefix.
- Add support for path prefixed URLs.
- Pass ingress URL in the relation data bag

### Changed

- Require ingresses with stripped path prefix.

## 2025-08-28

### Changed

- Updated the documentation workflow to be fully integrated with the Vale GitHub Action.

## 2025-08-26

### Changed

- Switched from MicroK8s to Canonical Kubernetes.

## 2025-08-25

### Changed

- Pin CI dependencies.

## 2025-08-20

### Changed

- Update Juju TF provider minimum version to 0.21.1.

## 2025-06-26

### Changed

- Enabled vale checks.

## 2025-03-04

### Changed

- Add the `sysconfig` charm with the appropriate parameters to automate the kernel settings changes.

### Added

- Changelog added for tracking changes.
