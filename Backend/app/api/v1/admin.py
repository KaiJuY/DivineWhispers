"""
Admin API endpoints for user and role management

These endpoints provide administrative functionality for managing users,
roles, permissions, and system operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

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