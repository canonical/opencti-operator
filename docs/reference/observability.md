# Observability

## Prometheus metrics

The OpenCTI platform provides the following Prometheus metrics.

### `target_info`
 
_type_: gauge

Target metadata

### `opencti_api_direct_bulk`
 
_type_: gauge

Size of bulks for direct absorption

### `opencti_api_side_bulk`
 
_type_: gauge

Size of bulk for absorption impacts

### `nodejs_version_info`
 
_type_: gauge

Node.js version info.

### `process_start_time_seconds`
 
_type_: gauge

Start time of the process since Unix epoch in seconds.

### `nodejs_eventloop_lag_seconds`
 
_type_: gauge

Lag of event loop in seconds.

### `nodejs_eventloop_lag_min_seconds`
 
_type_: gauge

The minimum recorded event loop delay.

### `nodejs_eventloop_lag_max_seconds`
 
_type_: gauge

The maximum recorded event loop delay.

### `nodejs_eventloop_lag_mean_seconds`
 
_type_: gauge

The mean of the recorded event loop delays.

### `nodejs_eventloop_lag_stddev_seconds`
 
_type_: gauge

The standard deviation of the recorded event loop delays.

### `nodejs_eventloop_lag_p50_seconds`
 
_type_: gauge

The 50th percentile of the recorded event loop delays.

### `nodejs_eventloop_lag_p90_seconds`
 
_type_: gauge

The 90th percentile of the recorded event loop delays.

### `nodejs_eventloop_lag_p99_seconds`
 
_type_: gauge

The 99th percentile of the recorded event loop delays.

### `nodejs_gc_duration_seconds`
 
_type_: histogram

Garbage collection duration by kind, one of `major`, `minor`, `incremental` or `weakcb`.

### `nodejs_heap_size_total_bytes`
 
_type_: gauge

Process heap size from Node.js in bytes.

### `nodejs_heap_size_used_bytes`
 
_type_: gauge

Process heap size used from Node.js in bytes.

### `nodejs_external_memory_bytes`
 
_type_: gauge

Node.js external memory size in bytes.

### `nodejs_heap_space_size_total_bytes`
 
_type_: gauge

Process heap space size total from Node.js in bytes.

### `nodejs_heap_space_size_used_bytes`
 
_type_: gauge

Process heap space size used from Node.js in bytes.

### `nodejs_heap_space_size_available_bytes`
 
_type_: gauge

Process heap space size available from Node.js in bytes.

### `process_resident_memory_bytes`
 
_type_: gauge

Resident memory size in bytes.

### `process_virtual_memory_bytes`
 
_type_: gauge

Virtual memory size in bytes.

### `process_heap_bytes`
 
_type_: gauge

Process heap size in bytes.

### `process_cpu_user_seconds_total`
 
_type_: counter

Total user CPU time spent in seconds.

### `process_cpu_system_seconds_total`
 
_type_: counter

Total system CPU time spent in seconds.

### `process_cpu_seconds_total`
 
_type_: counter

Total user and system CPU time spent in seconds.

### `nodejs_active_handles`
 
_type_: gauge

Number of active `libuv` handles grouped by handle type. Every handle type is C++ class name.

### `nodejs_active_handles_total`
 
_type_: gauge

Total number of active handles.

### `process_max_fds`
 
_type_: gauge

Maximum number of open file descriptors.

### `process_open_fds`
 
_type_: gauge

Number of open file descriptors.

### `nodejs_active_requests`
 
_type_: gauge

Number of active `libuv` requests grouped by request type. Every request type is C++ class name.

### `nodejs_active_requests_total`
 gauge

Total number of active requests.

## Prometheus alerts

The OpenCTI charm provides the following default Prometheus alerts.  
The full alert rules can be seen [here](https://github.com/canonical/opencti-operator/blob/main/src/prometheus_alert_rules/opencti.rule).

### `OpenCTITargetMissing`

_severity_: critical

OpenCTI target has disappeared. An exporter might be crashed.

### `OpenCTINodeEventloopLag`

_severity_: critical

OpenCTI NodeJS Event loop lag is above 500 milliseconds for two minutes.

## Logging

Container logs for the OpenCTI platform, OpenCTI workers, and OpenCTI 
connectors are exported using [Pebble log forwarding](https://documentation.ubuntu.com/pebble/reference/log-forwarding/).  

Integrate the OpenCTI charm or OpenCTI worker charm with the Loki charm via 
the `logging` charm integration to export logs.

## Healthcheck endpoints

The OpenCTI charm doesn't expose external health check endpoints. Health check
endpoints are internally checked and linked to the pod's readiness check.
