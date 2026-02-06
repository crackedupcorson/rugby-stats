#!/usr/bin/env python3
"""Runner to perform Validation Checkpoint 1: fetch one known Leinster player.

Usage:
  python3 scripts/fetch_single_player.py --player-id 12345

Or set environment variable `PLAYER_ID`.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from rugby_stats.client import fetch_player_season_stats, dump_pretty


EXPECTED_METRICS = [
    "carries",
    "metres",
    "offloads",
    "clean break",
    "defenders beaten",
    "tackles",
    "missed",
    "turnovers",
    "steals",
    "tackle success",
    "penalties",
    "yellow",
    "red",
    "minutes",
    "appearances",
]


def simple_presence_check(raw_json: dict, keywords: list) -> dict:
    s = json.dumps(raw_json).lower()
    present = {}
    for k in keywords:
        present[k] = (k.lower() in s)
    return present


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--player-id", type=str, help="Player ID to fetch (string)")
    p.add_argument("--season", type=int, default=202501)
    args = p.parse_args()

    player_id = args.player_id or os.environ.get("PLAYER_ID")
    if not player_id:
        print("Provide --player-id or set PLAYER_ID environment variable", file=sys.stderr)
        sys.exit(2)

    try:
        # player_id is a string; fetch function will convert to int
        raw = fetch_player_season_stats([player_id], season_id=args.season)
    except Exception as e:
        print("Request failed:", e, file=sys.stderr)
        sys.exit(3)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"raw_response_{player_id}.json"
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2)

    print("Raw GraphQL response saved to:", out_file)
    print("----- RAW RESPONSE -----")
    print(dump_pretty(raw))
    print("----- VALIDATION -----")

    presence = simple_presence_check(raw, EXPECTED_METRICS)
    missing = [k for k, v in presence.items() if not v]
    for k, v in presence.items():
        print(f"{k}: {'FOUND' if v else 'MISSING'}")

    if missing:
        print(f"Missing {len(missing)} expected metric keywords. See output file.")
        sys.exit(4)

    print("All expected metric keywords detected in raw response.")


if __name__ == "__main__":
    main()
