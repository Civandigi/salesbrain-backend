"""
Onboarding Links API Endpoints

Provides APIs for generating and managing onboarding links.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel

from app.services import onboarding_link_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/onboarding", tags=["Onboarding Links"])


# ========================================
# Request/Response Models
# ========================================

class CreateOnboardingLinkRequest(BaseModel):
    """Request to create onboarding link"""
    organization_id: UUID
    template_name: str = "Basic Onboarding"
    welcome_message: str = "Welcome to Salesbrain!"
    expiration_days: int = 7
    total_steps: int = 5


class ExtendLinkRequest(BaseModel):
    """Request to extend link expiration"""
    additional_days: int = 7


class RevokeLinkRequest(BaseModel):
    """Request to revoke link"""
    reason: str = "Revoked by admin"


class UpdateProgressRequest(BaseModel):
    """Request to update onboarding progress"""
    current_step: int
    progress_percentage: int


# ========================================
# Endpoints
# ========================================

@router.post("/create-link", status_code=status.HTTP_201_CREATED)
async def create_onboarding_link(
    request: CreateOnboardingLinkRequest,
    created_by: UUID = Query(..., description="User UUID creating the link")
):
    """
    Create a new onboarding link.

    **Args:**
    - organization_id: Organization UUID
    - template_name: Onboarding template (Basic/Advanced/Enterprise)
    - welcome_message: Custom welcome message
    - expiration_days: Days until link expires
    - total_steps: Total steps in onboarding flow

    **Returns:**
    - link_url: Full onboarding URL
    - link_id: UUID of created link
    - expires_at: Expiration timestamp
    """
    try:
        link = await onboarding_link_service.create_onboarding_link(
            organization_id=request.organization_id,
            created_by=created_by,
            template_name=request.template_name,
            welcome_message=request.welcome_message,
            expiration_days=request.expiration_days,
            total_steps=request.total_steps
        )

        return {
            "success": True,
            "data": {
                "link_url": link["link_url"],
                "link_id": str(link["id"]),
                "link_token": link["link_token"],
                "expires_at": link["expires_at"].isoformat(),
                "status": link["status"]
            }
        }

    except Exception as e:
        logger.error(f"Failed to create onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/links", status_code=status.HTTP_200_OK)
async def get_onboarding_links(
    organization_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    created_by: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get onboarding links with filters.

    **Filters:**
    - organization_id: Filter by organization
    - status: Filter by status (active, expired, used, revoked)
    - created_by: Filter by creator

    **Returns:**
    - List of onboarding links with metadata
    """
    try:
        result = await onboarding_link_service.get_onboarding_links(
            organization_id=organization_id,
            status=status_filter,
            created_by=created_by,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Failed to fetch onboarding links: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/link/{link_id}", status_code=status.HTTP_200_OK)
async def get_onboarding_link_detail(link_id: UUID):
    """
    Get detailed information for a single onboarding link.

    **Returns:**
    - Complete link details with tracking data
    """
    try:
        link = await onboarding_link_service.get_onboarding_link_by_id(link_id)

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Onboarding link {link_id} not found"
            )

        return {
            "success": True,
            "data": link
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch onboarding link detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/link/{link_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_onboarding_link(
    link_id: UUID,
    request: RevokeLinkRequest,
    revoked_by: UUID = Query(..., description="User UUID revoking the link")
):
    """
    Revoke an onboarding link.

    **Admin Only**

    **Args:**
    - link_id: Link UUID
    - reason: Reason for revocation

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.revoke_onboarding_link(
            link_id=link_id,
            revoked_by=revoked_by,
            reason=request.reason
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or already revoked/used"
            )

        return {
            "success": True,
            "message": f"Onboarding link {link_id} revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/link/{link_id}/extend", status_code=status.HTTP_200_OK)
async def extend_onboarding_link(
    link_id: UUID,
    request: ExtendLinkRequest
):
    """
    Extend the expiration of an onboarding link.

    **Args:**
    - link_id: Link UUID
    - additional_days: Days to add to expiration

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.extend_onboarding_link(
            link_id=link_id,
            additional_days=request.additional_days
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )

        return {
            "success": True,
            "message": f"Link expiration extended by {request.additional_days} days"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extend onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Public Onboarding Access Endpoints
# ========================================

@router.get("/o/{link_token}", status_code=status.HTTP_200_OK)
async def access_onboarding_link(
    link_token: str,
    request: Request
):
    """
    Access an onboarding link (public endpoint).

    Tracks access and returns link details.

    **Args:**
    - link_token: Unique link token

    **Returns:**
    - Link details and onboarding configuration
    """
    try:
        # Get link
        link = await onboarding_link_service.get_onboarding_link_by_token(link_token)

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding link not found"
            )

        # Check if expired
        if link["status"] == "expired":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This onboarding link has expired"
            )

        # Check if revoked
        if link["status"] == "revoked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This onboarding link has been revoked"
            )

        # Check if already used
        if link["status"] == "used":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This onboarding link has already been used"
            )

        # Track access
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")

        await onboarding_link_service.track_link_access(
            link_token=link_token,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "success": True,
            "data": {
                "organization_name": link["organization_name"],
                "welcome_message": link["welcome_message"],
                "total_steps": link["total_steps"],
                "current_step": link["current_step"],
                "progress_percentage": link["progress_percentage"],
                "template_name": link["template_name"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to access onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/o/{link_token}/progress", status_code=status.HTTP_200_OK)
async def update_onboarding_progress(
    link_token: str,
    request: UpdateProgressRequest
):
    """
    Update progress for an onboarding session.

    **Args:**
    - link_token: Unique link token
    - current_step: Current step number
    - progress_percentage: Progress (0-100)

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.update_link_progress(
            link_token=link_token,
            current_step=request.current_step,
            progress_percentage=request.progress_percentage
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or not active"
            )

        return {
            "success": True,
            "message": "Progress updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update onboarding progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/o/{link_token}/complete", status_code=status.HTTP_200_OK)
async def complete_onboarding(link_token: str):
    """
    Mark onboarding as completed.

    **Args:**
    - link_token: Unique link token

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.complete_onboarding(link_token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or not active"
            )

        return {
            "success": True,
            "message": "Onboarding completed successfully! 🎉"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
