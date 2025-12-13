#!/usr/bin/env python3
"""
Example: Using the Trello client to access Memphis Pool board
"""

from trello import TrelloClient
import json

# Initialize client
client = TrelloClient()

print("="*80)
print("MEMPHIS POOL BOARD - EXAMPLE")
print("="*80)
print()

# Find Memphis Pool board
boards = client.get_boards()
memphis_board = next((b for b in boards if "Memphis Pool" in b['name']), None)

if not memphis_board:
    print("❌ Memphis Pool board not found")
    print("\nAvailable boards:")
    for board in boards:
        print(f"  • {board['name']}")
    exit(1)

print(f"✅ Found board: {memphis_board['name']}")
print(f"   URL: {memphis_board['url']}")
print(f"   ID: {memphis_board['id']}")
print()

# Get lists
lists = client.get_board_lists(memphis_board['id'])
print(f"📋 Lists ({len(lists)}):")
for lst in lists:
    print(f"   • {lst['name']}")
print()

# Get cards with full details
cards = client.get_board_cards(
    memphis_board['id'],
    attachments="true",
    checklists="all"
)

print(f"📇 Cards: {len(cards)} total")
print()

# Organize by list
cards_by_list = {}
for card in cards:
    list_id = card['idList']
    if list_id not in cards_by_list:
        cards_by_list[list_id] = []
    cards_by_list[list_id].append(card)

# Show breakdown
for lst in lists:
    count = len(cards_by_list.get(lst['id'], []))
    if count > 0:
        print(f"   {lst['name']:35s} {count:3d} cards")

print()

# Find unbilled jobs
unbilled_list = next((l for l in lists if "bill" in l['name'].lower() and "need" in l['name'].lower()), None)

if unbilled_list:
    unbilled_cards = cards_by_list.get(unbilled_list['id'], [])
    print(f"💵 Unbilled Jobs: {len(unbilled_cards)}")
    for card in unbilled_cards[:5]:
        print(f"   • {card['name'][:70]}")
    if len(unbilled_cards) > 5:
        print(f"   ... and {len(unbilled_cards) - 5} more")
    print()

# Export summary
summary = {
    'board_name': memphis_board['name'],
    'board_url': memphis_board['url'],
    'total_lists': len(lists),
    'total_cards': len(cards),
    'lists': [
        {
            'name': lst['name'],
            'card_count': len(cards_by_list.get(lst['id'], []))
        }
        for lst in lists
    ]
}

print("="*80)
print(f"✅ Summary:")
print(f"   Board: {summary['board_name']}")
print(f"   Lists: {summary['total_lists']}")
print(f"   Cards: {summary['total_cards']}")
print("="*80)
