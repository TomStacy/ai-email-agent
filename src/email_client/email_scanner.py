"""Scanner for inbox and folder email operations."""

from __future__ import annotations

import os
from collections.abc import Generator, Mapping
from typing import Any

from tqdm import tqdm  # type: ignore[import-untyped]

from src.auth.graph_client import GraphApiClient

from .folder_manager import FolderManager
from .models import Email, ScanResult


class EmailScanner:
    """Scans mailbox folders for emails via Microsoft Graph API."""

    # Default fields to select during scanning (minimal for performance)
    DEFAULT_SCAN_FIELDS = [
        "id",
        "subject",
        "from",
        "sender",
        "toRecipients",
        "receivedDateTime",
        "sentDateTime",
        "hasAttachments",
        "importance",
        "isRead",
        "bodyPreview",
        "categories",
        "parentFolderId",
        "conversationId",
    ]

    def __init__(
        self,
        graph_client: GraphApiClient,
        folder_manager: FolderManager | None = None,
        user_id: str | None = None,
        max_emails: int | None = None,
        batch_size: int | None = None,
        include_body: bool = False,
    ) -> None:
        """Initialize the EmailScanner.

        Args:
            graph_client: Authenticated Graph API client
            folder_manager: Optional FolderManager instance
            user_id: Optional user ID (defaults to "me" for current user)
            max_emails: Maximum number of emails to scan (from env or default 100)
            batch_size: Number of emails per page (from env or default 50)
            include_body: Whether to include email body in scan (default False)
        """
        self._client = graph_client
        self._folder_manager = folder_manager or FolderManager(graph_client, user_id)
        self._user_id = user_id or "me"

        # Configuration from environment or parameters
        self._max_emails = max_emails or int(os.getenv("MAX_EMAILS_PER_SCAN", "100"))
        self._batch_size = batch_size or int(os.getenv("SCAN_BATCH_SIZE", "50"))
        self._include_body = include_body or os.getenv("INCLUDE_BODY_IN_SCAN", "false").lower() == "true"

    def scan_inbox(
        self,
        max_emails: int | None = None,
        show_progress: bool = True,
    ) -> ScanResult:
        """Scan the inbox folder.

        Args:
            max_emails: Override maximum emails to scan
            show_progress: Whether to show progress bar

        Returns:
            ScanResult object with emails and metadata
        """
        inbox_folder = self._folder_manager.get_inbox_folder()
        if not inbox_folder:
            return ScanResult(
                emails=[],
                total_count=0,
                scanned_count=0,
                skipped_count=0,
                folder_name="Inbox",
                errors=["Inbox folder not found"],
            )

        return self.scan_folder(
            folder_id=inbox_folder.id,
            folder_name=inbox_folder.display_name,
            max_emails=max_emails,
            show_progress=show_progress,
        )

    def scan_folder(
        self,
        folder_id: str,
        folder_name: str | None = None,
        max_emails: int | None = None,
        show_progress: bool = True,
        order_by: str = "receivedDateTime desc",
    ) -> ScanResult:
        """Scan a specific folder for emails.

        Args:
            folder_id: The folder ID to scan
            folder_name: Optional folder display name for result
            max_emails: Override maximum emails to scan
            show_progress: Whether to show progress bar
            order_by: OData orderBy clause (default: newest first)

        Returns:
            ScanResult object with emails and metadata
        """
        limit = max_emails or self._max_emails
        path = f"{self._user_id}/mailFolders/{folder_id}/messages"

        select_fields = self.DEFAULT_SCAN_FIELDS.copy()
        if self._include_body:
            select_fields.append("body")

        params: dict[str, Any] = {
            "$top": min(self._batch_size, limit),
            "$select": ",".join(select_fields),
            "$orderby": order_by,
        }

        emails: list[Email] = []
        errors: list[str] = []
        scanned_count = 0
        skipped_count = 0
        next_link: str | None = None

        # Create progress bar if requested
        pbar = tqdm(total=limit, desc="Scanning emails", disable=not show_progress)

        try:
            for email_batch, batch_next_link in self._fetch_email_pages(path, params, limit):
                for email_data in email_batch:
                    scanned_count += 1

                    try:
                        email = Email.from_graph_api(email_data)
                        emails.append(email)
                    except (KeyError, ValueError) as e:
                        skipped_count += 1
                        errors.append(f"Failed to parse email: {e}")

                    pbar.update(1)

                    if len(emails) >= limit:
                        break

                next_link = batch_next_link
                if len(emails) >= limit:
                    break
        finally:
            pbar.close()

        has_more = next_link is not None and len(emails) >= limit

        return ScanResult(
            emails=emails,
            total_count=len(emails),
            scanned_count=scanned_count,
            skipped_count=skipped_count,
            folder_id=folder_id,
            folder_name=folder_name,
            has_more=has_more,
            next_link=next_link,
            errors=errors,
        )

    def scan_with_filter(
        self,
        filter_query: str,
        folder_id: str | None = None,
        max_emails: int | None = None,
        show_progress: bool = True,
    ) -> ScanResult:
        """Scan emails with an OData filter.

        Args:
            filter_query: OData filter expression (e.g., "isRead eq false")
            folder_id: Optional folder ID to scan (defaults to inbox)
            max_emails: Override maximum emails to scan
            show_progress: Whether to show progress bar

        Returns:
            ScanResult object with filtered emails
        """
        if folder_id is None:
            inbox_folder = self._folder_manager.get_inbox_folder()
            if not inbox_folder:
                return ScanResult(
                    emails=[],
                    total_count=0,
                    scanned_count=0,
                    skipped_count=0,
                    errors=["Inbox folder not found"],
                )
            folder_id = inbox_folder.id
            folder_name: str | None = inbox_folder.display_name
        else:
            folder = self._folder_manager.get_folder_by_id(folder_id)
            folder_name = folder.display_name if folder else None

        limit = max_emails or self._max_emails
        path = f"{self._user_id}/mailFolders/{folder_id}/messages"

        select_fields = self.DEFAULT_SCAN_FIELDS.copy()
        if self._include_body:
            select_fields.append("body")

        params: dict[str, Any] = {
            "$top": min(self._batch_size, limit),
            "$select": ",".join(select_fields),
            "$filter": filter_query,
            "$orderby": "receivedDateTime desc",
        }

        emails: list[Email] = []
        errors: list[str] = []
        scanned_count = 0
        skipped_count = 0
        next_link: str | None = None

        pbar = tqdm(total=limit, desc="Scanning with filter", disable=not show_progress)

        try:
            for email_batch, batch_next_link in self._fetch_email_pages(path, params, limit):
                for email_data in email_batch:
                    scanned_count += 1

                    try:
                        email = Email.from_graph_api(email_data)
                        emails.append(email)
                    except (KeyError, ValueError) as e:
                        skipped_count += 1
                        errors.append(f"Failed to parse email: {e}")

                    pbar.update(1)

                    if len(emails) >= limit:
                        break

                next_link = batch_next_link
                if len(emails) >= limit:
                    break
        finally:
            pbar.close()

        has_more = next_link is not None and len(emails) >= limit

        return ScanResult(
            emails=emails,
            total_count=len(emails),
            scanned_count=scanned_count,
            skipped_count=skipped_count,
            folder_id=folder_id,
            folder_name=folder_name,
            has_more=has_more,
            next_link=next_link,
            errors=errors,
        )

    def scan_unread_emails(
        self,
        folder_id: str | None = None,
        max_emails: int | None = None,
        show_progress: bool = True,
    ) -> ScanResult:
        """Scan only unread emails.

        Args:
            folder_id: Optional folder ID to scan (defaults to inbox)
            max_emails: Override maximum emails to scan
            show_progress: Whether to show progress bar

        Returns:
            ScanResult object with unread emails
        """
        return self.scan_with_filter(
            filter_query="isRead eq false",
            folder_id=folder_id,
            max_emails=max_emails,
            show_progress=show_progress,
        )

    def _fetch_email_pages(
        self,
        path: str,
        params: dict[str, Any],
        max_emails: int,
    ) -> Generator[tuple[list[dict[str, Any]], str | None], None, None]:
        """Generator that yields pages of email data.

        Args:
            path: API endpoint path
            params: Query parameters
            max_emails: Maximum total emails to fetch

        Yields:
            Tuple of (email_batch, next_link)
        """
        next_link: str | None = None
        total_fetched = 0

        while total_fetched < max_emails:
            # Calculate how many more emails we need
            remaining = max_emails - total_fetched
            current_params = params.copy()
            current_params["$top"] = min(current_params.get("$top", self._batch_size), remaining)

            try:
                if next_link:
                    # Graph API next links are full URLs, strip the base
                    result = self._client.request("GET", next_link)
                else:
                    result = self._client.request("GET", path, params=current_params)

                if not isinstance(result, Mapping):
                    break

                value = result.get("value", [])
                if not isinstance(value, list) or len(value) == 0:
                    break

                email_batch = [item for item in value if isinstance(item, dict)]
                total_fetched += len(email_batch)

                next_link = result.get("@odata.nextLink")

                yield email_batch, next_link

                if not next_link:
                    break

            except Exception:
                # Log error but don't crash - return what we have so far
                break
