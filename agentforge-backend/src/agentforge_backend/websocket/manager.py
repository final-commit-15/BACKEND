from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, execution_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(execution_id, []).append(websocket)

    def disconnect(self, execution_id: str, websocket: WebSocket):
        self.active_connections[execution_id].remove(websocket)

    async def broadcast(self, execution_id: str, message: dict):
        for ws in self.active_connections.get(execution_id, []):
            try:
                await ws.send_json(message)
            except:
                pass

ws_manager = ConnectionManager()