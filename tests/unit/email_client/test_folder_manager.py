"""Unit tests for email_client.folder_manager module."""

from unittest.mock import MagicMock, Mock

import pytest

from src.email_client.folder_manager import FolderManager
from src.email_client.models import Folder


@pytest.fixture
def mock_graph_client():
    """Create a mock GraphApiClient."""
    return MagicMock()


@pytest.fixture
def folder_manager(mock_graph_client):
    """Create a FolderManager instance with mocked client."""
    return FolderManager(mock_graph_client)


@pytest.fixture
def sample_folders_response():
    """Sample folder data from Graph API."""
    return {
        "value": [
            {
                "id": "inbox-123",
                "displayName": "Inbox",
                "parentFolderId": "root",
                "childFolderCount": 2,
                "unreadItemCount": 10,
                "totalItemCount": 100,
                "isHidden": False,
            },
            {
                "id": "sent-456",
                "displayName": "Sent Items",
                "parentFolderId": "root",
                "childFolderCount": 0,
                "unreadItemCount": 0,
                "totalItemCount": 50,
                "isHidden": False,
            },
            {
                "id": "trash-789",
                "displayName": "Deleted Items",
                "parentFolderId": "root",
                "childFolderCount": 0,
                "unreadItemCount": 5,
                "totalItemCount": 20,
                "isHidden": False,
            },
        ]
    }


class TestFolderManager:
    """Tests for FolderManager class."""

    def test_list_folders(self, folder_manager, mock_graph_client, sample_folders_response):
        """Test listing all folders."""
        mock_graph_client.request.return_value = sample_folders_response

        folders = folder_manager.list_folders()

        assert len(folders) == 3
        assert folders[0].display_name == "Inbox"
        assert folders[1].display_name == "Sent Items"
        assert folders[2].display_name == "Deleted Items"

        # Verify API was called correctly
        mock_graph_client.request.assert_called_once()
        call_args = mock_graph_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "mailFolders" in call_args[0][1]

    def test_list_folders_with_cache(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test that list_folders uses cache on second call."""
        mock_graph_client.request.return_value = sample_folders_response

        # First call
        folders1 = folder_manager.list_folders()
        # Second call
        folders2 = folder_manager.list_folders()

        assert len(folders1) == 3
        assert len(folders2) == 3
        # API should only be called once due to caching
        assert mock_graph_client.request.call_count == 1

    def test_list_folders_refresh_cache(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test refreshing the folder cache."""
        mock_graph_client.request.return_value = sample_folders_response

        # First call
        folders1 = folder_manager.list_folders()
        # Second call with refresh
        folders2 = folder_manager.list_folders(refresh_cache=True)

        assert len(folders1) == 3
        assert len(folders2) == 3
        # API should be called twice due to refresh
        assert mock_graph_client.request.call_count == 2

    def test_list_folders_pagination(self, folder_manager, mock_graph_client):
        """Test folder listing with pagination."""
        page1 = {
            "value": [
                {
                    "id": "folder-1",
                    "displayName": "Folder 1",
                    "parentFolderId": "root",
                    "childFolderCount": 0,
                    "unreadItemCount": 0,
                    "totalItemCount": 10,
                }
            ],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/mailFolders?$skip=1",
        }
        page2 = {
            "value": [
                {
                    "id": "folder-2",
                    "displayName": "Folder 2",
                    "parentFolderId": "root",
                    "childFolderCount": 0,
                    "unreadItemCount": 0,
                    "totalItemCount": 5,
                }
            ]
        }

        mock_graph_client.request.side_effect = [page1, page2]

        folders = folder_manager.list_folders()

        assert len(folders) == 2
        assert folders[0].display_name == "Folder 1"
        assert folders[1].display_name == "Folder 2"
        assert mock_graph_client.request.call_count == 2

    def test_get_folder_by_id(self, folder_manager, mock_graph_client):
        """Test getting a folder by ID."""
        folder_data = {
            "id": "inbox-123",
            "displayName": "Inbox",
            "parentFolderId": "root",
            "childFolderCount": 2,
            "unreadItemCount": 10,
            "totalItemCount": 100,
        }
        mock_graph_client.request.return_value = folder_data

        folder = folder_manager.get_folder_by_id("inbox-123")

        assert folder is not None
        assert folder.id == "inbox-123"
        assert folder.display_name == "Inbox"

    def test_get_folder_by_id_not_found(self, folder_manager, mock_graph_client):
        """Test getting a folder that doesn't exist."""
        mock_graph_client.request.side_effect = Exception("Not found")

        folder = folder_manager.get_folder_by_id("nonexistent")

        assert folder is None

    def test_get_folder_by_name(self, folder_manager, mock_graph_client, sample_folders_response):
        """Test getting a folder by name."""
        mock_graph_client.request.return_value = sample_folders_response

        folder = folder_manager.get_folder_by_name("Inbox")

        assert folder is not None
        assert folder.display_name == "Inbox"
        assert folder.id == "inbox-123"

    def test_get_folder_by_name_case_insensitive(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test case-insensitive folder name matching."""
        mock_graph_client.request.return_value = sample_folders_response

        folder = folder_manager.get_folder_by_name("inbox")

        assert folder is not None
        assert folder.display_name == "Inbox"

    def test_get_folder_by_name_case_sensitive(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test case-sensitive folder name matching."""
        mock_graph_client.request.return_value = sample_folders_response

        folder = folder_manager.get_folder_by_name("inbox", case_sensitive=True)

        assert folder is None  # Should not match "Inbox" with "inbox"

    def test_get_inbox_folder(self, folder_manager, mock_graph_client, sample_folders_response):
        """Test getting the inbox folder."""
        mock_graph_client.request.return_value = sample_folders_response

        inbox = folder_manager.get_inbox_folder()

        assert inbox is not None
        assert inbox.display_name == "Inbox"

    def test_get_sent_items_folder(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test getting the sent items folder."""
        mock_graph_client.request.return_value = sample_folders_response

        sent = folder_manager.get_sent_items_folder()

        assert sent is not None
        assert sent.display_name == "Sent Items"

    def test_get_deleted_items_folder(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test getting the deleted items folder."""
        mock_graph_client.request.return_value = sample_folders_response

        deleted = folder_manager.get_deleted_items_folder()

        assert deleted is not None
        assert deleted.display_name == "Deleted Items"

    def test_search_folders(self, folder_manager, mock_graph_client, sample_folders_response):
        """Test searching folders by query."""
        mock_graph_client.request.return_value = sample_folders_response

        results = folder_manager.search_folders("Sent")

        assert len(results) == 1
        assert results[0].display_name == "Sent Items"

    def test_search_folders_case_insensitive(
        self, folder_manager, mock_graph_client, sample_folders_response
    ):
        """Test case-insensitive folder search."""
        mock_graph_client.request.return_value = sample_folders_response

        results = folder_manager.search_folders("deleted")

        assert len(results) == 1
        assert results[0].display_name == "Deleted Items"

    def test_clear_cache(self, folder_manager, mock_graph_client, sample_folders_response):
        """Test clearing the folder cache."""
        mock_graph_client.request.return_value = sample_folders_response

        # Populate cache
        folder_manager.list_folders()
        assert len(folder_manager._folder_cache) > 0

        # Clear cache
        folder_manager.clear_cache()
        assert len(folder_manager._folder_cache) == 0
