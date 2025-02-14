# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI connector charm library."""

# The unique Charmhub library identifier, never change it
LIBID = "312661b5c30e4aeba8767706f3974899"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 2

import abc
import os
import pathlib
import urllib.parse
import uuid

import ops
import yaml


class NotReady(Exception):
    """The OpenCTI connector is not ready."""


class OpenctiConnectorCharm(ops.CharmBase, abc.ABC):
    """OpenCTI connector base charm."""

    @property
    @abc.abstractmethod
    def connector_type(self) -> str:
        """The OpenCTI connector type.

        Can be either "EXTERNAL_IMPORT", "INTERNAL_ENRICHMENT", "INTERNAL_IMPORT_FILE",
        "INTERNAL_EXPORT_FILE" or "STREAM".

        Returns: the connector type.
        """
        pass

    @property
    @abc.abstractmethod
    def charm_dir(self) -> pathlib.Path:
        """Return the charm directory (the one with charmcraft.yaml in it)."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._reconcile)
        self.framework.observe(self.on["opencti-connector"].relation_changed, self._reconcile)
        self.framework.observe(self.on.secret_changed, self._reconcile)
        self.framework.observe(self.on.upgrade_charm, self._reconcile)
        self.framework.observe(self.on[self.meta.name].pebble_ready, self._reconcile)

    @property
    def boolean_style(self) -> str:
        """Dictate how boolean-typed configurations should translate to environment variable values.

        The style should be either "json" for true/false or "python" for True/False.

        Returns: "json" or "python"
        """
        return "json"

    def _config_metadata(self) -> dict:
        """Get charm configuration metadata.

        Returns:
            The charm configuration metadata.

        Raises:
            RuntimeError: If charm metadata file doesn't exist.
        """
        config_file = self.charm_dir / "config.yaml"
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())["options"]
        config_file = self.charm_dir / "charmcraft.yaml"
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())["config"]["options"]
        raise RuntimeError("charm configuration metadata doesn't exist")

    def kebab_to_constant(self, name: str) -> str:
        """Convert kebab case to constant case

        Args:
            name: Kebab case name.

        Returns:
            Input in constant case.
        """
        return name.replace("-", "_").upper()

    def _check_config(self) -> None:
        """Check if required charm configurations are ready.

        Raises:
            NotReady: If some charm configurations isn't ready.
        """
        missing = []
        for config, config_meta in self._config_metadata().items():
            value = self.config.get(config)
            if value is None and config_meta.get("optional") is False:
                missing.append(config)
        if missing:
            raise NotReady("missing configurations: {}".format(", ".join(missing)))

    def _check_integration(self) -> None:
        """Check if required charm integrations are ready.

        Raises:
            NotReady: If some charm integrations isn't ready.
        """
        integration = self.model.get_relation("opencti-connector")
        if integration is None:
            raise NotReady("missing opencti-connector integration")

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
            self._check_integration()
            self._reconcile_integration()
            self._reconcile_connector()
            self.unit.status = ops.ActiveStatus()
        except NotReady as exc:
            self.unit.status = ops.WaitingStatus(str(exc))

    def _reconcile_integration(self) -> None:
        """Reconcile the charm integrations."""
        if self.unit.is_leader():
            integration = self.model.get_relation("opencti-connector")
            data = integration.data[self.app]
            data.update(
                {
                    "connector_charm_name": self.meta.name,
                    "connector_type": self.connector_type,
                }
            )
            if "connector_id" not in data:
                data["connector_id"] = str(uuid.uuid4())

    def _gen_env(self) -> dict[str, str]:
        """Generate environment variables for the opencti connector service.

        Returns:
            Environment variables.
        """
        integration = self.model.get_relation("opencti-connector")
        integration_data = integration.data[integration.app]
        opencti_url, opencti_token_id = (
            integration_data.get("opencti_url"),
            integration_data.get("opencti_token"),
        )
        if not opencti_url or not opencti_token_id:
            raise NotReady("waiting for opencti-connector integration")
        opencti_token_secret = self.model.get_secret(id=opencti_token_id)
        opencti_token = opencti_token_secret.get_content(refresh=True)["token"]
        environment = {
            "OPENCTI_URL": opencti_url,
            "OPENCTI_TOKEN": opencti_token,
            "CONNECTOR_ID": integration.data[self.app]["connector_id"],
            "CONNECTOR_NAME": self.app.name,
            "CONNECTOR_TYPE": self.connector_type,
        }

        for config, config_meta in self._config_metadata().items():
            value = self.config.get(config)
            if value is None:
                continue
            environment[self.kebab_to_constant(config)] = str(value)
            if self.boolean_style == "json" and isinstance(value, bool):
                environment[self.kebab_to_constant(config)] = str(value).lower()

        environment.update(self._get_proxy_environment(opencti_url))

        return environment

    def _get_proxy_environment(self, opencti_url: str) -> dict[str, str]:
        """Get proxy environment variables.

        Args:
            opencti_url: OpenCTI URL.

        Returns:
            proxy environment variables.
        """
        environment = {}
        http_proxy = os.environ.get("JUJU_CHARM_HTTP_PROXY")
        https_proxy = os.environ.get("JUJU_CHARM_HTTPS_PROXY")
        no_proxy = os.environ.get("JUJU_CHARM_NO_PROXY")
        if http_proxy:
            environment["HTTP_PROXY"] = http_proxy
            environment["http_proxy"] = http_proxy
        if https_proxy:
            environment["HTTPS_PROXY"] = https_proxy
            environment["https_proxy"] = https_proxy
        no_proxy_list = no_proxy.split(",") if no_proxy else []
        if http_proxy or https_proxy:
            opencti_host = urllib.parse.urlparse(opencti_url).hostname
            no_proxy_list.append(opencti_host)
            environment["NO_PROXY"] = ",".join(no_proxy_list)
            environment["no_proxy"] = ",".join(no_proxy_list)
        return environment

    def _reconcile_connector(self) -> None:
        """Reconcile connector service."""
        container = self.unit.get_container(self.meta.name)
        if not container.can_connect():
            raise NotReady("waiting for container ready")
        container.add_layer(
            "connector",
            layer=ops.pebble.LayerDict(
                summary=self.meta.name,
                description=self.meta.name,
                services={
                    "connector": {
                        "startup": "enabled",
                        "on-failure": "restart",
                        "override": "replace",
                        "command": "bash /entrypoint.sh",
                        "environment": self._gen_env(),
                    },
                },
            ),
            combine=True,
        )
        container.replan()
