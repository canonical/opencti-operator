#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=too-many-arguments,too-many-positional-arguments

"""Integration tests."""

import textwrap
import time
import typing
import urllib.parse

import boto3
import botocore.client
import botocore.exceptions
import pytest
import requests
import yaml
from juju.model import Model

from opencti import OpenctiClient


def _create_bucket_with_retry(
    s3: botocore.client.BaseClient, bucket: str, timeout: int = 300
) -> None:
    """Create an S3 bucket, retrying while the endpoint is not yet reachable.

    minio's workload can report "idle"/"active" via Juju well before its pod
    has finished starting (image pull, PVC provisioning, container init),
    so retry for a while instead of failing immediately.

    Raises:
        ConnectionError: if the S3 endpoint is still unreachable after the
            timeout.
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            s3.create_bucket(Bucket=bucket)
            return
        except botocore.exceptions.ConnectionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(5)


def _wait_for_connector_registration(
    query_connectors: typing.Callable[[], dict], connector: str, timeout: int = 120
) -> dict:
    """Poll the OpenCTI connectors query until the connector registers as active.

    A charm/unit reporting "active" via Juju only means its workload was
    started, not that the connector process has finished connecting to and
    registering itself with the OpenCTI platform, which can take longer.
    """
    deadline = time.monotonic() + timeout
    while True:
        connectors = query_connectors()
        if connector in connectors and connectors[connector]["active"]:
            return connectors
        if time.monotonic() >= deadline:
            assert connector in connectors
            assert connectors[connector]["active"]
        time.sleep(5)


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("machine_charm_dependencies")
async def test_deploy_charm(
    pytestconfig: pytest.Config,
    model: Model,
    machine_model: Model,
    machine_controller_name: str,
    get_unit_ips,
    opencti_charm,
):
    """
    arrange: deploy dependencies of the OpenCTI charm.
    act: deploy the OpenCTI charm.
    assert: deployment is successful.
    """
    minio = await model.deploy(
        "minio",
        channel="ckf-1.10/stable",
        config={"access-key": "minioadmin", "secret-key": "minioadmin"},
    )
    await model.wait_for_idle(apps=[minio.name])
    ip = (await get_unit_ips(minio.name))[0]
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{ip}:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        config=botocore.client.Config(signature_version="s3v4"),
    )
    _create_bucket_with_retry(s3, "opencti")
    s3_integrator = await model.deploy(
        "s3-integrator",
        config={
            "bucket": "opencti",
            "endpoint": f"http://minio-endpoints.{model.name}.svc.cluster.local:9000",
        },
    )
    await model.wait_for_idle(apps=[s3_integrator.name])
    action = await s3_integrator.units[0].run_action(
        "sync-s3-credentials",
        **{
            "access-key": "minioadmin",
            "secret-key": "minioadmin",
        },
    )
    await action.wait()
    opencti = await model.deploy(
        f"./{opencti_charm}",
        resources={
            "opencti-image": pytestconfig.getoption("--opencti-image"),
        },
        num_units=2,
    )
    redis_k8s = await model.deploy("redis-k8s", channel="latest/edge")
    nginx_ingress_integrator = await model.deploy(
        "nginx-ingress-integrator",
        channel="edge",
        config={
            "path-routes": "/",
            "service-hostname": "nginx-ingress-microk8s-controller.ingress.svc.cluster.local",
        },
        trust=True,
        revision=109,
    )
    await model.integrate(
        f"{machine_controller_name}:admin/{machine_model.name}.opensearch-client",
        opencti.name,
    )
    await model.integrate(
        f"{machine_controller_name}:admin/{machine_model.name}.amqp",
        opencti.name,
    )
    await model.integrate(redis_k8s.name, opencti.name)
    await model.integrate(nginx_ingress_integrator.name, opencti.name)
    await model.integrate(s3_integrator.name, opencti.name)
    secret_id = await model.add_secret(
        name="opencti-admin-user", data_args=["email=admin@example.com", "password=test"]
    )
    secret_id = secret_id.strip()
    await model.grant_secret("opencti-admin-user", opencti.name)
    await opencti.set_config({"admin-user": secret_id})
    await model.wait_for_idle(timeout=900, status="active")


async def test_opencti_workers(get_unit_ips, ops_test):
    """
    arrange: deploy the OpenCTI charm.
    act: get the number of OpenCTI workers.
    assert: the number of OpenCTI workers matches the expectation.
    """
    query = {
        "id": "WorkersStatusQuery",
        "query": textwrap.dedent("""\
            query WorkerCount {
                rabbitMQMetrics {
                    consumers
                }
            }
            """),
        "variables": {},
    }
    _, stdout, _ = await ops_test.juju(
        "ssh", "--container", "opencti", "opencti/0", "pebble", "plan"
    )
    plan = yaml.safe_load(stdout)
    api_token = plan["services"]["platform"]["environment"]["APP__ADMIN__TOKEN"]
    resp = requests.post(
        f"http://{(await get_unit_ips('opencti'))[0]}:8080/graphql",
        json=query,
        headers={"Authorization": f"Bearer {api_token}"},
        timeout=5,
    )
    worker_count = resp.json()["data"]["rabbitMQMetrics"]["consumers"]
    assert worker_count == str(6)


async def test_opencti_client(get_unit_ips, ops_test):
    """
    arrange: deploy the OpenCTI charm.
    act: use the OpenCTI client to create some users.
    assert: users are created normally.
    """
    _, stdout, _ = await ops_test.juju(
        "ssh", "--container", "opencti", "opencti/0", "pebble", "plan"
    )
    plan = yaml.safe_load(stdout)
    api_token = plan["services"]["platform"]["environment"]["APP__ADMIN__TOKEN"]
    client = OpenctiClient(
        url=f"http://{(await get_unit_ips('opencti'))[0]}:8080", api_token=api_token
    )
    assert {u.name for u in client.list_users()} == {"admin"}
    assert {g.name for g in client.list_groups()} == {"Administrators", "Connectors", "Default"}
    client.create_user(name="testing")
    user = {u.name: u for u in client.list_users()}["testing"]
    client.set_account_status(user.id, "Inactive")
    user = {u.name: u for u in client.list_users()}["testing"]
    assert user.account_status == "Inactive"


async def test_opencti_connectors(
    ops_test, model, opencti_connector_charms, opencti_connector_images
):
    """
    arrange: deploy the OpenCTI charm and OpenCTI connector charm.
    act: integrate the OpenCTI connector charm with the OpenCTI charm.
    assert: OpenCTI connector should register itself inside the OpenCTI platform
    """
    connector = "opencti-export-file-stix-connector"
    connector_charm = await model.deploy(
        f"./{opencti_connector_charms[connector]}",
        resources={
            f"{connector}-image": opencti_connector_images[connector],
        },
        config={"connector-scope": "application/json"},
    )
    await model.integrate(connector_charm.name, "opencti")
    await model.wait_for_idle(status="active")
    query = {
        "id": "WorkersStatusQuery",
        "query": textwrap.dedent("""\
                query ConnectorsStatusQuery {
                  ...ConnectorsStatus_data
                }
                fragment ConnectorsStatus_data on Query {
                  connectors {
                    name
                    active
                  }
                }
            """),
        "variables": {},
    }
    _, stdout, _ = await ops_test.juju(
        "ssh", "--container", "opencti", "opencti/0", "pebble", "plan"
    )
    plan = yaml.safe_load(stdout)
    api_token = plan["services"]["platform"]["environment"]["APP__ADMIN__TOKEN"]
    url = plan["services"]["platform"]["environment"]["APP__BASE_URL"]

    def _query_connectors() -> dict:
        """Fetch the connectors currently known to the OpenCTI platform."""
        resp = requests.post(
            "http://127.0.0.1/graphql",
            json=query,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Host": urllib.parse.urlparse(url).netloc,
            },
            timeout=5,
            verify=False,
        )
        return {c["name"]: c for c in resp.json()["data"]["connectors"]}

    # a charm/unit reporting "active" only means its workload was started, not
    # that the connector process has finished registering with the platform,
    # so poll for a while instead of asserting immediately.
    _wait_for_connector_registration(_query_connectors, connector)
