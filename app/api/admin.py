"""
Admin Dashboard API Endpoints

Provides APIs for Admin Dashboard monitoring and management.
"""

import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.services import webhook_log_service
# from app.core.auth import get_current_user, require_admin  # TODO: Implement auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


# ========================================
# Request/Response Models
# ========================================

class WebhookLogResponse(BaseModel):
    """Single webhook log entry"""
    id: str
    event_type: str
    event_source: str
    campaign_id: Optional[str]
    campaign_name: Optional[str]
    contact_id: Optional[str]
    contact_email: Optional[str]
    organization_id: Optional[str]
    status: str
    payload: dict
    error_message: Optional[str]
    retry_count: int
    created_at: datetime


class WebhookLogsListResponse(BaseModel):
    """List of webhook logs with pagination"""
    success: bool
    data: dict


class RetryWebhookResponse(BaseModel):
    """Response from webhook retry"""
    success: bool
    message: str


class CleanupWebhookLogsResponse(BaseModel):
    """Response from cleanup operation"""
    success: bool
    deleted_count: int
    message: str


# ========================================
# Webhook Logs Endpoints
# ========================================

@router.get("/webhooks/logs", status_code=status.HTTP_200_OK)
async def get_webhook_logs(
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    campaign_id: Optional[UUID] = Query(None, description="Filter by campaign"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (success/failed/retrying)"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter logs until this date"),
    search: Optional[str] = Query(None, description="Full-text search in payload"),
    organization_id: Optional[UUID] = Query(None, description="Organization ID (for customer view)"),
    user_role: str = Query("member", description="User role (sb_admin, sb_operator, owner, admin, member)")
):
    """
    Get webhook logs with filters and pagination.

    **Admin Access:** sb_admin and sb_operator can see ALL logs across ALL organizations
    **Customer Access:** Customers only see their organization's logs (RLS applied)

    **Filters:**
    - event_type: Filter by webhook event type (email_sent, reply_received, etc.)
    - campaign_id: Filter by specific campaign
    - status: Filter by status (success, failed, retrying, pending)
    - date_from/date_to: Date range filter
    - search: Full-text search in webhook payload

    **Pagination:**
    - limit: Max 500 logs per request
    - offset: For pagination

    **Returns:**
    - List of webhook logs with campaign/contact info
    - Total count
    - Pagination info
    """
    # TODO: Add auth check and get user role from token
    # user = Depends(get_current_user)
    # user_role = user.role
    # organization_id = user.organization_id if user_role not in ['sb_admin', 'sb_operator'] else None

    try:
        result = await webhook_log_service.get_webhook_logs(
            limit=limit,
            offset=offset,
            event_type=event_type,
            campaign_id=campaign_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            search=search,
            organization_id=organization_id,
            user_role=user_role
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Failed to fetch webhook logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch webhook logs: {str(e)}"
        )


@router.get("/webhooks/logs/{log_id}", status_code=status.HTTP_200_OK)
async def get_webhook_log_detail(log_id: UUID):
    """
    Get detailed information for a single webhook log.

    **Args:**
    - log_id: Webhook log UUID

    **Returns:**
    - Complete webhook log with full payload
    """
    try:
        log = await webhook_log_service.get_webhook_log_by_id(log_id)

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook log {log_id} not found"
            )

        return {
            "success": True,
            "data": log
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch webhook log detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/webhooks/logs/{log_id}/retry", status_code=status.HTTP_200_OK)
async def retry_failed_webhook(log_id: UUID):
    """
    Retry a failed webhook.

    Marks the webhook log as "retrying" and increments retry count.
    Only works for webhooks with status="failed".

    **Admin Only**

    **Args:**
    - log_id: Webhook log UUID

    **Returns:**
    - Success message
    """
    # TODO: Add auth check (admin only)
    # user = Depends(require_admin)

    try:
        success = await webhook_log_service.retry_webhook_log(log_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook log not found or not in failed status"
            )

        return {
            "success": True,
            "message": f"Webhook {log_id} queued for retry"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/webhooks/logs/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_old_webhook_logs(
    older_than_days: int = Query(90, ge=1, le=365, description="Delete logs older than X days")
):
    """
    Delete old webhook logs to free up database space.

    **Admin Only** - Requires sb_admin role

    **Args:**
    - older_than_days: Delete logs older than this many days (default: 90, max: 365)

    **Returns:**
    - Number of deleted logs

    **⚠️ Warning:** This operation is irreversible!
    """
    # TODO: Add auth check (sb_admin only)
    # user = Depends(require_admin)
    # if user.role != 'sb_admin':
    #     raise HTTPException(status_code=403, detail="Only sb_admin can delete logs")

    try:
        deleted_count = await webhook_log_service.cleanup_old_webhook_logs(older_than_days)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} webhook logs older than {older_than_days} days"
        }

    except Exception as e:
        logger.error(f"Failed to cleanup webhook logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/webhooks/stats", status_code=status.HTTP_200_OK)
