"""
Email Account Service
CRUD operations and business logic for email accounts
"""

import logging
from uuid import UUID
from typing import List, Optional, Dict, Any

from app.core.db import tenant_db_pool
from app.integrations.instantly.schemas import InstantlyEmailAccount

logger = logging.getLogger(__name__)


class EmailAccountService:
    """Email Account Business Logic"""

    @staticmethod
    async def import_from_instantly(
        organization_id: UUID,
        provider_connection_id: UUID,
        accounts: List[InstantlyEmailAccount]
    ) -> Dict[str, int]:
        """
        Import email accounts from Instantly API

        Args:
            organization_id: Organization UUID
            provider_connection_id: Provider connection UUID
            accounts: List of InstantlyEmailAccount objects

        Returns:
            {"imported": count, "updated": count, "skipped": count}
        """
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        async with tenant_db_pool.acquire() as conn:
            for account in accounts:
                try:
                    # Check if account already exists
                    existing = await conn.fetchrow("""
                        SELECT id
                        FROM email_account
                        WHERE provider_account_id = $1
                        AND provider = 'instantly'
                    """, account.id)

                    if existing:
                        # Update existing account
                        await conn.execute("""
                            UPDATE email_account
                            SET
                                email_address = $1,
                                display_name = $2,
                                status = $3,
                                daily_limit = $4,
                                warmup_enabled = $5,
                                emails_sent_today = $6,
                                emails_sent_total = $7,
                                last_email_sent_at = $8,
                                updated_at = NOW()
                            WHERE id = $9
                        """,
                            account.email,
                            account.display_name,
                            account.status,
                            account.daily_limit,
                            account.warmup_enabled,
                            account.emails_sent_today,
                            account.emails_sent_total,
                            account.last_email_sent_at,
                            existing['id']
                        )
                        updated_count += 1
                        logger.info(f"Updated email account: {account.email}")

                    else:
                        # Insert new account
                        await conn.execute("""
                            INSERT INTO email_account (
                                organization_id,
                                provider_connection_id,
                                email_address,
                                display_name,
                                provider,
                                provider_account_id,
                                daily_limit,
                                warmup_enabled,
                                status,
                                emails_sent_today,
                                emails_sent_total,
                                last_email_sent_at,
                                created_at,
                                updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
                        """,
                            organization_id,
                            provider_connection_id,
                            account.email,
                            account.display_name,
                            'instantly',
                            account.id,
                            account.daily_limit,
                            account.warmup_enabled,
                            account.status,
                            account.emails_sent_today,
                            account.emails_sent_total,
                            account.last_email_sent_at
                        )
                        imported_count += 1
                        logger.info(f"Imported new email account: {account.email}")

                except Exception as e:
                    logger.error(f"Failed to import email account {account.email}: {e}")
                    skipped_count += 1

        return {
            "imported": imported_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(accounts)
        }

    @staticmethod
    async def get_all_accounts_for_admin() -> List[Dict[str, Any]]:
        """
        Get ALL email accounts across ALL organizations
        ADMIN ONLY - Bypasses RLS

        Returns:
            List of email account dicts with organization info
        """
        async with tenant_db_pool.acquire() as conn:
            # Set admin role to bypass RLS
            await conn.execute("SET LOCAL app.user_role = 'sb_admin'")

            rows = await conn.fetch("""
                SELECT
                    ea.id,
                    ea.organization_id,
                    o.name as organization_name,
                    ea.email_address,
                    ea.display_name,
                    ea.provider,
                    ea.provider_account_id,
                    ea.status,
                    ea.daily_limit,
                    ea.warmup_enabled,
                    ea.emails_sent_today,
                    ea.emails_sent_total,
                    ea.last_email_sent_at,
                    ea.created_at
                FROM email_account ea
                LEFT JOIN organization o ON ea.organization_id = o.id
                ORDER BY ea.created_at DESC
            """)

            return [dict(row) for row in rows]

    @staticmethod
    async def get_accounts_for_org(organization_id: UUID) -> List[Dict[str, Any]]:
        """
        Get email accounts for specific organization
        RLS applies automatically

        Args:
            organization_id: Organization UUID

        Returns:
            List of email account dicts
        """
        async with tenant_db_pool.acquire() as conn:
            # Set organization context for RLS
            await conn.execute("SET LOCAL app.current_org_id = $1", str(organization_id))

            rows = await conn.fetch("""
                SELECT
                    ea.id,
                    ea.email_address,
                    ea.display_name,
                    ea.provider,
                    ea.status,
                    ea.daily_limit,
                    ea.warmup_enabled,
                    ea.emails_sent_today,
                    ea.emails_sent_total,
                    ea.last_email_sent_at,
                    ea.created_at
                FROM email_account ea
                WHERE ea.organization_id = $1
                ORDER BY ea.email_address ASC
            """, organization_id)

            return [dict(row) for row in rows]

    @staticmethod
    async def get_account_by_email(email_address: str) -> Optional[Dict[str, Any]]:
        """
        Get email account by email address

        Args:
            email_address: Email address

        Returns:
            Email account dict or None
        """
        async with tenant_db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    ea.id,
                    ea.organization_id,
                    ea.provider_connection_id,
                    ea.email_address,
                    ea.provider,
                    ea.provider_account_id,
                    ea.status
                FROM email_account ea
                WHERE ea.email_address = $1
            """, email_address)

            return dict(row) if row else None

    @staticmethod
    async def update_account_status(account_id: UUID, status: str) -> bool:
        """
        Update email account status

        Args:
            account_id: Email account UUID
            status: New status

        Returns:
            True if updated, False otherwise
        """
        async with tenant_db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE email_account
                SET status = $1, updated_at = NOW()
                WHERE id = $2
            """, status, account_id)

            return result == "UPDATE 1"

    @staticmethod
    async def increment_sent_count(account_id: UUID) -> bool:
        """
        Increment emails_sent_today counter

        Args:
            account_id: Email account UUID

        Returns:
            True if updated, False otherwise
        """
        async with tenant_db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE email_account
                SET
                    emails_sent_today = emails_sent_today + 1,
                    emails_sent_total = emails_sent_total + 1,
                    last_email_sent_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
            """, account_id)

            return result == "UPDATE 1"

    @staticmethod
    async def reset_daily_counters() -> int:
        """
        Reset emails_sent_today for all accounts
        Should be run daily via cron

        Returns:
            Number of accounts reset
        """
        async with tenant_db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE email_account
                SET emails_sent_today = 0, updated_at = NOW()
                WHERE emails_sent_today > 0
            """)

            # Extract count from "UPDATE N" result
            count = int(result.split()[-1]) if result.startswith("UPDATE") else 0
            logger.info(f"Reset daily counters for {count} email accounts")
            return count

    @staticmethod
    async def handle_error(email_address: str, error_message: str) -> bool:
        """
        Handle email account error from webhook

        Args:
            email_address: Email address that errored
            error_message: Error description

        Returns:
            True if handled, False otherwise
        """
        async with tenant_db_pool.acquire() as conn:
            # Update account status to 'error'
            result = await conn.execute("""
                UPDATE email_account
                SET
                    status = 'suspended',
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{last_error}',
                        to_jsonb($1::text)
                    ),
                    updated_at = NOW()
                WHERE email_address = $2
            """, error_message, email_address)

            if result == "UPDATE 1":
                logger.warning(f"Email account {email_address} suspended due to error: {error_message}")
                return True

            return False

    @staticmethod
    async def get_account_stats(account_id: UUID) -> Dict[str, Any]:
        """
        Get email account statistics

        Args:
            account_id: Email account UUID

        Returns:
            Dict with usage stats
        """
        async with tenant_db_pool.acquire() as conn:
            # Get account info
            account = await conn.fetchrow("""
                SELECT
                    daily_limit,
                    emails_sent_today,
                    emails_sent_total,
                    last_email_sent_at,
                    status
                FROM email_account
                WHERE id = $1
            """, account_id)

            if not account:
                return {}

            # Get campaign count
            campaign_count = await conn.fetchval("""
                SELECT COUNT(DISTINCT campaign_id)
                FROM campaign
                WHERE email_account_id = $1
            """, account_id)

            return {
                "daily_limit": account['daily_limit'],
                "emails_sent_today": account['emails_sent_today'],
                "emails_sent_total": account['emails_sent_total'],
                "last_email_sent_at": account['last_email_sent_at'],
                "status": account['status'],
                "usage_percentage": round((account['emails_sent_today'] / account['daily_limit']) * 100, 2) if account['daily_limit'] > 0 else 0,
                "campaigns_count": campaign_count or 0
            }
