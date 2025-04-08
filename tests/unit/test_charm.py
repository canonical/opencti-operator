# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Unit tests."""

import json
import typing

import ops.testing
import pytest

from src.charm import OpenCTICharm
from tests.unit.state import StateBuilder


@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_pebble_plan():
    """
    arrange: provide the charm with the required integrations and configurations.
    act: simulate a config-changed event.
    assert: the installed Pebble plan matches the expectation.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = StateBuilder().add_required_integrations().add_required_configs().build()
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    container = state_out.get_container("opencti")
    assert container.plan.to_dict() == {
        "checks": {
            "platform": {
                "http": {
                    "url": "http://localhost:8080/health?health_access_key=opencti-health-access-key"
                },
                "level": "ready",
                "override": "replace",
                "period": "1m",
                "threshold": 5,
                "timeout": "5s",
            }
        },
        "services": {
            "charm-callback": {
                "command": "bash /opt/opencti/charm-callback.sh",
                "override": "replace",
            },
            "platform": {
                "command": "node build/back.js",
                "environment": {
                    "APP__ADMIN__EMAIL": "admin@example.com",
                    "APP__ADMIN__PASSWORD": "admin-password",
                    "APP__ADMIN__TOKEN": "opencti-admin-token",
                    "APP__APP_LOGS__LOGS_LEVEL": "info",
                    "APP__BASE_URL": "http://opencti/",
                    "APP__HEALTH_ACCESS_KEY": "opencti-health-access-key",
                    "APP__PORT": "8080",
                    "APP__TELEMETRY__METRICS__ENABLED": "true",
                    "ELASTICSEARCH__PASSWORD": "opensearch-password",
                    "ELASTICSEARCH__INDEX_PREFIX": "opencti",
                    "ELASTICSEARCH__SSL__CA": "/opt/opencti/config/opensearch.pem",
                    "ELASTICSEARCH__URL": json.dumps(
                        [
                            "https://10.212.71.100:9200",
                            "https://10.212.71.62:9200",
                            "https://10.212.71.84:9200",
                        ]
                    ),
                    "ELASTICSEARCH__USERNAME": "opensearch-username",
                    "MINIO__ACCESS_KEY": "minioadmin",
                    "MINIO__ENDPOINT": "minio-endpoints.test-opencti.svc.cluster.local",
                    "MINIO__PORT": "9000",
                    "MINIO__SECRET_KEY": "minioadmin",
                    "MINIO__USE_SSL": "false",
                    "NODE_ENV": "production",
                    "NODE_OPTIONS": "--max-old-space-size=8096",
                    "PROVIDERS__LOCAL__STRATEGY": "LocalStrategy",
                    "PYTHONUNBUFFERED": "1",
                    "RABBITMQ__HOSTNAME": "10.212.71.5",
                    "RABBITMQ__MANAGEMENT_SSL": "false",
                    "RABBITMQ__PASSWORD": "rabbitmq-password",
                    "RABBITMQ__PORT": "5672",
                    "RABBITMQ__PORT_MANAGEMENT": "15672",
                    "RABBITMQ__USERNAME": "opencti",
                    "REDIS__HOSTNAME": (
                        "redis-k8s-0.redis-k8s-endpoints.test-opencti.svc.cluster.local"
                    ),
                    "REDIS__PORT": "6379",
                },
                "override": "replace",
                "working-dir": "/opt/opencti",
            },
            "worker-0": {
                "after": ["platform"],
                "command": "python3 worker.py",
                "environment": {
                    "OPENCTI_TOKEN": "opencti-admin-token",
                    "OPENCTI_URL": "http://localhost:8080",
                    "WORKER_LOG_LEVEL": "info",
                },
                "override": "replace",
                "requires": ["platform"],
                "working-dir": "/opt/opencti-worker",
            },
            "worker-1": {
                "after": ["platform"],
                "command": "python3 worker.py",
                "environment": {
                    "OPENCTI_TOKEN": "opencti-admin-token",
                    "OPENCTI_URL": "http://localhost:8080",
                    "WORKER_LOG_LEVEL": "info",
                },
                "override": "replace",
                "requires": ["platform"],
                "working-dir": "/opt/opencti-worker",
            },
            "worker-2": {
                "after": ["platform"],
                "command": "python3 worker.py",
                "environment": {
                    "OPENCTI_TOKEN": "opencti-admin-token",
                    "OPENCTI_URL": "http://localhost:8080",
                    "WORKER_LOG_LEVEL": "info",
                },
                "override": "replace",
                "requires": ["platform"],
                "working-dir": "/opt/opencti-worker",
            },
        },
    }
    assert (container.get_filesystem(ctx) / "opt/opencti/config/opensearch.pem").exists()


@pytest.mark.parametrize(
    "missing_integration", ["opensearch-client", "amqp", "redis", "s3", "ingress", "opencti-peer"]
)
@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_missing_integration(missing_integration):
    """
    arrange: set up the charm with a missing required integration.
    act: simulate a config-changed event.
    assert: charm produce the correct state message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder()
        .add_required_integrations(excludes=[missing_integration])
        .add_required_configs()
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    if missing_integration == "opencti-peer":
        assert state_out.unit_status.name == "waiting"
        assert state_out.unit_status.message == "waiting for peer integration"
    else:
        assert state_out.unit_status.name == "blocked"
        assert state_out.unit_status.message == f"missing integration(s): {missing_integration}"


