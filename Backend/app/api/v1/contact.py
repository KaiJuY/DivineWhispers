"""
Contact form API endpoints for user inquiries and support
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.utils.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactFormSubmission(BaseModel):
    """Contact form submission schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Contact person's name")
    email: EmailStr = Field(..., description="Contact email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Message subject")
    message: str = Field(..., min_length=10, max_length=2000, description="Message content")
    category: str = Field("general", description="Message category (general, support, bug_report, suggestion)")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Question about fortune readings",
                "message": "I have a question about how to interpret my fortune reading results. Could you provide some guidance?",
                "category": "support"
            }
        }


class ContactMessage(BaseModel):
    """Contact message response schema"""
    id: int
    name: str
    email: str
    subject: str
    message: str
    category: str
    status: str
    created_at: datetime
    user_id: Optional[int] = None
    
    class Config:
        from_attributes = True


@router.post("/submit", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    form_data: ContactFormSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Submit a contact form message"""
    try:
        # For now, we'll log the contact form submission
        # In a real implementation, you'd save this to a database table
        contact_info = {
            "name": form_data.name,
            "email": form_data.email,
            "subject": form_data.subject,
            "message": form_data.message,
            "category": form_data.category,
            "user_id": current_user.id if current_user else None,
            "submitted_at": datetime.utcnow().isoformat(),
            "ip_address": "unknown"  # Could be extracted from request
        }
        
        logger.info(f"Contact form submission received: {contact_info}")
        
        # Here you would typically:
        # 1. Save to database
        # 2. Send email notification to support team
        # 3. Send confirmation email to user
        # 4. Create support ticket in external system
        
        # Simulate saving to database with a mock ID
        mock_contact_id = hash(f"{form_data.email}_{datetime.utcnow().timestamp()}") % 10000
        
        # Send email notification (placeholder)
        await _send_contact_form_notification(contact_info, mock_contact_id)
        
        return MessageResponse(
            message=f"Thank you for your message! We have received your inquiry about '{form_data.subject}' and will respond within 24-48 hours.",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error processing contact form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact form. Please try again later."
        )


@router.get("/categories")
async def get_contact_categories():
    """Get available contact form categories"""
    categories = {
        "general": "General Inquiry",
        "support": "Technical Support",
        "bug_report": "Bug Report",
        "suggestion": "Feature Suggestion",
        "billing": "Billing Question",
        "fortune_reading": "Fortune Reading Question",
        "account": "Account Issue"
    }
    
    return {
        "categories": categories,
        "default": "general"
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: str = Field(..., min_length=10, max_length=1000),
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars"),
    feature_area: str = Field("general", description="Area of the app being reviewed"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit user feedback and rating"""
    try:
        feedback_data = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "feedback": feedback,
            "rating": rating,
            "feature_area": feature_area,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Feedback received from user {current_user.id}: {feedback_data}")
        
        # Here you would save feedback to database
        # and potentially trigger analytics or notifications
        
        return {
            "message": "Thank you for your feedback! Your input helps us improve Divine Whispers.",
            "rating_received": rating,
            "feedback_id": hash(f"{current_user.id}_{datetime.utcnow().timestamp()}") % 10000
        }
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


async def _send_contact_form_notification(contact_info: dict, contact_id: int):
    """Send notification about new contact form submission"""
    try:
        # Placeholder for email notification logic
        # In a real implementation, you would:
        # 1. Use an email service (SendGrid, AWS SES, etc.)
        # 2. Send to support team
        # 3. Send confirmation to user
        
        logger.info(f"Contact form notification sent for ID: {contact_id}")
        
        # Mock email content
        notification_content = f"""
New Contact Form Submission (ID: {contact_id})

From: {contact_info['name']} <{contact_info['email']}>
Subject: {contact_info['subject']}
Category: {contact_info['category']}

Message:
{contact_info['message']}

Submitted: {contact_info['submitted_at']}
User ID: {contact_info.get('user_id', 'Anonymous')}
"""
        
        logger.info(f"Email content prepared: {notification_content}")
        
    except Exception as e:
        logger.error(f"Error sending contact form notification: {e}")


@router.get("/faq")
async def get_faq():
    """Get frequently asked questions"""
    faqs = [
        {
            "id": 1,
            "category": "fortune_reading",
            "question": "How accurate are the fortune readings?",
            "answer": "Our fortune readings are based on ancient wisdom and traditional interpretations. They are meant for guidance and reflection, not absolute predictions. The accuracy depends on how well you connect with the guidance provided."
        },
        {
            "id": 2,
            "category": "technical",
            "question": "How do I use the interactive chat feature?",
            "answer": "After receiving your fortune, you can click on the chat icon to start an interactive conversation. Ask specific questions about your reading, and our AI-powered assistant will provide personalized interpretations."
        },
        {
            "id": 3,
            "category": "account",
            "question": "How do points work?",
            "answer": "Points are used to access premium features like detailed fortune interpretations and interactive chat sessions. You can purchase points through our secure payment system or earn them through daily check-ins."
        },
        {
            "id": 4,
            "category": "fortune_reading",
            "question": "What's the difference between the different deities?",
            "answer": "Each deity specializes in different aspects of life: Guan Yin for compassion and guidance, Mazu for protection, Guan Yu for business and loyalty, Yue Lao for love and relationships, and others. Choose based on your specific question or area of concern."
        },
        {
            "id": 5,
            "category": "technical",
            "question": "Can I save my fortune readings?",
            "answer": "Yes! All your fortune readings are automatically saved in your account profile under the 'Reports' section. You can access them anytime to review past guidance."
        }
    ]
    
    categories = list(set([faq["category"] for faq in faqs]))
    
    return {
        "faqs": faqs,
        "categories": categories,
        "total_count": len(faqs)
    }