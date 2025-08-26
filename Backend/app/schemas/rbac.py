"""
Pydantic schemas for RBAC (Role-Based Access Control) operations
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from app.models.user import UserRole, UserStatus
from app.core.permissions import Permission, PermissionCategory


class RoleChangeRequest(BaseModel):
    """Schema for role change requests"""
    target_user_id: int = Field(..., description="ID of user whose role is being changed")
    new_role: UserRole = Field(..., description="New role to assign")
    reason: Optional[str] = Field(None, description="Reason for role change")
    
    class Config:
        use_enum_values = True


class RoleChangeResponse(BaseModel):
    """Schema for role change responses"""
    user_id: int
    email: str
    old_role: str
    new_role: str
    changed_by: int
    changed_at: datetime
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserSuspensionRequest(BaseModel):
    """Schema for user suspension requests"""
    target_user_id: int = Field(..., description="ID of user to suspend")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for suspension")


class UserActivationRequest(BaseModel):
    """Schema for user activation requests"""
    target_user_id: int = Field(..., description="ID of user to activate")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for activation")


class UserStatusChangeResponse(BaseModel):
    """Schema for user status change responses"""
    user_id: int
    email: str
    old_status: str
    new_status: str
    changed_by: int
    changed_at: datetime
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class PermissionInfo(BaseModel):
    """Schema for permission information"""
    permission: str
    category: str
    description: str
    critical: bool = False
    
    class Config:
        use_enum_values = True


class RoleInfo(BaseModel):
    """Schema for role information"""
    role: str
    level: int
    permissions: List[str]
    permission_count: int
    critical_permissions: List[str]
    can_manage_roles: List[str]
    
    class Config:
        use_enum_values = True


class UserPermissionsResponse(BaseModel):
    """Schema for user permissions response"""
    user_id: int
    email: str
    role: str
    status: str
    role_level: int
    permissions: List[str]
    permission_count: int
    categorized_permissions: Dict[str, List[str]]
    critical_permissions: List[str]
    can_manage_roles: List[str]
    
    class Config:
        use_enum_values = True


class PermissionCheckRequest(BaseModel):
    """Schema for permission check requests"""
    permission: Permission
    resource_owner_id: Optional[int] = Field(None, description="ID of resource owner for ownership checks")
    resource_type: Optional[str] = Field(None, description="Type of resource being accessed")
    resource_id: Optional[str] = Field(None, description="ID of resource being accessed")
    
    class Config:
        use_enum_values = True


class PermissionCheckResponse(BaseModel):
    """Schema for permission check responses"""
    user_id: int
    permission: str
    granted: bool
    reason: str
    resource_owner_id: Optional[int] = None
    is_owner: bool = False
    user_role: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class BulkPermissionCheckRequest(BaseModel):
    """Schema for bulk permission check requests"""
    permissions: List[Permission] = Field(..., description="List of permissions to check")
    resource_owner_id: Optional[int] = None
    resource_type: Optional[str] = None
    
    @validator('permissions')
    def validate_permissions(cls, v):
        if not v:
            raise ValueError("At least one permission must be specified")
        if len(v) > 20:
            raise ValueError("Maximum 20 permissions can be checked at once")
        return v
    
    class Config:
        use_enum_values = True


class BulkPermissionCheckResponse(BaseModel):
    """Schema for bulk permission check responses"""
    user_id: int
    user_role: str
    checks: Dict[str, bool]  # permission -> granted
    any_granted: bool
    all_granted: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class UserManagementFilter(BaseModel):
    """Schema for user management filtering"""
    role: Optional[UserRole] = Field(None, description="Filter by role")
    status: Optional[UserStatus] = Field(None, description="Filter by status")
    search: Optional[str] = Field(None, description="Search by email or user ID")
    has_permission: Optional[Permission] = Field(None, description="Filter users with specific permission")
    
    class Config:
        use_enum_values = True


class UserManagementResponse(BaseModel):
    """Schema for user management response"""
    user_id: int
    email: str
    role: str
    status: str
    points_balance: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    can_be_suspended: bool = False
    can_change_role: bool = False
    
    class Config:
        from_attributes = True
        use_enum_values = True


class PaginatedUserResponse(BaseModel):
    """Schema for paginated user responses"""
    users: List[UserManagementResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class RoleStatistics(BaseModel):
    """Schema for role statistics"""
    role: str
    count: int
    percentage: float
    active_count: int
    suspended_count: int
    
    class Config:
        use_enum_values = True


class PermissionStatistics(BaseModel):
    """Schema for permission usage statistics"""
    permission: str
    category: str
    users_with_permission: int
    usage_count: int
    last_used: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class SystemRBACStats(BaseModel):
    """Schema for system RBAC statistics"""
    total_users: int
    role_distribution: List[RoleStatistics]
    permission_usage: List[PermissionStatistics]
    recent_role_changes: int
    recent_suspensions: int
    critical_permission_usage: int
    
    class Config:
        use_enum_values = True


class AuditLogFilter(BaseModel):
    """Schema for audit log filtering"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    critical_only: bool = False
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError("End date must be after start date")
        return v


