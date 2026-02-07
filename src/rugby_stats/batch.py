"""Batch processor for multiple players with graceful partial failure handling.

Ensures that one player's failure doesn't abort the entire batch.
Supports configurable backoff between batches for rate limiting.
Detects and reports rate limit errors.
"""
from typing import List, Dict, Any, Optional
import logging
import time

from client import fetch_player_season_stats, RateLimitError
from metrics import extract_metrics
from normalization import normalize_metrics
from scoring import compute_all_scores

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple players; track successes and failures."""
    
    def __init__(self, season: int = 202501, backoff_seconds: float = 0):
        self.season = season
        self.backoff_seconds = backoff_seconds  # delay between batches
        self.results = []
        self.failures = []
    
    def process_player(
        self,
        player_id: str,
        player_name: str,
        minutes_played: Optional[float] = None,
        appearances: Optional[int] = None,
        position: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a single player; handle errors gracefully.
        
        Args:
            player_id: player ID
            player_name: player name
            minutes_played: optional minutes played (for normalization)
            appearances: optional number of appearances
            position: player position/jersey number (for role-based weighting)
        
        Returns:
            result dict with either 'error' or full pipeline output
        """
        result = {"player_id": player_id}
        
        try:
            # Fetch
        
            logger.info(f"Fetching player {player_id}{player_name}...")
            raw_response = fetch_player_season_stats([player_id], season_id=self.season)
            
            # Check for GraphQL errors
            if "errors" in raw_response:
                error_msg = str(raw_response["errors"])
                logger.error(f"  GraphQL error: {error_msg}")
                result["error"] = error_msg
                self.failures.append(result)
                return result
            
            result["name"]= player_name
            # Extract metrics
            extracted = extract_metrics(raw_response)
            result["raw_metrics"] = extracted
            
            # Normalize
            normalized = normalize_metrics(extracted, minutes_played, appearances)
            result["normalized_metrics"] = normalized
            
            # Score (with role-based weighting)
            derived = compute_all_scores(normalized, player_position=position)
            result["derived_metrics"] = derived
            result["position"] = position
            
            logger.info(f"  ✓ Composite score: {derived['composite_contribution']['score']:.2f}")
            self.results.append(result)
            
        except RateLimitError as e:
            logger.error(f"  RATE LIMIT: {e}", exc_info=False)
            result["error"] = f"Rate limit: {str(e)}"
            result["rate_limited"] = True
            if e.retry_after:
                result["retry_after_seconds"] = e.retry_after
                logger.warning(f"  Retry-After: {e.retry_after}s")
            self.failures.append(result)
            
        except Exception as e:
            logger.error(f"  Exception: {e}", exc_info=True)
            result["error"] = str(e)
            self.failures.append(result)
        
        return result
    
    def process_batch(
        self,
        player_ids: List[tuple],
        minutes_played: Optional[float] = None,
        appearances: Optional[int] = None,
        player_details: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Process all players in batch; partial failures allowed.
        
        Applies backoff_seconds delay between batches for rate limiting.
        
        Args:
            player_ids: list of (player_id, player_name) tuples
            minutes_played: optional minutes played (for normalization)
            appearances: optional number of appearances
            player_details: optional list of dicts with 'playerId', 'position', etc.
        
        Returns:
            summary: {
                "total": int,
                "successful": int,
                "failed": int,
                "results": [...],
                "failures": [...],
            }
        """
        logger.info(f"Processing batch of {len(player_ids)} players (season {self.season})...")
        
        self.results = []
        self.failures = []
        
        # Build position lookup from player_details
        position_lookup = {}
        if player_details:
            for detail in player_details:
                player_id = detail.get("playerId")
                position = detail.get("position")
                if player_id and position:
                    position_lookup[str(player_id)] = position
        
        # Process in sub-batches with backoff
        batch_size = 5
        for i in range(0, len(player_ids), batch_size):
            batch = player_ids[i:i+batch_size]
            logger.info(f"Processing sub-batch {i//batch_size + 1} ({len(batch)} players)...")
            
            for player_id, player_name in batch:
                # Look up position if available
                position = position_lookup.get(str(player_id))
                self.process_player(player_id, player_name, minutes_played, appearances, position=position)
            
            # Apply backoff between batches (except after the last one)
            if i + batch_size < len(player_ids) and self.backoff_seconds > 0:
                logger.info(f"Backoff: sleeping {self.backoff_seconds}s before next batch...")
                time.sleep(self.backoff_seconds)
        
        summary = {
            "total": len(player_ids),
            "successful": len(self.results),
            "failed": len(self.failures),
            "results": self.results,
            "failures": self.failures,
        }
        
        return summary
    
    def get_rankings(self, metric_key: str = "composite_contribution") -> List[Dict[str, Any]]:
        """Rank successful players by a derived metric.
        
        Args:
            metric_key: one of 'composite_contribution', 'unstructured_impact', etc.
        
        Returns:
            sorted list of {player_id, score, ...}
        """
        rankings = []
        
        for result in self.results:
            if "error" in result:
                continue
            
            derived = result.get("derived_metrics", {})
            metric = derived.get(metric_key, {})
            score = metric.get("score")
            
            if score is not None:
                rankings.append({
                    "player_id": result["player_id"],
                    "score": score,
                    "metric": metric_key,
                })
        
        # Sort descending
        rankings.sort(key=lambda x: x["score"], reverse=True)
        return rankings
