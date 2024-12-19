# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Generate fake data for unit tests."""

import json

import ops.testing


class StateBuilder:
    """ops.testing.State builder."""

    def __init__(self, leader=True, can_connect=True):
        """Initialize the state builder.

        Args:
            leader: whether this charm has leadership.
            can_connect: whether the pebble is ready.
        """
        self._integrations = []
        self._config = {}
        self._secrets = []
        self._leader = leader
        self._can_connect = can_connect

    def add_opensearch_client_integration(self, insecure=False) -> "StateBuilder":
        """Add opensearch-client integration.

        Args:
            insecure: whether the opensearch integration uses TLS and password authentication.

        Returns: self.
        """
        tls_secret = ops.testing.Secret(
            tracked_content={
                "tls-ca": "-----BEGIN CERTIFICATE-----\nOPENSEARCH\n-----END CERTIFICATE-----",
            },
            label="opensearch-client.9999.tls.secret",
        )
        user_secret = ops.testing.Secret(
            tracked_content={
                "password": "opensearch-password",
                "username": "opensearch-username",
            },
            label="opensearch-client.9999.user.secret",
        )
        if insecure:
            requested_secrets = "[]"
        else:
            requested_secrets = json.dumps(["username", "password", "tls", "tls-ca", "uris"])
        relation = ops.testing.Relation(
            endpoint="opensearch-client",
            id=9999,
            remote_app_name="opensearch",
            remote_app_data={
                "data": json.dumps(
                    {
                        "index": "opencti",
                        "requested-secrets": requested_secrets,
                    }
                ),
                "endpoints": "10.212.71.100:9200,10.212.71.62:9200,10.212.71.84:9200",
                "index": "opencti",
                **(
                    {}
                    if insecure
                    else {
                        "secret-tls": tls_secret.id,
                        "secret-user": user_secret.id,
                    }
                ),
                "version": "2.17.0",
            },
        )
        self._integrations.append(relation)
        if not insecure:
            self._secrets.append(tls_secret)
            self._secrets.append(user_secret)
        return self

    def add_rabbitmq_integration(self) -> "StateBuilder":
        """Add rabbitmq integration.

        Returns: self
        """
        self._integrations.append(
            ops.testing.Relation(
                remote_app_name="rabbitmq-server",
                endpoint="amqp",
                remote_units_data={
                    0: {
                        "password": "rabbitmq-password",
                        "hostname": "10.212.71.5",
                    }
                },
            )
        )
        return self

    def add_redis_integration(self) -> "StateBuilder":
        """Add redis integration.

        Returns: self
        """
        self._integrations.append(
            ops.testing.Relation(
                remote_app_name="redis-k8s",
                endpoint="redis",
                remote_app_data={
                    "leader-host": "redis-k8s-0.redis-k8s-endpoints.test-opencti.svc.cluster.local"
                },
                remote_units_data={
                    0: {"hostname": "10.1.75.171", "port": "6379"},
                    1: {"hostname": "10.1.75.184", "port": "6379"},
                    2: {"hostname": "10.1.75.178", "port": "6379"},
                },
            )
        )
        return self

    def add_s3_integration(self) -> "StateBuilder":
        """Add s3 integration.

        Returns: self
        """
        self._integrations.append(
            ops.testing.Relation(
                remote_app_name="s3-integrator",
                endpoint="s3",
                remote_app_data={
                    "access-key": "minioadmin",
                    "bucket": "opencti",
                    "data": json.dumps({"bucket": "opencti"}),
                    "endpoint": "http://minio-endpoints.test-opencti.svc.cluster.local:9000",
                    "secret-key": "minioadmin",
                },
            )
        )
        return self

    def add_ingress_integration(self) -> "StateBuilder":
        """Add ingress integration.

        Returns: self
        """
        self._integrations.append(
            ops.testing.Relation(
                remote_app_name="nginx-ingress-integrator",
                endpoint="ingress",
                remote_app_data={"ingress": json.dumps({"url": "http://opencti"})},
            )
        )
        return self

    def add_opencti_peer_integration(self) -> "StateBuilder":
        """Add opencti-peer integration.

        Returns: self
        """
        secret = ops.testing.Secret(
            tracked_content={
                "admin-token": "opencti-admin-token",
                "health-access-key": "opencti-health-access-key",
            }
        )
        self._secrets.append(secret)
        self._integrations.append(
            ops.testing.PeerRelation(
                endpoint="opencti-peer",
                local_app_data={"secret": secret.id},
            )
        )
        return self

    def add_required_integrations(self, excludes: list[str] | None = None) -> "StateBuilder":
        """Add all required integrations.

        Args:
            excludes: list of integration names to exclude.

        Returns: self
        """
        excludes = excludes or []
        if "opensearch-client" not in excludes:
            self.add_opensearch_client_integration()
        if "amqp" not in excludes:
            self.add_rabbitmq_integration()
        if "redis" not in excludes:
            self.add_redis_integration()
        if "s3" not in excludes:
            self.add_s3_integration()
        if "ingress" not in excludes:
            self.add_ingress_integration()
        if "opencti-peer" not in excludes:
            self.add_opencti_peer_integration()
        return self

    def add_required_configs(self, excludes: list[str] | None = None) -> "StateBuilder":
        """Add all required configs.

        Args:
            excludes: list of config names to exclude.

        Returns: self
        """
        excludes = excludes or []
        if "admin-user" not in excludes:
            secret = ops.testing.Secret(
                tracked_content={
                    "email": "admin@example.com",
                    "password": "admin-password",
                }
            )
            self._secrets.append(secret)
            self._config["admin-user"] = secret.id
        return self

    def add_integration(self, integration: ops.testing.RelationBase) -> "StateBuilder":
        """Add integration.

        Args:
            integration: integration to add.

        Returns: self
        """
        self._integrations.append(integration)
        return self

    def add_secret(self, secret: ops.testing.Secret) -> "StateBuilder":
        """Add secret.

        Args:
            secret: secret to add.

        Returns: self
        """
        self._secrets.append(secret)
        return self

    def set_config(self, name: str, value: str) -> "StateBuilder":
        """Set charm config.

        Args:
            name: config name.
            value: config value.

        Returns: self
        """
        self._config[name] = value
        return self

    def build(self) -> ops.testing.State:
        """Build state.

        Returns: ops.testing.State
        """
        return ops.testing.State(
            model=ops.testing.Model("test-opencti"),
            leader=self._leader,
            containers=[
                ops.testing.Container(  # type: ignore
                    name="opencti",
                    can_connect=self._can_connect,
                )
            ],
            relations=self._integrations,
            secrets=self._secrets,
            config=self._config,
        )


