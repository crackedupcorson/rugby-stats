"""Squad discovery via GetPlayerThemeSettingsById endpoint.

Fetches the full roster for a team without inferring or crawling.
"""
from typing import List, Dict, Any, Optional
import logging
import requests

logger = logging.getLogger(__name__)

ENDPOINT = "https://www.unitedrugby.com/graphql"
OPERATION_NAME = "GetPlayerThemeSettingsById"
PERSISTED_QUERY_HASH = "e1b82de16fadff0637731c7e7ca176c6f304685eb2760ea391fc1ee5745636ab"


def fetch_squad(
    club_id: str,
    endpoint: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Fetch squad information for a given club.
    
    Args:
        club_id: e.g., "5356" for Leinster
        endpoint: GraphQL endpoint URL (default: known URC endpoint)
        session: requests.Session (optional)
        timeout: request timeout in seconds
    
    Returns:
        raw squad response from GraphQL
    """
    endpoint = endpoint or ENDPOINT
    session = session or requests.Session()
    
    payload = {
        "operationName": OPERATION_NAME,
        "variables": {"currentClub": [club_id]},
        "extensions": {"persistedQuery": {"version": 1, "sha256Hash": PERSISTED_QUERY_HASH}},
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": "https://www.unitedrugby.com/",
    }
    
    import json
    params = {
        "operationName": OPERATION_NAME,
        "variables": json.dumps(payload["variables"]),
        "extensions": json.dumps(payload["extensions"]),
    }
    
    logger.info("GET %s (club=%s)", endpoint, club_id)
    resp = session.get(endpoint, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    
    return resp.json()


def extract_player_ids(raw_squad_response: Dict[str, Any]) -> List[tuple]:
    """Extract all player IDs from squad response.
    
    Returns:
        list of player IDs (as strings)
    """
    player_ids = []
    
    try:
        squads = raw_squad_response["data"]["playerThemeSettings"]["squads"]
        for squad in squads:
            for player in squad["squad"]:
                player_id = player.get("playerId")
                if player_id is not None:
                    name = f"{player.get('playerFirstName', '')} {player.get('playerLastName', '')}".strip()
                    player_ids.append((player_id, name))
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to extract player IDs: {e}")
        return []
    
    return player_ids


def extract_squad_details(raw_squad_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract full player details from squad response.
    
    Returns:
        list of {playerId, playerFirstName, playerLastName, playerPosition, ...}
    """
    players = []
    
    try:
        squads = raw_squad_response["data"]["playerThemeSettings"]["squads"]
        for squad in squads:
            for player in squad["squad"]:
                players.append({
                    "playerId": player.get("playerId"),
                    "firstName": player.get("playerFirstName"),
                    "lastName": player.get("playerLastName"),
                    "position": player.get("playerPosition"),
                    "age": player.get("playerAge"),
                    "nationality": player.get("nationalTeam"),
                })
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to extract squad details: {e}")
        return []
    
    return players
