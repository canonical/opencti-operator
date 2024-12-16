# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import operator
import pathlib
import textwrap

import jinja2
import requests
import markdown
import yaml

from bs4 import BeautifulSoup

DEFAULT_CONFIG = {
    "connector-scope": {"type": "string", "description": "connector scope"},
    "connector-log-level": {
        "type": "string",
        "description": "determines the verbosity of the logs. Options are debug, info, warn, or error",
        "default": "info",
    },
}


def constant_to_kebab(string: str) -> str:
    return string.replace("_", "-").lower()


def kebab_to_pascal(string: str) -> str:
    words = string.split("-")
    return "".join(word.capitalize() for word in words)


def kebab_to_snake(string: str) -> str:
    return string.replace("-", "_")


def extract_crowdstrike_configs(doc_url: str) -> dict:
    response = requests.get(doc_url, timeout=10)
    response.raise_for_status()
    html = markdown.markdown(response.text, extensions=["tables"])
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    rows = []

    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        for row in table.find_all("tr"):
            cells = row.find_all(["td"])
            if len(cells) == len(headers):
                row_data = {
                    headers[i].lower(): cells[i].get_text(strip=True) for i in range(len(headers))
                }
                rows.append(row_data)

    result = {}
    for row in rows:
        name = row["docker environment variable"]
        if name in (
            "OPENCTI_URL",
            "OPENCTI_TOKEN",
            "CONNECTOR_ID",
            "CONNECTOR_NAME",
        ):
            continue
        is_mandatory = row["mandatory"].lower()
        assert is_mandatory in ("yes", "no")
        is_mandatory = is_mandatory == "yes"
        description = row["description"]
        if not is_mandatory:
            description = "(optional) " + description
        config_type = "int" if (row["example"].isdigit() or row["default"].isdigit()) else "string"
        result[constant_to_kebab(name)] = {
            "description": description,
            "type": config_type,
        }
    result.update(DEFAULT_CONFIG)
    del result["connector-scope"]
    return result


def sort_config(options):
    mandatory = {
        k: v
        for k, v in options.items()
        if not v["description"].startswith("(optional)") and "default" not in v
    }
    mandatory_with_default = {
        k: v
        for k, v in options.items()
        if not v["description"].startswith("(optional)") and "default" in v
    }
    optional = {
        k: v for k, v in options.items() if k not in mandatory and k not in mandatory_with_default
    }
    sorted_options = {}
    for k, v in sorted(mandatory.items(), key=operator.itemgetter(0)):
        sorted_options[k] = v
    for k, v in sorted(mandatory_with_default.items(), key=operator.itemgetter(0)):
        sorted_options[k] = v
    for k, v in sorted(optional.items(), key=operator.itemgetter(0)):
        sorted_options[k] = v
    return sorted_options


def render_template(
    name,
    connector_type,
    version,
    display_name,
    config,
    charm_override: str = "",
    template_dir: pathlib.Path = pathlib.Path("connector-template"),
    output_dir: pathlib.Path = pathlib.Path("connectors"),
):
    if "_" in name or name.lower() != name:
        raise ValueError(f"connector name should be in kebab case: {name}")
    charm_dir = output_dir / kebab_to_snake(name)
    for source in template_dir.glob("**/*"):
        file = source.relative_to(template_dir)
        if "__pycache__" in str(file) or source.is_dir():
            continue
        output = charm_dir / file
        output.parent.mkdir(exist_ok=True, parents=True)
        if not str(file).endswith(".j2"):
            output.write_bytes(source.read_bytes())
            continue
        output = pathlib.Path(str(output).removesuffix(".j2"))
        template = jinja2.Template(source.read_text())
        template.globals["kebab_to_pascal"] = kebab_to_pascal
        template.globals["constant_to_kebab"] = constant_to_kebab
        output.write_text(
            template.render(
                connector_name=name,
                connector_type=connector_type,
                version=version,
                display_name=display_name,
                config=yaml.safe_dump(
                    {"config": {"options": sort_config(config)}}, width=99999, sort_keys=False
                ),
                charm_override=charm_override,
            ),
            encoding="utf-8",
        )
    (charm_dir / "lib/charms/opencti/v0").mkdir(parents=True, exist_ok=True)
    (charm_dir / "lib/charms/opencti/v0/opencti_connector.py").write_bytes(
        pathlib.Path("lib/charms/opencti/v0/opencti_connector.py").read_bytes()
    )
    (charm_dir / "src/charm.py").chmod(0o755)


def render(connector: str) -> None:
    version = "6.4.1"
    if connector == "crowdstrike" or connector == "all":
        render_template(
            name="crowdstrike",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="CrowdStrike",
            config=extract_crowdstrike_configs(
                "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
                f"/refs/tags/{version}/external-import/crowdstrike/README.md"
            ),
            charm_override=textwrap.dedent(
                """\
                def _gen_env(self) -> dict[str, str]:
                    env = super()._gen_env()
                    env["CONNECTOR_SCOPE"] = "crowdStrike"
                    return env
                """
            ),
        )
    if connector == "export-file-csv" or connector == "all":
        render_template(
            name="export-file-csv",
            connector_type="INTERNAL_EXPORT_FILE",
            version=version,
            display_name="Export CSV File",
            config=DEFAULT_CONFIG,
        )
    if connector == "export-file-txt" or connector == "all":
        render_template(
            name="export-file-txt",
            connector_type="INTERNAL_EXPORT_FILE",
            version=version,
            display_name="Export TXT File",
            config=DEFAULT_CONFIG,
        )
    if connector == "export-file-stix" or connector == "all":
        render_template(
            name="export-file-stix",
            connector_type="INTERNAL_EXPORT_FILE",
            version=version,
            display_name="Export STIX File",
            config=DEFAULT_CONFIG,
        )


render("all")
