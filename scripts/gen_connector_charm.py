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

CHARM_MANAGED_ENV = {
    "OPENCTI_URL",
    "OPENCTI_TOKEN",
    "CONNECTOR_ID",
    "CONNECTOR_NAME",
}


def constant_to_kebab(string: str) -> str:
    return string.replace("_", "-").lower()


def kebab_to_pascal(string: str) -> str:
    words = string.split("-")
    return "".join(word.capitalize() for word in words)


def kebab_to_snake(string: str) -> str:
    return string.replace("-", "_")


def extract_tables(doc) -> list[dict[str, str]]:
    html = markdown.markdown(doc, extensions=["tables"])
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
    return rows


def extract_crowdstrike_configs(doc_url: str) -> dict:
    response = requests.get(doc_url, timeout=10)
    response.raise_for_status()
    rows = extract_tables(response.text)
    result = {}
    for row in rows:
        name = row["docker environment variable"]
        if name in CHARM_MANAGED_ENV:
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


def extract_misp_feed_configs(doc_url: str) -> dict:
    response = requests.get(doc_url, timeout=10)
    response.raise_for_status()
    rows = extract_tables(response.text)
    result = {}
    for row in rows:
        name = row["docker environment variable"]
        if name in CHARM_MANAGED_ENV:
            continue
        is_mandatory = row["mandatory"].lower()
        assert is_mandatory in ("yes", "no")
        is_mandatory = is_mandatory == "yes"
        description = row["description"]
        if not is_mandatory:
            description = "(optional) " + description
        config_type = "boolean" if row["default"].lower() in ("true", "false") else "string"
        result[constant_to_kebab(name)] = {
            "description": description,
            "type": config_type,
        }
    result.update(DEFAULT_CONFIG)
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
    generate_entrypoint: str = "",
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
                generate_entrypoint=generate_entrypoint,
            ),
            encoding="utf-8",
        )
    (charm_dir / "lib/charms/opencti/v0").mkdir(parents=True, exist_ok=True)
    (charm_dir / "lib/charms/opencti/v0/opencti_connector.py").write_bytes(
        pathlib.Path("lib/charms/opencti/v0/opencti_connector.py").read_bytes()
    )
    (charm_dir / "src/charm.py").chmod(0o755)


