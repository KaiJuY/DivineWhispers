"""
Chat API endpoints for interactive fortune conversations
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.deps import get_db, get_current_user
from app.models.user import User
from app.models.chat_message import MessageType
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionListResponse,
    ChatMessageCreate, ChatMessageResponse, ChatMessageListResponse,
    FortuneConversationCreate
)
from app.services.chat_service import chat_service
from app.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    try:
        session = await chat_service.create_session(
            user_id=current_user.id,
            session_data=session_data,
            db=db
        )
        
        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            session_name=session.session_name,
            context_data=session.context_data,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.get("/sessions", response_model=ChatSessionListResponse)
async def get_chat_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat sessions"""
    try:
        sessions, total_count = await chat_service.get_user_sessions(
            user_id=current_user.id,
            db=db,
            limit=limit,
            offset=offset,
            active_only=active_only
        )
        
        session_responses = []
        for session in sessions:
            session_responses.append(ChatSessionResponse(
                id=session.id,
                user_id=session.user_id,
                session_name=session.session_name,
                context_data=session.context_data,
                created_at=session.created_at,
                updated_at=session.updated_at,
                is_active=session.is_active,
                message_count=len(session.messages) if hasattr(session, 'messages') else 0
            ))
        
        return ChatSessionListResponse(
            sessions=session_responses,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions")


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def get_session_messages(
    session_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a chat session"""
    try:
        messages, total_count = await chat_service.get_session_messages(
            session_id=session_id,
            user_id=current_user.id,
            db=db,
            limit=limit,
            offset=offset
        )
        
        message_responses = []
        for message in messages:
            message_responses.append(ChatMessageResponse(
                id=message.id,
                session_id=message.session_id,
                user_id=message.user_id,
                message_type=message.message_type,
                content=message.content,
                metadata=message.metadata,
                created_at=message.created_at
            ))
        
        return ChatMessageListResponse(
            messages=message_responses,
            total_count=total_count,
            has_more=len(messages) == limit
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a chat session"""
    try:
        # Add user message
        user_message = await chat_service.add_message(
            session_id=session_id,
            user_id=current_user.id,
            message_data=message_data,
            message_type=MessageType.USER,
            db=db
        )
        
        # Trigger assistant response (this will be handled via WebSocket)
        # For now, we'll just return the user message
        await chat_service.send_websocket_message(
            user_id=current_user.id,
            message_type="message_received",
            data={"message": "Processing your message..."},
            session_id=session_id
        )
        
        return ChatMessageResponse(
            id=user_message.id,
            session_id=user_message.session_id,
            user_id=user_message.user_id,
            message_type=user_message.message_type,
            content=user_message.content,
            metadata=user_message.metadata,
            created_at=user_message.created_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.post("/fortune-conversation", response_model=Dict[str, Any])
async def start_fortune_conversation(
    conversation_data: FortuneConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new fortune reading conversation"""
    try:
        # Check if user has enough points (if this is a paid feature)
        # user_points = await wallet_service.get_user_points(current_user.id, db)
        # required_points = 5  # Points cost for interactive chat
        # if user_points < required_points:
        #     raise HTTPException(status_code=402, detail="Insufficient points")
        
        session, initial_message = await chat_service.start_fortune_conversation(
            user_id=current_user.id,
            conversation_data=conversation_data,
            db=db
        )
        
        return {
            "session_id": session.id,
            "session_name": session.session_name,
            "context": session.context_data,
            "initial_message": {
                "id": initial_message.id,
                "content": initial_message.content,
                "created_at": initial_message.created_at
            },
            "message": "Fortune conversation started. You can now chat interactively!"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting fortune conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start fortune conversation")


@router.get("/sessions/{session_id}/stream")
async def stream_chat_response(
    session_id: int,
    message: str = Query(..., description="User message to respond to"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stream fortune response for a user message (SSE endpoint)"""
    try:
        async def generate_stream():
            async for chunk in chat_service.generate_fortune_response(
                session_id=session_id,
                user_message=message,
                user_id=current_user.id,
                db=db
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error streaming chat response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")


@router.delete("/sessions/{session_id}")
async def deactivate_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate (soft delete) a chat session"""
    try:
        from sqlalchemy import select, update
        from app.models.chat_message import ChatSession
        
        # Check if session exists and belongs to user
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Deactivate session
        await db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(is_active=False)
        )
        await db.commit()
        
        return {"message": "Chat session deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate session")