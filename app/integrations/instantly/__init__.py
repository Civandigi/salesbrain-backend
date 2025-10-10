"""
Instantly.ai Integration
API Client, Webhooks, and Data Synchronization
"""

from .client import InstantlyClient
from .schemas import (
    InstantlyEventType,
    InstantlyWebhookPayload,
    InstantlyCampaign,
    InstantlyEmailAccount,
    InstantlyWorkspace
)

__all__ = [
    "InstantlyClient",
    "InstantlyEventType",
    "InstantlyWebhookPayload",
    "InstantlyCampaign",
    "InstantlyEmailAccount",
    "InstantlyWorkspace",
]
