#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI VirusTotal Livehunt Notifications connector charm the service."""

import pathlib

import ops

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiVirustotalLivehuntConnectorCharm(OpenctiConnectorCharm):
    connector_type = "EXTERNAL_IMPORT"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    @property
    def boolean_style(self) -> str:
        return "python"


if __name__ == "__main__":
    ops.main(OpenctiVirustotalLivehuntConnectorCharm)
