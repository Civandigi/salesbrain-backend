"""
Authentication endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta

from app.core.config import settings
from app.core.db import get_tenant_db_conn
from app.core.security import verify_password, create_access_token
from app.core.auth import get_current_user
from app.models.auth import LoginRequest, LoginResponse, TokenData


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Login endpoint

    Args:
        credentials: Email and password

    Returns:
        JWT access token and user info

    Raises:
        401: Invalid credentials
    """
    # Query user from database
    async with get_tenant_db_conn("00000000-0000-0000-0000-000000000000") as conn:
        # Note: Using dummy org_id for login query (RLS not applicable here)
        # We'll get the real org_id from the user record
        user_record = await conn.fetchrow(
            """
            SELECT
                id,
                organization_id,
                email,
                password_hash,
                role,
                status,
                first_name,
                last_name
            FROM "user"
            WHERE email = $1
            """,
            credentials.email
        )

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user status
    if user_record["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user_record['status']}"
        )

    # Create JWT token
    token_data = {
        "user_id": str(user_record["id"]),
        "organization_id": str(user_record["organization_id"]),
        "role": user_record["role"],
        "email": user_record["email"]
    }

    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user_record["id"]),
        organization_id=str(user_record["organization_id"]),
        role=user_record["role"],
        email=user_record["email"],
        first_name=user_record["first_name"],
        last_name=user_record["last_name"]
    )


@router.get("/me", response_model=TokenData)
async def get_current_user_info(user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user info

    Requires:
        Authorization: Bearer <token>

    Returns:
        Current user data from JWT token
    """
    return user


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal)

    Note: JWT tokens are stateless, so logout is handled client-side
          by removing the token from storage
    """
    return {"message": "Logged out successfully"}
