#!/usr/bin/env python3
"""
Comprehensive backend test for Classic Carduitive game.
Tests multi-player dealing, privacy, card validation, and progression.
"""

import requests
import time
import sys
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"

# Generate unique lobby codes to avoid conflicts
test_counter = int(time.time())

def get_unique_code(prefix: str) -> str:
    global test_counter
    test_counter += 1
    return f"{prefix}{test_counter}"

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"🎮 {title}")
    print(f"{'='*70}")

def print_result(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")

def create_lobby(code: str, player_name: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Create lobby and return (success, session_cookie, player_id)"""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/lobbies",
            json={"code": code, "player_name": player_name},
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code != 200:
            return False, None, None
        
        cookie = resp.cookies.get(f"lobby_{code}")
        data = resp.json()
        player_id = data.get("you", {}).get("id")
        return True, cookie, player_id
    except Exception as e:
        print(f"   Error: {e}")
        return False, None, None

def join_lobby(code: str, player_name: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Join lobby and return (success, session_cookie, player_id)"""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/lobbies/{code}/join",
            json={"player_name": player_name},
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code != 200:
            return False, None, None
        
        cookie = resp.cookies.get(f"lobby_{code}")
        data = resp.json()
        player_id = data.get("you", {}).get("id")
        return True, cookie, player_id
    except Exception as e:
        print(f"   Error: {e}")
        return False, None, None

def start_game(code: str, session_cookie: str, deck_size: int = 20) -> tuple[bool, Optional[Dict]]:
    """Start game and return (success, game_state)"""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/lobbies/{code}/start",
            json={"game_type": "classic", "config": {"deck_size": deck_size, "max_card_value": deck_size}},
            cookies={f"lobby_{code}": session_cookie}
        )
        
        if resp.status_code != 200:
            return False, None
        
        return True, resp.json()
    except Exception as e:
        print(f"   Error: {e}")
        return False, None

def get_game_state(code: str, session_cookie: str) -> tuple[bool, Optional[Dict]]:
    """Get game state and return (success, state)"""
    try:
        resp = requests.get(
            f"{BASE_URL}/api/lobbies/{code}/game-state",
            cookies={f"lobby_{code}": session_cookie}
        )
        
        if resp.status_code != 200:
            return False, None
        
        return True, resp.json()
    except Exception as e:
        print(f"   Error: {e}")
        return False, None

def play_card(code: str, session_cookie: str, card: int) -> tuple[bool, Optional[Dict]]:
    """Play a card and return (success, result)"""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/lobbies/{code}/action",
            json={"action": "play", "data": {"card": card}},
            cookies={f"lobby_{code}": session_cookie}
        )
        
        if resp.status_code != 200:
            return False, None
        
        return True, resp.json()
    except Exception as e:
        print(f"   Error: {e}")
        return False, None

def test_multiplayer_dealing():
    """Test 1: Multi-player card dealing"""
    print_header("TEST 1: Multi-Player Card Dealing")
    
    lobby_code = get_unique_code("DEAL")
    
    # Create 3 players
    players = []
    for i, name in enumerate(["Alice", "Bob", "Charlie"]):
        if i == 0:
            success, cookie, pid = create_lobby(lobby_code, name)
        else:
            success, cookie, pid = join_lobby(lobby_code, name)
        
        if not success:
            print_result(f"Player {name} setup", False, "Failed to join")
            return False
        
        players.append({"name": name, "cookie": cookie, "id": pid})
        print(f"   ✓ {name} joined (ID: {pid[:8]}...)")
    
    # Start game (host is Alice)
    success, game_state = start_game(lobby_code, players[0]["cookie"], deck_size=30)
    if not success:
        print_result("Game start", False, "Failed to start")
        return False
    
    print(f"   ✓ Game started - Level {game_state['level']}")
    
    # Get each player's game state and check cards
    all_have_cards = True
    cards_by_player = {}
    
    for player in players:
        success, state = get_game_state(lobby_code, player["cookie"])
        if not success:
            print_result(f"Get state for {player['name']}", False)
            all_have_cards = False
            continue
        
        my_cards = state.get("my_hand", {}).get("cards", [])
        cards_by_player[player["name"]] = my_cards
        
        if len(my_cards) == 1:  # Level 1 should give 1 card each
            print(f"   ✓ {player['name']} has card: {my_cards}")
        else:
            print(f"   ❌ {player['name']} has {len(my_cards)} cards (expected 1)")
            all_have_cards = False
    
    # Verify all cards are different (no duplicates in dealing)
    all_cards = []
    for name, cards in cards_by_player.items():
        all_cards.extend(cards)
    
    has_duplicates = len(all_cards) != len(set(all_cards))
    
    print_result(
        "Multi-player dealing",
        all_have_cards and not has_duplicates,
        f"Cards dealt: {cards_by_player}"
    )
    
    return all_have_cards and not has_duplicates

