#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI IpInfo connector charm the service."""

import pathlib

import ops

import logging
logger = logging.getLogger(__name__)

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiIpinfoConnectorCharm(OpenctiConnectorCharm):
    connector_type = "INTERNAL_ENRICHMENT"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    

if __name__ == "__main__":
    ops.main(OpenctiIpinfoConnectorCharm)
