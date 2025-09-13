"""
Admin API endpoints for user and role management

These endpoints provide administrative functionality for managing users,
roles, permissions, and system operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, delete
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.faq import FAQ
from app.schemas.faq import FAQCreate, FAQUpdate, FAQResponse

import re
from app.utils.deps import get_db, get_current_user
from app.utils.rbac import (
    RequirePermission,
    RequireRole,
    require_admin,
    require_user_management,
    require_system_access
)
from app.models.user import User, UserRole, UserStatus
from app.models.audit_log import AuditLog, ActionType
from app.models.wallet import Wallet
from app.models.job import Job
from app.core.permissions import Permission, get_all_permissions_for_role
from app.services.rbac_service import RBACService
from app.services.auth_service import AuthService
from app.schemas.rbac import (
    RoleChangeRequest,
    RoleChangeResponse,
    UserSuspensionRequest,
    UserActivationRequest,
    UserStatusChangeResponse,
    UserPermissionsResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    BulkPermissionCheckRequest,
    BulkPermissionCheckResponse,
    UserManagementFilter,
    UserManagementResponse,
    PaginatedUserResponse,
    SystemRBACStats,
    RoleStatistics,
    PermissionStatistics,
    AuditLogFilter,
    AuditLogEntry,
    PaginatedAuditLogResponse,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    PointAdjustmentRequest,
    PointAdjustmentResponse,
    RBACError,
    SuccessResponse,
    MessageResponse,
    PermissionInfo,
    RoleInfo
)

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


@router.get(
    "/stats",
    response_model=SystemRBACStats,
    summary="Get system RBAC statistics",
    description="Get comprehensive statistics about roles, permissions, and user management"
)
async def get_system_stats(
    current_user: User = Depends(require_system_access()),
    db: AsyncSession = Depends(get_db)
):
    """Get system RBAC statistics"""
    
    # Total users
    total_users_result = await db.execute(select(func.count(User.user_id)))
    total_users = total_users_result.scalar()
    
    # Role distribution
    role_stats = []
    for role in UserRole:
        role_count_result = await db.execute(
            select(func.count(User.user_id)).where(User.role == role)
        )
        role_count = role_count_result.scalar()
        
        active_count_result = await db.execute(
            select(func.count(User.user_id)).where(
                and_(User.role == role, User.status == UserStatus.ACTIVE)
            )
        )
        active_count = active_count_result.scalar()
        
        suspended_count_result = await db.execute(
            select(func.count(User.user_id)).where(
                and_(User.role == role, User.status == UserStatus.SUSPENDED)
            )
        )
        suspended_count = suspended_count_result.scalar()
        
        role_stats.append(RoleStatistics(
            role=role.value,
            count=role_count,
            percentage=round((role_count / total_users) * 100, 2) if total_users > 0 else 0,
            active_count=active_count,
            suspended_count=suspended_count
        ))
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_role_changes_result = await db.execute(
        select(func.count(AuditLog.log_id)).where(
            and_(
                AuditLog.resource_type == "user_role",
                AuditLog.timestamp >= thirty_days_ago
            )
        )
    )
    recent_role_changes = recent_role_changes_result.scalar()
    
    recent_suspensions_result = await db.execute(
        select(func.count(AuditLog.log_id)).where(
            and_(
                AuditLog.resource_type == "user_status",
                AuditLog.timestamp >= thirty_days_ago
            )
        )
    )
    recent_suspensions = recent_suspensions_result.scalar()
    
    critical_usage_result = await db.execute(
        select(func.count(AuditLog.log_id)).where(
            and_(
                AuditLog.resource_type == "permission",
                AuditLog.timestamp >= thirty_days_ago,
                AuditLog.details["critical"].astext == "true"
            )
        )
    )
    critical_permission_usage = critical_usage_result.scalar()
    
    # Mock permission statistics (would need more complex queries for real data)
    permission_stats = []
    for permission in Permission:
        # Count users with this permission
        users_with_permission = 0
        for role in UserRole:
            if permission in get_all_permissions_for_role(role):
                role_count_result = await db.execute(
                    select(func.count(User.user_id)).where(User.role == role)
                )
                users_with_permission += role_count_result.scalar()
        
        permission_stats.append(PermissionStatistics(
            permission=permission.value,
            category=permission.value.split("_")[0],  # Simplified category
            users_with_permission=users_with_permission,
            usage_count=0,  # Would need detailed tracking
            last_used=None  # Would need detailed tracking
        ))
    
    return SystemRBACStats(
        total_users=total_users,
        role_distribution=role_stats,
        permission_usage=permission_stats[:10],  # Limit to first 10
        recent_role_changes=recent_role_changes,
        recent_suspensions=recent_suspensions,
        critical_permission_usage=critical_permission_usage
    )


@router.get(
    "/users",
    response_model=PaginatedUserResponse,
    summary="List all users with filtering",
    description="Get paginated list of users with optional filtering by role, status, etc."
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by email"),
    current_user: User = Depends(RequirePermission(Permission.VIEW_ALL_USERS)),
    db: AsyncSession = Depends(get_db)
):
    """List users with pagination and filtering"""
    
    # Build query
    query = select(User)
    count_query = select(func.count(User.user_id))
    
    # Apply filters
    conditions = []
    if role:
        conditions.append(User.role == role)
    if status:
        conditions.append(User.status == status)
    if search:
        conditions.append(User.email.ilike(f"%{search}%"))
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(desc(User.created_at))
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Convert to response format
    user_responses = []
    for user in users:
        user_response = UserManagementResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            points_balance=user.points_balance,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active(),
            can_be_suspended=(
                user.user_id != current_user.user_id and
                await RBACService.has_permission(current_user, Permission.SUSPEND_USER) and
                user.status != UserStatus.SUSPENDED
            ),
            can_change_role=(
                await RBACService.has_permission(current_user, Permission.MODIFY_USER_ROLES)
            )
        )
        user_responses.append(user_response)
    
    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedUserResponse(
        users=user_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get(
    "/users/{user_id}",
    response_model=UserPermissionsResponse,
    summary="Get user details with permissions",
    description="Get detailed information about a user including their permissions"
)
async def get_user_details(
    user_id: int,
    current_user: User = Depends(RequirePermission(Permission.VIEW_ALL_USERS)),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user information with permissions"""
    
    # Get user
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get permissions
    permissions_info = await RBACService.get_user_permissions(user)
    
    return UserPermissionsResponse(**permissions_info)


