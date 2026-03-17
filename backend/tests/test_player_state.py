"""
Test game state preservation when players leave and rejoin the lobby.
"""

import sys
sys.path.insert(0, '/Users/Patrick/code/carduitive3/backend')

from app.lobby_manager import LobbyManager, Lobby, Player
from app.games.classic import ClassicCarduitive
from app.games.factory import GameFactory
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class MockPlayer:
    id: str
    name: str


def test_player_leave_during_game_preserves_state():
    """
    Test that when a player leaves during an active game,
    their game state (cards) is preserved for when they rejoin.
    """
    print("\n" + "="*60)
    print("TEST 1: Player leaving during game preserves their cards")
    print("="*60)
    
    lobby_manager = LobbyManager()
    
    # Create lobby with 2 players
    code = "TEST1"
    lobby = lobby_manager.create_lobby(code)
    
    player1 = lobby.add_player("Alice", is_host=True)
    player2 = lobby.add_player("Bob")
    
    print(f"Created lobby with players:")
    print(f"  P1: {player1.id} (Alice)")
    print(f"  P2: {player2.id} (Bob)")
    
    # Start game
    result = lobby_manager.start_game(code, "classic", {"deck_size": 100, "timing_mode": "relaxed"})
    
    # Get initial hands
    p1_hand_before = lobby.game.player_hands[player1.id].cards.copy()
    p2_hand_before = lobby.game.player_hands[player2.id].cards.copy()
    
    print(f"\nInitial hands:")
    print(f"  Alice (P1): {p1_hand_before}")
    print(f"  Bob (P2): {p2_hand_before}")
    
    # Alice plays one card
    p1_card = p1_hand_before[0]
    game_state = lobby.game.handle_action(player1.id, "play", {"card": p1_card})
    print(f"\nAlice played {p1_card}")
    print(f"  Played cards: {lobby.game.played_cards}")
    
    # Now Alice leaves the lobby
    print(f"\nAlice leaves the lobby...")
    lobby_manager.leave_lobby(code, player1.id)
    
    # Check: Is Alice still in the lobby's player list?
    still_in_lobby = any(p.id == player1.id for p in lobby.players)
    print(f"  Alice still in lobby.players: {still_in_lobby}")
    
    # Check: Does the game still track Alice's hand?
    alice_hand_in_game = lobby.game.player_hands.get(player1.id)
    print(f"  Alice's hand in game: {alice_hand_in_game.cards if alice_hand_in_game else 'NOT FOUND'}")
    
    # The issue: After leave_lobby, player is completely removed
    if not still_in_lobby:
        print("\n  ❌ ISSUE FOUND: Player was completely removed from lobby!")
        print("     This means their game state is lost when they rejoin.")
        return False
    
    if not alice_hand_in_game:
        print("\n  ❌ ISSUE FOUND: Player's hand was removed from game!")
        return False
    
    print("\n  ✅ Player state preserved after leaving!")
    return True


def test_player_rejoin_gets_same_state():
    """
    Test that when a player rejoins after leaving during a game,
    they get back their previous game state (cards).
    """
    print("\n" + "="*60)
    print("TEST 2: Player rejoining gets their previous game state")
    print("="*60)
    
    lobby_manager = LobbyManager()
    
    # Create lobby with 2 players
    code = "TEST2"
    lobby = lobby_manager.create_lobby(code)
    
    player1 = lobby.add_player("Alice", is_host=True)
    player2 = lobby.add_player("Bob")
    
    # Store original session for rejoin
    original_session = player1.session_id
    original_player_id = player1.id
    
    # Start game
    result = lobby_manager.start_game(code, "classic", {"deck_size": 100, "timing_mode": "relaxed"})
    
    # Alice plays one card
    p1_hand = lobby.game.player_hands[player1.id].cards
    p1_card = p1_hand[0]
    lobby.game.handle_action(player1.id, "play", {"card": p1_card})
    
    print(f"\nAlice played {p1_card}")
    print(f"  Alice's remaining cards: {lobby.game.player_hands[player1.id].cards}")
    print(f"  Played cards: {lobby.game.played_cards}")
    
    # Alice leaves
    print(f"\nAlice leaves the lobby...")
    lobby_manager.leave_lobby(code, player1.id)
    
    # Try to rejoin using session-based lookup (same as API does)
    print(f"Alice tries to rejoin with session {original_session[:8]}...")
    
    # This is what the API does - check for existing session first
    rejoined_player = lobby.get_player_by_session(original_session)
    
    print(f"\nRejoin result:")
    print(f"  Rejoined player: {rejoined_player}")
    
    if rejoined_player:
        print(f"  Same as original: {rejoined_player.id == original_player_id}")
        
        # Can we get game state?
        hand = lobby.game.player_hands.get(rejoined_player.id)
        print(f"  Game hand accessible: {hand.cards if hand else 'NOT FOUND'}")
        
        if rejoined_player.id == original_player_id and hand:
            print("\n  ✅ Player rejoined with preserved state!")
            return True
        else:
            print("\n  ❌ ISSUE: Player state not accessible!")
            return False
    else:
        # This happens if player was completely removed - new behavior should prevent this
        print("\n  ❌ ISSUE: Player was completely removed from lobby!")
        return False


