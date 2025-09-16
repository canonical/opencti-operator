# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://juju.is/docs/sdk/testing

"""Unit tests for connectors."""
import importlib

import ops.testing
import pytest

from connectors.export_file_stix.src.charm import OpenctiExportFileStixConnectorCharm
from tests.unit.state import ConnectorStateBuilder


def _kebab_to_pascal(string: str) -> str:
    """Convert names from kebab case to pascal case."""
    words = string.split("-")
    return "".join(word.capitalize() for word in words)


def _kebab_to_snake(string: str) -> str:
    """Convert names from kebab case to snake case."""
    return string.replace("-", "_")


_CONNECTOR_TEST_PARAMS = []


def _add_connector_test_params(
    *,
    name: str,
    connector_name: str,
    charm_config: dict[str, str | int | bool],
    environment: dict[str, str],
) -> None:
    """Add a connector test parameter."""
    _CONNECTOR_TEST_PARAMS.append(pytest.param(connector_name, charm_config, environment, id=name))


_add_connector_test_params(
    name="abuseipdb-ipblacklist",
    connector_name="abuseipdb-ipblacklist",
    charm_config={
        "connector-scope": "abuseipdb",
        "connector-log-level": "error",
        "abuseipdb-url": "https://api.abuseipdb.com/api/v2/blacklist",
        "abuseipdb-api-key": "ChangeMe",
        "abuseipdb-score": 100,
        "abuseipdb-limit": 10000,
        "abuseipdb-interval": 2,
    },
    environment={
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "CONNECTOR_NAME": "opencti-abuseipdb-ipblacklist-connector",
        "CONNECTOR_SCOPE": "abuseipdb",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "ABUSEIPDB_URL": "https://api.abuseipdb.com/api/v2/blacklist",
        "ABUSEIPDB_API_KEY": "ChangeMe",
        "ABUSEIPDB_SCORE": "100",
        "ABUSEIPDB_LIMIT": "10000",
        "ABUSEIPDB_INTERVAL": "2",
    },
)

_add_connector_test_params(
    name="alienvault",
    connector_name="alienvault",
    charm_config={
        "connector-scope": "alienvault",
        "connector-log-level": "error",
        "connector-duration-period": "PT30M",
        "alienvault-base-url": "https://otx.alienvault.com",
        "alienvault-api-key": "ChangeMe",
        "alienvault-tlp": "White",
        "alienvault-create-observables": True,
        "alienvault-create-indicators": True,
        "alienvault-pulse-start-timestamp": "2022-05-01T00:00:00",
        "alienvault-report-type": "threat-report",
        "alienvault-report-status": "New",
        "alienvault-guess-malware": False,
        "alienvault-guess-cve": False,
        "alienvault-excluded-pulse-indicator-types": "FileHash-MD5,FileHash-SHA1",
        "alienvault-enable-relationships": True,
        "alienvault-enable-attack-patterns-indicates": False,
        "alienvault-interval-sec": 1800,
        "alienvault-default-x-opencti-score": 50,
        "alienvault-x-opencti-score-ip": 60,
        "alienvault-x-opencti-score-domain": 70,
        "alienvault-x-opencti-score-hostname": 75,
        "alienvault-x-opencti-score-email": 70,
        "alienvault-x-opencti-score-file": 85,
        "alienvault-x-opencti-score-url": 80,
        "alienvault-x-opencti-score-mutex": 60,
        "alienvault-x-opencti-score-cryptocurrency-wallet": 80,
    },
    environment={
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "CONNECTOR_NAME": "opencti-alienvault-connector",
        "CONNECTOR_SCOPE": "alienvault",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_DURATION_PERIOD": "PT30M",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "ALIENVAULT_BASE_URL": "https://otx.alienvault.com",
        "ALIENVAULT_API_KEY": "ChangeMe",
        "ALIENVAULT_TLP": "White",
        "ALIENVAULT_CREATE_OBSERVABLES": "true",
        "ALIENVAULT_CREATE_INDICATORS": "true",
        "ALIENVAULT_PULSE_START_TIMESTAMP": "2022-05-01T00:00:00",
        "ALIENVAULT_REPORT_TYPE": "threat-report",
        "ALIENVAULT_REPORT_STATUS": "New",
        "ALIENVAULT_GUESS_MALWARE": "false",
        "ALIENVAULT_GUESS_CVE": "false",
        "ALIENVAULT_EXCLUDED_PULSE_INDICATOR_TYPES": "FileHash-MD5,FileHash-SHA1",
        "ALIENVAULT_ENABLE_RELATIONSHIPS": "true",
        "ALIENVAULT_ENABLE_ATTACK_PATTERNS_INDICATES": "false",
        "ALIENVAULT_INTERVAL_SEC": "1800",
        "ALIENVAULT_DEFAULT_X_OPENCTI_SCORE": "50",
        "ALIENVAULT_X_OPENCTI_SCORE_IP": "60",
        "ALIENVAULT_X_OPENCTI_SCORE_DOMAIN": "70",
        "ALIENVAULT_X_OPENCTI_SCORE_HOSTNAME": "75",
        "ALIENVAULT_X_OPENCTI_SCORE_EMAIL": "70",
        "ALIENVAULT_X_OPENCTI_SCORE_FILE": "85",
        "ALIENVAULT_X_OPENCTI_SCORE_URL": "80",
        "ALIENVAULT_X_OPENCTI_SCORE_MUTEX": "60",
        "ALIENVAULT_X_OPENCTI_SCORE_CRYPTOCURRENCY_WALLET": "80",
    },
)

