"""
Role-Based Access Control (RBAC) permissions and role mappings
"""

from enum import Enum
from typing import Dict, Set, List
from app.models.user import UserRole


class Permission(str, Enum):
    """
    System permissions enumeration
    
    Each permission represents a specific action that can be performed in the system.
    Permissions are assigned to roles through the ROLE_PERMISSIONS mapping.
    """
    
    # User Management Permissions
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user"
    SUSPEND_USER = "suspend_user"
    VIEW_ALL_USERS = "view_all_users"
    MODIFY_USER_ROLES = "modify_user_roles"
    VIEW_USER_DETAILS = "view_user_details"
    UPDATE_USER_PROFILE = "update_user_profile"
    
    # Fortune Service Permissions
    USE_FORTUNE_SERVICE = "use_fortune_service"
    VIEW_ALL_FORTUNES = "view_all_fortunes"
    MANAGE_FORTUNE_PRICING = "manage_fortune_pricing"
    VIEW_FORTUNE_ANALYTICS = "view_fortune_analytics"
    MODERATE_FORTUNE_CONTENT = "moderate_fortune_content"
    
    # Financial Permissions
    MANAGE_OWN_WALLET = "manage_own_wallet"
    VIEW_ALL_WALLETS = "view_all_wallets"
    MANAGE_ALL_TRANSACTIONS = "manage_all_transactions"
    REFUND_POINTS = "refund_points"
    VIEW_FINANCIAL_REPORTS = "view_financial_reports"
    ADJUST_USER_BALANCE = "adjust_user_balance"
    
    # Job Management Permissions
    VIEW_OWN_JOBS = "view_own_jobs"
    VIEW_ALL_JOBS = "view_all_jobs"
    MANAGE_JOB_QUEUE = "manage_job_queue"
    CANCEL_ANY_JOB = "cancel_any_job"
    RETRY_FAILED_JOBS = "retry_failed_jobs"
    
    # System Permissions
    VIEW_SYSTEM_LOGS = "view_system_logs"
    SYSTEM_MAINTENANCE = "system_maintenance"
    MANAGE_CONFIGURATIONS = "manage_configurations"
    VIEW_SYSTEM_METRICS = "view_system_metrics"
    BACKUP_RESTORE = "backup_restore"
    
    # Audit and Security Permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SECURITY_SETTINGS = "manage_security_settings"
    EXPORT_USER_DATA = "export_user_data"
    DELETE_AUDIT_LOGS = "delete_audit_logs"
    
    # Content Moderation Permissions
    MODERATE_USER_CONTENT = "moderate_user_content"
    BAN_USERS = "ban_users"
    REVIEW_REPORTED_CONTENT = "review_reported_content"
    MANAGE_BLACKLISTS = "manage_blacklists"


class PermissionCategory(str, Enum):
    """Permission categories for organization and UI purposes"""
    USER_MANAGEMENT = "user_management"
    FORTUNE_SERVICES = "fortune_services"
    FINANCIAL = "financial"
    JOB_MANAGEMENT = "job_management"
    SYSTEM = "system"
    AUDIT_SECURITY = "audit_security"
    CONTENT_MODERATION = "content_moderation"


