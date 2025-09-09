#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI NSFocus connector charm the service."""

import pathlib

import ops

import logging
logger = logging.getLogger(__name__)

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiNtiConnectorCharm(OpenctiConnectorCharm):
    connector_type = "EXTERNAL_IMPORT"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    VALID_LOG_LEVELS = {"debug", "info", "warn", "error"}

    def _gen_env(self) -> dict[str, str]:
        env = super()._gen_env()

        # Force nti
        env["CONNECTOR_SCOPE"] = "nti"

        # Check log level value, logging and setting to default if there is a misconfiguration
        log_level = env.get("CONNECTOR_LOG_LEVEL", "info")
        if log_level not in self.VALID_LOG_LEVELS:
            logger.warning(
                f"CONNECTOR_LOG_LEVEL '{log_level}' is invalid, using 'info' instead."
            )
            log_level = "info"
        env["CONNECTOR_LOG_LEVEL"] = log_level

        return env


if __name__ == "__main__":
    ops.main(OpenctiNtiConnectorCharm)
