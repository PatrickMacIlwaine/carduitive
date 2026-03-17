from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import uuid


class GameStatus(Enum):
    SETUP = "setup"           # Game being configured
    WAITING = "waiting"       # Waiting for players to be ready
    PLAYING = "playing"       # Game in progress
    SUCCESS = "success"       # Level completed successfully
    FAILED = "failed"         # Level failed
    COMPLETED = "completed"   # All levels completed


@dataclass
class GameAction:
    """Represents a game action (play, pass, etc.)"""
    id: str
    type: str              # 'play', 'pass', 'start', 'fail', etc.
    player_id: str
    data: Dict[str, Any]   # Action-specific data
    timestamp: datetime


class Game(ABC):
    """
    Abstract base class for all Carduitive games.
    All game logic runs server-side for security.
    """
    
    def __init__(self, lobby_code: str, players: List[Any]):
        self.lobby_code = lobby_code
        self.players = players  # Reference to lobby players
        self.status = GameStatus.SETUP
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.actions: List[GameAction] = []
        self.config: Dict[str, Any] = {}
        
    @abstractmethod
    def get_game_type(self) -> str:
        """Return the game type identifier"""
        pass
    
    @abstractmethod
    def start_game(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the game with given configuration.
        Returns initial game state.
        """
        pass
    
    @abstractmethod
    def handle_action(self, player_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a player action.
        Returns updated game state.
        """
        pass
    
    @abstractmethod
    def get_public_state(self) -> Dict[str, Any]:
        """
        Get game state visible to all players.
        (excludes private info like other players' cards)
        """
        pass
    
    @abstractmethod
    def get_player_state(self, player_id: str) -> Dict[str, Any]:
        """
        Get game state for a specific player.
        (includes their private info like their cards)
        """
        pass
    
    def log_action(self, action_type: str, player_id: str, data: Dict[str, Any]):
        """Log a game action"""
        action = GameAction(
            id=str(uuid.uuid4()),
            type=action_type,
            player_id=player_id,
            data=data,
            timestamp=datetime.now()
        )
        self.actions.append(action)
        self.updated_at = datetime.now()
        
        # Keep only last 100 actions
        if len(self.actions) > 100:
            self.actions = self.actions[-100:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize game to dictionary"""
        return {
            "game_type": self.get_game_type(),
            "status": self.status.value,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
