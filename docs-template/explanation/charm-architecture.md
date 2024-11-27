# Charm architecture

Add overview material here:
1) What kind of application is it? What kind of software does it use?
2) Describe Pebble services.
3) Include an architecture diagram.

<!-- Example: Indico
At its core, [Indico](https://getindico.io/) is a [Flask](https://flask.palletsprojects.com/) application that integrates with [PostgreSQL](https://www.postgresql.org/), [Redis](https://redis.io/), and [Celery](https://docs.celeryq.dev/en/stable/).

The charm design leverages the [sidecar](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/#example-1-sidecar-containers) pattern to allow multiple containers in each pod with [Pebble](https://juju.is/docs/sdk/pebble) running as the workload container’s entrypoint.

Pebble is a lightweight, API-driven process supervisor that is responsible for configuring processes to run in a container and controlling those processes throughout the workload lifecycle.

Pebble `services` are configured through [layers](https://github.com/canonical/pebble#layer-specification), and the following containers represent each one a layer forming the effective Pebble configuration, or `plan`:

1. An [NGINX](https://www.nginx.com/) container, which can be used to efficiently serve static resources, as well as be the incoming point for all web traffic to the pod.
2. The [Indico](https://getindico.io/) container itself, which has a [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) server configured in HTTP mode.


As a result, if you run a `kubectl get pods` on a namespace named for the Juju model you've deployed the Indico charm into, you'll see something like the following:

```bash
NAME                             READY   STATUS    RESTARTS   AGE
indico-0                         3/3     Running   0         6h4m
```

This shows there are 4 containers - the three named above, as well as a container for the charm code itself.

And if you run `kubectl describe pod indico-0`, all the containers will have as Command ```/charm/bin/pebble```. That's because Pebble is responsible for the processes startup as explained above.
-->

## OCI images

We use [Rockcraft](https://canonical-rockcraft.readthedocs-hosted.com/en/latest/) to build OCI Images for <charm-name>. 
The images are defined in [<charm-name> rock](link to rock).
They are published to [Charmhub](https://charmhub.io/), the official repository of charms.

> See more: [How to publish your charm on Charmhub](https://juju.is/docs/sdk/publishing)

## (Optional) Containers

Configuration files for the containers can be found in the respective directories that define the rocks.

<!--
### Container example

Description of container.

The workload that this container is running is defined in the [<container-name> rock](link to rock).
-->

## Metrics
<! --
Add a description of the metrics:
* Are there metrics for containers, non-containerised workloads, snaps, or something else?
* How are the metrics defined or added?

For example, if the charm uses containers: Inside the above mentioned containers, additional Pebble layers are defined in order to provide metrics.
-->

<!--
### Metrics example

Description of metric. In what container is the metric run? What statistics or values does the metric provide? 

How is the container started? 

On what port(s) does the metric listen?

The workload that this container is running is defined in the [<container-name> rock](link to rock).
-->
 
## Juju events

For this charm, the following Juju events are observed:

<!--
Numbered list of Juju events. Link to describe the event in more detail (either in Juju docs or in a specific charm's docs). When is the event fired? What does the event indicate/mean?
-->

> See more in the Juju docs: [Event](https://juju.is/docs/sdk/event)

## Charm code overview

The `src/charm.py` is the default entry point for a charm and has the <relevant-charm-class> Python class which inherits from CharmBase. CharmBase is the base class 
from which all Charms are formed, defined by [Ops](https://juju.is/docs/sdk/ops) (Python framework for developing charms).

> See more in the Juju docs: [Charm](https://juju.is/docs/sdk/constructs#heading--charm)

The `__init__` method guarantees that the charm observes all events relevant to its operation and handles them.

Take, for example, when a configuration is changed by using the CLI.

1. User runs the configuration command:
```bash
juju config <relevant-charm-configuration>
```
2. A `config-changed` event is emitted.
3. In the `__init__` method is defined how to handle this event like this:
```python
self.framework.observe(self.on.config_changed, self._on_config_changed)
```
4. The method `_on_config_changed`, for its turn, will take the necessary actions such as waiting for all the relations to be ready and then configuring the containers.
