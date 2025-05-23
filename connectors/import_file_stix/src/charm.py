#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI Import File Stix connector charm the service."""

import pathlib

import ops

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm


class OpenctiImportFileStixConnectorCharm(OpenctiConnectorCharm):
    connector_type = "INTERNAL_IMPORT_FILE"

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    

if __name__ == "__main__":
    ops.main(OpenctiImportFileStixConnectorCharm)
