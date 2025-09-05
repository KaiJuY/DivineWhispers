"""
Chat Message Model - Stores interactive chat conversations
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class MessageType(str, Enum):
    """Message type enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    """Chat session model for grouping related messages"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    session_name = Column(String(200), nullable=True)
    context_data = Column(JSON, nullable=True)  # Store fortune context, deity info, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, name='{self.session_name}')>"


class ChatMessage(Base):
    """Chat message model for storing individual messages"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    
    message_type = Column(String(20), nullable=False, default=MessageType.USER)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)  # Store token count, model used, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type={self.message_type}, content='{self.content[:50]}...')>"