_add_connector_test_params(
    name="cisa-kev",
    connector_name="cisa-kev",
    charm_config={
        "connector-scope": "cisa",
        "connector-run-and-terminate": False,
        "connector-log-level": "error",
        "connector-duration-period": "P2D",
        "cisa-catalog-url": (
            "https://www.cisa.gov/sites/default/files/feeds/"
            "known_exploited_vulnerabilities.json"
        ),
        "cisa-create-infrastructures": False,
        "cisa-tlp": "TLP:CLEAR",
    },
    environment={
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "CONNECTOR_NAME": "opencti-cisa-kev-connector",
        "CONNECTOR_SCOPE": "cisa",
        "CONNECTOR_RUN_AND_TERMINATE": "false",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_DURATION_PERIOD": "P2D",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "CISA_CATALOG_URL": (
            "https://www.cisa.gov/sites/default/files/feeds/"
            "known_exploited_vulnerabilities.json"
        ),
        "CISA_CREATE_INFRASTRUCTURES": "false",
        "CISA_TLP": "TLP:CLEAR",
    },
)

_add_connector_test_params(
    name="crowdstrike",
    connector_name="crowdstrike",
    charm_config={
        "connector-log-level": "error",
        "connector-duration-period": "PT30M",
        "crowdstrike-base-url": "https://api.crowdstrike.com",
        "crowdstrike-client-id": "ChangeMe",
        "crowdstrike-client-secret": "ChangeMe",
        "crowdstrike-tlp": "Amber",
        "crowdstrike-create-observables": "true",
        "crowdstrike-create-indicators": "true",
        "crowdstrike-scopes": "actor,report,indicator,yara_master",
        "crowdstrike-actor-start-timestamp": 0,
        "crowdstrike-report-start-timestamp": 0,
        "crowdstrike-report-status": "New",
        "crowdstrike-report-include-types": "notice,tipper,intelligence report,periodic report",
        "crowdstrike-report-type": "threat-report",
        "crowdstrike-report-target-industries": "",
        "crowdstrike-report-guess-malware": "false",
        "crowdstrike-indicator-start-timestamp": 0,
        "crowdstrike-indicator-exclude-types": "hash_ion,hash_md5,hash_sha1",
        # undocumented configuration
        # "crowdstrike-default-x-opencti-score": 50,
        "crowdstrike-indicator-low-score": 40,
        "crowdstrike-indicator-low-score-labels": "MaliciousConfidence/Low",
        "crowdstrike-indicator-medium-score": 60,
        "crowdstrike-indicator-medium-score-labels": "MaliciousConfidence/Medium",
        "crowdstrike-indicator-high-score": 80,
        "crowdstrike-indicator-high-score-labels": "MaliciousConfidence/High",
        "crowdstrike-indicator-unwanted-labels": "",
    },
    environment={
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "CONNECTOR_NAME": "opencti-crowdstrike-connector",
        "CONNECTOR_SCOPE": "crowdstrike",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "CONNECTOR_DURATION_PERIOD": "PT30M",
        "CROWDSTRIKE_BASE_URL": "https://api.crowdstrike.com",
        "CROWDSTRIKE_CLIENT_ID": "ChangeMe",
        "CROWDSTRIKE_CLIENT_SECRET": "ChangeMe",
        "CROWDSTRIKE_TLP": "Amber",
        "CROWDSTRIKE_CREATE_OBSERVABLES": "true",
        "CROWDSTRIKE_CREATE_INDICATORS": "true",
        "CROWDSTRIKE_SCOPES": "actor,report,indicator,yara_master",
        "CROWDSTRIKE_ACTOR_START_TIMESTAMP": "0",
        "CROWDSTRIKE_REPORT_START_TIMESTAMP": "0",
        "CROWDSTRIKE_REPORT_STATUS": "New",
        "CROWDSTRIKE_REPORT_INCLUDE_TYPES": "notice,tipper,intelligence report,periodic report",
        "CROWDSTRIKE_REPORT_TYPE": "threat-report",
        "CROWDSTRIKE_REPORT_TARGET_INDUSTRIES": "",
        "CROWDSTRIKE_REPORT_GUESS_MALWARE": "false",
        "CROWDSTRIKE_INDICATOR_START_TIMESTAMP": "0",
        "CROWDSTRIKE_INDICATOR_EXCLUDE_TYPES": "hash_ion,hash_md5,hash_sha1",
        # "CROWDSTRIKE_DEFAULT_X_OPENCTI_SCORE": "50",
        "CROWDSTRIKE_INDICATOR_LOW_SCORE": "40",
        "CROWDSTRIKE_INDICATOR_LOW_SCORE_LABELS": "MaliciousConfidence/Low",
        "CROWDSTRIKE_INDICATOR_MEDIUM_SCORE": "60",
        "CROWDSTRIKE_INDICATOR_MEDIUM_SCORE_LABELS": "MaliciousConfidence/Medium",
        "CROWDSTRIKE_INDICATOR_HIGH_SCORE": "80",
        "CROWDSTRIKE_INDICATOR_HIGH_SCORE_LABELS": "MaliciousConfidence/High",
        "CROWDSTRIKE_INDICATOR_UNWANTED_LABELS": "",
    },
)


