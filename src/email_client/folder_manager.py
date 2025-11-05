"""Manager for mailbox folder operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.auth.graph_client import GraphApiClient

from .models import Folder


class FolderManager:
    """Manages mailbox folder operations via Microsoft Graph API."""

    def __init__(
        self,
        graph_client: GraphApiClient,
        user_id: str | None = None,
    ) -> None:
        """Initialize the FolderManager.

        Args:
            graph_client: Authenticated Graph API client
            user_id: Optional user ID (defaults to "me" for current user)
        """
        self._client = graph_client
        self._user_id = user_id or "me"
        self._folder_cache: dict[str, Folder] = {}

    def list_folders(
        self,
        include_hidden: bool = False,
        refresh_cache: bool = False,
    ) -> list[Folder]:
        """List all mail folders for the user.

        Args:
            include_hidden: Whether to include hidden folders
            refresh_cache: Force refresh the folder cache

        Returns:
            List of Folder objects
        """
        if self._folder_cache and not refresh_cache:
            folders = list(self._folder_cache.values())
            if not include_hidden:
                folders = [f for f in folders if not f.is_hidden]
            return folders

        path = f"{self._user_id}/mailFolders"
        params: dict[str, Any] = {
            "$top": 100,
        }

        all_folders: list[Folder] = []
        next_link = None

        while True:
            if next_link:
                # Use the next link directly (it's a full URL)
                result = self._client.request("GET", next_link)
            else:
                result = self._client.request("GET", path, params=params)

            if not isinstance(result, Mapping):
                break

            value = result.get("value", [])
            if isinstance(value, list):
                for folder_data in value:
                    if isinstance(folder_data, dict):
                        try:
                            folder = Folder.from_graph_api(folder_data)
                            all_folders.append(folder)
                            self._folder_cache[folder.id] = folder
                        except (KeyError, ValueError):
                            # Skip malformed folder data
                            continue

            # Check for more pages
            next_link = result.get("@odata.nextLink")
            if not next_link:
                break

        if not include_hidden:
            all_folders = [f for f in all_folders if not f.is_hidden]

        return all_folders

    def get_folder_by_id(self, folder_id: str, use_cache: bool = True) -> Folder | None:
        """Get a folder by its ID.

        Args:
            folder_id: The folder ID
            use_cache: Whether to use cached folder data

        Returns:
            Folder object or None if not found
        """
        if use_cache and folder_id in self._folder_cache:
            return self._folder_cache[folder_id]

        path = f"{self._user_id}/mailFolders/{folder_id}"

        try:
            result = self._client.request("GET", path)
            if isinstance(result, Mapping):
                folder = Folder.from_graph_api(dict(result))
                self._folder_cache[folder.id] = folder
                return folder
        except Exception:
            # Folder not found or error
            return None

        return None

    def get_folder_by_name(
        self,
        name: str,
        case_sensitive: bool = False,
    ) -> Folder | None:
        """Get a folder by its display name.

        Args:
            name: The folder display name
            case_sensitive: Whether to match case-sensitively

        Returns:
            Folder object or None if not found
        """
        folders = self.list_folders(include_hidden=True)

        for folder in folders:
            if case_sensitive:
                if folder.display_name == name:
                    return folder
            else:
                if folder.display_name.lower() == name.lower():
                    return folder

        return None

    def get_inbox_folder(self) -> Folder | None:
        """Get the inbox folder.

        Returns:
            Inbox Folder object or None if not found
        """
        # Try common inbox names
        inbox_names = ["Inbox", "INBOX"]
        for name in inbox_names:
            folder = self.get_folder_by_name(name)
            if folder:
                return folder

        # Fallback: return first folder with "inbox" in the name
        folders = self.list_folders(include_hidden=False)
        for folder in folders:
            if "inbox" in folder.display_name.lower():
                return folder

        return None

    def get_sent_items_folder(self) -> Folder | None:
        """Get the sent items folder.

        Returns:
            Sent Items Folder object or None if not found
        """
        sent_names = ["Sent Items", "Sent", "SENT"]
        for name in sent_names:
            folder = self.get_folder_by_name(name)
            if folder:
                return folder

        return None

    def get_deleted_items_folder(self) -> Folder | None:
        """Get the deleted items folder.

        Returns:
            Deleted Items Folder object or None if not found
        """
        deleted_names = ["Deleted Items", "Trash", "Deleted"]
        for name in deleted_names:
            folder = self.get_folder_by_name(name)
            if folder:
                return folder

        return None

    def search_folders(self, query: str) -> list[Folder]:
        """Search for folders by name.

        Args:
            query: Search query string (case-insensitive substring match)

        Returns:
            List of matching Folder objects
        """
        folders = self.list_folders(include_hidden=True)
        query_lower = query.lower()
        return [f for f in folders if query_lower in f.display_name.lower()]

    def clear_cache(self) -> None:
        """Clear the folder cache."""
        self._folder_cache.clear()
