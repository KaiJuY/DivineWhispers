"""
Authentication service for handling user authentication business logic
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import SecurityManager
from app.models.user import User, UserRole, UserStatus
from app.models.audit_log import AuditLog
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    LoginResponse,
    PasswordChange
)


class AuthService:
    """Authentication service for user management and JWT tokens"""
    
    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: UserRegister,
        client_ip: str = "unknown"
    ) -> Tuple[User, TokenResponse]:
        """Register a new user and return user with tokens"""
        
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Validate password strength
        password_validation = SecurityManager.validate_password_strength(user_data.password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Create new user
        hashed_password = SecurityManager.hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            points_balance=settings.DEFAULT_USER_POINTS
        )
        
        db.add(new_user)
        await db.flush()  # Get user_id without committing
        
        # Create tokens
        token_data = {
            "sub": str(new_user.user_id),
            "email": new_user.email,
            "role": new_user.role.value,
            "status": new_user.status.value
        }
        
        access_token, refresh_token = SecurityManager.create_token_pair(token_data)
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=new_user.user_id,
            action="user_register",
            resource_type="user",
            resource_id=str(new_user.user_id),
            ip_address=client_ip,
            details={"email": new_user.email}
        )
        db.add(audit_log)
        
        await db.commit()
        
        # Create token response
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        return new_user, tokens
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        login_data: UserLogin,
        client_ip: str = "unknown"
    ) -> LoginResponse:
        """Authenticate user and return user info with tokens"""
        
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Log failed login attempt
            audit_log = AuditLog(
                action="login_failed",
                resource_type="user",
                ip_address=client_ip,
                details={"email": login_data.email, "reason": "user_not_found"}
            )
            db.add(audit_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not SecurityManager.verify_password(login_data.password, user.password_hash):
            # Log failed login attempt
            audit_log = AuditLog(
                user_id=user.user_id,
                action="login_failed",
                resource_type="user",
                resource_id=str(user.user_id),
                ip_address=client_ip,
                details={"email": user.email, "reason": "invalid_password"}
            )
            db.add(audit_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active():
            # Log failed login attempt
            audit_log = AuditLog(
                user_id=user.user_id,
                action="login_failed",
                resource_type="user",
                resource_id=str(user.user_id),
                ip_address=client_ip,
                details={"email": user.email, "reason": "inactive_user", "status": user.status.value}
            )
            db.add(audit_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Create tokens
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value
        }
        
        access_token, refresh_token = SecurityManager.create_token_pair(token_data)
        
        # Log successful login
        audit_log = AuditLog(
            user_id=user.user_id,
            action="login_success",
            resource_type="user",
            resource_id=str(user.user_id),
            ip_address=client_ip,
            details={"email": user.email}
        )
        db.add(audit_log)
        await db.commit()
        
        # Create response objects
        user_response = UserResponse.from_orm(user)
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        return LoginResponse(user=user_response, tokens=tokens)
    
    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str,
        client_ip: str = "unknown"
    ) -> TokenResponse:
        """Refresh access token using refresh token"""
        
        # Verify refresh token
        try:
            payload = await SecurityManager.verify_token_with_blacklist(
                db, refresh_token, "refresh"
            )
        except HTTPException as e:
            # Log failed token refresh
            audit_log = AuditLog(
                action="token_refresh_failed",
                resource_type="token",
                ip_address=client_ip,
                details={"reason": str(e.detail)}
            )
            db.add(audit_log)
            await db.commit()
            raise e
        
        user_id = int(payload["sub"])
        
        # Get current user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active():
            # Blacklist the refresh token
            await SecurityManager.blacklist_token(
                db,
                payload["jti"],
                "refresh",
                user_id,
                datetime.fromtimestamp(payload["exp"]),
                "user_inactive"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new token pair (rotate refresh token)
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value
        }
        
        new_access_token, new_refresh_token = SecurityManager.create_token_pair(token_data)
        
        # Blacklist the old refresh token
        await SecurityManager.blacklist_token(
            db,
            payload["jti"],
            "refresh",
            user_id,
            datetime.fromtimestamp(payload["exp"]),
            "token_rotated"
        )
        
        # Log successful token refresh
        audit_log = AuditLog(
            user_id=user.user_id,
            action="token_refresh_success",
            resource_type="token",
            resource_id=payload["jti"],
            ip_address=client_ip,
            details={"email": user.email}
        )
        db.add(audit_log)
        await db.commit()
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
    
    @staticmethod
    async def logout_user(
        db: AsyncSession,
        access_token: str,
        refresh_token: Optional[str] = None,
        client_ip: str = "unknown"
    ) -> None:
        """Logout user by blacklisting tokens"""
        
        # Verify and blacklist access token
        try:
            access_payload = await SecurityManager.verify_token_with_blacklist(
                db, access_token, "access"
            )
            
            user_id = int(access_payload["sub"])
            
            # Blacklist access token
            await SecurityManager.blacklist_token(
                db,
                access_payload["jti"],
                "access",
                user_id,
                datetime.fromtimestamp(access_payload["exp"]),
                "logout"
            )
            
            # Blacklist refresh token if provided
            if refresh_token:
                try:
                    refresh_payload = SecurityManager.verify_token(refresh_token, "refresh")
                    await SecurityManager.blacklist_token(
                        db,
                        refresh_payload["jti"],
                        "refresh",
                        user_id,
                        datetime.fromtimestamp(refresh_payload["exp"]),
                        "logout"
                    )
                except HTTPException:
                    # Refresh token is invalid, but we can still proceed with access token logout
                    pass
            
            # Log successful logout
            audit_log = AuditLog(
                user_id=user_id,
                action="logout_success",
                resource_type="user",
                resource_id=str(user_id),
                ip_address=client_ip,
                details={"tokens_revoked": 1 if not refresh_token else 2}
            )
            db.add(audit_log)
            await db.commit()
            
        except HTTPException as e:
            # Log failed logout
            audit_log = AuditLog(
                action="logout_failed",
                resource_type="token",
                ip_address=client_ip,
                details={"reason": str(e.detail)}
            )
            db.add(audit_log)
            await db.commit()
            raise e
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: int,
        password_data: PasswordChange,
        client_ip: str = "unknown"
    ) -> None:
        """Change user password"""
        
        # Get user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not SecurityManager.verify_password(password_data.current_password, user.password_hash):
            # Log failed password change
            audit_log = AuditLog(
                user_id=user_id,
                action="password_change_failed",
                resource_type="user",
                resource_id=str(user_id),
                ip_address=client_ip,
                details={"reason": "invalid_current_password"}
            )
            db.add(audit_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        password_validation = SecurityManager.validate_password_strength(password_data.new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "New password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Update password
        user.password_hash = SecurityManager.hash_password(password_data.new_password)
        
        # Log successful password change
        audit_log = AuditLog(
            user_id=user_id,
            action="password_change_success",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=client_ip,
            details={"email": user.email}
        )
        db.add(audit_log)
        await db.commit()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """Clean up expired blacklisted tokens"""
        return await SecurityManager.cleanup_expired_tokens(db)
    
    @staticmethod
    async def update_user_profile(
        user_id: int,
        profile_data,  # UserProfileUpdate type
        db: AsyncSession
    ) -> Optional[User]:
        """Update user profile information"""
        # Get user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Update only provided fields
        update_fields = profile_data.dict(exclude_unset=True)
        
        for field, value in update_fields.items():
            if field == "email" and value != user.email:
                # Check if new email is already taken
                existing_result = await db.execute(
                    select(User).where(User.email == value)
                )
                existing_user = existing_result.scalar_one_or_none()
                if existing_user and existing_user.user_id != user_id:
                    raise ValueError("Email address is already in use")
            
            # Handle special fields
            if field == "birth_date" and value:
                try:
                    from datetime import datetime
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError("Invalid birth_date format. Use YYYY-MM-DD")
            
            if field == "preferred_language" and value:
                if value not in ["zh", "en", "jp"]:
                    raise ValueError("Invalid preferred_language. Must be one of: zh, en, jp")
            
            # Update the field
            if hasattr(user, field):
                setattr(user, field, value)
        
        # Save changes
        await db.commit()
        await db.refresh(user)
        
        return user