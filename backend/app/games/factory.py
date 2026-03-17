from typing import Dict, Type, Optional, List, Any

from app.games.base import Game
from app.games.classic import ClassicCarduitive


class GameFactory:
    """Factory for creating game instances by type."""
    
    # Registry of game types
    _games: Dict[str, Type[Game]] = {
        "classic": ClassicCarduitive,
        # Add more games here as they're implemented
        # "memory": MemoryGame,
        # "speed": SpeedSequence,
    }
    
    @classmethod
    def create_game(cls, game_type: str, lobby_code: str, players: List[Any]) -> Optional[Game]:
        """
        Create a new game instance.
        
        Args:
            game_type: Type of game to create ('classic', etc.)
            lobby_code: Lobby code for the game
            players: List of lobby players
            
        Returns:
            Game instance or None if game type not found
        """
        game_class = cls._games.get(game_type.lower())
        if not game_class:
            return None
        
        return game_class(lobby_code, players)
    
    @classmethod
    def register_game(cls, game_type: str, game_class: Type[Game]):
        """
        Register a new game type.
        
        Args:
            game_type: Unique identifier for the game
            game_class: Game class (must inherit from Game)
        """
        cls._games[game_type.lower()] = game_class
    
    @classmethod
    def get_available_games(cls) -> List[str]:
        """Get list of available game types."""
        return list(cls._games.keys())
    
    @classmethod
    def is_valid_game(cls, game_type: str) -> bool:
        """Check if a game type is valid."""
        return game_type.lower() in cls._games
