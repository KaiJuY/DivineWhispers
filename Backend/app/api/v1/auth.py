"""
Authentication API endpoints for user registration, login, token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.utils.deps import get_db, get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenRevoke,
    LoginResponse,
    TokenResponse,
    UserResponse,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    MessageResponse,
    AuthErrorResponse,
    UserProfileUpdate
)

# Create router
router = APIRouter()
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account and return user info with authentication tokens",
    responses={
        201: {"description": "User registered successfully"},
        400: {
            "description": "Registration failed - validation error or user exists",
            "model": AuthErrorResponse
        },
        422: {"description": "Validation error"}
    }
)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    client_ip = get_client_ip(request)
    
    try:
        user, tokens = await AuthService.register_user(db, user_data, client_ip)
        user_response = UserResponse.model_validate(user)
        
        return LoginResponse(user=user_response, tokens=tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Registration error: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user with email and password, return user info and tokens",
    responses={
        200: {"description": "Login successful"},
        401: {
            "description": "Authentication failed - invalid credentials",
            "model": AuthErrorResponse
        },
        403: {
            "description": "Account is inactive",
            "model": AuthErrorResponse
        },
        422: {"description": "Validation error"}
    }
)
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    client_ip = get_client_ip(request)
    
    try:
        return await AuthService.authenticate_user(db, login_data, client_ip)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use refresh token to obtain a new access token and refresh token pair",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {
            "description": "Token refresh failed - invalid or expired token",
            "model": AuthErrorResponse
        },
        422: {"description": "Validation error"}
    }
)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    client_ip = get_client_ip(request)
    
    try:
        return await AuthService.refresh_token(db, token_data.refresh_token, client_ip)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to server error"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout user by revoking their access and refresh tokens",
    responses={
        200: {"description": "Logout successful"},
        401: {
            "description": "Logout failed - invalid token",
            "model": AuthErrorResponse
        }
    }
)
async def logout(
    request: Request,
    refresh_token: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Logout user by blacklisting tokens"""
    client_ip = get_client_ip(request)
    access_token = credentials.credentials
    
    try:
        await AuthService.logout_user(db, access_token, refresh_token, client_ip)
        return MessageResponse(message="Logout successful")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to server error"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        200: {"description": "User information retrieved"},
        401: {
            "description": "Authentication required",
            "model": AuthErrorResponse
        },
        404: {
            "description": "User not found",
            "model": AuthErrorResponse
        }
    }
)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {
            "description": "Password change failed - validation error or incorrect current password",
            "model": AuthErrorResponse
        },
        401: {
            "description": "Authentication required",
            "model": AuthErrorResponse
        },
        404: {
            "description": "User not found",
            "model": AuthErrorResponse
        }
    }
)
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    client_ip = get_client_ip(request)
    
    try:
        await AuthService.change_password(db, current_user.user_id, password_data, client_ip)
        return MessageResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed due to server error"
        )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Request a password reset token (placeholder endpoint)",
    responses={
        200: {"description": "Password reset email sent (if user exists)"},
        422: {"description": "Validation error"}
    }
)
async def forgot_password(
    reset_data: PasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset (placeholder implementation)"""
    # TODO: Implement email sending functionality
    # For security reasons, always return success even if user doesn't exist
    return MessageResponse(
        message="If an account with this email exists, a password reset link has been sent"
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
    description="Reset password using a reset token (placeholder endpoint)",
    responses={
        200: {"description": "Password reset successful"},
        400: {
            "description": "Password reset failed - invalid token or validation error",
            "model": AuthErrorResponse
        },
        422: {"description": "Validation error"}
    }
)
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using reset token (placeholder implementation)"""
    # TODO: Implement password reset token verification and password update
    return MessageResponse(message="Password reset successful")


@router.post(
    "/verify-token",
    response_model=UserResponse,
    summary="Verify token validity",
    description="Verify if the provided access token is valid and return user info",
    responses={
        200: {"description": "Token is valid"},
        401: {
            "description": "Token is invalid or expired",
            "model": AuthErrorResponse
        }
    }
)
async def verify_token(
    current_user = Depends(get_current_user)
):
    """Verify token validity and return user info"""
    return UserResponse.model_validate(current_user)


# Admin endpoints (require admin role)
@router.post(
    "/admin/cleanup-tokens",
    response_model=MessageResponse,
    summary="Clean up expired tokens",
    description="Remove expired tokens from blacklist (admin only)",
    responses={
        200: {"description": "Token cleanup completed"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"}
    }
)
async def cleanup_expired_tokens(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Clean up expired blacklisted tokens (admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        cleaned_count = await AuthService.cleanup_expired_tokens(db)
        return MessageResponse(
            message=f"Cleaned up {cleaned_count} expired tokens"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token cleanup failed due to server error"
        )


# Profile Management Endpoints

@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get user profile",
    description="Get current user's profile information",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Authentication required"}
    }
)
async def get_user_profile(
    current_user = Depends(get_current_user)
):
    """Get user profile information"""
    return UserResponse.model_validate(current_user)


@router.put(
    "/profile", 
    response_model=UserResponse,
    summary="Update user profile",
    description="Update current user's profile information",
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Authentication required"},
        400: {"description": "Invalid profile data"}
    }
)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update user profile information"""
    try:
        updated_user = await AuthService.update_user_profile(
            user_id=current_user.user_id,
            profile_data=profile_update,
            db=db
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile update failed"
            )
        
        return UserResponse.model_validate(updated_user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed due to server error"
        )


@router.get(
    "/profile/reports",
    summary="Get user fortune reports", 
    description="Get current user's fortune consultation history and reports",
    responses={
        200: {"description": "Reports retrieved successfully"},
        401: {"description": "Authentication required"}
    }
)
async def get_user_reports(
    limit: int = 10,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """Get user's fortune consultation reports"""
    # This endpoint integrates with the fortune history
    from app.services.job_processor import job_processor
    
    try:
        jobs = await job_processor.get_user_jobs(
            user_id=str(current_user.user_id),
            limit=limit,
            offset=offset
        )
        
        reports = []
        for job_data in jobs:
            if job_data.get("status") == "completed" and job_data.get("result_data"):
                reports.append({
                    "id": job_data["id"],
                    "created_at": job_data["created_at"],
                    "type": job_data.get("job_type", "fortune"),
                    "title": f"Fortune Reading #{job_data['id'][:8]}",
                    "summary": job_data.get("result_data", {}).get("interpretation", "")[:200] + "...",
                    "status": job_data["status"]
                })
        
        return {
            "reports": reports,
            "total_count": len(reports),
            "has_more": len(jobs) == limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )