# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import pathlib

import jinja2
import requests
import markdown
import yaml

from bs4 import BeautifulSoup

DEFAULT_CONFIG = {
    "connector-scope": {"type": "string", "description": "connector scope"},
    "connector-log-level": {"type": "string", "description": "connector log level"},
}


def constant_to_kebab(string: str) -> str:
    return string.replace("_", "-").lower()


def kebab_to_pascal(string: str) -> str:
    words = string.split("-")
    return "".join(word.capitalize() for word in words)


def extract_configs(doc_url: str) -> dict:
    response = requests.get(doc_url, timeout=10)
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
        is_mandatory = is_mandatory == "yes" and row["default"] != "/"
        description = row["description"]
        if not is_mandatory:
            description = "(optional) " + description
        config_type = "int" if (row["example"].isdigit() or row["default"].isdigit()) else "string"
        result[constant_to_kebab(name)] = {
            "description": description,
            "type": config_type,
        }
    return result


def render_template(
    name,
    connector_type,
    version,
    display_name,
    config,
    template_dir: pathlib.Path = pathlib.Path("connector-template"),
    output_dir: pathlib.Path = pathlib.Path("connectors"),
):
    if "_" in name or name.lower() != name:
        raise ValueError(f"connector name should be in kebab case: {name}")
    for source in template_dir.glob("**/*"):
        file = source.relative_to(template_dir)
        if "__pycache__" in str(file) or source.is_dir():
            continue
        output = output_dir / name / file
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
                config=yaml.safe_dump({"config": {"options": config}}),
            ),
            encoding="utf-8",
        )
    (output_dir / name / "lib/charms/opencti/v0").mkdir(parents=True, exist_ok=True)
    (output_dir / name / "lib/charms/opencti/v0/opencti_connector.py").write_bytes(
        pathlib.Path("lib/charms/opencti/v0/opencti_connector.py").read_bytes()
    )
    (output_dir / name / "src/charm.py").chmod(0o755)


def render(connector: str) -> None:
    match connector:
        case "crowdstrike":
            render_template(
                name="crowdstrike",
                connector_type="EXTERNAL_IMPORT",
                version="6.4.1",
                display_name="CrowdStrike",
                config=extract_configs(
                    "https://raw.githubusercontent.com/OpenCTI-Platform/connectors/refs/heads/master/external-import/crowdstrike/README.md"
                ),
            )
        case "export-file-csv":
            render_template(
                name="export-file-csv",
                connector_type="INTERNAL_EXPORT_FILE",
                version="6.4.1",
                display_name="Export CSV File",
                config=DEFAULT_CONFIG,
            )


render("export-file-csv")
