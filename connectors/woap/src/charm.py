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
        # "woap-connector" is the index the connector will use
        self.opensearch = OpenSearchRequires(
            self, 
            relation_name=RELATION_NAME, 
            index="woap-connector",
            extra_user_roles="admin"
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
        self._reconcile_connector()
        self.unit.status = ops.ActiveStatus("OpenSearch integrated and ready")
        # Log that we have received data
        logger.info("OpenSearch credentials received. Updating workload configuration.")

    def _on_relation_broken(self, event):
        self.unit.status = ops.BlockedStatus("Missing OpenSearch relation")
        # Calling replan will stop the service since gen_env won't have DB info
        self._reconcile_connector()
        

    def _gen_env(self) -> dict[str, str]:
        env = super()._gen_env()

        # Force woap
        env["CONNECTOR_SCOPE"] = "woap"

        rel = self.model.get_relation("opensearch-client")
        if rel and rel.app and rel.data.get(rel.app):
            rel_data = rel.data[rel.app]
            
            # Override Host with the endpoints from the databag
            endpoints = rel_data.get("endpoints", "")
            if endpoints:
                host_list = [e.split(':')[0] for e in endpoints.split(',')]
                env["OPENSEARCH_HOST"] = host_list[0]
                env["OPENSEARCH_PORT"] = "9200"

            #Resolve the Secret URI
            user_secret_uri = rel_data.get("secret-user")
            if user_secret_uri:
                # Resolve URI and use refresh=True 
                # This is mandatory to pull data across models
                secret = self.model.get_secret(id=user_secret_uri)
                content = secret.get_content(refresh=True)
                
                # Map the actual values
                env["OPENSEARCH_USER"] = content.get("username")
                env["OPENSEARCH_PASSWORD"] = content.get("password")

                logger.info("WOAP: Successfully populated environment from Relation secret.")
        else:
            logger.warning("WOAP: opensearch-client relation data not found or not yet synced.")

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