def render(connector: str) -> None:
    version = "6.4.5"
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
    if connector == "sekoia" or connector == "all":
        render_template(
            name="sekoia",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="Sekoia.io",
            config={
                "sekoia-base-url": {
                    "description": "Sekoia base url",
                    "type": "string",
                    "default": "https://api.sekoia.io",
                },
                "sekoia-api-key": {
                    "description": "Sekoia API key",
                    "type": "string",
                },
                "sekoia-collection": {
                    "description": "Sekoia collection",
                    "type": "string",
                },
                "sekoia-start-data": {
                    "description": "(optional) the date to start consuming data from. Maybe in the formats YYYY-MM-DD or YYYY-MM-DDT00:00:00",
                    "type": "string",
                },
                "sekoia-create-observables": {
                    "description": "create observables from indicators",
                    "type": "boolean",
                    "default": True,
                },
            },
            generate_entrypoint="echo 'cd /opt/opencti-connector-sekoia; python3 sekoia.py' > entrypoint.sh",
        )
    if connector == "" or connector == "all":
        render_template(
            name="virustotal-livehunt-notifications",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="VirusTotal Livehunt Notifications",
            config={
                "virustotal-livehunt-notifications-api-key": {
                    "description": "Private API Key",
                    "type": "string",
                },
                "virustotal-livehunt-notifications-interval-sec": {
                    "description": "Time to wait in seconds between subsequent requests",
                    "type": "int",
                },
                "virustotal-livehunt-notifications-create-alert": {
                    "description": "Set to true to create alerts",
                    "type": "boolean",
                },
                "virustotal-livehunt-notifications-extensions": {
                    "description": "(optional) Comma separated filter to only download files matching these extensions",
                    "type": "string",
                },
                "virustotal-livehunt-notifications-min-file-size": {
                    "description": "(optional) Don't download files smaller than this many bytes",
                    "type": "int",
                },
                "virustotal-livehunt-notifications-max-file-size": {
                    "description": "(optional) Don't download files larger than this many bytes",
                    "type": "int",
                },
                "virustotal-livehunt-notifications-max-age-days": {
                    "description": "Only create the alert if the first submission of the file is not older than `max_age_days`",
                    "type": "int",
                },
                "virustotal-livehunt-notifications-min-positives": {
                    "description": "(optional) Don't download files with less than this many vendors marking malicious",
                    "type": "int",
                },
                "virustotal-livehunt-notifications-create-file": {
                    "description": "Set to true to create file object linked to the alerts",
                    "type": "boolean",
                },
                "virustotal-livehunt-notifications-upload-artifact": {
                    "description": "Set to true to upload the file to opencti",
                    "type": "boolean",
                },
                "virustotal-livehunt-notifications-create-yara-rule": {
                    "description": "Set to true to create yara rule linked to the alert and the file",
                    "type": "boolean",
                },
                "virustotal-livehunt-notifications-delete-notification": {
                    "description": "Set to true to remove livehunt notifications",
                    "type": "boolean",
                },
                "virustotal-livehunt-notifications-filter-with-tag": {
                    "description": "Filter livehunt notifications with this tag",
                    "type": "string",
                },
            },
        )
    if connector == "abuseipdb-ipblacklist" or connector == "all":
        render_template(
            name="abuseipdb-ipblacklist",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="abuseipdb ipblacklist",
            config={
                "abuseipdb-url": {
                    "description": "the Abuse IPDB URL",
                    "type": "string",
                    "default": "https://api.abuseipdb.com/api/v2/blacklist",
                },
                "abuseipdb-api-key": {
                    "description": "Abuse IPDB API KEY",
                    "type": "string",
                },
                "abuseipdb-score": {
                    "description": "AbuseIPDB Score Limitation",
                    "type": "int",
                },
                "abuseipdb-limit": {
                    "description": "limit number of result itself",
                    "type": "int",
                },
                "abuseipdb-interval": {
                    "description": "interval between 2 collect itself",
                    "type": "int",
                },
            },
        )
    if connector == "misp-feed" or connector == "all":
        render_template(
            name="misp-feed",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="MISP Source",
            config=extract_misp_feed_configs(
                "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
                f"/refs/tags/{version}/external-import/misp-feed/README.md"
            ),
        )
    if connector == "malwarebazaar-recent-additions" or connector == "all":
        render_template(
            name="malwarebazaar-recent-additions",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="MalwareBazaar Recent Additions",
            config={
                "connector-log-level": {
                    "description": "The log level for the connector",
                    "type": "string",
                },
                "malwarebazaar-recent-additions-api-url": {
                    "description": "The API URL for MalwareBazaar Recent Additions",
                    "type": "string",
                },
                "malwarebazaar-recent-additions-cooldown-seconds": {
                    "description": "Time to wait in seconds between subsequent requests",
                    "type": "integer",
                },
                "malwarebazaar-recent-additions-include-tags": {
                    "description": "(optional) Only download files if any tag matches. (Comma separated)",
                    "type": "string",
                },
                "malwarebazaar-recent-additions-include-reporters": {
                    "description": "(optional) Only download files uploaded by these reporters. (Comma separated)",
                    "type": "string",
                },
                "malwarebazaar-recent-additions-labels": {
                    "description": "(optional) Labels to apply to uploaded Artifacts. (Comma separated)",
                    "type": "string",
                },
                "malwarebazaar-recent-additions-labels-color": {
                    "description": "Color to use for labels",
                    "type": "string",
                },
            },
        )
    if connector == "cisa-known-exploited-vulnerabilities" or connector == "all":
        render_template(
            name="cisa-known-exploited-vulnerabilities",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="CISA Known Exploited Vulnerabilities",
            config=extract_misp_feed_configs(
                "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
                f"/refs/tags/{version}/external-import/cisa-known-exploited-vulnerabilities/README.md"
            ),
        )
    if connector == "urlscan" or connector == "all":
        render_template(
            name="urlscan",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="Urlscan.io",
            config={
                "connector-confidence-level": {
                    "description": "The default confidence level for created relationships (0 -> 100).",
                    "type": "integer",
                },
                "connector-update-existing-data": {
                    "description": "If an entity already exists, update its attributes with information provided by this connector.",
                    "type": "boolean",
                },
                "connector-log-level": {
                    "description": "The log level for this connector, could be `debug`, `info`, `warn` or `error` (less verbose).",
                    "type": "string",
                },
                "connector-create-indicators": {
                    "description": "(optional) Create indicators for each observable processed.",
                    "type": "boolean",
                },
                "connector-tlp": {
                    "description": "(optional) The TLP to apply to any indicators and observables, this could be `white`,`green`,`amber` or `red`",
                    "type": "string",
                },
                "connector-labels": {
                    "description": "(optional) Comma delimited list of labels to apply to each observable.",
                    "type": "string",
                },
                "connector-interval": {
                    "description": "(optional) An interval (in seconds) for data gathering from Urlscan.",
                    "type": "integer",
                },
                "connector-lookback": {
                    "description": "(optional) How far to look back in days if the connector has never run or the last run is older than this value. Default is 3. You should not go above 7.",
                    "type": "integer",
                },
                "urlscan-url": {"description": "The Urlscan URL.", "type": "string"},
                "urlscan-api-key": {"description": "The Urlscan client secret.", "type": "string"},
                "urlscan-default-x-opencti-score": {
                    "description": "(optional) The default x_opencti_score to use across observable/indicator types. Default is 50.",
                    "type": "integer",
                },
                "urlscan-x-opencti-score-domain": {
                    "description": "(optional) The x_opencti_score to use across Domain-Name observable and indicators. Defaults to default score.",
                    "type": "integer",
                },
                "urlscan-x-opencti-score-url": {
                    "description": "(optional) The x_opencti_score to use across Url observable and indicators. Defaults to default score.",
                    "type": "integer",
                },
            },
            charm_override=textwrap.dedent(
                """\
            def _gen_env(self) -> dict[str, str]:
                env = super()._gen_env()
                env["CONNECTOR_SCOPE"] = "threatmatch"
                return env
            """
            ),
        )
    if connector == "cyber-campaign-collection" or connector == "all":
        render_template(
            name="cyber-campaign-collection",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="APT & Cybercriminals Campaign Collection",
            config={
                "connector-scope": {
                    "description": "The data scope of the connector.",
                    "type": "string",
                },
                "connector-run-and-terminate": {
                    "description": "Whether the connector should run and terminate after execution.",
                    "type": "boolean",
                },
                "connector-log-level": {
                    "description": "The log level for the connector.",
                    "type": "string",
                },
                "cyber-monitor-github-token": {
                    "description": "(optional) If not provided, rate limit will be very low.",
                    "type": "string",
                },
                "cyber-monitor-from-year": {
                    "description": "The starting year for monitoring cyber campaigns.",
                    "type": "integer",
                },
                "cyber-monitor-interval": {
                    "description": "The interval in days, must be strictly greater than 1.",
                    "type": "integer",
                },
            },
        )
    if connector == "urlscan-enrichment" or connector == "all":
        render_template(
            name="urlscan-enrichment",
            connector_type="INTERNAL_ENRICHMENT",
            version=version,
            display_name="URLScan Enrichment",
            config=extract_misp_feed_configs(
                "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
                f"/refs/tags/{version}/internal-enrichment/urlscan-enrichment/README.md"
            ),
        )
    if connector == "alienvault" or connector == "all":
        render_template(
            name="alienvault",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="AlienVault",
            config=extract_misp_feed_configs(
                "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
                f"/refs/tags/{version}/external-import/alienvault/README.md"
            ),
        )
    if connector == "vxvault" or connector == "all":
        render_template(
            name="vxvault",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="VXVault",
            config={
                "connector-scope": {
                    "description": "The scope of the connector",
                    "type": "string",
                    "default": "vxvault",
                },
                "connector-log-level": {
                    "description": "(optional) The log level of the connector",
                    "type": "string",
                },
                "vxvault-url": {
                    "description": "The URL for VX Vault URL list",
                    "type": "string",
                    "default": "https://vxvault.net/URL_List.php",
                },
                "vxvault-create-indicators": {
                    "description": "(optional) Whether to create indicators from the VX Vault URL list",
                    "type": "boolean",
                },
                "vxvault-interval": {
                    "description": "In days, must be strictly greater than 1",
                    "type": "integer",
                },
                "vxvault-ssl-verify": {
                    "description": "(optional) Whether to verify SSL certificates",
                    "type": "boolean",
                },
            },
        )
    if connector == "mitre" or connector == "all":
        render_template(
            name="mitre",
            connector_type="EXTERNAL_IMPORT",
            version=version,
            display_name="MITRE Datasets",
            config={
                "mitre-interval": {
                    "description": "Number of the days between each MITRE datasets collection.",
                    "type": "integer",
                },
                "mitre-remove-statement-marking": {
                    "description": "Remove the statement MITRE marking definition.",
                    "type": "boolean",
                },
                "mitre-enterprise-file-url": {"description": "Resource URL", "type": "string"},
                "mitre-mobile-attack-file-url": {"description": "Resource URL", "type": "string"},
                "mitre-ics-attack-file-url": {"description": "Resource URL", "type": "string"},
                "mitre-capec-file-url": {
                    "description": "(optional) Resource URL",
                    "type": "string",
                },
                **DEFAULT_CONFIG,
            },
            generate_entrypoint="echo 'cd /opt/opencti-connector-mitre; python3 connector.py' > entrypoint.sh",
        )
    if connector == "import-document" or connector == "all":
        render_template(
            name="import-document",
            connector_type="INTERNAL_IMPORT_FILE",
            version=version,
            display_name="Document Import",
            config={
                "connector-only-contextual": {
                    "description": "true Only extract data related to an entity (a report, a threat actor, etc.)",
                    "type": "boolean",
                },
                "connector-auto": {
                    "description": "false Enable/disable auto import of report file",
                    "type": "boolean",
                },
                "connector-scope": {
                    "description": "Supported file types: 'application/pdf','text/plain','text/html', 'text/csv,'text/markdown'",
                    "type": "string",
                },
                "connector-confidence-level": {
                    "description": "The default confidence level for created sightings (a number between 1 and 4).",
                    "type": "integer",
                },
                "connector-log-level": {
                    "description": "The log level for this connector, could be debug, info, warn or error (less verbose).",
                    "type": "string",
                },
                "import-document-create-indicator": {
                    "description": "Create an indicator for each extracted observable",
                    "type": "boolean",
                },
            },
        )
    if connector == "import-file-stix" or connector == "all":
        render_template(
            name="import-file-stix",
            connector_type="INTERNAL_IMPORT_FILE",
            version=version,
            display_name="Import File Stix",
            config={
                "connector-validate-before-import": {
                    "description": "(optional) Validate any bundle before import",
                    "type": "boolean",
                },
                "connector-scope": {
                    "description": "The accepted file types for import",
                    "type": "string",
                },
                "connector-auto": {
                    "description": "(optional) Enable/disable auto-import of file",
                    "type": "boolean",
                },
                "connector-confidence-level": {
                    "description": "(optional) From 0 (Unknown) to 100 (Fully trusted)",
                    "type": "integer",
                },
                "connector-log-level": {
                    "description": "The logging level of the connector",
                    "type": "string",
                },
            },
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
