#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI MISP Source connector charm the service."""

import pathlib

import ops

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiMispFeedConnectorCharm(OpenctiConnectorCharm):
    connector_type = "EXTERNAL_IMPORT"
    connector_charm_name = "misp-feed"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    

if __name__ == "__main__":
    ops.main(OpenctiMispFeedConnectorCharm)