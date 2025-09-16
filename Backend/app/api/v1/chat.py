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


@router.post("/fortune-conversation-test")
async def start_fortune_conversation_test():
    """Test endpoint without dependencies"""
    print("CLAUDE DEBUG: TEST ENDPOINT HIT - NO DEPENDENCIES!")
    return {"status": "success", "message": "Test endpoint reached"}

@router.post("/test-db-only")
async def test_db_dependency(db: AsyncSession = Depends(get_db)):
    """Test only database dependency"""
    print("CLAUDE DEBUG: DB DEPENDENCY TEST - SUCCESS!")
    return {"status": "success", "message": "Database dependency works"}

@router.post("/test-auth-only")
async def test_auth_dependency(current_user: User = Depends(get_current_user)):
    """Test only authentication dependency"""
    print(f"CLAUDE DEBUG: AUTH DEPENDENCY TEST - USER: {current_user.id}")
    return {"status": "success", "message": f"Auth dependency works for user {current_user.id}"}

@router.post("/test-steps")
async def test_steps(
    conversation_data: FortuneConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test each step individually"""
    print("="*50)
    print("CLAUDE DEBUG: TESTING EACH STEP")
    print("="*50)

    try:
        # Step 1: Test dependency injection
        print(f"STEP 1 - Dependencies OK - User: {current_user.id}, DB: {type(db)}")

        # Step 2: Test data parsing
        print(f"STEP 2 - Data parsed OK: deity_id={conversation_data.deity_id}, fortune_number={conversation_data.fortune_number}")

        # Step 3: Test deity service
        print("STEP 3 - Testing deity service...")
        deity = await deity_service.get_deity_by_id(conversation_data.deity_id)
        print(f"STEP 3 - Deity service result: {deity is not None}")
        if deity:
            print(f"STEP 3 - Deity name: {deity.deity.name}")

        # Step 4: Test temple name lookup
        print("STEP 4 - Testing temple name lookup...")
        temple_name = deity_service.get_temple_name(conversation_data.deity_id)
        print(f"STEP 4 - Temple name: {temple_name}")

        # Step 5: Test poem service if fortune number provided
        poem_service_working = False
        if conversation_data.fortune_number:
            print("STEP 5 - Testing poem service...")
            poem_id = f"{temple_name}_{conversation_data.fortune_number}"
            print(f"STEP 5 - Looking for poem: {poem_id}")

            try:
                # Check if poem service is initialized
                from app.services.poem_service import poem_service
                print(f"STEP 5 - Poem service initialized: {getattr(poem_service, '_initialized', False)}")

                if hasattr(poem_service, '_initialized') and poem_service._initialized:
                    fortune_data = await poem_service.get_poem_by_id(poem_id)
                    print(f"STEP 5 - Poem found: {fortune_data is not None}")
                    poem_service_working = True
                else:
                    print("STEP 5 - Poem service not initialized - this is likely the issue!")

            except Exception as poem_error:
                print(f"STEP 5 - Poem error: {type(poem_error).__name__}: {poem_error}")

        # Step 6: Test session creation
        print("STEP 6 - Testing session creation...")
        session_create = ChatSessionCreate(
            session_name=f"Test Session - {deity.deity.name}",
            context_data={"test": True}
        )
        session = await chat_service.create_session(current_user.id, session_create, db)
        print(f"STEP 6 - Session created: {session.id}")

        print("="*50)
        print("CLAUDE DEBUG: ALL STEPS COMPLETED!")
        print("="*50)

        return {
            "status": "success",
            "steps_completed": 6,
            "session_id": session.id,
            "deity_name": deity.deity.name if deity else None,
            "temple_name": temple_name,
            "poem_service_working": poem_service_working,
            "diagnosis": "Poem service initialization failure is likely the root cause" if not poem_service_working else "All services working"
        }

    except Exception as e:
        print(f"CLAUDE DEBUG: ERROR in step test: {type(e).__name__}: {e}")
        logger.error(f"CLAUDE DEBUG: ERROR in step test: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Step test error: {str(e)}")

@router.post("/fortune-conversation", response_model=Dict[str, Any])
async def start_fortune_conversation(
    conversation_data: FortuneConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new fortune reading conversation"""
    print("="*80)
    print("CLAUDE ENDPOINT CALLED - FORTUNE CONVERSATION")
    print(f"Data received: {conversation_data}")
    print(f"User ID: {current_user.id}")
    print("="*80)

    logger.info(f"[FORTUNE-ENDPOINT] Called with data: {conversation_data}")
    logger.info(f"[FORTUNE-ENDPOINT] User: {current_user.id}")

    try:
        logger.info(f"[DEBUG] About to call chat_service.start_fortune_conversation")

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

        logger.info(f"[DEBUG] Successfully got session {session.id} and message {initial_message.id}")

        # Check if we have poem data in the session context
        poem_available = session.context_data.get("poem_content") is not None

        return {
            "session_id": session.id,
            "session_name": session.session_name,
            "context": session.context_data,
            "initial_message": {
                "id": initial_message.id,
                "content": initial_message.content,
                "created_at": initial_message.created_at
            },
            "message": "Fortune conversation started. You can now chat interactively!",
            "poem_available": poem_available,
            "poem_service_status": "available" if poem_available else "unavailable"
        }

    except ValueError as e:
        logger.error(f"[DEBUG] ValueError in fortune conversation: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Specific handling for poem service initialization failures
        if "Failed to initialize poem service" in str(e):
            logger.warning(f"[DEBUG] Poem service unavailable, creating conversation without poems: {e}")
            # Try to create a basic conversation without poem service
            try:
                # This should work even without poem service
                from app.schemas.chat import ChatSessionCreate, ChatMessageCreate
                deity = await deity_service.get_deity_by_id(conversation_data.deity_id)
                if not deity:
                    raise HTTPException(status_code=400, detail="Invalid deity ID")

                session_create = ChatSessionCreate(
                    session_name=f"Fortune Reading - {deity.deity.name}",
                    context_data={
                        "deity_id": conversation_data.deity_id,
                        "deity_name": deity.deity.name,
                        "deity_chinese_name": deity.deity.chinese_name,
                        "fortune_number": conversation_data.fortune_number,
                        "conversation_type": "fortune_reading",
                        "poem_service_available": False
                    }
                )

                session = await chat_service.create_session(current_user.id, session_create, db)

                initial_message_data = ChatMessageCreate(
                    content=conversation_data.initial_question,
                    metadata={"conversation_starter": True, "poem_service_unavailable": True}
                )

                initial_message = await chat_service.add_message(
                    session.id, current_user.id, initial_message_data, MessageType.USER, db
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
                    "message": "Fortune conversation started in basic mode. Poem service is temporarily unavailable.",
                    "poem_available": False,
                    "poem_service_status": "initialization_failed"
                }
            except Exception as fallback_error:
                logger.error(f"[DEBUG] Fallback conversation creation failed: {fallback_error}", exc_info=True)
                raise HTTPException(status_code=500, detail="Unable to start fortune conversation")
        else:
            raise HTTPException(status_code=500, detail=f"Runtime error: {str(e)}")
    except Exception as e:
        logger.error(f"[DEBUG] Exception in fortune conversation: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start fortune conversation")


@router.post("/fortune-conversation-debug", response_model=Dict[str, Any])
async def start_fortune_conversation_debug(
    conversation_data: FortuneConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug version with detailed error tracking"""
    try:
        print("CLAUDE DEBUG: ENDPOINT HIT!")
        logger.info("CLAUDE DEBUG: ENDPOINT HIT!")

        print(f"CLAUDE DEBUG: Data: {conversation_data}")
        logger.info(f"CLAUDE DEBUG: Data: {conversation_data}")

        print(f"CLAUDE DEBUG: User: {current_user.id}")
        logger.info(f"CLAUDE DEBUG: User: {current_user.id}")

        # Test deity service call
        print("CLAUDE DEBUG: Testing deity service...")
        logger.info("CLAUDE DEBUG: Testing deity service...")

        deity = await deity_service.get_deity_by_id(conversation_data.deity_id)
        if deity:
            print(f"CLAUDE DEBUG: Deity found: {deity.deity.name}")
            logger.info(f"CLAUDE DEBUG: Deity found: {deity.deity.name}")
        else:
            print(f"CLAUDE DEBUG: Deity NOT found for ID: {conversation_data.deity_id}")
            logger.error(f"CLAUDE DEBUG: Deity NOT found for ID: {conversation_data.deity_id}")
            return {"error": "Deity not found", "deity_id": conversation_data.deity_id}

        print("CLAUDE DEBUG: All checks passed - endpoint working!")
        logger.info("CLAUDE DEBUG: All checks passed - endpoint working!")

        return {
            "status": "success",
            "deity_id": conversation_data.deity_id,
            "deity_name": deity.deity.name,
            "user_id": current_user.id,
            "message": "Debug endpoint completed successfully"
        }

    except Exception as e:
        print(f"CLAUDE DEBUG: ERROR in debug endpoint: {type(e).__name__}: {e}")
        logger.error(f"CLAUDE DEBUG: ERROR in debug endpoint: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")


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