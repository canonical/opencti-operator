# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import operator
import pathlib
import textwrap
from typing import Callable

import jinja2
import requests
import markdown
import yaml

from bs4 import BeautifulSoup

_CONNECTOR_GENERATORS = {}


def connector_generator(name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        _CONNECTOR_GENERATORS[name] = func
        return func

    return decorator


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


def extract_template_configs(doc_url: str) -> dict:
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
        config_type = "string"
        if row["default"].lower() in ("true", "false"):
            config_type = "boolean"
        if row["default"].isdigit():
            config_type = "int"
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
    *,
    name,
    connector_type,
    version,
    display_name,
    config,
    output_dir,
    connector_name: str | None = None,
    display_name_short: str | None = None,
    charm_override: str = "",
    generate_entrypoint: str = "",
    install_location: str | None = None,
    template_dir: pathlib.Path = pathlib.Path("connector-template"),
):
    if "_" in name or name.lower() != name:
        raise ValueError(f"connector name should be in kebab case: {name}")
    connector_name = connector_name or name
    display_name_short = display_name_short or display_name
    output_dir.mkdir(exist_ok=True)
    for source in template_dir.glob("**/*"):
        file = source.relative_to(template_dir)
        if "__pycache__" in str(file):
            continue
        output = output_dir / file
        if source.is_dir():
            output.mkdir(exist_ok=True)
            continue
        if not str(file).endswith(".j2"):
            output.write_bytes(source.read_bytes())
            continue
        output = pathlib.Path(str(output).removesuffix(".j2"))
        template = jinja2.Template(source.read_text())
        template.globals["kebab_to_pascal"] = kebab_to_pascal
        template.globals["constant_to_kebab"] = constant_to_kebab
        output.write_text(
            template.render(
                name=name,
                connector_name=connector_name,
                connector_type=connector_type,
                version=version,
                display_name=display_name,
                display_name_short=(
                    display_name if display_name_short is None else display_name_short
                ),
                config=yaml.safe_dump(
                    {"config": {"options": sort_config(config)}}, width=99999, sort_keys=False
                ),
                charm_override=charm_override,
                install_location=(
                    install_location if install_location else f"opencti-connector-{connector_name}"
                ),
                generate_entrypoint=generate_entrypoint,
            ),
            encoding="utf-8",
        )
    (output_dir / "lib/charms/opencti/v0").mkdir(parents=True, exist_ok=True)
    (output_dir / "lib/charms/opencti/v0/opencti_connector.py").write_bytes(
        pathlib.Path("lib/charms/opencti/v0/opencti_connector.py").read_bytes()
    )
    (output_dir / "src/charm.py").chmod(0o755)


@connector_generator("abuseipdb-ipblacklist")
def generate_abuseipdb_ipblacklist_connector(location: pathlib.Path, version: str):
    """Generate opencti abuseipdb-ipblacklist connector

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/abuseipdb-ipblacklist
    """
    render_template(
        name="abuseipdb-ipblacklist",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="abuseipdb ipblacklist",
        output_dir=location,
        config={
            **DEFAULT_CONFIG,
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
        install_location="abuseipdb-ipblacklist",
    )


@connector_generator("alienvault")
def generate_alienvault_connector(location: pathlib.Path, version: str):
    """Generate opencti alienvault connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/alienvault
    """
    config = extract_template_configs(
        "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
        f"/refs/tags/{version}/external-import/alienvault/README.md"
    )
    config["alienvault-interval-sec"] = {
        "description": "alienvault interval seconds",
        "type": "int",
    }
    render_template(
        name="alienvault",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="AlienVault",
        output_dir=location,
        config=config,
    )


@connector_generator("cisa-kev")
def generate_cisa_known_exploited_vulnerabilities_connector(location: pathlib.Path, version: str):
    """Generate opencti cisa-known-exploited-vulnerabilities (cisa-kev) connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/cisa-known-exploited-vulnerabilities
    """
    config = extract_template_configs(
        "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
        f"/refs/tags/{version}/external-import/cisa-known-exploited-vulnerabilities/README.md"
    )
    config["cisa-create-infrastructures"]["type"] = "boolean"
    render_template(
        name="cisa-kev",
        connector_name="cisa-known-exploited-vulnerabilities",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="CISA Known Exploited Vulnerabilities",
        display_name_short="CISA KEV",
        output_dir=location,
        config=config,
    )


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


@connector_generator("crowdstrike")
def gen_crowdstrike_connector(location: pathlib.Path, version: str):
    """Generate opencti crowdstrike connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/crowdstrike
    """
    render_template(
        name="crowdstrike",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="CrowdStrike",
        config=extract_crowdstrike_configs(
            "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
            f"/refs/tags/{version}/external-import/crowdstrike/README.md"
        ),
        output_dir=location,
        charm_override=textwrap.dedent(
            """\
            def _gen_env(self) -> dict[str, str]:
                env = super()._gen_env()
                env["CONNECTOR_SCOPE"] = "crowdstrike"
                return env
            """
        ),
    )


@connector_generator("cyber-campaign")
def gen_cyber_campaign_collection_connector(location: pathlib.Path, version: str):
    """Generate opencti cyber-campaign-collection (cyber-campaign) connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/cyber-campaign-collection
    """
    render_template(
        name="cyber-campaign",
        connector_name="cyber-campaign-collection",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="APT & Cybercriminals Campaign Collection",
        display_name_short="APT & Cyber Campaign",
        output_dir=location,
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
                "type": "int",
            },
            "cyber-monitor-interval": {
                "description": "The interval in days, must be strictly greater than 1.",
                "type": "int",
            },
        },
    )


