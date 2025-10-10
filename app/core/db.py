"""
Database connection pools for Global-KB and Tenant-DB
Uses asyncpg for async PostgreSQL connections
"""

import asyncpg
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from app.core.config import settings


# Connection pools (initialized on startup)
global_kb_pool: asyncpg.Pool = None
tenant_db_pool: asyncpg.Pool = None


async def init_db_pools():
    """
    Initialize both database connection pools
    Called on application startup
    """
    global global_kb_pool, tenant_db_pool

    # Global-KB pool
    global_kb_pool = await asyncpg.create_pool(
        settings.database_global_url,
        min_size=2,
        max_size=10,
        command_timeout=60
    )

    # Tenant-DB pool
    tenant_db_pool = await asyncpg.create_pool(
        settings.database_tenant_url,
        min_size=5,
        max_size=20,
        command_timeout=60
    )

    print("[OK] Database pools initialized")


async def close_db_pools():
    """
    Close both database connection pools
    Called on application shutdown
    """
    global global_kb_pool, tenant_db_pool

    if global_kb_pool:
        await global_kb_pool.close()
        print("[OK] Global-KB pool closed")

    if tenant_db_pool:
        await tenant_db_pool.close()
        print("[OK] Tenant-DB pool closed")


@asynccontextmanager
async def get_global_kb_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get connection from Global-KB pool

    Usage:
        async with get_global_kb_conn() as conn:
            result = await conn.fetch("SELECT * FROM company LIMIT 10")
    """
    async with global_kb_pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_tenant_db_conn(org_id: str) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get connection from Tenant-DB pool with RLS context

    Args:
        org_id: Organization UUID for Row-Level Security

    Usage:
        async with get_tenant_db_conn(org_id) as conn:
            result = await conn.fetch("SELECT * FROM contact")
    """
    async with tenant_db_pool.acquire() as conn:
        # Set RLS context
        await conn.execute(f"SET app.current_org_id = '{org_id}'")

        try:
            yield conn
        finally:
            # Reset RLS context
            await conn.execute("RESET app.current_org_id")


async def check_global_kb_health() -> bool:
    """Check Global-KB connection health"""
    try:
        async with get_global_kb_conn() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        print(f"[ERROR] Global-KB health check failed: {e}")
        return False


async def check_tenant_db_health() -> bool:
    """Check Tenant-DB connection health"""
    try:
        # Use test org ID for health check (no RLS context needed)
        async with tenant_db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        print(f"[ERROR] Tenant-DB health check failed: {e}")
        return False