# Permission to category mapping
PERMISSION_CATEGORIES: Dict[Permission, PermissionCategory] = {
    # User Management
    Permission.CREATE_USER: PermissionCategory.USER_MANAGEMENT,
    Permission.DELETE_USER: PermissionCategory.USER_MANAGEMENT,
    Permission.SUSPEND_USER: PermissionCategory.USER_MANAGEMENT,
    Permission.VIEW_ALL_USERS: PermissionCategory.USER_MANAGEMENT,
    Permission.MODIFY_USER_ROLES: PermissionCategory.USER_MANAGEMENT,
    Permission.VIEW_USER_DETAILS: PermissionCategory.USER_MANAGEMENT,
    Permission.UPDATE_USER_PROFILE: PermissionCategory.USER_MANAGEMENT,
    
    # Fortune Services
    Permission.USE_FORTUNE_SERVICE: PermissionCategory.FORTUNE_SERVICES,
    Permission.VIEW_ALL_FORTUNES: PermissionCategory.FORTUNE_SERVICES,
    Permission.MANAGE_FORTUNE_PRICING: PermissionCategory.FORTUNE_SERVICES,
    Permission.VIEW_FORTUNE_ANALYTICS: PermissionCategory.FORTUNE_SERVICES,
    Permission.MODERATE_FORTUNE_CONTENT: PermissionCategory.FORTUNE_SERVICES,
    
    # Financial
    Permission.MANAGE_OWN_WALLET: PermissionCategory.FINANCIAL,
    Permission.VIEW_ALL_WALLETS: PermissionCategory.FINANCIAL,
    Permission.MANAGE_ALL_TRANSACTIONS: PermissionCategory.FINANCIAL,
    Permission.REFUND_POINTS: PermissionCategory.FINANCIAL,
    Permission.VIEW_FINANCIAL_REPORTS: PermissionCategory.FINANCIAL,
    Permission.ADJUST_USER_BALANCE: PermissionCategory.FINANCIAL,
    
    # Job Management
    Permission.VIEW_OWN_JOBS: PermissionCategory.JOB_MANAGEMENT,
    Permission.VIEW_ALL_JOBS: PermissionCategory.JOB_MANAGEMENT,
    Permission.MANAGE_JOB_QUEUE: PermissionCategory.JOB_MANAGEMENT,
    Permission.CANCEL_ANY_JOB: PermissionCategory.JOB_MANAGEMENT,
    Permission.RETRY_FAILED_JOBS: PermissionCategory.JOB_MANAGEMENT,
    
    # System
    Permission.VIEW_SYSTEM_LOGS: PermissionCategory.SYSTEM,
    Permission.SYSTEM_MAINTENANCE: PermissionCategory.SYSTEM,
    Permission.MANAGE_CONFIGURATIONS: PermissionCategory.SYSTEM,
    Permission.VIEW_SYSTEM_METRICS: PermissionCategory.SYSTEM,
    Permission.BACKUP_RESTORE: PermissionCategory.SYSTEM,
    
    # Audit & Security
    Permission.VIEW_AUDIT_LOGS: PermissionCategory.AUDIT_SECURITY,
    Permission.MANAGE_SECURITY_SETTINGS: PermissionCategory.AUDIT_SECURITY,
    Permission.EXPORT_USER_DATA: PermissionCategory.AUDIT_SECURITY,
    Permission.DELETE_AUDIT_LOGS: PermissionCategory.AUDIT_SECURITY,
    
    # Content Moderation
    Permission.MODERATE_USER_CONTENT: PermissionCategory.CONTENT_MODERATION,
    Permission.BAN_USERS: PermissionCategory.CONTENT_MODERATION,
    Permission.REVIEW_REPORTED_CONTENT: PermissionCategory.CONTENT_MODERATION,
    Permission.MANAGE_BLACKLISTS: PermissionCategory.CONTENT_MODERATION,
}


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.USER: {
        # Basic user permissions
        Permission.USE_FORTUNE_SERVICE,
        Permission.MANAGE_OWN_WALLET,
        Permission.VIEW_OWN_JOBS,
        Permission.VIEW_USER_DETAILS,  # Own details only
        Permission.UPDATE_USER_PROFILE,  # Own profile only
    },
    
    UserRole.MODERATOR: {
        # All user permissions plus moderation abilities
        Permission.USE_FORTUNE_SERVICE,
        Permission.MANAGE_OWN_WALLET,
        Permission.VIEW_OWN_JOBS,
        Permission.VIEW_USER_DETAILS,
        Permission.UPDATE_USER_PROFILE,
        
        # Moderation specific permissions
        Permission.SUSPEND_USER,
        Permission.VIEW_ALL_USERS,
        Permission.MODERATE_FORTUNE_CONTENT,
        Permission.REFUND_POINTS,
        Permission.VIEW_ALL_JOBS,
        Permission.MODERATE_USER_CONTENT,
        Permission.REVIEW_REPORTED_CONTENT,
        Permission.VIEW_AUDIT_LOGS,
        Permission.BAN_USERS,
        Permission.MANAGE_BLACKLISTS,
        Permission.CANCEL_ANY_JOB,
    },
    
    UserRole.ADMIN: {
        # All permissions (full system access)
        Permission.CREATE_USER,
        Permission.DELETE_USER,
        Permission.SUSPEND_USER,
        Permission.VIEW_ALL_USERS,
        Permission.MODIFY_USER_ROLES,
        Permission.VIEW_USER_DETAILS,
        Permission.UPDATE_USER_PROFILE,
        
        Permission.USE_FORTUNE_SERVICE,
        Permission.VIEW_ALL_FORTUNES,
        Permission.MANAGE_FORTUNE_PRICING,
        Permission.VIEW_FORTUNE_ANALYTICS,
        Permission.MODERATE_FORTUNE_CONTENT,
        
        Permission.MANAGE_OWN_WALLET,
        Permission.VIEW_ALL_WALLETS,
        Permission.MANAGE_ALL_TRANSACTIONS,
        Permission.REFUND_POINTS,
        Permission.VIEW_FINANCIAL_REPORTS,
        Permission.ADJUST_USER_BALANCE,
        
        Permission.VIEW_OWN_JOBS,
        Permission.VIEW_ALL_JOBS,
        Permission.MANAGE_JOB_QUEUE,
        Permission.CANCEL_ANY_JOB,
        Permission.RETRY_FAILED_JOBS,
        
        Permission.VIEW_SYSTEM_LOGS,
        Permission.SYSTEM_MAINTENANCE,
        Permission.MANAGE_CONFIGURATIONS,
        Permission.VIEW_SYSTEM_METRICS,
        Permission.BACKUP_RESTORE,
        
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_SECURITY_SETTINGS,
        Permission.EXPORT_USER_DATA,
        Permission.DELETE_AUDIT_LOGS,
        
        Permission.MODERATE_USER_CONTENT,
        Permission.BAN_USERS,
        Permission.REVIEW_REPORTED_CONTENT,
        Permission.MANAGE_BLACKLISTS,
    },
}


