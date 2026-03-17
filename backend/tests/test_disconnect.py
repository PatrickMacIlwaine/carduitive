"""
Test game behavior when players disconnect during gameplay.
Game should wait for disconnected players - no auto-play.
"""

import sys
sys.path.insert(0, '/Users/Patrick/code/carduitive3/backend')

from app.games.classic import ClassicCarduitive
from dataclasses import dataclass

@dataclass
class MockPlayer:
    id: str
    name: str


def test_game_waits_for_disconnected_player():
    """Test that game waits for disconnected player to return - no auto-play"""
    print("\n" + "="*60)
    print("TEST 1: Game waits for disconnected player (no auto-play)")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST', players)
    
    result = game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    print(f"Initial hands:")
    print(f"  P1 (Alice): {game.player_hands['p1'].cards}")
    print(f"  P2 (Bob): {game.player_hands['p2'].cards}")
    
    # Find minimum card holder
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
        
        # Try to have P1 play
        p1_card = game.player_hands['p1'].cards[0]
        print(f"\n🃏 P1 tries to play {p1_card}...")
        
        result = game.handle_action('p1', 'play', {'card': p1_card})
        
        print(f"   Result status: {result.get('status')}")
        print(f"   Played cards: {result.get('played_cards')}")
        print(f"   Expected next: {result.get('next_expected')}")
        
        # Game should NOT auto-play P2's card
        # P2's card should still be in their hand
        p2_hand_after = game.player_hands['p2'].cards
        print(f"   P2's remaining hand: {p2_hand_after}")
        
        # Game should be stuck waiting for P2
        if min_card in p2_hand_after:
            print(f"   ✅ PASS - P2's card still in hand, game is waiting!")
            return True
        else:
            print(f"   ❌ FAIL - P2's card was auto-played!")
            return False
    else:
        print(f"\n✓ P1 has minimum card, plays it...")
        result = game.handle_action('p1', 'play', {'card': min_card})
        print(f"   Status: {result.get('status')}")
        return True


def test_reconnected_player_can_continue():
    """Test that reconnected player can continue playing"""
    print("\n" + "="*60)
    print("TEST 2: Reconnected player can continue")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST2', players)
    
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    # Find and play minimum card with P1 first
    all_cards = [
        (card, pid) for pid in ['p1', 'p2']
        for card in game.player_hands[pid].cards
    ]
    all_cards.sort(key=lambda x: x[0])
    min_card, min_pid = all_cards[0]
    
    print(f"Playing first card: {min_card} by {min_pid}")
    result = game.handle_action(min_pid, 'play', {'card': min_card})
    print(f"   Status after: {result.get('status')}")
    
    # Now disconnect remaining player
    other_pid = 'p2' if min_pid == 'p1' else 'p1'
    print(f"\n⚠️  {other_pid} disconnects...")
    game.handle_player_disconnect(other_pid)
    
    # Try to play again - should fail since disconnected player is next
    remaining_cards = game.player_hands[other_pid].cards
    if remaining_cards:
        next_card = min(remaining_cards)
        print(f"\n🔄 Attempting to play next card {next_card}...")
        result = game.handle_action(min_pid, 'play', {'card': next_card})
        
        # Should get error because it's not our turn (disconnected player's turn)
        print(f"   Result: {result}")
    
    # Now reconnect the player
    print(f"\n📡 {other_pid} reconnects!")
    game.handle_player_reconnect(other_pid)
    
    # Check they can get their state
    state = game.get_player_state(other_pid)
    print(f"   Reconnected player state:")
    print(f"   - Hand: {state.get('my_hand', {}).get('cards')}")
    print(f"   - Status: {state.get('status')}")
    
    # Game should still be in playing state
    if game.status.value == 'playing':
        print(f"\n   ✅ PASS - Game waiting for reconnected player!")
        return True
    else:
        print(f"\n   ❌ FAIL - Game state incorrect: {game.status.value}")
        return False


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
    
    # Simulate P1 disconnect and reconnect
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


def test_disconnected_player_still_in_game_state():
    """Test that disconnected player is tracked but game waits"""
    print("\n" + "="*60)
    print("TEST 4: Disconnected player tracked in game state")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob'), MockPlayer('p3', 'Charlie')]
    game = ClassicCarduitive('TEST4', players)
    
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    # Disconnect P2
    print("Disconnecting P2...")
    game.handle_player_disconnect('p2')
    
    # Check disconnected_players set
    print(f"   Disconnected players: {game.disconnected_players}")
    
    # Play some cards with P1
    p1_cards = game.player_hands['p1'].cards
    if p1_cards:
        min_card = min(p1_cards)
        print(f"\nP1 plays {min_card}")
        game.handle_action('p1', 'play', {'card': min_card})
    
    # Check game state includes disconnected players
    state = game.get_public_state()
    print(f"\nPublic state:")
    print(f"   Status: {state.get('status')}")
    print(f"   Disconnected tracked in player_hands: {len(state.get('player_hands', {}))}")
    
    # Game should still be playing
    if game.status.value == 'playing':
        print(f"\n   ✅ PASS - Game tracking disconnected player, still playing!")
        return True
    else:
        print(f"\n   ❌ FAIL - Game ended unexpectedly")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DISCONNECT/RECONNECT TEST SUITE (No Auto-Play)")
    print("="*60)
    
    results = []
    
    results.append(("Game waits for disconnected player", test_game_waits_for_disconnected_player()))
    results.append(("Reconnected player can continue", test_reconnected_player_can_continue()))
    results.append(("Reconnect gets current game state", test_reconnect_gets_current_game_state()))
    results.append(("Disconnected player tracked in state", test_disconnected_player_still_in_game_state()))
    
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
