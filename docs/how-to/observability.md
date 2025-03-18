# How to integrate with COS

The OpenCTI charm exposes standard [COS](https://charmhub.io/topics/canonical-observability-stack)
integration [endpoints](https://canonical-juju.readthedocs-hosted.com/en/latest/user/reference/application/#application-endpoint). 

These include:

- `metrics-endpoint`: integrate with the [`prometheus-k8s` charm](https://charmhub.io/prometheus-k8s)
  for Prometheus metrics and alert rules.
- `grafana-dashboard`: integrate with the [`grafana-k8s` charm](https://charmhub.io/grafana-k8s)
  to provide the OpenCTI Grafana dashboard.
- `logging`: integrate with the [`loki-k8s` charm](https://charmhub.io/loki-k8s)
  to export logs from both the OpenCTI platform and OpenCTI workers.

All OpenCTI connector charms support the `logging` endpoint for exporting logs 
from OpenCTI connectors.