_FILE_EXPORTER_CONFIGS = {
    **DEFAULT_CONFIG,
    "connector-confidence-level": {
        "type": "int",
        "description": "(optional) the confidence level of the connector.",
    },
}


@connector_generator("export-file-csv")
def gen_export_file_csv_connector(location: pathlib.Path, version: str):
    """Generate opencti export-file-csv connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/internal-export-file/export-file-csv
    """
    render_template(
        name="export-file-csv",
        connector_type="INTERNAL_EXPORT_FILE",
        version=version,
        display_name="Export CSV File",
        output_dir=location,
        config={
            **_FILE_EXPORTER_CONFIGS,
            "export-file-csv-delimiter": {
                "type": "string",
                "description": "(optional) the delimiter of the exported CSV file.",
            },
        },
    )


@connector_generator("export-file-stix")
def gen_export_file_stix_connector(location: pathlib.Path, version: str):
    """Generate opencti export-file-stix connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/internal-export-file/export-file-stix
    """
    render_template(
        name="export-file-stix",
        connector_type="INTERNAL_EXPORT_FILE",
        version=version,
        display_name="Export STIX File",
        output_dir=location,
        config=_FILE_EXPORTER_CONFIGS,
    )


@connector_generator("export-file-txt")
def gen_export_file_txt_connector(location: pathlib.Path, version: str):
    """Generate opencti export-file-txt connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/internal-export-file/export-file-txt
    """
    render_template(
        name="export-file-txt",
        connector_type="INTERNAL_EXPORT_FILE",
        version=version,
        display_name="Export TXT File",
        output_dir=location,
        config=_FILE_EXPORTER_CONFIGS,
    )


@connector_generator("import-document")
def gen_import_document(location: pathlib.Path, version: str):
    """Generate opencti import-document connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/internal-import-file/import-document
    """
    render_template(
        name="import-document",
        connector_type="INTERNAL_IMPORT_FILE",
        version=version,
        display_name="Document Import",
        output_dir=location,
        config={
            "connector-only-contextual": {
                "description": "true only extract data related to an entity (a report, a threat actor, etc.)",
                "type": "boolean",
            },
            "connector-auto": {
                "description": "enable/disable auto import of report file",
                "type": "boolean",
            },
            "connector-scope": {
                "description": "connector scope",
                "type": "string",
            },
            "connector-confidence-level": {
                "description": "connector confidence level, from 0 (unknown) to 100 (fully trusted).",
                "type": "int",
            },
            "connector-log-level": {
                "description": "log level for this connector.",
                "type": "string",
                "default": "info",
            },
            "connector-validate-before-import": {
                "description": "validate any bundle before import.",
                "type": "boolean",
            },
            "import-document-create-indicator": {
                "description": "import document create indicator",
                "type": "boolean",
            },
        },
    )


