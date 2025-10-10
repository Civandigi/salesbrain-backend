"""
Health check endpoints
"""

from fastapi import APIRouter

from app.core.db import check_global_kb_health, check_tenant_db_health


router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint

    Returns:
        Health status with database connectivity
    """
    global_kb_ok = await check_global_kb_health()
    tenant_db_ok = await check_tenant_db_health()

    all_ok = global_kb_ok and tenant_db_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "databases": {
            "global_kb": "connected" if global_kb_ok else "disconnected",
            "tenant": "connected" if tenant_db_ok else "disconnected"
        }
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe

    Returns:
        200 if ready, 503 if not ready
    """
    global_kb_ok = await check_global_kb_health()
    tenant_db_ok = await check_tenant_db_health()

    if global_kb_ok and tenant_db_ok:
        return {"status": "ready"}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Not ready")


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe

    Returns:
        Always 200 (application is alive)
    """
    return {"status": "alive"}
