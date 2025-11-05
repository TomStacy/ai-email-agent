"""Fetcher for individual email operations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.auth.graph_client import GraphApiClient

from .models import Email, EmailBody


class EmailFetcher:
    """Fetches individual email details via Microsoft Graph API."""

    # Default fields to select for email retrieval
    DEFAULT_SELECT_FIELDS = [
        "id",
        "subject",
        "from",
        "sender",
        "toRecipients",
        "ccRecipients",
        "bccRecipients",
        "receivedDateTime",
        "sentDateTime",
        "hasAttachments",
        "importance",
        "isRead",
        "bodyPreview",
        "body",
        "categories",
        "parentFolderId",
        "conversationId",
        "internetMessageId",
        "webLink",
    ]

    def __init__(
        self,
        graph_client: GraphApiClient,
        user_id: str | None = None,
    ) -> None:
        """Initialize the EmailFetcher.

        Args:
            graph_client: Authenticated Graph API client
            user_id: Optional user ID (defaults to "me" for current user)
        """
        self._client = graph_client
        self._user_id = user_id or "me"

    def fetch_email(
        self,
        email_id: str,
        select_fields: Sequence[str] | None = None,
    ) -> Email | None:
        """Fetch a single email by ID with full details.

        Args:
            email_id: The email message ID
            select_fields: Optional list of fields to select (uses defaults if not provided)

        Returns:
            Email object or None if not found
        """
        path = f"{self._user_id}/messages/{email_id}"
        params: dict[str, Any] = {}

        if select_fields:
            params["$select"] = ",".join(select_fields)
        else:
            params["$select"] = ",".join(self.DEFAULT_SELECT_FIELDS)

        try:
            result = self._client.request("GET", path, params=params)
            if isinstance(result, Mapping):
                return Email.from_graph_api(dict(result))
        except Exception:
            # Email not found or error
            return None

        return None

    def fetch_email_body(
        self,
        email_id: str,
        body_type: str | None = None,
    ) -> EmailBody | None:
        """Fetch only the body of an email.

        Args:
            email_id: The email message ID
            body_type: Optional body type preference ("text" or "html")

        Returns:
            EmailBody object or None if not found
        """
        path = f"{self._user_id}/messages/{email_id}"
        params: dict[str, Any] = {
            "$select": "body",
        }

        try:
            result = self._client.request("GET", path, params=params)
            if isinstance(result, Mapping):
                body_data = result.get("body")
                if isinstance(body_data, dict):
                    content_type = str(body_data.get("contentType", "text")).lower()
                    content = str(body_data.get("content", ""))

                    # If user prefers a specific type and it matches, return it
                    if body_type and content_type != body_type.lower():
                        # Could implement conversion here in the future
                        pass

                    return EmailBody(content=content, content_type=content_type)
        except Exception:
            return None

        return None

    def fetch_attachments_metadata(
        self,
        email_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch metadata about email attachments (without downloading).

        Args:
            email_id: The email message ID

        Returns:
            List of attachment metadata dictionaries
        """
        path = f"{self._user_id}/messages/{email_id}/attachments"
        params: dict[str, Any] = {
            "$select": "id,name,contentType,size,isInline",
        }

        try:
            result = self._client.request("GET", path, params=params)
            if isinstance(result, Mapping):
                value = result.get("value", [])
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        except Exception:
            return []

        return []

    def fetch_multiple_emails(
        self,
        email_ids: Sequence[str],
        select_fields: Sequence[str] | None = None,
    ) -> list[Email]:
        """Fetch multiple emails by their IDs.

        Note: Currently fetches emails sequentially. Could be optimized with batch requests.

        Args:
            email_ids: List of email message IDs
            select_fields: Optional list of fields to select

        Returns:
            List of Email objects (excludes not found emails)
        """
        emails: list[Email] = []

        for email_id in email_ids:
            email = self.fetch_email(email_id, select_fields=select_fields)
            if email:
                emails.append(email)

        return emails

    def fetch_email_raw(
        self,
        email_id: str,
    ) -> dict[str, Any] | None:
        """Fetch raw email data as a dictionary.

        Useful for debugging or when you need fields not in the Email model.

        Args:
            email_id: The email message ID

        Returns:
            Raw email data dictionary or None if not found
        """
        path = f"{self._user_id}/messages/{email_id}"

        try:
            result = self._client.request("GET", path)
            if isinstance(result, Mapping):
                return dict(result)
        except Exception:
            return None

        return None

    def check_email_exists(self, email_id: str) -> bool:
        """Check if an email exists.

        Args:
            email_id: The email message ID

        Returns:
            True if email exists, False otherwise
        """
        path = f"{self._user_id}/messages/{email_id}"
        params: dict[str, Any] = {
            "$select": "id",
        }

        try:
            result = self._client.request("GET", path, params=params)
            return isinstance(result, Mapping) and "id" in result
        except Exception:
            return False