@pytest.mark.parametrize("missing_config", ["admin-user"])
@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_missing_config(missing_config):
    """
    arrange: set up the charm with a missing required configuration.
    act: simulate a config-changed event.
    assert: charm produce the correct state message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder()
        .add_required_integrations()
        .add_required_configs(excludes=[missing_config])
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "blocked"
    assert state_out.unit_status.message == "missing charm config: admin-user"


@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_invalid_admin_user_not_a_secret():
    """
    arrange: set up the charm with admin-user contains a value that's not a juju user secret id.
    act: simulate a config-changed event.
    assert: charm produce the correct state message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder()
        .add_required_integrations()
        .add_required_configs(excludes=["admin-user"])
        .set_config("admin-user", "secret:foobar")
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "blocked"
    assert state_out.unit_status.message == "admin-user config is not a secret"


@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_invalid_admin_user_invalid_content():
    """
    arrange: set up the charm with admin-user configuration with incorrect permission setting.
    act: simulate a config-changed event.
    assert: charm produce the correct state message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    secret = ops.testing.Secret(tracked_content={"foobar": "foobar"})
    state_in = (
        StateBuilder()
        .add_required_integrations()
        .add_required_configs(excludes=["admin-user"])
        .set_config("admin-user", secret.id)
        .add_secret(secret)
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "blocked"
    assert state_out.unit_status.message == "invalid secret content in admin-user config"


@pytest.mark.parametrize("leader", [True, False])
@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_amqp_request_admin_user(leader):
    """
    arrange: none.
    act: simulate an amqp-relation-joined event.
    assert: charm set the admin field in the relation application data to request admin privilege.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    relation = ops.testing.Relation(endpoint="amqp")
    state_in = StateBuilder(leader=leader).add_integration(relation).build()
    state_out = ctx.run(ctx.on.relation_joined(relation), state_in)
    if leader:
        data = typing.cast(dict, state_out.get_relation(relation.id).local_app_data)
        assert data["admin"] == "true"


def test_opencti_wait_platform_start(patch_is_platform_healthy):
    """
    arrange: provide the charm with the required integrations and configurations.
    act: simulate a config-changed event.
    assert: charm set the correct status message during opencti platform start-up.
    """
    patch_is_platform_healthy.return_value = False
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = StateBuilder().add_required_integrations().add_required_configs().build()
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"
    assert state_out.unit_status.message == "waiting for opencti platform to start"


