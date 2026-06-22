# Deploy OpenCTI for the first time

OpenCTI is an open-source cyber threat intelligence platform that enables
organisations to collect, correlate, and leverage threat data at strategic,
operational and tactical levels. This tutorial walks you through deploying
the OpenCTI charm with all its dependencies using Juju.

## What you'll do

- Set up two Juju models: one VM model (LXD) for databases and one Kubernetes
  model (MicroK8s) for the OpenCTI platform
- Deploy OpenSearch and RabbitMQ on the VM model
- Deploy OpenCTI and its Kubernetes dependencies (Redis, MinIO, NGINX ingress)
- Integrate the two models using Juju cross-model relations
- Create an admin user and access the OpenCTI platform from a browser

## What you'll need

You will need a working station with AMD64 architecture. Your
working station should have at least eight CPU cores, 16 GB of RAM, and 100 GB of
disk space.

> **Tip:** You can use Multipass to create an isolated environment by running:
> ```
> multipass launch 24.04 --name opencti-tutorial-vm --cpus 8 --memory 16G --disk 100G
> ```
> When using a Multipass VM, make sure to replace `127.0.0.1` IP addresses with
> the VM IP in steps that assume you're running locally. To get the IP address of
> the Multipass instance run `multipass info opencti-tutorial-vm`.

This tutorial requires the following software to be installed in your working
environment (preferably a Multipass VM):

- Juju 3.6+
- Canonical Kubernetes 1.32+
- LXD 5.21+

