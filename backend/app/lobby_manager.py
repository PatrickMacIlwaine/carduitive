from typing import Dict, List, Optional
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


@dataclass
class Lobby:
    code: str
    players: List[Player] = field(default_factory=list)
    messages: List[ChatMessage] = field(default_factory=list)
    status: str = "waiting"  # waiting, playing, ended
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
    
    def to_dict(self, include_players: bool = True) -> dict:
        result = {
            "code": self.code,
            "status": self.status,
            "player_count": self.player_count,
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
                }
                for p in self.players
            ]
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
        
        removed = lobby.remove_player(player_id)
        
        # Delete lobby if empty
        if lobby.player_count == 0:
            self.delete_lobby(code)
        # Promote new host if host left
        elif removed and not lobby.host:
            if lobby.players:
                lobby.players[0].is_host = True
        
        return removed
    
    def list_lobbies(self) -> List[Lobby]:
        """List all active lobbies."""
        return list(self._lobbies.values())


# Global lobby manager instance
lobby_manager = LobbyManager()
