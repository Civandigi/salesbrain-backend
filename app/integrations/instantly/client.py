"""
Instantly.ai API v2 Client
Async HTTP client for Instantly REST API

Documentation: https://developer.instantly.ai/api/v2
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.integrations.instantly.schemas import (
    InstantlyCampaign,
    InstantlyEmailAccount,
    InstantlyWorkspace,
    InstantlyLead,
    InstantlyCampaignListResponse,
    InstantlyEmailAccountListResponse,
    InstantlyLeadListResponse,
    InstantlyErrorResponse,
)

logger = logging.getLogger(__name__)


class InstantlyAPIError(Exception):
    """Base exception for Instantly API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class InstantlyAuthenticationError(InstantlyAPIError):
    """Authentication failed (401)"""
    pass


class InstantlyRateLimitError(InstantlyAPIError):
    """Rate limit exceeded (429)"""
    pass


class InstantlyClient:
    """
    Instantly.ai API v2 Client

    Features:
    - Bearer Token Authentication
    - Automatic retries with exponential backoff
    - Comprehensive error handling
    - Async/await support

    Usage:
        client = InstantlyClient(api_key="your_api_key")
        workspace = await client.get_current_workspace()
        campaigns = await client.list_campaigns()
    """

    BASE_URL = "https://api.instantly.ai/api/v2"
    TIMEOUT = 30.0  # seconds

    def __init__(self, api_key: str, timeout: Optional[float] = None):
        """
        Initialize Instantly API Client

        Args:
            api_key: Instantly API v2 key (Bearer token)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.timeout = timeout or self.TIMEOUT
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Salesbrain/1.0"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Instantly API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/campaigns")
            params: Query parameters
            json_data: Request body (JSON)

        Returns:
            Response data as dict

        Raises:
            InstantlyAuthenticationError: Invalid API key
            InstantlyRateLimitError: Rate limit exceeded
            InstantlyAPIError: Other API errors
        """
        url = f"{self.BASE_URL}{endpoint}"

        logger.debug(f"Instantly API: {method} {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data
                )

                # Handle specific HTTP status codes
                if response.status_code == 401:
                    raise InstantlyAuthenticationError(
                        "Invalid API key or expired token",
                        status_code=401,
                        response=response.json() if response.content else None
                    )

                elif response.status_code == 429:
                    raise InstantlyRateLimitError(
                        "Rate limit exceeded. Please retry later.",
                        status_code=429,
                        response=response.json() if response.content else None
                    )

                elif response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise InstantlyAPIError(
                        f"API request failed: {error_data.get('message', 'Unknown error')}",
                        status_code=response.status_code,
                        response=error_data
                    )

                # Success
                response.raise_for_status()
                return response.json() if response.content else {}

        except httpx.TimeoutException as e:
            logger.error(f"Instantly API timeout: {e}")
            raise InstantlyAPIError(f"Request timeout after {self.timeout}s")

        except httpx.RequestError as e:
            logger.error(f"Instantly API request error: {e}")
            raise InstantlyAPIError(f"Request failed: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(InstantlyRateLimitError)
    )
    async def _request_with_retry(self, *args, **kwargs) -> Dict[str, Any]:
        """Request with automatic retry on rate limits"""
        return await self._request(*args, **kwargs)

    # ========================================
    # Workspace Endpoints
    # ========================================

    async def get_current_workspace(self) -> InstantlyWorkspace:
        """
        Get current workspace information

        Endpoint: GET /workspaces/current
        Docs: https://developer.instantly.ai/api/v2/workspace

        Returns:
            InstantlyWorkspace object
        """
        data = await self._request_with_retry("GET", "/workspaces/current")
        return InstantlyWorkspace(**data)

    # ========================================
    # Campaign Endpoints
    # ========================================

    async def list_campaigns(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> List[InstantlyCampaign]:
        """
        List all campaigns in workspace

        Endpoint: GET /campaigns
        Docs: https://developer.instantly.ai/api/v2/campaign

        Args:
            status: Filter by status ("active", "paused", "completed")
            tags: Filter by tags
            page: Page number (default: 1)
            page_size: Results per page (default: 100)

        Returns:
            List of InstantlyCampaign objects
        """
        params = {
            "page": page,
            "page_size": page_size
        }

        if status:
            params["status"] = status

        if tags:
            params["tags"] = ",".join(tags)

        data = await self._request_with_retry("GET", "/campaigns", params=params)

        # Handle both array response and paginated response
        if isinstance(data, list):
            return [InstantlyCampaign(**campaign) for campaign in data]
        elif "campaigns" in data:
            return [InstantlyCampaign(**campaign) for campaign in data["campaigns"]]
        else:
            return []

    async def get_campaign(self, campaign_id: str) -> InstantlyCampaign:
        """
        Get single campaign by ID

        Endpoint: GET /campaigns/{campaign_id}

        Args:
            campaign_id: Instantly campaign ID

        Returns:
            InstantlyCampaign object
        """
        data = await self._request_with_retry("GET", f"/campaigns/{campaign_id}")
        return InstantlyCampaign(**data)

    # ========================================
    # Email Account Endpoints
    # ========================================

    async def list_email_accounts(
        self,
        status: Optional[str] = None
    ) -> List[InstantlyEmailAccount]:
        """
        List all email accounts in workspace

        Endpoint: GET /accounts
        Docs: https://developer.instantly.ai/api/v2/email

        Args:
            status: Filter by status ("active", "paused", "warming", etc.)

        Returns:
            List of InstantlyEmailAccount objects
        """
        params = {}
        if status:
            params["status"] = status

        data = await self._request_with_retry("GET", "/accounts", params=params)

        # Handle both array response and object response
        if isinstance(data, list):
            return [InstantlyEmailAccount(**account) for account in data]
        elif "accounts" in data:
            return [InstantlyEmailAccount(**account) for account in data["accounts"]]
        else:
            return []

    async def get_email_account(self, account_id: str) -> InstantlyEmailAccount:
        """
        Get single email account by ID

        Endpoint: GET /accounts/{account_id}

        Args:
            account_id: Instantly email account ID

        Returns:
            InstantlyEmailAccount object
        """
        data = await self._request_with_retry("GET", f"/accounts/{account_id}")
        return InstantlyEmailAccount(**data)

    # ========================================
    # Lead Endpoints
    # ========================================

    async def list_leads(
        self,
        campaign_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> List[InstantlyLead]:
        """
        List leads

        Endpoint: GET /leads
        Docs: https://developer.instantly.ai/api/v2/lead

        Args:
            campaign_id: Filter by campaign
            status: Filter by status
            page: Page number
            page_size: Results per page

        Returns:
            List of InstantlyLead objects
        """
        params = {
            "page": page,
            "page_size": page_size
        }

        if campaign_id:
            params["campaign_id"] = campaign_id

        if status:
            params["status"] = status

        data = await self._request_with_retry("GET", "/leads", params=params)

        # Handle both array and paginated response
        if isinstance(data, list):
            return [InstantlyLead(**lead) for lead in data]
        elif "leads" in data:
            return [InstantlyLead(**lead) for lead in data["leads"]]
        else:
            return []

    async def get_lead(self, lead_id: str) -> InstantlyLead:
        """
        Get single lead by ID

        Endpoint: GET /leads/{lead_id}

        Args:
            lead_id: Instantly lead ID

        Returns:
            InstantlyLead object
        """
        data = await self._request_with_retry("GET", f"/leads/{lead_id}")
        return InstantlyLead(**data)

    # ========================================
    # Account Campaign Mapping
    # ========================================

    async def get_account_campaigns(self, account_id: str) -> List[InstantlyCampaign]:
        """
        Get campaigns associated with an email account

        Endpoint: GET /account-campaign-mapping
        Docs: https://developer.instantly.ai/api/v2/accountcampaignmapping

        Args:
            account_id: Email account ID

        Returns:
            List of campaigns using this email account
        """
        params = {"account_id": account_id}
        data = await self._request_with_retry("GET", "/account-campaign-mapping", params=params)

        if isinstance(data, list):
            return [InstantlyCampaign(**campaign) for campaign in data]
        elif "campaigns" in data:
            return [InstantlyCampaign(**campaign) for campaign in data["campaigns"]]
        else:
            return []

    # ========================================
    # Utility Methods
    # ========================================

    async def test_connection(self) -> bool:
        """
        Test API connection and authentication

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.get_current_workspace()
            logger.info("Instantly API connection successful")
            return True
        except InstantlyAuthenticationError:
            logger.error("Instantly API authentication failed")
            return False
        except InstantlyAPIError as e:
            logger.error(f"Instantly API connection test failed: {e}")
            return False

    async def close(self):
        """Close client session (cleanup)"""
        # httpx.AsyncClient is closed automatically in context manager
        pass
