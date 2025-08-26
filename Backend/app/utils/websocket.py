"""
WebSocket connection manager for real-time notifications
"""

from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata
        self.connection_info: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        
        # Disconnect existing connection if any
        if user_id in self.active_connections:
            await self.disconnect(user_id)
        
        self.active_connections[user_id] = websocket
        self.connection_info[user_id] = {
            "connected_at": datetime.utcnow(),
            "client_host": websocket.client.host if websocket.client else "unknown"
        }
        
        logger.info(f"WebSocket connected for user: {user_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to Divine Whispers notifications",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.connection_info:
            del self.connection_info[user_id]
        
        logger.info(f"WebSocket disconnected for user: {user_id}")
    
    async def send_personal_message(self, message: any, user_id: str):
        """Send a message to a specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"No active connection found for user: {user_id}")
            return False
        
        try:
            websocket = self.active_connections[user_id]
            
            # Convert message to JSON string if it's a dict
            if isinstance(message, dict):
                message = json.dumps(message)
            
            await websocket.send_text(message)
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
            # Remove the connection if it's broken
            self.disconnect(user_id)
            return False
    
    async def broadcast_message(self, message: any, exclude_users: Optional[List[str]] = None):
        """Broadcast a message to all connected users"""
        if exclude_users is None:
            exclude_users = []
        
        # Convert message to JSON string if it's a dict
        if isinstance(message, dict):
            message = json.dumps(message)
        
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            if user_id in exclude_users:
                continue
            
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
        
        return len(self.active_connections) - len(disconnected_users)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is connected"""
        return user_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self, user_id: str) -> Optional[dict]:
        """Get connection information for a user"""
        return self.connection_info.get(user_id)
    
    async def send_fortune_result(self, user_id: str, fortune_data: dict):
        """Send fortune reading result to user"""
        message = {
            "type": "fortune_result",
            "data": fortune_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.send_personal_message(message, user_id)
    
    async def send_points_update(self, user_id: str, new_balance: int, change: int):
        """Send points balance update to user"""
        message = {
            "type": "points_update",
            "data": {
                "new_balance": new_balance,
                "change": change,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        return await self.send_personal_message(message, user_id)
    
    async def send_system_notification(self, user_id: str, notification: dict):
        """Send system notification to user"""
        message = {
            "type": "system_notification",
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.send_personal_message(message, user_id)
    
    async def send_error_notification(self, user_id: str, error_message: str):
        """Send error notification to user"""
        message = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.send_personal_message(message, user_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()