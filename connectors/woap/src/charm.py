#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Note: This connector's files were not generated via scripts/gen_connector_charm.py
# due to its unique requirements and structure compared to the standard connector template.

"""
Juju Charm for the OpenCTI WOAP (Wazuh OpenSearch Alert Puller) connector.

This charm manages the lifecycle of the WOAP connector, which ingests Wazuh 
security alerts from OpenSearch into the OpenCTI platform.
"""

import pathlib
import re
import ops
import logging
from lib.charms.opencti.v0.opencti_connector import OpenctiConnectorCharm, Blocked, NotReady
from charms.data_platform_libs.v0.data_interfaces import OpenSearchRequires


logger = logging.getLogger(__name__)
OPENSEARCH_RELATION_NAME = "opensearch-client"
# Regex for ISO 8601 duration: 
# Matches 'P' followed by days/weeks OR 'PT' followed by hours/minutes/seconds
ISO8601_DURATION_REGEX = re.compile(
    r"^P(?!$)(?:\d+D)?(?:\d+W)?(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+S)?)?$"
)


class OpenctiWoapConnectorCharm(OpenctiConnectorCharm):
    connector_type = "EXTERNAL_IMPORT"

    def __init__(self, *args):
        super().__init__(*args)
        
        self.opensearch = OpenSearchRequires(
            self, 
            relation_name=OPENSEARCH_RELATION_NAME, 
            index="woap-connector",
            extra_user_roles="admin"
        )

        # Observing the event when OpenSearch provides the credentials/index
        self.framework.observe(self.opensearch.on.index_created, self._reconcile)
        self.framework.observe(self.on[OPENSEARCH_RELATION_NAME].relation_changed, self._reconcile)
        self.framework.observe(self.on[OPENSEARCH_RELATION_NAME].relation_broken, self._reconcile)

    @property
    def charm_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent.absolute()

    def _check_config(self) -> None:
        """Check if required charm configurations are ready.

        Raises:
            NotReady: If some charm configurations isn't ready.
        """
        # Check for missing required configurations
        super()._check_config()
        
        # Validate the 'connector-log-level' value
        log_level = self.config.get("connector-log-level")
        if log_level and log_level not in ["debug", "info", "warn", "error"]:
            raise NotReady("invalid connector-log-level value: {}".format(log_level))
        
        # Validate 'connector-duration-period' format
        duration = self.config.get("connector-duration-period")
        if duration and not ISO8601_DURATION_REGEX.match(duration):
            raise NotReady("invalid connector-duration-period value format: {}".format(duration))
        
        # Validate 'wazuh-min-severity' within valid values
        severity = self.config.get("wazuh-min-severity")
        if severity and not (1 <= int(severity) <= 15):
            raise NotReady(f"invalid wazuh-min-severity: {severity} (must be between 1 and 15)")
    
    def _reconcile(self, _) -> None:
        """Reconcile the charm."""
        try:
            if self.app.planned_units() != 1:
                self.unit.status = ops.BlockedStatus(
                    "connector charm cannot have multiple units, "
                    "scale down using the `juju scale` command"
                )
                return
            self._check_config()

            missing_requirements = []

            # Check OpenCTI Relation
            try:
                self._check_integration()
                self._reconcile_integration()
            except NotReady:
                missing_requirements.append("OpenCTI relation")

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
                self.stop_connector()
                return
            
            # If we reached here, everything is ready
            self._reconcile_connector()
            self.unit.status = ops.ActiveStatus()
            
        except NotReady as exc:
            self.unit.status = ops.WaitingStatus(str(exc))
        except Blocked as exc:
            self.unit.status = ops.BlockedStatus(str(exc))

    def stop_connector(self) -> None:
        """Stop the connector service."""
        container = self.unit.get_container(self.meta.name)
        if not container.can_connect():
            raise NotReady("waiting for container ready")

        try:
            container.stop("connector")
        except ops.pebble.ChangeError as exc:
            raise Blocked("failed to stop connector, will retry") from exc


    def _gen_env(self) -> dict[str, str]:
        env = super()._gen_env()

        # Set the connector scope
        env["CONNECTOR_SCOPE"] = "woap"

        rel = self.model.get_relation("opensearch-client")
        if rel and rel.app and rel.data.get(rel.app):
            rel_data = rel.data[rel.app]
            
            # Override Host with the endpoints from the databag
            endpoints = rel_data.get("endpoints", "")
            if endpoints:
                host_list = [e.split(':')[0] for e in endpoints.split(',')]
                env["OPENSEARCH_HOST"] = ",".join(host_list)
                env["OPENSEARCH_PORT"] = "9200"

            # Resolve the Secret URI
            user_secret_uri = rel_data.get("secret-user")
            if user_secret_uri:
                # Resolve URI and use refresh=True 
                # This is mandatory to pull data across models
                secret = self.model.get_secret(id=user_secret_uri)
                content = secret.get_content(refresh=True)
                env["OPENSEARCH_USER"] = content.get("username")
                env["OPENSEARCH_PASSWORD"] = content.get("password")

                logger.info("Successfully populated environment from Relation secret.")
        else:
            logger.warning("opensearch-client relation data not found or not yet synced.")

        # Assign log level
        log_level = self.config.get("connector-log-level")
        env["CONNECTOR_LOG_LEVEL"] = log_level

        return env


if __name__ == "__main__":
    ops.main(OpenctiWoapConnectorCharm)

