# Trello Board Audit - Usage

## Setup

1. Create a Trello API key and token: https://trello.com/app-key
2. Set environment variables (or add to .env):

```
export TRELLO_API_KEY=xxx
export TRELLO_TOKEN=yyy
export TRELLO_BOARD_ID=abcdef123456
```

3. (Optional) Copy the example list-role mapping and edit to match your lists:
```
cp config/trello_list_map.example.yml config/trello_list_map.yml
```

## Commands

- Sync a snapshot and actions (last 180 days by default):
```
godman trello sync --board $TRELLO_BOARD_ID --out data/trello
```

- Analyze and generate a Markdown report from existing files:
```
godman trello analyze data/trello/$TRELLO_BOARD_ID/snapshot_latest.json \
                       data/trello/$TRELLO_BOARD_ID/actions_latest.json \
                       --map config/trello_list_map.yml \
                       --out reports/trello_audit.md
```

- Run both in one step:
```
godman trello audit --board $TRELLO_BOARD_ID \
                    --map config/trello_list_map.yml \
                    --out data/trello --report reports/trello_audit.md
```

## Outputs

- data/trello/<board_id>/snapshot_YYYYMMDD.json and actions_YYYYMMDD.json
- data/trello/<board_id>/snapshot_latest.json and actions_latest.json (symlinks/pointers)
- reports/trello_audit.md with strengths, weaknesses, flow metrics, and recommendations
