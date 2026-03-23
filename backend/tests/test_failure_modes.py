"""
Test game config settings: failure modes, card sorting, and timer.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
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


class TestTimer:
    def test_no_timer_by_default(self):
        game = _make_game("forgiving")
        assert game.get_remaining_time() is None
        assert not game.is_timed_out()

    def test_timer_returns_remaining(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15})
        remaining = game.get_remaining_time()
        assert remaining is not None
        assert 14 < remaining <= 15

    def test_timer_expired(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15})
        # Simulate time passing
        game.game_start_time = datetime.now() - timedelta(seconds=20)
        assert game.is_timed_out()
        assert game.get_remaining_time() == 0.0

    def test_timeout_action_fails_level(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15})
        result = game.handle_action("system", "timeout", {})
        assert result["status"] == "failed"
        assert game.status == GameStatus.FAILED

    def test_timeout_progression_message(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15, "failure_mode": "hardcore"})
        # Advance to level 2 first
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        assert game.level == 2
        # Timeout
        game.handle_action("system", "timeout", {})
        state = game.get_public_state()
        assert state["progression"]["is_timeout"] is True
        assert "Time's up" in state["progression"]["message"]
        assert state["progression"]["restart_level"] == 1  # hardcore

    def test_play_after_timeout_returns_timeout(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15})
        # Simulate expired timer
        game.game_start_time = datetime.now() - timedelta(seconds=20)
        # Try to play a card — should trigger timeout instead
        card = game.player_hands["p1"].cards[0]
        result = game.handle_action("p1", "play", {"card": card})
        assert result["status"] == "failed"
        assert game.status == GameStatus.FAILED

    def test_timer_resets_on_new_level(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15})
        # Simulate time passing
        game.game_start_time = datetime.now() - timedelta(seconds=10)
        remaining_before = game.get_remaining_time()
        assert remaining_before is not None and remaining_before < 6
        # Complete level and advance
        _play_through_level(game)
        game.handle_action("p1", "advance", {})
        # Timer should be reset
        remaining_after = game.get_remaining_time()
        assert remaining_after is not None and remaining_after > 14

    def test_timeout_not_allowed_when_not_playing(self):
        players = [MockPlayer("p1", "Alice"), MockPlayer("p2", "Bob")]
        game = ClassicCarduitive("TEST", players)
        game.start_game({"timer_seconds": 15})
        # Fail the level first
        _fail_level(game)
        assert game.status == GameStatus.FAILED
        # Timeout should error since already failed
        result = game.handle_action("system", "timeout", {})
        assert "error" in result