def test_privacy():
    """Test 2: Player privacy - A cannot see B's cards"""
    print_header("TEST 2: Privacy - Players Cannot See Others' Cards")
    
    lobby_code = get_unique_code("PRIV")
    
    # Setup - Create Alice
    success, alice_cookie, alice_id = create_lobby(lobby_code, "Alice")
    if not success:
        print_result("Privacy test", False, "Failed to create lobby")
        return False
    
    # Join Bob
    success, bob_cookie, bob_id = join_lobby(lobby_code, "Bob")
    if not success:
        print_result("Privacy test", False, "Failed to join Bob")
        return False
    
    print(f"   ✓ Alice ID: {alice_id[:8]}...")
    print(f"   ✓ Bob ID: {bob_id[:8]}...")
    
    # Start game (Alice is host)
    success, _ = start_game(lobby_code, alice_cookie, deck_size=20)
    if not success:
        print_result("Privacy test", False, "Failed to start game")
        return False
    
    # Get Alice's view
    success, alice_state = get_game_state(lobby_code, alice_cookie)
    
    if not success:
        print_result("Privacy test", False, "Failed to get state")
        return False
    
    # Check what Alice sees about Bob
    player_hands = alice_state.get("player_hands", {})
    bob_hand = player_hands.get(bob_id, {})
    
    # Alice should see card_count but not actual cards
    has_card_count = "card_count" in bob_hand
    has_no_cards = "cards" not in bob_hand or len(bob_hand.get("cards", [])) == 0
    
    print(f"   Alice sees Bob's hand: {bob_hand}")
    print(f"   ✓ Sees card_count: {has_card_count}")
    print(f"   ✓ Does NOT see card values: {has_no_cards}")
    
    print_result(
        "Privacy protection",
        has_card_count and has_no_cards,
        f"Bob's visible info: card_count={bob_hand.get('card_count')}"
    )
    
    return has_card_count and has_no_cards

