"""
Message Service
Business logic for message tracking and webhook event processing
"""

import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.db import tenant_db_pool
from app.integrations.instantly.schemas import InstantlyWebhookPayload, InstantlyEventType

logger = logging.getLogger(__name__)


class MessageService:
    """Message Tracking and Event Processing"""

    @staticmethod
    async def process_webhook_event(payload: InstantlyWebhookPayload) -> Dict[str, Any]:
        """
        Process Instantly webhook event and create message/event records

        Args:
            payload: Webhook payload from Instantly

        Returns:
            Dict with processing result

        Raises:
            ValueError: If campaign not found or invalid data
        """
        async with tenant_db_pool.acquire() as conn:
            # Find campaign by external_id
            campaign = await conn.fetchrow("""
                SELECT
                    id,
                    organization_id,
                    email_account_id
                FROM campaign
                WHERE external_id = $1
            """, payload.campaign_id)

            if not campaign:
                logger.warning(f"Campaign {payload.campaign_id} not found for webhook event")
                raise ValueError(f"Campaign {payload.campaign_id} not found")

            # Find or create contact
            contact_id = None
            if payload.lead_email:
                contact_id = await MessageService._get_or_create_contact(
                    conn,
                    campaign['organization_id'],
                    payload.lead_email
                )

            # Determine message direction and status
            direction = "outbound"
            status = payload.event_type.value

            if payload.event_type == InstantlyEventType.REPLY_RECEIVED:
                direction = "inbound"

            # Create message record
            message_id = await conn.fetchval("""
                INSERT INTO message (
                    organization_id,
                    campaign_id,
                    contact_id,
                    email_account_id,
                    from_email,
                    to_email,
                    direction,
                    status,
                    event_type,
                    subject,
                    body,
                    external_data,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
                RETURNING id
            """,
                campaign['organization_id'],
                campaign['id'],
                contact_id,
                campaign['email_account_id'],
                payload.email_account or payload.lead_email,
                payload.lead_email,
                direction,
                status,
                payload.event_type.value,
                payload.subject,
                payload.body_text or payload.body_html,
                payload.dict()  # Store full webhook payload as JSONB
            )

            # Create event_log entry for tracking
            await conn.execute("""
                INSERT INTO event_log (
                    organization_id,
                    event_type,
                    entity_type,
                    entity_id,
                    data,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """,
                campaign['organization_id'],
                f'instantly.{payload.event_type.value}',
                'message',
                message_id,
                payload.dict()
            )

            # Update email account stats if email_sent
            if payload.event_type == InstantlyEventType.EMAIL_SENT and campaign['email_account_id']:
                from app.services.email_account_service import EmailAccountService
                await EmailAccountService.increment_sent_count(campaign['email_account_id'])

            # Handle specific event types
            if payload.event_type == InstantlyEventType.ACCOUNT_ERROR:
                from app.services.email_account_service import EmailAccountService
                if payload.email_account:
                    await EmailAccountService.handle_error(
                        payload.email_account,
                        payload.error_message or "Unknown error"
                    )

            logger.info(
                f"Processed webhook: {payload.event_type.value} "
                f"for campaign {payload.campaign_name} "
                f"(lead: {payload.lead_email})"
            )

            return {
                "message_id": str(message_id),
                "campaign_id": str(campaign['id']),
                "event_type": payload.event_type.value,
                "processed_at": datetime.utcnow().isoformat()
            }

    @staticmethod
    async def _get_or_create_contact(
        conn,
        organization_id: UUID,
        email: str
    ) -> UUID:
        """
        Get existing contact or create new one

        Args:
            conn: Database connection
            organization_id: Organization UUID
            email: Contact email

        Returns:
            Contact UUID
        """
        # Check if contact exists
        contact_id = await conn.fetchval("""
            SELECT id
            FROM contact
            WHERE organization_id = $1 AND email = $2
        """, organization_id, email)

        if contact_id:
            return contact_id

        # Create new contact
        contact_id = await conn.fetchval("""
            INSERT INTO contact (
                organization_id,
                email,
                status,
                created_at,
                updated_at
            ) VALUES ($1, $2, 'lead', NOW(), NOW())
            RETURNING id
        """, organization_id, email)

        logger.info(f"Created new contact: {email}")
        return contact_id

    @staticmethod
    async def get_messages_for_campaign(
        campaign_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a campaign

        Args:
            campaign_id: Campaign UUID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of message dicts
        """
        async with tenant_db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    m.id,
                    m.from_email,
                    m.to_email,
                    m.direction,
                    m.status,
                    m.event_type,
                    m.subject,
                    m.body,
                    m.created_at,
                    c.email as contact_email,
                    c.first_name,
                    c.last_name
                FROM message m
                LEFT JOIN contact c ON m.contact_id = c.id
                WHERE m.campaign_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2 OFFSET $3
            """, campaign_id, limit, offset)

            return [dict(row) for row in rows]

    @staticmethod
    async def get_messages_for_contact(
        contact_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get message history for a contact

        Args:
            contact_id: Contact UUID
            limit: Max results

        Returns:
            List of message dicts (conversation thread)
        """
        async with tenant_db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    m.id,
                    m.from_email,
                    m.to_email,
                    m.direction,
                    m.status,
                    m.event_type,
                    m.subject,
                    m.body,
                    m.created_at,
                    m.campaign_id,
                    ca.name as campaign_name
                FROM message m
                LEFT JOIN campaign ca ON m.campaign_id = ca.id
                WHERE m.contact_id = $1
                ORDER BY m.created_at ASC
                LIMIT $2
            """, contact_id, limit)

            return [dict(row) for row in rows]

    @staticmethod
    async def get_message_stats_for_org(organization_id: UUID) -> Dict[str, int]:
        """
        Get message statistics for organization

        Args:
            organization_id: Organization UUID

        Returns:
            Dict with sent, opened, replied, bounced counts
        """
        async with tenant_db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'email_sent') as sent,
                    COUNT(*) FILTER (WHERE event_type = 'email_opened') as opened,
                    COUNT(*) FILTER (WHERE event_type = 'reply_received') as replied,
                    COUNT(*) FILTER (WHERE event_type = 'email_bounced') as bounced,
                    COUNT(*) FILTER (WHERE event_type = 'link_clicked') as clicked
                FROM message
                WHERE organization_id = $1
            """, organization_id)

            return {
                "sent": row['sent'] or 0,
                "opened": row['opened'] or 0,
                "replied": row['replied'] or 0,
                "bounced": row['bounced'] or 0,
                "clicked": row['clicked'] or 0,
                "open_rate": round((row['opened'] / row['sent'] * 100), 2) if row['sent'] > 0 else 0,
                "reply_rate": round((row['replied'] / row['sent'] * 100), 2) if row['sent'] > 0 else 0
            }

    @staticmethod
    async def search_messages(
        organization_id: UUID,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search messages by email, subject, or body

        Args:
            organization_id: Organization UUID
            query: Search query
            limit: Max results

        Returns:
            List of matching message dicts
        """
        async with tenant_db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    m.id,
                    m.from_email,
                    m.to_email,
                    m.subject,
                    m.event_type,
                    m.created_at,
                    c.email as contact_email,
                    ca.name as campaign_name
                FROM message m
                LEFT JOIN contact c ON m.contact_id = c.id
                LEFT JOIN campaign ca ON m.campaign_id = ca.id
                WHERE m.organization_id = $1
                AND (
                    m.from_email ILIKE $2
                    OR m.to_email ILIKE $2
                    OR m.subject ILIKE $2
                    OR m.body ILIKE $2
                )
                ORDER BY m.created_at DESC
                LIMIT $3
            """, organization_id, f"%{query}%", limit)

            return [dict(row) for row in rows]
