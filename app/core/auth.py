"""
Authentication dependencies and middleware
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.security import decode_access_token
from app.models.auth import TokenData


# HTTP Bearer scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract required fields
    user_id = payload.get("user_id")
    organization_id = payload.get("organization_id")
    role = payload.get("role")
    email = payload.get("email")

    if not all([user_id, organization_id, role, email]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenData(
        user_id=user_id,
        organization_id=organization_id,
        role=role,
        email=email
    )


async def require_role(required_role: str, user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Require specific role for endpoint access

    Usage:
        @app.get("/admin")
        async def admin_only(user: TokenData = Depends(lambda: require_role("admin"))):
            return {"message": "Admin access"}
    """
    if user.role not in [required_role, "sb_admin", "sb_operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {required_role}"
        )

    return user


async def require_sb_admin(user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Require Salesbrain admin access

    Usage:
        @app.post("/admin/create-org")
        async def create_org(user: TokenData = Depends(require_sb_admin)):
            return {"message": "Creating organization"}
    """
    if user.role not in ["sb_admin", "sb_operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Salesbrain admin access required"
        )

    return user
