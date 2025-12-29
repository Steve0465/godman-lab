from fastapi import APIRouter, HTTPException, Depends, Query
from godman_ai.services.trello_client import get_cards
from godman_ai.server.security import get_api_key

router = APIRouter(prefix="/api/trello", tags=["Trello"])


@router.get("/cards", dependencies=[Depends(get_api_key)])
def list_trello_cards(
    board: str,
    list_name: str = Query(..., alias="list"),
):
    """
    Read-only endpoint to list cards from a Trello board/list.

    Example:
      /api/trello/cards?board=memphis_pool&list=BILLS
    """
    try:
        cards = get_cards(board, list_name)
        return {
            "board": board,
            "list": list_name,
            "count": len(cards),
            "cards": [
                {"id": c["id"], "name": c["name"], "url": c["url"]}
                for c in cards
            ],
        }
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Trello cards")

