"""
User Assignment Service

Handles user-campaign and user-contact assignments.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.core import db


async def assign_user_to_campaigns(
    user_id: UUID,
    campaign_ids: List[UUID],
    assigned_by: UUID,
    organization_id: UUID,
    role: str = "member",
    can_edit: bool = False,
    can_view_stats: bool = True,
    can_manage_contacts: bool = False
) -> Dict[str, Any]:
    """
    Assign a user to multiple campaigns.

    Args:
        user_id: User UUID to assign
        campaign_ids: List of campaign UUIDs
        assigned_by: User UUID who is making the assignment
        organization_id: Organization UUID
        role: User role in campaigns (owner, admin, member, viewer)
        can_edit: Permission to edit campaigns
        can_view_stats: Permission to view statistics
        can_manage_contacts: Permission to manage contacts

    Returns:
        Dict with success count and failed campaigns
    """
    success_count = 0
    failed_campaigns = []

    async with db.tenant_db_pool.acquire() as conn:
        for campaign_id in campaign_ids:
            try:
                await conn.execute(
                    """
                    INSERT INTO user_campaign_assignment (
                        user_id, campaign_id, organization_id, assigned_by,
                        role, can_edit, can_view_stats, can_manage_contacts,
                        status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')
                    ON CONFLICT (user_id, campaign_id)
                    DO UPDATE SET
                        role = EXCLUDED.role,
                        can_edit = EXCLUDED.can_edit,
                        can_view_stats = EXCLUDED.can_view_stats,
                        can_manage_contacts = EXCLUDED.can_manage_contacts,
                        status = 'active',
                        updated_at = NOW()
                    """,
                    user_id, campaign_id, organization_id, assigned_by,
                    role, can_edit, can_view_stats, can_manage_contacts
                )
                success_count += 1
            except Exception as e:
                failed_campaigns.append({
                    "campaign_id": str(campaign_id),
                    "error": str(e)
                })

    return {
        "success_count": success_count,
        "failed_count": len(failed_campaigns),
        "failed_campaigns": failed_campaigns
    }


async def assign_contacts_to_user(
    user_id: UUID,
    contact_ids: List[UUID],
    assigned_by: UUID,
    organization_id: UUID,
    assignment_type: str = "manual"
) -> Dict[str, Any]:
    """
    Assign multiple contacts to a user.

    Args:
        user_id: User UUID to assign contacts to
        contact_ids: List of contact UUIDs
        assigned_by: User UUID who is making the assignment
        organization_id: Organization UUID
        assignment_type: Type of assignment (manual, round_robin, lead_score, territory)

    Returns:
        Dict with success count and failed contacts
    """
    success_count = 0
    failed_contacts = []

    async with db.tenant_db_pool.acquire() as conn:
        for contact_id in contact_ids:
            try:
                await conn.execute(
                    """
                    INSERT INTO user_contact_assignment (
                        user_id, contact_id, organization_id, assigned_by,
                        assignment_type, is_primary_owner, status
                    ) VALUES ($1, $2, $3, $4, $5, true, 'active')
                    ON CONFLICT (user_id, contact_id)
                    DO UPDATE SET
                        assignment_type = EXCLUDED.assignment_type,
                        status = 'active',
                        updated_at = NOW()
                    """,
                    user_id, contact_id, organization_id, assigned_by,
                    assignment_type
                )
                success_count += 1
            except Exception as e:
                failed_contacts.append({
                    "contact_id": str(contact_id),
                    "error": str(e)
                })

    return {
        "success_count": success_count,
        "failed_count": len(failed_contacts),
        "failed_contacts": failed_contacts
    }


async def get_user_assignments(user_id: UUID) -> Dict[str, Any]:
    """
    Get all campaigns and contacts assigned to a user.

    Args:
        user_id: User UUID

    Returns:
        Dict with campaigns and contacts
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Get assigned campaigns
        campaigns = await conn.fetch(
            """
            SELECT
                uca.id as assignment_id,
                uca.campaign_id,
                c.name as campaign_name,
                c.status as campaign_status,
                uca.role,
                uca.can_edit,
                uca.can_view_stats,
                uca.can_manage_contacts,
                uca.assigned_at
            FROM user_campaign_assignment uca
            JOIN campaign c ON uca.campaign_id = c.id
            WHERE uca.user_id = $1 AND uca.status = 'active'
            ORDER BY uca.assigned_at DESC
            """,
            user_id
        )

        # Get assigned contacts
        contacts = await conn.fetch(
            """
            SELECT
                uca.id as assignment_id,
                uca.contact_id,
                ct.email as contact_email,
                ct.first_name,
                ct.last_name,
                ct.company,
                ct.lead_score,
                uca.assignment_type,
                uca.is_primary_owner,
                uca.last_contacted_at,
                uca.next_followup_at,
                uca.interactions_count,
                uca.assigned_at
            FROM user_contact_assignment uca
            JOIN contact ct ON uca.contact_id = ct.id
            WHERE uca.user_id = $1 AND uca.status = 'active'
            ORDER BY uca.assigned_at DESC
            """,
            user_id
        )

    return {
        "campaigns": [dict(row) for row in campaigns],
        "contacts": [dict(row) for row in contacts],
        "campaigns_count": len(campaigns),
        "contacts_count": len(contacts)
    }


async def get_organization_users_with_assignments(
    organization_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get all users in an organization with their assignment counts.

    Args:
        organization_id: Organization UUID

    Returns:
        List of users with assignment statistics
    """
    async with db.tenant_db_pool.acquire() as conn:
        users = await conn.fetch(
            """
            SELECT
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.status,
                u.created_at,
                get_user_campaign_count(u.id) as campaigns_count,
                get_user_contact_count(u.id) as contacts_count
            FROM "user" u
            WHERE u.organization_id = $1
            ORDER BY u.created_at DESC
            """,
            organization_id
        )

    return [dict(row) for row in users]


async def auto_assign_contact_round_robin(
    contact_id: UUID,
    organization_id: UUID,
    assigned_by: UUID
) -> Optional[UUID]:
    """
    Automatically assign a contact to the user with the fewest contacts (round-robin).

    Args:
        contact_id: Contact UUID to assign
        organization_id: Organization UUID
        assigned_by: User UUID who triggered the assignment

    Returns:
        User UUID who was assigned the contact, or None if no users available
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Get next user via round-robin function
        user_id = await conn.fetchval(
            """
            SELECT get_next_user_round_robin($1)
            """,
            organization_id
        )

        if not user_id:
            return None

        # Assign contact to user
        await conn.execute(
            """
            INSERT INTO user_contact_assignment (
                user_id, contact_id, organization_id, assigned_by,
                assignment_type, is_primary_owner, status
            ) VALUES ($1, $2, $3, $4, 'round_robin', true, 'active')
            ON CONFLICT (user_id, contact_id)
            DO UPDATE SET
                assignment_type = 'round_robin',
                status = 'active',
                updated_at = NOW()
            """,
            user_id, contact_id, organization_id, assigned_by
        )

    return user_id


async def remove_user_campaign_assignment(
    user_id: UUID,
    campaign_id: UUID
) -> bool:
    """
    Remove a user from a campaign (set status to inactive).

    Args:
        user_id: User UUID
        campaign_id: Campaign UUID

    Returns:
        True if removed successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_campaign_assignment
            SET status = 'inactive', updated_at = NOW()
            WHERE user_id = $1 AND campaign_id = $2 AND status = 'active'
            """,
            user_id, campaign_id
        )

    return result != "UPDATE 0"


async def remove_user_contact_assignment(
    user_id: UUID,
    contact_id: UUID
) -> bool:
    """
    Remove a contact from a user (set status to inactive).

    Args:
        user_id: User UUID
        contact_id: Contact UUID

    Returns:
        True if removed successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_contact_assignment
            SET status = 'inactive', updated_at = NOW()
            WHERE user_id = $1 AND contact_id = $2 AND status = 'active'
            """,
            user_id, contact_id
        )

    return result != "UPDATE 0"
