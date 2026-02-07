"""Role-based player classification and role-specific metric weighting.

Implements the role-based analysis framework:
- FRONT_5 (Loosehead, Hooker, Tighthead, Lock)
- BACK_ROW (6, 7, 8)
- HALF_BACKS (9, 10)
- BACKS (11, 12, 13, 14, 15)

Each role defines different metric weightings and performance expectations.
No single overall score without role context.
"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Map jersey numbers to position groups
POSITION_TO_ROLE = {
    # Front 5
    "1": "FRONT_5",  # Loosehead
    "2": "FRONT_5",  # Hooker
    "3": "FRONT_5",  # Tighthead
    "4": "FRONT_5",  # Lock
    "5": "FRONT_5",  # Lock
    # Back Row
    "6": "BACK_ROW",
    "7": "BACK_ROW",
    "8": "BACK_ROW",
    # Half-backs
    "9": "HALF_BACKS",
    "10": "HALF_BACKS",
    # Backs
    "11": "BACKS",
    "12": "BACKS",
    "13": "BACKS",
    "14": "BACKS",
    "15": "BACKS",
}

# Weight constants for each role
# These define what metrics matter for each position group

ROLE_WEIGHTS = {
    "FRONT_5": {
        "unstructured": {
            "carries": 0.25,
            "metres_made": 0.10,
            "offloads": 0.10,
            "clean_breaks": 0.10,
            "defenders_beaten": 0.10,
        },
        "defensive": {
            "tackles": 0.45,
            "tackle_success_pct": 0.30,
            "missed_tackles": -0.15,
            "turnovers_won": 0.10,
        },
        "discipline": {
            "penalties_conceded": -0.80,  # Front row penalties are very costly
            "yellow_cards": -2.0,
            "red_cards": -5.0,
        },
        "composite_blend": {
            "unstructured": 0.30,
            "defensive": 0.50,
            "discipline": 0.20,
        },
    },
    "BACK_ROW": {
        "unstructured": {
            "carries": 0.30,
            "metres_made": 0.15,
            "offloads": 0.15,
            "clean_breaks": 0.15,
            "defenders_beaten": 0.15,
        },
        "defensive": {
            "tackles": 0.40,
            "tackle_success_pct": 0.30,
            "missed_tackles": -0.15,
            "turnovers_won": 0.15,
        },
        "discipline": {
            "penalties_conceded": -0.50,
            "yellow_cards": -2.0,
            "red_cards": -5.0,
        },
        "composite_blend": {
            "unstructured": 0.40,
            "defensive": 0.40,
            "discipline": 0.20,
        },
    },
    "HALF_BACKS": {
        "unstructured": {
            "carries": 0.15,
            "metres_made": 0.15,
            "offloads": 0.25,
            "clean_breaks": 0.20,
            "defenders_beaten": 0.25,
        },
        "defensive": {
            "tackles": 0.35,
            "tackle_success_pct": 0.35,
            "missed_tackles": -0.15,
            "turnovers_won": 0.15,
        },
        "discipline": {
            "penalties_conceded": -0.50,
            "yellow_cards": -2.0,
            "red_cards": -5.0,
        },
        "composite_blend": {
            "unstructured": 0.45,
            "defensive": 0.35,
            "discipline": 0.20,
        },
    },
    "BACKS": {
        "unstructured": {
            "carries": 0.20,
            "metres_made": 0.30,
            "offloads": 0.15,
            "clean_breaks": 0.18,
            "defenders_beaten": 0.17,
        },
        "defensive": {
            "tackles": 0.30,
            "tackle_success_pct": 0.35,
            "missed_tackles": -0.20,
            "turnovers_won": 0.10,
        },
        "discipline": {
            "penalties_conceded": -0.30,  # Outside backs less penalized
            "yellow_cards": -2.0,
            "red_cards": -5.0,
        },
        "composite_blend": {
            "unstructured": 0.50,
            "defensive": 0.30,
            "discipline": 0.20,
        },
    },
}


def get_role_from_position(position: Optional[str]) -> Optional[str]:
    """Determine role from player position.
    
    Args:
        position: Jersey number as string or known position name (e.g., "no. 8", "8", "Hooker")
    
    Returns:
        Role name (FRONT_5, BACK_ROW, HALF_BACKS, BACKS) or None
    """
    if not position:
        return None
    
    # Normalize to string and clean up
    position_str = str(position).strip().lower()
    
    # Remove common prefixes like "no. " or "no "
    if position_str.startswith("no."):
        position_str = position_str.replace("no.", "").strip()
    elif position_str.startswith("no "):
        position_str = position_str.replace("no", "").strip()
    
    # Now check jersey number mapping
    if position_str in POSITION_TO_ROLE:
        return POSITION_TO_ROLE[position_str]
    
    # Case-insensitive role name check (in case passed directly)
    position_upper = position_str.upper()
    if position_upper in ROLE_WEIGHTS:
        return position_upper
    
    # Fuzzy matching for common position names
    if "front" in position_upper or "prop" in position_upper or "hook" in position_upper or "lock" in position_upper:
        return "FRONT_5"
    if "back_row" in position_upper or "flanker" in position_upper or "number" in position_upper or "openside" in position_upper or "blindside" in position_upper or "8" in position_upper:
        return "BACK_ROW"
    if "half" in position_upper or "scrum" in position_upper or "fly" in position_upper or "9" in position_upper or "10" in position_upper:
        return "HALF_BACKS"
    if "back" in position_upper or "wing" in position_upper or "centre" in position_upper or "full" in position_upper or "11" in position_upper or "12" in position_upper or "13" in position_upper or "14" in position_upper or "15" in position_upper:
        return "BACKS"
    
    logger.warning(f"Could not determine role from position: {position}")
    return None


def get_role_weights(role: Optional[str]) -> Dict[str, Dict[str, float]]:
    """Get metric weights for a specific role.
    
    Args:
        role: Role name (FRONT_5, BACK_ROW, HALF_BACKS, BACKS)
    
    Returns:
        dict with 'unstructured', 'defensive', 'discipline', 'composite_blend' weights
    """
    if not role or role not in ROLE_WEIGHTS:
        logger.warning(f"Unknown role: {role}, using BACK_ROW defaults")
        return ROLE_WEIGHTS["BACK_ROW"]
    
    return ROLE_WEIGHTS[role]


def extract_role_weights(
    role: Optional[str],
    metric_type: str = "unstructured"
) -> Dict[str, float]:
    """Extract weights for a specific metric type and role.
    
    Args:
        role: Role name
        metric_type: 'unstructured', 'defensive', 'discipline', or 'composite_blend'
    
    Returns:
        weight dict for that metric type
    """
    role_weights = get_role_weights(role)
    return role_weights.get(metric_type, {})
