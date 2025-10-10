"""
Fetch all data from Instantly workspace
Get campaigns, email accounts, and leads
"""

import asyncio
import json
from app.core.config import settings
from app.integrations.instantly.client import InstantlyClient


async def fetch_all_data():
    """Fetch all workspace data"""

    print("=" * 80)
    print("FETCHING INSTANTLY WORKSPACE DATA")
    print("=" * 80)
    print()

    client = InstantlyClient(api_key=settings.instantly_api_key)

    # 1. Workspace Info
    print("[1/4] Workspace Information")
    print("-" * 80)
    workspace = await client.get_current_workspace()
    print(f"ID: {workspace.id}")
    print(f"Name: {workspace.name}")
    print(f"Owner: {workspace.owner}")
    print(f"Created: {workspace.timestamp_created}")
    print(f"Plan: {workspace.plan or 'N/A'}")
    print()

    # 2. Campaigns
    print("[2/4] Campaigns")
    print("-" * 80)
    campaigns = await client.list_campaigns()
    print(f"Total Campaigns: {len(campaigns)}\n")

    for i, campaign in enumerate(campaigns, 1):
        print(f"{i}. {campaign.name}")
        print(f"   ID: {campaign.id}")
        print(f"   Status: {campaign.status}")
        print(f"   Created: {campaign.timestamp_created}")
        if hasattr(campaign, 'schedule') and campaign.schedule:
            print(f"   Schedule: {campaign.schedule}")
        print()

    # 3. Email Accounts
    print("[3/4] Email Accounts")
    print("-" * 80)
    accounts = await client.list_email_accounts()
    print(f"Total Email Accounts: {len(accounts)}\n")

    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account.email}")
        print(f"   ID: {account.id}")
        print(f"   Status: {account.status}")
        if hasattr(account, 'smtp_username'):
            print(f"   SMTP: {account.smtp_username}")
        if hasattr(account, 'warmup_enabled'):
            print(f"   Warmup: {account.warmup_enabled}")
        if hasattr(account, 'daily_limit'):
            print(f"   Daily Limit: {account.daily_limit}")
        print()

    # 4. Save to JSON for import
    print("[4/4] Saving data for database import")
    print("-" * 80)

    export_data = {
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "owner": workspace.owner,
            "created": str(workspace.timestamp_created),
            "plan": workspace.plan
        },
        "campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "created": str(c.timestamp_created),
                "raw": c.dict() if hasattr(c, 'dict') else str(c)
            }
            for c in campaigns
        ],
        "email_accounts": [
            {
                "id": a.id,
                "email": a.email,
                "status": a.status,
                "raw": a.dict() if hasattr(a, 'dict') else str(a)
            }
            for a in accounts
        ]
    }

    # Save to file
    output_file = "instantly_export.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"Data exported to: {output_file}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Workspace: {workspace.name}")
    print(f"Campaigns: {len(campaigns)}")
    print(f"Email Accounts: {len(accounts)}")
    print(f"Export File: {output_file}")
    print()
    print("Ready for database import!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(fetch_all_data())
