# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI connector charm library."""

# The unique Charmhub library identifier, never change it
LIBID = "bced1658f20f49d28b88f61f83c2d233"

LIBAPI = 0
LIBPATCH = 1

import abc
import pathlib
import uuid

import ops
import yaml


class NotReady(Exception):
    """The OpenCTI connector is not ready."""


class OpenctiConnectorCharm(ops.CharmBase, abc.ABC):
    """OpenCTI connector base charm."""

    @property
    @abc.abstractmethod
    def connector_charm_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def connector_type(self) -> str:
        pass

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._reconcile)
        self.framework.observe(self.on["opencti-connector"].relation_changed, self._reconcile)
        self.framework.observe(self.on.secret_changed, self._reconcile)
        self.framework.observe(self.on.upgrade_charm, self._reconcile)
        self.framework.observe(self.on[self._charm_name].pebble_ready, self._reconcile)

    @property
    def _charm_name(self):
        config_file = pathlib.Path("metadata.yaml")
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())["name"]
        config_file = pathlib.Path("charmcraft.yaml")
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())["name"]
        raise RuntimeError("charm metadata doesn't exist")

    def _config_metadata(self) -> dict:
        """Get charm configuration metadata.

        Returns:
            The charm configuration metadata.

        Raises:
                ValueError: if the charm_dir input is invalid.
        """
        config_file = pathlib.Path("config.yaml")
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())["options"]
        config_file = pathlib.Path("charmcraft.yaml")
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())["config"]["options"]
        raise RuntimeError("charm configuration metadata doesn't exist")

    def kebab_to_constant(self, name: str) -> str:
        return name.replace("-", "_").upper()

    def _check_config(self):
        missing = []
        for config, config_meta in self._config_metadata().items():
            value = self.config.get(config)
            if value is None and not config_meta["description"].strip().startswith("(optional)"):
                missing.append(config)
        if missing:
            raise NotReady("missing configurations: {}".format(", ".join(missing)))

    def _check_integration(self):
        integration = self.model.get_relation("opencti-connector")
        if integration is None:
            raise NotReady("missing opencti-connector integration")

    def _reconcile(self, _):
        try:
            self._check_config()
            self._check_integration()
            self._reconcile_integration()
            self._reconcile_connector()
            self.unit.status = ops.ActiveStatus()
        except NotReady as exc:
            self.unit.status = ops.WaitingStatus(str(exc))

    def _reconcile_integration(self):
        if self.unit.is_leader():
            integration = self.model.get_relation("opencti-connector")
            data = integration.data[self.app]
            data.update(
                {
                    "connector_charm_name": self.connector_charm_name,
                    "connector_type": self.connector_type,
                }
            )
            if "connector_id" not in data:
                data["connector_id"] = str(uuid.uuid4())

    def _gen_env(self) -> dict[str, str]:
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
        return environment

    def _reconcile_connector(self):
        container = self.unit.get_container(self._charm_name)
        container.add_layer(
            "connector",
            layer=ops.pebble.LayerDict(
                summary=self._charm_name,
                description=self._charm_name,
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
