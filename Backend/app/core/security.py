"""
Security utilities for JWT tokens and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import secrets
import string
import uuid

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Security utilities manager"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with unique JTI for blacklisting"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add unique JWT ID for blacklisting and timestamps
        jti = str(uuid.uuid4())
        iat = datetime.utcnow()
        
        to_encode.update({
            "exp": expire,
            "iat": iat,
            "jti": jti,
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token with unique JTI for blacklisting"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Add unique JWT ID for blacklisting and timestamps
        jti = str(uuid.uuid4())
        iat = datetime.utcnow()
        
        to_encode.update({
            "exp": expire,
            "iat": iat,
            "jti": jti,
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_token_pair(user_data: Dict[str, Any]) -> Tuple[str, str]:
        """Create access and refresh token pair for a user"""
        access_token = SecurityManager.create_access_token(user_data)
        refresh_token = SecurityManager.create_refresh_token(user_data)
        return access_token, refresh_token
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration"
                )
            
            if datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            # Check JTI exists
            jti = payload.get("jti")
            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing JWT ID"
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}"
            )
    
    @staticmethod
    async def is_token_blacklisted(db: AsyncSession, jti: str) -> bool:
        """Check if a token is blacklisted"""
        from app.models.token_blacklist import TokenBlacklist
        
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        blacklisted_token = result.scalar_one_or_none()
        return blacklisted_token is not None
    
    @staticmethod
    async def blacklist_token(
        db: AsyncSession,
        jti: str,
        token_type: str,
        user_id: int,
        expires_at: datetime,
        reason: str = "logout"
    ) -> None:
        """Add a token to the blacklist"""
        from app.models.token_blacklist import TokenBlacklist, TokenType
        
        # Convert string token type to enum
        token_type_enum = TokenType.ACCESS if token_type == "access" else TokenType.REFRESH
        
        blacklisted_token = TokenBlacklist(
            jti=jti,
            token_type=token_type_enum,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason
        )
        
        db.add(blacklisted_token)
        await db.commit()
    
    @staticmethod
    async def blacklist_all_user_tokens(
        db: AsyncSession,
        user_id: int,
        reason: str = "security_breach"
    ) -> None:
        """Blacklist all existing tokens for a user (e.g., on security breach)"""
        # Note: This is a placeholder implementation
        # In a real scenario, you'd need to track all active tokens for a user
        # This could be done by storing tokens in the database when issued
        # or by adding user_id to the blacklist and checking during verification
        pass
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """Clean up expired tokens from blacklist (should be run periodically)"""
        from app.models.token_blacklist import TokenBlacklist
        
        result = await db.execute(
            delete(TokenBlacklist).where(
                TokenBlacklist.expires_at < datetime.utcnow()
            )
        )
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def verify_token_with_blacklist(
        db: AsyncSession,
        token: str,
        token_type: str = "access"
    ) -> Dict[str, Any]:
        """Verify token and check if it's blacklisted"""
        # First verify the token structure and signature
        payload = SecurityManager.verify_token(token, token_type)
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if await SecurityManager.is_token_blacklisted(db, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        return payload
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength according to settings"""
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SYMBOLS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """Generate a random secure password"""
        characters = string.ascii_letters + string.digits
        if settings.PASSWORD_REQUIRE_SYMBOLS:
            characters += "!@#$%^&*()_+-="
        
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure reset token"""
        return secrets.token_urlsafe(32)


# Convenience functions for backward compatibility
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    return SecurityManager.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    return SecurityManager.create_refresh_token(data, expires_delta)


def create_token_pair(user_data: Dict[str, Any]) -> Tuple[str, str]:
    """Create access and refresh token pair for a user"""
    return SecurityManager.create_token_pair(user_data)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify and decode JWT token"""
    return SecurityManager.verify_token(token, token_type)


async def verify_token_with_blacklist(
    db: AsyncSession,
    token: str,
    token_type: str = "access"
) -> Dict[str, Any]:
    """Verify token and check if it's blacklisted"""
    return await SecurityManager.verify_token_with_blacklist(db, token, token_type)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return SecurityManager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return SecurityManager.verify_password(plain_password, hashed_password)