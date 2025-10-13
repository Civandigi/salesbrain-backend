"""
Onboarding Link Service

Handles creation and management of onboarding links.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID

from app.core import db


async def create_onboarding_link(
    organization_id: UUID,
    created_by: UUID,
    template_name: str = "Basic Onboarding",
    welcome_message: str = "Welcome to Salesbrain!",
    expiration_days: int = 7,
    total_steps: int = 5
) -> Dict[str, Any]:
    """
    Create a new onboarding link.

    Args:
        organization_id: Organization UUID
        created_by: User UUID who created the link
        template_name: Onboarding template name
        welcome_message: Custom welcome message
        expiration_days: Days until link expires
        total_steps: Total steps in onboarding flow

    Returns:
        Dict with link details
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Generate unique token
        link_token = await conn.fetchval(
            """
            SELECT generate_onboarding_token()
            """
        )

        # Build full URL
        link_url = f"https://onboarding.salesbrain.com/o/{link_token}"

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        # Insert link
        link_id = await conn.fetchval(
            """
            INSERT INTO onboarding_link (
                organization_id, created_by, link_token, link_url,
                template_name, welcome_message, expires_at, total_steps,
                status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')
            RETURNING id
            """,
            organization_id, created_by, link_token, link_url,
            template_name, welcome_message, expires_at, total_steps
        )

        # Get created link
        link = await conn.fetchrow(
            """
            SELECT * FROM onboarding_link WHERE id = $1
            """,
            link_id
        )

    return dict(link)


async def get_onboarding_links(
    organization_id: Optional[UUID] = None,
    status: Optional[str] = None,
    created_by: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get onboarding links with filters.

    Args:
        organization_id: Filter by organization
        status: Filter by status (active, expired, used, revoked)
        created_by: Filter by creator
        limit: Number of links to return
        offset: Pagination offset

    Returns:
        Dict with links and pagination info
    """
    where_clauses = []
    params = []
    param_count = 0

    if organization_id:
        param_count += 1
        where_clauses.append(f"organization_id = ${param_count}")
        params.append(organization_id)

    if status:
        param_count += 1
        where_clauses.append(f"status = ${param_count}")
        params.append(status)

    if created_by:
        param_count += 1
        where_clauses.append(f"created_by = ${param_count}")
        params.append(created_by)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Add limit and offset
    param_count += 1
    limit_param = param_count
    params.append(limit)

    param_count += 1
    offset_param = param_count
    params.append(offset)

    async with db.tenant_db_pool.acquire() as conn:
        # Get total count
        total = await conn.fetchval(
            f"""
            SELECT COUNT(*) FROM onboarding_link {where_sql}
            """,
            *params[:-2]
        )

        # Get links with creator info
        rows = await conn.fetch(
            f"""
            SELECT
                ol.*,
                o.name as organization_name,
                u.email as created_by_email,
                u.first_name as created_by_first_name,
                u.last_name as created_by_last_name
            FROM onboarding_link ol
            JOIN organization o ON ol.organization_id = o.id
            LEFT JOIN "user" u ON ol.created_by = u.id
            {where_sql}
            ORDER BY ol.created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
            """,
            *params
        )

        links = [dict(row) for row in rows]

    return {
        "links": links,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


async def get_onboarding_link_by_id(link_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a single onboarding link by ID.

    Args:
        link_id: Onboarding link UUID

    Returns:
        Link dict or None
    """
    async with db.tenant_db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ol.*,
                o.name as organization_name,
                u.email as created_by_email
            FROM onboarding_link ol
            JOIN organization o ON ol.organization_id = o.id
            LEFT JOIN "user" u ON ol.created_by = u.id
            WHERE ol.id = $1
            """,
            link_id
        )

    return dict(row) if row else None


async def get_onboarding_link_by_token(link_token: str) -> Optional[Dict[str, Any]]:
    """
    Get an onboarding link by its token (for public access).

    Args:
        link_token: Link token

    Returns:
        Link dict or None
    """
    async with db.tenant_db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ol.*,
                o.name as organization_name
            FROM onboarding_link ol
            JOIN organization o ON ol.organization_id = o.id
            WHERE ol.link_token = $1
            """,
            link_token
        )

    return dict(row) if row else None


async def track_link_access(
    link_token: str,
    ip_address: str,
    user_agent: str
) -> bool:
    """
    Track an access to an onboarding link.

    Args:
        link_token: Link token
        ip_address: IP address of accessor
        user_agent: User agent string

    Returns:
        True if tracked successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        await conn.execute(
            """
            SELECT track_onboarding_link_access($1, $2, $3)
            """,
            link_token, ip_address, user_agent
        )

    return True


async def update_link_progress(
    link_token: str,
    current_step: int,
    progress_percentage: int
) -> bool:
    """
    Update onboarding progress for a link.

    Args:
        link_token: Link token
        current_step: Current step number
        progress_percentage: Progress (0-100)

    Returns:
        True if updated successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                current_step = $2,
                progress_percentage = $3,
                updated_at = NOW()
            WHERE link_token = $1 AND status = 'active'
            """,
            link_token, current_step, progress_percentage
        )

    return result != "UPDATE 0"


async def complete_onboarding(link_token: str) -> bool:
    """
    Mark an onboarding link as completed.

    Args:
        link_token: Link token

    Returns:
        True if completed successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                status = 'used',
                completed_at = NOW(),
                progress_percentage = 100,
                updated_at = NOW()
            WHERE link_token = $1 AND status = 'active'
            """,
            link_token
        )

    return result != "UPDATE 0"


async def revoke_onboarding_link(
    link_id: UUID,
    revoked_by: UUID,
    reason: str = "Revoked by admin"
) -> bool:
    """
    Revoke an onboarding link.

    Args:
        link_id: Link UUID
        revoked_by: User UUID who revoked the link
        reason: Reason for revocation

    Returns:
        True if revoked successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                status = 'revoked',
                revoked_at = NOW(),
                revoked_by = $2,
                revoked_reason = $3,
                updated_at = NOW()
            WHERE id = $1 AND status IN ('active', 'expired')
            """,
            link_id, revoked_by, reason
        )

    return result != "UPDATE 0"


async def extend_onboarding_link(
    link_id: UUID,
    additional_days: int = 7
) -> bool:
    """
    Extend the expiration of an onboarding link.

    Args:
        link_id: Link UUID
        additional_days: Days to add to expiration

    Returns:
        True if extended successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                expires_at = expires_at + ($2 || ' days')::INTERVAL,
                status = CASE
                    WHEN status = 'expired' THEN 'active'
                    ELSE status
                END,
                updated_at = NOW()
            WHERE id = $1
            """,
            link_id, additional_days
        )

    return result != "UPDATE 0"


async def expire_old_links() -> int:
    """
    Expire all onboarding links past their expiration date.

    Returns:
        Number of links expired
    """
    async with db.tenant_db_pool.acquire() as conn:
        expired_count = await conn.fetchval(
            """
            SELECT expire_old_onboarding_links()
            """
        )

    return expired_count
