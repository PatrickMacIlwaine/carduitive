"""
Test game config settings: failure modes and card sorting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.games.classic import ClassicCarduitive
from app.games.base import GameStatus
from dataclasses import dataclass


@dataclass
class MockPlayer:
    id: str
    name: str


def _make_game(failure_mode: str = "forgiving"):
    players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
    game = ClassicCarduitive("TEST", players)
    game.start_game({"failure_mode": failure_mode})
    return game


def _play_through_level(game: ClassicCarduitive):
    """Play all cards in correct order to complete the current level."""
    while game.status == GameStatus.PLAYING:
        all_cards = []
        for hand in game.player_hands.values():
            for card in hand.cards:
                all_cards.append((card, hand.player_id))
        all_cards.sort()
        card, player_id = all_cards[0]
        game.handle_action(player_id, "play", {"card": card})


def _fail_level(game: ClassicCarduitive):
    """Force a failure by playing the wrong card."""
    all_cards = []
    for hand in game.player_hands.values():
        for card in hand.cards:
            all_cards.append((card, hand.player_id))
    all_cards.sort()
    # Play the max card instead of the min
    if len(all_cards) >= 2:
        card, player_id = all_cards[-1]
        game.handle_action(player_id, "play", {"card": card})


@pytest.mark.asyncio_mode("strict")
class TestForgivingMode:
    def test_restart_stays_on_same_level(self):
        game = _make_game("forgiving")
        # Complete level 1, advance to level 2
        _play_through_level(game)
        assert game.status == GameStatus.SUCCESS
        game.handle_action("p1", "advance", {})
        assert game.level == 2

        # Fail level 2
        _fail_level(game)
        assert game.status == GameStatus.FAILED

        # Restart should stay on level 2
        game.handle_action("p1", "restart", {})
        assert game.level == 2
        assert game.status == GameStatus.PLAYING

    def test_progression_message_shows_current_level(self):
        game = _make_game("forgiving")
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        assert game.level == 2

        _fail_level(game)
        state = game.get_public_state()
        assert state["progression"]["restart_level"] == 2
        assert "Level 2" in state["progression"]["message"]
        assert "Level 1" not in state["progression"]["message"]

    def test_default_config_is_forgiving(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({})  # No failure_mode specified
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        _fail_level(game)
        game.handle_action("p1", "restart", {})
        # Default should be forgiving — stays on level 2
        assert game.level == 2


class TestHardcoreMode:
    def test_restart_goes_to_level_1(self):
        game = _make_game("hardcore")
        # Complete level 1, advance to level 2
        _play_through_level(game)
        assert game.status == GameStatus.SUCCESS
        game.handle_action("p1", "advance", {})
        assert game.level == 2

        # Fail level 2
        _fail_level(game)
        assert game.status == GameStatus.FAILED

        # Restart should go back to level 1
        game.handle_action("p1", "restart", {})
        assert game.level == 1
        assert game.status == GameStatus.PLAYING

    def test_progression_message_shows_level_1(self):
        game = _make_game("hardcore")
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        assert game.level == 2

        _fail_level(game)
        state = game.get_public_state()
        assert state["progression"]["restart_level"] == 1
        assert "Level 1" in state["progression"]["message"]

    def test_restart_from_high_level(self):
        game = _make_game("hardcore")
        # Play through levels 1-3
        for expected_level in range(1, 4):
            assert game.level == expected_level
            _play_through_level(game)
            game.handle_action("p1", "advance", {})

        assert game.level == 4

        # Fail at level 4
        _fail_level(game)
        assert game.status == GameStatus.FAILED

        # Should go all the way back to 1
        game.handle_action("p1", "restart", {})
        assert game.level == 1
        assert game.status == GameStatus.PLAYING

    def test_cards_per_player_resets_with_level(self):
        game = _make_game("hardcore")
        # Advance to level 3 (should have 3 cards per player)
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        assert game.level == 3

        # Fail and restart
        _fail_level(game)
        game.handle_action("p1", "restart", {})
        assert game.level == 1

        # At level 1, each player should have 1 card
        for hand in game.player_hands.values():
            assert hand.card_count == 1


class TestCardsSorted:
    def test_sorted_by_default(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        # Advance to level 3 so each player has 3 cards
        game.start_game({})
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        # Level 3: 3 cards each, should be sorted
        for hand in game.player_hands.values():
            assert hand.cards == sorted(hand.cards)

    def test_sorted_true(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"cards_sorted": True})
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        for hand in game.player_hands.values():
            assert hand.cards == sorted(hand.cards)

    def test_shuffled_not_always_sorted(self):
        """With cards_sorted=False, at least one hand should be unsorted over many trials."""
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        found_unsorted = False
        for _ in range(20):
            game = ClassicCarduitive("TEST", players)
            game.start_game({"cards_sorted": False})
            _play_through_level(game)
            game.handle_action("p1", "advance", {})
            _play_through_level(game)
            game.handle_action("p1", "advance", {})
            # Level 3: 3 cards each
            for hand in game.player_hands.values():
                if hand.cards != sorted(hand.cards):
                    found_unsorted = True
                    break
            if found_unsorted:
                break
        assert found_unsorted, "Expected at least one unsorted hand over 20 trials"
