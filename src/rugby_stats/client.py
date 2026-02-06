import json
import logging
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DEFAULT_ENDPOINT = "https://www.unitedrugby.com/graphql"
OPERATION_NAME = "GetPlayerSeasonStats1"
PERSISTED_QUERY_HASH = "0a0022eeecff7bbdae5667322bd51a42cac3c9260bd116acd4e3e338b314ce28"


class RateLimitError(Exception):
    """Raised when rate limit is detected."""
    def __init__(self, retry_after: Optional[int] = None, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        super().__init__(message)


def _check_rate_limits(response: requests.Response, data: dict) -> None:
    """Check for rate limit indicators in response.
    
    Raises RateLimitError if rate limiting is detected.
    """
    # Check HTTP 429
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        retry_seconds = int(retry_after) if retry_after else None
        logger.warning(f"HTTP 429 Too Many Requests. Retry-After: {retry_after}")
        raise RateLimitError(retry_after=retry_seconds, message="HTTP 429 Too Many Requests")
    
    # Check for rate limit headers
    if response.status_code == 503:
        logger.warning("HTTP 503 Service Unavailable (possible rate limit)")
        raise RateLimitError(message="HTTP 503 Service Unavailable")
    
    # Check GraphQL response for rate limit errors
    if isinstance(data, dict) and "errors" in data:
        errors = data.get("errors", [])
        for error in errors:
            if isinstance(error, dict):
                message = error.get("message", "").lower()
                # Look for common rate limit messages
                if any(kw in message for kw in ["rate", "limit", "quota", "throttle", "too many"]):
                    logger.warning(f"GraphQL rate limit detected: {error.get('message')}")
                    raise RateLimitError(message=error.get("message", "Rate limit in GraphQL"))
    
    # Check custom headers that some APIs use
    for header_name in ["X-RateLimit-Remaining", "X-RateLimit-Limit", "RateLimit-Remaining"]:
        if header_name in response.headers:
            remaining = response.headers.get(header_name)
            logger.debug(f"{header_name}: {remaining}")
            # Warn if getting low
            try:
                if int(remaining) < 5:
                    logger.warning(f"⚠️  Rate limit approaching: {remaining} requests remaining")
            except (ValueError, TypeError):
                pass


def fetch_player_season_stats(
    player_ids: List[str],
    season_id: int = 202501,
    endpoint: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
) -> dict:
    """Fetch season stats for one or more players using the known persisted query.

    Uses GET with query parameters (no POST body).
    player_ids can be strings; they will be converted to integers for the API.
    
    Raises:
        RateLimitError if rate limiting is detected.
    """
    endpoint = endpoint or DEFAULT_ENDPOINT
    session = session or requests.Session()

    # Convert player IDs to integers
    int_player_ids = [int(pid) for pid in player_ids]
    variables = {"player_id": int_player_ids, "season_id": [season_id]}
    extensions = {"persistedQuery": {"version": 1, "sha256Hash": PERSISTED_QUERY_HASH}}

    params = {
        "operationName": OPERATION_NAME,
        "variables": json.dumps(variables),
        "extensions": json.dumps(extensions),
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": "https://www.unitedrugby.com/",
    }

    logger.info("GET %s (players=%s season=%s)", endpoint, player_ids, season_id)
    resp = session.get(endpoint, params=params, headers=headers, timeout=timeout)
    
    try:
        data = resp.json()
    except ValueError:
        # fallback: return raw text wrapped
        data = {"text": resp.text}
    
    # Check for rate limits before raising for HTTP errors
    _check_rate_limits(resp, data)
    
    # Raise for other HTTP errors (after rate limit check)
    resp.raise_for_status()

    return data


def dump_pretty(data: dict) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
import json
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

GRAPHQL_ENDPOINT = "https://www.unitedrugby.com/graphql"

# Persisted query details from the prompt
PLAYER_SEASON_STATS_PERSISTED = {
    "version": 1,
    "sha256Hash": "0a0022eeecff7bbdae5667322bd51a42cac3c9260bd116acd4e3e338b314ce28",
}


class GraphQLClient:
    def __init__(self, endpoint: str = GRAPHQL_ENDPOINT, session: requests.Session = None):
        self.endpoint = endpoint
        self.session = session or requests.Session()

    def fetch_player_season_stats(self, player_ids: List[int], season_id: int) -> Dict[str, Any]:
        payload = {
            "operationName": "GetPlayerSeasonStats1",
            "variables": {"player_id": player_ids, "season_id": [season_id]},
            "extensions": {"persistedQuery": PLAYER_SEASON_STATS_PERSISTED},
        }

        logger.debug("Posting GraphQL payload: %s", json.dumps(payload))

        resp = self.session.post(self.endpoint, json=payload, timeout=30)

        # Always return the raw status and body so the caller can save and
        # inspect it for validation, even when the remote returns a non-200.
        result = {"http_status": resp.status_code}
        text = resp.text
        # Try parse JSON if possible
        try:
            result["body"] = resp.json()
        except ValueError:
            result["body"] = text

        if resp.status_code >= 400:
            logger.warning("GraphQL request returned status %s", resp.status_code)

        return result