# Role hierarchy mapping (roles that inherit permissions from other roles)
ROLE_HIERARCHY: Dict[UserRole, List[UserRole]] = {
    UserRole.ADMIN: [UserRole.ADMIN, UserRole.MODERATOR, UserRole.USER],
    UserRole.MODERATOR: [UserRole.MODERATOR, UserRole.USER],
    UserRole.USER: [UserRole.USER]
}


def get_all_permissions_for_role(role: UserRole) -> Set[Permission]:
    """
    Get all permissions for a role including inherited permissions from role hierarchy.
    
    Args:
        role: The user role to get permissions for
        
    Returns:
        Set of all permissions for the role
    """
    all_permissions = set()
    
    # Get all roles this role inherits from
    inherited_roles = ROLE_HIERARCHY.get(role, [role])
    
    # Collect permissions from all inherited roles
    for inherited_role in inherited_roles:
        role_permissions = ROLE_PERMISSIONS.get(inherited_role, set())
        all_permissions.update(role_permissions)
    
    return all_permissions


def get_permissions_by_category(role: UserRole) -> Dict[PermissionCategory, Set[Permission]]:
    """
    Get permissions organized by category for a role.
    
    Args:
        role: The user role to get categorized permissions for
        
    Returns:
        Dictionary mapping categories to sets of permissions
    """
    all_permissions = get_all_permissions_for_role(role)
    categorized = {}
    
    for permission in all_permissions:
        category = PERMISSION_CATEGORIES.get(permission)
        if category:
            if category not in categorized:
                categorized[category] = set()
            categorized[category].add(permission)
    
    return categorized


def is_role_higher_or_equal(user_role: UserRole, required_role: UserRole) -> bool:
    """
    Check if a user role is higher than or equal to a required role in the hierarchy.
    
    Args:
        user_role: The user's current role
        required_role: The minimum required role
        
    Returns:
        True if user role is sufficient, False otherwise
    """
    user_hierarchy = ROLE_HIERARCHY.get(user_role, [user_role])
    return required_role in user_hierarchy


def get_role_level(role: UserRole) -> int:
    """
    Get the hierarchical level of a role (higher number = more permissions).
    
    Args:
        role: The role to get the level for
        
    Returns:
        Integer representing the role level
    """
    if role == UserRole.ADMIN:
        return 3
    elif role == UserRole.MODERATOR:
        return 2
    elif role == UserRole.USER:
        return 1
    else:
        return 0


