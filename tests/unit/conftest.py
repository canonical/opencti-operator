# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm unit tests."""

import typing
import unittest.mock
from unittest.mock import MagicMock

import pytest

import opencti
import src.charm
from opencti import OpenctiGroup, OpenctiUser


@pytest.fixture(scope="function", autouse=True)
def juju_version(monkeypatch):
    """Patch JUJU_VERSION environment variable."""
    monkeypatch.setenv("JUJU_VERSION", "3.3.0")


@pytest.fixture(scope="function", autouse=True)
def patch_is_platform_healthy():
    """Patch OpenCTICharm.is_platform_healthy function."""
    mock = MagicMock(return_value=True)
    with unittest.mock.patch.object(src.charm.OpenCTICharm, "_is_platform_healthy", mock):
        yield mock


@pytest.fixture(scope="function", autouse=True)
def patch_opencti_client():
    """Patch OpenctiClient class."""
    with unittest.mock.patch.object(opencti, "OpenctiClient", OpenctiClientMock):
        yield OpenctiClientMock()


class OpenctiClientMock:
    """A mock for OpenctiClient.

    Attributes:
        last_instance (OpenctiClientMock): pointer to most-recently created instance
    """

    last_instance = None

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

    def __init__(self, *_args, **_kwargs):
        """Initialize OpenctiClientMock."""
        self.init_args = _args
        self.init_kwargs = _kwargs
        OpenctiClientMock.last_instance = self

    def list_users(self, name_starts_with: str | None = None) -> list[OpenctiUser]:
        """List OpenCTI users.

        Args:
            name_starts_with: Name starts with this string.

        Returns:
            A list of OpenctiUser objects.
        """
        return [
            OpenctiUser(**u) for u in self._users if u["name"].startswith(name_starts_with or "")
        ]

    def list_groups(self) -> list[OpenctiGroup]:
        """List OpenCTI groups.

        Returns:
            A list of OpenctiGroup objects.
        """
        return [OpenctiGroup(**g) for g in self._groups]

    def create_user(
        self,
        name: str,
        user_email: str | None = None,
        groups: list[str] | None = None,  # pylint: disable=unused-argument
    ) -> OpenctiUser | None:
        """Create a user.

        Args:
            name: The name of the user.
            user_email: The email address of the user.
            groups: The groups associated with the user.

        Returns:
            The created user.
        """
        new_user = {
            "name": name,
            "id": "00000000-0000-0000-0000-000000000000",
            "user_email": user_email or f"{name}@opencti.local",
            "account_status": "Active",
            "api_token": "00000000-0000-0000-0000-000000000000",
        }
        self._users.append(new_user)
        return OpenctiUser(**new_user)

    def set_account_status(
        self,
        user_id: str,
        status: typing.Literal["Active", "Inactive"],
    ) -> None:
        """Set OpenCTI account status.

        Args:
            user_id: The ID of the user.
            status: The status of the user.

        Raises:
            RuntimeError: If user doesn't exist.
        """
        for user in self._users:
            if user["id"] == user_id:
                user["account_status"] = status
                return
        raise RuntimeError(f"Unknown user id: {user_id}")
