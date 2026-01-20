#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI WOAP connector charm the service."""

import pathlib

import ops

import logging
logger = logging.getLogger(__name__)
RELATION_NAME = "opensearch-client"

from charms.opencti.v0.opencti_connector import OpenctiConnectorCharm
from charms.data_platform_libs.v0.data_interfaces import OpenSearchRequires


class OpenctiWoapConnectorCharm(OpenctiConnectorCharm):
    connector_type = "EXTERNAL_IMPORT"

    def __init__(self, *args):
        super().__init__(*args)
        
        # 1. Initializing OpenSearch integration
        # "opensearch" must match the name in your charmcraft.yaml requires section
        # "wazuh-alerts-*" is the index the connector will use
        self.opensearch = OpenSearchRequires(
            self, 
            relation_name=RELATION_NAME, 
            index="wazuh-alerts-*"
        )

        # 2. Observe the event when OpenSearch provides the credentials/index
        self.framework.observe(self.opensearch.on.index_created, self._on_opensearch_ready)

        self.framework.observe(self.on[RELATION_NAME].relation_broken, self._on_relation_broken)

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    VALID_LOG_LEVELS = {"debug", "info", "warn", "error"}

    def _on_opensearch_ready(self, event):
        """Triggered when the OpenSearch relation is joined and the index is ready."""
        # By calling 'replan', the charm calls _gen_env, notices the new 
        # credentials, updates the container, and restarts the service.
        self.container.replan()
        self.unit.status = ops.ActiveStatus("OpenSearch integrated and ready")
        # Log that we have received data
        logger.info("OpenSearch credentials received. Updating workload configuration.")

    def _on_relation_broken(self, event):
        self.unit.status = ops.BlockedStatus("Missing OpenSearch relation")
        # Calling replan will stop the service since gen_env won't have DB info
        self.container.replan()
        

    def _gen_env(self) -> dict[str, str]:
        env = super()._gen_env()

        # Force woap
        env["CONNECTOR_SCOPE"] = "woap"

        # Dynamically adding OpenSearch credentials if they are available
        creds = self.opensearch.fetch_relation_data()
        if creds:
            # Getting the first relation ID available
            rid = list(creds.keys())[0]
            rel_data = creds[rid]
            
            env["OPENSEARCH_HOST"] = rel_data.get("endpoints", "")
            #Accessing the 'secret-user' URI
            user_secret_uri = rel_data.get("secret-user")
            if user_secret_uri:
                # Resolve the secret URI to get the actual content
                secret = self.model.get_secret(id=user_secret_uri)
                content = secret.get_content() # This returns a dict
                
                # The keys inside the secret are defined by the OpenSearch charm
                env["OPENSEARCH_USER"] = content.get("username")
                env["OPENSEARCH_PASSWORD"] = content.get("password")
                
            logger.info("OpenSearch credentials added to environment map.")

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
    ops.main(OpenctiWoapConnectorCharm)
