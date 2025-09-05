"""
FAQ Model - Manages frequently asked questions and answers
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class FAQCategory(str, Enum):
    """FAQ category enumeration"""
    GENERAL = "general"
    TECHNICAL = "technical"
    FORTUNE_READING = "fortune_reading"
    ACCOUNT = "account"
    BILLING = "billing"
    CHAT = "chat"
    SUPPORT = "support"


class FAQ(Base):
    """FAQ model for storing questions and answers"""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, default=FAQCategory.GENERAL)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    
    # SEO and organization
    slug = Column(String(200), unique=True, nullable=False, index=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Status and ordering
    is_published = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    
    # Admin tracking
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<FAQ(id={self.id}, category='{self.category}', question='{self.question[:50]}...')>"


class FAQFeedback(Base):
    """FAQ feedback model for tracking user feedback on FAQs"""
    __tablename__ = "faq_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    faq_id = Column(Integer, ForeignKey("faqs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)  # Allow anonymous feedback
    
    is_helpful = Column(Boolean, nullable=False)
    feedback_text = Column(Text, nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    faq = relationship("FAQ")
    user = relationship("User")
    
    def __repr__(self):
        return f"<FAQFeedback(id={self.id}, faq_id={self.faq_id}, helpful={self.is_helpful})>"