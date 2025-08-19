# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test fixtures for integration tests."""

import json
import logging
import pathlib
import secrets
import typing

import pytest
import pytest_asyncio
from juju.model import Controller, Model
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

MACHINE_MODEL_CONFIG = {
    "logging-config": "<root>=INFO;unit=DEBUG",
    "update-status-hook-interval": "5m",
}


@pytest_asyncio.fixture(scope="module", name="model")
async def model_fixture(ops_test: OpsTest) -> Model:
    """The current test model."""
    assert ops_test.model
    return ops_test.model


@pytest_asyncio.fixture(scope="module", name="machine_controller_name")
def machine_controller_name_fixture(pytestconfig: pytest.Config) -> str:
    """The name of the machine controller."""
    return pytestconfig.getoption("--machine-controller", default="localhost")


@pytest_asyncio.fixture(scope="module", name="machine_controller")
async def machine_controller_fixture(
    machine_controller_name,
) -> typing.AsyncGenerator[Controller, None]:
    """The lxd controller."""
    controller = Controller()
    await controller.connect_controller(machine_controller_name)
    yield controller
    await controller.disconnect()


@pytest_asyncio.fixture(scope="module", name="machine_model")
async def machine_model_fixture(
    machine_controller: Controller, machine_controller_name: str, pytestconfig
) -> typing.AsyncGenerator[Model, None]:
    """The machine model for OpenSearch charm."""
    machine_model_name = f"test-opencti-deps-{secrets.token_hex(2)}"
    model = await machine_controller.add_model(machine_model_name)
    await model.connect(f"{machine_controller_name}:admin/{model.name}")
    await model.set_config(MACHINE_MODEL_CONFIG)
    yield model
    await model.disconnect()
    if not pytestconfig.getoption("--keep-models"):
        await machine_controller.destroy_models(model.uuid)


@pytest_asyncio.fixture(name="get_unit_ips", scope="module")
async def get_unit_ips_fixture(ops_test: OpsTest, model: Model):
    """A function to get unit ips of a charm application."""

    async def _get_unit_ips(name: str):
        """A function to get unit ips of a charm application.

        Args:
            name: The name of the charm application.

        Returns:
            A list of unit ips.
        """
        _, status, _ = await ops_test.juju("status", "-m", model.name, "--format", "json")
        status = json.loads(status)
        logger.error(status)
        units = status["applications"][name]["units"]
        ip_list = []
        for key in sorted(units.keys(), key=lambda n: int(n.split("/")[-1])):
            ip_list.append(units[key]["address"])
        return ip_list

    return _get_unit_ips


@pytest_asyncio.fixture(name="machine_charm_dependencies", scope="module")
async def machine_charm_dependencies_fixture(machine_model: Model):
    """Deploy opencti charm's machine dependency charms."""
    self_signed_certificates = await machine_model.deploy("self-signed-certificates")
    opensearch = await machine_model.deploy("opensearch", channel="2/stable", num_units=3)
    await machine_model.integrate(self_signed_certificates.name, opensearch.name)
    await machine_model.create_offer(f"{opensearch.name}:opensearch-client", "opensearch-client")
    rabbitmq_server = await machine_model.deploy("rabbitmq-server", channel="3.9/stable")
    await machine_model.create_offer(f"{rabbitmq_server.name}:amqp", "amqp")
    await machine_model.wait_for_idle(timeout=1200)


@pytest.fixture(name="opencti_charm", scope="module")
def opencti_charm_fixture(pytestconfig) -> dict[str, str]:
    """Opencti charm file."""
    charm_files = pytestconfig.getoption("--charm-file")
    assert charm_files
    for charm_file in charm_files:
        if "connector" not in pathlib.Path(charm_file).name:
            return charm_file
    raise ValueError("opencti charm file not provided")


@pytest.fixture(name="opencti_connector_charms", scope="module")
def opencti_connector_charms_fixture(connectors, pytestconfig) -> dict[str, str]:
    """Get opencti connector charm files."""
    charms = {}
    charm_files = pytestconfig.getoption("--charm-file")
    for charm_file in charm_files:
        name = pathlib.Path(charm_file).name.split("_")[0]
        if name in connectors:
            charms[name] = charm_file
    logger.info("load opencti connector charms: %s", charms)
    return charms


@pytest.fixture(name="opencti_connector_images", scope="module")
def opencti_connector_images_fixture(connectors, pytestconfig) -> dict[str, str]:
    """Get opencti connector charm images."""
    images = {}
    for connector in connectors:
        image = pytestconfig.getoption(f"--{connector}-image")
        if image:
            images[connector] = image
    logger.info("load opencti connector images: %s", images)
    return images
