"""
Authentication schema models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.user import UserRole, UserStatus


class TokenType(str, Enum):
    """Token type enumeration for responses"""
    BEARER = "bearer"


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="User password (minimum 6 characters)"
    )
    confirm_password: str = Field(..., description="Password confirmation")
    
    # Optional profile fields
    username: Optional[str] = Field(None, max_length=50, description="Username (optional)")
    birth_date: Optional[str] = Field(None, description="Birth date (YYYY-MM-DD format)")
    gender: Optional[str] = Field(None, max_length=20, description="Gender (optional)")
    location: Optional[str] = Field(None, max_length=100, description="Location (optional)")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123",
                "confirm_password": "SecurePassword123",
                "username": "JohnDoe",
                "birth_date": "1990-01-01",
                "gender": "Male",
                "location": "San Francisco, CA"
            }
        }


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123"
            }
        }


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenRevoke(BaseModel):
    """Token revocation request schema"""
    token: Optional[str] = Field(None, description="Specific token to revoke (optional)")
    revoke_all: bool = Field(False, description="Revoke all user tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "revoke_all": False
            }
        }


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: TokenType = Field(TokenType.BEARER, description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_expires_in": 604800
            }
        }


class UserResponse(BaseModel):
    """User response schema"""
    user_id: int = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="User account status")
    points_balance: int = Field(..., description="User points balance")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Profile fields (optional)
    full_name: Optional[str] = Field(None, description="User's full name")
    phone: Optional[str] = Field(None, description="Phone number")
    birth_date: Optional[str] = Field(None, description="Birth date (YYYY-MM-DD format)")
    location: Optional[str] = Field(None, description="User location")
    preferred_language: Optional[str] = Field(None, description="Preferred language")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "email": "user@example.com",
                "role": "user",
                "status": "active",
                "points_balance": 100,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "full_name": "John Doe",
                "phone": "+1234567890",
                "birth_date": "1990-01-01",
                "location": "New York, USA",
                "preferred_language": "en"
            }
        }


class LoginResponse(BaseModel):
    """Login response schema combining tokens and user info"""
    user: UserResponse = Field(..., description="User information")
    tokens: TokenResponse = Field(..., description="Authentication tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "user_id": 123,
                    "email": "user@example.com",
                    "role": "user",
                    "status": "active",
                    "points_balance": 100,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "refresh_expires_in": 604800
                }
            }
        }


class PasswordChange(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (minimum 8 characters)"
    )
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPassword123",
                "new_password": "NewSecurePassword456",
                "confirm_new_password": "NewSecurePassword456"
            }
        }


class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="Email address for password reset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (minimum 8 characters)"
    )
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "reset_token": "secure-reset-token-here",
                "new_password": "NewSecurePassword456",
                "confirm_new_password": "NewSecurePassword456"
            }
        }


class AuthErrorResponse(BaseModel):
    """Authentication error response schema"""
    error: dict = Field(..., description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": 401,
                    "message": "Invalid credentials",
                    "type": "authentication_error"
                }
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "success": True
            }
        }


class UserProfileUpdate(BaseModel):
    """User profile update request schema"""
    email: Optional[EmailStr] = Field(None, description="Updated email address")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    birth_date: Optional[str] = Field(None, description="Birth date (YYYY-MM-DD format)")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    preferred_language: Optional[str] = Field(None, max_length=10, description="Preferred language (zh, en, jp)")
    notification_preferences: Optional[dict] = Field(None, description="Notification preferences")
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "phone": "+1234567890",
                "birth_date": "1990-01-01",
                "location": "New York, USA",
                "preferred_language": "en",
                "notification_preferences": {
                    "email_notifications": True,
                    "push_notifications": False
                }
            }
        }