<!--
Avoid using this README file for information that is maintained or published elsewhere, e.g.:

* metadata.yaml > published on Charmhub
* documentation > published on (or linked to from) Charmhub
* detailed contribution guide > documentation or CONTRIBUTING.md

Use links instead.
-->

<!-- vale Canonical.007-Headings-sentence-case = NO -->
# OpenCTI operator
<!-- vale Canonical.007-Headings-sentence-case = YES -->

[![CharmHub Badge](https://charmhub.io/opencti/badge.svg)](https://charmhub.io/opencti)
[![Publish to edge](https://github.com/canonical/opencti-operator/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/opencti-operator/actions/workflows/publish_charm.yaml)
[![Promote charm](https://github.com/canonical/opencti-operator/actions/workflows/promote_charm.yaml/badge.svg)](https://github.com/canonical/opencti-operator/actions/workflows/promote_charm.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

A [Juju](https://juju.is/) [charm](https://canonical.com/juju/docs/juju-cli/3.6/reference/charm/)
for deploying and managing the [OpenCTI](https://filigran.io/solutions/open-cti/)
open source threat intelligence platform in your systems.

This charm simplifies the configuration and maintenance of OpenCTI system and
commonly used OpenCTI connectors across a range of environments, enabling users
to collect, correlate, and leverage threat data at strategic, operational and
tactical levels.

This repository is a monorepo for Charmed OpenCTI: it contains the main OpenCTI Juju charm, 
OpenCTI connector charms, and Terraform modules for deploying the charm and a product-level OpenCTI bundle.

For information about how to deploy, integrate, and manage this charm, see the
Official [OpenCTI Charm Documentation](https://charmhub.io/opencti).

## Repository layout

```
src/                       # Main OpenCTI charm source code

lib/                       # Charm libraries used by the main charm and tests

connectors/                # 22 OpenCTI connector charms; one connector charm per subdirectory

connector-template/        # Template used for OpenCTI connector charm scaffolding

opencti_rock/              # Rockcraft packaging for the OpenCTI workload image

docs/                      # Product documentation

terraform/
  charm/                   # Base Terraform module for deploying the OpenCTI charm
  product/                 # Product Terraform module for OpenCTI with dependencies

tests/                     # Unit, integration, and repository tests

scripts/                   # Repository maintenance and helper scripts
```

## Components

This repository is a monorepo for Charmed OpenCTI, containing the main OpenCTI charm, 22 OpenCTI connector charms, and Terraform modules.

| Component | Path | Role |
| --- | --- | --- |
| `opencti` | `charmcraft.yaml`, `src/` | The main charm for deploying and managing the OpenCTI open source threat intelligence platform. |
| OpenCTI connector charms | `connectors/` | 22 connector charm subprojects. Connectors are add-ons used by OpenCTI for platform integration with other tools and applications; charm names follow the `opencti-<connector-name>-connector` pattern (for example, `connectors/export_file_stix/` builds the `opencti-export-file-stix-connector` charm). |
| Terraform modules | `terraform/charm/`, `terraform/product/` | The base Terraform module for the OpenCTI charm (`terraform/charm/`) and the product-level module for deploying OpenCTI with its dependencies (`terraform/product/`). |

The [available OpenCTI connector charms](connectors) are:

* `connectors/abuseipdb_ipblacklist/`
* `connectors/alienvault/`
* `connectors/cisa_kev/`
* `connectors/crowdstrike/`
* `connectors/cyber_campaign/`
* `connectors/export_file_csv/`
* `connectors/export_file_stix/`
* `connectors/export_file_txt/`
* `connectors/import_document/`
* `connectors/import_file_stix/`
* `connectors/ipinfo/`
* `connectors/malwarebazaar/`
* `connectors/misp_feed/`
* `connectors/mitre/`
* `connectors/nti/`
* `connectors/sekoia/`
* `connectors/urlhaus/`
* `connectors/urlscan/`
* `connectors/urlscan_enrichment/`
* `connectors/virustotal_livehunt/`
* `connectors/vxvault/`
* `connectors/woap/`

## Get started

See our [tutorial](docs/tutorial/index.md).

## Integrations

The [available OpenCTI connector charms](connectors) can be found in the connectors directory.

Deploy and integrate an OpenCTI connector charm with:

```bash
juju deploy opencti-export-file-stix-connector --channel latest/edge
juju integrate opencti opencti-export-file-stix-connector
```

## Documentation

Our documentation is stored in the `docs` directory and
can be viewed at https://charmhub.io/opencti.
It is hosted on the [Charmhub forum](https://discourse.charmhub.io/)
to enable easy collaboration.

You may open a pull request with your documentation changes, or you can
[file a bug](https://github.com/canonical/opencti-operator/issues) to
provide constructive feedback or suggestions.

GitHub runs automatic checks on the documentation to verify links and style guide
compliance.

You can (and should) run the same checks locally:

```bash
make lychee
make vale
```

## Project and community

* [Issues](https://github.com/canonical/opencti-operator/issues)
* [Contributing](https://charmhub.io/opencti/docs/how-to-contribute)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

## Licensing and trademark

See [`LICENSE`](LICENSE).
