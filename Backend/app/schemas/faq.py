"""
FAQ-related Pydantic schemas for API requests and responses
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.faq import FAQCategory


class FAQCreate(BaseModel):
    """Schema for creating a new FAQ"""
    category: FAQCategory = Field(..., description="FAQ category")
    question: str = Field(..., min_length=10, max_length=500, description="FAQ question")
    answer: str = Field(..., min_length=20, max_length=5000, description="FAQ answer")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    display_order: Optional[int] = Field(0, description="Display order")
    is_published: Optional[bool] = Field(True, description="Whether FAQ is published")
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "fortune_reading",
                "question": "How accurate are the fortune readings?",
                "answer": "Our fortune readings are based on ancient wisdom and traditional interpretations...",
                "tags": "accuracy, reliability, divination",
                "display_order": 1,
                "is_published": True
            }
        }


class FAQUpdate(BaseModel):
    """Schema for updating an existing FAQ"""
    category: Optional[FAQCategory] = Field(None, description="FAQ category")
    question: Optional[str] = Field(None, min_length=10, max_length=500, description="FAQ question")
    answer: Optional[str] = Field(None, min_length=20, max_length=5000, description="FAQ answer")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    display_order: Optional[int] = Field(None, description="Display order")
    is_published: Optional[bool] = Field(None, description="Whether FAQ is published")


class FAQResponse(BaseModel):
    """Schema for FAQ response"""
    id: int
    category: str
    question: str
    answer: str
    slug: str
    tags: Optional[str] = None
    is_published: bool
    display_order: int
    view_count: int
    helpful_votes: int
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FAQListResponse(BaseModel):
    """Schema for listing FAQs"""
    faqs: List[FAQResponse]
    total_count: int
    categories: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "faqs": [
                    {
                        "id": 1,
                        "category": "fortune_reading",
                        "question": "How accurate are the fortune readings?",
                        "answer": "Our fortune readings are based on ancient wisdom...",
                        "slug": "how-accurate-fortune-readings",
                        "is_published": True,
                        "view_count": 150,
                        "helpful_votes": 25
                    }
                ],
                "total_count": 1,
                "categories": ["fortune_reading", "technical", "account"]
            }
        }


class FAQFeedbackCreate(BaseModel):
    """Schema for creating FAQ feedback"""
    faq_id: int = Field(..., description="FAQ ID")
    is_helpful: bool = Field(..., description="Whether the FAQ was helpful")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "faq_id": 1,
                "is_helpful": True,
                "feedback_text": "This answered my question perfectly!"
            }
        }


class FAQFeedbackResponse(BaseModel):
    """Schema for FAQ feedback response"""
    id: int
    faq_id: int
    user_id: Optional[int] = None
    is_helpful: bool
    feedback_text: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FAQAnalytics(BaseModel):
    """Schema for FAQ analytics data"""
    total_faqs: int
    published_faqs: int
    total_views: int
    total_feedback: int
    helpful_percentage: float
    top_categories: List[dict]
    recent_feedback: List[FAQFeedbackResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_faqs": 25,
                "published_faqs": 23,
                "total_views": 1250,
                "total_feedback": 85,
                "helpful_percentage": 78.5,
                "top_categories": [
                    {"category": "fortune_reading", "count": 8},
                    {"category": "account", "count": 6}
                ],
                "recent_feedback": []
            }
        }