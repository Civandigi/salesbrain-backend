"""
Instantly API Explorer
Discover all available API endpoints and features for v1 and v2
"""

import asyncio
import httpx
from app.core.config import settings

# API Keys
API_V1_KEY = "_k3rc_FPx5X-7tdJuCZ30nMnckNHC"
API_V2_KEY = settings.instantly_api_key

# Base URLs
BASE_V1 = "https://api.instantly.ai/api/v1"
BASE_V2 = "https://api.instantly.ai/api/v2"


async def explore_v2_api():
    """Explore API v2 endpoints"""
    print("\n" + "=" * 80)
    print("INSTANTLY API V2 EXPLORATION")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {API_V2_KEY}"}

        # Known v2 endpoints from our implementation
        endpoints = [
            ("GET", "/workspaces/current", "Get current workspace info"),
            ("GET", "/campaigns", "List all campaigns"),
            ("GET", "/accounts", "List email accounts"),
            ("GET", "/leads", "List leads"),
            ("POST", "/leads", "Add new lead"),
            ("DELETE", "/leads/{id}", "Delete lead"),
            ("GET", "/analytics/campaign/{id}", "Campaign analytics"),
            ("GET", "/analytics/account/{id}", "Account analytics"),
            ("POST", "/campaigns", "Create campaign"),
            ("PUT", "/campaigns/{id}", "Update campaign"),
            ("DELETE", "/campaigns/{id}", "Delete campaign"),
            ("POST", "/campaigns/{id}/start", "Start campaign"),
            ("POST", "/campaigns/{id}/pause", "Pause campaign"),
            ("GET", "/webhooks", "List webhooks"),
            ("POST", "/webhooks", "Create webhook"),
            ("DELETE", "/webhooks/{id}", "Delete webhook"),
        ]

        print("\nKNOWN API V2 ENDPOINTS:\n")
        for method, path, description in endpoints:
            print(f"  [{method:6}] {path:40} - {description}")

        # Test some endpoints
        print("\n" + "-" * 80)
        print("TESTING ENDPOINTS:")
        print("-" * 80 + "\n")

        test_endpoints = [
            ("GET", "/workspaces/current"),
            ("GET", "/campaigns"),
            ("GET", "/accounts"),
            ("GET", "/leads?limit=5"),
        ]

        for method, path in test_endpoints:
            url = f"{BASE_V2}{path}"
            print(f"\n[{method}] {path}")
            print(f"URL: {url}")

            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"Response Type: {type(data).__name__}")

                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        # Show sample data structure
                        for key, value in list(data.items())[:3]:
                            if isinstance(value, (str, int, bool, type(None))):
                                print(f"  - {key}: {value}")
                            elif isinstance(value, list):
                                print(f"  - {key}: [{len(value)} items]")
                            elif isinstance(value, dict):
                                print(f"  - {key}: {{{', '.join(list(value.keys())[:3])}...}}")
                    elif isinstance(data, list):
                        print(f"Count: {len(data)} items")
                        if data:
                            print(f"Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                else:
                    print(f"Error: {response.text[:200]}")

            except Exception as e:
                print(f"ERROR: {str(e)[:200]}")


async def explore_v1_api():
    """Explore API v1 endpoints"""
    print("\n\n" + "=" * 80)
    print("INSTANTLY API V1 EXPLORATION")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Known v1 endpoints (common patterns)
        endpoints = [
            ("GET", "/campaign/list", {"api_key": API_V1_KEY}, "List campaigns"),
            ("GET", "/account/list", {"api_key": API_V1_KEY}, "List email accounts"),
            ("POST", "/lead/add", {"api_key": API_V1_KEY}, "Add lead to campaign"),
            ("POST", "/lead/delete", {"api_key": API_V1_KEY}, "Delete lead"),
            ("GET", "/lead/list", {"api_key": API_V1_KEY}, "List leads"),
            ("GET", "/campaign/summary", {"api_key": API_V1_KEY}, "Campaign summary/stats"),
        ]

        print("\nKNOWN API V1 ENDPOINTS:\n")
        for method, path, params, description in endpoints:
            print(f"  [{method:6}] {path:30} - {description}")

        # Test endpoints
        print("\n" + "-" * 80)
        print("TESTING ENDPOINTS:")
        print("-" * 80 + "\n")

        for method, path, params, description in endpoints[:4]:  # Test first 4
            url = f"{BASE_V1}{path}"
            print(f"\n[{method}] {path} - {description}")
            print(f"URL: {url}")

            try:
                if method == "GET":
                    response = await client.get(url, params=params)
                else:
                    response = await client.post(url, json=params)

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"Response Type: {type(data).__name__}")

                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"Count: {len(data)} items")
                        if data and isinstance(data[0], dict):
                            print(f"Sample keys: {list(data[0].keys())}")
                else:
                    print(f"Error: {response.text[:200]}")

            except Exception as e:
                print(f"ERROR: {str(e)[:200]}")


async def compare_features():
    """Compare v1 vs v2 features"""
    print("\n\n" + "=" * 80)
    print("API V1 vs V2 COMPARISON")
    print("=" * 80)

    print("""
API V2 ADVANTAGES:
- Bearer token authentication (more secure)
- RESTful design (better standards)
- Double the endpoints of v1
- Better error handling
- Webhook support built-in
- Real-time event notifications
- Campaign analytics endpoints
- Account analytics endpoints

API V1 FEATURES:
- Simple API key authentication
- Basic CRUD operations
- Campaign management
- Lead management
- Email account management
- Being deprecated in 2025

RECOMMENDATION:
Use API V2 for all new development. V1 will be deprecated.

INSTANTLY AGENTS:
The API documentation doesn't expose "Instantly Agents" directly via API.
This appears to be a UI/dashboard feature for AI-powered email assistance.
However, we can leverage:
- Campaign automation via API
- Lead scoring and tracking
- Email sequence management
- Analytics for optimization

For Salesbrain, we should:
1. Use API v2 exclusively
2. Build on top of Instantly's campaign management
3. Add our own intelligence layer
4. Provide better analytics/dashboard
5. Multi-customer workspace management
""")


async def main():
    """Main exploration function"""

    print("\n" + "=" * 80)
    print("INSTANTLY.AI API EXPLORER")
    print("=" * 80)
    print(f"\nAPI v1 Key: {API_V1_KEY[:20]}...")
    print(f"API v2 Key: {API_V2_KEY[:20]}...")

    # Explore both APIs
    await explore_v2_api()
    await explore_v1_api()
    await compare_features()

    print("\n" + "=" * 80)
    print("EXPLORATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
