# How to Integrate with COS

The OpenCTI charm exposes standard [COS](https://charmhub.io/topics/canonical-observability-stack)
integration endpoints. These include the `metrics-endpoint` [endpoint](https://canonical-juju.readthedocs-hosted.com/en/latest/user/reference/application/#application-endpoint), 
which can be integrated with the [`prometheus-k8s` charm](https://charmhub.io/prometheus-k8s)
for Prometheus metrics and alert rules; the `grafana-dashboard` endpoint, which
can be integrated with the [`grafana-k8s` charm](https://charmhub.io/grafana-k8s)
to provide the OpenCTI Grafana dashboard; and the `logging` endpoint, which can
be integrated with the [`loki-k8s` charm](https://charmhub.io/loki-k8s) for 
exporting logs from both the OpenCTI platform and OpenCTI workers.

All OpenCTI connector charms support the `logging` endpoint for exporting logs 
from OpenCTI connectors.
