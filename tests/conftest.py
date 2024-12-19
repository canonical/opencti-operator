# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm tests."""

import pathlib

import pytest
import yaml


def list_connectors() -> list[str]:
    """Return a list of opencti connector charms."""
    connectors = []
    for file in pathlib.Path("connectors").glob("**/charmcraft.yaml"):
        charmcraft_yaml = yaml.safe_load(file.read_text())
        connectors.append(charmcraft_yaml["name"])
    return connectors


@pytest.fixture(scope="session", name="connectors")
def connectors_fixture() -> list[str]:
    """Return a list of opencti connector charms."""
    return list_connectors()


def pytest_addoption(parser):
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption("--charm-file", action="append")
    parser.addoption("--opencti-image", action="store")
    parser.addoption("--machine-controller", action="store", default="localhost")
    for connector in list_connectors():
        parser.addoption(f"--{connector}-image", action="store")
