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

A [Juju](https://juju.is/) [charm](https://canonical-juju.readthedocs-hosted.com/en/3.6/user/reference/charm/)
for deploying and managing the [OpenCTI](https://filigran.io/solutions/open-cti/)
open source threat intelligence platform in your systems.

This charm simplifies the configuration and maintenance of OpenCTI system and
commonly used OpenCTI connectors across a range of environments, enabling users
to collect, correlate, and leverage threat data at strategic, operational and
tactical levels.

For information about how to deploy, integrate, and manage this charm, see the
Official [OpenCTI Charm Documentation](https://charmhub.io/opencti).

## Get started

See our [tutorial](docs/tutorial/index.md)

## Integrations

The `opencti-connector` integration integrates the OpenCTI charm and OpenCTI
connector charms. OpenCTI connectors are add-ons used by OpenCTI for platform
integration with other tools and applications. The OpenCTI connector
charms help with the deployment, configuration, and management of OpenCTI
connectors.

Existing OpenCTI connector charms can be found in the [connectors directory](connectors).

Deploy and integrate an OpenCTI connector charm with:

```bash
juju deploy opencti-export-file-stix-connector --channel latest/edge
juju integrate opencti opencti-export-file-stix-connector
```

## Learn more

* [OpenCTI charm on Charmhub](https://charmhub.io/opencti)
* [Official webpage](https://filigran.io/solutions/open-cti/)
* [Troubleshooting](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

## Project and community

* [Issues](https://github.com/canonical/opencti-operator/issues)
* [Contributing](https://charmhub.io/opencti/docs/how-to-contribute)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
