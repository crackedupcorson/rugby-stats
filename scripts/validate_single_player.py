#!/usr/bin/env python3
"""Fetch one player's season stats and log raw response for validation checkpoint 1."""
import argparse
import json
import logging
import os
from pathlib import Path

from rugby_stats.client import GraphQLClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXPECTED_METRIC_KEYWORDS = [
    "carries",
    "metres",
    "offload",
    "clean",
    "break",
    "defender",
    "tackle",
    "miss",
    "turnover",
    "penalt",
    "yellow",
    "red",
]


def save_raw_response(player_id: int, data: dict) -> Path:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    out = logs_dir / f"raw_response_{player_id}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return out


def check_metric_presence(raw_json: dict) -> dict:
    s = json.dumps(raw_json).lower()
    found = {k: (k in s) for k in EXPECTED_METRIC_KEYWORDS}
    return found


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--player-id", type=int, required=True)
    p.add_argument("--season", type=int, default=202501)
    args = p.parse_args()

    client = GraphQLClient()
    logger.info("Fetching season %s for player %s", args.season, args.player_id)

    try:
        resp = client.fetch_player_season_stats([args.player_id], args.season)
    except Exception as e:
        logger.error("Failed to fetch player data: %s", e)
        return

    out = save_raw_response(args.player_id, resp)
    logger.info("Raw GraphQL response saved to %s", out)

    found = check_metric_presence(resp)
    logger.info("Metric keyword presence check (True=found):")
    for k, v in found.items():
        logger.info("  %s: %s", k, v)

    # Basic validation: ensure 'data' exists and is not null
    if "data" in resp and resp["data"]:
        logger.info("Response contains 'data' key and it is non-empty.")
    else:
        logger.warning("Response missing 'data' or it's empty. Inspect %s", out)


if __name__ == "__main__":
    main()