_add_connector_test_params(
    name="cyber-campaign",
    connector_name="cyber-campaign",
    charm_config={
        "connector-scope": "report",
        "connector-run-and-terminate": False,
        "connector-log-level": "error",
        "cyber-monitor-github-token": "",
        "cyber-monitor-from-year": 2018,
        "cyber-monitor-interval": 4,
    },
    environment={
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "CONNECTOR_NAME": "opencti-cyber-campaign-connector",
        "CONNECTOR_SCOPE": "report",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "CONNECTOR_RUN_AND_TERMINATE": "false",
        "CONNECTOR_LOG_LEVEL": "error",
        "CYBER_MONITOR_GITHUB_TOKEN": "",
        "CYBER_MONITOR_FROM_YEAR": "2018",
        "CYBER_MONITOR_INTERVAL": "4",
    },
)

_add_connector_test_params(
    name="export-file-csv",
    connector_name="export-file-csv",
    charm_config={
        "connector-scope": "text/csv",
        "connector-confidence-level": 100,
        "connector-log-level": "error",
        "export-file-csv-delimiter": ";",
    },
    environment={
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "CONNECTOR_NAME": "opencti-export-file-csv-connector",
        "CONNECTOR_SCOPE": "text/csv",
        "CONNECTOR_TYPE": "INTERNAL_EXPORT_FILE",
        "CONNECTOR_CONFIDENCE_LEVEL": "100",
        "CONNECTOR_LOG_LEVEL": "error",
        "EXPORT_FILE_CSV_DELIMITER": ";",
    },
)

_add_connector_test_params(
    name="export-file-stix",
    connector_name="export-file-stix",
    charm_config={
        "connector-scope": "application/vnd.oasis.stix+json",
        "connector-confidence-level": 100,
        "connector-log-level": "error",
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-export-file-stix-connector",
        "CONNECTOR_SCOPE": "application/vnd.oasis.stix+json",
        "CONNECTOR_CONFIDENCE_LEVEL": "100",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "INTERNAL_EXPORT_FILE",
    },
)

