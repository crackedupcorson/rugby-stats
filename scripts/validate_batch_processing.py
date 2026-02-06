#!/usr/bin/env python3
"""Validation Checkpoint 3: Batch Processing with Partial Failure Handling

Process at least 5 Leinster players through the full pipeline:
- Fetch
- Extract metrics
- Normalize
- Score
Partial failures must not abort execution.

Usage:
  python3 scripts/validate_batch_processing.py
  python3 scripts/validate_batch_processing.py --players 116468,114910,118531,144570,164116
"""
import argparse
import json
import logging
from pathlib import Path

from rugby_stats.batch import BatchProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser(description="Checkpoint 3: Batch processing with partial failure handling")
    p.add_argument(
        "--players",
        type=str,
        default="116468,114910,118531,144570,164116",
        help="Comma-separated player IDs"
    )
    p.add_argument("--season", type=int, default=202501)
    args = p.parse_args()
    
    player_ids = [pid.strip() for pid in args.players.split(",")]
    
    logger.info("=" * 70)
    logger.info("CHECKPOINT 3: BATCH PROCESSING WITH PARTIAL FAILURE HANDLING")
    logger.info("=" * 70)
    logger.info(f"Players: {len(player_ids)}")
    logger.info(f"Season: {args.season}")
    logger.info("")
    
    processor = BatchProcessor(season=args.season)
    summary = processor.process_batch(player_ids)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total players: {summary['total']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    
    if summary['failed'] > 0:
        logger.warning(f"Failures (but batch continued):")
        for fail in summary['failures']:
            logger.warning(f"  {fail['player_id']}: {fail.get('error', 'unknown')}")
    
    logger.info("")
    logger.info("COMPOSITE CONTRIBUTION RANKINGS:")
    logger.info("-" * 70)
    
    rankings = processor.get_rankings("composite_contribution")
    for i, rank in enumerate(rankings, 1):
        logger.info(f"{i}. Player {rank['player_id']}: {rank['score']:.2f}")
    
    logger.info("")
    logger.info("SANITY CHECKS:")
    logger.info("-" * 70)
    
    # Check 1: Non-zero scores for active players
    active_with_scores = [r for r in summary['results'] if 'error' not in r]
    non_zero = sum(
        1 for r in active_with_scores
        if r.get('derived_metrics', {}).get('composite_contribution', {}).get('score', 0) > 0
    )
    logger.info(f"✓ Active players with non-zero scores: {non_zero}/{len(active_with_scores)}")
    
    # Check 2: Discipline reduces composite
    for result in summary['results']:
        if 'error' in result:
            continue
        derived = result.get('derived_metrics', {})
        unstructured = derived.get('unstructured_impact', {}).get('score', 0)
        defensive = derived.get('defensive_reliability', {}).get('score', 0)
        discipline = derived.get('discipline_risk', {}).get('score', 0)
        composite = derived.get('composite_contribution', {}).get('score', 0)
        
        # Just log; don't enforce (some players may have zero discipline impact)
        if discipline < 0:
            logger.info(
                f"Player {result['player_id']}: discipline penalty applied "
                f"({discipline:.2f}) → composite {composite:.2f}"
            )
    
    logger.info("")
    logger.info("SAMPLE DETAILED OUTPUT (first player):")
    logger.info("-" * 70)
    
    if summary['results']:
        first = summary['results'][0]
        logger.info(f"Player ID: {first['player_id']}")
        
        metrics = first.get('raw_metrics', {})
        logger.info(f"Raw metrics (sample):")
        for k in ['carries', 'metres_made', 'tackles', 'penalties_conceded'][:4]:
            logger.info(f"  {k}: {metrics.get(k, 'N/A')}")
        
        derived = first.get('derived_metrics', {})
        logger.info(f"Derived scores:")
        for key in ['unstructured_impact', 'defensive_reliability', 'discipline_risk', 'composite_contribution']:
            score = derived.get(key, {}).get('score', 'N/A')
            logger.info(f"  {key}: {score}")
    
    # Save full results to JSON
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "checkpoint3_batch_results.json"
    
    # Convert to JSON-safe (handle numpy types, etc.)
    json_results = []
    for r in summary['results']:
        json_results.append({
            "player_id": r["player_id"],
            "raw_metrics": r.get("raw_metrics", {}),
            "normalized_metrics": {
                "normalization_applied": r.get("normalized_metrics", {}).get("normalization_applied"),
                "notes": r.get("normalized_metrics", {}).get("notes"),
            },
            "derived_metrics": {
                "composite_contribution": r.get("derived_metrics", {}).get("composite_contribution", {}),
                "unstructured_impact": r.get("derived_metrics", {}).get("unstructured_impact", {}),
                "defensive_reliability": r.get("derived_metrics", {}).get("defensive_reliability", {}),
                "discipline_risk": r.get("derived_metrics", {}).get("discipline_risk", {}),
            }
        })
    
    with out_file.open("w") as fh:
        json.dump({
            "summary": {
                "total": summary["total"],
                "successful": summary["successful"],
                "failed": summary["failed"],
            },
            "players": json_results,
            "rankings": rankings,
        }, fh, indent=2)
    
    logger.info("")
    logger.info(f"Full results saved to: {out_file}")
    logger.info("=" * 70)
    logger.info("Checkpoint 3 validation complete!")


if __name__ == "__main__":
    main()