Use [Concierge](https://github.com/canonical/concierge) to set up Juju, LXD and
Canonical Kubernetes:

```shell
sudo snap install --classic concierge
sudo concierge prepare -p dev
```

Once the command succeeds, you have a working environment with Juju, LXD and
Kubernetes working. You can confirm by running `juju controllers` that should 
return both controllers:

```shell
Controller      Model    User   Access     Cloud/Region         Models  Nodes    HA  Version
concierge-k8s   testing  admin  superuser  k8s                       2      1     -  3.6.24  
concierge-lxd*  testing  admin  superuser  localhost/localhost       2      1  none  3.6.24  
```

Kubernetes must have an ingress controller enabled. Complete this step by running:

```shell
sudo k8s enable ingress
```

Additionally, this tutorial uses the AWS CLI to create an S3 bucket in MinIO.
Install it with:

```shell
sudo snap install aws-cli --classic
```

## Set up the tutorial models

Create a Juju model on the LXD controller for the database dependencies:

```shell
juju switch concierge-lxd
juju add-model opencti-databases
```

You can confirm with `juju status`:

```shell
Model              Controller     Cloud/Region         Version  SLA          Timestamp
opencti-databases  concierge-lxd  localhost/localhost  3.6.24   unsupported  17:22:42+02:00
```

Create a Juju model on the Kubernetes controller for the OpenCTI platform:

```
juju switch concierge-k8s
juju add-model opencti
```

## Deploy the databases

OpenCTI requires OpenSearch and RabbitMQ, which run best as machine charms on
LXD rather than on Kubernetes. Switch to the database model and deploy them:

```shell
juju switch concierge-lxd:opencti-databases
```

Deploy a self-signed certificate authority for securing OpenSearch:

```shell
juju deploy self-signed-certificates
```

You can check the progress with `juju status`:

```shell
Model              Controller     Cloud/Region         Version  SLA          Timestamp
opencti-databases  concierge-lxd  localhost/localhost  3.6.24   unsupported  17:25:35+02:00

App                       Version  Status  Scale  Charm                     Channel   Rev  Exposed  Message
self-signed-certificates           active      1  self-signed-certificates  1/stable  586  no       

Unit                         Workload  Agent      Machine  Public address  Ports  Message
self-signed-certificates/0*  active    executing  0        10.204.160.215         (start) 

Machine  State    Address         Inst id        Base          AZ                   Message
0        started  10.204.160.215  juju-3415cb-0  ubuntu@24.04  opencti-tutorial-vm  Running
```

Deploy a three-node OpenSearch cluster. OpenSearch requires specific kernel
parameters on the host machine. The `sysconfig` charm applies them
automatically:

```
juju deploy opensearch --channel 2/stable
juju deploy sysconfig --channel latest/stable \
  --config sysctl="{vm.max_map_count: 262144, vm.swappiness: 0, net.ipv4.tcp_retries2: 5, fs.file-max: 1048576}"
juju integrate sysconfig opensearch
juju integrate self-signed-certificates opensearch
```

Deploy RabbitMQ, which OpenCTI uses as a message queue:

```shell
juju deploy rabbitmq-server --channel 3.9/stable
```

Wait for all applications to become active before proceeding. You can monitor the progress
with `juju status --watch 2s` or just wait by using the following command:

```shell
juju wait-for application opensearch --query='status=="active"' --timeout 20m
```

## Create Juju offers

Create [cross-model offers](https://canonical.com/juju/docs/juju-cli/latest/reference/offer/)
so that the Kubernetes model can consume the database services:

```shell
juju offer opensearch:opensearch-client opensearch-client
juju offer rabbitmq-server:amqp amqp
```

## Deploy OpenCTI and its dependencies

Switch to the Kubernetes model and deploy the OpenCTI platform and its requirements:

```shell
juju switch concierge-k8s:opencti
```

Deploy MinIO as S3-compatible object storage for OpenCTI file attachments. The
`s3-integrator` charm then provides the S3 credentials to OpenCTI:

```shell
juju deploy minio --channel ckf-1.10/stable \
  --config access-key=minioadmin \
  --config secret-key=minioadmin
juju deploy s3-integrator \
  --config "endpoint=http://minio-endpoints.opencti.svc.cluster.local:9000" \
  --config bucket=opencti
```

It's expected for the `s3-integrator` to remain in `blocked` state. We will provide
it the required credentials later.

Deploy Redis, which OpenCTI uses for caching:

```shell
juju deploy redis-k8s --channel latest/edge
```

TODO
Deploy NGINX ingress integrator to expose the OpenCTI web interface:

```
juju deploy nginx-ingress-integrator --trust \
  --channel latest/edge \
  --config path-routes=/ \
  --config service-hostname=opencti.local
```

Deploy the OpenCTI charm itself:

```shell
juju deploy opencti --channel latest/edge
```

## Configure S3 storage

Before integrating, create the S3 bucket in MinIO. Retrieve the MinIO service
IP and create the bucket with the AWS CLI:

```shell
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_ENDPOINT_URL=http://$(juju status --format=json | jq -r '.applications.minio.units."minio/0".address'):9000
aws s3 mb s3://opencti
```

Sync the credentials to the `s3-integrator` charm:

```
juju run s3-integrator/0 sync-s3-credentials \
  --string-args access-key=minioadmin secret-key=minioadmin
```

The `s3-integrator` should now turn to `active`.

## Integrate the services

Integrate OpenCTI with all its dependencies, including the cross-model offers
from the LXD controller:

```
juju integrate opencti concierge-lxd:admin/opencti-databases.opensearch-client
juju integrate opencti concierge-lxd:admin/opencti-databases.amqp
juju integrate opencti redis-k8s
juju integrate opencti s3-integrator
juju integrate opencti nginx-ingress-integrator
```

## Configure the admin user

OpenCTI requires an initial admin account. Store the credentials securely as a
[Juju secret](https://canonical.com/juju/docs/juju-cli/latest/reference/secret/)
and provide the secret ID to the charm:

```shell
OPENCTI_ADMIN_SECRET_ID=$(juju add-secret opencti-admin-user email=admin@example.com password=changeme)
juju grant-secret opencti-admin-user opencti
juju config opencti admin-user=$OPENCTI_ADMIN_SECRET_ID
```

Replace `changeme` with a strong password of your choice.

Wait for OpenCTI to finish deploying:

```shell
juju wait-for application opencti --query='status=="active"' --timeout 20m
```

## Check the deployment

Run `juju status` to confirm that all applications are active:

```
juju status
```

The output should resemble:

```
Model   Controller          Cloud/Region        Version  SLA          Timestamp
opencti  concierge-k8s  microk8s/localhost  3.6.0    unsupported  ...

App                       Version  Status  Scale  Charm                     Channel      Rev  Address         Exposed  Message
minio                              active      1  minio                     ckf-1.10/stable  ...
nginx-ingress-integrator           active      1  nginx-ingress-integrator  latest/edge  ...
opencti                            active      1  opencti                   latest/edge  ...
redis-k8s                          active      1  redis-k8s                 latest/edge  ...
s3-integrator                      active      1  s3-integrator             ...
```

You can also verify the Kubernetes pods are running:

```
kubectl get pods -n opencti
```

Expected output:

```
NAME                                   READY   STATUS    RESTARTS   AGE
opencti-0                              2/2     Running   0          5m
```

The `2/2` indicates both the charm sidecar container and the OpenCTI container
are running successfully.

## Access OpenCTI

Add the `opencti.local` hostname to your `/etc/hosts` file, pointing it to
`127.0.0.1` (or to your Multipass VM IP if applicable):

```
echo "127.0.0.1 opencti.local" | sudo tee -a /etc/hosts
```

Open a browser and navigate to `http://opencti.local`. Log in with the
credentials you configured in the previous step:

- **Email:** `admin@example.com`
- **Password:** the password you chose

You should see the OpenCTI dashboard. Congratulations — your OpenCTI deployment
is up and running!

## Tear down the environment

Well done for completing the tutorial! You have successfully deployed OpenCTI
with all its dependencies using Juju.

To remove everything created during this tutorial, destroy both Juju models:

```
juju switch concierge-k8s
juju destroy-model opencti --no-prompt
```

```
juju switch concierge-lxd
juju destroy-model opencti-databases --no-prompt
```

If you created a Multipass VM, you can also delete it:

```
multipass delete opencti-tutorial-vm
multipass purge
```
