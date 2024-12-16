# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm unit tests."""
import typing
import unittest.mock
from unittest.mock import MagicMock

import pytest

import src.charm
import opencti

from opencti import OpenctiUser, OpenctiGroup


@pytest.fixture(scope="function", autouse=True)
def juju_version(monkeypatch):
    """Patch JUJU_VERSION environment variable."""
    monkeypatch.setenv("JUJU_VERSION", "3.3.0")


@pytest.fixture(scope="function")
def patch_check_platform_health():
    """Patch OpenCTICharm._check_platform_health function."""
    mock = MagicMock()
    with unittest.mock.patch.object(src.charm.OpenCTICharm, "_check_platform_health", mock):
        yield mock


@pytest.fixture(scope="function")
def patch_opencti_client():
    """Patch OpenctiClient class."""
    with unittest.mock.patch.object(opencti, "OpenctiClient", OpenctiClientMock):
        yield OpenctiClientMock()


class OpenctiClientMock:
    _users = [
        {
            "id": "88ec0c6a-13ce-5e39-b486-354fe4a7084f",
            "name": "admin",
            "user_email": "admin@example.com",
            "account_status": "Active",
            "api_token": "a614ebcb-d597-4011-a626-c5302959efa6",
        },
    ]
    _groups = [
        {"name": "Administrators", "id": "35c94569-bbdd-4535-9def-26b781359a5b"},
        {"name": "Connectors", "id": "f4fb5f8d-91f5-441e-8ef9-93c283476110"},
        {"name": "Default", "id": "1e257543-6bfb-46f2-a25f-5d50bb0819bd"},
    ]

    def __init__(self, *args, **kwargs):
        pass

    def list_users(self):
        return [OpenctiUser(**u) for u in self._users]

    def list_groups(self):
        return [OpenctiGroup(**g) for g in self._groups]

    def create_user(
        self,
        name: str,
        user_email: str | None = None,
        groups: list[str] | None = None,
    ):
        new_user = {
            "name": name,
            "id": "00000000-0000-0000-0000-000000000000",
            "user_email": user_email or f"{name}@opencti.local",
            "account_status": "Active",
            "api_token": "00000000-0000-0000-0000-000000000000",
        }
        self._users.append(new_user)

    def set_account_status(
        self,
        user_id: str,
        status: typing.Literal["Active", "Inactive"],
    ) -> None:
        for user in self._users:
            if user["id"] == user_id:
                user["account_status"] = status
                return
        raise RuntimeError(f"Unknown user id: {user_id}")
