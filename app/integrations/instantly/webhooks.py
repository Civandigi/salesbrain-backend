"""
Instantly Webhook Handler
Receives and processes webhook events from Instantly.ai
"""

import logging
from fastapi import APIRouter, Request, HTTPException, status

from app.integrations.instantly.schemas import InstantlyWebhookPayload, InstantlyEventType
from app.services.message_service import MessageService
from app.services.campaign_service import CampaignService
from app.services.email_account_service import EmailAccountService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/instantly", tags=["Instantly Webhooks"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def instantly_webhook(payload: InstantlyWebhookPayload):
    """
    Receive and process Instantly webhook events

    Instantly sends webhooks for various events:
    - Email events: sent, opened, replied, bounced, clicked
    - Lead status: interested, not_interested, neutral
    - Account events: errors, campaign completion

    Authentication: None (Instantly doesn't sign webhooks)
    We validate workspace_id against our database

    Args:
        payload: Webhook payload from Instantly

    Returns:
        {"status": "success", "event_type": "...", "message_id": "..."}

    Raises:
        HTTPException 400: Invalid payload
        HTTPException 404: Campaign not found
        HTTPException 500: Processing error
    """
    logger.info(
        f"[Webhook] Received {payload.event_type.value} "
        f"from workspace {payload.workspace_id} "
        f"for campaign {payload.campaign_name}"
    )

    try:
        # Route to appropriate handler based on event type
        result = await _route_webhook_event(payload)

        return {
            "status": "success",
            "event_type": payload.event_type.value,
            "campaign_id": payload.campaign_id,
            **result
        }

    except ValueError as e:
        # Campaign not found or invalid data
        logger.warning(f"[Webhook] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected error
        logger.error(f"[Webhook] Processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


async def _route_webhook_event(payload: InstantlyWebhookPayload) -> dict:
    """
    Route webhook event to appropriate handler

    Args:
        payload: Webhook payload

    Returns:
        Processing result dict
    """
    event_type = payload.event_type

    # Email Events - Create message records
    if event_type in [
        InstantlyEventType.EMAIL_SENT,
        InstantlyEventType.EMAIL_OPENED,
        InstantlyEventType.REPLY_RECEIVED,
        InstantlyEventType.AUTO_REPLY_RECEIVED,
        InstantlyEventType.LINK_CLICKED,
        InstantlyEventType.EMAIL_BOUNCED,
        InstantlyEventType.LEAD_UNSUBSCRIBED
    ]:
        return await _handle_email_event(payload)

    # Lead Status Events - Update lead/contact status
    elif event_type in [
        InstantlyEventType.LEAD_INTERESTED,
        InstantlyEventType.LEAD_NOT_INTERESTED,
        InstantlyEventType.LEAD_NEUTRAL,
        InstantlyEventType.LEAD_OUT_OF_OFFICE,
        InstantlyEventType.LEAD_WRONG_PERSON
    ]:
        return await _handle_lead_status_event(payload)

    # Meeting Events
    elif event_type in [
        InstantlyEventType.LEAD_MEETING_BOOKED,
        InstantlyEventType.LEAD_MEETING_COMPLETED
    ]:
        return await _handle_meeting_event(payload)

    # Account Error Events
    elif event_type == InstantlyEventType.ACCOUNT_ERROR:
        return await _handle_account_error(payload)

    # Campaign Completion
    elif event_type == InstantlyEventType.CAMPAIGN_COMPLETED:
        return await _handle_campaign_completed(payload)

    else:
        logger.warning(f"[Webhook] Unknown event type: {event_type}")
        return {"handled": False, "reason": "unknown_event_type"}


async def _handle_email_event(payload: InstantlyWebhookPayload) -> dict:
    """
    Handle email-related events

    Creates message record and updates statistics

    Args:
        payload: Webhook payload

    Returns:
        Processing result
    """
    result = await MessageService.process_webhook_event(payload)

    logger.info(
        f"[Webhook] Email event processed: {payload.event_type.value} "
        f"from {payload.email_account} to {payload.lead_email}"
    )

    return result


async def _handle_lead_status_event(payload: InstantlyWebhookPayload) -> dict:
    """
    Handle lead status change events

    Updates contact status in database

    Args:
        payload: Webhook payload

    Returns:
        Processing result
    """
    # Create message record for tracking
    result = await MessageService.process_webhook_event(payload)

    # TODO: Update contact status in contact table
    # This will be implemented when we add lead scoring/status tracking

    logger.info(
        f"[Webhook] Lead status changed: {payload.lead_email} → {payload.event_type.value}"
    )

    return {
        **result,
        "lead_status": payload.event_type.value
    }


async def _handle_meeting_event(payload: InstantlyWebhookPayload) -> dict:
    """
    Handle meeting booking events

    Args:
        payload: Webhook payload

    Returns:
        Processing result
    """
    # Create message/event record
    result = await MessageService.process_webhook_event(payload)

    # TODO: Create calendar event or notification
    # This could trigger notification to sales team

    logger.info(
        f"[Webhook] Meeting event: {payload.event_type.value} "
        f"for {payload.lead_email} at {payload.meeting_time}"
    )

    return {
        **result,
        "meeting_url": payload.meeting_url,
        "meeting_time": payload.meeting_time
    }


async def _handle_account_error(payload: InstantlyWebhookPayload) -> dict:
    """
    Handle email account error events

    Suspends email account and logs error

    Args:
        payload: Webhook payload

    Returns:
        Processing result
    """
    # Create event record
    result = await MessageService.process_webhook_event(payload)

    # Suspend email account
    if payload.email_account:
        error_handled = await EmailAccountService.handle_error(
            payload.email_account,
            payload.error_message or "Unknown account error"
        )

        if error_handled:
            logger.warning(
                f"[Webhook] Email account suspended: {payload.email_account} "
                f"due to: {payload.error_message}"
            )

    return {
        **result,
        "account_suspended": True,
        "error": payload.error_message
    }


async def _handle_campaign_completed(payload: InstantlyWebhookPayload) -> dict:
    """
    Handle campaign completion event

    Updates campaign status to completed

    Args:
        payload: Webhook payload

    Returns:
        Processing result
    """
    # Get campaign
    campaign = await CampaignService.get_campaign_by_external_id(payload.campaign_id)

    if campaign:
        # Update status to completed
        await CampaignService.update_campaign_status(
            campaign['id'],
            'completed'
        )

        logger.info(
            f"[Webhook] Campaign completed: {payload.campaign_name} "
            f"(ID: {payload.campaign_id})"
        )

        return {
            "campaign_id": str(campaign['id']),
            "status": "completed"
        }

    else:
        raise ValueError(f"Campaign {payload.campaign_id} not found")


# Health check endpoint for webhook testing
@router.get("/health", status_code=status.HTTP_200_OK)
async def webhook_health():
    """
    Webhook health check

    Use this to verify webhook endpoint is reachable

    Returns:
        {"status": "healthy", "service": "instantly_webhooks"}
    """
    return {
        "status": "healthy",
        "service": "instantly_webhooks",
        "endpoint": "/webhooks/instantly/webhook"
    }


# Test endpoint for development (accepts any JSON)
@router.post("/test", status_code=status.HTTP_200_OK)
async def webhook_test(request: Request):
    """
    Test webhook endpoint for development

    Accepts any JSON payload and logs it

    Returns:
        Echo of received payload
    """
    try:
        payload = await request.json()
        logger.info(f"[Webhook Test] Received payload: {payload}")

        return {
            "status": "received",
            "payload": payload,
            "note": "This is a test endpoint. Use /webhook for production."
        }

    except Exception as e:
        logger.error(f"[Webhook Test] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
