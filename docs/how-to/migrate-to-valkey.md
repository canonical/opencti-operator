# How to migrate from Redis to Valkey

OpenCTI charm revision 129 and later supports the `valkey` integration, and Valkey is the
recommended charm. The `redis` integration still works, but exactly one of the two is required:
the charm is `blocked` if neither or both are integrated.

```{warning}
OpenCTI doesn't migrate data from Redis to Valkey. OpenCTI keeps its event streams, locks,
connector work tracking and cache there, so the stream history and in-flight work are lost.
The threat intelligence data in OpenSearch isn't affected. Pause the connectors and let their
queues drain before you switch.
```

Refresh the OpenCTI charm, deploy Charmed Valkey, then replace the integration:

```bash
juju refresh opencti
juju deploy valkey --channel 9/edge --trust
juju remove-relation opencti redis-k8s
juju integrate opencti:valkey valkey:valkey-client
```

OpenCTI is `blocked` until Valkey is ready. After OpenCTI is `active`, remove the old Redis
application:

```bash
juju remove-application redis-k8s
```

## Migrate the Terraform modules

The `terraform/charm` module exposes `requires.valkey`, and the `terraform/product` module
deploys `valkey` instead of `redis-k8s`. The `redis_k8s` variable is replaced by `valkey`.
Setting `redis_k8s` fails the plan with an error.

1. Update the OpenCTI Terraform modules to a version that includes Valkey.
2. Set `opencti.revision` to 129 or later.
3. Replace `redis_k8s` with `valkey`. Use `valkey = {}` for the defaults.
4. Apply the change. Terraform destroys the Redis application and its integration, and creates
   the Valkey application and its integration.
