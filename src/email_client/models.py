"""Data models for email client operations."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EmailAddress:
    """Represents an email address with name and address."""

    name: str | None
    address: str


@dataclass
class EmailBody:
    """Represents email body content."""

    content: str
    content_type: str  # "text" or "html"


@dataclass
class Email:
    """Represents an email message from Microsoft Graph API."""

    id: str
    subject: str | None
    sender: EmailAddress | None
    from_address: EmailAddress | None
    to_recipients: list[EmailAddress]
    cc_recipients: list[EmailAddress]
    bcc_recipients: list[EmailAddress]
    received_datetime: datetime | None
    sent_datetime: datetime | None
    has_attachments: bool
    importance: str  # "low", "normal", "high"
    is_read: bool
    body_preview: str | None
    body: EmailBody | None = None
    categories: list[str] = field(default_factory=list)
    folder_id: str | None = None
    conversation_id: str | None = None
    internet_message_id: str | None = None
    web_link: str | None = None

    @classmethod
    def from_graph_api(cls, data: dict[str, Any]) -> Email:
        """Create an Email instance from Microsoft Graph API response."""
        # Parse sender
        sender_data = data.get("sender")
        sender = None
        if sender_data and isinstance(sender_data, dict):
            email_data = sender_data.get("emailAddress", {})
            if isinstance(email_data, dict):
                sender = EmailAddress(
                    name=email_data.get("name"),
                    address=str(email_data.get("address", "")),
                )

        # Parse from address
        from_data = data.get("from")
        from_address = None
        if from_data and isinstance(from_data, dict):
            email_data = from_data.get("emailAddress", {})
            if isinstance(email_data, dict):
                from_address = EmailAddress(
                    name=email_data.get("name"),
                    address=str(email_data.get("address", "")),
                )

        # Parse recipients
        def parse_recipients(recipient_list: Any) -> list[EmailAddress]:
            if not isinstance(recipient_list, list):
                return []
            recipients = []
            for recipient in recipient_list:
                if isinstance(recipient, dict):
                    email_data = recipient.get("emailAddress", {})
                    if isinstance(email_data, dict) and email_data.get("address"):
                        recipients.append(
                            EmailAddress(
                                name=email_data.get("name"),
                                address=str(email_data.get("address")),
                            )
                        )
            return recipients

        to_recipients = parse_recipients(data.get("toRecipients", []))
        cc_recipients = parse_recipients(data.get("ccRecipients", []))
        bcc_recipients = parse_recipients(data.get("bccRecipients", []))

        # Parse body
        body = None
        body_data = data.get("body")
        if body_data and isinstance(body_data, dict):
            body = EmailBody(
                content=str(body_data.get("content", "")),
                content_type=str(body_data.get("contentType", "text")).lower(),
            )

        # Parse datetimes
        received_datetime = None
        if data.get("receivedDateTime"):
            with contextlib.suppress(ValueError, AttributeError):
                received_datetime = datetime.fromisoformat(
                    str(data["receivedDateTime"]).replace("Z", "+00:00")
                )

        sent_datetime = None
        if data.get("sentDateTime"):
            with contextlib.suppress(ValueError, AttributeError):
                sent_datetime = datetime.fromisoformat(
                    str(data["sentDateTime"]).replace("Z", "+00:00")
                )

        return cls(
            id=str(data["id"]),
            subject=data.get("subject"),
            sender=sender,
            from_address=from_address,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            received_datetime=received_datetime,
            sent_datetime=sent_datetime,
            has_attachments=bool(data.get("hasAttachments", False)),
            importance=str(data.get("importance", "normal")).lower(),
            is_read=bool(data.get("isRead", False)),
            body_preview=data.get("bodyPreview"),
            body=body,
            categories=list(data.get("categories", [])),
            folder_id=data.get("parentFolderId"),
            conversation_id=data.get("conversationId"),
            internet_message_id=data.get("internetMessageId"),
            web_link=data.get("webLink"),
        )


@dataclass
class Folder:
    """Represents a mail folder from Microsoft Graph API."""

    id: str
    display_name: str
    parent_folder_id: str | None
    child_folder_count: int
    unread_item_count: int
    total_item_count: int
    is_hidden: bool = False

    @classmethod
    def from_graph_api(cls, data: dict[str, Any]) -> Folder:
        """Create a Folder instance from Microsoft Graph API response."""
        return cls(
            id=str(data["id"]),
            display_name=str(data.get("displayName", "")),
            parent_folder_id=data.get("parentFolderId"),
            child_folder_count=int(data.get("childFolderCount", 0)),
            unread_item_count=int(data.get("unreadItemCount", 0)),
            total_item_count=int(data.get("totalItemCount", 0)),
            is_hidden=bool(data.get("isHidden", False)),
        )


@dataclass
class ScanResult:
    """Represents the result of an email scan operation."""

    emails: list[Email]
    total_count: int
    scanned_count: int
    skipped_count: int
    folder_id: str | None = None
    folder_name: str | None = None
    has_more: bool = False
    next_link: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the scan."""
        if self.scanned_count == 0:
            return 0.0
        return (self.scanned_count - self.skipped_count) / self.scanned_count * 100
