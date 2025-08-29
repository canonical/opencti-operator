#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI Export STIX File connector charm the service."""

import pathlib

import ops

import logging
logger = logging.getLogger(__name__)

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiExportFileStixConnectorCharm(OpenctiConnectorCharm):
    connector_type = "INTERNAL_EXPORT_FILE"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    

if __name__ == "__main__":
    ops.main(OpenctiExportFileStixConnectorCharm)
