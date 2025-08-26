# Divine Whispers RBAC System Usage Guide

## Overview

The Divine Whispers application now includes a comprehensive Role-Based Access Control (RBAC) system that provides fine-grained permissions and secure access control across all API endpoints.

## System Architecture

### Components Created

1. **`app/core/permissions.py`** - Core permission definitions and role mappings
2. **`app/services/rbac_service.py`** - RBAC business logic and utilities
3. **`app/utils/rbac.py`** - FastAPI decorators and dependency functions
4. **`app/schemas/rbac.py`** - Pydantic models for RBAC operations
5. **`app/api/v1/admin.py`** - Administrative endpoints
6. **`app/utils/deps.py`** - Enhanced with RBAC dependencies

## Role Hierarchy

### USER (Level 1)
- **Permissions**: 5 basic permissions
- **Can do**: Use fortune services, manage own wallet, view own jobs
- **Cannot do**: Access admin features, view other users' data

### MODERATOR (Level 2) 
- **Permissions**: 16 permissions (includes all USER permissions)
- **Can do**: Moderate content, suspend users, view audit logs, manage user reports
- **Cannot do**: Delete users, modify system settings, change roles

### ADMIN (Level 3)
- **Permissions**: 36 permissions (includes all MODERATOR and USER permissions)
- **Can do**: Everything - full system access, user management, system configuration
- **Cannot do**: Nothing (has all permissions)

## Permission Categories

1. **User Management** (7 permissions)
   - CREATE_USER, DELETE_USER, SUSPEND_USER, VIEW_ALL_USERS, etc.

2. **Fortune Services** (5 permissions)
   - USE_FORTUNE_SERVICE, VIEW_ALL_FORTUNES, MANAGE_FORTUNE_PRICING, etc.

3. **Financial** (6 permissions)
   - MANAGE_OWN_WALLET, VIEW_ALL_WALLETS, REFUND_POINTS, etc.

4. **Job Management** (5 permissions)
   - VIEW_OWN_JOBS, VIEW_ALL_JOBS, MANAGE_JOB_QUEUE, etc.

5. **System** (5 permissions)
   - VIEW_SYSTEM_LOGS, SYSTEM_MAINTENANCE, MANAGE_CONFIGURATIONS, etc.

6. **Audit & Security** (4 permissions)
   - VIEW_AUDIT_LOGS, MANAGE_SECURITY_SETTINGS, etc.

7. **Content Moderation** (4 permissions)
   - MODERATE_USER_CONTENT, BAN_USERS, REVIEW_REPORTED_CONTENT, etc.

## Using RBAC in Your Endpoints

### Method 1: Using RBAC Dependencies

```python
from app.utils.rbac import RequirePermission, RequireRole
from app.core.permissions import Permission
from app.models.user import UserRole

@router.get("/admin/users")
async def list_users(
    user: User = Depends(RequirePermission(Permission.VIEW_ALL_USERS))
):
    # Only users with VIEW_ALL_USERS permission can access
    return {"users": [...]}

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(RequireRole(UserRole.ADMIN))
):
    # Only ADMIN role can access
    return {"message": "User deleted"}
```

### Method 2: Using Pre-configured Dependencies

```python
from app.utils.deps import require_admin_role, require_view_all_users

@router.get("/admin/dashboard")
async def admin_dashboard(
    user: User = Depends(require_admin_role)
):
    return {"dashboard": "admin data"}

@router.get("/admin/users") 
async def list_users(
    user: User = Depends(require_view_all_users)
):
    return {"users": [...]}
```

### Method 3: Resource Ownership + Permission

```python
from app.utils.rbac import ResourceOwnerOrPermission

@router.get("/users/{user_id}/wallet")
async def get_wallet(
    user_id: int,
    user: User = Depends(ResourceOwnerOrPermission(
        permission=Permission.VIEW_ALL_WALLETS,
        resource_owner_id_param="user_id"
    ))
):
    # Users can access their own wallet OR admins can access any wallet
    return {"wallet": "data"}
```

### Method 4: Manual Permission Checking

```python
from app.services.rbac_service import RBACService

@router.post("/some-endpoint")
async def some_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check permission manually
    if not await RBACService.has_permission(user, Permission.SOME_PERMISSION, db):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    # Proceed with operation
    return {"result": "success"}
```

## Admin API Endpoints

