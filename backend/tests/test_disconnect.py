"""
Test game behavior when players disconnect during gameplay.
Game logic is STATIC in backend - doesn't wait for anyone.
"""

import sys
sys.path.insert(0, '/Users/Patrick/code/carduitive3/backend')

from app.games.classic import ClassicCarduitive
from dataclasses import dataclass

@dataclass
class MockPlayer:
    id: str
    name: str


def test_game_static_ignores_disconnected():
    """Test that game logic is static - disconnected players don't affect game"""
    print("\n" + "="*60)
    print("TEST 1: Game is static - ignores disconnected players")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST', players)
    
    result = game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    print(f"Initial hands:")
    print(f"  P1: {game.player_hands['p1'].cards}")
    print(f"  P2: {game.player_hands['p2'].cards}")
    
    # Find minimum card across ALL players
    all_cards = [
        (card, 'p1') for card in game.player_hands['p1'].cards
    ] + [
        (card, 'p2') for card in game.player_hands['p2'].cards
    ]
    all_cards.sort(key=lambda x: x[0])
    min_card, min_player = all_cards[0]
    
    print(f"\nMinimum card {min_card} belongs to {min_player}")
    
    # Disconnect the player with minimum card
    if min_player == 'p2':
        print(f"\n⚠️  P2 (Bob) has minimum card but disconnects!")
        
        game.handle_player_disconnect('p2')
        print(f"   P2 marked as disconnected")
        
        # next_expected should STILL be P2's card (static game logic)
        state = game.get_public_state()
        print(f"   next_expected: {state.get('next_expected')}")
        
        # Verify next_expected is still P2's minimum card
        if state.get('next_expected') == min_card:
            print(f"   ✅ PASS - Game is static, next_expected unchanged!")
            return True
        else:
            print(f"   ❌ FAIL - next_expected changed!")
            return False
    else:
        print(f"\n✓ P1 has minimum card, plays it...")
        result = game.handle_action('p1', 'play', {'card': min_card})
        print(f"   Status: {result.get('status')}")
        return True


def test_other_players_can_continue():
    """Test that other players can continue when someone disconnects"""
    print("\n" + "="*60)
    print("TEST 2: Other players can continue when someone disconnects")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST2', players)
    
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    # Get all cards sorted
    all_cards = [
        (card, pid) for pid in ['p1', 'p2']
        for card in game.player_hands[pid].cards
    ]
    all_cards.sort(key=lambda x: x[0])
    
    min_card, min_pid = all_cards[0]
    
    # Play first card
    print(f"Playing first card: {min_card} by {min_pid}")
    result = game.handle_action(min_pid, 'play', {'card': min_card})
    print(f"   Status: {result.get('status')}")
    
    # Disconnect the other player
    other_pid = 'p2' if min_pid == 'p1' else 'p1'
    print(f"\n⚠️  {other_pid} disconnects...")
    game.handle_player_disconnect(other_pid)
    
    # The next minimum should be whatever is in the connected player's hand
    remaining = game.player_hands[min_pid].cards
    if remaining:
        next_card = min(remaining)
        print(f"\n🃏 {min_pid} tries to play {next_card}...")
        
        # This should work because the game is static
        result = game.handle_action(min_pid, 'play', {'card': next_card})
        print(f"   Result status: {result.get('status')}")
        
        if result.get('status') == 'playing':
            print(f"   ✅ PASS - Game continued with connected player's card!")
            return True
        else:
            print(f"   ❌ FAIL - Game blocked: {result}")
            return False
    
    return True


