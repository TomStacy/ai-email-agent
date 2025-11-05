"""Integration test script for inbox scanning functionality.

This script demonstrates and tests the email scanning capabilities by:
1. Authenticating with Microsoft Graph API
2. Listing mailbox folders
3. Scanning the inbox
4. Displaying email details

Run this script to verify the inbox scanning implementation works correctly.
"""

from __future__ import annotations

import sys
from pathlib import Path

from colorama import Fore, Style, init  # type: ignore[import-untyped]
from dotenv import load_dotenv  # type: ignore[import-untyped]

from src.auth.config import AuthConfig
from src.auth.graph_client import GraphApiClient
from src.auth.manager import AuthenticationManager
from src.email_client.email_scanner import EmailScanner
from src.email_client.folder_manager import FolderManager


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text.center(80)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Fore.YELLOW}→ {text}{Style.RESET_ALL}")


def test_folder_listing(folder_manager: FolderManager) -> bool:
    """Test listing mailbox folders."""
    print_header("Testing Folder Listing")

    try:
        print_info("Fetching mailbox folders...")
        folders = folder_manager.list_folders()

        if not folders:
            print_error("No folders found!")
            return False

        print_success(f"Found {len(folders)} folders:")
        print()

        for folder in folders[:10]:  # Show first 10 folders
            unread_info = f"({folder.unread_item_count} unread)" if folder.unread_item_count > 0 else ""
            print(f"  • {Fore.WHITE}{folder.display_name:<30}{Style.RESET_ALL} "
                  f"Total: {folder.total_item_count:>4} {Fore.YELLOW}{unread_info}{Style.RESET_ALL}")

        if len(folders) > 10:
            print(f"  ... and {len(folders) - 10} more folders")

        print()

        # Test finding specific folders
        print_info("Testing folder lookup methods...")
        inbox = folder_manager.get_inbox_folder()
        if inbox:
            print_success(f"Inbox found: {inbox.display_name} (ID: {inbox.id})")
        else:
            print_error("Inbox not found!")
            return False

        sent = folder_manager.get_sent_items_folder()
        if sent:
            print_success(f"Sent Items found: {sent.display_name}")

        deleted = folder_manager.get_deleted_items_folder()
        if deleted:
            print_success(f"Deleted Items found: {deleted.display_name}")

        return True

    except Exception as e:
        print_error(f"Folder listing failed: {e}")
        return False


def test_inbox_scanning(scanner: EmailScanner) -> bool:
    """Test scanning the inbox."""
    print_header("Testing Inbox Scanning")

    try:
        print_info("Scanning inbox (max 10 emails)...")
        result = scanner.scan_inbox(max_emails=10, show_progress=True)

        print()
        print_success("Scan completed!")
        print(f"  • Scanned: {result.scanned_count} emails")
        print(f"  • Retrieved: {result.total_count} emails")
        print(f"  • Skipped: {result.skipped_count} emails")
        print(f"  • Success rate: {result.success_rate:.1f}%")

        if result.errors:
            print_error(f"  • Errors: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"    - {error}")

        if result.has_more:
            print_info("  • More emails available (next_link present)")

        print()

        if not result.emails:
            print_info("No emails found in inbox")
            return True

        print_success(f"Displaying first {min(5, len(result.emails))} emails:\n")

        for i, email in enumerate(result.emails[:5], 1):
            print(f"{Fore.CYAN}Email #{i}:{Style.RESET_ALL}")
            print(f"  From: {Fore.WHITE}{email.sender.name if email.sender else 'Unknown'}{Style.RESET_ALL} "
                  f"<{email.sender.address if email.sender else 'N/A'}>")
            print(f"  Subject: {Fore.WHITE}{email.subject or '(No subject)'}{Style.RESET_ALL}")
            print(f"  Date: {email.received_datetime}")
            print(f"  Read: {'Yes' if email.is_read else 'No'} | "
                  f"Importance: {email.importance} | "
                  f"Attachments: {'Yes' if email.has_attachments else 'No'}")

            if email.body_preview:
                preview = email.body_preview[:100] + "..." if len(email.body_preview) > 100 else email.body_preview
                print(f"  Preview: {Fore.YELLOW}{preview}{Style.RESET_ALL}")

            print()

        return True

    except Exception as e:
        print_error(f"Inbox scanning failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filtered_scanning(scanner: EmailScanner) -> bool:
    """Test scanning with filters."""
    print_header("Testing Filtered Scanning")

    try:
        print_info("Scanning for unread emails (max 5)...")
        result = scanner.scan_unread_emails(max_emails=5, show_progress=True)

        print()
        print_success(f"Found {result.total_count} unread email(s)")

        if result.emails:
            print()
            for i, email in enumerate(result.emails, 1):
                print(f"  {i}. {email.subject or '(No subject)'} - "
                      f"from {email.sender.name if email.sender else 'Unknown'}")

        return True

    except Exception as e:
        print_error(f"Filtered scanning failed: {e}")
        return False


def main() -> int:
    """Main test execution."""
    # Initialize colorama for cross-platform color support
    init(autoreset=True)

    print_header("Email Client Integration Test")

    # Load environment configuration
    load_dotenv()

    try:
        print_info("Loading authentication configuration...")
        config = AuthConfig.from_env()
        print_success("Configuration loaded")
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        print_info("Make sure .env file is configured with Azure credentials")
        return 1

    # Initialize authentication
    try:
        print_info("Initializing authentication...")
        auth_manager = AuthenticationManager(config)
        print_success("Authentication manager initialized")

        print_info("Acquiring access token...")
        # This will use cached token or acquire a new one
        token = auth_manager.get_access_token()
        print_success("Access token acquired")
    except Exception as e:
        print_error(f"Authentication failed: {e}")
        print_info("Try running scripts/interactive_login.py first to authenticate")
        return 1

    # Initialize clients
    try:
        graph_client = GraphApiClient(auth_manager)
        folder_manager = FolderManager(graph_client)
        scanner = EmailScanner(graph_client, folder_manager)
        print_success("Email client components initialized")
    except Exception as e:
        print_error(f"Failed to initialize clients: {e}")
        return 1

    # Run tests
    print()
    all_passed = True

    # Test 1: Folder listing
    if not test_folder_listing(folder_manager):
        all_passed = False

    # Test 2: Inbox scanning
    if not test_inbox_scanning(scanner):
        all_passed = False

    # Test 3: Filtered scanning
    if not test_filtered_scanning(scanner):
        all_passed = False

    # Summary
    print_header("Test Summary")
    if all_passed:
        print_success("All tests passed! ✓")
        print()
        print(f"{Fore.GREEN}The inbox scanning functionality is working correctly.{Style.RESET_ALL}")
        return 0
    else:
        print_error("Some tests failed! ✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