_add_connector_test_params(
    name="export-file-stix-minimal",
    connector_name="export-file-stix",
    charm_config={"connector-scope": "application/json"},
    environment={
        "CONNECTOR_LOG_LEVEL": "info",
        "CONNECTOR_NAME": "opencti-export-file-stix-connector",
        "CONNECTOR_SCOPE": "application/json",
        "CONNECTOR_TYPE": "INTERNAL_EXPORT_FILE",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
    },
)

_add_connector_test_params(
    name="export-file-txt",
    connector_name="export-file-txt",
    charm_config={
        "connector-scope": "text/plain",
        "connector-confidence-level": 100,
        "connector-log-level": "error",
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-export-file-txt-connector",
        "CONNECTOR_TYPE": "INTERNAL_EXPORT_FILE",
        "CONNECTOR_SCOPE": "text/plain",
        "CONNECTOR_CONFIDENCE_LEVEL": "100",
        "CONNECTOR_LOG_LEVEL": "error",
    },
)

_add_connector_test_params(
    name="import-document",
    connector_name="import-document",
    charm_config={
        "connector-validate-before-import": True,
        "connector-scope": "application/pdf,text/plain,text/html,text/markdown",
        "connector-auto": False,
        "connector-only-contextual": False,
        "connector-confidence-level": 100,
        "connector-log-level": "error",
        "import-document-create-indicator": False,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-import-document-connector",
        "CONNECTOR_VALIDATE_BEFORE_IMPORT": "true",
        "CONNECTOR_SCOPE": "application/pdf,text/plain,text/html,text/markdown",
        "CONNECTOR_AUTO": "false",
        "CONNECTOR_ONLY_CONTEXTUAL": "false",
        "CONNECTOR_CONFIDENCE_LEVEL": "100",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "INTERNAL_IMPORT_FILE",
        "IMPORT_DOCUMENT_CREATE_INDICATOR": "false",
    },
)

_add_connector_test_params(
    name="import-file-stix",
    connector_name="import-file-stix",
    charm_config={
        "connector-validate-before-import": True,
        "connector-scope": "application/json,application/xml",
        "connector-auto": False,
        "connector-confidence-level": 15,
        "connector-log-level": "error",
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-import-file-stix-connector",
        "CONNECTOR_VALIDATE_BEFORE_IMPORT": "true",
        "CONNECTOR_SCOPE": "application/json,application/xml",
        "CONNECTOR_AUTO": "false",
        "CONNECTOR_CONFIDENCE_LEVEL": "15",
        "CONNECTOR_TYPE": "INTERNAL_IMPORT_FILE",
        "CONNECTOR_LOG_LEVEL": "error",
    },
)

_add_connector_test_params(
    name="ipinfo",
    connector_name="ipinfo",
    charm_config={
        "connector-scope": "IPv4-Addr,IPv6-Addr",
        "connector-auto": False,
        "connector-confidence-level": 75,
        "connector-log-level": "error",
        "ipinfo-token": "abcd",
        "ipinfo-max-tlp": "TLP:AMBER",
        "ipinfo-use-asn-name": True,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-ipinfo-connector",
        "CONNECTOR_SCOPE": "IPv4-Addr,IPv6-Addr",
        "CONNECTOR_AUTO": "false",
        "CONNECTOR_CONFIDENCE_LEVEL": "75",
        "CONNECTOR_TYPE": "INTERNAL_ENRICHMENT",
        "CONNECTOR_LOG_LEVEL": "error",
        "IPINFO_TOKEN": "abcd",
        "IPINFO_MAX_TLP": "TLP:AMBER",
        "IPINFO_USE_ASN_NAME": "true",
    },
)