@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_pebble_ready():
    """
    arrange: provide the charm with the opencti container not ready.
    act: simulate a config-changed event.
    assert: charm set the correct status message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder(can_connect=False, leader=False)
        .add_required_integrations()
        .add_required_configs()
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"
    assert state_out.unit_status.message == "waiting for opencti container"


@pytest.mark.parametrize("leader", [True, False])
@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_opencti_peer_initiation(leader):
    """
    arrange: none.
    act: simulate an opencti-peer-relation-created event.
    assert: charm correctly initializes the peer integration.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    relation = ops.testing.PeerRelation("opencti-peer")
    state_in = ops.testing.State(
        leader=leader,
        relations=[relation],
        containers=[ops.testing.Container("opencti")],  # type: ignore
    )
    state_out = ctx.run(ctx.on.relation_created(relation), state_in)
    if leader:
        data = typing.cast(dict, state_out.get_relation(relation.id).local_app_data)
        assert "secret" in data


@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_insecure_opensearch_integration():
    """
    arrange: provide the charm with an opensearch integration without password or TLS protection.
    act: simulate a config-changed event.
    assert: charm set the correct opensearch-related environment variables in the pebble plan.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder()
        .add_required_integrations(excludes=["opensearch-client"])
        .add_opensearch_client_integration(insecure=True)
        .add_required_configs()
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    plan = state_out.get_container("opencti").plan.to_dict()
    environment = plan["services"]["platform"]["environment"]
    assert "ELASTICSEARCH__PASSWORD" not in environment
    assert "ELASTICSEARCH__SSL__CA" not in environment
    assert "ELASTICSEARCH__USERNAME" not in environment


@pytest.mark.parametrize(
    "incomplete_integration", ["opensearch-client", "amqp", "redis", "s3", "ingress"]
)
@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_incomplete_integration(incomplete_integration):
    """
    arrange: provide the charm with one required integration not ready.
    act: simulate a config-changed event.
    assert: charm set the correct status message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder()
        .add_required_integrations(excludes=[incomplete_integration])
        .add_integration(ops.testing.Relation(endpoint=incomplete_integration))
        .add_required_configs()
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"
    assert state_out.unit_status.message == f"waiting for {incomplete_integration} integration"


@pytest.mark.usefixtures("patch_is_platform_healthy")
def test_redis_library_workaround():
    """
    arrange: provide the charm with a broken redis integration.
    act: simulate a config-changed event.
    assert: charm set the correct status message.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    state_in = (
        StateBuilder()
        .add_required_integrations(excludes=["redis"])
        .add_integration(
            ops.testing.Relation(
                endpoint="redis",
                remote_app_data={
                    "leader-host": "redis-k8s-0.redis-k8s-endpoints.test-opencti.svc.cluster.local"
                },
            )
        )
        .add_required_configs()
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "blocked"
    assert state_out.unit_status.message == "invalid redis integration"


def test_opencti_connector(patch_opencti_client):
    """
    arrange: provide the charm with the required integrations and configurations.
    act: simulate a config-changed event.
    assert: opencti charm should configure opencti users properly for the connector.
    """
    ctx = ops.testing.Context(OpenCTICharm)
    opencti_connector_integration = ops.testing.Relation(
        endpoint="opencti-connector",
        remote_app_data={
            "connector_type": "INTERNAL_EXPORT_FILE",
            "connector_charm_name": "test",
        },
    )
    state_in = (
        StateBuilder()
        .add_required_integrations()
        .add_required_configs()
        .add_integration(opencti_connector_integration)
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    users = {u.name: u for u in patch_opencti_client.list_users()}
    assert "charm-connector-test" in users
    integration_out = state_out.get_relation(opencti_connector_integration.id)
    assert (
        integration_out.local_app_data["opencti_url"]  # type: ignore
        == "http://opencti-endpoints.test-opencti.svc:8080"
    )
    secret_id = integration_out.local_app_data["opencti_token"]  # type: ignore
    secret = state_out.get_secret(id=secret_id)
    assert secret.tracked_content == {"token": "00000000-0000-0000-0000-000000000000"}
