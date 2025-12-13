#!/usr/bin/env python3
"""
Test script for Trello API client
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.trello import TrelloClient, TrelloAuthError, TrelloAPIError


def test_trello_client():
    """Test basic Trello client functionality"""
    
    print("="*80)
    print("TRELLO API CLIENT TEST")
    print("="*80)
    print()
    
    # Test 1: Authentication
    print("Test 1: Authentication")
    print("-"*80)
    try:
        client = TrelloClient()
        print("✅ Successfully authenticated with Trello")
        print(f"   API Key: {client.api_key[:8]}...")
        print(f"   Token: {client.token[:8]}...")
        print()
    except TrelloAuthError as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Test 2: Get user info
    print("Test 2: Get User Info")
    print("-"*80)
    try:
        me = client.get_me()
        print(f"✅ User: {me.get('fullName', 'Unknown')}")
        print(f"   Username: @{me.get('username', 'unknown')}")
        print(f"   ID: {me.get('id', 'unknown')}")
        print()
    except TrelloAPIError as e:
        print(f"❌ Failed to get user info: {e}")
        print()
    
    # Test 3: Get boards
    print("Test 3: Get Boards")
    print("-"*80)
    try:
        boards = client.get_boards()
        print(f"✅ Found {len(boards)} boards:")
        for i, board in enumerate(boards[:5], 1):
            print(f"   {i}. {board['name']} (ID: {board['id']})")
        if len(boards) > 5:
            print(f"   ... and {len(boards) - 5} more boards")
        print()
        
        # Store first board for next test
        test_board_id = boards[0]['id'] if boards else None
    except TrelloAPIError as e:
        print(f"❌ Failed to get boards: {e}")
        print()
        test_board_id = None
    
    # Test 4: Get board details
    if test_board_id:
        print("Test 4: Get Board Details")
        print("-"*80)
        try:
            board = client.get_board(test_board_id)
            print(f"✅ Board: {board['name']}")
            print(f"   URL: {board['url']}")
            print(f"   Description: {board.get('desc', 'No description')[:100]}")
            print()
        except TrelloAPIError as e:
            print(f"❌ Failed to get board details: {e}")
            print()
    
    # Test 5: Get board lists
    if test_board_id:
        print("Test 5: Get Board Lists")
        print("-"*80)
        try:
            lists = client.get_board_lists(test_board_id)
            print(f"✅ Found {len(lists)} lists:")
            for i, lst in enumerate(lists[:5], 1):
                print(f"   {i}. {lst['name']} (ID: {lst['id']})")
            if len(lists) > 5:
                print(f"   ... and {len(lists) - 5} more lists")
            print()
        except TrelloAPIError as e:
            print(f"❌ Failed to get lists: {e}")
            print()
    
    # Test 6: Get board cards
    if test_board_id:
        print("Test 6: Get Board Cards")
        print("-"*80)
        try:
            cards = client.get_board_cards(test_board_id)
            print(f"✅ Found {len(cards)} cards:")
            for i, card in enumerate(cards[:5], 1):
                print(f"   {i}. {card['name'][:60]}")
            if len(cards) > 5:
                print(f"   ... and {len(cards) - 5} more cards")
            print()
        except TrelloAPIError as e:
            print(f"❌ Failed to get cards: {e}")
            print()
    
    # Test 7: Context manager
    print("Test 7: Context Manager")
    print("-"*80)
    try:
        with TrelloClient() as client2:
            me = client2.get_me()
            print(f"✅ Context manager works: {me.get('fullName', 'Unknown')}")
        print()
    except Exception as e:
        print(f"❌ Context manager failed: {e}")
        print()
    
    print("="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == '__main__':
    # Check for credentials
    if not os.getenv('TRELLO_API_KEY') or not os.getenv('TRELLO_TOKEN'):
        print("⚠️  Missing credentials!")
        print()
        print("Set environment variables:")
        print("  export TRELLO_API_KEY='your_key_here'")
        print("  export TRELLO_TOKEN='your_token_here'")
        print()
        print("Get credentials from: https://trello.com/power-ups/admin")
        sys.exit(1)
    
    test_trello_client()
