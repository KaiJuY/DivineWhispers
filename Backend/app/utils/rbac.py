"""
RBAC (Role-Based Access Control) utilities and decorators for FastAPI

This module provides decorators and dependency functions for protecting API endpoints
with role and permission-based access control.
"""

from functools import wraps
from typing import List, Optional, Callable, Any, Union
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.permissions import Permission
from app.services.rbac_service import RBACService
from app.utils.deps import get_current_user, get_db


class RBACDependency:
    """Base class for RBAC dependencies"""
    
    def __init__(self, log_access: bool = True):
        self.log_access = log_access


class RequirePermission(RBACDependency):
    """
    Dependency to require a specific permission for endpoint access.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: User = Depends(RequirePermission(Permission.VIEW_SYSTEM_LOGS))
        ):
            return {"message": "Admin access granted"}
    """
    
    def __init__(
        self,
        permission: Permission,
        log_access: bool = True,
        allow_owner: bool = False,
        resource_owner_key: Optional[str] = None
    ):
        super().__init__(log_access)
        self.permission = permission
        self.allow_owner = allow_owner
        self.resource_owner_key = resource_owner_key
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        return self._check_permission(current_user, db)
    
    async def _check_permission(self, user: User, db: AsyncSession) -> User:
        """Check if user has the required permission"""
        has_perm = await RBACService.has_permission(user, self.permission, db)
        
        if self.log_access:
            await RBACService.log_permission_check(
                user=user,
                permission=self.permission,
                granted=has_perm,
                db=db
            )
        
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {self.permission.value}"
            )
        
        return user


class RequireAnyPermission(RBACDependency):
    """
    Dependency to require any of the specified permissions for endpoint access.
    
    Usage:
        @router.get("/moderate-content")
        async def moderate_endpoint(
            user: User = Depends(RequireAnyPermission([
                Permission.MODERATE_USER_CONTENT,
                Permission.MODERATE_FORTUNE_CONTENT
            ]))
        ):
            return {"message": "Moderation access granted"}
    """
    
    def __init__(
        self,
        permissions: List[Permission],
        log_access: bool = True
    ):
        super().__init__(log_access)
        self.permissions = permissions
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        return self._check_permissions(current_user, db)
    
    async def _check_permissions(self, user: User, db: AsyncSession) -> User:
        """Check if user has any of the required permissions"""
        has_any_perm = await RBACService.has_any_permission(user, self.permissions, db)
        
        if self.log_access:
            for permission in self.permissions:
                has_perm = await RBACService.has_permission(user, permission, db)
                if has_perm:
                    await RBACService.log_permission_check(
                        user=user,
                        permission=permission,
                        granted=True,
                        db=db
                    )
                    break
        
        if not has_any_perm:
            permission_names = [p.value for p in self.permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(permission_names)}"
            )
        
        return user


class RequireAllPermissions(RBACDependency):
    """
    Dependency to require all of the specified permissions for endpoint access.
    
    Usage:
        @router.delete("/critical-operation")
        async def critical_endpoint(
            user: User = Depends(RequireAllPermissions([
                Permission.SYSTEM_MAINTENANCE,
                Permission.DELETE_AUDIT_LOGS
            ]))
        ):
            return {"message": "Critical operation access granted"}
    """
    
    def __init__(
        self,
        permissions: List[Permission],
        log_access: bool = True
    ):
        super().__init__(log_access)
        self.permissions = permissions
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        return self._check_permissions(current_user, db)
    
    async def _check_permissions(self, user: User, db: AsyncSession) -> User:
        """Check if user has all of the required permissions"""
        has_all_perms = await RBACService.has_all_permissions(user, self.permissions, db)
        
        if self.log_access:
            for permission in self.permissions:
                has_perm = await RBACService.has_permission(user, permission, db)
                await RBACService.log_permission_check(
                    user=user,
                    permission=permission,
                    granted=has_perm,
                    db=db
                )
        
        if not has_all_perms:
            permission_names = [p.value for p in self.permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of these permissions required: {', '.join(permission_names)}"
            )
        
        return user


class RequireRole(RBACDependency):
    """
    Dependency to require a specific role (or higher in hierarchy) for endpoint access.
    
    Usage:
        @router.get("/admin-dashboard")
        async def admin_dashboard(
            user: User = Depends(RequireRole(UserRole.ADMIN))
        ):
            return {"message": "Admin dashboard"}
    """
    
    def __init__(
        self,
        role: UserRole,
        log_access: bool = True
    ):
        super().__init__(log_access)
        self.role = role
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        return self._check_role(current_user, db)
    
    async def _check_role(self, user: User, db: AsyncSession) -> User:
        """Check if user has the required role"""
        has_role = await RBACService.has_role(user, self.role)
        
        if self.log_access and not has_role:
            await RBACService.log_permission_check(
                user=user,
                permission=Permission.USE_FORTUNE_SERVICE,  # Dummy permission for logging
                granted=False,
                resource_type="role",
                resource_id=self.role.value,
                db=db
            )
        
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {self.role.value} or higher"
            )
        
        return user