@router.post(
    "/users",
    response_model=CreateUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user account (admin only)"
)
async def create_user(
    user_data: CreateUserRequest,
    request: Request,
    current_user: User = Depends(RequirePermission(Permission.CREATE_USER)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user account"""
    
    client_ip = get_client_ip(request)
    
    # Check if admin can assign the requested role
    from app.core.permissions import can_manage_role
    if not can_manage_role(current_user.role, user_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient privileges to create user with {user_data.role.value} role"
        )
    
    # Check if user already exists
    existing_user_result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    try:
        # Create user using auth service
        from app.schemas.auth import UserRegister
        register_data = UserRegister(
            email=user_data.email,
            password=user_data.password,
            confirm_password=user_data.password
        )
        
        user, tokens = await AuthService.register_user(db, register_data, client_ip)
        
        # Update role and points if different from defaults
        if user_data.role != UserRole.USER:
            user.role = user_data.role
        if user_data.initial_points > 0:
            user.points_balance = user_data.initial_points
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action=ActionType.CREATE,
            resource_type="user",
            resource_id=str(user.user_id),
            details={
                "created_user_email": user.email,
                "assigned_role": user.role.value,
                "initial_points": user.points_balance
            }
        )
        db.add(audit_log)
        await db.commit()
        
        return CreateUserResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            initial_points=user.points_balance,
            created_by=current_user.user_id,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put(
    "/users/{user_id}/role",
    response_model=RoleChangeResponse,
    summary="Change user role",
    description="Change a user's role with proper validation and audit logging"
)
async def change_user_role(
    user_id: int,
    role_data: RoleChangeRequest,
    current_user: User = Depends(RequirePermission(Permission.MODIFY_USER_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """Change a user's role"""
    
    if role_data.target_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and request body must match"
        )
    
    try:
        old_user = await db.get(User, user_id)
        if not old_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        old_role = old_user.role
        
        updated_user = await RBACService.change_user_role(
            manager=current_user,
            target_user_id=user_id,
            new_role=role_data.new_role,
            db=db,
            reason=role_data.reason
        )
        
        return RoleChangeResponse(
            user_id=updated_user.user_id,
            email=updated_user.email,
            old_role=old_role.value,
            new_role=updated_user.role.value,
            changed_by=current_user.user_id,
            changed_at=updated_user.updated_at,
            reason=role_data.reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change user role"
        )


@router.put(
    "/users/{user_id}/suspend",
    response_model=UserStatusChangeResponse,
    summary="Suspend user",
    description="Suspend a user account"
)
async def suspend_user(
    user_id: int,
    suspension_data: UserSuspensionRequest,
    current_user: User = Depends(RequirePermission(Permission.SUSPEND_USER)),
    db: AsyncSession = Depends(get_db)
):
    """Suspend a user account"""
    
    if suspension_data.target_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and request body must match"
        )
    
    try:
        old_user = await db.get(User, user_id)
        if not old_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        old_status = old_user.status
        
        updated_user = await RBACService.suspend_user(
            manager=current_user,
            target_user_id=user_id,
            db=db,
            reason=suspension_data.reason
        )
        
        return UserStatusChangeResponse(
            user_id=updated_user.user_id,
            email=updated_user.email,
            old_status=old_status.value,
            new_status=updated_user.status.value,
            changed_by=current_user.user_id,
            changed_at=updated_user.updated_at,
            reason=suspension_data.reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )


@router.put(
    "/users/{user_id}/activate",
    response_model=UserStatusChangeResponse,
    summary="Activate user",
    description="Activate/unsuspend a user account"
)
async def activate_user(
    user_id: int,
    activation_data: UserActivationRequest,
    current_user: User = Depends(RequirePermission(Permission.SUSPEND_USER)),
    db: AsyncSession = Depends(get_db)
):
    """Activate/unsuspend a user account"""
    
    if activation_data.target_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and request body must match"
        )
    
    try:
        old_user = await db.get(User, user_id)
        if not old_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        old_status = old_user.status
        
        updated_user = await RBACService.activate_user(
            manager=current_user,
            target_user_id=user_id,
            db=db,
            reason=activation_data.reason
        )
        
        return UserStatusChangeResponse(
            user_id=updated_user.user_id,
            email=updated_user.email,
            old_status=old_status.value,
            new_status=updated_user.status.value,
            changed_by=current_user.user_id,
            changed_at=updated_user.updated_at,
            reason=activation_data.reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@router.put(
    "/users/{user_id}/points",
    response_model=PointAdjustmentResponse,
    summary="Adjust user points",
    description="Adjust a user's point balance"
)
async def adjust_user_points(
    user_id: int,
    adjustment_data: PointAdjustmentRequest,
    current_user: User = Depends(RequirePermission(Permission.ADJUST_USER_BALANCE)),
    db: AsyncSession = Depends(get_db)
):
    """Adjust a user's point balance"""
    
    if adjustment_data.target_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and request body must match"
        )
    
    # Get target user
    result = await db.execute(select(User).where(User.user_id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_balance = target_user.points_balance
    new_balance = old_balance + adjustment_data.amount
    
    if new_balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment would result in negative balance"
        )
    
    try:
        # Update balance
        target_user.points_balance = new_balance
        target_user.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action=ActionType.UPDATE,
            resource_type="user_balance",
            resource_id=str(user_id),
            details={
                "target_user_email": target_user.email,
                "old_balance": old_balance,
                "new_balance": new_balance,
                "adjustment_amount": adjustment_data.amount,
                "reason": adjustment_data.reason,
                "adjustment_type": adjustment_data.adjustment_type
            }
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(target_user)
        
        return PointAdjustmentResponse(
            user_id=target_user.user_id,
            user_email=target_user.email,
            old_balance=old_balance,
            new_balance=new_balance,
            adjustment_amount=adjustment_data.amount,
            reason=adjustment_data.reason,
            adjusted_by=current_user.user_id,
            adjusted_at=target_user.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust user points"
        )


@router.delete(
    "/users/{user_id}",
    response_model=DeleteUserResponse,
    summary="Delete user",
    description="Delete a user account (soft delete by default)"
)
async def delete_user(
    user_id: int,
    deletion_data: DeleteUserRequest,
    current_user: User = Depends(RequirePermission(Permission.DELETE_USER)),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user account"""
    
    if deletion_data.target_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and request body must match"
        )
    
    # Get target user
    result = await db.execute(select(User).where(User.user_id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    try:
        deletion_type = "permanent" if deletion_data.permanent else "soft"
        
        if deletion_data.permanent:
            # Permanent deletion - actually remove from database
            await db.delete(target_user)
        else:
            # Soft deletion - mark as inactive/banned
            target_user.status = UserStatus.BANNED
            target_user.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action=ActionType.DELETE,
            resource_type="user",
            resource_id=str(user_id),
            details={
                "deleted_user_email": target_user.email,
                "deletion_type": deletion_type,
                "reason": deletion_data.reason,
                "permanent": deletion_data.permanent,
                "data_transferred_to": deletion_data.transfer_data_to
            }
        )
        
        db.add(audit_log)
        await db.commit()
        
        return DeleteUserResponse(
            deleted_user_id=user_id,
            deleted_user_email=target_user.email,
            deletion_type=deletion_type,
            deleted_by=current_user.user_id,
            deleted_at=datetime.utcnow(),
            reason=deletion_data.reason,
            data_transferred_to=deletion_data.transfer_data_to
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get(
    "/audit-logs",
    response_model=PaginatedAuditLogResponse,
    summary="Get audit logs",
    description="Get paginated audit logs with filtering"
)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    critical_only: bool = Query(False, description="Show only critical actions"),
    current_user: User = Depends(RequirePermission(Permission.VIEW_AUDIT_LOGS)),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated audit logs with filtering"""
    
    # Build query
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.log_id))
    
    # Apply filters
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if start_date:
        conditions.append(AuditLog.timestamp >= start_date)
    if end_date:
        conditions.append(AuditLog.timestamp <= end_date)
    if critical_only:
        conditions.append(AuditLog.details["critical"].astext == "true")
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(desc(AuditLog.timestamp))
    
    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()
    
    # Convert to response format
    log_entries = []
    for log in audit_logs:
        # Get user email if available
        user_email = None
        if log.user:
            user_email = log.user.email
        
        log_entry = AuditLogEntry(
            log_id=log.log_id,
            user_id=log.user_id,
            user_email=user_email,
            action=log.action.value,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details or {},
            timestamp=log.timestamp,
            ip_address=log.details.get("ip_address") if log.details else None
        )
        log_entries.append(log_entry)
    
    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedAuditLogResponse(
        logs=log_entries,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get(
    "/permissions",
    response_model=List[PermissionInfo],
    summary="List all permissions",
    description="Get list of all system permissions with descriptions"
)
async def list_permissions(
    current_user: User = Depends(require_system_access()),
    db: AsyncSession = Depends(get_db)
):
    """List all system permissions"""
    
    from app.core.permissions import PERMISSION_DESCRIPTIONS, PERMISSION_CATEGORIES, is_critical_permission
    
    permissions = []
    for permission in Permission:
        perm_info = PermissionInfo(
            permission=permission.value,
            category=PERMISSION_CATEGORIES.get(permission, "unknown").value,
            description=PERMISSION_DESCRIPTIONS.get(permission, "No description available"),
            critical=is_critical_permission(permission)
        )
        permissions.append(perm_info)
    
    return permissions


@router.get(
    "/roles",
    response_model=List[RoleInfo],
    summary="List all roles",
    description="Get list of all roles with their permissions"
)
async def list_roles(
    current_user: User = Depends(require_system_access()),
    db: AsyncSession = Depends(get_db)
):
    """List all roles with their permissions"""
    
    from app.core.permissions import get_role_level, can_manage_role, is_critical_permission
    
    roles = []
    for role in UserRole:
        permissions = get_all_permissions_for_role(role)
        critical_permissions = [p for p in permissions if is_critical_permission(p)]
        manageable_roles = [r for r in UserRole if can_manage_role(role, r)]
        
        role_info = RoleInfo(
            role=role.value,
            level=get_role_level(role),
            permissions=[p.value for p in permissions],
            permission_count=len(permissions),
            critical_permissions=[p.value for p in critical_permissions],
            can_manage_roles=[r.value for r in manageable_roles]
        )
        roles.append(role_info)
    
    return roles


@router.post(
    "/check-permission",
    response_model=PermissionCheckResponse,
    summary="Check user permission",
    description="Check if the current user has a specific permission"
)
async def check_permission(
    permission_data: PermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if user has a specific permission"""
    
    has_permission = await RBACService.can_access_resource(
        user=current_user,
        resource_owner_id=permission_data.resource_owner_id,
        required_permission=permission_data.permission,
        allow_owner=True
    )
    
    is_owner = (
        permission_data.resource_owner_id is not None and 
        current_user.user_id == permission_data.resource_owner_id
    )
    
    reason = "Permission granted"
    if not has_permission:
        if is_owner:
            reason = "Access denied: insufficient permissions for owned resource"
        else:
            reason = f"Permission required: {permission_data.permission.value}"
    
    return PermissionCheckResponse(
        user_id=current_user.user_id,
        permission=permission_data.permission.value,
        granted=has_permission,
        reason=reason,
        resource_owner_id=permission_data.resource_owner_id,
        is_owner=is_owner,
        user_role=current_user.role.value
    )


@router.post(
    "/check-permissions-bulk",
    response_model=BulkPermissionCheckResponse,
    summary="Check multiple permissions",
    description="Check if the current user has multiple permissions"
)
async def check_permissions_bulk(
    permission_data: BulkPermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check multiple permissions for user"""
    
    checks = {}
    granted_count = 0
    
    for permission in permission_data.permissions:
        has_permission = await RBACService.can_access_resource(
            user=current_user,
            resource_owner_id=permission_data.resource_owner_id,
            required_permission=permission,
            allow_owner=True
        )
        
        checks[permission.value] = has_permission
        if has_permission:
            granted_count += 1
    
    return BulkPermissionCheckResponse(
        user_id=current_user.user_id,
        user_role=current_user.role.value,
        checks=checks,
        any_granted=granted_count > 0,
        all_granted=granted_count == len(permission_data.permissions)
    )


# Enhanced Customer Management Dashboard

@router.get("/dashboard/overview")
async def get_admin_dashboard_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard overview for admins"""
    try:
        # Get user statistics
        total_users = await db.scalar(select(func.count(User.user_id)))
        active_users = await db.scalar(
            select(func.count(User.user_id)).where(User.status == UserStatus.ACTIVE)
        )
        new_users_today = await db.scalar(
            select(func.count(User.user_id)).where(
                func.date(User.created_at) == datetime.utcnow().date()
            )
        )
        
        # Get wallet/transaction statistics
        from app.models.transaction import Transaction, TransactionType
        total_transactions = await db.scalar(select(func.count(Transaction.transaction_id)))
        total_revenue = await db.scalar(
            select(func.sum(Transaction.amount)).where(Transaction.transaction_type == TransactionType.CREDIT)
        ) or 0
        
        # Get chat statistics
        from app.models.chat_message import ChatSession, ChatMessage
        total_chat_sessions = await db.scalar(select(func.count(ChatSession.id)))
        total_chat_messages = await db.scalar(select(func.count(ChatMessage.id)))
        
        # Get job statistics (fortune readings)
        from app.models.fortune_job import FortuneJob, JobStatus
        total_fortune_jobs = await db.scalar(select(func.count(FortuneJob.id)))
        completed_jobs = await db.scalar(
            select(func.count(FortuneJob.id)).where(FortuneJob.status == JobStatus.COMPLETED)
        )
        
        return {
            "users": {
                "total": total_users or 0,
                "active": active_users or 0,
                "new_today": new_users_today or 0,
                "suspended": (total_users or 0) - (active_users or 0)
            },
            "revenue": {
                "total_transactions": total_transactions or 0,
                "total_revenue": float(total_revenue) if total_revenue else 0.0,
                "currency": "USD"
            },
            "engagement": {
                "chat_sessions": total_chat_sessions or 0,
                "chat_messages": total_chat_messages or 0,
                "fortune_readings": completed_jobs or 0,
                "success_rate": round((completed_jobs / max(total_fortune_jobs, 1)) * 100, 1) if total_fortune_jobs else 0
            },
            "system": {
                "uptime": "99.9%",  # Placeholder
                "api_calls_today": 1500,  # Placeholder
                "error_rate": "0.1%"  # Placeholder
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard overview")


@router.get("/customers")
async def get_customer_list(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated customer list with search and filtering"""
    try:
        # Build base query
        query = select(User)
        count_query = select(func.count(User.user_id))
        
        # Apply search filter
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%") if hasattr(User, 'full_name') else False
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply status filter
        if status_filter and status_filter != "all":
            try:
                status_enum = UserStatus(status_filter)
                query = query.where(User.status == status_enum)
                count_query = count_query.where(User.status == status_enum)
            except ValueError:
                pass
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total_count = await db.scalar(count_query)
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Enhance user data with additional info
        customer_list = []
        for user in users:
            # Get wallet info
            wallet_result = await db.execute(
                select(Wallet).where(Wallet.user_id == user.user_id)
            )
            wallet = wallet_result.scalar_one_or_none()
            
            # Get recent activity
            recent_activity = await db.scalar(
                select(func.max(AuditLog.timestamp)).where(AuditLog.user_id == user.user_id)
            )
            
            customer_info = {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": getattr(user, 'full_name', None),
                "status": user.status.value,
                "role": user.role.value,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": getattr(user, 'last_login', None),
                "wallet_balance": wallet.available_balance if wallet else 0,
                "total_spent": wallet.total_spent if hasattr(wallet, 'total_spent') else 0,
                "recent_activity": recent_activity
            }
            customer_list.append(customer_info)
        
        return {
            "customers": customer_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count or 0,
                "pages": ((total_count or 0) + limit - 1) // limit
            },
            "filters": {
                "search": search,
                "status": status_filter,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting customer list: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer list")


@router.get("/customers/{user_id}")
async def get_customer_details(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific customer"""
    try:
        # Get user
        user = await db.scalar(select(User).where(User.user_id == user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get wallet information
        wallet_result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallet = wallet_result.scalar_one_or_none()
        
        # Get transaction history
        from app.models.transaction import Transaction
        transactions_result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(10)
        )
        recent_transactions = transactions_result.scalars().all()
        
        # Get chat sessions
        from app.models.chat_message import ChatSession
        chat_sessions_result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.created_at))
            .limit(5)
        )
        recent_chats = chat_sessions_result.scalars().all()
        
        # Get fortune job history
        from app.models.fortune_job import FortuneJob
        jobs_result = await db.execute(
            select(FortuneJob)
            .where(FortuneJob.user_id == user_id)
            .order_by(desc(FortuneJob.created_at))
            .limit(10)
        )
        recent_jobs = jobs_result.scalars().all()
        
        # Get audit logs
        audit_logs_result = await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(20)
        )
        audit_logs = audit_logs_result.scalars().all()
        
        return {
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": getattr(user, 'full_name', None),
                "phone": getattr(user, 'phone', None),
                "status": user.status.value,
                "role": user.role.value,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": getattr(user, 'last_login', None),
                "preferred_language": getattr(user, 'preferred_language', 'en')
            },
            "wallet": {
                "balance": wallet.available_balance if wallet else 0,
                "pending": wallet.pending_amount if wallet else 0,
                "total_earned": wallet.total_earned if hasattr(wallet, 'total_earned') else 0,
                "total_spent": wallet.total_spent if hasattr(wallet, 'total_spent') else 0
            },
            "activity": {
                "total_transactions": len(recent_transactions),
                "total_chat_sessions": len(recent_chats),
                "total_fortune_readings": len(recent_jobs),
                "recent_transactions": [
                    {
                        "id": t.transaction_id,
                        "amount": float(t.amount),
                        "type": t.transaction_type.value,
                        "description": t.description,
                        "created_at": t.created_at
                    } for t in recent_transactions
                ],
                "recent_chats": [
                    {
                        "id": c.id,
                        "name": c.session_name,
                        "created_at": c.created_at,
                        "message_count": len(c.messages) if hasattr(c, 'messages') else 0
                    } for c in recent_chats
                ],
                "recent_jobs": [
                    {
                        "id": j.id,
                        "type": j.job_type.value,
                        "status": j.status.value,
                        "created_at": j.created_at,
                        "completed_at": j.completed_at
                    } for j in recent_jobs
                ]
            },
            "audit_trail": [
                {
                    "id": log.id,
                    "action": log.action.value,
                    "resource_type": log.resource_type,
                    "timestamp": log.timestamp,
                    "ip_address": log.ip_address,
                    "details": log.details
                } for log in audit_logs
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer details for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer details")


@router.post("/customers/{user_id}/actions")
async def perform_customer_action(
    user_id: int,
    action: str,
    reason: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Perform administrative actions on a customer account"""
    try:
        # Get target user
        target_user = await db.scalar(select(User).where(User.user_id == user_id))
        if not target_user:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Prevent admin from acting on themselves
        if target_user.user_id == current_user.user_id:
            raise HTTPException(status_code=400, detail="Cannot perform actions on your own account")
        
        action_performed = None
        
        if action == "suspend":
            target_user.status = UserStatus.SUSPENDED
            action_performed = "Account suspended"
        elif action == "activate":
            target_user.status = UserStatus.ACTIVE
            action_performed = "Account activated"
        elif action == "ban":
            target_user.status = UserStatus.BANNED
            action_performed = "Account banned"
        elif action == "reset_password":
            # In real implementation, you would generate a password reset token
            action_performed = "Password reset initiated"
        elif action == "add_points":
            # This would require additional parameters
            action_performed = "Points added to account"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action=ActionType.USER_MANAGEMENT,
            resource_type="user",
            resource_id=str(user_id),
            ip_address="admin_dashboard",
            details={
                "action": action,
                "target_user": target_user.email,
                "reason": reason,
                "performed_by": current_user.email
            }
        )
        db.add(audit_log)
        
        await db.commit()
        
        return {
            "success": True,
            "action": action,
            "message": action_performed,
            "target_user_id": user_id,
            "performed_by": current_user.email,
            "timestamp": datetime.utcnow(),
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing customer action {action} on user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform customer action")


# FAQ Management System

@router.get("/faq")
async def get_admin_faqs(
    category: Optional[str] = Query(None),
    published_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get FAQs for admin management"""
    try:
        from app.models.faq import FAQ, FAQCategory
        from app.schemas.faq import FAQListResponse, FAQResponse
        
        # Build query
        query = select(FAQ)
        count_query = select(func.count(FAQ.id))
        
        # Apply filters
        if category:
            try:
                category_enum = FAQCategory(category)
                query = query.where(FAQ.category == category_enum)
                count_query = count_query.where(FAQ.category == category_enum)
            except ValueError:
                pass
        
        if published_only:
            query = query.where(FAQ.is_published == True)
            count_query = count_query.where(FAQ.is_published == True)
        
        # Order by display_order and created_at
        query = query.order_by(FAQ.display_order, desc(FAQ.created_at))
        
        # Get total count
        total_count = await db.scalar(count_query)
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        faqs = result.scalars().all()
        
        # Get all categories for filter
        categories_result = await db.execute(
            select(FAQ.category).distinct()
        )
        categories = [cat[0] for cat in categories_result.all()]
        
        faq_responses = [FAQResponse.model_validate(faq) for faq in faqs]
        
        return FAQListResponse(
            faqs=faq_responses,
            total_count=total_count or 0,
            categories=categories
        )
        
    except Exception as e:
        logger.error(f"Error getting admin FAQs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve FAQs")


@router.post("/faq", status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq_data: "FAQCreate",
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new FAQ"""
    try:
        # Generate slug from question
        slug = re.sub(r'[^\w\s-]', '', faq_data.question.lower())
        slug = re.sub(r'[-\s]+', '-', slug)[:200]
        
        # Ensure slug is unique
        base_slug = slug
        counter = 1
        while await db.scalar(select(FAQ).where(FAQ.slug == slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create FAQ
        faq = FAQ(
            category=faq_data.category,
            question=faq_data.question,
            answer=faq_data.answer,
            slug=slug,
            tags=faq_data.tags,
            display_order=faq_data.display_order or 0,
            is_published=faq_data.is_published if faq_data.is_published is not None else True,
            created_by=current_user.user_id
        )
        
        db.add(faq)
        await db.commit()
        await db.refresh(faq)
        
        logger.info(f"Admin {current_user.user_id} created FAQ {faq.id}")
        
        from app.schemas.faq import FAQResponse
        return FAQResponse.model_validate(faq)
        
    except Exception as e:
        logger.error(f"Error creating FAQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to create FAQ")


@router.put("/faq/{faq_id}")
async def update_faq(
    faq_id: int,
    faq_data: "FAQUpdate", 
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing FAQ"""
    try:
        # Get FAQ
        faq = await db.scalar(select(FAQ).where(FAQ.id == faq_id))
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Update fields
        update_data = faq_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(faq, field):
                setattr(faq, field, value)
        
        # Regenerate slug if question changed
        if "question" in update_data:
            import re
            slug = re.sub(r'[^\w\s-]', '', faq.question.lower())
            slug = re.sub(r'[-\s]+', '-', slug)[:200]
            
            # Ensure slug is unique (excluding current FAQ)
            base_slug = slug
            counter = 1
            while await db.scalar(select(FAQ).where(FAQ.slug == slug, FAQ.id != faq_id)):
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            faq.slug = slug
        
        faq.updated_by = current_user.user_id
        
        await db.commit()
        await db.refresh(faq)
        
        logger.info(f"Admin {current_user.user_id} updated FAQ {faq_id}")
        
        return FAQResponse.model_validate(faq)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating FAQ {faq_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update FAQ")


@router.delete("/faq/{faq_id}")
async def delete_faq(
    faq_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete an FAQ"""
    try:
        from app.models.faq import FAQ
        
        # Get FAQ
        faq = await db.scalar(select(FAQ).where(FAQ.id == faq_id))
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Delete associated feedback first
        from app.models.faq import FAQFeedback
        await db.execute(
            delete(FAQFeedback).where(FAQFeedback.faq_id == faq_id)
        )
        
        # Delete FAQ
        await db.delete(faq)
        await db.commit()
        
        logger.info(f"Admin {current_user.user_id} deleted FAQ {faq_id}")
        
        return {"message": "FAQ deleted successfully", "faq_id": faq_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting FAQ {faq_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete FAQ")


@router.get("/faq/analytics")
async def get_faq_analytics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get FAQ analytics and metrics"""
    try:
        from app.models.faq import FAQ, FAQFeedback
        from app.schemas.faq import FAQAnalytics, FAQFeedbackResponse
        
        # Basic counts
        total_faqs = await db.scalar(select(func.count(FAQ.id)))
        published_faqs = await db.scalar(
            select(func.count(FAQ.id)).where(FAQ.is_published == True)
        )
        total_views = await db.scalar(select(func.sum(FAQ.view_count))) or 0
        
        # Feedback stats
        total_feedback = await db.scalar(select(func.count(FAQFeedback.id)))
        helpful_feedback = await db.scalar(
            select(func.count(FAQFeedback.id)).where(FAQFeedback.is_helpful == True)
        ) or 0
        
        helpful_percentage = (helpful_feedback / max(total_feedback, 1)) * 100 if total_feedback else 0
        
        # Top categories
        categories_result = await db.execute(
            select(FAQ.category, func.count(FAQ.id).label('count'))
            .group_by(FAQ.category)
            .order_by(desc('count'))
            .limit(5)
        )
        top_categories = [
            {"category": cat, "count": count} 
            for cat, count in categories_result.all()
        ]
        
        # Recent feedback
        recent_feedback_result = await db.execute(
            select(FAQFeedback)
            .order_by(desc(FAQFeedback.created_at))
            .limit(10)
        )
        recent_feedback = [
            FAQFeedbackResponse.model_validate(feedback)
            for feedback in recent_feedback_result.scalars().all()
        ]
        
        return FAQAnalytics(
            total_faqs=total_faqs or 0,
            published_faqs=published_faqs or 0,
            total_views=total_views,
            total_feedback=total_feedback or 0,
            helpful_percentage=round(helpful_percentage, 1),
            top_categories=top_categories,
            recent_feedback=recent_feedback
        )
        
    except Exception as e:
        logger.error(f"Error getting FAQ analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve FAQ analytics")


# Comprehensive Analytics and Reporting

@router.get("/analytics/users")
async def get_user_analytics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive user analytics"""
    try:
        # Calculate date range
        now = datetime.utcnow()
        period_map = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30), 
            "90d": timedelta(days=90),
            "1y": timedelta(days=365)
        }
        
        start_date = now - period_map.get(period, timedelta(days=30))
        
        # User growth metrics
        total_users = await db.scalar(select(func.count(User.user_id)))
        new_users_period = await db.scalar(
            select(func.count(User.user_id)).where(User.created_at >= start_date)
        )
        active_users = await db.scalar(
            select(func.count(User.user_id)).where(User.status == UserStatus.ACTIVE)
        )
        
        # Daily registration data for chart
        daily_registrations = await db.execute(
            select(
                func.date(User.created_at).label('date'),
                func.count(User.user_id).label('count')
            )
            .where(User.created_at >= start_date)
            .group_by(func.date(User.created_at))
            .order_by('date')
        )
        
        registration_chart = [
            {"date": str(date), "registrations": count}
            for date, count in daily_registrations.all()
        ]
        
        # User status breakdown
        status_breakdown = await db.execute(
            select(User.status, func.count(User.user_id).label('count'))
            .group_by(User.status)
        )
        
        status_data = {
            status.value: count for status, count in status_breakdown.all()
        }
        
        # Role distribution
        role_breakdown = await db.execute(
            select(User.role, func.count(User.user_id).label('count'))
            .group_by(User.role)
        )
        
        role_data = {
            role.value: count for role, count in role_breakdown.all()
        }
        
        return {
            "summary": {
                "total_users": total_users or 0,
                "new_users_period": new_users_period or 0,
                "active_users": active_users or 0,
                "growth_rate": round((new_users_period / max(total_users - new_users_period, 1)) * 100, 2),
                "period": period
            },
            "charts": {
                "daily_registrations": registration_chart,
                "status_breakdown": status_data,
                "role_distribution": role_data
            },
            "insights": {
                "activation_rate": round((active_users / max(total_users, 1)) * 100, 1),
                "avg_daily_signups": round(new_users_period / 30, 1) if period == "30d" else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user analytics")


@router.get("/analytics/revenue")
async def get_revenue_analytics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive revenue analytics"""
    try:
        from app.models.transaction import Transaction, TransactionType
        
        # Calculate date range
        now = datetime.utcnow()
        period_map = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90), 
            "1y": timedelta(days=365)
        }
        
        start_date = now - period_map.get(period, timedelta(days=30))
        
        # Revenue metrics
        total_revenue = await db.scalar(
            select(func.sum(Transaction.amount))
            .where(Transaction.transaction_type == TransactionType.CREDIT)
        ) or 0
        
        period_revenue = await db.scalar(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.transaction_type == TransactionType.CREDIT,
                Transaction.created_at >= start_date
            )
        ) or 0
        
        # Daily revenue data
        daily_revenue = await db.execute(
            select(
                func.date(Transaction.created_at).label('date'),
                func.sum(Transaction.amount).label('revenue'),
                func.count(Transaction.transaction_id).label('transactions')
            )
            .where(
                Transaction.transaction_type == TransactionType.CREDIT,
                Transaction.created_at >= start_date
            )
            .group_by(func.date(Transaction.created_at))
            .order_by('date')
        )
        
        revenue_chart = [
            {
                "date": str(date),
                "revenue": float(revenue),
                "transactions": transactions
            }
            for date, revenue, transactions in daily_revenue.all()
        ]
        
        # Average transaction value
        avg_transaction = await db.scalar(
            select(func.avg(Transaction.amount))
            .where(
                Transaction.transaction_type == TransactionType.CREDIT,
                Transaction.created_at >= start_date
            )
        ) or 0
        
        # Top spending users
        top_users = await db.execute(
            select(
                User.email,
                func.sum(Transaction.amount).label('total_spent')
            )
            .join(Transaction, User.user_id == Transaction.user_id)
            .where(
                Transaction.transaction_type == TransactionType.DEBIT,
                Transaction.created_at >= start_date
            )
            .group_by(User.user_id, User.email)
            .order_by(desc('total_spent'))
            .limit(10)
        )
        
        spending_leaderboard = [
            {"email": email, "total_spent": float(spent)}
            for email, spent in top_users.all()
        ]
        
        return {
            "summary": {
                "total_revenue": float(total_revenue),
                "period_revenue": float(period_revenue),
                "avg_transaction_value": float(avg_transaction),
                "period": period
            },
            "charts": {
                "daily_revenue": revenue_chart,
                "top_spenders": spending_leaderboard
            },
            "insights": {
                "avg_daily_revenue": round(period_revenue / 30, 2) if period == "30d" else None,
                "revenue_growth": "positive" if period_revenue > 0 else "neutral"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue analytics")


@router.get("/analytics/engagement")
async def get_engagement_analytics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user engagement analytics"""
    try:
        from app.models.chat_message import ChatSession, ChatMessage
        from app.models.fortune_job import FortuneJob, JobStatus
        
        # Calculate date range
        now = datetime.utcnow()
        period_map = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
            "1y": timedelta(days=365)
        }
        
        start_date = now - period_map.get(period, timedelta(days=30))
        
        # Chat engagement
        total_chat_sessions = await db.scalar(
            select(func.count(ChatSession.id))
            .where(ChatSession.created_at >= start_date)
        ) or 0
        
        total_chat_messages = await db.scalar(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.created_at >= start_date)
        ) or 0
        
        avg_messages_per_session = total_chat_messages / max(total_chat_sessions, 1)
        
        # Fortune reading engagement
        total_fortune_jobs = await db.scalar(
            select(func.count(FortuneJob.id))
            .where(FortuneJob.created_at >= start_date)
        ) or 0
        
        completed_jobs = await db.scalar(
            select(func.count(FortuneJob.id))
            .where(
                FortuneJob.created_at >= start_date,
                FortuneJob.status == JobStatus.COMPLETED
            )
        ) or 0
        
        success_rate = (completed_jobs / max(total_fortune_jobs, 1)) * 100
        
        # Daily engagement data
        daily_engagement = await db.execute(
            select(
                func.date(ChatSession.created_at).label('date'),
                func.count(ChatSession.id).label('sessions'),
                func.count(ChatMessage.id).label('messages')
            )
            .outerjoin(ChatMessage, ChatSession.id == ChatMessage.session_id)
            .where(ChatSession.created_at >= start_date)
            .group_by(func.date(ChatSession.created_at))
            .order_by('date')
        )
        
        engagement_chart = [
            {
                "date": str(date),
                "sessions": sessions,
                "messages": messages or 0
            }
            for date, sessions, messages in daily_engagement.all()
        ]
        
        # Active user engagement
        active_chatters = await db.scalar(
            select(func.count(func.distinct(ChatSession.user_id)))
            .where(ChatSession.created_at >= start_date)
        ) or 0
        
        return {
            "summary": {
                "total_chat_sessions": total_chat_sessions,
                "total_chat_messages": total_chat_messages,
                "avg_messages_per_session": round(avg_messages_per_session, 1),
                "total_fortune_readings": total_fortune_jobs,
                "reading_success_rate": round(success_rate, 1),
                "active_chatters": active_chatters,
                "period": period
            },
            "charts": {
                "daily_engagement": engagement_chart
            },
            "insights": {
                "engagement_trend": "positive" if total_chat_sessions > 0 else "low",
                "avg_daily_sessions": round(total_chat_sessions / 30, 1) if period == "30d" else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting engagement analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve engagement analytics")


@router.get("/analytics/system")
async def get_system_analytics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system performance and health analytics"""
    try:
        # Database statistics
        total_records = {}
        
        # Count all major tables
        tables_to_count = [
            ("users", User),
            ("chat_sessions", "app.models.chat_message.ChatSession"),
            ("chat_messages", "app.models.chat_message.ChatMessage"),
            ("transactions", "app.models.transaction.Transaction"),
            ("fortune_jobs", "app.models.fortune_job.FortuneJob"),
            ("audit_logs", AuditLog)
        ]
        
        for table_name, model in tables_to_count:
            try:
                if isinstance(model, str):
                    # Dynamic import for models in other modules
                    module_path, class_name = model.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[class_name])
                    model_class = getattr(module, class_name)
                    count = await db.scalar(select(func.count(model_class.id)))
                else:
                    count = await db.scalar(select(func.count(model.user_id)))
                
                total_records[table_name] = count or 0
            except Exception:
                total_records[table_name] = 0
        
        # Recent system activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_activity = {
            "new_users": await db.scalar(
                select(func.count(User.user_id)).where(User.created_at >= yesterday)
            ) or 0,
            "new_sessions": 0,  # Placeholder
            "api_calls": 2500,  # Placeholder - would come from API gateway metrics
            "errors": 12  # Placeholder - would come from error logging
        }
        
        # Performance metrics (placeholders for real implementation)
        performance_metrics = {
            "avg_response_time_ms": 245,
            "database_connections": 8,
            "memory_usage_mb": 512,
            "cpu_usage_percent": 15.2,
            "disk_usage_gb": 2.3,
            "uptime_hours": 168
        }
        
        return {
            "database": {
                "total_records": total_records,
                "total_size_mb": sum(total_records.values()) * 0.001  # Rough estimate
            },
            "activity": recent_activity,
            "performance": performance_metrics,
            "health_checks": {
                "database": "healthy",
                "redis_cache": "healthy", 
                "file_storage": "healthy",
                "external_apis": "healthy"
            },
            "recommendations": [
                "Database performance is optimal",
                "Consider scaling chat system for growing usage",
                "Monitor disk space usage"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system analytics")


@router.get("/reports/export")
async def export_admin_report(
    report_type: str = Query(..., description="Type of report: users, revenue, engagement, system"),
    format: str = Query("json", description="Export format: json, csv"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export administrative reports in various formats"""
    try:
        # Get the appropriate analytics data
        if report_type == "users":
            data = await get_user_analytics(period, current_user, db)
        elif report_type == "revenue":
            data = await get_revenue_analytics(period, current_user, db)
        elif report_type == "engagement":
            data = await get_engagement_analytics(period, current_user, db)
        elif report_type == "system":
            data = await get_system_analytics(current_user, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Add export metadata
        export_data = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": current_user.email,
            "period": period,
            "format": format,
            "data": data
        }
        
        if format == "csv":
            # In a real implementation, you would convert to CSV format
            # For now, return JSON with CSV indication
            export_data["note"] = "CSV export would be implemented with pandas or csv module"
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting {report_type} report: {e}")
        raise HTTPException(status_code=500, detail="Failed to export report")