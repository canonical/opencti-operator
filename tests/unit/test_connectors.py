# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Unit tests for connectors."""

import ops.testing

from connectors.export_file_stix.src.charm import OpenctiExportFileStixConnectorCharm
from tests.unit.state import ConnectorStateBuilder


def test_export_file_stix_connector():
    """
    arrange: provide the connector charm with the required integrations and configurations
    act: simulate a config-changed event
    assert: the installed Pebble plan matches the expectation
    """
    container = "opencti-export-file-stix-connector"
    ctx = ops.testing.Context(OpenctiExportFileStixConnectorCharm)
    state_in = (
        ConnectorStateBuilder(container)
        .add_opencti_connector_integration()
        .set_config("connector-scope", "application/json")
        .build()
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    plan = state_out.get_container(container).plan.to_dict()
    del plan["services"]["connector"]["environment"]["CONNECTOR_ID"]
    assert plan == {
        "services": {
            "connector": {
                "command": "bash /entrypoint.sh",
                "environment": {
                    "CONNECTOR_LOG_LEVEL": "info",
                    "CONNECTOR_NAME": "opencti-export-file-stix-connector",
                    "CONNECTOR_SCOPE": "application/json",
                    "CONNECTOR_TYPE": "INTERNAL_EXPORT_FILE",
                    "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
                    "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
                },
                "on-failure": "restart",
                "override": "replace",
                "startup": "enabled",
            }
        }
    }
