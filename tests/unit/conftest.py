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
def patch_is_platform_healthy():
    """Patch OpenCTICharm.is_platform_healthy function."""
    mock = MagicMock(return_value=True)
    with unittest.mock.patch.object(src.charm.OpenCTICharm, "_is_platform_healthy", mock):
        yield mock
