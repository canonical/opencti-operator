<!--
Avoid using this README file for information that is maintained or published elsewhere, e.g.:

* metadata.yaml > published on Charmhub
* documentation > published on (or linked to from) Charmhub
* detailed contribution guide > documentation or CONTRIBUTING.md

Use links instead.
-->
<!-- vale off -->
# OpenCTI operator
<!-- vale on -->

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
In this section, we will deploy the base OpenCTI charm.

You’ll need a workstation, e.g., a laptop, with sufficient resources to launch 
a virtual machine with 4 CPUs, 8 GB RAM, and 50 GB disk space.

### Set up
You can follow the tutorial [here](https://canonical-juju.readthedocs-hosted.com/en/latest/user/howto/manage-your-deployment/manage-your-deployment-environment/#manage-your-deployment-environment) 
to set up a test environment for Juju.

### Deploy databases on the VM model

First, deploy the OpenSearch and RabbitMQ databases on the VM model. Note that 
deploying the OpenSearch database requires you to configure certain kernel 
parameters on the host as required by the OpenSearch charm.
The [sysconfig charm](https://charmhub.io/sysconfig) will be used for this.

```bash

juju switch lxd:welcome-lxd

juju deploy self-signed-certificates
juju deploy opensearch --channel 2/stable --num-units 3
juju deploy sysconfig --channel latest/stable --config sysctl="{vm.max_map_count: 262144, vm.swappiness: 0, net.ipv4.tcp_retries2: 5, fs.file-max: 1048576}"
juju integrate sysconfig opensearch

juju deploy rabbitmq-server --channel 3.9/stable

juju integrate self-signed-certificates opensearch
```
### Create Juju offers
Next, we will create some [offers](https://canonical-juju.readthedocs-hosted.com/en/latest/user/reference/offer/)
for cross-model integrations.

```bash
juju offer opensearch:opensearch-client opensearch-client
juju offer rabbitmq-server:amqp amqp
```

### Deploy the OpenCTI charm
In the Kubernetes model, deploy the OpenCTI charm along with the rest of 
dependencies.

```bash
juju switch lxd:welcome-microk8s

juju deploy minio --channel ckf-1.9/stable --config access-key=minioadmin --config secret-key=minioadmin
juju deploy s3-integrator --config "endpoint=http://minio-endpoints.welcome-microk8s.svc.cluster.local:9000" --config bucket=opencti
juju deploy redis-k8s --channel latest/edge
juju deploy nginx-ingress-integrator --trust --revision 109 --channel latest/edge --config path-routes=/ --config service-hostname=opencti.local
juju deploy opencti --channel latest/edge
```
### Configure and integrate
Configure minio to provide a S3 compatible storage for the OpenCTI charm.

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_ENDPOINT_URL=http://$(juju status --format=json | jq -r '.applications.minio.units."minio/0".address'):9000
aws s3 mb s3://opencti
juju run s3-integrator/0 sync-s3-credentials --string-args access-key=minioadmin secret-key=minioadmin
```

Integrate the OpenCTI charm with all its dependencies.

```bash
juju integrate opencti lxd:admin/welcome-lxd.opensearch-client
juju integrate opencti lxd:admin/welcome-lxd.amqp
juju integrate opencti redis-k8s
juju integrate opencti s3-integrator
juju integrate opencti nginx-ingress-integrator
```
### Create an admin user and access OpenCTI
Create the initial admin user for the OpenCTI deployment and provide it to the 
OpenCTI charm.

```bash
OPENCTI_ADMIN_USER_SECRET_ID=$(juju add-secret opencti-admin-user email=admin@example.com password=test)
juju grant-secret opencti-admin-user opencti
juju config opencti admin-user=$OPENCTI_ADMIN_USER_SECRET_ID
```

When the OpenCTI charm has completed deployment and installation, you can 
access OpenCTI from a browser. First, we need to modify the `/etc/hosts` file 
to point the `opencti.local` domain to the IP address of the virtual machine.  
After that, we can access the OpenCTI instance in the browser using the address 
`http://opencti.local` and the test admin username `admin@example.com` and
password `test`.  

## Integrations

The `opencti-connector` integration integrates the OpenCTI charm and OpenCTI 
connector charms. OpenCTI connectors are add-ons used by OpenCTI for platform 
integration with other tools and applications. The OpenCTI connector 
charms help with the deployment, configuration, and management of OpenCTI 
connectors.

Existing OpenCTI connector charms can be found [here](connectors).

Deploy and integrate an OpenCTI connector charm with:

```bash
juju deploy opencti-export-file-stix-connector --channel latest/edge
juju integrate opencti opencti-export-file-stix-connector
```

## Learn more
* [Read more](https://charmhub.io/opencti)
* [Official webpage](https://filigran.io/solutions/open-cti/)
* [Troubleshooting](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

## Project and community
* [Issues](https://github.com/canonical/opencti-operator/issues)
* [Contributing](https://charmhub.io/opencti/docs/how-to-contribute)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
