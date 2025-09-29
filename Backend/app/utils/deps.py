"""
Dependency injection utilities for FastAPI
"""

from typing import Optional, AsyncGenerator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_database_session
from app.core.security import verify_token_with_blacklist
from app.models.user import User, UserRole
from app.core.permissions import Permission

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency
    """
    async for session in get_database_session():
        yield session


async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Extract and verify JWT token from Authorization header with blacklist check
    Returns the token payload
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = await verify_token_with_blacklist(db, token, "access")
    
    return payload


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(get_current_user_token)
) -> User:
    """
    Get current user from database based on token payload
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )
    
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Refresh the user object to ensure all attributes are loaded within the current session
    await db.refresh(user)

    # Synchronize legacy user.points_balance with wallet balance for consistency
    # Temporarily completely disabled to prevent authentication failures due to greenlet context issues
    # TODO: Fix the async context mixing in WalletService and re-enable
    pass  # Disabled wallet sync to isolate greenlet issue
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (already checked in get_current_user)
    """
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current admin user
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def check_user_points(
    current_user: User = Depends(get_current_user),
    required_points: int = 10
) -> User:
    """
    Check if user has enough points for an operation
    """
    if not current_user.has_sufficient_points(required_points):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient points. Required: {required_points}, Available: {current_user.points_balance}"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None
    Useful for endpoints that can work with or without authentication
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = await verify_token_with_blacklist(db, token, "access")
        
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        user_id = int(user_id)
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if user and user.is_active():
            return user
        return None
        
    except (HTTPException, ValueError):
        return None


class CommonQueryParams:
    """Common query parameters for list endpoints"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Max 1000 items per request
        self.search = search
        self.sort_by = sort_by
        self.sort_desc = sort_desc


def get_query_params() -> CommonQueryParams:
    """Dependency for common query parameters"""
    return CommonQueryParams


# Rate limiting dependency (placeholder)
async def rate_limit_dependency():
    """
    Rate limiting dependency
    TODO: Implement proper rate limiting with Redis or in-memory cache
    """
    # For now, this is a placeholder
    # In production, you'd implement actual rate limiting here
    pass


# RBAC Enhanced Dependencies

async def get_current_admin_or_moderator(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user if they are admin or moderator
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator privileges required"
        )
    return current_user


async def get_current_moderator_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current moderator user (moderator or admin)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required"
        )
    return current_user


async def verify_user_access(
    target_user_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that current user can access target user's data
    (either owns the data or has admin privileges)
    """
    if current_user.user_id != target_user_id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own data"
        )
    return current_user


async def verify_resource_ownership(
    resource_owner_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that current user owns the resource or has sufficient privileges
    """
    # Import here to avoid circular imports
    from app.services.rbac_service import RBACService
    from app.utils.deps import get_db
    
    # Allow access if user owns the resource
    if current_user.user_id == resource_owner_id:
        return current_user
    
    # Check if user has permission to access any user's resources
    # This is a simplified check - in practice, you'd specify the exact permission needed
    if current_user.is_admin():
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Insufficient permissions"
    )


# Enhanced point checking with RBAC
async def check_user_points_or_admin(
    required_points: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Check if user has enough points or is an admin (admins bypass point requirements)
    """
    if current_user.is_admin():
        return current_user
    
    if not current_user.has_sufficient_points(required_points):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient points. Required: {required_points}, Available: {current_user.points_balance}"
        )
    return current_user


def require_role_dependency(required_role: UserRole):
    """
    Factory function to create role-based dependencies
    
    Usage:
        require_admin = require_role_dependency(UserRole.ADMIN)
        
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_admin)):
            return {"message": "Admin access granted"}
    """
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        from app.services.rbac_service import RBACService
        
        if not await RBACService.has_role(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {required_role.value} or higher"
            )
        return current_user
    
    return _check_role


def require_permission_dependency(required_permission: Permission):
    """
    Factory function to create permission-based dependencies
    
    Usage:
        require_user_mgmt = require_permission_dependency(Permission.VIEW_ALL_USERS)
        
        @router.get("/users")
        async def list_users(user: User = Depends(require_user_mgmt)):
            return {"users": []}
    """
    async def _check_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        from app.services.rbac_service import RBACService
        
        if not await RBACService.has_permission(current_user, required_permission, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {required_permission.value}"
            )
        return current_user
    
    return _check_permission


# Pre-configured dependency instances for common roles
require_admin_role = require_role_dependency(UserRole.ADMIN)
require_moderator_role = require_role_dependency(UserRole.MODERATOR)

# Pre-configured dependency instances for common permissions
require_view_all_users = require_permission_dependency(Permission.VIEW_ALL_USERS)
require_user_management = require_permission_dependency(Permission.SUSPEND_USER)
require_system_access = require_permission_dependency(Permission.VIEW_SYSTEM_LOGS)
require_financial_access = require_permission_dependency(Permission.VIEW_ALL_WALLETS)