_add_connector_test_params(
    name="malwarebazaar",
    connector_name="malwarebazaar",
    charm_config={
        "connector-log-level": "error",
        "malwarebazaar-recent-additions-api-url": "https://mb-api.abuse.ch/api/v1/",
        "malwarebazaar-recent-additions-cooldown-seconds": 300,
        "malwarebazaar-recent-additions-include-tags": "exe,dll,docm,docx,doc,xls,xlsx,xlsm,js",
        "malwarebazaar-recent-additions-include-reporters": "",
        "malwarebazaar-recent-additions-labels": "malware-bazaar",
        "malwarebazaar-recent-additions-labels-color": "#54483b",
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-malwarebazaar-connector",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "MALWAREBAZAAR_RECENT_ADDITIONS_API_URL": "https://mb-api.abuse.ch/api/v1/",
        "MALWAREBAZAAR_RECENT_ADDITIONS_COOLDOWN_SECONDS": "300",
        "MALWAREBAZAAR_RECENT_ADDITIONS_INCLUDE_TAGS": "exe,dll,docm,docx,doc,xls,xlsx,xlsm,js",
        "MALWAREBAZAAR_RECENT_ADDITIONS_INCLUDE_REPORTERS": "",
        "MALWAREBAZAAR_RECENT_ADDITIONS_LABELS": "malware-bazaar",
        "MALWAREBAZAAR_RECENT_ADDITIONS_LABELS_COLOR": "#54483b",
    },
)

_add_connector_test_params(
    name="misp-feed",
    connector_name="misp-feed",
    charm_config={
        "connector-scope": "misp-feed",
        "connector-run-and-terminate": False,
        "connector-log-level": "error",
        "misp-feed-url": "https://changeme.com/misp-feed",
        "misp-feed-ssl-verify": True,
        "misp-feed-import-from-date": "2000-01-01",
        "misp-feed-create-reports": True,
        "misp-feed-report-type": "misp-event",
        "misp-feed-create-indicators": True,
        "misp-feed-create-observables": True,
        "misp-feed-create-object-observables": True,
        "misp-feed-create-tags-as-labels": True,
        "misp-feed-guess-threat-from-tags": False,
        "misp-feed-author-from-tags": False,
        "misp-feed-import-to-ids-no-score": True,
        "misp-feed-import-unsupported-observables-as-text": False,
        "misp-feed-import-unsupported-observables-as-text-transparent": True,
        "misp-feed-import-with-attachments": False,
        "misp-feed-interval": 5,
        "misp-feed-source-type": "url",
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-misp-feed-connector",
        "CONNECTOR_SCOPE": "misp-feed",
        "CONNECTOR_RUN_AND_TERMINATE": "false",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "MISP_FEED_URL": "https://changeme.com/misp-feed",
        "MISP_FEED_SSL_VERIFY": "true",
        "MISP_FEED_IMPORT_FROM_DATE": "2000-01-01",
        "MISP_FEED_CREATE_REPORTS": "true",
        "MISP_FEED_REPORT_TYPE": "misp-event",
        "MISP_FEED_CREATE_INDICATORS": "true",
        "MISP_FEED_CREATE_OBSERVABLES": "true",
        "MISP_FEED_CREATE_OBJECT_OBSERVABLES": "true",
        "MISP_FEED_CREATE_TAGS_AS_LABELS": "true",
        "MISP_FEED_GUESS_THREAT_FROM_TAGS": "false",
        "MISP_FEED_AUTHOR_FROM_TAGS": "false",
        "MISP_FEED_IMPORT_TO_IDS_NO_SCORE": "true",
        "MISP_FEED_IMPORT_UNSUPPORTED_OBSERVABLES_AS_TEXT": "false",
        "MISP_FEED_IMPORT_UNSUPPORTED_OBSERVABLES_AS_TEXT_TRANSPARENT": "true",
        "MISP_FEED_IMPORT_WITH_ATTACHMENTS": "false",
        "MISP_FEED_INTERVAL": "5",
        "MISP_FEED_SOURCE_TYPE": "url",
    },
)

_add_connector_test_params(
    name="mitre",
    connector_name="mitre",
    charm_config={
        "connector-scope": (
            "tool,report,malware,identity,campaign,"
            "intrusion-set,attack-pattern,course-of-action,"
            "x-mitre-data-source,x-mitre-data-component,"
            "x-mitre-matrix,x-mitre-tactic,x-mitre-collection"
        ),
        "connector-run-and-terminate": False,
        "connector-log-level": "error",
        "mitre-remove-statement-marking": True,
        "mitre-interval": 7,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-mitre-connector",
        "CONNECTOR_SCOPE": (
            "tool,report,malware,identity,campaign,intrusion-set,"
            "attack-pattern,course-of-action,x-mitre-data-source,"
            "x-mitre-data-component,x-mitre-matrix,x-mitre-tactic,x-mitre-collection"
        ),
        "CONNECTOR_RUN_AND_TERMINATE": "false",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "MITRE_REMOVE_STATEMENT_MARKING": "true",
        "MITRE_INTERVAL": "7",
    },
)

_add_connector_test_params(
    name="nti",
    connector_name="nti",
    charm_config={
        "connector-log-level": "info",
        "connector-duration-period": "P1D",
        "nti-base-url": "https://nti.nsfocusglobal.com/api/v2/",
        "nti-api-key": "ChangeMe",
        "nti-tlp": "white",
        "nti-create-ioc": True,
        "nti-create-ip": True,
        "nti-create-domain": True,
        "nti-create-file": True,
        "nti-create-url": True,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-nti-connector",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "CONNECTOR_LOG_LEVEL": "info",
        "CONNECTOR_QUEUE_THRESHOLD": "500",
        "CONNECTOR_SCOPE": "nti",
        "CONNECTOR_DURATION_PERIOD": "P1D",
        "NTI_BASE_URL": "https://nti.nsfocusglobal.com/api/v2/",
        "NTI_API_KEY": "ChangeMe",
        "NTI_TLP": "white",
        "NTI_CREATE_IOC": "true",
        "NTI_CREATE_IP": "true",
        "NTI_CREATE_DOMAIN": "true",
        "NTI_CREATE_FILE": "true",
        "NTI_CREATE_URL": "true",
        "NTI_PACKAGE_TYPE": "updated",
    },
)

_add_connector_test_params(
    name="sekoia",
    connector_name="sekoia",
    charm_config={
        "connector-scope": (
            "identity,attack-pattern,course-of-action,intrusion-set,"
            "malware,tool,report,location,vulnerability,indicator,"
            "campaign,infrastructure,relationship"
        ),
        "connector-log-level": "error",
        "sekoia-api-key": "ChangeMe",
        "sekoia-collection": "d6092c37-d8d7-45c3-8aff-c4dc26030608",
        "sekoia-start-date": "2022-01-01",
        "sekoia-create-observables": True,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-sekoia-connector",
        "CONNECTOR_SCOPE": (
            "identity,attack-pattern,course-of-action,intrusion-set,"
            "malware,tool,report,location,vulnerability,indicator,"
            "campaign,infrastructure,relationship"
        ),
        "CONNECTOR_LOG_LEVEL": "error",
        "SEKOIA_API_KEY": "ChangeMe",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "SEKOIA_BASE_URL": "https://api.sekoia.io",
        "SEKOIA_COLLECTION": "d6092c37-d8d7-45c3-8aff-c4dc26030608",
        "SEKOIA_START_DATE": "2022-01-01",
        "SEKOIA_CREATE_OBSERVABLES": "true",
    },
)

_add_connector_test_params(
    name="urlhaus",
    connector_name="urlhaus",
    charm_config={
        "connector-log-level": "error",
        "connector-confidence-level": 40,
        "urlhaus-interval": 3,
    },
    environment={
        "CONNECTOR_CONFIDENCE_LEVEL": "40",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_NAME": "opencti-urlhaus-connector",
        "CONNECTOR_SCOPE": "urlhaus",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "URLHAUS_CSV_URL": "https://urlhaus.abuse.ch/downloads/csv_recent/",
        "URLHAUS_IMPORT_OFFLINE": "true",
        "URLHAUS_INTERVAL": "3",
        "URLHAUS_THREATS_FROM_LABELS": "true",
    },
)


_add_connector_test_params(
    name="urlscan",
    connector_name="urlscan",
    charm_config={
        "connector-log-level": "error",
        "connector-confidence-level": 40,
        "connector-create-indicators": True,
        "connector-tlp": "white",
        "connector-labels": "Phishing,Phishfeed",
        "connector-interval": 86400,
        "connector-lookback": 3,
        "connector-update-existing-data": True,
        "urlscan-url": "https://urlscan.io/api/v1/pro/phishfeed?format=json",
        "urlscan-api-key": "",
        "urlscan-default-x-opencti-score": 50,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-urlscan-connector",
        "CONNECTOR_SCOPE": "threatmatch",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_CONFIDENCE_LEVEL": "40",
        "CONNECTOR_CREATE_INDICATORS": "true",
        "CONNECTOR_TLP": "white",
        "CONNECTOR_LABELS": "Phishing,Phishfeed",
        "CONNECTOR_INTERVAL": "86400",
        "CONNECTOR_LOOKBACK": "3",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "CONNECTOR_UPDATE_EXISTING_DATA": "true",
        "URLSCAN_URL": "https://urlscan.io/api/v1/pro/phishfeed?format=json",
        "URLSCAN_API_KEY": "",
        "URLSCAN_DEFAULT_X_OPENCTI_SCORE": "50",
    },
)

