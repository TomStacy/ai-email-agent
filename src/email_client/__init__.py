"""Email client module for Microsoft Graph API"""

from .email_fetcher import EmailFetcher
from .email_scanner import EmailScanner
from .folder_manager import FolderManager
from .models import Email, EmailAddress, EmailBody, Folder, ScanResult

__all__ = [
    "Email",
    "EmailAddress",
    "EmailBody",
    "Folder",
    "ScanResult",
    "EmailFetcher",
    "EmailScanner",
    "FolderManager",
]
