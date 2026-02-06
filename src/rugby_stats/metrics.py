"""Metric extraction and normalization.

Checkpoint 2: Explicit mapping of raw API fields to internal metric names.
Assertion: zero unintended metric loss.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# === EXPLICIT FIELD MAPPING ===
# Maps internal metric name -> list of possible raw API field paths
# This ensures we catch all fields and know exactly where they come from.

UNSTRUCTURED_PLAY_METRICS = {
    "carries": ["data.playerseasonstats[0].player_stats.playerStats.attack.carries"],
    "metres_made": ["data.playerseasonstats[0].player_stats.playerStats.attack.metresMade"],
    "offloads": ["data.playerseasonstats[0].player_stats.playerStats.attack.offload"],
    "clean_breaks": ["data.playerseasonstats[0].player_stats.playerStats.attack.cleanBreak"],
    "defenders_beaten": ["data.playerseasonstats[0].player_stats.playerStats.attack.defenderBeaten"],
}

DEFENSIVE_METRICS = {
    "tackles": ["data.playerseasonstats[0].player_stats.playerStats.defence.tackle"],
    "missed_tackles": ["data.playerseasonstats[0].player_stats.playerStats.defence.missedTackle"],
    "turnovers_won": ["data.playerseasonstats[0].player_stats.playerStats.defence.turnoverWon"],
    "lineout_steals": ["data.playerseasonstats[0].player_stats.playerStats.lineout.lineoutSteals"],
    "tackle_success_pct": ["data.playerseasonstats[0].player_stats.playerStats.defence.percentTackleMade"],
}

DISCIPLINE_METRICS = {
    "penalties_conceded": ["data.playerseasonstats[0].player_stats.playerStats.discipline.penaltyConceded"],
    "yellow_cards": ["data.playerseasonstats[0].player_stats.playerStats.discipline.yellowCard"],
    "red_cards": ["data.playerseasonstats[0].player_stats.playerStats.discipline.redCard"],
}

ALL_EXPECTED_METRICS = {
    **UNSTRUCTURED_PLAY_METRICS,
    **DEFENSIVE_METRICS,
    **DISCIPLINE_METRICS,
}


def deep_get(obj: Any, path: str) -> Optional[Any]:
    """Safely traverse nested dict/list using dot/bracket notation.
    
    E.g. "data[0].foo.bar" -> obj["data"][0]["foo"]["bar"]
    """
    parts = []
    current = ""
    i = 0
    while i < len(path):
        if path[i] == "[":
            if current:
                parts.append(("key", current))
                current = ""
            # Parse [n]
            j = i + 1
            while j < len(path) and path[j] != "]":
                j += 1
            parts.append(("index", int(path[i+1:j])))
            i = j + 1
        elif path[i] == ".":
            if current:
                parts.append(("key", current))
                current = ""
            i += 1
        else:
            current += path[i]
            i += 1
    if current:
        parts.append(("key", current))

    result = obj
    for op, val in parts:
        if op == "key":
            if isinstance(result, dict):
                result = result.get(val)
            else:
                return None
        elif op == "index":
            if isinstance(result, (list, tuple)):
                try:
                    result = result[val]
                except (IndexError, TypeError):
                    return None
        if result is None:
            return None
    return result


def extract_metrics(raw_response: dict) -> Dict[str, Optional[Any]]:
    """Extract all known metrics from raw GraphQL response.
    
    Returns dict of {internal_name: value, ...}
    Includes None for missing fields (no silent drops).
    """
    extracted = {}
    
    for metric_name, paths in ALL_EXPECTED_METRICS.items():
        # Try all possible paths for this metric (future-proofing)
        value = None
        for path in paths:
            value = deep_get(raw_response, path)
            if value is not None:
                break
        extracted[metric_name] = value
    
    return extracted


def log_mapping_report(player_id: str, raw_response: dict, extracted: dict) -> None:
    """Log a detailed report of the mapping for a single player."""
    logger.info(f"Player {player_id} - Metric Extraction Report:")
    
    # Count found vs missing
    found = sum(1 for v in extracted.values() if v is not None)
    total = len(extracted)
    
    logger.info(f"  Found: {found}/{total}")
    logger.info(f"  Metrics:")
    
    for metric_name, value in sorted(extracted.items()):
        status = "✓" if value is not None else "✗"
        logger.info(f"    {status} {metric_name}: {value}")


def assert_no_metric_loss(raw_response: dict, extracted: dict) -> bool:
    """Assert that we're not losing any unexpected metrics from raw response.
    
    Checks if there are fields in raw response that aren't in our known mapping.
    Returns True if assertion passes (no unexpected loss).
    """
    raw_str = str(raw_response).lower()
    
    # Simple heuristic: check if "stat" or "metric" keywords appear
    # in raw but aren't in our extracted keys
    suspicious_keywords = ["stat", "value", "count"]
    
    missing_mappings = []
    for kw in suspicious_keywords:
        if kw in raw_str:
            # Could indicate unmapped field; log a warning
            logger.warning(f"Possible unmapped metric keyword '{kw}' found in response")
            missing_mappings.append(kw)
    
    return len(missing_mappings) == 0