_add_connector_test_params(
    name="urlscan-enrichment",
    connector_name="urlscan-enrichment",
    charm_config={
        "connector-scope": "url,ipv4-addr,ipv6-addr",
        "connector-auto": False,
        "connector-log-level": "error",
        "urlscan-enrichment-api-key": "ChangeMe",
        "urlscan-enrichment-api-base-url": "https://urlscan.io/api/v1/",
        "urlscan-enrichment-import-screenshot": True,
        "urlscan-enrichment-visibility": "public",
        "urlscan-enrichment-search-filtered-by-date": ">now-1y",
        "urlscan-enrichment-max-tlp": "TLP:AMBER",
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-urlscan-enrichment-connector",
        "CONNECTOR_SCOPE": "url,ipv4-addr,ipv6-addr",
        "CONNECTOR_AUTO": "false",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "INTERNAL_ENRICHMENT",
        "URLSCAN_ENRICHMENT_API_KEY": "ChangeMe",
        "URLSCAN_ENRICHMENT_API_BASE_URL": "https://urlscan.io/api/v1/",
        "URLSCAN_ENRICHMENT_IMPORT_SCREENSHOT": "true",
        "URLSCAN_ENRICHMENT_VISIBILITY": "public",
        "URLSCAN_ENRICHMENT_SEARCH_FILTERED_BY_DATE": ">now-1y",
        "URLSCAN_ENRICHMENT_MAX_TLP": "TLP:AMBER",
    },
)

_add_connector_test_params(
    name="virustotal-livehunt",
    connector_name="virustotal-livehunt",
    charm_config={
        "connector-scope": "StixFile,Indicator,Incident",
        "connector-log-level": "error",
        "virustotal-livehunt-notifications-api-key": "ChangeMe",
        "virustotal-livehunt-notifications-interval-sec": 300,
        "virustotal-livehunt-notifications-create-alert": True,
        "virustotal-livehunt-notifications-extensions": "'exe,dll'",
        "virustotal-livehunt-notifications-min-file-size": 1000,
        "virustotal-livehunt-notifications-max-file-size": 52428800,
        "virustotal-livehunt-notifications-max-age-days": 3,
        "virustotal-livehunt-notifications-min-positives": 5,
        "virustotal-livehunt-notifications-create-file": True,
        "virustotal-livehunt-notifications-upload-artifact": False,
        "virustotal-livehunt-notifications-create-yara-rule": True,
        "virustotal-livehunt-notifications-delete-notification": False,
        "virustotal-livehunt-notifications-filter-with-tag": '"mytag"',
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-virustotal-livehunt-connector",
        "CONNECTOR_SCOPE": "StixFile,Indicator,Incident",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_API_KEY": "ChangeMe",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_INTERVAL_SEC": "300",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_CREATE_ALERT": "True",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_EXTENSIONS": "'exe,dll'",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_MIN_FILE_SIZE": "1000",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_MAX_FILE_SIZE": "52428800",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_MAX_AGE_DAYS": "3",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_MIN_POSITIVES": "5",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_CREATE_FILE": "True",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_UPLOAD_ARTIFACT": "False",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_CREATE_YARA_RULE": "True",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_DELETE_NOTIFICATION": "False",
        "VIRUSTOTAL_LIVEHUNT_NOTIFICATIONS_FILTER_WITH_TAG": '"mytag"',
    },
)


