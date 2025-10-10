"""
Test Instantly API Connection
Quick script to verify API key works and fetch workspace info
"""

import asyncio
import sys
from app.core.config import settings
from app.integrations.instantly.client import InstantlyClient


async def test_connection():
    """Test Instantly API connection"""

    print("=" * 60)
    print("INSTANTLY API CONNECTION TEST")
    print("=" * 60)
    print()

    # Get API key from settings
    api_key = settings.instantly_api_key
    print(f"API Key (first 20 chars): {api_key[:20]}...")
    print()

    # Initialize client
    print("[1/4] Initializing Instantly Client...")
    client = InstantlyClient(api_key=api_key)
    print("[OK] Client initialized")
    print()

    # Test connection
    print("[2/4] Testing API connection...")
    try:
        connection_ok = await client.test_connection()
        if connection_ok:
            print("[OK] Connection successful!")
        else:
            print("[ERROR] Connection failed (authentication issue)")
            return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return False
    print()

    # Get workspace info
    print("[3/4] Fetching workspace info...")
    try:
        workspace = await client.get_current_workspace()
        print("[OK] Workspace fetched successfully")
        print(f"  - ID: {workspace.id}")
        print(f"  - Name: {workspace.name}")
        print(f"  - Plan: {workspace.plan or 'N/A'}")
        print(f"  - Email Accounts: {workspace.email_accounts_count or 0}")
        print(f"  - Emails Sent (Month): {workspace.emails_sent_this_month or 0}")
    except Exception as e:
        print(f"[ERROR] Error fetching workspace: {e}")
        return False
    print()

    # List campaigns
    print("[4/4] Fetching campaigns...")
    try:
        campaigns = await client.list_campaigns()
        print(f"[OK] Found {len(campaigns)} campaigns")

        if campaigns:
            print("\nCampaigns:")
            for i, campaign in enumerate(campaigns[:5], 1):  # Show first 5
                print(f"  {i}. {campaign.name} (Status: {campaign.status})")

            if len(campaigns) > 5:
                print(f"  ... and {len(campaigns) - 5} more")
        else:
            print("  (No campaigns found - this is OK for a new workspace)")

    except Exception as e:
        print(f"✗ Error fetching campaigns: {e}")
        return False
    print()

    # List email accounts
    print("[BONUS] Fetching email accounts...")
    try:
        accounts = await client.list_email_accounts()
        print(f"[OK] Found {len(accounts)} email accounts")

        if accounts:
            print("\nEmail Accounts:")
            for i, account in enumerate(accounts, 1):
                print(f"  {i}. {account.email} (Status: {account.status})")
        else:
            print("  (No email accounts found)")

    except Exception as e:
        print(f"[ERROR] Error fetching email accounts: {e}")
        return False
    print()

    print("=" * 60)
    print("[SUCCESS] ALL TESTS PASSED! Instantly integration is ready!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # Run async test
    result = asyncio.run(test_connection())

    if not result:
        print("\n[FAILED] Tests failed. Check your API key and configuration.")
        sys.exit(1)
    else:
        print("\n[READY] Ready to proceed with webhook configuration!")
        sys.exit(0)
