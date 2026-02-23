#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI WOAP connector charm the service."""

import pathlib

from lib.charms.opencti.v0.opencti_connector import Blocked, NotReady
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
        self.framework.observe(self.opensearch.on.index_created, self._reconcile)
        self.framework.observe(self.on[RELATION_NAME].relation_changed, self._reconcile)
        self.framework.observe(self.on[RELATION_NAME].relation_broken, self._reconcile)

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    VALID_LOG_LEVELS = {"debug", "info", "warn", "error"}

    def _reconcile(self, _=None) -> None:
        """Reconcile the charm."""
        try:
            if self.app.planned_units() != 1:
                self.unit.status = ops.BlockedStatus(
                    "connector charm cannot have multiple units, "
                    "scale down using the `juju scale` command"
                )
                return
            self._check_config()

            # Track what is missing
            missing_requirements = []

            # Check OpenCTI Relation
            opencti_rel = self.model.get_relation("opencti-connector")
            if not opencti_rel:
                missing_requirements.append("OpenCTI relation")
            else:
                self._reconcile_integration()

            # Check OpenSearch Relation
            opensearch_rel = self.model.get_relation("opensearch-client")
            if not opensearch_rel:
                missing_requirements.append("OpenSearch relation")
            elif not (opensearch_rel.app and opensearch_rel.data.get(opensearch_rel.app)):
                # Relation exists but no data/credentials yet
                missing_requirements.append("OpenSearch credentials")

            # Determine Status based on collected requirements
            if missing_requirements:
                status_msg = "Waiting for: " + ", ".join(missing_requirements)
                self.unit.status = ops.WaitingStatus(status_msg)
                try:
                    self.update_pebble(missing_requirements)
                except Exception:
                    pass
                #return here because we cannot configure the workload yet
                return
            
            #If we reached here, everything is ready
            self._reconcile_connector()
            self.unit.status = ops.ActiveStatus()
            
        except NotReady as exc:
            self.unit.status = ops.WaitingStatus(str(exc))
        except Blocked as exc:
            self.unit.status = ops.BlockedStatus(str(exc))

    def update_pebble(self, missing_requirements) -> None:
        """Zero out relation-based configuration and stop the service."""
        container = self.unit.get_container(self.meta.name)
        if not container.can_connect():
            return
        
        try:
            # wrapping this because super()._gen_env() will raise NotReady 
            # if the OpenCTI relation is gone.
            env = super()._gen_env()
        except NotReady:
            env = {}

        for requirement in missing_requirements:
            if requirement == "OpenCTI relation":
                # Remove all OpenCTI related environment variables
                env.pop("OPENCTI_URL", None)
                env.pop("OPENCTI_TOKEN", None)
            elif requirement == "OpenSearch relation":
                # Remove all OpenSearch related environment variables
                env.pop("OPENSEARCH_HOST", None)
                env.pop("OPENSEARCH_PORT", None)
                env.pop("OPENSEARCH_USER", None)
                env.pop("OPENSEARCH_PASSWORD", None)
            elif requirement == "OpenSearch credentials":
                # Remove all OpenSearch credential environment variables
                env.pop("OPENSEARCH_USER", None)
                env.pop("OPENSEARCH_PASSWORD", None)

        #Create a layer that disables the service and clears the env
        cleanup_layer = ops.pebble.LayerDict(
            services={
                "connector": {
                    "override": "replace",
                    "startup": "disabled",  # Stop the service from running/restarting
                    "environment": env,
                }
            }
        )

        #Push the layer and replan
        container.add_layer("connector", cleanup_layer, combine=True)
        container.replan()
        logger.info("Cleaning up Pebble layer due to missing requirements")


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

