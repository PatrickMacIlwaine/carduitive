from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class ChatMessage:
    id: str
    player_name: str
    player_id: str
    message: str
    timestamp: datetime
    type: str = "chat"  # 'chat' or 'system'


@dataclass
class Player:
    name: str
    is_host: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    joined_at: datetime = field(default_factory=datetime.now)
    # Google auth fields (optional)
    user_id: int | None = None
    avatar_url: str | None = None
    is_authenticated: bool = False
    is_ready: bool = False  # Ready to start game


@dataclass
class Lobby:
    code: str
    players: List[Player] = field(default_factory=list)
    messages: List[ChatMessage] = field(default_factory=list)
    status: str = "waiting"  # waiting, starting, playing, ended
    game_type: str = "classic"  # Type of game to play
    game: Any = None  # Game instance (populated when game starts)
    current_level: int = 1  # Current game level
    countdown: Optional[int] = None  # Countdown value (3, 2, 1, None)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    @property
    def host(self) -> Optional[Player]:
        return next((p for p in self.players if p.is_host), None)
    
    def add_player(
        self,
        name: str,
        is_host: bool = False,
        user_id: int | None = None,
        avatar_url: str | None = None,
        is_authenticated: bool = False
    ) -> Player:
        player = Player(
            name=name,
            is_host=is_host,
            user_id=user_id,
            avatar_url=avatar_url,
            is_authenticated=is_authenticated
        )
        self.players.append(player)
        self.updated_at = datetime.now()
        return player
    
    def remove_player(self, player_id: str) -> bool:
        initial_count = len(self.players)
        self.players = [p for p in self.players if p.id != player_id]
        self.updated_at = datetime.now()
        return len(self.players) < initial_count
    
    def get_player_by_session(self, session_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.session_id == session_id), None)
    
    def add_message(self, player_name: str, player_id: str, message: str, msg_type: str = "chat") -> ChatMessage:
        """Add a message to the lobby chat history."""
        msg = ChatMessage(
            id=str(uuid.uuid4()),
            player_name=player_name,
            player_id=player_id,
            message=message,
            timestamp=datetime.now(),
            type=msg_type
        )
        self.messages.append(msg)
        # Keep only last 100 messages to prevent memory issues
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]
        return msg
    
    def get_messages(self, limit: int = 50) -> List[ChatMessage]:
        """Get recent messages from the lobby."""
        return self.messages[-limit:] if self.messages else []
    
    def to_dict(self, include_players: bool = True, player_id: Optional[str] = None) -> dict:
        # Get connected players from WebSocket manager
        from app.websocket import lobby_manager_ws
        connected_players = lobby_manager_ws.get_connected_players(self.code)
        connected_set = set(connected_players)
        
        result = {
            "code": self.code,
            "status": self.status,
            "game_type": self.game_type,
            "player_count": self.player_count,
            "current_level": self.current_level,
            "countdown": self.countdown,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_players:
            result["players"] = [
                {
                    "id": p.id,
                    "name": p.name,
                    "is_host": p.is_host,
                    "joined_at": p.joined_at.isoformat(),
                    "avatar_url": p.avatar_url,
                    "is_authenticated": p.is_authenticated,
                    "is_ready": p.is_ready,
                    "is_connected": p.id in connected_set,  # Connection status
                }
                for p in self.players
            ]
        
        # Include game state if game is active
        if self.game and self.status == "playing":
            if player_id:
                # Include this player's private info
                result["game_state"] = self.game.get_player_state(player_id)
            else:
                # Public state only
                result["game_state"] = self.game.get_public_state()
        
        return result


class LobbyManager:
    """In-memory lobby manager for real-time game sessions."""
    
    def __init__(self):
        self._lobbies: Dict[str, Lobby] = {}
    
    def create_lobby(self, code: str) -> Lobby:
        """Create a new lobby with the given code."""
        if code in self._lobbies:
            raise ValueError(f"Lobby with code {code} already exists")
        
        lobby = Lobby(code=code)
        self._lobbies[code] = lobby
        return lobby
    
    def get_lobby(self, code: str) -> Optional[Lobby]:
        """Get a lobby by its code."""
        return self._lobbies.get(code)
    
    def delete_lobby(self, code: str) -> bool:
        """Delete a lobby by its code."""
        if code in self._lobbies:
            del self._lobbies[code]
            return True
        return False
    
    def lobby_exists(self, code: str) -> bool:
        """Check if a lobby exists."""
        return code in self._lobbies
    
    def is_name_taken(self, code: str, name: str, exclude_session_id: str = None) -> bool:
        """Check if name is taken by another player (not this session)."""
        lobby = self._lobbies.get(code)
        if not lobby:
            return False
        
        name_lower = name.lower()
        for player in lobby.players:
            # Skip current player (allows re-join with same name)
            if exclude_session_id and player.session_id == exclude_session_id:
                continue
            if player.name.lower() == name_lower:
                return True
        return False
    
    def get_player_by_session(self, code: str, session_id: str) -> Optional[Player]:
        """Get player by session ID in a specific lobby."""
        lobby = self._lobbies.get(code)
        if not lobby:
            return None
        return lobby.get_player_by_session(session_id)
    
    def join_lobby(
        self,
        code: str,
        player_name: str,
        user_id: int | None = None,
        avatar_url: str | None = None,
        is_authenticated: bool = False
    ) -> Optional[Player]:
        """Add a player to an existing lobby."""
        lobby = self._lobbies.get(code)
        if not lobby:
            return None
        
        # First player becomes host
        is_host = len(lobby.players) == 0
        player = lobby.add_player(
            player_name,
            is_host=is_host,
            user_id=user_id,
            avatar_url=avatar_url,
            is_authenticated=is_authenticated
        )
        return player
    
    def leave_lobby(self, code: str, player_id: str) -> bool:
        """Remove a player from a lobby."""
        lobby = self._lobbies.get(code)
        if not lobby:
            return False
        
        # If game is in progress, don't remove player - just mark them as disconnected
        # This preserves their game state (cards) for when they rejoin
        if lobby.status == "playing" and lobby.game:
            # Mark player as disconnected in the game
            if hasattr(lobby.game, 'handle_player_disconnect'):
                lobby.game.handle_player_disconnect(player_id)
            # Player stays in lobby.players but is marked as disconnected
            # The WebSocket manager will handle tracking actual connection status
            self._notify_player_left(lobby, player_id)
            return True
        
        # Game not in progress - actually remove the player
        removed = lobby.remove_player(player_id)
        
        # Delete lobby if empty
        if lobby.player_count == 0:
            self.delete_lobby(code)
        # Promote new host if host left
        elif removed and not lobby.host:
            if lobby.players:
                lobby.players[0].is_host = True
        
        return removed
    
    def _notify_player_left(self, lobby: Lobby, player_id: str):
        """Notify that a player left (for game in progress case)."""
        player = next((p for p in lobby.players if p.id == player_id), None)
        if player:
            lobby.add_message("System", "system", f"{player.name} left the lobby", "system")
        lobby.updated_at = datetime.now()
    
    def start_game(self, code: str, game_type: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Start a game in a lobby.
        Only the host can start the game.
        """
        from app.games.factory import GameFactory
        
        lobby = self._lobbies.get(code)
        if not lobby:
            return None
        
        # Check if lobby is in waiting or starting state
        if lobby.status not in ["waiting", "starting"]:
            return {"error": "Game already in progress"}
        
        # Check minimum players
        if lobby.player_count < 1:  # Configurable minimum
            return {"error": "Not enough players to start game"}
        
        # Create game instance
        game = GameFactory.create_game(game_type, code, lobby.players)
        if not game:
            return {"error": f"Unknown game type: {game_type}"}
        
        # Assign game to lobby
        lobby.game = game
        lobby.game_type = game_type
        
        # Start the game (this deals cards)
        try:
            game_state = game.start_game(config)
            lobby.status = "playing"
            lobby.updated_at = datetime.now()
            return game_state
        except Exception as e:
            lobby.game = None
            return {"error": f"Failed to start game: {str(e)}"}
    
    def handle_game_action(self, code: str, player_id: str, action: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle a game action from a player.
        """
        lobby = self._lobbies.get(code)
        if not lobby or not lobby.game:
            return None
        
        result = lobby.game.handle_action(player_id, action, data)
        lobby.updated_at = datetime.now()
        
        # Handle level transitions and update lobby.current_level
        if action in ["advance", "restart"]:
            lobby.current_level = lobby.game.level
            lobby.game_type = lobby.game.get_game_type()  # Ensure consistency
        
        return result
    
    def get_game_state(self, code: str, player_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get current game state.
        If player_id provided, returns player-specific state with their private info.
        """
        lobby = self._lobbies.get(code)
        if not lobby or not lobby.game:
            return None
        
        if player_id:
            return lobby.game.get_player_state(player_id)
        else:
            return lobby.game.get_public_state()
    
    def handle_player_disconnect(self, code: str, player_id: str):
        """Notify game that a player has disconnected (WebSocket closed)."""
        lobby = self._lobbies.get(code)
        if not lobby or not lobby.game:
            return
        
        # Call game's disconnect handler
        if hasattr(lobby.game, 'handle_player_disconnect'):
            lobby.game.handle_player_disconnect(player_id)
    
    def handle_player_reconnect(self, code: str, player_id: str):
        """Notify game that a player has reconnected."""
        lobby = self._lobbies.get(code)
        if not lobby or not lobby.game:
            return
        
        # Call game's reconnect handler
        if hasattr(lobby.game, 'handle_player_reconnect'):
            lobby.game.handle_player_reconnect(player_id)
    
    def list_lobbies(self) -> List[Lobby]:
        """List all active lobbies."""
        return list(self._lobbies.values())


# Global lobby manager instance
lobby_manager = LobbyManager()