@connector_generator("import-file-stix")
def gen_import_file_stix_connector(location: pathlib.Path, version: str):
    """Generate opencti import-file-stix connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/internal-import-file/import-file-stix
    """
    render_template(
        name="import-file-stix",
        connector_type="INTERNAL_IMPORT_FILE",
        version=version,
        display_name="Import File Stix",
        output_dir=location,
        config={
            "connector-validate-before-import": {
                "description": "validate any bundle before import",
                "type": "boolean",
            },
            "connector-scope": {
                "description": "connector scope",
                "type": "string",
            },
            "connector-auto": {
                "description": "enable/disable auto-import of file",
                "type": "boolean",
            },
            "connector-confidence-level": {
                "description": "from 0 (Unknown) to 100 (Fully trusted)",
                "type": "int",
            },
            "connector-log-level": {
                "description": "logging level of the connector",
                "type": "string",
                "default": "info",
            },
        },
    )


@connector_generator("malwarebazaar")
def gen_malwarebazaar_recent_additions_connector(location: pathlib.Path, version: str):
    """Generate opencti malwarebazaar-recent-additions (malwarebazaar) connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/malwarebazaar-recent-additions
    """
    render_template(
        name="malwarebazaar",
        connector_name="malwarebazaar-recent-additions",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="MalwareBazaar Recent Additions",
        display_name_short="MalwareBazaar",
        output_dir=location,
        config={
            "connector-log-level": {
                "description": "The log level for the connector",
                "type": "string",
            },
            "malwarebazaar-recent-additions-api-url": {
                "description": "The API URL",
                "type": "string",
            },
            "malwarebazaar-recent-additions-cooldown-seconds": {
                "description": "Time to wait in seconds between subsequent requests",
                "type": "int",
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


@connector_generator("misp-feed")
def gen_misp_feed_connector(location: pathlib.Path, version: str):
    """Generate opencti misp-feed connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/misp-feed
    """
    config = extract_template_configs(
        "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
        f"/refs/tags/{version}/external-import/misp-feed/README.md"
    )
    del config["connector-type"]
    config["misp-feed-create-indicators"]["type"] = "boolean"
    config["misp-feed-create-observables"]["type"] = "boolean"
    config["misp-feed-import-to-ids-no-score"]["type"] = "boolean"
    config["connector-run-and-terminate"] = {
        "type": "boolean",
        "description": "(optional) Launch the connector once if set to True",
    }
    config["misp-feed-interval"] = {"type": "int", "description": "misp feed interval in minutes"}
    config["misp-feed-create-tags-as-labels"] = {
        "type": "boolean",
        "description": "(optional) create tags as labels (sanitize MISP tag to OpenCTI labels)",
    }
    render_template(
        name="misp-feed",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="MISP Source",
        output_dir=location,
        config=config,
    )


@connector_generator("mitre")
def gen_mitre_connector(location: pathlib.Path, version: str):
    """Generate opencti mitre connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/mitre
    """
    render_template(
        name="mitre",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="MITRE Datasets",
        output_dir=location,
        config={
            "connector-run-and-terminate": {
                "type": "boolean",
                "description": "(optional) Launch the connector once if set to True",
            },
            "mitre-interval": {
                "description": "Number of the days between each MITRE datasets collection.",
                "type": "int",
            },
            "mitre-remove-statement-marking": {
                "description": "Remove the statement MITRE marking definition.",
                "type": "boolean",
            },
            "mitre-enterprise-file-url": {
                "description": "(optional) Resource URL",
                "type": "string",
            },
            "mitre-mobile-attack-file-url": {
                "description": "(optional) Resource URL",
                "type": "string",
            },
            "mitre-ics-attack-file-url": {
                "description": "(optional) Resource URL",
                "type": "string",
            },
            "mitre-capec-file-url": {
                "description": "(optional) Resource URL",
                "type": "string",
            },
            **DEFAULT_CONFIG,
        },
        generate_entrypoint="echo 'cd /opt/opencti-connector-mitre; python3 connector.py' > entrypoint.sh",
    )


@connector_generator("sekoia")
def gen_sekoia_connector(location: pathlib.Path, version: str):
    render_template(
        name="sekoia",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="Sekoia.io",
        output_dir=location,
        config={
            **DEFAULT_CONFIG,
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
            "sekoia-start-date": {
                "description": "(optional) the date to start consuming data from. Maybe in the formats YYYY-MM-DD or YYYY-MM-DDT00:00:00",
                "type": "string",
            },
            "sekoia-create-observables": {
                "description": "create observables from indicators",
                "type": "boolean",
            },
        },
        generate_entrypoint="echo 'cd /opt/opencti-connector-sekoia; python3 sekoia.py' > entrypoint.sh",
    )


@connector_generator("urlscan")
def genc_urlscan_connector(location: pathlib.Path, version: str):
    """Generate opencti urlscan connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/urlscan
    """
    render_template(
        name="urlscan",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="Urlscan.io",
        output_dir=location,
        config={
            "connector-confidence-level": {
                "description": "The default confidence level for created relationships (0 -> 100).",
                "type": "int",
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
                "type": "int",
            },
            "connector-lookback": {
                "description": "(optional) How far to look back in days if the connector has never run or the last run is older than this value. Default is 3. You should not go above 7.",
                "type": "int",
            },
            "urlscan-url": {
                "description": "The Urlscan URL.",
                "type": "string",
            },
            "urlscan-api-key": {
                "description": "The Urlscan client secret.",
                "type": "string",
            },
            "urlscan-default-x-opencti-score": {
                "description": "(optional) The default x_opencti_score to use across observable/indicator types. Default is 50.",
                "type": "int",
            },
            "urlscan-x-opencti-score-domain": {
                "description": "(optional) The x_opencti_score to use across Domain-Name observable and indicators. Defaults to default score.",
                "type": "int",
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


@connector_generator("urlscan-enrichment")
def gen_urlscan_enrichment_connector(location: pathlib.Path, version: str):
    """Generate opencti urlscan-enrichment connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/internal-enrichment/urlscan-enrichment
    """
    config = extract_template_configs(
        "https://raw.githubusercontent.com/OpenCTI-Platform/connectors"
        f"/refs/tags/{version}/internal-enrichment/urlscan-enrichment/README.md"
    )
    config["connector-auto"] = {"type": "boolean", "description": "connector auto"}
    render_template(
        name="urlscan-enrichment",
        connector_type="INTERNAL_ENRICHMENT",
        version=version,
        display_name="URLScan Enrichment",
        output_dir=location,
        config=config,
    )


@connector_generator("virustotal-livehunt")
def gen_virustotal_livehunt_notifications_connector(location: pathlib.Path, version: str):
    """Generate opencti virustotal-livehunt-notifications (virustotal-livehunt) connector.

    https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/virustotal-livehunt-notifications
    """
    render_template(
        name="virustotal-livehunt",
        connector_name="virustotal-livehunt-notifications",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="VirusTotal Livehunt Notifications",
        display_name_short="VirusTotal Livehunt",
        output_dir=location,
        config={
            **DEFAULT_CONFIG,
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
        charm_override=textwrap.dedent(
            """\
            @property
            def boolean_style(self) -> str:
                return "python"
            """
        ),
    )


@connector_generator("vxvault")
def gen_vxvault_connector(location: pathlib, version: str) -> None:
    render_template(
        name="vxvault",
        connector_type="EXTERNAL_IMPORT",
        version=version,
        display_name="VXVault",
        output_dir=location,
        config={
            "connector-scope": {
                "description": "connector scope",
                "type": "string",
            },
            "connector-log-level": {
                "description": "(optional) The log level of the connector",
                "type": "string",
            },
            "vxvault-url": {
                "description": "vxvault url",
                "type": "string",
                "default": "https://vxvault.net/URL_List.php",
            },
            "vxvault-create-indicators": {
                "description": "vxvault create indicators",
                "type": "boolean",
            },
            "vxvault-interval": {
                "description": "In days, must be strictly greater than 1",
                "type": "int",
            },
            "vxvault-ssl-verify": {
                "description": "Whether to verify SSL certificates",
                "type": "boolean",
                "default": True,
            },
        },
    )


def render(connector: str, version: str):
    location = (
        pathlib.Path(__file__).resolve().parent.parent / "connectors" / kebab_to_snake(connector)
    )
    _CONNECTOR_GENERATORS[connector](location=location, version=version)


def render_all(version):
    for connector in _CONNECTOR_GENERATORS:
        render(connector, version)


if __name__ == "__main__":
    render_all("6.4.5")