_add_connector_test_params(
    name="vxvault",
    connector_name="vxvault",
    charm_config={
        "connector-scope": "vxvault",
        "connector-log-level": "error",
        "vxvault-url": "https://vxvault.net/URL_List.php",
        "vxvault-create-indicators": True,
        "vxvault-interval": 3,
        "vxvault-ssl-verify": False,
    },
    environment={
        "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
        "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
        "CONNECTOR_NAME": "opencti-vxvault-connector",
        "CONNECTOR_SCOPE": "vxvault",
        "CONNECTOR_LOG_LEVEL": "error",
        "CONNECTOR_TYPE": "EXTERNAL_IMPORT",
        "VXVAULT_URL": "https://vxvault.net/URL_List.php",
        "VXVAULT_CREATE_INDICATORS": "true",
        "VXVAULT_INTERVAL": "3",
        "VXVAULT_SSL_VERIFY": "false",
    },
)


@pytest.mark.parametrize("connector_name, charm_config, environment", _CONNECTOR_TEST_PARAMS)
def test_connector_environment(connector_name, charm_config, environment):
    """
    arrange: provide the connector charm with the required integrations and configurations.
    act: simulate a config-changed event.
    assert: the installed Pebble plan matches the expectation.
    """
    name = f"opencti-{connector_name}-connector"
    module = connector_name
    charm_module = importlib.import_module(f"connectors.{_kebab_to_snake(module)}.src.charm")
    charm_class = getattr(charm_module, _kebab_to_pascal(name) + "Charm")
    ctx = ops.testing.Context(charm_class)
    state_builder = ConnectorStateBuilder(name).add_opencti_connector_integration()
    for config_key, config_value in charm_config.items():
        state_builder = state_builder.set_config(config_key, config_value)
    state_in = state_builder.build()
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    plan = state_out.get_container(name).plan.to_dict()
    del plan["services"]["connector"]["environment"]["CONNECTOR_ID"]
    assert plan == {
        "services": {
            "connector": {
                "command": "bash /entrypoint.sh",
                "environment": environment,
                "on-failure": "restart",
                "override": "replace",
                "startup": "enabled",
            }
        }
    }


def test_proxy_environment(monkeypatch):
    """
    arrange: provide the connector charm with http proxy configured.
    act: simulate a config-changed event.
    assert: the installed Pebble plan matches the expectation.
    """
    monkeypatch.setenv("JUJU_CHARM_HTTP_PROXY", "http://example.com")
    monkeypatch.setenv("JUJU_CHARM_HTTPS_PROXY", "https://example.com")
    monkeypatch.setenv("JUJU_CHARM_NO_PROXY", "localhost,127.0.0.1")

    ctx = ops.testing.Context(OpenctiExportFileStixConnectorCharm)
    state_builder = ConnectorStateBuilder(
        "opencti-export-file-stix-connector"
    ).add_opencti_connector_integration()
    state_builder = state_builder.set_config("connector-scope", "application/vnd.oasis.stix+json")
    state_builder = state_builder.set_config("connector-confidence-level", 100)
    state_in = state_builder.build()
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    plan = state_out.get_container("opencti-export-file-stix-connector").plan.to_dict()
    del plan["services"]["connector"]["environment"]["CONNECTOR_ID"]
    assert plan == {
        "services": {
            "connector": {
                "command": "bash /entrypoint.sh",
                "environment": {
                    "CONNECTOR_CONFIDENCE_LEVEL": "100",
                    "CONNECTOR_LOG_LEVEL": "info",
                    "CONNECTOR_NAME": "opencti-export-file-stix-connector",
                    "CONNECTOR_SCOPE": "application/vnd.oasis.stix+json",
                    "CONNECTOR_TYPE": "INTERNAL_EXPORT_FILE",
                    "HTTPS_PROXY": "https://example.com",
                    "HTTP_PROXY": "http://example.com",
                    "NO_PROXY": "localhost,127.0.0.1,opencti-endpoints.test-opencti-connector.svc",
                    "OPENCTI_TOKEN": "00000000-0000-0000-0000-000000000000",
                    "OPENCTI_URL": "http://opencti-endpoints.test-opencti-connector.svc:8080",
                    "http_proxy": "http://example.com",
                    "https_proxy": "https://example.com",
                    "no_proxy": "localhost,127.0.0.1,opencti-endpoints.test-opencti-connector.svc",
                },
                "on-failure": "restart",
                "override": "replace",
                "startup": "enabled",
            }
        }
    }
