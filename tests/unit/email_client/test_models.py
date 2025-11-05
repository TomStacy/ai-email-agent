"""Unit tests for email_client.models module."""

from datetime import datetime

import pytest

from src.email_client.models import Email, EmailAddress, EmailBody, Folder, ScanResult


class TestEmailAddress:
    """Tests for EmailAddress dataclass."""

    def test_create_email_address(self):
        """Test creating an EmailAddress instance."""
        addr = EmailAddress(name="John Doe", address="john@example.com")
        assert addr.name == "John Doe"
        assert addr.address == "john@example.com"

    def test_email_address_no_name(self):
        """Test EmailAddress with no name."""
        addr = EmailAddress(name=None, address="john@example.com")
        assert addr.name is None
        assert addr.address == "john@example.com"


class TestEmailBody:
    """Tests for EmailBody dataclass."""

    def test_create_email_body(self):
        """Test creating an EmailBody instance."""
        body = EmailBody(content="Hello, World!", content_type="text")
        assert body.content == "Hello, World!"
        assert body.content_type == "text"

    def test_email_body_html(self):
        """Test EmailBody with HTML content."""
        body = EmailBody(content="<p>Hello</p>", content_type="html")
        assert body.content == "<p>Hello</p>"
        assert body.content_type == "html"


class TestEmail:
    """Tests for Email dataclass and parsing."""

    def test_from_graph_api_minimal(self):
        """Test parsing minimal email data from Graph API."""
        data = {
            "id": "AAMkADU3",
            "subject": "Test Email",
            "hasAttachments": False,
            "importance": "normal",
            "isRead": False,
        }
        email = Email.from_graph_api(data)
        assert email.id == "AAMkADU3"
        assert email.subject == "Test Email"
        assert email.has_attachments is False
        assert email.importance == "normal"
        assert email.is_read is False

    def test_from_graph_api_full(self):
        """Test parsing complete email data from Graph API."""
        data = {
            "id": "AAMkADU3",
            "subject": "Test Email",
            "sender": {
                "emailAddress": {"name": "John Doe", "address": "john@example.com"}
            },
            "from": {
                "emailAddress": {"name": "John Doe", "address": "john@example.com"}
            },
            "toRecipients": [
                {"emailAddress": {"name": "Jane Smith", "address": "jane@example.com"}}
            ],
            "ccRecipients": [],
            "bccRecipients": [],
            "receivedDateTime": "2024-01-15T10:30:00Z",
            "sentDateTime": "2024-01-15T10:29:55Z",
            "hasAttachments": True,
            "importance": "high",
            "isRead": True,
            "bodyPreview": "This is a test email preview",
            "body": {"contentType": "html", "content": "<p>Test body</p>"},
            "categories": ["Important"],
            "parentFolderId": "inbox-123",
            "conversationId": "conv-456",
            "internetMessageId": "<msg@example.com>",
            "webLink": "https://outlook.office365.com/mail/inbox/id/AAMkADU3",
        }
        email = Email.from_graph_api(data)

        assert email.id == "AAMkADU3"
        assert email.subject == "Test Email"
        assert email.sender is not None
        assert email.sender.name == "John Doe"
        assert email.sender.address == "john@example.com"
        assert len(email.to_recipients) == 1
        assert email.to_recipients[0].address == "jane@example.com"
        assert email.has_attachments is True
        assert email.importance == "high"
        assert email.is_read is True
        assert email.body is not None
        assert email.body.content_type == "html"
        assert "Important" in email.categories

    def test_from_graph_api_datetime_parsing(self):
        """Test datetime parsing from Graph API format."""
        data = {
            "id": "AAMkADU3",
            "receivedDateTime": "2024-01-15T10:30:00Z",
            "sentDateTime": "2024-01-15T10:29:55Z",
            "hasAttachments": False,
            "importance": "normal",
            "isRead": False,
        }
        email = Email.from_graph_api(data)

        assert email.received_datetime is not None
        assert isinstance(email.received_datetime, datetime)
        assert email.sent_datetime is not None
        assert isinstance(email.sent_datetime, datetime)

    def test_from_graph_api_malformed_datetime(self):
        """Test handling of malformed datetime strings."""
        data = {
            "id": "AAMkADU3",
            "receivedDateTime": "invalid-date",
            "hasAttachments": False,
            "importance": "normal",
            "isRead": False,
        }
        email = Email.from_graph_api(data)
        assert email.received_datetime is None

    def test_from_graph_api_missing_recipients(self):
        """Test parsing email with missing recipient fields."""
        data = {
            "id": "AAMkADU3",
            "subject": "Test",
            "hasAttachments": False,
            "importance": "normal",
            "isRead": False,
        }
        email = Email.from_graph_api(data)

        assert email.to_recipients == []
        assert email.cc_recipients == []
        assert email.bcc_recipients == []


class TestFolder:
    """Tests for Folder dataclass and parsing."""

    def test_from_graph_api(self):
        """Test parsing folder data from Graph API."""
        data = {
            "id": "folder-123",
            "displayName": "Inbox",
            "parentFolderId": "root",
            "childFolderCount": 5,
            "unreadItemCount": 10,
            "totalItemCount": 100,
            "isHidden": False,
        }
        folder = Folder.from_graph_api(data)

        assert folder.id == "folder-123"
        assert folder.display_name == "Inbox"
        assert folder.parent_folder_id == "root"
        assert folder.child_folder_count == 5
        assert folder.unread_item_count == 10
        assert folder.total_item_count == 100
        assert folder.is_hidden is False

    def test_from_graph_api_minimal(self):
        """Test parsing minimal folder data."""
        data = {
            "id": "folder-456",
            "displayName": "Archive",
        }
        folder = Folder.from_graph_api(data)

        assert folder.id == "folder-456"
        assert folder.display_name == "Archive"
        assert folder.child_folder_count == 0
        assert folder.unread_item_count == 0
        assert folder.total_item_count == 0


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_create_scan_result(self):
        """Test creating a ScanResult instance."""
        emails = []
        result = ScanResult(
            emails=emails,
            total_count=0,
            scanned_count=10,
            skipped_count=2,
            folder_id="inbox-123",
            folder_name="Inbox",
        )

        assert result.emails == []
        assert result.total_count == 0
        assert result.scanned_count == 10
        assert result.skipped_count == 2
        assert result.folder_id == "inbox-123"
        assert result.folder_name == "Inbox"

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = ScanResult(
            emails=[],
            total_count=0,
            scanned_count=100,
            skipped_count=10,
        )
        assert result.success_rate == 90.0

    def test_success_rate_zero_scanned(self):
        """Test success rate when no emails scanned."""
        result = ScanResult(
            emails=[],
            total_count=0,
            scanned_count=0,
            skipped_count=0,
        )
        assert result.success_rate == 0.0

    def test_scan_result_with_errors(self):
        """Test ScanResult with errors."""
        result = ScanResult(
            emails=[],
            total_count=0,
            scanned_count=5,
            skipped_count=1,
            errors=["Error 1", "Error 2"],
        )
        assert len(result.errors) == 2
        assert "Error 1" in result.errors