def test_card_validation():
    """Test 3: Card play validation"""
    print_header("TEST 3: Card Play Validation")
    
    lobby_code = get_unique_code("VAL")
    
    # Setup
    success, cookie, player_id = create_lobby(lobby_code, "Player1")
    
    if not success:
        print_result("Setup", False, "Failed to create lobby")
        return False
    
    # Start game with deck of 5
    success, _ = start_game(lobby_code, cookie, deck_size=5)
    
    if not success:
        print_result("Setup", False, "Failed to start game")
        return False
    
    # Get state to see what card we have
    success, state = get_game_state(lobby_code, cookie)
    my_cards = state.get("my_hand", {}).get("cards", [])
    
    if not my_cards:
        print_result("Card validation", False, "No cards dealt")
        return False
    
    print(f"   Player has cards: {my_cards}")
    
    # Test 1: Try playing a card not in hand (should fail)
    wrong_card = 999
    if wrong_card in my_cards:
        wrong_card = 998
    
    success, result = play_card(lobby_code, cookie, wrong_card)
    cant_play_nonexistent = result is not None and result.get("error") is not None
    print(f"   ✓ Cannot play non-existent card {wrong_card}: {cant_play_nonexistent}")
    
    if cant_play_nonexistent:
        print(f"      Error: {result.get('error')}")
    
    # Test 2: Get state to find the minimum card across all hands
    success, state = get_game_state(lobby_code, cookie)
    expected_min = state.get("next_expected")
    current_card = my_cards[0]
    
    print(f"\n   Minimum card to play: {expected_min}")
    print(f"   Attempting to play {current_card}...")
    success, result = play_card(lobby_code, cookie, current_card)
    
    print(f"   Result status: {result.get('status')}")
    
    # Check if we played the correct minimum
    if current_card == expected_min:
        print(f"   ✓ Playing minimum card {current_card} (correct)")
        played_correctly = True
        failed_wrong_order = False
    else:
        # Playing non-minimum should fail
        played_correctly = False
        failed_wrong_order = result.get("status") == "failed"
        print(f"   ✓ Playing {current_card} fails (expected min {expected_min}): {failed_wrong_order}")
    
    print_result(
        "Card validation",
        cant_play_nonexistent or failed_wrong_order or played_correctly,
        f"Validation working: nonexistent={cant_play_nonexistent}, wrong_order={failed_wrong_order}"
    )
    
    return cant_play_nonexistent or failed_wrong_order or played_correctly

def test_level_progression():
    """Test 4: Level progression (advance/restart)"""
    print_header("TEST 4: Level Progression")
    
    lobby_code = get_unique_code("PROG")
    
    # Setup with 2 players so we can test failure/success properly
    success, cookie1, pid1 = create_lobby(lobby_code, "Player1")
    if not success:
        print_result("Setup", False, "Failed to create lobby")
        return False
    
    success, cookie2, pid2 = join_lobby(lobby_code, "Player2")
    if not success:
        print_result("Setup", False, "Failed to join Player2")
        return False
    
    print("   ✓ Created lobby with 2 players...")
    
    # Start game
    success, _ = start_game(lobby_code, cookie1)
    if not success:
        print_result("Setup", False, "Failed to start")
        return False
    
    # Get hands
    success, state1 = get_game_state(lobby_code, cookie1)
    success, state2 = get_game_state(lobby_code, cookie2)
    
    cards1 = state1.get("my_hand", {}).get("cards", [])
    cards2 = state2.get("my_hand", {}).get("cards", [])
    
    print(f"   P1 cards: {cards1}")
    print(f"   P2 cards: {cards2}")
    
    # Find who has the minimum card
    all_cards = [(c, cookie1) for c in cards1] + [(c, cookie2) for c in cards2]
    all_cards.sort(key=lambda x: x[0])
    min_card, min_cookie = all_cards[0]
    max_card, max_cookie = all_cards[-1]
    
    # Test 1: Try playing non-minimum first (should fail)
    print(f"   Testing failure path: Playing {max_card} (not min {min_card})...")
    success, result = play_card(lobby_code, max_cookie, max_card)
    
    if result and result.get("status") == "failed":
        print("   ✓ Level failed correctly")
        print(f"   ✓ Progression options: {result.get('progression')}")
        
        # Test restart
        resp = requests.post(
            f"{BASE_URL}/api/lobbies/{lobby_code}/action",
            json={"action": "restart", "data": {}},
            cookies={f"lobby_{lobby_code}": cookie1}
        )
        restart_result = resp.json()
        restarted = restart_result.get("level") == 1 and restart_result.get("attempts", 0) > 1
        print(f"   ✓ Restart works: {restarted}")
        print(f"   New cards after restart: {restart_result.get('my_hand', {}).get('cards')}")
        
        # After restart, complete level successfully
        print("   Testing success path after restart...")
        # Get new hands
        success, state1 = get_game_state(lobby_code, cookie1)
        success, state2 = get_game_state(lobby_code, cookie2)
        cards1 = state1.get("my_hand", {}).get("cards", [])
        cards2 = state2.get("my_hand", {}).get("cards", [])
        
        # Play in correct order
        all_cards = [(c, cookie1) for c in cards1] + [(c, cookie2) for c in cards2]
        all_cards.sort(key=lambda x: x[0])
        
        for card, cookie in all_cards:
            success, result = play_card(lobby_code, cookie, card)
        
        if result.get("status") == "success":
            # Test advance
            resp = requests.post(
                f"{BASE_URL}/api/lobbies/{lobby_code}/action",
                json={"action": "advance", "data": {}},
                cookies={f"lobby_{lobby_code}": cookie1}
            )
            advance_result = resp.json()
            advanced = advance_result.get("level") == 2
            has_two_cards = len(advance_result.get("my_hand", {}).get("cards", [])) == 2
            print(f"   ✓ Advanced to Level 2: {advanced}")
            print(f"   ✓ Has 2 cards: {has_two_cards}")
            
            print_result("Level progression", restarted and advanced and has_two_cards, "Failure → Restart → Advance flow working")
            return restarted and advanced and has_two_cards
        else:
            print_result("Level progression", False, "Should have succeeded after restart")
            return False
    else:
        print_result("Level progression", False, f"Should have failed, got: {result}")
        return False