def can_manage_role(manager_role: UserRole, target_role: UserRole) -> bool:
    """
    Check if a manager role can manage (assign/remove) a target role.
    
    Rules:
    - Admins can manage all roles
    - Moderators cannot manage admin roles
    - Users cannot manage any roles
    
    Args:
        manager_role: Role of the user attempting to manage
        target_role: Role being managed
        
    Returns:
        True if management is allowed, False otherwise
    """
    manager_level = get_role_level(manager_role)
    target_level = get_role_level(target_role)
    
    # Can only manage roles at lower levels
    return manager_level > target_level


# Permission descriptions for UI and documentation
PERMISSION_DESCRIPTIONS: Dict[Permission, str] = {
    # User Management
    Permission.CREATE_USER: "Create new user accounts",
    Permission.DELETE_USER: "Permanently delete user accounts",
    Permission.SUSPEND_USER: "Suspend or reactivate user accounts",
    Permission.VIEW_ALL_USERS: "View all user accounts and their details",
    Permission.MODIFY_USER_ROLES: "Change user roles and permissions",
    Permission.VIEW_USER_DETAILS: "View detailed user information",
    Permission.UPDATE_USER_PROFILE: "Update user profile information",
    
    # Fortune Services
    Permission.USE_FORTUNE_SERVICE: "Access fortune-telling services",
    Permission.VIEW_ALL_FORTUNES: "View all fortune readings and history",
    Permission.MANAGE_FORTUNE_PRICING: "Modify fortune service pricing and costs",
    Permission.VIEW_FORTUNE_ANALYTICS: "Access fortune service analytics and reports",
    Permission.MODERATE_FORTUNE_CONTENT: "Moderate and manage fortune content",
    
    # Financial
    Permission.MANAGE_OWN_WALLET: "Manage personal wallet and transactions",
    Permission.VIEW_ALL_WALLETS: "View all user wallets and balances",
    Permission.MANAGE_ALL_TRANSACTIONS: "Manage all financial transactions",
    Permission.REFUND_POINTS: "Issue point refunds to users",
    Permission.VIEW_FINANCIAL_REPORTS: "Access financial reports and analytics",
    Permission.ADJUST_USER_BALANCE: "Manually adjust user point balances",
    
    # Job Management
    Permission.VIEW_OWN_JOBS: "View personal job history and status",
    Permission.VIEW_ALL_JOBS: "View all system jobs and their status",
    Permission.MANAGE_JOB_QUEUE: "Manage job queue and processing",
    Permission.CANCEL_ANY_JOB: "Cancel any job in the system",
    Permission.RETRY_FAILED_JOBS: "Retry failed jobs",
    
    # System
    Permission.VIEW_SYSTEM_LOGS: "Access system logs and error reports",
    Permission.SYSTEM_MAINTENANCE: "Perform system maintenance operations",
    Permission.MANAGE_CONFIGURATIONS: "Modify system configuration settings",
    Permission.VIEW_SYSTEM_METRICS: "View system performance metrics",
    Permission.BACKUP_RESTORE: "Perform system backup and restore operations",
    
    # Audit & Security
    Permission.VIEW_AUDIT_LOGS: "Access audit logs and security events",
    Permission.MANAGE_SECURITY_SETTINGS: "Modify security settings and policies",
    Permission.EXPORT_USER_DATA: "Export user data for compliance purposes",
    Permission.DELETE_AUDIT_LOGS: "Delete old audit log entries",
    
    # Content Moderation
    Permission.MODERATE_USER_CONTENT: "Moderate user-generated content",
    Permission.BAN_USERS: "Ban users from the system",
    Permission.REVIEW_REPORTED_CONTENT: "Review content reported by users",
    Permission.MANAGE_BLACKLISTS: "Manage content and user blacklists",
}


# Critical permissions that require extra security measures
CRITICAL_PERMISSIONS: Set[Permission] = {
    Permission.DELETE_USER,
    Permission.MODIFY_USER_ROLES,
    Permission.SYSTEM_MAINTENANCE,
    Permission.BACKUP_RESTORE,
    Permission.DELETE_AUDIT_LOGS,
    Permission.MANAGE_SECURITY_SETTINGS,
    Permission.BAN_USERS,
}


def is_critical_permission(permission: Permission) -> bool:
    """
    Check if a permission is considered critical and requires extra security measures.
    
    Args:
        permission: The permission to check
        
    Returns:
        True if the permission is critical, False otherwise
    """
    return permission in CRITICAL_PERMISSIONS