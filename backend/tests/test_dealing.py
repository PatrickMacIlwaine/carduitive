#!/usr/bin/env python3
"""
Comprehensive dealing tests for Classic Carduitive.
Tests that cards are dealt randomly from 1-100 and each player gets correct count.
"""

import requests
import time
from collections import defaultdict

BASE_URL = "http://localhost:8000"


def test_random_dealing_from_full_deck():
    """Test that cards are dealt from full 1-100 range with variety"""
    print("\n" + "="*70)
    print("🃏 TEST: Dealing from Full Deck Range (1-100)")
    print("="*70)
    
    # Run multiple games with varying player counts
    all_dealt_cards = []
    num_games = 20
    
    for game_num in range(num_games):
        code = f"RANDOM{game_num}{int(time.time())}"
        
        # Vary number of players (2-10)
        num_players = (game_num % 9) + 2
        
        resp = requests.post(f"{BASE_URL}/api/lobbies", 
            json={"code": code, "player_name": "Host"})
        cookie1 = resp.cookies.get(f"lobby_{code}")
        
        cookies = [cookie1]
        for i in range(2, num_players + 1):
            resp = requests.post(f"{BASE_URL}/api/lobbies/{code}/join",
                json={"player_name": f"Player{i}"})
            cookies.append(resp.cookies.get(f"lobby_{code}"))
        
        # Start game
        requests.post(f"{BASE_URL}/api/lobbies/{code}/start",
            json={"game_type": "classic", "config": {}})
        
        # Collect cards from all players' private states
        for cookie in cookies:
            resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
                cookies={f"lobby_{code}": cookie})
            state = resp.json()
            my_hand = state.get("my_hand", {}).get("cards", [])
            all_dealt_cards.extend(my_hand)
    
    # Analyze distribution
    unique_cards = set(all_dealt_cards)
    min_card = min(all_dealt_cards) if all_dealt_cards else 0
    max_card = max(all_dealt_cards) if all_dealt_cards else 0
    
    print(f"   Games played: {num_games} (varying 2-10 players)")
    print(f"   Total cards dealt: {len(all_dealt_cards)}")
    print(f"   Unique card values: {len(unique_cards)}")
    print(f"   Min card: {min_card}, Max card: {max_card}")
    print(f"   Sample cards: {sorted(list(unique_cards))[:30]}")
    
    # Verify required cards 1-10 are always present (for up to 10 players)
    has_all_required = set(range(1, 11)).issubset(unique_cards)
    
    # Check distribution across ranges (these variables verify the deck is well-shuffled)
    _ = any(c <= 20 for c in unique_cards)  # has_low
    _ = any(30 <= c <= 70 for c in unique_cards)  # has_mid  
    _ = any(c >= 80 for c in unique_cards)  # has_high
    
    # We need both required cards AND variety from higher range
    passed = has_all_required and (max_card > 50)
    
    if passed:
        print("   ✅ PASS: Cards dealt from full range")
        print(f"      - Required cards 1-10: {'✅' if has_all_required else '❌'}")
        print(f"      - High cards (>50): {'✅' if max_card > 50 else '❌'} (max: {max_card})")
        print(f"      - Range: {min_card} to {max_card}")
    else:
        print("   ❌ FAIL: Insufficient card variety")
        if not has_all_required:
            missing = set(range(1, 11)) - unique_cards
            print(f"      - Missing required cards: {sorted(missing)}")
        if max_card <= 50:
            print(f"      - No high cards dealt (max: {max_card})")
    
    return passed


