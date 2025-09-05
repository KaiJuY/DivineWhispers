"""
Chat Service - Handles interactive chat conversations and WebSocket communications
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.models.chat_message import ChatSession, ChatMessage, MessageType
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate, ChatMessageCreate, ChatSessionResponse, 
    ChatMessageResponse, FortuneConversationCreate
)
from app.services.poem_service import poem_service
from app.services.deity_service import deity_service
from app.utils.websocket import websocket_manager

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and interactive conversations"""
    
    @staticmethod
    async def create_session(
        user_id: int,
        session_data: ChatSessionCreate,
        db: AsyncSession
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            user_id=user_id,
            session_name=session_data.session_name,
            context_data=session_data.context_data or {}
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created chat session {session.id} for user {user_id}")
        return session
    
    @staticmethod
    async def get_user_sessions(
        user_id: int,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True
    ) -> tuple[List[ChatSession], int]:
        """Get user's chat sessions with message count"""
        query = select(ChatSession).where(ChatSession.user_id == user_id)
        
        if active_only:
            query = query.where(ChatSession.is_active == True)
        
        query = query.order_by(desc(ChatSession.updated_at))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.scalar(count_query)
        
        # Get sessions with pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        return list(sessions), total_count
    
    @staticmethod
    async def get_session_messages(
        session_id: int,
        user_id: int,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[ChatMessage], int]:
        """Get messages for a chat session"""
        # Verify session belongs to user
        session_query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        session = await db.scalar(session_query)
        
        if not session:
            raise ValueError("Session not found or access denied")
        
        # Get messages
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.is_deleted == False
        ).order_by(ChatMessage.created_at)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.scalar(count_query)
        
        # Get messages with pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return list(messages), total_count
    
    @staticmethod
    async def add_message(
        session_id: int,
        user_id: int,
        message_data: ChatMessageCreate,
        message_type: MessageType,
        db: AsyncSession
    ) -> ChatMessage:
        """Add a message to a chat session"""
        # Verify session exists and belongs to user
        session_query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        session = await db.scalar(session_query)
        
        if not session:
            raise ValueError("Session not found or access denied")
        
        # Create message
        message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            message_type=message_type,
            content=message_data.content,
            metadata=message_data.metadata or {}
        )
        
        db.add(message)
        
        # Update session timestamp
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Added {message_type} message to session {session_id}")
        return message
    
    @staticmethod
    async def start_fortune_conversation(
        user_id: int,
        conversation_data: FortuneConversationCreate,
        db: AsyncSession
    ) -> tuple[ChatSession, ChatMessage]:
        """Start a new fortune conversation with context"""
        # Get deity information
        deity = await deity_service.get_deity_by_id(conversation_data.deity_id)
        if not deity:
            raise ValueError("Invalid deity ID")
        
        # Get fortune data if specific number provided
        fortune_data = None
        if conversation_data.fortune_number:
            temple_name = deity_service.get_temple_name(conversation_data.deity_id)
            poem_id = f"{temple_name}_{conversation_data.fortune_number}"
            fortune_data = await poem_service.get_poem_by_id(poem_id)
        
        # Create session with context
        context_data = {
            "deity_id": conversation_data.deity_id,
            "deity_name": deity.deity.name,
            "deity_chinese_name": deity.deity.chinese_name,
            "fortune_number": conversation_data.fortune_number,
            "conversation_type": "fortune_reading"
        }
        
        if fortune_data:
            context_data.update({
                "poem_id": fortune_data.id,
                "poem_title": fortune_data.title,
                "poem_fortune": fortune_data.fortune,
                "poem_content": fortune_data.poem
            })
        
        session_create = ChatSessionCreate(
            session_name=f"Fortune Reading - {deity.deity.name}",
            context_data=context_data
        )
        
        session = await ChatService.create_session(user_id, session_create, db)
        
        # Add initial user message
        initial_message_data = ChatMessageCreate(
            content=conversation_data.initial_question,
            metadata={"conversation_starter": True}
        )
        
        initial_message = await ChatService.add_message(
            session.id, user_id, initial_message_data, MessageType.USER, db
        )
        
        return session, initial_message
    
    @staticmethod
    async def generate_fortune_response(
        session_id: int,
        user_message: str,
        user_id: int,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """Generate streaming fortune response using LLM"""
        # Get session with context
        session_query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).options(selectinload(ChatSession.messages))
        
        session = await db.scalar(session_query)
        if not session:
            raise ValueError("Session not found")
        
        context_data = session.context_data or {}
        
        # Build conversation context
        conversation_history = []
        for msg in session.messages[-10:]:  # Last 10 messages for context
            conversation_history.append({
                "role": "user" if msg.message_type == MessageType.USER else "assistant",
                "content": msg.content
            })
        
        # Get fortune context if available
        fortune_context = ""
        if context_data.get("poem_content"):
            fortune_context = f"""
Fortune Poem: "{context_data.get('poem_title', '')}"
Content: {context_data.get('poem_content', '')}
Fortune Type: {context_data.get('poem_fortune', '')}
Deity: {context_data.get('deity_name', '')} ({context_data.get('deity_chinese_name', '')})
"""
        
        # Create system prompt for fortune interpretation
        system_prompt = f"""You are a wise fortune interpreter channeling the wisdom of {context_data.get('deity_name', 'the divine')}. 
        
{fortune_context}

Previous conversation context: {json.dumps(conversation_history[-5:], ensure_ascii=False)}

Provide thoughtful, compassionate guidance based on the fortune poem and the user's questions. 
Speak in a warm, mystical tone while being practical and helpful. Keep responses conversational and engaging.
Reference the specific fortune details when relevant."""
        
        try:
            # Use the existing fortune system for generation
            if poem_service.fortune_system:
                # This would integrate with the LLM streaming
                full_response = f"""Based on your fortune reading and the wisdom of {context_data.get('deity_name', 'the divine')}, I can offer this guidance:

The poem "{context_data.get('poem_title', '')}" speaks to your situation. {context_data.get('poem_content', '')}

Regarding your question: "{user_message}"

{context_data.get('poem_fortune', 'The energies')} surrounding this reading suggest that this is a time for reflection and mindful action. The divine guidance indicates that your path forward requires both patience and determination.

Consider how the ancient wisdom applies to your current circumstances. What aspects of this reading resonate most deeply with your current situation?"""
            else:
                # Fallback response
                full_response = f"""Thank you for your question about "{user_message}". 

Based on your fortune reading with {context_data.get('deity_name', 'the divine')}, I sense that this is an important moment for reflection. The wisdom suggests looking within for answers while remaining open to guidance from unexpected sources.

How does this resonate with your current situation?"""
            
            # Simulate streaming by yielding chunks
            words = full_response.split()
            current_chunk = ""
            
            for i, word in enumerate(words):
                current_chunk += word + " "
                
                # Send chunk every 3-5 words
                if i % 4 == 0 and current_chunk.strip():
                    yield current_chunk.strip()
                    current_chunk = ""
            
            # Send remaining chunk
            if current_chunk.strip():
                yield current_chunk.strip()
                
        except Exception as e:
            logger.error(f"Error generating fortune response: {e}")
            yield "I apologize, but I'm having difficulty accessing the divine wisdom at this moment. Please try again shortly."
    
    @staticmethod
    async def send_websocket_message(
        user_id: int,
        message_type: str,
        data: Dict,
        session_id: Optional[int] = None
    ):
        """Send message via WebSocket to user"""
        message = {
            "type": message_type,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.send_personal_message(
            json.dumps(message), str(user_id)
        )


# Global service instance
chat_service = ChatService()