async def get_webhook_stats():
    """
    Get webhook statistics for dashboard.

    **Returns:**
    - Webhook stats by event type
    - Recent failed webhooks
    - Overall webhook statistics
    """
    try:
        stats = await webhook_log_service.get_webhook_stats()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Failed to fetch webhook stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Dashboard Stats Endpoints
# ========================================

@router.get("/dashboard/stats", status_code=status.HTTP_200_OK)
async def get_dashboard_stats(
    organization_id: Optional[UUID] = Query(None, description="Organization ID (for customer view)")
):
    """
    Get overall dashboard statistics.

    **Admin View:** Shows stats across ALL organizations
    **Customer View:** Shows stats for specific organization only

    **Returns:**
    - Total campaigns, contacts, messages
    - Webhook statistics
    - API health metrics
    - User counts
    """
    # TODO: Add auth check
    # user = Depends(get_current_user)
    # if user.role not in ['sb_admin', 'sb_operator']:
    #     organization_id = user.organization_id

    try:
        from app.core import db

        async with db.tenant_db_pool.acquire() as conn:
            # Build WHERE clause for organization filtering
            org_filter = ""
            params = []
            if organization_id:
                org_filter = "WHERE c.organization_id = $1"
                params.append(organization_id)

            # Get campaign stats
            campaign_stats = await conn.fetchrow(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as today,
                    COUNT(*) FILTER (WHERE status = 'active') as active
                FROM campaign c
                {org_filter}
            """, *params)

            # Get contact stats
            contact_stats = await conn.fetchrow(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as today,
                    ROUND(AVG(lead_score), 1) as lead_score_avg
                FROM contact c
                {org_filter.replace('c.organization_id', 'c.organization_id') if organization_id else ''}
            """, *params)

            # Get message stats
            message_stats = await conn.fetchrow(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE sent_at >= NOW() - INTERVAL '24 hours') as today,
                    ROUND(
                        COUNT(*) FILTER (WHERE opened_at IS NOT NULL)::numeric * 100 /
                        NULLIF(COUNT(*), 0), 1
                    ) as open_rate,
                    ROUND(
                        COUNT(*) FILTER (WHERE replied_at IS NOT NULL)::numeric * 100 /
                        NULLIF(COUNT(*), 0), 1
                    ) as reply_rate
                FROM message m
                JOIN campaign c ON m.campaign_id = c.id
                {org_filter.replace('c.organization_id', 'c.organization_id') if organization_id else ''}
            """, *params)

            # Get webhook stats (last hour and 24h)
            webhook_filter = ""
            if organization_id:
                webhook_filter = "WHERE wl.organization_id = $1"

            webhook_stats = await conn.fetchrow(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as last_hour,
                    COUNT(*) FILTER (WHERE status = 'failed' AND created_at >= NOW() - INTERVAL '1 hour') as failed_last_hour,
                    CASE
                        WHEN COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 minute') > 0
                        THEN ROUND(COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 minute')::numeric / 60, 1)
                        ELSE 0
                    END as avg_per_second
                FROM webhook_log wl
                {webhook_filter}
            """, *params)

            # Get user count (admin only, no org filter for now)
            user_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'active') as active_now
                FROM "user"
            """)

        return {
            "success": True,
            "data": {
                "campaigns": dict(campaign_stats) if campaign_stats else {},
                "contacts": dict(contact_stats) if contact_stats else {},
                "messages": dict(message_stats) if message_stats else {},
                "webhooks": dict(webhook_stats) if webhook_stats else {},
                "users": dict(user_stats) if user_stats else {},
                "api_calls": {
                    "total": 0,  # TODO: Implement API call tracking
                    "status": "healthy",
                    "avg_response_time": 0
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to fetch dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/dashboard/recent-activity", status_code=status.HTTP_200_OK)
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=100, description="Number of activities to return")
):
    """
    Get recent activity feed for dashboard.

    Combines webhook events, campaign changes, and user actions into a unified activity feed.

    **Returns:**
    - Recent webhook events
    - Recent campaign/contact activities
    - Sorted by timestamp (newest first)
    """
    try:
        # Get recent webhook activity
        webhook_activity = await webhook_log_service.get_recent_webhook_activity(limit)

        # Format for activity feed
        activities = []
        for wh in webhook_activity:
            activities.append({
                "type": "webhook",
                "event_type": wh["event_type"],
                "event_source": wh["event_source"],
                "description": f"Webhook received: {wh['event_type']}",
                "campaign_name": wh.get("campaign_name"),
                "contact_email": wh.get("contact_email"),
                "status": wh["status"],
                "timestamp": wh["created_at"]
            })

        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "success": True,
            "data": activities[:limit]
        }

    except Exception as e:
        logger.error(f"Failed to fetch recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Health Check
# ========================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def admin_api_health():
    """
    Health check for Admin Dashboard API endpoints.

    **Returns:**
    - API health status
    - Available endpoints
    """
    return {
        "status": "healthy",
        "service": "admin_dashboard_api",
        "endpoints": {
            "webhook_logs": "/api/admin/webhooks/logs",
            "dashboard_stats": "/api/admin/dashboard/stats",
            "recent_activity": "/api/admin/dashboard/recent-activity"
        }
    }
