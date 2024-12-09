#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI charm the service."""

import json
import logging
import secrets
import time
import typing
import urllib.parse
import uuid

import ops
import requests
from charms.data_platform_libs.v0.data_interfaces import OpenSearchRequires
from charms.data_platform_libs.v0.s3 import S3Requirer
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v1.loki_push_api import LogForwarder
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.rabbitmq_k8s.v0.rabbitmq import RabbitMQRequires
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer

logger = logging.getLogger(__name__)


class MissingConfig(Exception):
    """Missing charm configuration."""


class InvalidConfig(Exception):
    """Invalid content in charm configurations."""


class MissingIntegration(Exception):
    """Missing charm integration."""


class InvalidIntegration(Exception):
    """Invalid content in integrations."""


class ContainerNotReady(Exception):
    """Container (pebble) not ready."""


class IntegrationNotReady(Exception):
    """Charm integration not ready."""


class PlatformNotReady(Exception):
    """OpenCTI platform service not ready."""


# caused by charm libraries
# pylint: disable=too-many-instance-attributes
class OpenCTICharm(ops.CharmBase):
    """OpenCTI charm the service.

    Attrs:
        on: RedisRelationCharmEvents.
    """

    on = RedisRelationCharmEvents()
    _PEER_INTEGRATION_NAME = "opencti-peer"
    # bandit false alarm
    _PEER_SECRET_FIELD = "secret"  # nosec
    _PEER_SECRET_ADMIN_TOKEN_SECRET_FIELD = "admin-token"  # nosec
    _PEER_SECRET_HEALTH_ACCESS_KEY_SECRET_FIELD = "health-access-key"  # nosec
    _HEALTH_CHECK_TIMEOUT = 200
    _HEALTH_CHECK_INTERVAL = 5

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self._container = self.unit.get_container("opencti")
        if self.app.name == "x-opencti":
            self.unit.status = ops.BlockedStatus("charm cannot be named 'x-opencti'")
            return
        self._opensearch = OpenSearchRequires(
            self,
            relation_name="opensearch-client",
            # suppress the OpenSearch charm from creating the index
            # use the name x-opencti so OpenSearch will create an index named 'x-opencti'
            # which shouldn't interfere with the OpenCTI (index prefix is the charm app name)
            # hope nobody names the charm app 'x-opencti'
            index="x-opencti",
            # the OpenSearch charm can't handle access control for index patterns
            extra_user_roles="admin",
        )
        self._redis = RedisRequires(self, relation_name="redis")
        self._rabbitmq = RabbitMQRequires(
            self,
            "amqp",
            username=self.app.name,
            vhost="/",
        )
        self._s3 = S3Requirer(self, relation_name="s3", bucket_name=self.app.name)
        self._ingress = IngressPerAppRequirer(
            self,
            relation_name="ingress",
            port=8080,
        )
        self._log_forwarder = LogForwarder(self)
        self._grafana_dashboards = GrafanaDashboardProvider(self)
        self._metrics_endpoint = MetricsEndpointProvider(
            self,
            jobs=[
                {
                    "job_name": "opencti_metrics",
                    "static_configs": [{"targets": ["*:14269"]}],
                }
            ],
        )
        self.framework.observe(self.on.amqp_relation_joined, self._amqp_relation_joined)
        self.framework.observe(self.on.config_changed, self._reconcile)
        self.framework.observe(self.on.upgrade_charm, self._reconcile)
        self.framework.observe(self.on.update_status, self._reconcile)
        self.framework.observe(self.on.secret_changed, self._reconcile)
        self.framework.observe(self.on.opencti_pebble_ready, self._reconcile)
        self.framework.observe(self.on.opencti_peer_relation_created, self._reconcile)
        self.framework.observe(self.on.opencti_peer_relation_changed, self._reconcile)
        self.framework.observe(self.on.opencti_peer_relation_departed, self._reconcile)
        self.framework.observe(self._opensearch.on.index_created, self._reconcile)
        self.framework.observe(self._opensearch.on.endpoints_changed, self._reconcile)
        self.framework.observe(self._opensearch.on.authentication_updated, self._reconcile)
        self.framework.observe(self.on.opensearch_client_relation_broken, self._reconcile)
        self.framework.observe(self._redis.charm.on.redis_relation_updated, self._reconcile)
        self.framework.observe(self.on.redis_relation_broken, self._reconcile)
        self.framework.observe(self._s3.on.credentials_changed, self._reconcile)
        self.framework.observe(self._s3.on.credentials_gone, self._reconcile)
        self.framework.observe(self._ingress.on.ready, self._reconcile)
        self.framework.observe(self._ingress.on.revoked, self._reconcile)

    def _amqp_relation_joined(self, event: ops.RelationJoinedEvent) -> None:
        """Handle amqp relation joined event.

        Args:
            event: Relation joined event.
        """
        # rabbitmq charm library doesn't expose the admin user setting
        if self.unit.is_leader():
            event.relation.data[self.app]["admin"] = "true"

    def _reconcile(self, _: ops.EventBase) -> None:
        """Run charm reconcile function and catch all exceptions."""
        try:
            self._reconcile_raw()
            self.unit.status = ops.ActiveStatus()
        except (MissingIntegration, MissingConfig, InvalidIntegration, InvalidConfig) as exc:
            self.unit.status = ops.BlockedStatus(str(exc))
        except (ContainerNotReady, IntegrationNotReady, PlatformNotReady) as exc:
            self.unit.status = ops.WaitingStatus(str(exc))

    def _reconcile_raw(self) -> None:
        """Run charm reconcile function.

        Raises:
            PlatformNotReady: failed to start the OpenCTI platform
        """
        self._init_peer_relation()
        self._check()
        worker_service: ops.pebble.ServiceDict = {
            "override": "replace",
            "command": "python3 worker.py",
            "working-dir": "/opt/opencti-worker",
            "environment": {
                "OPENCTI_URL": "http://localhost:8080",
                "OPENCTI_TOKEN": self._get_peer_secret(self._PEER_SECRET_ADMIN_TOKEN_SECRET_FIELD),
                "WORKER_LOG_LEVEL": "info",
            },
            "after": ["platform"],
            "requires": ["platform"],
        }
        health_check_token = self._get_peer_secret(
            self._PEER_SECRET_HEALTH_ACCESS_KEY_SECRET_FIELD
        )
        health_check_url = f"http://localhost:8080/health?health_access_key={health_check_token}"
        self._container.add_layer(
            "opencti",
            layer=ops.pebble.LayerDict(
                summary="OpenCTI platform/worker",
                description="OpenCTI platform/worker",
                services={
                    "platform": {
                        "override": "replace",
                        "command": "node build/back.js",
                        "working-dir": "/opt/opencti",
                        "environment": {
                            "NODE_OPTIONS": "--max-old-space-size=8096",
                            "NODE_ENV": "production",
                            "PYTHONUNBUFFERED": "1",
                            "APP__PORT": "8080",
                            "APP__APP_LOGS__LOGS_LEVEL": "info",
                            "PROVIDERS__LOCAL__STRATEGY": "LocalStrategy",
                            "APP__TELEMETRY__METRICS__ENABLED": "true",
                            **self._gen_secret_env(),
                            **self._prepare_opensearch_env(),
                            **self._gen_rabbitmq_env(),
                            **self._gen_redis_env(),
                            **self._gen_s3_env(),
                            **self._gen_ingress_env(),
                        },
                    },
                    "worker-0": worker_service,
                    "worker-1": worker_service,
                    "worker-2": worker_service,
                },
                checks={
                    "platform": {
                        "override": "replace",
                        "level": "ready",
                        "http": {"url": health_check_url},
                        "period": "1m",
                        "timeout": "5s",
                        "threshold": 5,
                    }
                },
            ),
            combine=True,
        )
        self._container.replan()
        self._container.start("platform")
        start_time = time.time()
        deadline = start_time + self._HEALTH_CHECK_TIMEOUT
        while time.time() < deadline:
            try:
                self._check_platform_health(health_check_url)
                self._container.start("worker-0")
                self._container.start("worker-1")
                self._container.start("worker-2")
                return
            except PlatformNotReady:
                self.unit.status = ops.WaitingStatus(
                    f"waiting for opencti platform to start ({int(time.time() - start_time)}s)"
                )
                time.sleep(self._HEALTH_CHECK_INTERVAL)
                continue
        raise PlatformNotReady("opencti platform start-up failed")

    @staticmethod
    def _check_platform_health(health_check_url: str) -> None:  # pragma: nocover
        """Check OpenCTI platform is ready using the health check url.

        Args:
            health_check_url: OpenCTI platform health check endpoint.

        Raises:
            PlatformNotReady: If OpenCTI platform is not ready.
        """
        try:
            response = requests.get(health_check_url, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PlatformNotReady() from exc

    def _check(self) -> None:
        """Check the prerequisites for the OpenCTI charm."""
        if not self._container.can_connect():
            raise ContainerNotReady("waiting for opencti container")
        integrations = [
            "opensearch-client",
            "redis",
            "amqp",
            "s3",
            "ingress",
        ]
        missing_integrations = []
        for integration_name in integrations:
            integration = self.model.get_relation(integration_name)
            if integration is None or integration.app is None or not integration.units:
                missing_integrations.append(integration_name)
        if missing_integrations:
            raise MissingIntegration(f"missing integration(s): {', '.join(missing_integrations)}")

    def _init_peer_relation(self) -> None:
        """Initialize the OpenCTI charm peer relation.

        It is safe to call this method at any time.
        """
        if not (peer_integration := self.model.get_relation(self._PEER_INTEGRATION_NAME)):
            return
        if not self.unit.is_leader():
            return
        if self._PEER_SECRET_FIELD in peer_integration.data[self.app]:
            return
        secret = self.app.add_secret(
            {
                self._PEER_SECRET_ADMIN_TOKEN_SECRET_FIELD: str(
                    uuid.UUID(bytes=secrets.token_bytes(16), version=4)
                ),
                self._PEER_SECRET_HEALTH_ACCESS_KEY_SECRET_FIELD: str(
                    uuid.UUID(bytes=secrets.token_bytes(16), version=4)
                ),
            }
        )
        peer_integration.data[self.app][self._PEER_SECRET_FIELD] = typing.cast(str, secret.id)

    def _gen_secret_env(self) -> dict[str, str]:
        """Generate the secret (token, user, etc.) environment variables for the OpenCTI charm.

        Returns:
            A dictionary containing the secret environment variables.
        """
        if not (admin_user := self.config.get("admin-user")):
            raise MissingConfig("missing charm config: admin-user")
        try:
            admin_user_secret = self.model.get_secret(id=typing.cast(str, admin_user))
        except ops.SecretNotFoundError as exc:
            raise InvalidConfig("admin-user config is not a secret") from exc
        except ops.ModelError as exc:
            raise InvalidConfig(
                "charm doesn't have access to the admin-user secret, "
                "run `juju grant` command to grant the secret to the charm"
            ) from exc
        admin_user_secret_content = admin_user_secret.get_content(refresh=True)
        try:
            admin_email = admin_user_secret_content["email"]
            admin_password = admin_user_secret_content["password"]
        except KeyError as exc:
            raise InvalidConfig("invalid secret content in admin-user config") from exc
        return {
            "APP__ADMIN__EMAIL": admin_email,
            "APP__ADMIN__PASSWORD": admin_password,
            "APP__ADMIN__TOKEN": self._get_peer_secret(self._PEER_SECRET_ADMIN_TOKEN_SECRET_FIELD),
            "APP__HEALTH_ACCESS_KEY": self._get_peer_secret(
                self._PEER_SECRET_HEALTH_ACCESS_KEY_SECRET_FIELD
            ),
        }

    def _get_peer_secret(self, key: str) -> str:
        """Get secret value from the peer relation.

        Args:
            key: secret key.

        Returns:
            secret value.

        Raises:
            IntegrationNotReady: peer relation not ready.
        """
        peer_relation = self.model.get_relation(relation_name=self._PEER_INTEGRATION_NAME)
        if peer_relation is None or not (
            secret_id := peer_relation.data[self.app].get(self._PEER_SECRET_FIELD)
        ):
            raise IntegrationNotReady("waiting for peer integration")
        secret = self.model.get_secret(id=secret_id)
        return secret.get_content(refresh=True)[key]

    def _prepare_opensearch_env(self) -> dict[str, str]:
        """Generate the OpenSearch-related environment variables for the OpenCTI platform.

        Returns:
            A dictionary containing the OpenSearch-related environment variables.

        Raises:
            IntegrationNotReady: OpenSearch integration not ready
            InvalidIntegration: invalid OpenSearch integration.
        """
        integration = typing.cast(
            ops.Relation, self.model.get_relation(self._opensearch.relation_name)
        )
        integration_id = integration.id
        try:
            data = self._opensearch.fetch_relation_data(
                relation_ids=[integration_id],
                fields=["endpoints", "username", "password", "tls", "tls-ca"],
            )[integration_id]
        except ops.ModelError as exc:
            # secret in integration not accessible before the integration events?
            logger.error(
                "invalid opensearch-client integration: %s",
                self._dump_integration("opensearch-client"),
            )
            raise InvalidIntegration("invalid opensearch integration") from exc
        if "endpoints" not in data:
            raise IntegrationNotReady("waiting for opensearch-client integration")
        uses_tls = data.get("tls-ca") or data.get("tls")
        uris = [
            f"{'https' if uses_tls else 'http'}://{endpoint}"
            for endpoint in data["endpoints"].split(",")
        ]
        env = {
            "ELASTICSEARCH__URL": json.dumps(uris),
            "ELASTICSEARCH__INDEX_PREFIX": self.app.name,
        }
        if ca := data.get("tls-ca"):
            self._container.make_dir("/opt/opencti/config/", make_parents=True)
            self._container.push(
                "/opt/opencti/config/opensearch.pem",
                source=ca,
                encoding="ascii",
            )
            env["ELASTICSEARCH__SSL__CA"] = "/opt/opencti/config/opensearch.pem"
        username, password = data.get("username"), data.get("password")
        if username:
            env["ELASTICSEARCH__USERNAME"] = username
            env["ELASTICSEARCH__PASSWORD"] = password
        return env

    def _gen_redis_env(self) -> dict[str, str]:
        """Generate the Redis-related environment variables for the OpenCTI platform.

        Returns:
            A dictionary containing the Redis-related environment variables.

        Raises:
            IntegrationNotReady: redis integration not ready.
            InvalidIntegration: invalid Redis integration.
        """
        redis_url = self._redis.url
        # bug in the Redis library produces an ill-formed redis_url
        # when the integration is not ready
        if not redis_url or redis_url == "redis://None:None":
            raise IntegrationNotReady("waiting for redis integration")
        parsed_redis_url = urllib.parse.urlparse(redis_url)
        try:
            return {
                "REDIS__HOSTNAME": parsed_redis_url.hostname,
                "REDIS__PORT": str(parsed_redis_url.port or "6379"),
            }
        except ValueError as exc:
            # same reason as above
            logger.error("invalid redis integration: %s", self._dump_integration("redis"))
            raise InvalidIntegration("invalid redis integration") from exc

    def _gen_rabbitmq_env(self) -> dict[str, str]:
        """Generate the RabbitMQ-related environment variables for the OpenCTI platform.

        Returns:
            A dictionary containing the RabbitMQ-related environment variables.

        Raises:
            IntegrationNotReady: rabbitmq integration not ready.
        """
        integration = typing.cast(ops.Relation, self.model.get_relation("amqp"))
        unit = sorted(list(integration.units), key=lambda u: int(u.name.split("/")[-1]))[0]
        data = integration.data[unit]
        hostname = data.get("hostname")
        username = self._rabbitmq.username
        password = data.get("password")
        if not (hostname and username and password):
            raise IntegrationNotReady("waiting for amqp integration")
        env = {
            "RABBITMQ__HOSTNAME": hostname,
            "RABBITMQ__PORT": "5672",
            # rabbitmq charms by default enables management plugin
            # but the port is not announced it in the integration
            "RABBITMQ__PORT_MANAGEMENT": "15672",
            "RABBITMQ__MANAGEMENT_SSL": "false",
            "RABBITMQ__USERNAME": username,
            "RABBITMQ__PASSWORD": password,
        }
        return env

    def _gen_s3_env(self) -> dict[str, str]:
        """Generate the S3-related environment variables for the OpenCTI platform.

        Returns:
            A dictionary contains the s3-related environment variables.

        Raises:
            IntegrationNotReady: s3 integration not ready.
        """
        s3_data = self._s3.get_s3_connection_info()
        if not s3_data or "access-key" not in s3_data:
            raise IntegrationNotReady("waiting for s3 integration")
        url = s3_data["endpoint"]
        parsed_url = urllib.parse.urlparse(url)
        return {
            "MINIO__ENDPOINT": parsed_url.hostname,
            "MINIO__PORT": str(parsed_url.port or (443 if parsed_url.scheme == "https" else 80)),
            "MINIO__USE_SSL": "true" if parsed_url.scheme == "https" else "false",
            "MINIO__ACCESS_KEY": s3_data["access-key"],
            "MINIO__SECRET_KEY": s3_data["secret-key"],
        }

    def _gen_ingress_env(self) -> dict[str, str]:
        """Generate the Ingress-related environment variables for the OpenCTI platform.

        Returns:
            A dictionary containing the ingress-related environment variables.

        Raises:
              IntegrationNotReady: ingress integration not ready.
        """
        public_url = self._ingress.url
        if not public_url:
            raise IntegrationNotReady("waiting for ingress integration")
        return {"APP__BASE_URL": public_url}

    def _dump_integration(self, name: str) -> str:
        """Create a debug string representation of the give integration.

        Args:
            name: The name of the integration.

        Returns:
            a string representation of the integration.
        """
        integration = self.model.get_relation(name)
        if not integration:
            return json.dumps(None)
        dump: dict = {}
        app = integration.app
        if not app:
            dump["application-data"] = None
        else:
            dump["application-data"] = dict(integration.data[app])
        units = integration.units
        if not units:
            dump["unit-data"] = {}
        else:
            dump["unit-data"] = {unit.name: dict(integration.data[unit]) for unit in units}
        return json.dumps(dump)


if __name__ == "__main__":  # pragma: nocover
    ops.main(OpenCTICharm)
