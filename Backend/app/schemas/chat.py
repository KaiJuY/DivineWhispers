"""
Chat-related Pydantic schemas for API requests and responses
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.chat_message import MessageType


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    session_name: Optional[str] = Field(None, max_length=200, description="Optional name for the chat session")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context data (deity, fortune, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_name": "Fortune Reading with Guan Yin",
                "context_data": {
                    "deity_id": "guan_yin", 
                    "fortune_number": 42,
                    "poem_id": "GuanYin100_42",
                    "initial_question": "What does my future hold?"
                }
            }
        }


class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message"""
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Can you explain what this fortune means for my career?",
                "metadata": {"source": "web", "language": "en"}
            }
        }


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    session_id: int
    user_id: int
    message_type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    @model_validator(mode='before')
    @classmethod
    def map_message_metadata(cls, values):
        """Map message_metadata from model to metadata for schema"""
        if hasattr(values, 'message_metadata'):
            # Handle SQLAlchemy model objects
            values_dict = values.__dict__.copy() if hasattr(values, '__dict__') else values
            if 'message_metadata' in values_dict:
                values_dict['metadata'] = values_dict.get('message_metadata')
            return values_dict
        elif isinstance(values, dict) and 'message_metadata' in values:
            # Handle dict inputs
            values['metadata'] = values.get('message_metadata')
        return values

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "session_id": 45,
                "user_id": 67,
                "message_type": "user",
                "content": "What does fortune number 42 mean?",
                "metadata": {"language": "en"},
                "created_at": "2024-01-15T14:30:00Z"
            }
        }


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: int
    user_id: int
    session_name: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: Optional[int] = None
    last_message: Optional[ChatMessageResponse] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 45,
                "user_id": 67,
                "session_name": "Fortune Reading with Guan Yin",
                "context_data": {"deity_id": "guan_yin", "fortune_number": 42},
                "created_at": "2024-01-15T14:00:00Z",
                "updated_at": "2024-01-15T14:30:00Z",
                "is_active": True,
                "message_count": 8
            }
        }


class ChatSessionListResponse(BaseModel):
    """Schema for listing chat sessions"""
    sessions: List[ChatSessionResponse]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": 45,
                        "user_id": 67,
                        "session_name": "Fortune Reading with Guan Yin",
                        "created_at": "2024-01-15T14:00:00Z",
                        "updated_at": "2024-01-15T14:30:00Z",
                        "is_active": True,
                        "message_count": 8
                    }
                ],
                "total_count": 1
            }
        }


class ChatMessageListResponse(BaseModel):
    """Schema for listing chat messages"""
    messages: List[ChatMessageResponse]
    total_count: int
    has_more: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": 123,
                        "session_id": 45,
                        "user_id": 67,
                        "message_type": "user",
                        "content": "What does fortune number 42 mean?",
                        "created_at": "2024-01-15T14:30:00Z"
                    }
                ],
                "total_count": 8,
                "has_more": False
            }
        }


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str = Field(..., description="Message type (chat_message, typing, error, etc.)")
    session_id: Optional[int] = Field(None, description="Chat session ID")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "chat_message",
                "session_id": 45,
                "data": {
                    "message": "Your fortune suggests...",
                    "is_streaming": True,
                    "chunk_id": 1
                },
                "timestamp": "2024-01-15T14:30:00Z"
            }
        }


class FortuneConversationCreate(BaseModel):
    """Schema for starting a fortune conversation"""
    deity_id: str = Field(..., description="Deity ID for the reading")
    fortune_number: Optional[int] = Field(None, ge=1, le=100, description="Specific fortune number")
    initial_question: str = Field(..., min_length=1, max_length=500, description="User's initial question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "deity_id": "guan_yin",
                "fortune_number": 42,
                "initial_question": "What guidance do you have for my career decisions?"
            }
        }