"""Unit tests for email_client.email_fetcher module."""

from unittest.mock import MagicMock

import pytest

from src.email_client.email_fetcher import EmailFetcher
from src.email_client.models import Email, EmailBody


@pytest.fixture
def mock_graph_client():
    """Create a mock GraphApiClient."""
    return MagicMock()


@pytest.fixture
def email_fetcher(mock_graph_client):
    """Create an EmailFetcher instance with mocked client."""
    return EmailFetcher(mock_graph_client)


@pytest.fixture
def sample_email_response():
    """Sample email data from Graph API."""
    return {
        "id": "AAMkADU3",
        "subject": "Test Email",
        "sender": {"emailAddress": {"name": "John Doe", "address": "john@example.com"}},
        "from": {"emailAddress": {"name": "John Doe", "address": "john@example.com"}},
        "toRecipients": [
            {"emailAddress": {"name": "Jane Smith", "address": "jane@example.com"}}
        ],
        "ccRecipients": [],
        "bccRecipients": [],
        "receivedDateTime": "2024-01-15T10:30:00Z",
        "sentDateTime": "2024-01-15T10:29:55Z",
        "hasAttachments": False,
        "importance": "normal",
        "isRead": False,
        "bodyPreview": "This is a test email",
        "body": {"contentType": "html", "content": "<p>Test body</p>"},
        "categories": [],
        "parentFolderId": "inbox-123",
    }


class TestEmailFetcher:
    """Tests for EmailFetcher class."""

    def test_fetch_email(self, email_fetcher, mock_graph_client, sample_email_response):
        """Test fetching a single email."""
        mock_graph_client.request.return_value = sample_email_response

        email = email_fetcher.fetch_email("AAMkADU3")

        assert email is not None
        assert email.id == "AAMkADU3"
        assert email.subject == "Test Email"
        assert email.sender is not None
        assert email.sender.name == "John Doe"

        # Verify API call
        mock_graph_client.request.assert_called_once()
        call_args = mock_graph_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "AAMkADU3" in call_args[0][1]

    def test_fetch_email_with_custom_fields(
        self, email_fetcher, mock_graph_client, sample_email_response
    ):
        """Test fetching email with custom select fields."""
        mock_graph_client.request.return_value = sample_email_response

        email = email_fetcher.fetch_email("AAMkADU3", select_fields=["id", "subject"])

        assert email is not None

        # Verify API call includes custom fields
        call_args = mock_graph_client.request.call_args
        params = call_args[1]["params"]
        assert "$select" in params
        assert params["$select"] == "id,subject"

    def test_fetch_email_not_found(self, email_fetcher, mock_graph_client):
        """Test fetching a non-existent email."""
        mock_graph_client.request.side_effect = Exception("Not found")

        email = email_fetcher.fetch_email("nonexistent")

        assert email is None

    def test_fetch_email_body(self, email_fetcher, mock_graph_client):
        """Test fetching only email body."""
        body_response = {"body": {"contentType": "text", "content": "Plain text body"}}
        mock_graph_client.request.return_value = body_response

        body = email_fetcher.fetch_email_body("AAMkADU3")

        assert body is not None
        assert isinstance(body, EmailBody)
        assert body.content == "Plain text body"
        assert body.content_type == "text"

        # Verify API call selects only body
        call_args = mock_graph_client.request.call_args
        params = call_args[1]["params"]
        assert params["$select"] == "body"

    def test_fetch_email_body_not_found(self, email_fetcher, mock_graph_client):
        """Test fetching body of non-existent email."""
        mock_graph_client.request.side_effect = Exception("Not found")

        body = email_fetcher.fetch_email_body("nonexistent")

        assert body is None

    def test_fetch_attachments_metadata(self, email_fetcher, mock_graph_client):
        """Test fetching attachment metadata."""
        attachments_response = {
            "value": [
                {
                    "id": "attach-1",
                    "name": "document.pdf",
                    "contentType": "application/pdf",
                    "size": 102400,
                    "isInline": False,
                },
                {
                    "id": "attach-2",
                    "name": "image.png",
                    "contentType": "image/png",
                    "size": 51200,
                    "isInline": True,
                },
            ]
        }
        mock_graph_client.request.return_value = attachments_response

        attachments = email_fetcher.fetch_attachments_metadata("AAMkADU3")

        assert len(attachments) == 2
        assert attachments[0]["name"] == "document.pdf"
        assert attachments[1]["name"] == "image.png"

        # Verify API call
        call_args = mock_graph_client.request.call_args
        assert "attachments" in call_args[0][1]

    def test_fetch_attachments_metadata_no_attachments(self, email_fetcher, mock_graph_client):
        """Test fetching attachments when there are none."""
        mock_graph_client.request.return_value = {"value": []}

        attachments = email_fetcher.fetch_attachments_metadata("AAMkADU3")

        assert len(attachments) == 0

    def test_fetch_attachments_metadata_error(self, email_fetcher, mock_graph_client):
        """Test fetching attachments when error occurs."""
        mock_graph_client.request.side_effect = Exception("Error")

        attachments = email_fetcher.fetch_attachments_metadata("AAMkADU3")

        assert len(attachments) == 0

    def test_fetch_multiple_emails(self, email_fetcher, mock_graph_client, sample_email_response):
        """Test fetching multiple emails by IDs."""
        # Mock returns the same email data for simplicity
        mock_graph_client.request.return_value = sample_email_response

        email_ids = ["email-1", "email-2", "email-3"]
        emails = email_fetcher.fetch_multiple_emails(email_ids)

        assert len(emails) == 3
        # API should be called once per email
        assert mock_graph_client.request.call_count == 3

    def test_fetch_multiple_emails_some_not_found(
        self, email_fetcher, mock_graph_client, sample_email_response
    ):
        """Test fetching multiple emails where some don't exist."""
        # First call succeeds, second fails, third succeeds
        mock_graph_client.request.side_effect = [
            sample_email_response,
            Exception("Not found"),
            sample_email_response,
        ]

        email_ids = ["email-1", "email-2", "email-3"]
        emails = email_fetcher.fetch_multiple_emails(email_ids)

        # Should return only the 2 successful fetches
        assert len(emails) == 2

    def test_fetch_email_raw(self, email_fetcher, mock_graph_client, sample_email_response):
        """Test fetching raw email data as dictionary."""
        mock_graph_client.request.return_value = sample_email_response

        raw_data = email_fetcher.fetch_email_raw("AAMkADU3")

        assert raw_data is not None
        assert isinstance(raw_data, dict)
        assert raw_data["id"] == "AAMkADU3"
        assert raw_data["subject"] == "Test Email"

    def test_fetch_email_raw_not_found(self, email_fetcher, mock_graph_client):
        """Test fetching raw data of non-existent email."""
        mock_graph_client.request.side_effect = Exception("Not found")

        raw_data = email_fetcher.fetch_email_raw("nonexistent")

        assert raw_data is None

    def test_check_email_exists(self, email_fetcher, mock_graph_client):
        """Test checking if an email exists."""
        mock_graph_client.request.return_value = {"id": "AAMkADU3"}

        exists = email_fetcher.check_email_exists("AAMkADU3")

        assert exists is True

        # Verify minimal API call
        call_args = mock_graph_client.request.call_args
        params = call_args[1]["params"]
        assert params["$select"] == "id"

    def test_check_email_exists_not_found(self, email_fetcher, mock_graph_client):
        """Test checking if a non-existent email exists."""
        mock_graph_client.request.side_effect = Exception("Not found")

        exists = email_fetcher.check_email_exists("nonexistent")

        assert exists is False
