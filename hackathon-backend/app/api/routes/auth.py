"""
Authentication API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse
)
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user (dummy - no password required)."""
    try:
        result = await auth_service.register(
            email=request.email,
            name=request.name
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user (dummy - no password verification)."""
    try:
        result = await auth_service.login(email=request.email)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout")
async def logout():
    """Logout (dummy endpoint - client should remove token)."""
    return {"message": "ログアウトしました"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current authenticated user."""
    user = await auth_service.get_current_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    return user


@router.get("/check")
async def check_auth(
    user_id: int = Depends(get_current_user_id)
):
    """Check if user is authenticated."""
    return {"authenticated": True, "user_id": user_id}

