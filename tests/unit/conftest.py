# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm unit tests."""

import unittest.mock
from unittest.mock import MagicMock

import pytest

import src.charm


@pytest.fixture(scope="function", autouse=True)
def juju_version(monkeypatch):
    """Patch JUJU_VERSION environment variable."""
    monkeypatch.setenv("JUJU_VERSION", "3.3.0")


@pytest.fixture(scope="function")
def patch_check_platform_health():
    """Patch OpenCTICharm._check_platform_health environment variable."""
    mock = MagicMock()
    with unittest.mock.patch.object(src.charm.OpenCTICharm, "_check_platform_health", mock):
        yield mock
