# Deploy OpenCTI for the first time

OpenCTI is an open-source threat intelligence platform that enables
organizations to collect, correlate, and leverage threat data at strategic,
operational and tactical levels. This tutorial walks you through deploying
the OpenCTI charm with all its dependencies using Juju.

## What you'll do

- Deploy OpenSearch and RabbitMQ on a VM model (using LXD)
- Deploy OpenCTI platform and its dependencies (Redis, MinIO, an ingress) on a Kubernetes model
- Integrate the two models using Juju cross-model relations
- Create an admin user and access the OpenCTI platform from a browser

## What you'll need

You will need a working station with AMD64 architecture. Your
working station should have at least eight CPU cores, 16 GB of RAM, and 100 GB of
disk space.

> **Tip:** You can use Multipass to create an isolated environment by running:
>
> ```shell
> multipass launch 24.04 --name opencti-tutorial-vm --cpus 8 --memory 16G --disk 100G
> ```

This tutorial requires the following software to be installed in your working
environment:

- Juju 3.6+
- Canonical Kubernetes 1.32+
- LXD 5.21+

Use [Concierge](https://github.com/canonical/concierge) to set up Juju, LXD and
Canonical Kubernetes:

```shell
VM_IP=$(hostname -I | awk '{print $1}')
sudo snap install --classic concierge
cat << EOF > concierge.yaml
providers:
  lxd:
    enable: true
    bootstrap: true
  k8s:
    enable: true
    bootstrap: true
    bootstrap-constraints:
      root-disk: "5G"
    features:
      load-balancer:
        l2-mode: "true"
        cidrs: "$VM_IP/28"
      local-storage: {}
      network: {}
      ingress: 

host:
  snaps:
    aws-cli:
EOF
sudo concierge prepare -c concierge.yaml
```

Once the command succeeds, you have a working environment with Juju, LXD and
Kubernetes working. You can confirm by running `juju controllers` that should
return both controllers:

```shell
Controller      Model    User   Access     Cloud/Region         Models  Nodes    HA  Version
concierge-k8s   testing  admin  superuser  k8s                       2      1     -  3.6.24  
concierge-lxd*  testing  admin  superuser  localhost/localhost       2      1  none  3.6.24  
```

## Deploy the databases

OpenCTI requires OpenSearch and RabbitMQ, which run best as machine charms on
LXD rather than on Kubernetes. So let's start by creating a Juju model on the LXD controller for them:

```shell
juju switch concierge-lxd
juju add-model opencti-databases
```

You can confirm with `juju status`:

```shell
Model              Controller     Cloud/Region         Version  SLA          Timestamp
opencti-databases  concierge-lxd  localhost/localhost  3.6.24   unsupported  17:22:42+02:00
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

Deploy a signle-node OpenSearch cluster. OpenSearch requires specific kernel
parameters on the host machine. The `sysconfig` charm applies them
automatically:

```shell
juju deploy opensearch --channel 2/stable --constraints "virt-type=virtual-machine cores=2 mem=4G"
juju deploy sysconfig --channel latest/stable \
  --config sysctl="{vm.max_map_count: 262144, vm.swappiness: 0, net.ipv4.tcp_retries2: 5, fs.file-max: 1048576}"
juju integrate sysconfig opensearch
juju integrate self-signed-certificates opensearch
```

Note: `sysconfig` will remain in `blocked` state as it needs a reboot:

```shell
  sysconfig/1*               blocked   idle            10.228.176.177                  update-grub and reboot required. Changes in: /etc/default/grub.d/90-sysconfig.cfg
```

This is not an issue for the rest of the tutorial. If you still want to reboot it, you can do so with:

```shell
juju ssh opensearch/leader -- sudo reboot
```

In parallel to OpenSearch, you can deploy RabbitMQ, which OpenCTI uses as a message queue:

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
so that the Kubernetes model can consume the database and certificate services:

```shell
juju offer opensearch:opensearch-client opensearch-client
juju offer rabbitmq-server:amqp amqp
juju offer self-signed-certificates:certificates certificates
```

## Deploy OpenCTI and its dependencies

Create a Juju model on the Kubernetes controller for the OpenCTI platform:

```shell
juju switch concierge-k8s
juju add-model opencti
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

Deploy `gateway-api-integrator` and `ingress-configurator` to provide an ingress relation to expose the OpenCTI web interface. The last command integrates the `gateway-api-service` with `self-signed-certificates` to be able to provide `https` access:

```shell
juju integrate gateway-api-integrator concierge-lxd:admin/opencti-databases.certificates
```

```shell
juju deploy gateway-api-integrator \
  --trust \
  --channel 1/edge \
  --config gateway-class=cilium
juju deploy ingress-configurator \
  --trust \
  --channel latest/edge  
juju integrate ingress-configurator gateway-api-integrator
juju integrate gateway-api-integrator concierge-lxd:admin/opencti-databases.certificates
```

Note: `ingress-configurator` will remain in `blocked` state until we integrate it to `opencti` in the coming sections.

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

```shell
juju run s3-integrator/0 sync-s3-credentials \
  --string-args access-key=minioadmin secret-key=minioadmin
```

The `s3-integrator` should now turn to `active`.

## Integrate the services

Integrate OpenCTI with all its dependencies, including the cross-model offers
from the LXD controller:

```shell
juju integrate opencti concierge-lxd:admin/opencti-databases.opensearch-client
juju integrate opencti concierge-lxd:admin/opencti-databases.amqp
juju integrate opencti redis-k8s
juju integrate opencti s3-integrator
juju integrate opencti ingress-configurator
```

The final result should look like this when you run `juju status`:

```shell
Model    Controller     Cloud/Region  Version  SLA          Timestamp
opencti  concierge-k8s  k8s           3.6.24   unsupported  11:52:39+02:00

SAAS               Status   Store          URL
amqp               active   concierge-lxd  admin/opencti-databases.amqp
certificates       active   concierge-lxd  admin/opencti-databases.certificates
opensearch-client  blocked  concierge-lxd  admin/opencti-databases.opensearch-client

App                     Version                Status   Scale  Charm                   Channel          Rev  Address         Exposed  Message
gateway-api-integrator                         active       1  gateway-api-integrator  1/edge           161  10.152.183.116  no       Gateway addresses: 10.56.254.16
ingress-configurator                           active       1  ingress-configurator    latest/edge       90  10.152.183.160  no       Ready
minio                   res:oci-image@7f2474f  active       1  minio                   ckf-1.10/stable  583  10.152.183.121  no       
opencti                                        blocked      1  opencti                 latest/edge      117  10.152.183.213  no       missing charm config: admin-user
redis-k8s               7.2.5                  active       1  redis-k8s               latest/edge       42  10.152.183.205  no       
s3-integrator                                  active       1  s3-integrator           1/stable         562  10.152.183.117  no       

Unit                       Workload  Agent  Address     Ports          Message
gateway-api-integrator/0*  active    idle   10.1.0.237                 Gateway addresses: 10.56.254.16
ingress-configurator/0*    active    idle   10.1.0.137                 Ready
minio/0*                   active    idle   10.1.0.71   9000-9001/TCP  
opencti/0*                 blocked   idle   10.1.0.229                 missing charm config: admin-user
redis-k8s/0*               active    idle   10.1.0.89                  
s3-integrator/0*           active    idle   10.1.0.57
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

> Note: In production, replace `changeme` with a strong password of your choice.

Wait for OpenCTI to finish deploying:

```shell
juju wait-for application opencti --query='status=="active"' --timeout 20m
```

## Check the deployment

Run `juju status` to confirm that all applications are active:

```shell
juju status
```

The output should resemble:

```shell
Model    Controller     Cloud/Region  Version  SLA          Timestamp
opencti  concierge-k8s  k8s           3.6.24   unsupported  14:36:29+02:00

...

App                     Version                Status  Scale  Charm                   Channel          Rev  Address         Exposed  Message
gateway-api-integrator                         active      1  gateway-api-integrator  1/edge           161  10.152.183.116  no       Gateway addresses: 10.56.254.16
ingress-configurator                           active      1  ingress-configurator    latest/edge       90  10.152.183.201  no       Ready
minio                   res:oci-image@7f2474f  active      1  minio                   ckf-1.10/stable  583  10.152.183.121  no       
opencti                                        active      1  opencti                 latest/edge      117  10.152.183.213  no       
redis-k8s               7.2.5                  active      1  redis-k8s               latest/edge       42  10.152.183.205  no       
s3-integrator                                  active      1  s3-integrator           1/stable         562  10.152.183.117  no       

Unit                       Workload  Agent  Address     Ports          Message
gateway-api-integrator/0*  active    idle   10.1.0.23                  Gateway addresses: 10.56.254.16
ingress-configurator/0*    active    idle   10.1.0.202                 Ready
minio/0*                   active    idle   10.1.0.17   9000-9001/TCP  
opencti/0*                 active    idle   10.1.0.62                  
redis-k8s/0*               active    idle   10.1.0.205                 
s3-integrator/0*           active    idle   10.1.0.164    
```

## Access OpenCTI in a browser

On your workstation open a browser and navigate to `https://<gateway-addresses>`, where `<gateway-address>` is the IP you see in front of `gateway-api-integrator` in the output of `juju status`.

Note: You will have to bypass the security warning as we are using a self-signed certificate in this tutorial: click the "Advanced" button and then follow the "Proceed to `<gateway-address>`" prompt.

Log in with the credentials you configured in the previous step:

- **Email:** `admin@example.com`
- **Password:** `changeme`

You should see the OpenCTI dashboard. Congratulations — your OpenCTI deployment
is up and running!

## Tear down the environment

Well done for completing the tutorial! You have successfully deployed OpenCTI
with all its dependencies using Juju.

To remove everything created during this tutorial, destroy both Juju models:

```shell
juju switch concierge-k8s
juju destroy-model opencti --destroy-storage --no-prompt
```

```shell
juju switch concierge-lxd
juju destroy-model opencti-databases --destroy-storage --no-prompt
```

If you created a Multipass VM, you can also delete it:

```shell
multipass delete --purge opencti-tutorial-vm
```
