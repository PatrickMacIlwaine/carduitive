from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random
from datetime import datetime

from app.games.base import Game, GameStatus


@dataclass
class PlayerHand:
    """Private hand for a player"""
    player_id: str
    cards: List[int] = field(default_factory=list)
    cards_played: List[int] = field(default_factory=list)
    
    @property
    def card_count(self) -> int:
        return len(self.cards)


class ClassicCarduitive(Game):
    """
    Classic Carduitive game implementation.
    Cooperative card sequencing game.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "starting_level": 1,
        "cards_per_player_per_level": 1,  # Increases by 1 each level
        "deck_size": 100,
        "min_card_value": 1,
        "max_card_value": 100,
        "timing_mode": "relaxed",  # relaxed, timed, speedrun
        "allow_undo": False,
        "strict_order": True,
    }
    
    def __init__(self, lobby_code: str, players: List[Any]):
        super().__init__(lobby_code, players)
        
        # Game state
        self.level: int = 1
        self.current_level_start: int = 1
        self.played_cards: List[int] = []
        self.deck: List[int] = []
        self.player_hands: Dict[str, PlayerHand] = {}
        self.current_player_index: int = 0  # For turn-based mode
        self.attempts: int = 0
        self.max_level_reached: int = 0
        self.game_start_time: Optional[datetime] = None
        
    def get_game_type(self) -> str:
        return "classic"
    
    def start_game(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new game or level.
        Deals cards to all players.
        """
        # Merge provided config with defaults
        self.config = {**self.DEFAULT_CONFIG, **config}
        
        # Reset state for new game/level
        self.played_cards = []
        self.current_player_index = 0
        self.attempts += 1
        self.game_start_time = datetime.now()
        
        # Calculate how many cards each player gets this level
        cards_per_player = (
            self.config["starting_level"] + 
            (self.level - 1) * self.config["cards_per_player_per_level"]
        )
        
        # Calculate total cards needed (must include 1 to total_cards_needed for winnable game)
        total_cards_needed = cards_per_player * len(self.players)
        deck_size = self.config["deck_size"]
        
        if total_cards_needed > deck_size:
            raise ValueError(
                f"Not enough cards in deck. Need {total_cards_needed}, "
                f"have {deck_size}"
            )
        
        # Create a full deck of 1-100 and deal randomly from it
        # Game is winnable because any card can be played first (ascending order only)
        full_deck = list(range(1, deck_size + 1))
        random.shuffle(full_deck)
        
        # Deal cards to players from the shuffled full deck
        self.player_hands = {}
        card_index = 0
        for player in self.players:
            hand = PlayerHand(player_id=player.id)
            for _ in range(cards_per_player):
                if card_index < len(full_deck):
                    hand.cards.append(full_deck[card_index])
                    card_index += 1
            hand.cards.sort()  # Sort for easier viewing
            self.player_hands[player.id] = hand
        
        # Store remaining deck for future levels
        self.deck = full_deck[card_index:]
        random.shuffle(self.deck)
        
        # Update status
        self.status = GameStatus.PLAYING
        
        # Log game start
        self.log_action("start", "system", {
            "level": self.level,
            "cards_per_player": cards_per_player,
            "total_cards": total_cards_needed,
            "player_count": len(self.players)
        })
        
        # Return public state
        return self.get_public_state()
    
    def handle_action(self, player_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle player actions:
        - 'play': Play a card
        - 'pass': Pass turn
        - 'advance': Advance to next level (after success)
        - 'restart': Restart current level (after failure)
        """
        # Check if this is a progression action
        if action == "advance":
            return self._handle_advance()
        elif action == "restart":
            return self._handle_restart()
        
        # Regular gameplay actions
        if self.status not in [GameStatus.PLAYING, GameStatus.WAITING]:
            # Allow progression actions even if game not in "playing" state
            if action in ["play", "pass"]:
                return {"error": "Game not in progress", "status": self.status.value}
        
        if action == "play":
            return self._handle_play(player_id, data.get("card"))
        elif action == "pass":
            return self._handle_pass(player_id)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _handle_advance(self) -> Dict[str, Any]:
        """Advance to next level after success"""
        if self.status != GameStatus.SUCCESS:
            return {"error": "Can only advance after successful level completion"}
        
        self.level += 1
        self.log_action("advance", "system", {"new_level": self.level})
        
        # Restart game with new level
        return self.start_game(self.config)
    
    def _handle_restart(self) -> Dict[str, Any]:
        """Restart current level after failure"""
        if self.status != GameStatus.FAILED:
            return {"error": "Can only restart after level failure"}
        
        self.log_action("restart", "system", {"level": self.level})
        
        # Restart game at same level
        return self.start_game(self.config)
    
    def _handle_play(self, player_id: str, card: Optional[int]) -> Dict[str, Any]:
        """Handle a player playing a card"""
        # Validate card
        if card is None:
            return {"error": "No card specified"}
        
        hand = self.player_hands.get(player_id)
        if not hand:
            return {"error": "Player not in game"}
        
        if card not in hand.cards:
            return {"error": "Card not in player's hand"}
        
        # Check if card can be played
        # Must play the LOWEST remaining card across ALL players
        all_remaining_cards = []
        for h in self.player_hands.values():
            all_remaining_cards.extend(h.cards)
        
        if not all_remaining_cards:
            return {"error": "No cards remaining"}
        
        min_card = min(all_remaining_cards)
        
        if card != min_card:
            # Wrong card - must play the minimum
            self.status = GameStatus.FAILED
            self.log_action("fail", player_id, {
                "card": card,
                "expected": min_card,
                "level": self.level
            })
            return self.get_public_state()
        
        # Card is valid - play it
        hand.cards.remove(card)
        hand.cards_played.append(card)
        self.played_cards.append(card)
        
        self.log_action("play", player_id, {
            "card": card,
            "cards_remaining": hand.card_count
        })
        
        # Check if level complete
        total_cards_remaining = sum(
            h.card_count for h in self.player_hands.values()
        )
        
        if total_cards_remaining == 0:
            # Level complete!
            self.status = GameStatus.SUCCESS
            if self.level > self.max_level_reached:
                self.max_level_reached = self.level
            
            self.log_action("level_complete", "system", {
                "level": self.level,
                "cards_played": len(self.played_cards)
            })
        
        # Move to next player (for turn-based mode)
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        return self.get_public_state()
    
    def _handle_pass(self, player_id: str) -> Dict[str, Any]:
        """Handle a player passing their turn"""
        self.log_action("pass", player_id, {})
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        return self.get_public_state()
    
    def advance_level(self) -> Dict[str, Any]:
        """Advance to next level (called after success)"""
        self.level += 1
        return self.start_game(self.config)
    
    def restart_level(self) -> Dict[str, Any]:
        """Restart current level (called after failure)"""
        return self.start_game(self.config)
    
    def get_public_state(self) -> Dict[str, Any]:
        """
        Get game state visible to all players.
        Excludes private card values.
        """
        # Calculate the minimum remaining card across all players
        all_remaining = []
        for h in self.player_hands.values():
            all_remaining.extend(h.cards)
        
        min_remaining = min(all_remaining) if all_remaining else None
        
        state = {
            "game_type": self.get_game_type(),
            "status": self.status.value,
            "level": self.level,
            "played_cards": self.played_cards,
            "last_played": self.played_cards[-1] if self.played_cards else None,
            "next_expected": min_remaining,
            "attempts": self.attempts,
            "max_level_reached": self.max_level_reached,
            "player_hands": {
                player_id: {
                    "card_count": hand.card_count,
                    "cards_played": hand.cards_played
                }
                for player_id, hand in self.player_hands.items()
            },
            "current_player_index": self.current_player_index,
            "config": self.config,
        }
        
        # Add progression controls when game is not playing
        if self.status == GameStatus.SUCCESS:
            state["progression"] = {
                "available_actions": ["advance"],
                "message": f"🎉 Level {self.level} complete! Ready for Level {self.level + 1}?",
                "next_level": self.level + 1,
            }
        elif self.status == GameStatus.FAILED:
            state["progression"] = {
                "available_actions": ["restart"],
                "message": f"💥 Wrong card! Try Level {self.level} again?",
                "restart_level": self.level,
            }
        
        return state
    
    def get_player_state(self, player_id: str) -> Dict[str, Any]:
        """
        Get game state for a specific player.
        Includes their private hand.
        """
        public_state = self.get_public_state()
        
        # Add player's private hand
        hand = self.player_hands.get(player_id)
        if hand:
            public_state["my_hand"] = {
                "cards": hand.cards,
                "cards_played": hand.cards_played
            }
        
        # Add actions history
        public_state["recent_actions"] = [
            {
                "type": a.type,
                "player_id": a.player_id,
                "data": a.data,
                "timestamp": a.timestamp.isoformat()
            }
            for a in self.actions[-20:]  # Last 20 actions
        ]
        
        return public_state
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize full game state"""
        return {
            **super().to_dict(),
            "level": self.level,
            "played_cards": self.played_cards,
            "attempts": self.attempts,
            "max_level_reached": self.max_level_reached,
        }
