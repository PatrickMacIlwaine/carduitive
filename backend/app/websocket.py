from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime


class LobbyConnectionManager:
    """WebSocket connection manager with lobby room and player tracking."""
    
    def __init__(self):
        # Map lobby_code -> List[WebSocket]
        self.lobby_connections: Dict[str, List[WebSocket]] = {}
        # Map WebSocket -> lobby_code
        self.websocket_to_lobby: Dict[WebSocket, str] = {}
        # Map WebSocket -> player_id (for connection tracking)
        self.websocket_to_player: Dict[WebSocket, str] = {}
        # Map lobby_code -> Set[player_id] (connected players)
        self.connected_players: Dict[str, set] = {}

    async def connect(self, websocket: WebSocket, lobby_code: str, player_id: Optional[str] = None):
        """Connect a websocket to a specific lobby and track player."""
        await websocket.accept()
        
        if lobby_code not in self.lobby_connections:
            self.lobby_connections[lobby_code] = []
            self.connected_players[lobby_code] = set()
        
        self.lobby_connections[lobby_code].append(websocket)
        self.websocket_to_lobby[websocket] = lobby_code
        
        # Track player connection if player_id provided
        if player_id:
            self.websocket_to_player[websocket] = player_id
            self.connected_players[lobby_code].add(player_id)
        
        connection_count = len(self.lobby_connections[lobby_code])
        player_count = len(self.connected_players[lobby_code])
        print(f"WebSocket connected to lobby {lobby_code}. "
              f"Total connections: {connection_count}, Unique players: {player_count}")
        
        # Broadcast connection update
        await self.broadcast_connection_update(lobby_code)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket and remove from its lobby."""
        lobby_code = self.websocket_to_lobby.get(websocket)
        player_id = self.websocket_to_player.get(websocket)

        if lobby_code and lobby_code in self.lobby_connections:
            if websocket in self.lobby_connections[lobby_code]:
                self.lobby_connections[lobby_code].remove(websocket)

                # Remove player from connected set
                if player_id and lobby_code in self.connected_players:
                    self.connected_players[lobby_code].discard(player_id)
                    if len(self.connected_players[lobby_code]) == 0:
                        del self.connected_players[lobby_code]

                # Clean up empty lobbies
                if len(self.lobby_connections[lobby_code]) == 0:
                    del self.lobby_connections[lobby_code]

        if websocket in self.websocket_to_lobby:
            del self.websocket_to_lobby[websocket]

        if websocket in self.websocket_to_player:
            del self.websocket_to_player[websocket]

        if lobby_code:
            print(f"WebSocket disconnected from lobby {lobby_code}")

    def is_player_connected(self, lobby_code: str, player_id: str) -> bool:
        """Check if a specific player is connected via WebSocket."""
        if lobby_code not in self.connected_players:
            return False
        return player_id in self.connected_players[lobby_code]

    def get_connected_players(self, lobby_code: str) -> List[str]:
        """Get list of connected player IDs for a lobby."""
        if lobby_code not in self.connected_players:
            return []
        return list(self.connected_players[lobby_code])

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific websocket."""
        await websocket.send_text(message)

    async def broadcast_to_lobby(self, message: str, lobby_code: str):
        """Broadcast a message to all connections in a specific lobby."""
        if lobby_code in self.lobby_connections:
            disconnected = []
            for connection in self.lobby_connections[lobby_code]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error broadcasting to websocket: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected websockets and notify remaining players
            if disconnected:
                for conn in disconnected:
                    self.disconnect(conn)
                await self.broadcast_connection_update(lobby_code)

    async def broadcast_connection_update(self, lobby_code: str):
        """Broadcast connection status update to all players."""
        if lobby_code in self.connected_players:
            connected_ids = list(self.connected_players[lobby_code])
            message = json.dumps({
                "type": "connection_update",
                "connected_players": connected_ids,
                "timestamp": str(datetime.now())
            })
            await self.broadcast_to_lobby(message, lobby_code)

    async def broadcast_player_joined(self, lobby_code: str, player_name: str, player_id: str):
        """Notify all players in a lobby that someone joined."""
        message = json.dumps({
            "type": "player_joined",
            "player_name": player_name,
            "player_id": player_id,
            "timestamp": str(datetime.now())
        })
        await self.broadcast_to_lobby(message, lobby_code)

    async def broadcast_player_left(self, lobby_code: str, player_name: str, player_id: str):
        """Notify all players in a lobby that someone left."""
        message = json.dumps({
            "type": "player_left",
            "player_name": player_name,
            "player_id": player_id,
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

    async def timer_tick(self):
        """Broadcast remaining time every second for lobbies with timed games."""
        from app.lobby_manager import lobby_manager

        while True:
            await asyncio.sleep(1)
            lobby_codes = list(self.lobby_connections.keys())
            for lobby_code in lobby_codes:
                if lobby_code not in self.lobby_connections:
                    continue

                lobby = lobby_manager.get_lobby(lobby_code)
                if not lobby or not lobby.game or lobby.status != "playing":
                    continue

                game = lobby.game
                remaining = game.get_remaining_time()
                if remaining is None:
                    continue

                if remaining <= 0 and game.status.value == "playing":
                    # Time expired — trigger timeout
                    result = game.handle_action("system", "timeout", {})
                    if result and result.get("status") == "failed":
                        lobby.updated_at = __import__("datetime").datetime.now()
                        await self.broadcast_to_lobby(
                            json.dumps({"type": "game_update", "data": result}),
                            lobby_code
                        )
                else:
                    # Broadcast remaining time
                    await self.broadcast_to_lobby(
                        json.dumps({
                            "type": "timer_tick",
                            "data": {"remaining": round(remaining, 1)}
                        }),
                        lobby_code
                    )

    async def heartbeat(self, interval: int = 10):
        """Periodically broadcast connection status to all active lobbies.

        This serves two purposes:
        1. Detects dead WebSocket connections (failed sends trigger cleanup).
        2. Keeps clients up-to-date with who is connected.
        """
        while True:
            await asyncio.sleep(interval)
            # Snapshot lobby codes to avoid dict-changed-during-iteration
            lobby_codes = list(self.lobby_connections.keys())
            for lobby_code in lobby_codes:
                if lobby_code in self.lobby_connections:
                    await self.broadcast_connection_update(lobby_code)


# Global lobby connection manager instance
lobby_manager_ws = LobbyConnectionManager()