### User Management
- `GET /api/v1/admin/users` - List all users with filtering
- `POST /api/v1/admin/users` - Create new user
- `GET /api/v1/admin/users/{user_id}` - Get user details with permissions
- `PUT /api/v1/admin/users/{user_id}/role` - Change user role
- `PUT /api/v1/admin/users/{user_id}/suspend` - Suspend user
- `PUT /api/v1/admin/users/{user_id}/activate` - Activate user
- `PUT /api/v1/admin/users/{user_id}/points` - Adjust user points
- `DELETE /api/v1/admin/users/{user_id}` - Delete user

### System Management
- `GET /api/v1/admin/stats` - Get system RBAC statistics
- `GET /api/v1/admin/audit-logs` - View audit logs
- `GET /api/v1/admin/permissions` - List all permissions
- `GET /api/v1/admin/roles` - List all roles with permissions

### Permission Checking
- `POST /api/v1/admin/check-permission` - Check single permission
- `POST /api/v1/admin/check-permissions-bulk` - Check multiple permissions

## Security Features

### Critical Permissions
The system identifies 7 critical permissions that require extra security:
- DELETE_USER
- MODIFY_USER_ROLES
- SYSTEM_MAINTENANCE
- BACKUP_RESTORE
- DELETE_AUDIT_LOGS
- MANAGE_SECURITY_SETTINGS
- BAN_USERS

### Audit Logging
All administrative actions are automatically logged with:
- User who performed the action
- Action type and target resource
- Timestamp and IP address
- Detailed change information

### Role Management Rules
- Admins can manage all roles
- Moderators can only manage USER roles
- Users cannot manage any roles
- No one can demote themselves from ADMIN

### Resource Ownership
Users automatically have access to their own resources (jobs, wallets, etc.) even without explicit permissions. Higher-level roles can override this with appropriate permissions.

## Error Handling

### Authentication Errors (401)
- Missing or invalid JWT token
- Token has been blacklisted
- User not found

### Authorization Errors (403)
- Insufficient permissions for the requested action
- Role level too low for the endpoint
- Resource ownership violation

### Example Error Response
```json
{
    "error": {
        "code": 403,
        "message": "Permission required: view_all_users",
        "type": "insufficient_permissions"
    }
}
```

## Best Practices

### 1. Principle of Least Privilege
- Always use the most specific permission required
- Prefer permission-based over role-based dependencies when possible

### 2. Resource Ownership
- Use `ResourceOwnerOrPermission` for user-specific resources
- Allow users to access their own data by default

### 3. Audit Trail
- Critical operations are automatically logged
- Use the `log_access` parameter for additional logging

### 4. Error Messages
- Provide clear, actionable error messages
- Don't leak sensitive information about system structure

### 5. Testing
- Test all permission combinations
- Verify role hierarchy works correctly
- Test edge cases like suspended users

## Migration Guide

### For Existing Endpoints

1. **Replace simple admin checks:**
```python
# OLD
if not current_user.is_admin():
    raise HTTPException(status_code=403, detail="Admin required")

# NEW
user: User = Depends(RequireRole(UserRole.ADMIN))
```

2. **Add resource ownership checks:**
```python
# OLD
if current_user.user_id != target_user_id and not current_user.is_admin():
    raise HTTPException(status_code=403, detail="Access denied")

# NEW
user: User = Depends(ResourceOwnerOrPermission(
    permission=Permission.VIEW_ALL_USERS,
    resource_owner_id_param="user_id"
))
```

3. **Use specific permissions:**
```python
# OLD
user: User = Depends(get_current_admin_user)

# NEW
user: User = Depends(RequirePermission(Permission.SPECIFIC_PERMISSION))
```

## Testing the System

### Quick Test Commands
```bash
# Test core RBAC functionality
cd Backend
python -c "from app.core.permissions import *; print('RBAC loaded successfully')"

# Check role permissions
python -c "
from app.core.permissions import get_all_permissions_for_role
from app.models.user import UserRole
print(f'Admin permissions: {len(get_all_permissions_for_role(UserRole.ADMIN))}')
"
```

### Integration Testing
The system has been thoroughly tested and all core functionality passes validation:
- ✅ Role hierarchy works correctly
- ✅ Permission inheritance is proper
- ✅ Critical permissions are restricted
- ✅ Security validations pass
- ✅ All 36 permissions are correctly mapped

## Support & Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all new modules are properly imported
2. **Permission Denied**: Check user role and specific permissions required
3. **Database Issues**: Run migrations to ensure audit log table exists

### Debugging Tips
- Use `/api/v1/admin/check-permission` to test specific permissions
- Check audit logs for failed permission attempts
- Verify user status is ACTIVE (suspended users have no permissions)

---

**The Divine Whispers RBAC system is now fully functional and ready for production use!**