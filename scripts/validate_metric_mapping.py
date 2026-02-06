#!/usr/bin/env python3
"""Validation Checkpoint 2: Metric Mapping

Fetch multiple players, extract metrics using explicit mapping,
and assert zero unintended metric loss.

Usage:
  python3 scripts/validate_metric_mapping.py
"""
import argparse
import json
import logging
from pathlib import Path

from rugby_stats.client import fetch_player_season_stats
from rugby_stats.metrics import extract_metrics, log_mapping_report, assert_no_metric_loss

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def validate_single_player(player_id: str, season: int = 202501) -> dict:
    """Fetch and validate a single player."""
    logger.info(f"Fetching player {player_id}...")
    
    try:
        raw = fetch_player_season_stats([player_id], season_id=season)
    except Exception as e:
        logger.error(f"  Failed to fetch: {e}")
        return {"player_id": player_id, "error": str(e)}
    
    extracted = extract_metrics(raw)
    log_mapping_report(player_id, raw, extracted)
    
    # Check for metric loss
    no_loss = assert_no_metric_loss(raw, extracted)
    
    return {
        "player_id": player_id,
        "raw_response": raw,
        "extracted_metrics": extracted,
        "metrics_verified": no_loss,
    }


def main():
    p = argparse.ArgumentParser(description="Validate metric mapping for multiple players")
    p.add_argument(
        "--players",
        type=str,
        default="116468,114910,118531,144570,164116",
        help="Comma-separated player IDs to validate"
    )
    p.add_argument("--season", type=int, default=202501)
    args = p.parse_args()
    
    player_ids = [pid.strip() for pid in args.players.split(",")]
    
    logger.info(f"Validating metric mapping for {len(player_ids)} players...")
    logger.info(f"Season: {args.season}")
    logger.info("")
    
    results = []
    for player_id in player_ids:
        result = validate_single_player(player_id, args.season)
        results.append(result)
        logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("CHECKPOINT 2 SUMMARY")
    logger.info("=" * 60)
    
    successes = sum(1 for r in results if "error" not in r)
    failures = len(results) - successes
    
    logger.info(f"Processed: {len(results)} players")
    logger.info(f"Successful: {successes}")
    logger.info(f"Failed: {failures}")
    
    # Show metric extraction summary
    all_found = 0
    all_missing = 0
    for result in results:
        if "extracted_metrics" in result:
            extracted = result["extracted_metrics"]
            found = sum(1 for v in extracted.values() if v is not None)
            missing = len(extracted) - found
            all_found += found
            all_missing += missing
    
    if all_found + all_missing > 0:
        logger.info(f"Total metrics found: {all_found}/{all_found + all_missing}")
    
    # Save results to JSON
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "checkpoint2_results.json"
    
    # Convert extracted metrics to JSON-safe format
    json_results = []
    for r in results:
        json_r = {
            "player_id": r["player_id"],
        }
        if "error" in r:
            json_r["error"] = r["error"]
        else:
            json_r["extracted_metrics"] = r["extracted_metrics"]
            json_r["metrics_verified"] = r.get("metrics_verified", False)
        json_results.append(json_r)
    
    with out_file.open("w") as fh:
        json.dump(json_results, fh, indent=2)
    
    logger.info(f"Results saved to: {out_file}")
    logger.info("")
    logger.info("Checkpoint 2 validation complete!")


if __name__ == "__main__":
    main()
