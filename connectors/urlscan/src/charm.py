#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI Urlscan.io connector charm the service."""

import pathlib

import ops

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiUrlscanConnectorCharm(OpenctiConnectorCharm):
    connector_type = "EXTERNAL_IMPORT"
    connector_charm_name = "urlscan"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    def _gen_env(self) -> dict[str, str]:
        env = super()._gen_env()
        env["CONNECTOR_SCOPE"] = "threatmatch"
        return env


if __name__ == "__main__":
    ops.main(OpenctiUrlscanConnectorCharm)