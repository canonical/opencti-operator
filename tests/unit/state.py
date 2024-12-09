# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Generate fake data for unit tests."""

import json
import typing

import ops.testing


class StateBuilder:
    def __init__(self, leader=True, can_connect=True):
        self._integrations = []
        self._config = {}
        self._secrets = []
        self._leader = leader
        self._can_connect = can_connect

    def add_opensearch_client_integration(self, insecure=False) -> typing.Self:
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

    def add_rabbitmq_integration(self) -> typing.Self:
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

    def add_redis_integration(self) -> typing.Self:
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

    def add_s3_integration(self) -> typing.Self:
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

    def add_ingress_integration(self) -> typing.Self:
        self._integrations.append(
            ops.testing.Relation(
                remote_app_name="nginx-ingress-integrator",
                endpoint="ingress",
                remote_app_data={"ingress": json.dumps({"url": "http://opencti"})},
            )
        )
        return self

    def add_opencti_peer_integration(self) -> typing.Self:
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

    def add_required_integrations(self, excludes: list[str] | None = None) -> typing.Self:
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

    def add_required_configs(self, excludes: list[str] | None = None) -> typing.Self:
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

    def add_integration(self, integration: ops.testing.RelationBase) -> typing.Self:
        self._integrations.append(integration)
        return self

    def add_secret(self, secret: ops.testing.Secret) -> typing.Self:
        self._secrets.append(secret)
        return self

    def set_config(self, name: str, value: str) -> typing.Self:
        self._config[name] = value
        return self

    def build(self) -> ops.testing.State:
        return ops.testing.State(
            leader=self._leader,
            containers=[
                ops.testing.Container(
                    name="opencti",
                    can_connect=self._can_connect,
                )
            ],
            relations=self._integrations,
            secrets=self._secrets,
            config=self._config,
        )
