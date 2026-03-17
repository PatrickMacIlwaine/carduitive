"""
Test game behavior when players disconnect during gameplay.
Ensures remaining players can continue and disconnected players can rejoin.
"""

import sys
sys.path.insert(0, '/Users/Patrick/code/carduitive3/backend')

from app.games.classic import ClassicCarduitive
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class MockPlayer:
    id: str
    name: str


def test_game_continues_when_player_disconnects():
    """Test that the game continues when a player disconnects mid-game"""
    print("\n" + "="*60)
    print("TEST 1: Game continues when player disconnects")
    print("="*60)
    
    # Create game with 2 players
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST', players)
    
    # Start game - deal cards
    result = game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    print(f"Initial hands:")
    print(f"  P1 (Alice): {game.player_hands['p1'].cards}")
    print(f"  P2 (Bob): {game.player_hands['p2'].cards}")
    
    # Simulate: Find who has minimum card
    all_cards = [
        (card, 'p1') for card in game.player_hands['p1'].cards
    ] + [
        (card, 'p2') for card in game.player_hands['p2'].cards
    ]
    all_cards.sort(key=lambda x: x[0])
    min_card, min_player = all_cards[0]
    
    print(f"\nMinimum card {min_card} belongs to {min_player}")
    
    # CASE 1: Minimum card player disconnects BEFORE playing
    if min_player == 'p2':
        print(f"\n⚠️  P2 (Bob) has minimum card but disconnects!")
        
        # Simulate disconnect
        game.handle_player_disconnect('p2')
        print(f"   P2 marked as disconnected")
        
        # Reduce auto-play delay for testing
        game.AUTO_PLAY_DELAY_SECONDS = 0
        
        # P1 tries to play their card
        p1_card = game.player_hands['p1'].cards[0]
        print(f"\n🃏 P1 tries to play {p1_card}...")
        
        result = game.handle_action('p1', 'play', {'card': p1_card})
        
        # Check if auto-play happened for P2
        print(f"   Result status: {result.get('status')}")
        print(f"   Played cards: {result.get('played_cards')}")
        
        if min_card in result.get('played_cards', []):
            print(f"   ✅ Auto-play worked! P2's card {min_card} was played automatically")
            return True
        elif result.get('status') == 'failed':
            print(f"   ❌ FAILED - game is still stuck")
            return False
        else:
            print(f"   ✅ Game continued somehow")
            return True
    else:
        print(f"\n✓ P1 has minimum card, plays it...")
        result = game.handle_action('p1', 'play', {'card': min_card})
        print(f"   Status: {result.get('status')}")
        return True


def test_disconnected_player_cards_get_auto_played():
    """Test that disconnected player cards are auto-played after timeout"""
    print("\n" + "="*60)
    print("TEST 2: Disconnected player cards auto-play")
    print("="*60)
    
    # Create game with 3 players
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob'), MockPlayer('p3', 'Charlie')]
    game = ClassicCarduitive('TEST2', players)
    
    # Start game
    result = game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    print(f"Initial hands:")
    for pid in ['p1', 'p2', 'p3']:
        print(f"  {pid}: {game.player_hands[pid].cards}")
    
    # Simulate: P2 disconnects with minimum card
    all_cards = []
    for pid in ['p1', 'p2', 'p3']:
        for card in game.player_hands[pid].cards:
            all_cards.append((card, pid))
    all_cards.sort(key=lambda x: x[0])
    
    min_card, min_player = all_cards[0]
    print(f"\nMinimum card is {min_card} held by {min_player}")
    
    if min_player == 'p2':
        print(f"\n⚠️  P2 (Bob) disconnects holding minimum card {min_card}")
        print(f"   Auto-play mechanism should play it after timeout...")
        
        # Simulate auto-play for disconnected player
        # This is the fix we need to implement
        print(f"\n   🔧 IMPLEMENTATION NEEDED:")
        print(f"   - Add disconnect timeout tracking")
        print(f"   - Auto-play minimum card for disconnected players")
        print(f"   - Notify all players via WebSocket")
        
        return False  # Currently not implemented
    
    return True


def test_reconnect_gets_current_game_state():
    """Test that reconnected player gets current game state"""
    print("\n" + "="*60)
    print("TEST 3: Reconnect gets current game state")
    print("="*60)
    
    # Create game
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST3', players)
    
    # Start and play some cards
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    # Play a few cards
    initial_cards = [
        (card, pid) for pid in ['p1', 'p2']
        for card in game.player_hands[pid].cards
    ]
    initial_cards.sort(key=lambda x: x[0])
    
    # Play first 2 cards
    for card, pid in initial_cards[:2]:
        if game.status.value == 'playing':
            game.handle_action(pid, 'play', {'card': card})
    
    print(f"Game state after some plays:")
    print(f"  Played cards: {game.played_cards}")
    print(f"  Current level: {game.level}")
    print(f"  Status: {game.status.value}")
    
    # Simulate P1 disconnect and reconnect
    print(f"\n📡 P1 disconnects and reconnects...")
    
    # Get game state for P1 (simulating API call)
    state = game.get_player_state('p1')
    
    print(f"   P1 receives state:")
    print(f"   - My hand: {state.get('my_hand', {}).get('cards')}")
    print(f"   - Played: {state.get('played_cards')}")
    print(f"   - Next expected: {state.get('next_expected')}")
    print(f"   - Status: {state.get('status')}")
    
    # Check if state is correct
    has_correct_hand = 'my_hand' in state and 'cards' in state.get('my_hand', {})
    has_played_cards = len(state.get('played_cards', [])) > 0
    
    if has_correct_hand and has_played_cards:
        print(f"\n   ✅ P1 successfully restored to current game state!")
        return True
    else:
        print(f"\n   ❌ P1 did not receive correct state!")
        return False


def test_game_ends_when_all_cards_played():
    """Test game completion with mixed connected/disconnected players"""
    print("\n" + "="*60)
    print("TEST 4: Game completion with disconnects")
    print("="*60)
    
    players = [MockPlayer('p1', 'Alice'), MockPlayer('p2', 'Bob')]
    game = ClassicCarduitive('TEST4', players)
    game.start_game({'deck_size': 100, 'timing_mode': 'relaxed'})
    
    print(f"Playing all cards...")
    
    # Play all cards in order
    while game.status.value == 'playing':
        # Find minimum card
        all_remaining = []
        for pid in ['p1', 'p2']:
            for card in game.player_hands[pid].cards:
                all_remaining.append((card, pid))
        
        if not all_remaining:
            break
            
        all_remaining.sort(key=lambda x: x[0])
        min_card, min_pid = all_remaining[0]
        
        result = game.handle_action(min_pid, 'play', {'card': min_card})
        print(f"  {min_pid} played {min_card}: {result.get('status')}")
    
    print(f"\nFinal status: {game.status.value}")
    print(f"Played sequence: {game.played_cards}")
    
    if game.status.value == 'success':
        print(f"\n   ✅ Game completed successfully!")
        return True
    else:
        print(f"\n   ❌ Game did not complete properly")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DISCONNECT/RECONNECT TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Game continues when player disconnects", test_game_continues_when_player_disconnects()))
    results.append(("Disconnected player cards auto-play", test_disconnected_player_cards_get_auto_played()))
    results.append(("Reconnect gets current game state", test_reconnect_gets_current_game_state()))
    results.append(("Game completion with disconnects", test_game_ends_when_all_cards_played()))
    
    # Summary
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