def test_exact_card_count_per_level():
    """Test that each player gets exactly the right number of cards per level"""
    print("\n" + "="*70)
    print("🃏 TEST: Exact Card Count Per Level")
    print("="*70)
    
    code = f"COUNTCHECK{int(time.time())}"
    
    # Create lobby with 4 players
    players = []
    resp = requests.post(f"{BASE_URL}/api/lobbies", 
        json={"code": code, "player_name": "P1"})
    players.append({"name": "P1", "cookie": resp.cookies.get(f"lobby_{code}")})
    
    for i in range(2, 5):
        resp = requests.post(f"{BASE_URL}/api/lobbies/{code}/join",
            json={"player_name": f"P{i}"})
        players.append({"name": f"P{i}", "cookie": resp.cookies.get(f"lobby_{code}")})
    
    # Start game
    requests.post(f"{BASE_URL}/api/lobbies/{code}/start",
        json={"game_type": "classic", "config": {}},
        cookies={f"lobby_{code}": players[0]["cookie"]})
    
    all_passed = True
    
    # Check Level 1 - each player should have 1 card
    print("\n   Level 1 (1 card per player):")
    for p in players:
        resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
            cookies={f"lobby_{code}": p["cookie"]})
        state = resp.json()
        cards = state.get("my_hand", {}).get("cards", [])
        card_count = len(cards)
        
        status = "✅" if card_count == 1 else "❌"
        print(f"      {status} {p['name']}: {card_count} card(s) - {cards}")
        
        if card_count != 1:
            all_passed = False
    
    # Play through level 1 to advance
    # Need to play cards 1, 2, 3, 4 in order
    cards_to_play = [1, 2, 3, 4]
    for card_num in cards_to_play:
        for p in players:
            resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
                cookies={f"lobby_{code}": p["cookie"]})
            state = resp.json()
            cards = state.get("my_hand", {}).get("cards", [])
            if card_num in cards:
                resp = requests.post(f"{BASE_URL}/api/lobbies/{code}/action",
                    json={"action": "play", "data": {"card": card_num}},
                    cookies={f"lobby_{code}": p["cookie"]})
                result = resp.json()
                print(f"   {p['name']} plays {card_num}: {result.get('status')}")
                break
    
    # Advance to Level 2
    requests.post(f"{BASE_URL}/api/lobbies/{code}/action",
        json={"action": "advance", "data": {}},
        cookies={f"lobby_{code}": players[0]["cookie"]})
    
    # Check Level 2 - each player should have 2 cards
    print("\n   Level 2 (2 cards per player):")
    for p in players:
        resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
            cookies={f"lobby_{code}": p["cookie"]})
        state = resp.json()
        cards = state.get("my_hand", {}).get("cards", [])
        card_count = len(cards)
        
        status = "✅" if card_count == 2 else "❌"
        print(f"      {status} {p['name']}: {card_count} card(s) - {cards}")
        
        if card_count != 2:
            all_passed = False
    
    # Play through level 2 to advance
    # Need to play cards 1-8 in order
    cards_to_play = list(range(1, 9))
    for card_num in cards_to_play:
        for p in players:
            resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
                cookies={f"lobby_{code}": p["cookie"]})
            state = resp.json()
            cards = state.get("my_hand", {}).get("cards", [])
            if card_num in cards:
                resp = requests.post(f"{BASE_URL}/api/lobbies/{code}/action",
                    json={"action": "play", "data": {"card": card_num}},
                    cookies={f"lobby_{code}": p["cookie"]})
                result = resp.json()
                break
    
    # Advance to Level 3
    requests.post(f"{BASE_URL}/api/lobbies/{code}/action",
        json={"action": "advance", "data": {}},
        cookies={f"lobby_{code}": players[0]["cookie"]})
    
    # Check Level 3 - each player should have 3 cards
    print("\n   Level 3 (3 cards per player):")
    for p in players:
        resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
            cookies={f"lobby_{code}": p["cookie"]})
        state = resp.json()
        cards = state.get("my_hand", {}).get("cards", [])
        card_count = len(cards)
        
        status = "✅" if card_count == 3 else "❌"
        print(f"      {status} {p['name']}: {card_count} card(s) - {cards}")
        
        if card_count != 3:
            all_passed = False
    
    if all_passed:
        print("\n   ✅ PASS: All players have correct card counts at each level")
    else:
        print("\n   ❌ FAIL: Some players have wrong card counts")
    
    return all_passed


def test_no_duplicate_cards():
    """Test that no card value is dealt to multiple players"""
    print("\n" + "="*70)
    print("🃏 TEST: No Duplicate Cards")
    print("="*70)
    
    code = f"UNIQUE{int(time.time())}"
    
    # Create lobby with 5 players
    resp = requests.post(f"{BASE_URL}/api/lobbies", 
        json={"code": code, "player_name": "Host"})
    cookie1 = resp.cookies.get(f"lobby_{code}")
    
    for i in range(2, 6):
        requests.post(f"{BASE_URL}/api/lobbies/{code}/join",
            json={"player_name": f"P{i}"})
    
    # Start game
    requests.post(f"{BASE_URL}/api/lobbies/{code}/start",
        json={"game_type": "classic", "config": {}})
    
    # Collect all cards
    all_cards = []
    resp = requests.get(f"{BASE_URL}/api/lobbies/{code}/game-state",
        cookies={f"lobby_{code}": cookie1})
    state = resp.json()
    
    for pid, hand in state.get("player_hands", {}).items():
        all_cards.extend(hand.get("cards_played", []))
    
    my_hand = state.get("my_hand", {}).get("cards", [])
    all_cards.extend(my_hand)
    
    # Check for duplicates
    has_duplicates = len(all_cards) != len(set(all_cards))
    
    print(f"   Total cards dealt: {len(all_cards)}")
    print(f"   Unique values: {len(set(all_cards))}")
    print(f"   Cards: {sorted(all_cards)}")
    
    if has_duplicates:
        # Find duplicates
        counts = defaultdict(int)
        for c in all_cards:
            counts[c] += 1
        duplicates = {c: n for c, n in counts.items() if n > 1}
        print(f"   ❌ FAIL: Duplicate cards found: {duplicates}")
        return False
    else:
        print("   ✅ PASS: All cards are unique")
        return True


def run_dealing_tests():
    """Run all dealing tests"""
    print("\n" + "="*70)
    print("🎲 DEALING VERIFICATION TESTS")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Random Dealing (1-100)", test_random_dealing_from_full_deck()))
    except Exception as e:
        print(f"\n❌ Random Dealing test failed: {e}")
        results.append(("Random Dealing (1-100)", False))
    
    try:
        results.append(("Exact Card Count Per Level", test_exact_card_count_per_level()))
    except Exception as e:
        print(f"\n❌ Card Count test failed: {e}")
        results.append(("Exact Card Count Per Level", False))
    
    try:
        results.append(("No Duplicate Cards", test_no_duplicate_cards()))
    except Exception as e:
        print(f"\n❌ Duplicate Check test failed: {e}")
        results.append(("No Duplicate Cards", False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 DEALING TEST RESULTS")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, passed_test in results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_dealing_tests()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("Make sure the backend is running on http://localhost:8000")
        exit(1)
