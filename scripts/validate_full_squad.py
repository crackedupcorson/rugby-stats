#!/usr/bin/env python3
"""Validation Checkpoint 4: Full Leinster Squad Processing

Fetch all 69 Leinster players via GetPlayerThemeSettingsById,
then process all through the full pipeline with rate limiting.

Usage:
  python3 scripts/validate_full_squad.py
  python3 scripts/validate_full_squad.py --backoff 10 --club 5356
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any

from rugby_stats.squad import fetch_squad, extract_player_ids, extract_squad_details
from rugby_stats.batch import BatchProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser(description="Checkpoint 4: Full squad processing with rate limiting")
    p.add_argument("--club", type=str, default="5356", help="Club ID (default: 5356 = Leinster)")
    p.add_argument("--season", type=int, default=202501)
    p.add_argument("--backoff", type=float, default=10, help="Backoff between batches (seconds)")
    args = p.parse_args()
    
    logger.info("=" * 70)
    logger.info("CHECKPOINT 4: FULL SQUAD PROCESSING WITH RATE LIMITING")
    logger.info("=" * 70)
    logger.info(f"Club ID: {args.club}")
    logger.info(f"Season: {args.season}")
    logger.info(f"Backoff: {args.backoff}s between batches")
    logger.info("")
    
    # Step 1: Fetch squad
    logger.info("Step 1: Fetching squad roster...")
    try:
        raw_squad = fetch_squad(args.club)
    except Exception as e:
        logger.error(f"Failed to fetch squad: {e}")
        return
    
    player_ids = extract_player_ids(raw_squad)
    squad_details = extract_squad_details(raw_squad)
    
    logger.info(f"Found {len(player_ids)} players")
    logger.info("")
    
    # Save squad roster for reference
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    
    roster_file = out_dir / "leinster_squad_roster.json"
    with roster_file.open("w") as fh:
        json.dump({
            "club_id": args.club,
            "season": args.season,
            "total_players": len(squad_details),
            "players": squad_details,
        }, fh, indent=2)
    logger.info(f"Squad roster saved to: {roster_file}")
    logger.info("")
    
    # Step 2: Process all players
    logger.info("Step 2: Processing all players through pipeline...")
    logger.info(f"Batch size: 5, with {args.backoff}s backoff between batches")
    logger.info("")
    
    processor = BatchProcessor(season=args.season, backoff_seconds=args.backoff)
    summary = processor.process_batch(player_ids)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("CHECKPOINT 4 SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total players: {summary['total']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    
    if summary['failed'] > 0:
        logger.warning(f"Failed players:")
        for fail in summary['failures'][:10]:  # Show first 10
            logger.warning(f"  {fail['player_id']}: {fail.get('error', 'unknown')}")
        if len(summary['failures']) > 10:
            logger.warning(f"  ... and {len(summary['failures']) - 10} more")
    
    logger.info("")
    logger.info("TOP 20 PLAYERS (by Composite Score):")
    logger.info("-" * 70)
    
    rankings = processor.get_rankings("composite_contribution")
    for i, rank in enumerate(rankings[:20], 1):
        # Find player details
        player_detail = next((p for p in squad_details if str(p["playerId"]) == rank["player_id"]), {})
        name = f"{player_detail.get('firstName', '')} {player_detail.get('lastName', '')}"
        pos = player_detail.get('position', 'N/A')
        logger.info(f"{i:2}. {name:25} ({pos:12}) Score: {rank['score']:6.2f}")
    
    logger.info("")
    logger.info("DISTRIBUTION ANALYSIS:")
    logger.info("-" * 70)
    
    if rankings:
        scores = [r['score'] for r in rankings]
        min_score = min(scores)
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        logger.info(f"Min: {min_score:.2f}")
        logger.info(f"Max: {max_score:.2f}")
        logger.info(f"Avg: {avg_score:.2f}")
        logger.info(f"Range: {max_score - min_score:.2f}")
    
    # Save full results
    logger.info("")
    logger.info("SAVING RESULTS...")
    logger.info("-" * 70)
    
    results_file = out_dir / "checkpoint4_full_squad_results.json"
    
    # Convert results to JSON-safe format
    json_results = []
    for r in summary['results']:
        json_results.append({
            "player_id": r["player_id"],
            "raw_metrics": r.get("raw_metrics", {}),
            "normalized_metrics": {
                "normalization_applied": r.get("normalized_metrics", {}).get("normalization_applied"),
            },
            "derived_metrics": {
                "composite_contribution": r.get("derived_metrics", {}).get("composite_contribution", {}),
                "unstructured_impact": r.get("derived_metrics", {}).get("unstructured_impact", {}),
                "defensive_reliability": r.get("derived_metrics", {}).get("defensive_reliability", {}),
                "discipline_risk": r.get("derived_metrics", {}).get("discipline_risk", {}),
            }
        })
    
    with results_file.open("w") as fh:
        json.dump({
            "summary": {
                "total": summary["total"],
                "successful": summary["successful"],
                "failed": summary["failed"],
                "backoff_seconds": args.backoff,
            },
            "rankings": rankings,
            "players": json_results,
        }, fh, indent=2)
    
    logger.info(f"Full results saved to: {results_file}")
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("Checkpoint 4 validation complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
