"""
Campaign Service
CRUD operations and business logic for campaigns
"""

import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.db import tenant_db_pool
from app.integrations.instantly.schemas import InstantlyCampaign

logger = logging.getLogger(__name__)


class CampaignService:
    """Campaign Business Logic"""

    @staticmethod
    async def import_from_instantly(
        organization_id: UUID,
        provider_connection_id: UUID,
        campaigns: List[InstantlyCampaign]
    ) -> Dict[str, int]:
        """
        Import campaigns from Instantly API

        Args:
            organization_id: Organization UUID
            provider_connection_id: Provider connection UUID
            campaigns: List of InstantlyCampaign objects

        Returns:
            {"imported": count, "updated": count, "skipped": count}
        """
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        async with tenant_db_pool.acquire() as conn:
            for campaign in campaigns:
                try:
                    # Check if campaign already exists
                    existing = await conn.fetchrow("""
                        SELECT id, updated_at
                        FROM campaign
                        WHERE external_id = $1 AND organization_id = $2
                    """, campaign.id, organization_id)

                    if existing:
                        # Update existing campaign
                        await conn.execute("""
                            UPDATE campaign
                            SET
                                name = $1,
                                status = $2,
                                workspace_id = $3,
                                imported_at = NOW(),
                                updated_at = NOW()
                            WHERE id = $4
                        """,
                            campaign.name,
                            campaign.status,
                            campaign.workspace_id,
                            existing['id']
                        )
                        updated_count += 1
                        logger.info(f"Updated campaign: {campaign.name} (ID: {campaign.id})")

                    else:
                        # Insert new campaign
                        await conn.execute("""
                            INSERT INTO campaign (
                                organization_id,
                                provider_connection_id,
                                external_id,
                                name,
                                status,
                                workspace_id,
                                imported_at,
                                created_at,
                                updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW(), NOW())
                        """,
                            organization_id,
                            provider_connection_id,
                            campaign.id,
                            campaign.name,
                            campaign.status,
                            campaign.workspace_id
                        )
                        imported_count += 1
                        logger.info(f"Imported new campaign: {campaign.name} (ID: {campaign.id})")

                except Exception as e:
                    logger.error(f"Failed to import campaign {campaign.id}: {e}")
                    skipped_count += 1

        return {
            "imported": imported_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(campaigns)
        }

    @staticmethod
    async def get_all_campaigns_for_admin() -> List[Dict[str, Any]]:
        """
        Get ALL campaigns across ALL organizations
        ADMIN ONLY - Bypasses RLS

        Returns:
            List of campaign dicts with organization info
        """
        async with tenant_db_pool.acquire() as conn:
            # Set admin role to bypass RLS
            await conn.execute("SET LOCAL app.user_role = 'sb_admin'")

            rows = await conn.fetch("""
                SELECT
                    c.id,
                    c.external_id,
                    c.name,
                    c.status,
                    c.organization_id,
                    o.name as organization_name,
                    c.provider_connection_id,
                    c.email_account_id,
                    ea.email_address as sending_email,
                    c.workspace_id,
                    c.imported_at,
                    c.created_at,
                    c.updated_at
                FROM campaign c
                LEFT JOIN organization o ON c.organization_id = o.id
                LEFT JOIN email_account ea ON c.email_account_id = ea.id
                ORDER BY c.created_at DESC
            """)

            return [dict(row) for row in rows]

    @staticmethod
    async def get_campaigns_for_org(organization_id: UUID) -> List[Dict[str, Any]]:
        """
        Get campaigns for specific organization
        RLS applies automatically

        Args:
            organization_id: Organization UUID

        Returns:
            List of campaign dicts
        """
        async with tenant_db_pool.acquire() as conn:
            # Set organization context for RLS
            await conn.execute("SET LOCAL app.current_org_id = $1", str(organization_id))

            rows = await conn.fetch("""
                SELECT
                    c.id,
                    c.external_id,
                    c.name,
                    c.status,
                    c.email_account_id,
                    ea.email_address as sending_email,
                    c.workspace_id,
                    c.imported_at,
                    c.created_at,
                    c.updated_at
                FROM campaign c
                LEFT JOIN email_account ea ON c.email_account_id = ea.id
                WHERE c.organization_id = $1
                ORDER BY c.created_at DESC
            """, organization_id)

            return [dict(row) for row in rows]

    @staticmethod
    async def get_campaign_by_external_id(external_id: str) -> Optional[Dict[str, Any]]:
        """
        Get campaign by Instantly campaign ID

        Args:
            external_id: Instantly campaign ID

        Returns:
            Campaign dict or None
        """
        async with tenant_db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    c.id,
                    c.external_id,
                    c.name,
                    c.status,
                    c.organization_id,
                    c.provider_connection_id,
                    c.email_account_id,
                    c.workspace_id
                FROM campaign c
                WHERE c.external_id = $1
            """, external_id)

            return dict(row) if row else None

    @staticmethod
    async def update_campaign_status(campaign_id: UUID, status: str) -> bool:
        """
        Update campaign status

        Args:
            campaign_id: Campaign UUID
            status: New status

        Returns:
            True if updated, False otherwise
        """
        async with tenant_db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE campaign
                SET status = $1, updated_at = NOW()
                WHERE id = $2
            """, status, campaign_id)

            return result == "UPDATE 1"

    @staticmethod
    async def assign_email_account(campaign_id: UUID, email_account_id: UUID) -> bool:
        """
        Assign email account to campaign

        Args:
            campaign_id: Campaign UUID
            email_account_id: Email Account UUID

        Returns:
            True if assigned, False otherwise
        """
        async with tenant_db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE campaign
                SET email_account_id = $1, updated_at = NOW()
                WHERE id = $2
            """, email_account_id, campaign_id)

            return result == "UPDATE 1"

    @staticmethod
    async def get_campaign_stats(campaign_id: UUID) -> Dict[str, int]:
        """
        Get campaign statistics

        Args:
            campaign_id: Campaign UUID

        Returns:
            Dict with sent, opened, replied counts
        """
        async with tenant_db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'email_sent') as sent,
                    COUNT(*) FILTER (WHERE event_type = 'email_opened') as opened,
                    COUNT(*) FILTER (WHERE event_type = 'reply_received') as replied
                FROM message
                WHERE campaign_id = $1
            """, campaign_id)

            return {
                "sent": row['sent'] or 0,
                "opened": row['opened'] or 0,
                "replied": row['replied'] or 0
            }
