"""
Webhook Log Service

Handles database operations for webhook logging and monitoring.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncpg
from uuid import UUID

from app.core import db


async def create_webhook_log(
    event_type: str,
    payload: Dict[str, Any],
    event_source: str = "instantly",
    campaign_id: Optional[UUID] = None,
    contact_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> UUID:
    """
    Create a new webhook log entry.

    Args:
        event_type: Type of webhook event (e.g., email_sent, reply_received)
        payload: Full webhook payload as dict
        event_source: Source of webhook (instantly, weconnect, n8n)
        campaign_id: Related campaign UUID
        contact_id: Related contact UUID
        organization_id: Organization UUID for RLS
        status: Log status (success, failed, retrying, pending)
        error_message: Error message if status is failed
        ip_address: IP address of webhook sender
        user_agent: User agent of webhook sender

    Returns:
        UUID of created webhook log
    """
    async with db.tenant_db_pool.acquire() as conn:
        log_id = await conn.fetchval(
            """
            INSERT INTO webhook_log (
                event_type, event_source, campaign_id, contact_id,
                organization_id, status, payload, error_message,
                ip_address, user_agent, processed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            event_type,
            event_source,
            campaign_id,
            contact_id,
            organization_id,
            status,
            payload,
            error_message,
            ip_address,
            user_agent,
            datetime.utcnow() if status == "success" else None
        )

    return log_id


async def get_webhook_logs(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    campaign_id: Optional[UUID] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    organization_id: Optional[UUID] = None,
    user_role: str = "member"
) -> Dict[str, Any]:
    """
    Get webhook logs with filters and pagination.

    Args:
        limit: Number of records to return
        offset: Pagination offset
        event_type: Filter by event type
        campaign_id: Filter by campaign
        status: Filter by status (success, failed, retrying)
        date_from: Filter logs from this date
        date_to: Filter logs until this date
        search: Full-text search in payload
        organization_id: Organization ID for RLS (customers)
        user_role: User role (sb_admin, sb_operator, owner, admin, member)

    Returns:
        Dict with logs and pagination info
    """
    # Build WHERE clause dynamically
    where_clauses = []
    params = []
    param_count = 0

    # RLS: If not admin, filter by organization
    if user_role not in ['sb_admin', 'sb_operator'] and organization_id:
        param_count += 1
        where_clauses.append(f"wl.organization_id = ${param_count}")
        params.append(organization_id)

    if event_type:
        param_count += 1
        where_clauses.append(f"wl.event_type = ${param_count}")
        params.append(event_type)

    if campaign_id:
        param_count += 1
        where_clauses.append(f"wl.campaign_id = ${param_count}")
        params.append(campaign_id)

    if status:
        param_count += 1
        where_clauses.append(f"wl.status = ${param_count}")
        params.append(status)

    if date_from:
        param_count += 1
        where_clauses.append(f"wl.created_at >= ${param_count}")
        params.append(date_from)

    if date_to:
        param_count += 1
        where_clauses.append(f"wl.created_at <= ${param_count}")
        params.append(date_to)

    if search:
        param_count += 1
        where_clauses.append(f"wl.payload::text ILIKE ${param_count}")
        params.append(f"%{search}%")

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
        count_query = f"""
            SELECT COUNT(*)
            FROM webhook_log wl
            {where_sql}
        """
        total = await conn.fetchval(count_query, *params[:-2])  # Without limit/offset

        # Get logs with campaign and contact info
        logs_query = f"""
            SELECT
                wl.id,
                wl.event_type,
                wl.event_source,
                wl.campaign_id,
                c.name as campaign_name,
                wl.contact_id,
                ct.email as contact_email,
                wl.organization_id,
                wl.status,
                wl.payload,
                wl.error_message,
                wl.retry_count,
                wl.last_retry_at,
                wl.created_at,
                wl.processed_at
            FROM webhook_log wl
            LEFT JOIN campaign c ON wl.campaign_id = c.id
            LEFT JOIN contact ct ON wl.contact_id = ct.id
            {where_sql}
            ORDER BY wl.created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """

        rows = await conn.fetch(logs_query, *params)

        logs = [dict(row) for row in rows]

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


async def get_webhook_log_by_id(log_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a single webhook log by ID.

    Args:
        log_id: Webhook log UUID

    Returns:
        Webhook log dict or None
    """
    async with db.tenant_db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                wl.*,
                c.name as campaign_name,
                ct.email as contact_email
            FROM webhook_log wl
            LEFT JOIN campaign c ON wl.campaign_id = c.id
            LEFT JOIN contact ct ON wl.contact_id = ct.id
            WHERE wl.id = $1
            """,
            log_id
        )

    return dict(row) if row else None


async def retry_webhook_log(log_id: UUID) -> bool:
    """
    Mark a webhook log for retry and increment retry count.

    Args:
        log_id: Webhook log UUID

    Returns:
        True if updated successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE webhook_log
            SET
                status = 'retrying',
                retry_count = retry_count + 1,
                last_retry_at = NOW()
            WHERE id = $1 AND status = 'failed'
            """,
            log_id
        )

    # Check if any row was updated
    return result != "UPDATE 0"


async def cleanup_old_webhook_logs(days_to_keep: int = 90) -> int:
    """
    Delete webhook logs older than specified days.

    Args:
        days_to_keep: Number of days to keep logs (default: 90)

    Returns:
        Number of deleted logs
    """
    async with db.tenant_db_pool.acquire() as conn:
        deleted_count = await conn.fetchval(
            """
            SELECT * FROM cleanup_old_webhook_logs($1)
            """,
            days_to_keep
        )

    return deleted_count


async def get_webhook_stats() -> Dict[str, Any]:
    """
    Get webhook log statistics for dashboard.

    Returns:
        Dict with webhook statistics
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Get stats from materialized view
        stats = await conn.fetch(
            """
            SELECT * FROM webhook_log_stats
            ORDER BY total_count DESC
            """
        )

        # Get recent failed logs
        recent_failed = await conn.fetch(
            """
            SELECT
                id, event_type, error_message, created_at
            FROM webhook_log
            WHERE status = 'failed'
                AND created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10
            """
        )

        # Get overall stats
        overall = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_logs,
                COUNT(*) FILTER (WHERE status = 'success') as success_count,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as last_hour,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                ROUND(AVG(retry_count), 2) as avg_retry_count
            FROM webhook_log
            """
        )

    return {
        "by_event_type": [dict(row) for row in stats],
        "recent_failed": [dict(row) for row in recent_failed],
        "overall": dict(overall) if overall else {}
    }


async def get_recent_webhook_activity(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent webhook activity for dashboard feed.

    Args:
        limit: Number of recent activities to return

    Returns:
        List of recent webhook activities
    """
    async with db.tenant_db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                wl.id,
                wl.event_type,
                wl.event_source,
                wl.status,
                c.name as campaign_name,
                ct.email as contact_email,
                wl.created_at
            FROM webhook_log wl
            LEFT JOIN campaign c ON wl.campaign_id = c.id
            LEFT JOIN contact ct ON wl.contact_id = ct.id
            ORDER BY wl.created_at DESC
            LIMIT $1
            """,
            limit
        )

    return [dict(row) for row in rows]
