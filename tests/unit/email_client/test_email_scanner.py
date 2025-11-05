"""Unit tests for email_client.email_scanner module."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.email_client.email_scanner import EmailScanner
from src.email_client.folder_manager import FolderManager
from src.email_client.models import Folder, ScanResult


@pytest.fixture
def mock_graph_client():
    """Create a mock GraphApiClient."""
    return MagicMock()


@pytest.fixture
def mock_folder_manager():
    """Create a mock FolderManager."""
    manager = MagicMock(spec=FolderManager)
    # Mock inbox folder
    inbox = Folder(
        id="inbox-123",
        display_name="Inbox",
        parent_folder_id="root",
        child_folder_count=0,
        unread_item_count=10,
        total_item_count=100,
    )
    manager.get_inbox_folder.return_value = inbox
    manager.get_folder_by_id.return_value = inbox
    return manager


@pytest.fixture
def email_scanner(mock_graph_client, mock_folder_manager):
    """Create an EmailScanner instance with mocked dependencies."""
    return EmailScanner(
        mock_graph_client,
        folder_manager=mock_folder_manager,
        max_emails=10,
        batch_size=5,
    )


@pytest.fixture
def sample_emails_response():
    """Sample emails response from Graph API."""
    return {
        "value": [
            {
                "id": f"email-{i}",
                "subject": f"Test Email {i}",
                "sender": {
                    "emailAddress": {"name": "Sender", "address": "sender@example.com"}
                },
                "receivedDateTime": "2024-01-15T10:30:00Z",
                "hasAttachments": False,
                "importance": "normal",
                "isRead": False,
            }
            for i in range(5)
        ]
    }


class TestEmailScanner:
    """Tests for EmailScanner class."""

    def test_scan_inbox(
        self, email_scanner, mock_graph_client, mock_folder_manager, sample_emails_response
    ):
        """Test scanning the inbox folder."""
        mock_graph_client.request.return_value = sample_emails_response

        result = email_scanner.scan_inbox(show_progress=False)

        assert isinstance(result, ScanResult)
        assert len(result.emails) == 5
        assert result.scanned_count == 5
        assert result.skipped_count == 0
        assert result.folder_id == "inbox-123"

        # Verify folder manager was called
        mock_folder_manager.get_inbox_folder.assert_called_once()

    def test_scan_inbox_not_found(self, email_scanner, mock_folder_manager):
        """Test scanning when inbox folder not found."""
        mock_folder_manager.get_inbox_folder.return_value = None

        result = email_scanner.scan_inbox(show_progress=False)

        assert len(result.emails) == 0
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_scan_folder(self, email_scanner, mock_graph_client, sample_emails_response):
        """Test scanning a specific folder."""
        mock_graph_client.request.return_value = sample_emails_response

        result = email_scanner.scan_folder(
            folder_id="inbox-123", folder_name="Inbox", show_progress=False
        )

        assert isinstance(result, ScanResult)
        assert len(result.emails) == 5
        assert result.folder_id == "inbox-123"
        assert result.folder_name == "Inbox"

        # Verify API call
        mock_graph_client.request.assert_called()
        call_args = mock_graph_client.request.call_args
        assert "mailFolders/inbox-123/messages" in call_args[0][1]

    def test_scan_folder_with_pagination(self, email_scanner, mock_graph_client):
        """Test scanning with pagination."""
        page1 = {
            "value": [
                {
                    "id": "email-1",
                    "subject": "Email 1",
                    "receivedDateTime": "2024-01-15T10:30:00Z",
                    "hasAttachments": False,
                    "importance": "normal",
                    "isRead": False,
                }
            ],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/messages?$skip=1",
        }
        page2 = {
            "value": [
                {
                    "id": "email-2",
                    "subject": "Email 2",
                    "receivedDateTime": "2024-01-15T10:29:00Z",
                    "hasAttachments": False,
                    "importance": "normal",
                    "isRead": False,
                }
            ]
        }

        mock_graph_client.request.side_effect = [page1, page2]

        result = email_scanner.scan_folder(
            folder_id="inbox-123", max_emails=10, show_progress=False
        )

        assert len(result.emails) == 2
        assert result.emails[0].id == "email-1"
        assert result.emails[1].id == "email-2"
        # Should have made 2 API calls
        assert mock_graph_client.request.call_count == 2

    def test_scan_folder_respects_max_emails(self, email_scanner, mock_graph_client):
        """Test that scanning respects max_emails limit."""
        # Create response with 10 emails
        large_response = {
            "value": [
                {
                    "id": f"email-{i}",
                    "subject": f"Email {i}",
                    "receivedDateTime": "2024-01-15T10:30:00Z",
                    "hasAttachments": False,
                    "importance": "normal",
                    "isRead": False,
                }
                for i in range(10)
            ]
        }
        mock_graph_client.request.return_value = large_response

        # Scan with limit of 5
        result = email_scanner.scan_folder(
            folder_id="inbox-123", max_emails=5, show_progress=False
        )

        assert len(result.emails) == 5

    def test_scan_with_filter(
        self, email_scanner, mock_graph_client, mock_folder_manager, sample_emails_response
    ):
        """Test scanning with OData filter."""
        mock_graph_client.request.return_value = sample_emails_response

        result = email_scanner.scan_with_filter(
            filter_query="isRead eq false", show_progress=False
        )

        assert len(result.emails) == 5

        # Verify API call includes filter
        call_args = mock_graph_client.request.call_args
        params = call_args[1]["params"]
        assert "$filter" in params
        assert params["$filter"] == "isRead eq false"

    def test_scan_with_filter_custom_folder(
        self, email_scanner, mock_graph_client, mock_folder_manager, sample_emails_response
    ):
        """Test scanning with filter on custom folder."""
        mock_graph_client.request.return_value = sample_emails_response

        result = email_scanner.scan_with_filter(
            filter_query="importance eq 'high'", folder_id="custom-123", show_progress=False
        )

        assert len(result.emails) == 5
        assert result.folder_id == "custom-123"

    def test_scan_unread_emails(
        self, email_scanner, mock_graph_client, mock_folder_manager, sample_emails_response
    ):
        """Test scanning only unread emails."""
        mock_graph_client.request.return_value = sample_emails_response

        result = email_scanner.scan_unread_emails(show_progress=False)

        assert len(result.emails) == 5

        # Verify correct filter was applied
        call_args = mock_graph_client.request.call_args
        params = call_args[1]["params"]
        assert "$filter" in params
        assert params["$filter"] == "isRead eq false"

    def test_scan_folder_with_malformed_email(self, email_scanner, mock_graph_client):
        """Test handling of malformed email data."""
        malformed_response = {
            "value": [
                {
                    "id": "email-1",
                    "subject": "Good Email",
                    "receivedDateTime": "2024-01-15T10:30:00Z",
                    "hasAttachments": False,
                    "importance": "normal",
                    "isRead": False,
                },
                {
                    # Missing required 'id' field
                    "subject": "Bad Email",
                },
                {
                    "id": "email-3",
                    "subject": "Another Good Email",
                    "receivedDateTime": "2024-01-15T10:30:00Z",
                    "hasAttachments": False,
                    "importance": "normal",
                    "isRead": False,
                },
            ]
        }
        mock_graph_client.request.return_value = malformed_response

        result = email_scanner.scan_folder(folder_id="inbox-123", show_progress=False)

        # Should have 2 valid emails and 1 skipped
        assert len(result.emails) == 2
        assert result.skipped_count == 1
        assert len(result.errors) > 0

    def test_scan_folder_empty_result(self, email_scanner, mock_graph_client):
        """Test scanning folder with no emails."""
        mock_graph_client.request.return_value = {"value": []}

        result = email_scanner.scan_folder(folder_id="empty-folder", show_progress=False)

        assert len(result.emails) == 0
        assert result.scanned_count == 0

    @patch.dict(os.environ, {"MAX_EMAILS_PER_SCAN": "50", "SCAN_BATCH_SIZE": "25"})
    def test_scanner_uses_env_variables(self, mock_graph_client, mock_folder_manager):
        """Test that scanner respects environment variables."""
        scanner = EmailScanner(mock_graph_client, folder_manager=mock_folder_manager)

        assert scanner._max_emails == 50
        assert scanner._batch_size == 25

    @patch.dict(os.environ, {"INCLUDE_BODY_IN_SCAN": "true"})
    def test_scanner_includes_body_from_env(self, mock_graph_client, mock_folder_manager):
        """Test that scanner includes body when env variable is set."""
        scanner = EmailScanner(mock_graph_client, folder_manager=mock_folder_manager)

        assert scanner._include_body is True

    def test_scan_result_has_more(self, email_scanner, mock_graph_client):
        """Test that has_more flag is set when there are more results."""
        response_with_next = {
            "value": [
                {
                    "id": f"email-{i}",
                    "subject": f"Email {i}",
                    "receivedDateTime": "2024-01-15T10:30:00Z",
                    "hasAttachments": False,
                    "importance": "normal",
                    "isRead": False,
                }
                for i in range(5)
            ],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/messages?$skip=5",
        }
        mock_graph_client.request.return_value = response_with_next

        # Scan with limit equal to response size
        result = email_scanner.scan_folder(
            folder_id="inbox-123", max_emails=5, show_progress=False
        )

        assert result.has_more is True
        assert result.next_link is not None
