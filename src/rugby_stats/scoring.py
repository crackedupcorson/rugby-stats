"""Derived scoring metrics with configurable weights.

Computes:
- Unstructured Impact Score
- Defensive Reliability Score
- Discipline Risk Index
- Composite Player Contribution Score
"""
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


# === CONFIGURABLE WEIGHT CONSTANTS ===
# Easily adjustable per rugby domain knowledge

UNSTRUCTURED_PLAY_WEIGHTS = {
    "carries": 0.20,
    "metres_made": 0.25,
    "offloads": 0.15,
    "clean_breaks": 0.20,
    "defenders_beaten": 0.20,
}

DEFENSIVE_RELIABILITY_WEIGHTS = {
    "tackles": 0.40,
    "tackle_success_pct": 0.35,  # percentage, normalized 0-100
    "missed_tackles": -0.15,  # negative (penalty)
    "turnovers_won": 0.10,
}

DISCIPLINE_RISK_WEIGHTS = {
    "penalties_conceded": -0.50,  # each penalty is costly
    "yellow_cards": -2.0,  # yellow card is very costly
    "red_cards": -5.0,  # red card is extremely costly
}

# Composite blend (weights for the three sub-scores)
COMPOSITE_BLEND_WEIGHTS = {
    "unstructured": 0.40,
    "defensive": 0.40,
    "discipline": 0.20,  # negative influence
}


def compute_unstructured_impact_score(
    metrics: Dict[str, Optional[Any]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Compute unstructured play impact (attack, ball-winning, evasion).
    
    Returns score (0-100 scale) and component breakdown.
    """
    weights = weights or UNSTRUCTURED_PLAY_WEIGHTS
    
    components = {}
    total_weighted = 0.0
    
    for metric, weight in weights.items():
        val = metrics.get(metric)
        if val is not None and isinstance(val, (int, float)):
            components[metric] = val
            # Scale using realistic season benchmarks (per-game avg ~)
            if metric == "carries":
                scaled = min(100, max(0, (val / 60) * 100))  # 60 carries = exceptional
            elif metric == "metres_made":
                scaled = min(100, max(0, (val / 150) * 100))  # 150m = exceptional
            elif metric == "offloads":
                scaled = min(100, max(0, (val / 10) * 100))  # 10 offloads = exceptional
            elif metric == "clean_breaks":
                scaled = min(100, max(0, (val / 8) * 100))  # 8 clean breaks = exceptional
            elif metric == "defenders_beaten":
                scaled = min(100, max(0, (val / 15) * 100))  # 15 defenders = exceptional
            else:
                scaled = val
            
            total_weighted += scaled * weight
        else:
            components[metric] = None
    
    # Average weighted score (all weights sum to 1.0)
    score = max(0, min(100, total_weighted * 100))
    
    return {
        "score": round(score, 2),
        "components": components,
        "method": "weighted attack metrics (0-100)",
    }


def compute_defensive_reliability_score(
    metrics: Dict[str, Optional[Any]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Compute defensive consistency (tackling, turnovers, success %).
    
    Returns score (0-100) and breakdown.
    """
    weights = weights or DEFENSIVE_RELIABILITY_WEIGHTS
    
    components = {}
    total_weighted = 0.0
    
    for metric, weight in weights.items():
        val = metrics.get(metric)
        if val is not None and isinstance(val, (int, float)):
            components[metric] = val
            
            if metric == "tackles":
                scaled = min(100, max(0, (val / 40) * 100))  # 40 tackles = exceptional
            elif metric == "tackle_success_pct":
                scaled = val  # already 0-100
            elif metric == "missed_tackles":
                scaled = min(100, max(0, (val / 12) * 100))  # 12+ missed = problematic
            elif metric == "turnovers_won":
                scaled = min(100, max(0, (val / 6) * 100))  # 6 turnovers = exceptional
            else:
                scaled = val
            
            total_weighted += scaled * weight
        else:
            components[metric] = None
    
    score = max(0, min(100, total_weighted * 100))
    
    return {
        "score": round(score, 2),
        "components": components,
        "method": "weighted defence metrics (0-100)",
    }


def compute_discipline_risk_index(
    metrics: Dict[str, Optional[Any]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Compute discipline cost (penalties, cards).
    
    Returns score (0-100 where 0 = high risk, 100 = clean).
    """
    weights = weights or DISCIPLINE_RISK_WEIGHTS
    
    components = {}
    total_weighted = 0.0
    
    for metric, weight in weights.items():
        val = metrics.get(metric)
        if val is not None and isinstance(val, (int, float)):
            components[metric] = val
            total_weighted += val * weight
        else:
            components[metric] = None
    
    # Convert to 0-100 scale: more negative cost = lower score
    # Clamp to [0, 100]
    risk_penalty = max(-100, total_weighted)  # -100 is catastrophic
    score = max(0, min(100, 100 + risk_penalty))
    
    return {
        "score": round(score, 2),  # 100 = clean, 0 = very risky
        "components": components,
        "method": "weighted discipline costs (0-100)",
    }


def compute_composite_contribution_score(
    unstructured_score: float,
    defensive_score: float,
    discipline_score: float,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Blend the three sub-scores into a composite 0-100 player value.
    
    All inputs are 0-100 scale.
    """
    weights = weights or COMPOSITE_BLEND_WEIGHTS
    
    total = (
        unstructured_score * weights["unstructured"]
        + defensive_score * weights["defensive"]
        + discipline_score * weights["discipline"]
    )
    
    total_weights = sum(weights.values())
    composite = (total / total_weights) if total_weights > 0 else 0
    composite = max(0, min(100, composite))
    
    return {
        "score": round(composite, 2),
        "breakdown": {
            "unstructured": round(unstructured_score * weights["unstructured"] / total_weights, 2),
            "defensive": round(defensive_score * weights["defensive"] / total_weights, 2),
            "discipline": round(discipline_score * weights["discipline"] / total_weights, 2),
        },
        "method": "composite blend (attack 40%, defence 40%, discipline 20%)",
    }


def compute_all_scores(
    normalized_metrics: Dict[str, Optional[Any]],
) -> Dict[str, Any]:
    """Compute all derived scores for a player.
    
    Args:
        normalized_metrics: dict with 'raw', 'per_80_min', 'per_appearance', etc.
    
    Returns:
        all_scores: {
            'unstructured_impact': {...},
            'defensive_reliability': {...},
            'discipline_risk': {...},
            'composite_contribution': {...},
        }
    """
    # Use best available normalization
    if normalized_metrics.get("per_80_min"):
        metrics_to_use = normalized_metrics["per_80_min"]
    elif normalized_metrics.get("per_appearance"):
        metrics_to_use = normalized_metrics["per_appearance"]
    else:
        metrics_to_use = normalized_metrics.get("raw", {})
    
    unstructured = compute_unstructured_impact_score(metrics_to_use)
    defensive = compute_defensive_reliability_score(metrics_to_use)
    discipline = compute_discipline_risk_index(metrics_to_use)
    composite = compute_composite_contribution_score(
        unstructured["score"],
        defensive["score"],
        discipline["score"],
    )
    
    return {
        "unstructured_impact": unstructured,
        "defensive_reliability": defensive,
        "discipline_risk": discipline,
        "composite_contribution": composite,
    }
