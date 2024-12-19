# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""OpenCTI API client."""

import secrets
import textwrap
import typing
import urllib.parse

import requests


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
        self._query_url = urllib.parse.urljoin(url, "graphql")
        self._api_token = api_token
        self._cached_users: list[OpenctiUser] | None = None
        self._cached_groups: list[OpenctiGroup] | None = None

    def _graphql(
        self,
        query_id: str,
        query: str,
        variables: dict | None = None,
    ) -> dict:
        """Call the OpenCTI GraphQL endpoint.

        Args:
            query_id: GraphQL id.
            query: GraphQL query.
            variables: GraphQL variables.

        Returns:
            data in GraphQL response.

        Raises:
            GraphqlError: errors returned in GraphQL response.
        """
        variables = variables or {}
        response = requests.post(
            self._query_url,
            json={"id": query_id, "query": query, "variables": variables},
            headers={"Authorization": f"Bearer {self._api_token}"},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        if "errors" in result:
            raise GraphqlError(result["errors"])
        return result["data"]

    def list_users(self) -> list[OpenctiUser]:
        """List OpenCTI users.

        Returns:
            list of OpenctiUser objects.
        """
        if self._cached_users is not None:
            return self._cached_users
        query = textwrap.dedent(
            """\
            query ListUsers {
              users {
                edges {
                  node {
                    id
                    name
                    user_email
                    account_status
                    api_token
                  }
                }
              }
            }
            """
        )
        data = self._graphql("ListUsers", query=query)
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
        self._cached_users = users
        return users

    def create_user(
        self,
        name: str,
        user_email: str | None = None,
        groups: list[str] | None = None,
    ) -> None:
        """Create a OpenCTI user.

        Args:
            name: User name.
            user_email: User's email address.
            groups: User's groups.
        """
        self._cached_users = None
        if user_email is None:
            user_email = f"{name}@opencti.local"
        if groups is None:
            groups = []
        query = textwrap.dedent(
            """\
            mutation UserCreationMutation(
              $input: UserAddInput!
            ) {
              userAdd(input: $input) {
                ...UserLine_node
                id
              }
            }
            fragment UserLine_node on User {
              id
              name
              user_email
              firstname
              external
              lastname
              effective_confidence_level {
                max_confidence
              }
              otp_activated
              created_at
            }
        """
        )
        variables = {
            "input": {
                "name": name,
                "user_email": user_email,
                "firstname": "",
                "lastname": "",
                "description": "",
                "password": secrets.token_urlsafe(32),
                "account_status": "Active",
                "account_lock_after_date": None,
                "objectOrganization": [],
                "groups": groups,
                "user_confidence_level": None,
            }
        }
        self._graphql("UserCreationMutation", query=query, variables=variables)

    def list_groups(self) -> list[OpenctiGroup]:
        """List OpenCTI groups.

        Returns:
            list of OpenctiGroup objects.
        """
        if self._cached_groups is not None:
            return self._cached_groups
        query = textwrap.dedent(
            """\
            query ListGroups {
              groups {
                edges {
                  node {
                    id
                    name
                  }
                }
              }
            }
            """
        )
        data = self._graphql("ListGroups", query=query)
        groups = []
        for group in data["groups"]["edges"]:
            group = group["node"]
            groups.append(OpenctiGroup(id=group["id"], name=group["name"]))
        self._cached_groups = groups
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
        self._cached_users = None
        query = textwrap.dedent(
            """
        mutation UserEditionOverviewFieldPatchMutation(
          $id: ID!
          $input: [EditInput]!
        ) {
          userEdit(id: $id) {
            fieldPatch(input: $input) {
              ...UserEditionOverview_user
              ...UserEdition_user
              id
            }
          }
        }
        fragment UserEditionGroups_user_2AtC8h on User {
          id
          objectOrganization(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
                grantable_groups {
                  id
                  name
                  group_confidence_level {
                    max_confidence
                  }
                }
              }
            }
          }
          roles(orderBy: name, orderMode: asc) {
            id
            name
          }
          groups(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
              }
            }
          }
          effective_confidence_level {
            max_confidence
            source {
              type
              object {
                __typename
                ... on User {
                  entity_type
                  id
                  name
                }
                ... on Group {
                  entity_type
                  id
                  name
                }
              }
            }
          }
        }
        fragment UserEditionOrganizationsAdmin_user_Z483F on User {
          id
          user_email
          objectOrganization(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
                description
                authorized_authorities
              }
            }
          }
        }
        fragment UserEditionOverview_user on User {
          id
          name
          description
          external
          user_email
          firstname
          lastname
          language
          theme
          api_token
          otp_activated
          stateless_session
          otp_qr
          account_status
          account_lock_after_date
          roles(orderBy: name, orderMode: asc) {
            id
            name
          }
          objectOrganization(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
              }
            }
          }
          groups(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        fragment UserEditionOverview_user_2AtC8h on User {
          id
          name
          description
          external
          user_email
          firstname
          lastname
          language
          theme
          api_token
          otp_activated
          stateless_session
          otp_qr
          account_status
          account_lock_after_date
          roles(orderBy: name, orderMode: asc) {
            id
            name
          }
          objectOrganization(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
              }
            }
          }
          groups(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        fragment UserEditionPassword_user on User {
          id
        }
        fragment UserEdition_user on User {
          id
          external
          user_confidence_level {
            max_confidence
            overrides {
              max_confidence
              entity_type
            }
          }
          effective_confidence_level {
            max_confidence
            overrides {
              max_confidence
              entity_type
              source {
                type
                object {
                  __typename
                  ... on User {
                    entity_type
                    id
                    name
                  }
                  ... on Group {
                    entity_type
                    id
                    name
                  }
                }
              }
            }
            source {
              type
              object {
                __typename
                ... on User {
                  entity_type
                  id
                  name
                }
                ... on Group {
                  entity_type
                  id
                  name
                }
              }
            }
          }
          groups(orderBy: name, orderMode: asc) {
            edges {
              node {
                id
                name
              }
            }
          }
          ...UserEditionOverview_user_2AtC8h
          ...UserEditionPassword_user
          ...UserEditionGroups_user_2AtC8h
          ...UserEditionOrganizationsAdmin_user_Z483F
          editContext {
            name
            focusOn
          }
        }
        """
        )
        self._graphql(
            query_id="UserEditionOverviewFieldPatchMutation",
            query=query,
            variables={
                "id": user_id,
                "input": {"key": "account_status", "value": status},
            },
        )