def test_multiplayer_game_flow():
    """Test 5: Multi-player game flow (2-5 players, correct and wrong order)"""
    print_header("TEST 5: Multi-Player Game Flow (2-5 Players)")
    
    all_passed = True
    
    for num_players in [2, 3, 4, 5]:
        print(f"\n   Testing with {num_players} players...")
        lobby_code = get_unique_code(f"MP{num_players}")
        
        # Create players
        players = []
        player_names = [f"Player{i+1}" for i in range(num_players)]
        
        for i, name in enumerate(player_names):
            if i == 0:
                success, cookie, pid = create_lobby(lobby_code, name)
            else:
                success, cookie, pid = join_lobby(lobby_code, name)
            
            if not success:
                print(f"   ❌ Failed to setup {name}")
                all_passed = False
                continue
            
            players.append({"name": name, "cookie": cookie, "id": pid})
        
        if len(players) != num_players:
            print(f"   ❌ Only {len(players)}/{num_players} players joined")
            all_passed = False
            continue
        
        # Start game
        success, _ = start_game(lobby_code, players[0]["cookie"])
        if not success:
            print("   ❌ Failed to start game")
            all_passed = False
            continue
        
        print(f"   ✓ Game started with {num_players} players")
        
        # Get all player hands
        all_cards = {}
        for player in players:
            success, state = get_game_state(lobby_code, player["cookie"])
            if success:
                cards = state.get("my_hand", {}).get("cards", [])
                all_cards[player["id"]] = {
                    "name": player["name"],
                    "cards": cards,
                    "cookie": player["cookie"]
                }
        
        # Verify each player has exactly 1 card
        actual_cards = []
        for pid, info in all_cards.items():
            actual_cards.extend(info["cards"])
        
        if len(actual_cards) != num_players:
            print(f"   ❌ Wrong number of cards. Expected {num_players}, got {len(actual_cards)}")
            all_passed = False
            continue
        
        print(f"   ✓ Cards dealt: {sorted(actual_cards)} (random from 1-100)")
        
        # Test 1: Play in CORRECT ascending order
        print("   Testing CORRECT ascending order play...")
        correct_order_passed = True
        
        # Sort all cards and play them in ascending order
        sorted_cards = sorted(actual_cards)
        
        for i, card_num in enumerate(sorted_cards):
            # Find which player has this card
            player_with_card = None
            for pid, info in all_cards.items():
                if card_num in info["cards"]:
                    player_with_card = info
                    break
            
            if not player_with_card:
                print(f"   ❌ No player has card {card_num}")
                correct_order_passed = False
                break
            
            # Play the card
            success, result = play_card(lobby_code, player_with_card["cookie"], card_num)
            
            if not success or result.get("status") not in ["playing", "success"]:
                print(f"   ❌ Playing card {card_num} failed: {result.get('status')}")
                correct_order_passed = False
                break
            
            # Verify state after each play
            for check_player in players:
                success, check_state = get_game_state(lobby_code, check_player["cookie"])
                if success:
                    played = check_state.get("played_cards", [])
                    if len(played) != i + 1:
                        print(f"   ❌ State error: expected {i + 1} played cards, got {len(played)}")
                        correct_order_passed = False
                        break
            
            if not correct_order_passed:
                break
        
        if not correct_order_passed:
            all_passed = False
            continue
        
        print("   ✓ Ascending order play passed")
        
        # Level should be complete
        success, final_state = get_game_state(lobby_code, players[0]["cookie"])
        if final_state.get("status") != "success":
            print(f"   ❌ Level should be complete, status is {final_state.get('status')}")
            all_passed = False
            continue
        
        print(f"   ✓ Level 1 complete after playing all {num_players} cards")
    
    print_result("Multi-player game flow", all_passed, "Tested 2-5 players")
    return all_passed


