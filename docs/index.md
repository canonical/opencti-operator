---
myst:
  html_meta:
    "description lang=en": "A Juju charm deploying and managing OpenCTI."
---
# OpenCTI operator

The OpenCTI operator is an open-source software operator that deploys and operates OpenCTI on Juju.

This charm simplifies the configuration and maintenance of OpenCTI system and 
commonly used OpenCTI connectors across a range of environments, enabling users
to collect, correlate, and leverage threat data at strategic, operational and 
tactical levels.

The OpenCTI charm allows for deployment on many different Kubernetes platforms, from 
[Canonical Kubernetes](https://ubuntu.com/kubernetes) to public cloud Kubernetes offerings.

## In this documentation

```{list-table}
   :header-rows: 0
   :widths: 15 30

* - **Get started**
  - [Deploy OpenCTI for the first time](tutorial/index.md)
* - **Operations**
  - [Create a user account](how-to/account.md) | [Upgrade](how-to/upgrade.md) | [Back up](how-to/backup.md) | [Redeploy](how-to/redeploy.md)
* - **Observability**
  - [Integrate with COS](how-to/observability.md) | [Observability reference](reference/observability.md)
* - **Reference**
  - [Actions](reference/actions.md) | [Configurations](reference/configurations.md) | [Integrations](reference/integrations.md)
* - **Architecture**
  - [Charm architecture](reference/charm-architecture.md)
```

## How this documentation is organized

This documentation uses the
[Diátaxis documentation structure](https://diataxis.fr/).

* The [Tutorial](tutorial/index.md) takes you step-by-step through a first deployment of the OpenCTI charm.
* The [How-to guides](how-to/index.md) cover practical tasks for configuring, integrating, and maintaining your OpenCTI deployment.
* The [Reference](reference/index.md) provides technical reference for the OpenCTI operator.

## Project and community

The OpenCTI operator is a member of the Ubuntu family. It's an open-source project that warmly welcomes community 
projects, contributions, suggestions, fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/docs/ethos/code-of-conduct)
-- [File a bug](https://github.com/canonical/opencti-operator/issues)
- Get support through the [Discourse forum](https://discourse.charmhub.io/)
- Join our [online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

[Thinking about using the OpenCTI operator for your next project?
[Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

```{toctree}
:hidden:
:maxdepth: 1
Tutorial <tutorial/index.md>
How-to guides <how-to/index.md>
Reference <reference/index.md>
```
