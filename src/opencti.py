# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI API client."""

import functools
import logging
import pathlib
import secrets
import typing
import urllib.parse

import gql
import gql.dsl
import gql.transport.requests
import graphql

gql.transport.requests.log.setLevel(logging.WARNING)


class OpenctiUser(typing.NamedTuple):
    """Opencti user.

    Attributes:
        id: opencti user id
        name: opencti username
        user_email: opencti user email
        account_status: opencti account status
        api_token: opencti user api token
    """

    id: str
    name: str
    user_email: str
    account_status: str
    api_token: str


class OpenctiGroup(typing.NamedTuple):
    """Opencti group.

    Attributes:
        id: opencti group id
        name: opencti group name
    """

    id: str
    name: str


class GraphqlError(Exception):
    """GraphQL error."""


class OpenctiClient:
    """Opencti API client."""

    def __init__(self, url: str, api_token: str) -> None:
        """Construct the Opencti client.

        Args:
            url: URL of the Opencti API.
            api_token: Opencti API token.
        """
        url = url + "/" if len(url) > 0 and url[-1] != "/" else url
        transport = gql.transport.requests.RequestsHTTPTransport(
            url=urllib.parse.urljoin(url, "graphql"),
            headers={"Authorization": f"Bearer {api_token}"},
        )
        self._client = gql.Client(
            transport=transport,
            schema=(pathlib.Path(__file__).parent / "opencti.graphql").read_text(),
        )
        self._dsl_schema = gql.dsl.DSLSchema(
            typing.cast(graphql.GraphQLSchema, self._client.schema)
        )

    @functools.lru_cache(maxsize=10)
    def list_users(self, name_starts_with: str | None = None) -> list[OpenctiUser]:
        """List OpenCTI users.

        Args:
            name_starts_with: list users with name starts with.

        Returns:
            list of OpenctiUser objects.
        """
        filters = None
        if name_starts_with:
            filters = {
                "mode": "and",
                "filters": [
                    {
                        "key": "name",
                        "values": name_starts_with,
                        "operator": "starts_with",
                        "mode": "and",
                    }
                ],
                "filterGroups": [],
            }
        query = gql.dsl.dsl_gql(
            gql.dsl.DSLQuery(
                self._dsl_schema.Query.users(filters=filters).select(
                    self._dsl_schema.UserConnection.edges.select(
                        self._dsl_schema.UserEdge.node.select(
                            self._dsl_schema.User.id,
                            self._dsl_schema.User.name,
                            self._dsl_schema.User.user_email,
                            self._dsl_schema.User.account_status,
                            self._dsl_schema.User.api_token,
                        ),
                    ),
                )
            )
        )
        data = self._client.execute(query)
        users = []
        for user in data["users"]["edges"]:
            node = user["node"]
            users.append(
                OpenctiUser(
                    id=node["id"],
                    name=node["name"],
                    user_email=node["user_email"],
                    account_status=node["account_status"],
                    api_token=node["api_token"],
                )
            )
        return users

    def create_user(
        self,
        name: str,
        user_email: str | None = None,
        groups: list[str] | None = None,
    ) -> OpenctiUser:
        """Create a OpenCTI user.

        Args:
            name: User name.
            user_email: User's email address.
            groups: User's groups.

        Returns:
            new user.
        """
        self.list_users.cache_clear()
        if user_email is None:
            user_email = f"{name}@opencti.local"
        if groups is None:
            groups = []
        query = gql.dsl.dsl_gql(
            gql.dsl.DSLMutation(
                self._dsl_schema.Mutation.userAdd.args(
                    input={
                        "name": name,
                        "user_email": user_email,
                        "first_name": "",
                        "last_name": "",
                        "password": secrets.token_urlsafe(32),
                        "account_status": "Active",
                        "groups": groups,
                    }
                ).select(
                    self._dsl_schema.User.id,
                    self._dsl_schema.User.name,
                    self._dsl_schema.User.user_email,
                    self._dsl_schema.User.account_status,
                    self._dsl_schema.User.api_token,
                )
            )
        )
        result = self._client.execute(query)
        user = result["userAdd"]
        return OpenctiUser(
            id=user["id"],
            name=user["name"],
            user_email=user["user_email"],
            account_status=user["account_status"],
            api_token=user["api_token"],
        )

    @functools.lru_cache(maxsize=10)
    def list_groups(self) -> list[OpenctiGroup]:
        """List OpenCTI groups.

        Returns:
            list of OpenctiGroup objects.
        """
        query = gql.dsl.dsl_gql(
            gql.dsl.DSLQuery(
                self._dsl_schema.Query.groups.select(
                    self._dsl_schema.GroupConnection.edges.select(
                        self._dsl_schema.GroupEdge.node.select(
                            self._dsl_schema.Group.id, self._dsl_schema.Group.name
                        )
                    )
                )
            )
        )
        data = self._client.execute(query)
        groups = []
        for group in data["groups"]["edges"]:
            group = group["node"]
            groups.append(OpenctiGroup(id=group["id"], name=group["name"]))
        return groups

    def set_account_status(
        self,
        user_id: str,
        status: typing.Literal["Active", "Inactive"],
    ) -> None:
        """Set Opencti account status.

        Args:
            user_id: Opencti user id.
            status: Opencti account status.
        """
        self.list_users.cache_clear()
        query = gql.dsl.dsl_gql(
            gql.dsl.DSLMutation(
                self._dsl_schema.Mutation.userEdit(id=user_id).select(
                    self._dsl_schema.UserEditMutations.fieldPatch(
                        input=[
                            {
                                "key": "account_status",
                                "value": status,
                                "operation": "replace",
                            }
                        ]
                    ).select(self._dsl_schema.User.id)
                )
            )
        )
        self._client.execute(query)
