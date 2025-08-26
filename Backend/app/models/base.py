"""
Base model class with common functionality for all database models
"""

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            comment="Record creation timestamp"
        )
    
    @declared_attr  
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
            comment="Record last update timestamp"
        )


class BaseModel(Base, TimestampMixin):
    """Base model class that includes common functionality"""
    __abstract__ = True
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict) -> None:
        """Update model instance from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model"""
        class_name = self.__class__.__name__
        primary_key_columns = [
            column.name for column in self.__table__.columns 
            if column.primary_key
        ]
        
        if primary_key_columns:
            pk_values = [
                f"{col}={getattr(self, col)}" 
                for col in primary_key_columns
            ]
            return f"<{class_name}({', '.join(pk_values)})>"
        
        return f"<{class_name}>"