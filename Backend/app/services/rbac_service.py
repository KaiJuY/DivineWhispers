"""
Role-Based Access Control (RBAC) Service

This service provides business logic for role and permission management,
including permission checking, role validation, and access control utilities.
"""

from typing import Optional, List, Set, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from fastapi import HTTPException, status
from datetime import datetime

from app.models.user import User, UserRole, UserStatus
from app.models.audit_log import AuditLog, ActionType
from app.core.permissions import (
    Permission,
    PermissionCategory,
    ROLE_PERMISSIONS,
    ROLE_HIERARCHY,
    CRITICAL_PERMISSIONS,
    get_all_permissions_for_role,
    get_permissions_by_category,
    is_role_higher_or_equal,
    get_role_level,
    can_manage_role,
    is_critical_permission
)


class RBACService:
    """Service class for Role-Based Access Control operations"""
    
    @staticmethod
    async def has_permission(
        user: User,
        permission: Permission,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: The user to check permissions for
            permission: The permission to check
            db: Optional database session for logging
            
        Returns:
            True if user has the permission, False otherwise
        """
        # Inactive users have no permissions
        if not user.is_active():
            return False
            
        # Get all permissions for the user's role
        user_permissions = get_all_permissions_for_role(user.role)
        
        return permission in user_permissions
    
    @staticmethod
    async def has_any_permission(
        user: User,
        permissions: List[Permission],
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Check if a user has any of the specified permissions.
        
        Args:
            user: The user to check permissions for
            permissions: List of permissions to check
            db: Optional database session for logging
            
        Returns:
            True if user has at least one of the permissions, False otherwise
        """
        if not user.is_active():
            return False
            
        user_permissions = get_all_permissions_for_role(user.role)
        
        return any(permission in user_permissions for permission in permissions)
    
    @staticmethod
    async def has_all_permissions(
        user: User,
        permissions: List[Permission],
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Check if a user has all of the specified permissions.
        
        Args:
            user: The user to check permissions for
            permissions: List of permissions to check
            db: Optional database session for logging
            
        Returns:
            True if user has all permissions, False otherwise
        """
        if not user.is_active():
            return False
            
        user_permissions = get_all_permissions_for_role(user.role)
        
        return all(permission in user_permissions for permission in permissions)
    
    @staticmethod
    async def has_role(user: User, role: UserRole) -> bool:
        """
        Check if a user has a specific role or higher in the hierarchy.
        
        Args:
            user: The user to check
            role: The minimum required role
            
        Returns:
            True if user has the role or higher, False otherwise
        """
        if not user.is_active():
            return False
            
        return is_role_higher_or_equal(user.role, role)
    
    @staticmethod
    async def can_access_resource(
        user: User,
        resource_owner_id: Optional[int] = None,
        required_permission: Optional[Permission] = None,
        allow_owner: bool = True
    ) -> bool:
        """
        Check if a user can access a specific resource.
        
        This method combines permission checking with resource ownership validation.
        
        Args:
            user: The user trying to access the resource
            resource_owner_id: ID of the user who owns the resource (if applicable)
            required_permission: Permission required to access the resource
            allow_owner: Whether the resource owner can access it regardless of permissions
            
        Returns:
            True if access is allowed, False otherwise
        """
        if not user.is_active():
            return False
        
        # Check if user owns the resource (and ownership access is allowed)
        if allow_owner and resource_owner_id and user.user_id == resource_owner_id:
            return True
        
        # Check if user has the required permission
        if required_permission:
            return await RBACService.has_permission(user, required_permission)
        
        return False
    
    @staticmethod
    async def validate_role_change(
        manager: User,
        target_user_id: int,
        new_role: UserRole,
        db: AsyncSession
    ) -> bool:
        """
        Validate if a role change is allowed.
        
        Args:
            manager: User attempting to change the role
            target_user_id: ID of user whose role is being changed
            new_role: The new role to assign
            db: Database session
            
        Returns:
            True if role change is valid, False otherwise
            
        Raises:
            HTTPException: If validation fails
        """
        # Check if manager has permission to modify roles
        if not await RBACService.has_permission(manager, Permission.MODIFY_USER_ROLES):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to modify user roles"
            )
        
        # Get target user
        result = await db.execute(select(User).where(User.user_id == target_user_id))
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Prevent self-demotion for admins
        if (manager.user_id == target_user_id and 
            manager.role == UserRole.ADMIN and 
            new_role != UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot demote themselves"
            )
        
        # Check if manager can assign the new role
        if not can_manage_role(manager.role, new_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges to assign {new_role.value} role"
            )
        
        # Check if manager can manage the target user's current role
        if not can_manage_role(manager.role, target_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges to modify user with {target_user.role.value} role"
            )
        
        return True
    
    @staticmethod
    async def change_user_role(
        manager: User,
        target_user_id: int,
        new_role: UserRole,
        db: AsyncSession,
        reason: Optional[str] = None
    ) -> User:
        """
        Change a user's role with proper validation and audit logging.
        
        Args:
            manager: User performing the role change
            target_user_id: ID of user whose role is being changed
            new_role: The new role to assign
            db: Database session
            reason: Optional reason for the role change
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If validation fails or operation is not allowed
        """
        # Validate the role change
        await RBACService.validate_role_change(manager, target_user_id, new_role, db)
        
        # Get target user
        result = await db.execute(select(User).where(User.user_id == target_user_id))
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        old_role = target_user.role
        
        # Update the role
        target_user.role = new_role
        target_user.updated_at = datetime.utcnow()
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=manager.user_id,
            action=ActionType.UPDATE,
            resource_type="user_role",
            resource_id=str(target_user_id),
            details={
                "old_role": old_role.value,
                "new_role": new_role.value,
                "target_user_email": target_user.email,
                "reason": reason or "No reason provided"
            }
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(target_user)
        
        return target_user
    
    @staticmethod
    async def suspend_user(
        manager: User,
        target_user_id: int,
        db: AsyncSession,
        reason: Optional[str] = None
    ) -> User:
        """
        Suspend a user account with proper validation and audit logging.
        
        Args:
            manager: User performing the suspension
            target_user_id: ID of user to suspend
            db: Database session
            reason: Reason for suspension
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If validation fails or operation is not allowed
        """
        # Check permissions
        if not await RBACService.has_permission(manager, Permission.SUSPEND_USER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to suspend users"
            )
        
        # Get target user
        result = await db.execute(select(User).where(User.user_id == target_user_id))
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Prevent self-suspension
        if manager.user_id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot suspend yourself"
            )
        
        # Check if manager can suspend this user
        if not can_manage_role(manager.role, target_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges to suspend user with {target_user.role.value} role"
            )
        
        old_status = target_user.status
        
        # Update status
        target_user.status = UserStatus.SUSPENDED
        target_user.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=manager.user_id,
            action=ActionType.UPDATE,
            resource_type="user_status",
            resource_id=str(target_user_id),
            details={
                "old_status": old_status.value,
                "new_status": UserStatus.SUSPENDED.value,
                "target_user_email": target_user.email,
                "reason": reason or "No reason provided"
            }
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(target_user)
        
        return target_user
    
    @staticmethod
    async def activate_user(
        manager: User,
        target_user_id: int,
        db: AsyncSession,
        reason: Optional[str] = None
    ) -> User:
        """
        Activate/unsuspend a user account.
        
        Args:
            manager: User performing the activation
            target_user_id: ID of user to activate
            db: Database session
            reason: Reason for activation
            
        Returns:
            Updated user object
        """
        # Check permissions
        if not await RBACService.has_permission(manager, Permission.SUSPEND_USER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to activate users"
            )
        
        # Get target user
        result = await db.execute(select(User).where(User.user_id == target_user_id))
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        old_status = target_user.status
        
        # Update status
        target_user.status = UserStatus.ACTIVE
        target_user.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=manager.user_id,
            action=ActionType.UPDATE,
            resource_type="user_status",
            resource_id=str(target_user_id),
            details={
                "old_status": old_status.value,
                "new_status": UserStatus.ACTIVE.value,
                "target_user_email": target_user.email,
                "reason": reason or "No reason provided"
            }
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(target_user)
        
        return target_user
    
    @staticmethod
    async def get_users_with_role(
        role: UserRole,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            role: Role to filter by
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of users with the specified role
        """
        result = await db.execute(
            select(User)
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_user_permissions(user: User) -> Dict[str, Any]:
        """
        Get comprehensive permission information for a user.
        
        Args:
            user: User to get permissions for
            
        Returns:
            Dictionary containing role, permissions, and metadata
        """
        user_permissions = get_all_permissions_for_role(user.role)
        categorized_permissions = get_permissions_by_category(user.role)
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value,
            "role_level": get_role_level(user.role),
            "permissions": [p.value for p in user_permissions],
            "permission_count": len(user_permissions),
            "categorized_permissions": {
                category.value: [p.value for p in permissions]
                for category, permissions in categorized_permissions.items()
            },
            "critical_permissions": [
                p.value for p in user_permissions 
                if is_critical_permission(p)
            ],
            "can_manage_roles": [
                role.value for role in UserRole
                if can_manage_role(user.role, role)
            ]
        }
    
    @staticmethod
    async def log_permission_check(
        user: User,
        permission: Permission,
        granted: bool,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> None:
        """
        Log permission checks for audit purposes.
        
        Args:
            user: User who attempted the action
            permission: Permission that was checked
            granted: Whether the permission was granted
            resource_type: Type of resource accessed (optional)
            resource_id: ID of resource accessed (optional)
            db: Database session (optional)
        """
        if not db:
            return
        
        # Only log failed permission checks and critical permission usage
        if not granted or is_critical_permission(permission):
            audit_log = AuditLog(
                user_id=user.user_id,
                action=ActionType.ACCESS if granted else ActionType.ACCESS_DENIED,
                resource_type=resource_type or "permission",
                resource_id=resource_id or permission.value,
                details={
                    "permission": permission.value,
                    "granted": granted,
                    "user_role": user.role.value,
                    "critical": is_critical_permission(permission)
                }
            )
            
            db.add(audit_log)
            # Don't await commit here - let the calling code handle it
    
    @staticmethod
    def get_permission_requirements(
        permission: Permission
    ) -> Dict[str, Any]:
        """
        Get information about a permission's requirements and restrictions.
        
        Args:
            permission: Permission to get information about
            
        Returns:
            Dictionary with permission metadata
        """
        # Find which roles have this permission
        roles_with_permission = []
        for role, permissions in ROLE_PERMISSIONS.items():
            if permission in permissions:
                roles_with_permission.append(role.value)
        
        return {
            "permission": permission.value,
            "category": PERMISSION_CATEGORIES.get(permission, "unknown").value,
            "description": PERMISSION_DESCRIPTIONS.get(permission, "No description available"),
            "roles": roles_with_permission,
            "critical": is_critical_permission(permission),
            "minimum_role_level": min([get_role_level(role) for role in UserRole if permission in get_all_permissions_for_role(role)]) if roles_with_permission else 0
        }


# Import permission categories and descriptions for convenience
from app.core.permissions import PERMISSION_CATEGORIES, PERMISSION_DESCRIPTIONS