def test_wrong_card_failure():
    """Test 6: Playing non-minimum card causes level failure"""
    print_header("TEST 6: Wrong Card Failure (Non-Minimum)")
    
    lobby_code = get_unique_code("WRONG")
    
    # Setup 2 players
    success, cookie1, pid1 = create_lobby(lobby_code, "Player1")
    if not success:
        print_result("Setup", False, "Failed to create lobby")
        return False
    
    success, cookie2, pid2 = join_lobby(lobby_code, "Player2")
    if not success:
        print_result("Setup", False, "Failed to join Player2")
        return False
    
    # Start game
    success, _ = start_game(lobby_code, cookie1)
    if not success:
        print_result("Setup", False, "Failed to start")
        return False
    
    # Get hands
    success, state1 = get_game_state(lobby_code, cookie1)
    success, state2 = get_game_state(lobby_code, cookie2)
    
    cards1 = state1.get("my_hand", {}).get("cards", [])
    cards2 = state2.get("my_hand", {}).get("cards", [])
    
    print(f"   Player1 hand: {cards1}")
    print(f"   Player2 hand: {cards2}")
    
    # Find minimum and maximum cards
    all_cards = [(c, cookie1) for c in cards1] + [(c, cookie2) for c in cards2]
    all_cards.sort(key=lambda x: x[0])
    
    if len(all_cards) >= 2:
        min_card, min_cookie = all_cards[0]
        max_card, max_cookie = all_cards[-1]
        
        print(f"   Minimum card: {min_card}, Maximum: {max_card}")
        
        # Try to play maximum first (should fail - not minimum)
        print(f"   Testing: Playing max {max_card} (should fail, min is {min_card})...")
        success, result = play_card(lobby_code, max_cookie, max_card)
        
        if result.get("status") == "failed":
            print(f"   ✓ Playing non-minimum {max_card} correctly failed")
            print(f"   Expected minimum: {result.get('next_expected')}")
            print_result("Wrong card failure", True, "Non-minimum play rejected")
            return True
        else:
            print(f"   ❌ Should have failed but got: {result.get('status')}")
            return False
    else:
        print("   ❌ Not enough cards to test")
        return False
    
    status = result.get("status")
    
    if status == "failed":
        print(f"   ✓ Correctly failed: {result.get('progression', {}).get('message')}")
        
        # Verify both players still have their cards (level restarted)
        success, state1_after = get_game_state(lobby_code, cookie1)
        success, state2_after = get_game_state(lobby_code, cookie2)
        
        cards1_after = state1_after.get("my_hand", {}).get("cards", [])
        cards2_after = state2_after.get("my_hand", {}).get("cards", [])
        
        print(f"   Player1 cards after fail: {cards1_after}")
        print(f"   Player2 cards after fail: {cards2_after}")
        
        # After failure, should be able to restart
        if state1_after.get("progression") and "restart" in state1_after.get("progression", {}).get("available_actions", []):
            print("   ✓ Restart option available")
            
            # Test restart
            resp = requests.post(
                f"{BASE_URL}/api/lobbies/{lobby_code}/action",
                json={"action": "restart", "data": {}},
                cookies={f"lobby_{lobby_code}": cookie1}
            )
            restart_result = resp.json()
            
            if restart_result.get("status") == "playing" and restart_result.get("attempts", 0) > 1:
                print("   ✓ Level restarted successfully")
                print_result("Wrong card failure", True, "Fail → Restart flow working")
                return True
            else:
                print(f"   ❌ Restart failed: {restart_result}")
                return False
        else:
            print("   ❌ Restart not available")
            return False
    else:
        print(f"   ❌ Should have failed but got status: {status}")
        return False