def test_disconnect_vs_leave_behavior():
    """
    Test the difference between disconnecting (WebSocket) and leaving (API).
    """
    print("\n" + "="*60)
    print("TEST 3: Disconnect vs Leave behavior")
    print("="*60)
    
    lobby_manager = LobbyManager()
    
    code = "TEST3"
    lobby = lobby_manager.create_lobby(code)
    
    player1 = lobby.add_player("Alice", is_host=True)
    player2 = lobby.add_player("Bob")
    
    # Start game
    lobby_manager.start_game(code, "classic", {"deck_size": 100, "timing_mode": "relaxed"})
    
    p1_hand = lobby.game.player_hands[player1.id].cards.copy()
    print(f"Initial hands:")
    print(f"  Alice: {p1_hand}")
    print(f"  Bob: {lobby.game.player_hands[player2.id].cards}")
    
    # Test: Handle disconnect (should mark player as disconnected but keep state)
    print(f"\n--- Testing handle_player_disconnect ---")
    lobby.game.handle_player_disconnect(player1.id)
    
    alice_hand_after_disconnect = lobby.game.player_hands.get(player1.id)
    is_disconnected = player1.id in lobby.game.disconnected_players
    
    print(f"After disconnect:")
    print(f"  Alice in disconnected_players: {is_disconnected}")
    print(f"  Alice's hand preserved: {alice_hand_after_disconnect.cards if alice_hand_after_disconnect else 'NOT FOUND'}")
    
    # Now test leave_lobby behavior
    print(f"\n--- Testing leave_lobby (the problematic path) ---")
    lobby_manager.leave_lobby(code, player1.id)
    
    alice_in_lobby = any(p.id == player1.id for p in lobby.players)
    alice_hand_after_leave = lobby.game.player_hands.get(player1.id)
    
    print(f"After leave_lobby:")
    print(f"  Alice still in lobby.players: {alice_in_lobby}")
    print(f"  Alice's hand in game: {alice_hand_after_leave.cards if alice_hand_after_leave else 'NOT FOUND'}")
    
    if not alice_in_lobby:
        print("\n  ❌ ISSUE: leave_lobby removes player completely from lobby!")
        print("     This breaks the rejoin flow because player_id changes.")
        return False
    
    return True


def test_rejoin_with_valid_session():
    """
    Test that rejoining with a valid session_id preserves state.
    This tests the session-based rejoin path in the API.
    """
    print("\n" + "="*60)
    print("TEST 4: Session-based rejoin preserves state")
    print("="*60)
    
    lobby_manager = LobbyManager()
    
    code = "TEST4"
    lobby = lobby_manager.create_lobby(code)
    
    player1 = lobby.add_player("Alice", is_host=True)
    player2 = lobby.add_player("Bob")
    
    original_session = player1.session_id
    original_id = player1.id
    
    # Start game
    lobby_manager.start_game(code, "classic", {"deck_size": 100, "timing_mode": "relaxed"})
    
    # Play some cards
    p1_hand = lobby.game.player_hands[player1.id].cards
    lobby.game.handle_action(player1.id, "play", {"card": p1_hand[0]})
    
    print(f"After playing:")
    print(f"  Played cards: {lobby.game.played_cards}")
    print(f"  Alice hand: {lobby.game.player_hands[player1.id].cards}")
    
    # Leave and try to rejoin with same session
    lobby_manager.leave_lobby(code, player1.id)
    
    # Check what happens with session-based rejoin
    rejoined_player = lobby.get_player_by_session(original_session)
    
    print(f"\nAfter leave_lobby:")
    print(f"  get_player_by_session('{original_session[:8]}...'): {rejoined_player}")
    
    if rejoined_player:
        print(f"  Rejoined player ID: {rejoined_player.id}")
        print(f"  Same as original: {rejoined_player.id == original_id}")
        
        # Can we get game state?
        if rejoined_player.id == original_id:
            hand = lobby.game.player_hands.get(rejoined_player.id)
            print(f"  Game hand accessible: {hand.cards if hand else 'NOT FOUND'}")
            print("\n  ✅ Session-based rejoin works!")
            return True
        else:
            print("\n  ❌ ISSUE: Session returned different player!")
            return False
    else:
        print("\n  ❌ ISSUE: Session-based rejoin failed - player was removed!")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LOBBY PLAYER LEAVE/REJOIN TEST SUITE")
    print("="*60)
    
    results = []
    
    results.append(("Player leave during game preserves state", test_player_leave_during_game_preserves_state()))
    results.append(("Player rejoining gets previous state", test_player_rejoin_gets_same_state()))
    results.append(("Disconnect vs Leave behavior", test_disconnect_vs_leave_behavior()))
    results.append(("Session-based rejoin preserves state", test_rejoin_with_valid_session()))
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, passed_test in results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n🔧 Issues found in backend that cause player state loss!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)
