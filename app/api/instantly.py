"""
Instantly API Endpoints
REST API for Instantly integration management
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.services.campaign_service import CampaignService
from app.services.email_account_service import EmailAccountService
from app.services.message_service import MessageService
# from app.core.auth import get_current_user, require_admin  # TODO: Implement auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/instantly", tags=["Instantly"])


# ========================================
# Request/Response Models
# ========================================

class SyncWorkspaceRequest(BaseModel):
    """Request to sync workspace data"""
    provider_connection_id: UUID
    sync_campaigns: bool = True
    sync_email_accounts: bool = True


class SyncWorkspaceResponse(BaseModel):
    """Response from workspace sync"""
    success: bool
    campaigns_imported: int = 0
    campaigns_updated: int = 0
    accounts_imported: int = 0
    accounts_updated: int = 0
    errors: list = []


# ========================================
# Admin Endpoints (Cross-Organization Access)
# ========================================

@router.get("/admin/campaigns", status_code=status.HTTP_200_OK)
async def admin_get_all_campaigns():
    """
    Get ALL campaigns across ALL organizations

    **Admin Only** - Requires sb_admin or sb_operator role

    Returns:
        List of all campaigns with organization info
    """
    # TODO: Add auth check
    # user = Depends(require_admin)

    try:
        campaigns = await CampaignService.get_all_campaigns_for_admin()

        return {
            "success": True,
            "campaigns": campaigns,
            "count": len(campaigns)
        }

    except Exception as e:
        logger.error(f"Failed to fetch admin campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin/email-accounts", status_code=status.HTTP_200_OK)
async def admin_get_all_email_accounts():
    """
    Get ALL email accounts across ALL organizations

    **Admin Only** - Requires sb_admin or sb_operator role

    Returns:
        List of all email accounts with organization info
    """
    # TODO: Add auth check
    # user = Depends(require_admin)

    try:
        accounts = await EmailAccountService.get_all_accounts_for_admin()

        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }

    except Exception as e:
        logger.error(f"Failed to fetch admin email accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin/campaign/{campaign_id}/stats", status_code=status.HTTP_200_OK)
async def admin_get_campaign_stats(campaign_id: UUID):
    """
    Get campaign statistics

    **Admin Only**

    Args:
        campaign_id: Campaign UUID

    Returns:
        Campaign stats (sent, opened, replied)
    """
    try:
        stats = await CampaignService.get_campaign_stats(campaign_id)

        return {
            "success": True,
            "campaign_id": str(campaign_id),
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to fetch campaign stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin/email-account/{account_id}/stats", status_code=status.HTTP_200_OK)
async def admin_get_account_stats(account_id: UUID):
    """
    Get email account statistics

    **Admin Only**

    Args:
        account_id: Email account UUID

    Returns:
        Account stats (usage, campaigns, etc.)
    """
    try:
        stats = await EmailAccountService.get_account_stats(account_id)

        return {
            "success": True,
            "account_id": str(account_id),
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to fetch account stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Customer Endpoints (Organization-Scoped)
# ========================================

@router.get("/campaigns", status_code=status.HTTP_200_OK)
async def get_user_campaigns(
    organization_id: UUID = Query(..., description="Organization UUID")
):
    """
    Get campaigns for current user's organization

    **Customer View** - RLS applies automatically

    Args:
        organization_id: Organization UUID (from auth token)

    Returns:
        List of campaigns for this organization
    """
    # TODO: Add auth check and get org_id from token
    # user = Depends(get_current_user)
    # organization_id = user.organization_id

    try:
        campaigns = await CampaignService.get_campaigns_for_org(organization_id)

        return {
            "success": True,
            "campaigns": campaigns,
            "count": len(campaigns)
        }

    except Exception as e:
        logger.error(f"Failed to fetch user campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/email-accounts", status_code=status.HTTP_200_OK)
async def get_user_email_accounts(
    organization_id: UUID = Query(..., description="Organization UUID")
):
    """
    Get email accounts for current user's organization

    **Customer View** - RLS applies automatically

    Args:
        organization_id: Organization UUID (from auth token)

    Returns:
        List of email accounts for this organization
    """
    # TODO: Add auth check
    # user = Depends(get_current_user)
    # organization_id = user.organization_id

    try:
        accounts = await EmailAccountService.get_accounts_for_org(organization_id)

        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }

    except Exception as e:
        logger.error(f"Failed to fetch user email accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/campaign/{campaign_id}/messages", status_code=status.HTTP_200_OK)
async def get_campaign_messages(
    campaign_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get messages for a campaign

    Args:
        campaign_id: Campaign UUID
        limit: Max results (1-500)
        offset: Pagination offset

    Returns:
        List of messages
    """
    try:
        messages = await MessageService.get_messages_for_campaign(
            campaign_id,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Failed to fetch campaign messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_organization_stats(
    organization_id: UUID = Query(..., description="Organization UUID")
):
    """
    Get overall statistics for organization

    Args:
        organization_id: Organization UUID

    Returns:
        Overall message stats (sent, opened, replied, rates)
    """
    try:
        stats = await MessageService.get_message_stats_for_org(organization_id)

        return {
            "success": True,
            "organization_id": str(organization_id),
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to fetch organization stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Sync Endpoints (Admin Only)
# ========================================

@router.post("/sync/workspace", status_code=status.HTTP_200_OK)
async def sync_workspace(request: SyncWorkspaceRequest):
    """
    Manually trigger sync of Instantly workspace

    **Admin Only** - Imports campaigns and email accounts from Instantly

    This endpoint requires Instantly API key to be configured.
    Use this to:
    1. Import existing campaigns from Instantly
    2. Import email accounts
    3. Update campaign/account statuses

    Args:
        request: Sync configuration

    Returns:
        Sync results (imported/updated counts)
    """
    # TODO: Add auth check
    # user = Depends(require_admin)

    logger.info(f"Starting workspace sync for provider_connection: {request.provider_connection_id}")

    try:
        # TODO: Implement actual sync with Instantly API
        # This requires:
        # 1. Get provider_connection from database
        # 2. Get API key from provider_connection
        # 3. Initialize InstantlyClient
        # 4. Fetch campaigns and accounts from Instantly
        # 5. Import to database

        # Placeholder response
        return SyncWorkspaceResponse(
            success=True,
            campaigns_imported=0,
            campaigns_updated=0,
            accounts_imported=0,
            accounts_updated=0,
            errors=["Sync not yet implemented - requires API key configuration"]
        )

    except Exception as e:
        logger.error(f"Workspace sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/sync/campaign/{campaign_id}", status_code=status.HTTP_200_OK)
async def sync_single_campaign(campaign_id: str):
    """
    Sync single campaign from Instantly

    **Admin Only**

    Args:
        campaign_id: Instantly campaign ID (external_id)

    Returns:
        Sync result
    """
    # TODO: Implement single campaign sync
    return {
        "success": True,
        "message": "Campaign sync not yet implemented",
        "campaign_id": campaign_id
    }


# ========================================
# Search Endpoints
# ========================================

@router.get("/search/messages", status_code=status.HTTP_200_OK)
async def search_messages(
    organization_id: UUID = Query(..., description="Organization UUID"),
    query: str = Query(..., min_length=3, description="Search query"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search messages by email, subject, or content

    Args:
        organization_id: Organization UUID
        query: Search query (min 3 chars)
        limit: Max results (1-200)

    Returns:
        Matching messages
    """
    try:
        messages = await MessageService.search_messages(
            organization_id,
            query,
            limit=limit
        )

        return {
            "success": True,
            "query": query,
            "messages": messages,
            "count": len(messages)
        }

    except Exception as e:
        logger.error(f"Message search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Health Check
# ========================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def instantly_api_health():
    """
    Health check for Instantly API endpoints

    Returns:
        API health status
    """
    return {
        "status": "healthy",
        "service": "instantly_api",
        "endpoints": {
            "admin": "/api/instantly/admin/*",
            "customer": "/api/instantly/*",
            "webhooks": "/webhooks/instantly/webhook"
        }
    }
