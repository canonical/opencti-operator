# Integrations

### `opensearch-client`

_Interface_: opensearch_client

_Supported charms_: opensearch

OpenCTI charm uses the `redis` integration to obtain OpenSearch server
connection information.

Example `opensearch-client` integrate command: 

```
juju integrate opencti:opensearch-client opensearch
```


### `redis`

_Interface_: redis

_Supported charms_: redis-k8s

OpenCTI charm uses the `redis` integration to obtain redis connection 
information.

Example `redis` integrate command: 

```
juju integrate opencti:redis redis-k8s
```


### `amqp`

_Interface_: rabbitmq

_Supported charms_: rabbitmq-server

OpenCTI charm uses the `redis` integration to obtain rabbitmq connection 
information.

Example `amqp` integrate command: 

```
juju integrate opencti:amqp rabbitmq-server
```


### `s3`

_Interface_: s3

_Supported charms_: s3-integrator

Description here.

OpenCTI charm uses the `redis` integration to obtain S3 compatible storage
credentials.

```
juju integrate opencti:s3 s3-integrator
```


### `ingress`

_Interface_: ingress

_Supported charms_: nginx-ingress-integrator, traefik-k8s

OpenCTI charm uses the `redis` integration to obtain S3 ingress services.

Example `ingress` integrate command: 

```
juju integrate opencti:ingress nginx-ingress-integrator
```


### `opencti-connector`

_Interface_: opencti_connector

_Supported charms_: OpenCTI connector charms

Integrate OpenCTI platform and OpenCTI connector charms.

Example `opencti-connector` integrate command: 

```
juju integrate opencti:opencti-connector opencti-export-file-stix-connector
```


### `logging`

_Interface_: loki_push_api

_Supported charms_: loki-k8s

Push OpenCTI logs to loki log aggregation services.

Example `logging` integrate command: 

```
juju integrate opencti:logging loki-k8s
```


### `metrics-endpoint`

_Interface_: prometheus_scrape

_Supported charms_: prometheus-k8s

Publish OpenCTI prometheus metrics endpoint information.

Example `metrics-endpoint` integrate command: 

```
juju integrate opencti:metrics-endpoint prometheus-k8s
```


### `grafana-dashboard`

_Interface_: grafana_dashboard

_Supported charms_: grafana-k8s

Send Grafana dashboard.

Example `grafana-dashboard` integrate command: 

```
juju integrate opencti:grafana-dashboard grafana-k8s
```