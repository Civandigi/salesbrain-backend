"""
Instantly.ai Pydantic Schemas
Data models for API responses and webhook payloads
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InstantlyEventType(str, Enum):
    """
    Instantly Webhook Event Types
    Based on: https://developer.instantly.ai/webhook-events
    """
    # Email Events
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    REPLY_RECEIVED = "reply_received"
    AUTO_REPLY_RECEIVED = "auto_reply_received"
    LINK_CLICKED = "link_clicked"
    EMAIL_BOUNCED = "email_bounced"
    LEAD_UNSUBSCRIBED = "lead_unsubscribed"
    ACCOUNT_ERROR = "account_error"
    CAMPAIGN_COMPLETED = "campaign_completed"

    # Lead Status Events
    LEAD_NEUTRAL = "lead_neutral"
    LEAD_INTERESTED = "lead_interested"
    LEAD_NOT_INTERESTED = "lead_not_interested"

    # Meeting Events
    LEAD_MEETING_BOOKED = "lead_meeting_booked"
    LEAD_MEETING_COMPLETED = "lead_meeting_completed"

    # Other Lead Events
    LEAD_CLOSED = "lead_closed"
    LEAD_OUT_OF_OFFICE = "lead_out_of_office"
    LEAD_WRONG_PERSON = "lead_wrong_person"


class InstantlyWebhookPayload(BaseModel):
    """
    Base Webhook Payload from Instantly

    All webhooks contain these base fields.
    Additional fields depend on event_type.
    """
    timestamp: str  # ISO 8601 format: "2025-10-10T12:00:00Z"
    event_type: InstantlyEventType
    workspace_id: str
    campaign_id: str
    campaign_name: str

    # Optional fields (present in most events)
    lead_email: Optional[str] = None
    email_account: Optional[str] = None  # Sending email address
    unibox_url: Optional[str] = None  # URL to conversation in Instantly

    # Email-specific fields
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None

    # Tracking fields
    open_count: Optional[int] = None
    click_count: Optional[int] = None

    # Error/Bounce fields
    bounce_type: Optional[str] = None  # "hard", "soft", "complaint"
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Lead fields
    lead_id: Optional[str] = None
    lead_status: Optional[str] = None

    # Meeting fields (for meeting events)
    meeting_url: Optional[str] = None
    meeting_time: Optional[str] = None

    # Raw data storage (for any additional fields)
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        extra = "allow"  # Allow additional fields from Instantly


class InstantlyCampaign(BaseModel):
    """
    Campaign from Instantly API
    Response from: GET /api/v2/campaigns
    """
    id: str
    name: str
    status: str  # "active", "paused", "completed"

    # Workspace association
    workspace_id: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Campaign settings
    daily_limit: Optional[int] = None
    schedule_enabled: Optional[bool] = None

    # Statistics
    total_leads: Optional[int] = 0
    emails_sent: Optional[int] = 0
    emails_opened: Optional[int] = 0
    replies_received: Optional[int] = 0

    # Tags (for filtering)
    tags: Optional[List[str]] = Field(default_factory=list)

    class Config:
        extra = "allow"


class InstantlyEmailAccount(BaseModel):
    """
    Email Account from Instantly API
    Response from: GET /api/v2/accounts
    """
    id: str
    email: str
    display_name: Optional[str] = None

    # Status
    status: str  # "active", "paused", "warming", "suspended", "bounced"

    # Settings
    daily_limit: Optional[int] = 50
    warmup_enabled: Optional[bool] = True

    # Statistics
    emails_sent_today: Optional[int] = 0
    emails_sent_total: Optional[int] = 0

    # Health metrics
    bounce_rate: Optional[float] = None
    spam_rate: Optional[float] = None

    # Provider info
    provider: Optional[str] = None  # "gmail", "outlook", "smtp"

    # Metadata
    created_at: Optional[datetime] = None
    last_email_sent_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class InstantlyWorkspace(BaseModel):
    """
    Workspace Info from Instantly API
    Response from: GET /api/v2/workspaces/current
    """
    id: str
    name: str

    # Plan info
    plan: Optional[str] = None  # "free", "growth", "hypergrowth", "enterprise"

    # Limits
    monthly_email_limit: Optional[int] = None
    email_accounts_limit: Optional[int] = None

    # Usage
    emails_sent_this_month: Optional[int] = 0
    email_accounts_count: Optional[int] = 0

    # Metadata
    created_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class InstantlyLead(BaseModel):
    """
    Lead from Instantly API
    Response from: GET /api/v2/leads
    """
    id: str
    email: str

    # Personal info
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None

    # Lead status
    status: str  # "neutral", "interested", "not_interested", "closed", "out_of_office", "wrong_person"

    # Campaign association
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None

    # Email account used
    email_account: Optional[str] = None

    # Engagement metrics
    emails_sent: Optional[int] = 0
    emails_opened: Optional[int] = 0
    links_clicked: Optional[int] = 0
    replies_received: Optional[int] = 0

    # Custom fields
    custom_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = "allow"


# Response wrappers for API endpoints

class InstantlyCampaignListResponse(BaseModel):
    """Response wrapper for campaign list"""
    campaigns: List[InstantlyCampaign]
    total: int
    page: Optional[int] = 1
    page_size: Optional[int] = 100


class InstantlyEmailAccountListResponse(BaseModel):
    """Response wrapper for email account list"""
    accounts: List[InstantlyEmailAccount]
    total: int


class InstantlyLeadListResponse(BaseModel):
    """Response wrapper for lead list"""
    leads: List[InstantlyLead]
    total: int
    page: Optional[int] = 1
    page_size: Optional[int] = 100


# Error response

class InstantlyErrorResponse(BaseModel):
    """Error response from Instantly API"""
    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
