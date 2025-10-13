"""
User Assignment API Endpoints

Provides APIs for managing user-campaign and user-contact assignments.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel

from app.services import user_assignment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["User Assignments"])


# ========================================
# Request/Response Models
# ========================================

class AssignCampaignsRequest(BaseModel):
    """Request to assign user to campaigns"""
    campaign_ids: List[UUID]
    role: str = "member"
    can_edit: bool = False
    can_view_stats: bool = True
    can_manage_contacts: bool = False


class AssignContactsRequest(BaseModel):
    """Request to assign contacts to user"""
    contact_ids: List[UUID]
    assignment_type: str = "manual"


class AssignmentResponse(BaseModel):
    """Response from assignment operation"""
    success: bool
    success_count: int
    failed_count: int
    failed_items: List[dict]


# ========================================
# Endpoints
# ========================================

@router.get("/{user_id}/assignments", status_code=status.HTTP_200_OK)
async def get_user_assignments(user_id: UUID):
    """
    Get all campaigns and contacts assigned to a user.

    **Returns:**
    - campaigns: List of assigned campaigns with permissions
    - contacts: List of assigned contacts with metadata
    - counts: Total assignments
    """
    try:
        result = await user_assignment_service.get_user_assignments(user_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Failed to fetch user assignments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/assign-campaigns", status_code=status.HTTP_200_OK)
async def assign_user_to_campaigns(
    user_id: UUID,
    request: AssignCampaignsRequest,
    assigned_by: UUID = Body(..., embed=True),
    organization_id: UUID = Body(..., embed=True)
):
    """
    Assign a user to multiple campaigns.

    **Args:**
    - user_id: User UUID to assign
    - campaign_ids: List of campaign UUIDs
    - role: User role (owner, admin, member, viewer)
    - permissions: can_edit, can_view_stats, can_manage_contacts

    **Returns:**
    - success_count: Number of successful assignments
    - failed_count: Number of failed assignments
    """
    try:
        result = await user_assignment_service.assign_user_to_campaigns(
            user_id=user_id,
            campaign_ids=request.campaign_ids,
            assigned_by=assigned_by,
            organization_id=organization_id,
            role=request.role,
            can_edit=request.can_edit,
            can_view_stats=request.can_view_stats,
            can_manage_contacts=request.can_manage_contacts
        )

        return {
            "success": True,
            "success_count": result["success_count"],
            "failed_count": result["failed_count"],
            "failed_items": result["failed_campaigns"]
        }

    except Exception as e:
        logger.error(f"Failed to assign user to campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/assign-contacts", status_code=status.HTTP_200_OK)
async def assign_contacts_to_user(
    user_id: UUID,
    request: AssignContactsRequest,
    assigned_by: UUID = Body(..., embed=True),
    organization_id: UUID = Body(..., embed=True)
):
    """
    Assign multiple contacts to a user.

    **Args:**
    - user_id: User UUID to assign contacts to
    - contact_ids: List of contact UUIDs
    - assignment_type: manual, round_robin, lead_score, territory

    **Returns:**
    - success_count: Number of successful assignments
    - failed_count: Number of failed assignments
    """
    try:
        result = await user_assignment_service.assign_contacts_to_user(
            user_id=user_id,
            contact_ids=request.contact_ids,
            assigned_by=assigned_by,
            organization_id=organization_id,
            assignment_type=request.assignment_type
        )

        return {
            "success": True,
            "success_count": result["success_count"],
            "failed_count": result["failed_count"],
            "failed_items": result["failed_contacts"]
        }

    except Exception as e:
        logger.error(f"Failed to assign contacts to user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_organization_users(
    organization_id: UUID
):
    """
    Get all users in an organization with assignment counts.

    **Returns:**
    - List of users with campaigns_count and contacts_count
    """
    try:
        users = await user_assignment_service.get_organization_users_with_assignments(
            organization_id
        )

        return {
            "success": True,
            "data": users
        }

    except Exception as e:
        logger.error(f"Failed to fetch organization users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/campaigns/{campaign_id}", status_code=status.HTTP_200_OK)
async def remove_user_from_campaign(
    user_id: UUID,
    campaign_id: UUID
):
    """
    Remove a user from a campaign.

    **Returns:**
    - success: True if removed
    """
    try:
        success = await user_assignment_service.remove_user_campaign_assignment(
            user_id, campaign_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or already inactive"
            )

        return {
            "success": True,
            "message": "User removed from campaign"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove user from campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/contacts/{contact_id}", status_code=status.HTTP_200_OK)
async def remove_contact_from_user(
    user_id: UUID,
    contact_id: UUID
):
    """
    Remove a contact from a user.

    **Returns:**
    - success: True if removed
    """
    try:
        success = await user_assignment_service.remove_user_contact_assignment(
            user_id, contact_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or already inactive"
            )

        return {
            "success": True,
            "message": "Contact removed from user"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove contact from user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
