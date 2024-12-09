#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=too-many-arguments,too-many-positional-arguments

"""Integration tests."""

import textwrap

import boto3
import botocore.client
import pytest
import requests
import yaml
from juju.model import Model


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("machine_charm_dependencies")
async def test_deploy_charm(
    pytestconfig: pytest.Config,
    model: Model,
    machine_model: Model,
    machine_controller_name: str,
    get_unit_ips,
):
    """
    arrange: deploy dependencies of the OpenCTI charm
    act: deploy the OpenCTI charm
    assert: deployment is successful
    """
    minio = await model.deploy(
        "minio",
        channel="ckf-1.9/stable",
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
    s3.create_bucket(Bucket="opencti")
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
        f"./{pytestconfig.getoption("--charm-file")}",
        resources={
            "opencti-image": pytestconfig.getoption("--opencti-image"),
        },
    )
    redis_k8s = await model.deploy("redis-k8s", channel="latest/edge")
    nginx_ingress_integrator = await model.deploy(
        "nginx-ingress-integrator",
        channel="edge",
        config={"path-routes": "/", "service-hostname": "penpot.local"},
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
    await model.wait_for_idle(timeout=1800, status="active")


async def test_opencti_workers(get_unit_ips, ops_test):
    """
    arrange: deploy the OpenCTI charm
    act: get the number of OpenCTI workers
    assert: the number of OpenCTI workers matches the expectation
    """
    query = {
        "id": "WorkersStatusQuery",
        "query": textwrap.dedent(
            """\
            query WorkerCount {
                rabbitMQMetrics {
                    consumers
                }
            }
            """
        ),
        "variables": {},
    }
    _, stdout, _ = await ops_test.juju(
        "ssh", "--container", "opencti", "opencti/0", "pebble", "plan"
    )
    plan = yaml.safe_load(stdout)
    api_token = plan["services"]["platform"]["environment"]["APP__ADMIN__TOKEN"]
    resp = requests.post(
        f"http://{(await get_unit_ips("opencti"))[0]}:8080/graphql",
        json=query,
        headers={"Authorization": f"Bearer {api_token}"},
        timeout=5,
    )
    worker_count = resp.json()["data"]["rabbitMQMetrics"]["consumers"]
    assert worker_count == str(3)