class AuditLogEntry(BaseModel):
    """Schema for audit log entries"""
    log_id: int
    user_id: int
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaginatedAuditLogResponse(BaseModel):
    """Schema for paginated audit log responses"""
    logs: List[AuditLogEntry]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CreateUserRequest(BaseModel):
    """Schema for admin user creation"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    role: UserRole = Field(UserRole.USER, description="Initial role for the user")
    initial_points: int = Field(0, ge=0, description="Initial point balance")
    send_welcome_email: bool = Field(False, description="Send welcome email to new user")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    class Config:
        use_enum_values = True


class CreateUserResponse(BaseModel):
    """Schema for admin user creation response"""
    user_id: int
    email: str
    role: str
    status: str
    initial_points: int
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class DeleteUserRequest(BaseModel):
    """Schema for user deletion request"""
    target_user_id: int = Field(..., description="ID of user to delete")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for deletion")
    transfer_data_to: Optional[int] = Field(None, description="User ID to transfer data to (optional)")
    permanent: bool = Field(False, description="Whether to permanently delete (true) or soft delete (false)")


class DeleteUserResponse(BaseModel):
    """Schema for user deletion response"""
    deleted_user_id: int
    deleted_user_email: str
    deletion_type: str  # "soft" or "permanent"
    deleted_by: int
    deleted_at: datetime
    reason: str
    data_transferred_to: Optional[int] = None
    
    class Config:
        from_attributes = True


class PointAdjustmentRequest(BaseModel):
    """Schema for point balance adjustment"""
    target_user_id: int = Field(..., description="ID of user whose points to adjust")
    amount: int = Field(..., description="Amount to adjust (positive or negative)")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for adjustment")
    adjustment_type: str = Field("manual", description="Type of adjustment")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError("Adjustment amount cannot be zero")
        return v


class PointAdjustmentResponse(BaseModel):
    """Schema for point adjustment response"""
    user_id: int
    user_email: str
    old_balance: int
    new_balance: int
    adjustment_amount: int
    reason: str
    adjusted_by: int
    adjusted_at: datetime
    
    class Config:
        from_attributes = True


# Error response schemas

class RBACError(BaseModel):
    """Schema for RBAC error responses"""
    error: str
    detail: str
    required_permission: Optional[str] = None
    required_role: Optional[str] = None
    user_role: Optional[str] = None
    user_permissions: Optional[List[str]] = None


class ValidationError(BaseModel):
    """Schema for validation error responses"""
    error: str = "validation_error"
    detail: str
    field_errors: Optional[Dict[str, List[str]]] = None


# Success response schemas

class SuccessResponse(BaseModel):
    """Generic success response schema"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Simple message response schema"""
    message: str


# Export commonly used schemas
__all__ = [
    "RoleChangeRequest",
    "RoleChangeResponse", 
    "UserSuspensionRequest",
    "UserActivationRequest",
    "UserStatusChangeResponse",
    "PermissionInfo",
    "RoleInfo",
    "UserPermissionsResponse",
    "PermissionCheckRequest",
    "PermissionCheckResponse",
    "BulkPermissionCheckRequest",
    "BulkPermissionCheckResponse",
    "UserManagementFilter",
    "UserManagementResponse",
    "PaginatedUserResponse",
    "RoleStatistics",
    "PermissionStatistics",
    "SystemRBACStats",
    "AuditLogFilter",
    "AuditLogEntry",
    "PaginatedAuditLogResponse",
    "CreateUserRequest",
    "CreateUserResponse",
    "DeleteUserRequest", 
    "DeleteUserResponse",
    "PointAdjustmentRequest",
    "PointAdjustmentResponse",
    "RBACError",
    "ValidationError",
    "SuccessResponse",
    "MessageResponse"
]