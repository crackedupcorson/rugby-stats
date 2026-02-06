"""Normalization: convert raw metrics to per-80-minute and per-appearance values.

Since the API doesn't currently provide minutes or appearances, we'll:
1. Accept them as optional parameters to normalize()
2. Fall back to raw values if unavailable
3. Track which normalization was applied
"""
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


def normalize_metrics(
    extracted_metrics: Dict[str, Optional[Any]],
    minutes_played: Optional[float] = None,
    appearances: Optional[int] = None,
) -> Dict[str, Any]:
    """Normalize metrics per 80 minutes or per appearance.
    
    Args:
        extracted_metrics: raw metrics dict from metrics.extract_metrics()
        minutes_played: total minutes in season (optional)
        appearances: total game appearances (optional)
    
    Returns:
        normalized_metrics: {
            "raw": {...},
            "per_80_min": {...},
            "per_appearance": {...},
            "normalization_applied": str,
            "notes": {...}
        }
    """
    normalized = {
        "raw": extracted_metrics.copy(),
        "per_80_min": {},
        "per_appearance": {},
        "normalization_applied": None,
        "notes": {},
    }
    
    # Metrics that make sense to normalize
    normalizable = [
        "carries",
        "metres_made",
        "offloads",
        "clean_breaks",
        "defenders_beaten",
        "tackles",
        "missed_tackles",
        "turnovers_won",
        "lineout_steals",
        "penalties_conceded",
    ]
    
    # Per 80 minutes normalization
    if minutes_played and minutes_played > 0:
        normalized["normalization_applied"] = "per_80_min"
        factor = 80.0 / minutes_played
        for metric in normalizable:
            val = extracted_metrics.get(metric)
            if val is not None and isinstance(val, (int, float)):
                normalized["per_80_min"][metric] = round(val * factor, 2)
            else:
                normalized["per_80_min"][metric] = val
        normalized["notes"]["minutes_played"] = minutes_played
    
    # Per appearance normalization (fallback)
    elif appearances and appearances > 0:
        normalized["normalization_applied"] = "per_appearance"
        factor = 1.0 / appearances
        for metric in normalizable:
            val = extracted_metrics.get(metric)
            if val is not None and isinstance(val, (int, float)):
                normalized["per_appearance"][metric] = round(val * factor, 2)
            else:
                normalized["per_appearance"][metric] = val
        normalized["notes"]["appearances"] = appearances
    
    else:
        normalized["normalization_applied"] = "raw (no minutes or appearances)"
        logger.warning("No minutes or appearances provided; using raw values")
    
    return normalized


def get_normalized_values(normalized_metrics: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    """Extract the best available normalized values (prefer per_80_min, fall back to raw)."""
    method = normalized_metrics.get("normalization_applied")
    
    if "per_80_min" in method:
        return normalized_metrics["per_80_min"]
    elif "per_appearance" in method:
        return normalized_metrics["per_appearance"]
    else:
        return normalized_metrics["raw"]
