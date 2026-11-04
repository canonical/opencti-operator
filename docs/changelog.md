# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each revision is versioned by the date of the revision.

## 2026-10-13

### Changed

- Migrated all Terraform modules (`terraform/charm`, `terraform/product` and
  its `rabbitmq-server`, `redis-k8s`, `s3-integrator` submodules) to the CC008
  Charm Terraform Standard: renamed `versions.tf` to `terraform.tf`, added
  `MAJOR_VERSION` files, normalized variable/output contracts, and added
  missing module tests.
- The `terraform/product` module's `requires`/`provides` outputs were replaced
  by new optional `ingress` and `logging` input variables, plus new mandatory
  `metadata` and `models` outputs.
- Charm module `base` and `constraints` variables now default to `null`
  instead of a concrete value; this only changes behavior for consumers
  invoking the charm modules standalone without an explicit value, since the
  product module always passes an explicit value.

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