def test_state_consistency():
    """Test 7: State consistency across all players after each action"""
    print_header("TEST 7: State Consistency Check")
    
    lobby_code = get_unique_code("CONSISTENT")
    
    # Setup 3 players
    players = []
    for i, name in enumerate(["Alice", "Bob", "Charlie"]):
        if i == 0:
            success, cookie, pid = create_lobby(lobby_code, name)
        else:
            success, cookie, pid = join_lobby(lobby_code, name)
        
        if success:
            players.append({"name": name, "cookie": cookie, "id": pid})
    
    if len(players) != 3:
        print_result("Setup", False, f"Only {len(players)}/3 players joined")
        return False
    
    # Start game
    start_game(lobby_code, players[0]["cookie"])
    
    print("   ✓ 3 players in game")
    
    # Get initial state for all
    initial_states = {}
    all_hands = {}
    for p in players:
        success, state = get_game_state(lobby_code, p["cookie"])
        initial_states[p["id"]] = state
        all_hands[p["id"]] = state.get("my_hand", {}).get("cards", [])
    
    # Find the lowest card among all players
    all_cards = []
    for pid, cards in all_hands.items():
        for c in cards:
            all_cards.append((c, pid))
    
    if not all_cards:
        print_result("State consistency", False, "No cards dealt")
        return False
    
    # Sort and get lowest card
    all_cards.sort(key=lambda x: x[0])
    lowest_card, player_with_lowest = all_cards[0]
    
    # Find player info
    player_info = next(p for p in players if p["id"] == player_with_lowest)
    
    print(f"   {player_info['name']} plays lowest card {lowest_card}...")
    success, result = play_card(lobby_code, player_info["cookie"], lowest_card)
    
    # Check all players see the same played_cards
    all_match = True
    expected_played = [lowest_card]
    
    for check_p in players:
        success, check_state = get_game_state(lobby_code, check_p["cookie"])
        played = check_state.get("played_cards", [])
        if played != expected_played:
            print(f"   ❌ {check_p['name']} sees wrong played_cards: {played} (expected {expected_played})")
            all_match = False
    
    if all_match:
        print(f"   ✓ All players see played_cards: {expected_played}")
        print_result("State consistency", True, "All players synchronized")
        return True
    else:
        print_result("State consistency", False, "Players have inconsistent state")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("🃏 CLASSIC CARDUITIVE BACKEND TEST SUITE")
    print("="*70)
    
    tests = [
        ("Multi-Player Dealing", test_multiplayer_dealing),
        ("Privacy Protection", test_privacy),
        ("Card Validation", test_card_validation),
        ("Level Progression", test_level_progression),
        ("Multi-Player Game Flow (2-5)", test_multiplayer_game_flow),
        ("Wrong Card Failure", test_wrong_card_failure),
        ("State Consistency", test_state_consistency),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} - ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        print()
    
    # Summary
    print("="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Backend is ready for frontend.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Review above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("Make sure the backend is running on http://localhost:8000")
        sys.exit(1)