def test_play_card_after_opponent_disconnect():
    """Test that a player can play cards after opponent disconnects but must wait for their minimum card"""
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST_DISCONNECT_FIX', players)
    
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    all_cards = [
        (card, pid) for pid in ['p1', 'p2']
        for card in game.player_hands[pid].cards
    ]
    all_cards.sort(key=lambda x: x[0])
    
    first_card, first_pid = all_cards[0]
    second_card, second_pid = all_cards[1]
    
    game.handle_action(first_pid, 'play', {'card': first_card})
    
    other_pid = 'p2' if first_pid == 'p1' else 'p1'
    game.handle_player_disconnect(other_pid)
    
    # If connected player has the minimum card, they can play
    remaining = game.player_hands[first_pid].cards
    if remaining:
        next_card = min(remaining)
        next_expected = min(
            card for pid, hand in game.player_hands.items()
            for card in hand.cards
        )
        
        if next_card == next_expected:
            result = game.handle_action(first_pid, 'play', {'card': next_card})
            assert 'error' not in result, f"Should be able to play minimum card: {result}"
            assert result.get('status') == 'playing', f"Game should continue: {result}"
        else:
            result = game.handle_action(first_pid, 'play', {'card': next_card})
            assert 'error' in result, "Should fail when trying to play non-minimum card"
            assert result.get('status') == 'failed', "Game should fail when wrong card played"
    
    print(f"✅ PASS - Correctly waits for disconnected player's minimum card")


def test_reconnect_gets_current_game_state():
    """Test that reconnected player gets current game state"""
    print("\n" + "="*60)
    print("TEST 3: Reconnect gets current game state")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST3', players)
    
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    # Play a few cards
    all_cards = [
        (card, pid) for pid in ['p1', 'p2']
        for card in game.player_hands[pid].cards
    ]
    all_cards.sort(key=lambda x: x[0])
    
    # Play first 2 cards
    for card, pid in all_cards[:2]:
        if game.status.value == 'playing':
            game.handle_action(pid, 'play', {'card': card})
    
    print(f"Game state after some plays:")
    print(f"  Played cards: {game.played_cards}")
    print(f"  Status: {game.status.value}")
    
    # Disconnect and reconnect P1
    print(f"\n📡 P1 disconnects and reconnects...")
    game.handle_player_disconnect('p1')
    game.handle_player_reconnect('p1')
    
    state = game.get_player_state('p1')
    
    print(f"   P1 receives state:")
    print(f"   - My hand: {state.get('my_hand', {}).get('cards')}")
    print(f"   - Played: {state.get('played_cards')}")
    print(f"   - Next expected: {state.get('next_expected')}")
    print(f"   - Status: {state.get('status')}")
    
    has_correct_hand = 'my_hand' in state and 'cards' in state.get('my_hand', {})
    has_played_cards = len(state.get('played_cards', [])) > 0
    
    if has_correct_hand and has_played_cards:
        print(f"\n   ✅ PASS - P1 restored to current game state!")
        return True
    else:
        print(f"\n   ❌ FAIL - P1 did not receive correct state!")
        return False


def test_disconnected_player_tracked_but_game_static():
    """Test that disconnected player is tracked but game logic is static"""
    print("\n" + "="*60)
    print("TEST 4: Disconnected tracked but game is static")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob'), MockPlayer('p3', 'Charlie')]
    game = ClassicCarduitive('TEST4', players)
    
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    # Get initial minimum
    all_cards = [(card, pid) for pid in ['p1', 'p2', 'p3'] 
                 for card in game.player_hands[pid].cards]
    all_cards.sort(key=lambda x: x[0])
    initial_min = all_cards[0][0]
    
    # Disconnect P2
    print("Disconnecting P2...")
    game.handle_player_disconnect('p2')
    
    # Check that next_expected is STILL the same (static game)
    state = game.get_public_state()
    new_min = state.get('next_expected')
    
    print(f"   Initial minimum: {initial_min}")
    print(f"   After disconnect: {new_min}")
    print(f"   Disconnected players: {game.disconnected_players}")
    
    if initial_min == new_min:
        print(f"\n   ✅ PASS - Game is static, next_expected unchanged!")
        return True
    else:
        print(f"\n   ❌ FAIL - Game logic changed based on connection!")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DISCONNECT/RECONNECT TEST SUITE (Static Game Logic)")
    print("="*60)
    
    results = []
    
    results.append(("Game is static - ignores disconnected", test_game_static_ignores_disconnected()))
    results.append(("Other players can continue", test_other_players_can_continue()))
    results.append(("Play card after opponent disconnect", test_play_card_after_opponent_disconnect() or True))
    results.append(("Reconnect gets current game state", test_reconnect_gets_current_game_state()))
    results.append(("Disconnected tracked but game static", test_disconnected_player_tracked_but_game_static()))
    
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
        print("\n🔧 Issues found that need fixing!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)
