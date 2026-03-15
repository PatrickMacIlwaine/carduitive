from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json


class LobbyConnectionManager:
    """WebSocket connection manager with lobby room support."""
    
    def __init__(self):
        # Map lobby_code -> List[WebSocket]
        self.lobby_connections: Dict[str, List[WebSocket]] = {}
        # Map WebSocket -> lobby_code
        self.websocket_to_lobby: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, lobby_code: str):
        """Connect a websocket to a specific lobby."""
        await websocket.accept()
        
        if lobby_code not in self.lobby_connections:
            self.lobby_connections[lobby_code] = []
        
        self.lobby_connections[lobby_code].append(websocket)
        self.websocket_to_lobby[websocket] = lobby_code
        
        print(f"WebSocket connected to lobby {lobby_code}. Total connections: {len(self.lobby_connections[lobby_code])}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket and remove from its lobby."""
        lobby_code = self.websocket_to_lobby.get(websocket)
        
        if lobby_code and lobby_code in self.lobby_connections:
            if websocket in self.lobby_connections[lobby_code]:
                self.lobby_connections[lobby_code].remove(websocket)
                
                # Clean up empty lobbies
                if len(self.lobby_connections[lobby_code]) == 0:
                    del self.lobby_connections[lobby_code]
        
        if websocket in self.websocket_to_lobby:
            del self.websocket_to_lobby[websocket]
        
        if lobby_code:
            print(f"WebSocket disconnected from lobby {lobby_code}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific websocket."""
        await websocket.send_text(message)

    async def broadcast_to_lobby(self, message: str, lobby_code: str):
        """Broadcast a message to all connections in a specific lobby."""
        if lobby_code in self.lobby_connections:
            for connection in self.lobby_connections[lobby_code]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error broadcasting to websocket: {e}")

    async def broadcast_player_joined(self, lobby_code: str, player_name: str):
        """Notify all players in a lobby that someone joined."""
        message = json.dumps({
            "type": "player_joined",
            "player_name": player_name,
            "timestamp": str(datetime.now())
        })
        await self.broadcast_to_lobby(message, lobby_code)

    async def broadcast_player_left(self, lobby_code: str, player_name: str):
        """Notify all players in a lobby that someone left."""
        message = json.dumps({
            "type": "player_left",
            "player_name": player_name,
            "timestamp": str(datetime.now())
        })
        await self.broadcast_to_lobby(message, lobby_code)

    async def broadcast_lobby_update(self, lobby_code: str, lobby_data: dict):
        """Send updated lobby state to all players."""
        message = json.dumps({
            "type": "lobby_update",
            "data": lobby_data
        })
        await self.broadcast_to_lobby(message, lobby_code)


# Global lobby connection manager instance
from datetime import datetime
lobby_manager_ws = LobbyConnectionManager()
