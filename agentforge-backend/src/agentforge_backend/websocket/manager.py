from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from typing import Dict, List, Optional
from ..security.jwt import decode_token, is_token_blacklisted, is_user_revoked
from ..db.session import async_session
from ..models.user import User
from ..models.execution import Execution
from sqlalchemy import select
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def authenticate_websocket(self, websocket: WebSocket) -> Optional[dict]:
        """Authenticate a WebSocket connection."""
        # Get token from query params or headers
        token = websocket.query_params.get("token")
        if not token:
            # Try to get from headers
            auth = websocket.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ")[1]
        
        if not token:
            return None
        
        payload = decode_token(token)
        if not payload:
            return None
        
        # Check if token is blacklisted
        if await is_token_blacklisted(token, "access"):
            return None
        
        if payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Check if user tokens were revoked
        if await is_user_revoked(user_id):
            return None
        
        # Verify user exists and is active
        async with async_session() as db:
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                return None
        
        return {
            "user_id": user_id,
            "role": payload.get("role", "user"),
        }
    
    async def authorize_execution_access(self, user_id: str, execution_id: str) -> bool:
        """Check if user has access to the execution."""
        async with async_session() as db:
            # Check if user owns the agent that owns the execution
            result = await db.execute(
                select(Execution)
                .join(User, Execution.agent_id == User.id)  # This needs to join through Agent
                .where(Execution.id == UUID(execution_id))
            )
            # Simplified check - in reality we'd join through Agent model
            execution = await db.get(Execution, execution_id)
            if not execution:
                return False
            
            # Get agent owner
            from ..models.agent import Agent
            agent = await db.get(Agent, execution.agent_id)
            if not agent:
                return False
            
            # Owner has access
            if str(agent.owner_id) == user_id:
                return True
            
            # TODO: Check workspace permissions for shared agents
            return False
    
    async def connect(self, execution_id: str, websocket: WebSocket, user_info: dict = None):
        """Connect a WebSocket with optional authentication."""
        await websocket.accept()
        
        metadata = {
            "execution_id": execution_id,
            "user_info": user_info,
            "connected_at": logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None)),
        }
        self.connection_metadata[websocket] = metadata
        self.active_connections.setdefault(execution_id, []).append(websocket)
        
        logger.info("websocket_connected", execution_id=execution_id, user_id=user_info.get("user_id") if user_info else None)
    
    def disconnect(self, execution_id: str, websocket: WebSocket):
        """Disconnect a WebSocket."""
        if execution_id in self.active_connections:
            if websocket in self.active_connections[execution_id]:
                self.active_connections[execution_id].remove(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
        
        metadata = self.connection_metadata.pop(websocket, {})
        logger.info("websocket_disconnected", execution_id=execution_id, user_id=metadata.get("user_info", {}).get("user_id"))
    
    async def broadcast(self, execution_id: str, message: dict, user_id: str = None):
        """Broadcast a message to all connections for an execution."""
        disconnected = []
        for ws in self.active_connections.get(execution_id, []):
            try:
                # Optionally filter by user_id
                metadata = self.connection_metadata.get(ws, {})
                if user_id and metadata.get("user_info", {}).get("user_id") != user_id:
                    continue
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        
        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(execution_id, ws)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass


ws_manager = ConnectionManager()