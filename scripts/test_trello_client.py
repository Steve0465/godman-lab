#!/usr/bin/env python3
"""
Test script for the enhanced TrelloClient.

Usage:
    export TRELLO_KEY="your_key"
    export TRELLO_TOKEN="your_token"
    python3 scripts/test_trello_client.py
"""

import sys
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs"))

from trello_client import TrelloClient, TrelloError


def main():
    print("=" * 70)
    print("Testing TrelloClient")
    print("=" * 70)
    print()
    
    try:
        # Initialize client (will read from env vars)
        print("1. Initializing TrelloClient...")
        client = TrelloClient()
        print()
        
        # Test: Get Memphis Pool board
        print("2. Finding Memphis Pool board...")
        # First, get all boards to find Memphis Pool
        boards = client.request("GET", "members/me/boards")
        memphis_board = next(
            (b for b in boards if "memphis" in b["name"].lower() or "pool" in b["name"].lower()),
            None
        )
        
        if not memphis_board:
            print("❌ Memphis Pool board not found")
            return
        
        board_id = memphis_board["id"]
        print(f"✓ Found board: {memphis_board['name']} (ID: {board_id})")
        print()
        
        # Test: Get board lists
        print("3. Testing get_board_lists()...")
        lists = client.get_board_lists(board_id)
        bills_list = next((l for l in lists if l["name"].upper() == "BILLS"), None)
        
        if bills_list:
            print(f"✓ Found BILLS list: {bills_list['name']} (ID: {bills_list['id']})")
        else:
            print("⚠️  BILLS list not found")
        print()
        
        # Test: Get board cards
        print("4. Testing get_board_cards()...")
        cards = client.get_board_cards(
            board_id, 
            fields="id,shortLink,name,idList,dateLastActivity,desc"
        )
        print(f"Sample card: {cards[0]['name']}" if cards else "No cards found")
        print()
        
        # Test: Get specific card by shortlink
        if cards:
            print("5. Testing get_card() with first card...")
            test_card_shortlink = cards[0]["shortLink"]
            detailed_card = client.get_card(
                test_card_shortlink,
                attachments=True,
                actions=True,
                action_types="commentCard,addAttachmentToCard"
            )
            print(f"✓ Retrieved card with {len(detailed_card.get('attachments', []))} attachments")
            print()
        
        # Test: Get card by exact shortlink (like Z6JwfLEl from your example)
        print("6. Testing get_card() with specific shortlink...")
        try:
            specific_card = client.get_card(
                "Z6JwfLEl",  # Your example card
                attachments=True,
                actions=True
            )
            print(f"✓ Successfully fetched card: {specific_card.get('name', 'Unknown')}")
        except TrelloError as e:
            print(f"⚠️  Card Z6JwfLEl not found or not accessible: {e}")
        print()
        
        # Test: Download capability (without actually downloading)
        print("7. Testing download_url() capability...")
        test_card = next((c for c in cards if c.get("badges", {}).get("attachments", 0) > 0), None)
        
        if test_card:
            full_card = client.get_card(test_card["shortLink"], attachments=True, actions=False)
            if full_card.get("attachments"):
                attachment = full_card["attachments"][0]
                print(f"✓ Found attachment: {attachment['name']}")
                print(f"  URL: {attachment['url'][:60]}...")
                print(f"  (download_url() method available for actual download)")
            else:
                print("⚠️  Card has no attachments to test with")
        else:
            print("⚠️  No cards with attachments found for testing")
        print()
        
        print("=" * 70)
        print("✅ All tests completed successfully!")
        print("=" * 70)
        
    except TrelloError as e:
        print(f"\n❌ TrelloError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