class ConnectorStateBuilder:
    """ops.testing.State builder for connector tests."""

    def __init__(self, container_name: str) -> None:
        """Initialize the state builder.

        Args:
            container_name: name of the container.
        """
        self._integrations: list[ops.testing.RelationBase] = []
        self._config: dict[str, str | int | float | bool] = {}
        self._secrets: list[ops.testing.Secret] = []
        self._container_name = container_name

    def add_opencti_connector_integration(self) -> "ConnectorStateBuilder":
        """Add opencti-connector integration.

        Returns: self
        """
        secret = ops.testing.Secret(
            tracked_content={"token": "00000000-0000-0000-0000-000000000000"}
        )
        integration = ops.testing.Relation(
            remote_app_name="opencti",
            endpoint="opencti-connector",
            remote_app_data={
                "opencti_token": secret.id,
                "opencti_url": "http://opencti-endpoints.test-opencti-connector.svc:8080",
            },
        )
        self._secrets.append(secret)
        self._integrations.append(integration)
        return self

    def set_config(self, name: str, value: str) -> "ConnectorStateBuilder":
        """Set charm config.

        Args:
            name: config name.
            value: config value.

        Returns: self
        """
        self._config[name] = value
        return self

    def build(self) -> ops.testing.State:
        """Build state.

        Returns: ops.testing.State
        """
        return ops.testing.State(
            model=ops.testing.Model("test-opencti-connector"),
            leader=True,
            containers=[
                ops.testing.Container(  # type: ignore
                    name=self._container_name,
                    can_connect=True,
                )
            ],
            relations=self._integrations,
            secrets=self._secrets,
            config=self._config,
        )
