# OpenCTI Operator

## Build, Test, and Lint

```bash
# Format code
tox -e fmt

# Lint (black, isort, flake8, mypy, pylint, codespell, pydocstyle)
tox -e lint

# Static analysis (bandit)
tox -e static

# Unit tests (with coverage)
tox -e unit

# Run a single unit test
tox -e unit -- tests/unit/test_charm.py::test_pebble_plan

# Integration tests (requires a running Juju/K8s environment)
tox -e integration

# Run all basic checks
tox

# Build the charm
charmcraft pack

# Regenerate connector charms from the OpenCTI connector registry
tox -e generate-connectors
```

**Style:** 99-character line length, Google-style docstrings, `black` + `isort` for formatting.

## Architecture

This is a **Juju Kubernetes charm** for the OpenCTI threat intelligence platform, built with the [Ops framework](https://canonical.com/juju/docs/ops/latest/).

### Two-charm pattern

The repo contains two kinds of charms:

1. **Main charm** (`src/charm.py`) — `OpenCTICharm` manages the OpenCTI platform and workers inside a single K8s pod using [Pebble](https://ubuntu.com/docs/pebble/) as process supervisor. The pod has two containers: the `charm` container (Ops code) and the `opencti` container (platform + 3 worker processes).

2. **Connector charms** (`connectors/<name>/`) — Thin charms, each wrapping a single OpenCTI connector. They all subclass `OpenctiConnectorCharm` from `lib/charms/opencti/v0/opencti_connector.py` and declare a `connector_type` class attribute. They connect to the main charm via the `opencti-connector` relation.

### Connector generation

Connector charms are **code-generated** — do not edit them by hand. They are produced by `scripts/gen_connector_charm.py` using the Jinja2 templates in `connector-template/` (primarily `charmcraft.yaml.j2` and `src/charm.py.j2`). Re-run `tox -e generate-connectors` after modifying templates or adding a new connector.

### Key integrations (required)

| Relation name | Interface | Charm library used |
|---|---|---|
| `opensearch-client` | `opensearch_client` | `data_platform_libs.v0.data_interfaces` |
| `redis` | `redis` | `redis_k8s.v0.redis` |
| `amqp` | `rabbitmq` | `rabbitmq_k8s.v0.rabbitmq` |
| `s3` | `s3` | `data_platform_libs.v0.s3` |
| `ingress` | `ingress` | `traefik_k8s.v2.ingress` |

Optional integrations: `logging` (Loki), `metrics-endpoint` (Prometheus), `grafana-dashboard`.

### Secrets and peer relation

Shared secrets (admin token, health access key) are stored in a Juju secret attached to the `opencti-peer` peer relation. The leader unit creates the secret; other units read it. Constants controlling the secret field names are defined near the top of `src/charm.py`.

### OpenCTI client

`src/opencti.py` contains `OpenctiClient`, a thin GraphQL client (via `gql`) that the charm uses to manage OpenCTI users and groups after the platform is running. Connector charms get their own API token created through this client during relation setup.

## Key Conventions

### Charm event handling

All Juju events funnel into `OpenCTICharm._reconcile()`. The method follows a guard-clause style: each dependency check raises a typed exception (`MissingIntegration`, `MissingConfig`, `ContainerNotReady`, etc.) and the caller catches them to set the appropriate charm status.

### Unit testing with `StateBuilder`

Unit tests use `ops.testing` (Scenario-style). `tests/unit/state.py` provides a `StateBuilder` fluent builder for constructing `ops.testing.State` objects with pre-populated relations, configs, and secrets. Use it — do not build raw `State` dicts manually.

The `OpenctiClient` and `_is_platform_healthy` are always mocked in unit tests via `autouse` fixtures in `tests/unit/conftest.py`.

### Charm library versioning

Libraries under `lib/charms/` follow the `LIBAPI` / `LIBPATCH` versioning convention. When you bump a library, update `LIBPATCH` (or `LIBAPI` for breaking changes) before running `charmcraft publish-lib`.

### Copyright header

Every Python file must start with:
```python
# Copyright <year> Canonical Ltd.
# See LICENSE file for licensing details.
```

### Connector `connector_type` values

Valid values for `OpenctiConnectorCharm.connector_type`:
`EXTERNAL_IMPORT`, `INTERNAL_ENRICHMENT`, `INTERNAL_IMPORT_FILE`, `INTERNAL_EXPORT_FILE`, `STREAM`.

### Environment variables managed by the charm

The following env vars are always injected by the charm into connector containers and must **not** be exposed as charm config options: `OPENCTI_URL`, `OPENCTI_TOKEN`, `CONNECTOR_ID`, `CONNECTOR_NAME`.