class ResourceOwnerOrPermission(RBACDependency):
    """
    Dependency that allows access if user owns the resource OR has a specific permission.
    
    This is useful for endpoints where users can access their own data,
    but admins/moderators can access anyone's data.
    
    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            user: User = Depends(ResourceOwnerOrPermission(
                permission=Permission.VIEW_ALL_USERS,
                resource_owner_id_param="user_id"
            ))
        ):
            return {"user_id": user_id}
    """
    
    def __init__(
        self,
        permission: Permission,
        resource_owner_id_param: Optional[str] = None,
        log_access: bool = True
    ):
        super().__init__(log_access)
        self.permission = permission
        self.resource_owner_id_param = resource_owner_id_param
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        **kwargs
    ) -> User:
        # Extract resource owner ID from path parameters if specified
        resource_owner_id = None
        if self.resource_owner_id_param and self.resource_owner_id_param in kwargs:
            resource_owner_id = kwargs[self.resource_owner_id_param]
        
        return self._check_access(current_user, db, resource_owner_id)
    
    async def _check_access(
        self,
        user: User,
        db: AsyncSession,
        resource_owner_id: Optional[int]
    ) -> User:
        """Check if user can access the resource"""
        can_access = await RBACService.can_access_resource(
            user=user,
            resource_owner_id=resource_owner_id,
            required_permission=self.permission,
            allow_owner=True
        )
        
        if self.log_access:
            await RBACService.log_permission_check(
                user=user,
                permission=self.permission,
                granted=can_access,
                resource_type="resource_access",
                resource_id=str(resource_owner_id) if resource_owner_id else None,
                db=db
            )
        
        if not can_access:
            if resource_owner_id == user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only access your own resources"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {self.permission.value}"
                )
        
        return user


# Convenience functions for common permission checks

def require_admin() -> Callable:
    """Convenience function to require admin role"""
    return RequireRole(UserRole.ADMIN)


def require_moderator() -> Callable:
    """Convenience function to require moderator role or higher"""
    return RequireRole(UserRole.MODERATOR)


def require_user_management() -> Callable:
    """Convenience function to require user management permissions"""
    return RequireAnyPermission([
        Permission.VIEW_ALL_USERS,
        Permission.SUSPEND_USER,
        Permission.MODIFY_USER_ROLES
    ])


def require_financial_access() -> Callable:
    """Convenience function to require financial management permissions"""
    return RequireAnyPermission([
        Permission.VIEW_ALL_WALLETS,
        Permission.MANAGE_ALL_TRANSACTIONS,
        Permission.REFUND_POINTS
    ])


def require_system_access() -> Callable:
    """Convenience function to require system management permissions"""
    return RequireAnyPermission([
        Permission.VIEW_SYSTEM_LOGS,
        Permission.SYSTEM_MAINTENANCE,
        Permission.VIEW_SYSTEM_METRICS
    ])


# Decorator functions for additional functionality

def log_access(
    permission: Optional[Permission] = None,
    resource_type: Optional[str] = None
):
    """
    Decorator to log access to endpoints.
    
    Usage:
        @log_access(Permission.VIEW_SYSTEM_LOGS, "system_logs")
        @router.get("/system/logs")
        async def get_system_logs(user: User = Depends(get_current_user)):
            return {"logs": []}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to extract user and db from function parameters
            user = None
            db = None
            
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                elif isinstance(arg, AsyncSession):
                    db = arg
            
            # Also check kwargs
            if 'user' in kwargs:
                user = kwargs['user']
            if 'db' in kwargs:
                db = kwargs['db']
            if 'current_user' in kwargs:
                user = kwargs['current_user']
            
            # Log the access if we have the required parameters
            if user and db and permission:
                await RBACService.log_permission_check(
                    user=user,
                    permission=permission,
                    granted=True,  # If we reach here, access was granted
                    resource_type=resource_type,
                    db=db
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Function to create custom resource access dependencies

def create_resource_access_dependency(
    permission: Permission,
    resource_owner_field: str = "user_id",
    allow_self_access: bool = True
) -> type:
    """
    Factory function to create custom resource access dependencies.
    
    Args:
        permission: Permission required for access
        resource_owner_field: Field name that contains the resource owner ID
        allow_self_access: Whether users can access their own resources
        
    Returns:
        Custom dependency class
    """
    
    class CustomResourceAccess(RBACDependency):
        def __init__(self, log_access: bool = True):
            super().__init__(log_access)
        
        def __call__(
            self,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            **kwargs
        ) -> User:
            resource_owner_id = kwargs.get(resource_owner_field)
            return self._check_access(current_user, db, resource_owner_id)
        
        async def _check_access(
            self,
            user: User,
            db: AsyncSession,
            resource_owner_id: Optional[int]
        ) -> User:
            can_access = await RBACService.can_access_resource(
                user=user,
                resource_owner_id=resource_owner_id,
                required_permission=permission,
                allow_owner=allow_self_access
            )
            
            if self.log_access:
                await RBACService.log_permission_check(
                    user=user,
                    permission=permission,
                    granted=can_access,
                    resource_type="custom_resource",
                    resource_id=str(resource_owner_id) if resource_owner_id else None,
                    db=db
                )
            
            if not can_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this resource"
                )
            
            return user
    
    return CustomResourceAccess


# Pre-configured dependencies for common use cases

# Wallet access - users can access own wallet, admins can access any wallet
require_wallet_access = create_resource_access_dependency(
    permission=Permission.VIEW_ALL_WALLETS,
    resource_owner_field="user_id",
    allow_self_access=True
)

# Job access - users can access own jobs, admins/moderators can access any job
require_job_access = create_resource_access_dependency(
    permission=Permission.VIEW_ALL_JOBS,
    resource_owner_field="user_id", 
    allow_self_access=True
)

# Fortune reading access - users can access own readings, admins can access any
require_fortune_access = create_resource_access_dependency(
    permission=Permission.VIEW_ALL_FORTUNES,
    resource_owner_field="user_id",
    allow_self_access=True
)