#!/usr/bin/env python3
"""Lightweight read-only scraper for RugbyPass public team stats.

Constraints: only uses requests, beautifulsoup4, pandas, time (stdlib)

Creates CSV previews in data/preview_<team>.csv and saves simple logs to stdout.
"""
import os
import re
import time
import json
import random
from typing import Optional, Tuple, List
import argparse

import requests
from bs4 import BeautifulSoup
import pandas as pd


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; rugby-stats-bot/0.1; +https://github.com/crackedupcorson/rugby-stats)"
}


def fetch_page(url: str, timeout: int = 20) -> Tuple[Optional[str], int]:
    """Fetch a page and return (html, status_code)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None, 0
    if resp.status_code != 200:
        print(f"Non-200 for {url}: {resp.status_code}")
        return resp.text, resp.status_code
    return resp.text, resp.status_code


def extract_table(html: str) -> pd.DataFrame:
    """Attempt to find a sensible HTML table and return a DataFrame.

    Fallbacks:
    - Find first <table> in document
    - If none, look for role="table" elements and try to parse rows
    - If still none, return empty DataFrame
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1) Standard <table>
    table = soup.find("table")
    if table:
        # Use pandas to read the HTML snippet for better robustness
        try:
            dfs = pd.read_html(str(table))
            if dfs:
                return dfs[0]
        except Exception:
            pass

    # 2) role="table" or ARIA-based tables
    role_table = soup.find(attrs={"role": "table"})
    if role_table:
        rows = []
        for tr in role_table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cols:
                rows.append(cols)
        if rows:
            # make best-effort DataFrame: first row as header if lengths match
            maxlen = max(len(r) for r in rows)
            norm_rows = [r + [""] * (maxlen - len(r)) for r in rows]
            df = pd.DataFrame(norm_rows)
            # if first row looks like header (non-numeric), set it
            first = df.iloc[0].astype(str)
            if any(re.search(r"[A-Za-z]", str(x)) for x in first.values):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0]).reset_index(drop=True)
            return df

    # 3) No table found
    return pd.DataFrame()


def _try_parse_json(candidate: str):
    """Try to parse a JS-like JSON candidate to Python object with mild cleaning."""
    if not candidate or len(candidate) < 2:
        return None
    try:
        return json.loads(candidate)
    except Exception:
        # Attempt to clean common JS -> JSON patterns: unquoted keys, single quotes
        cleaned = candidate
        # quote unquoted keys like: key: -> "key":
        cleaned = re.sub(r'([\{,\s])(\w+)\s*:', r'\1"\2":', cleaned)
        cleaned = cleaned.replace("'", '"')
        try:
            return json.loads(cleaned)
        except Exception:
            return None


def find_embedded_json(html: str) -> dict:
    """Search <script> tags for JSON blobs referencing Opta, dataLayer or preloaded state.

    Returns a mapping of keys found to parsed JSON (best-effort).
    """
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    scripts = [s.string for s in soup.find_all("script") if s.string]
    combined = "\n".join(scripts)

    # Look for common window state variables
    keys_to_check = ["__INITIAL_STATE__", "__PRELOADED_STATE__", "__INITIAL_PROPS__", "pageData", "dataLayer"]
    for key in keys_to_check:
        m = re.search(rf"{re.escape(key)}\s*=\s*(\{{[\s\S]*?\}}|\[[\s\S]*?\])\s*;", combined)
        if m:
            parsed = _try_parse_json(m.group(1))
            if parsed is not None:
                results[key] = parsed

    # Heuristic: find any reasonably-large JSON-like object/array inside scripts
    for m in re.finditer(r"(\{[\s\S]{200,}\}|\[[\s\S]{200,}\])", combined):
        candidate = m.group(1)
        parsed = _try_parse_json(candidate)
        if parsed is not None:
            key = f"embedded_{len(results)+1}"
            results[key] = parsed

    # Specific look for Opta/dataLayer mentions per script
    for script in scripts:
        if "Opta" in script or "opta" in script or "dataLayer" in script:
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", script)
            if m:
                parsed = _try_parse_json(m.group(1))
                if parsed is not None:
                    results.setdefault("Opta_or_dataLayer", parsed)

    return results


def save_to_csv(df: pd.DataFrame, team_name: str) -> str:
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", f"preview_{team_name}.csv")
    df.to_csv(path, index=False)
    return path



def _process_and_save(html: str, tag: str, prefix: str, summary_entry: dict):
    """Extract table and embedded JSON from html and save artifacts with prefix."""
    if not html:
        return

    df = extract_table(html)
    if not df.empty:
        path = save_to_csv(df, prefix)
        print(f"Saved table for {prefix} to {path}; shape={df.shape}")
        summary_entry.update({f"{tag}_table_rows": int(df.shape[0]), f"{tag}_table_cols": int(df.shape[1]), f"{tag}_csv": path})
    else:
        print(f"No obvious HTML <table> for {prefix}")

    embedded = find_embedded_json(html)
    if embedded:
        os.makedirs("data", exist_ok=True)
        embed_path = os.path.join("data", f"preview_{prefix}_embedded.json")
        with open(embed_path, "w", encoding="utf-8") as f:
            json.dump(embedded, f, ensure_ascii=False, indent=2)
        print(f"Found embedded JSON for {prefix}; saved to {embed_path}")
        summary_entry[f"{tag}_embedded_json"] = embed_path
    else:
        print(f"No embedded Opta/dataLayer JSON found for {prefix}")


def parse_args():
    p = argparse.ArgumentParser(description="Scrape RugbyPass team stats preview")
    p.add_argument("--teams", help="Comma-separated list of team slugs (e.g. leinster,munster)", default="")
    p.add_argument("--urls-file", help="File with one URL per line to fetch instead of teams")
    p.add_argument("--throttle-min", type=float, default=10.0)
    p.add_argument("--throttle-max", type=float, default=20.0)
    return p.parse_args()


def main():
    args = parse_args()
    teams: List[str] = []
    urls: List[tuple] = []  # list of (prefix, url, tag)

    if args.urls_file:
        # read lines as raw URLs; prefix is sanitized filename from URL
        with open(args.urls_file, "r", encoding="utf-8") as f:
            for line in f:
                u = line.strip()
                if not u:
                    continue
                prefix = re.sub(r"[^0-9A-Za-z_-]", "_", u.split("/")[-2] if u.endswith("/") else u.split("/")[-1])
                urls.append((prefix, u, "url"))
    else:
        if args.teams:
            teams = [t.strip() for t in args.teams.split(",") if t.strip()]
        else:
            teams = ["ireland", "leinster", "munster", "ulster", "connacht"]

        for team in teams:
            team_page = f"https://www.rugbypass.com/teams/{team}/"
            fixtures_page = f"https://www.rugbypass.com/teams/{team}/fixtures-results/"
            urls.append((f"{team}", team_page, "team_page"))
            urls.append((f"{team}_fixtures", fixtures_page, "fixtures"))

    summary = []
    for prefix, url, tag in urls:
        print(f"\n---\nFetching {prefix} ({tag}): {url}")
        html, status = fetch_page(url)
        time_fetched = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = {"prefix": prefix, "url": url, "status": status, "fetched_at": time_fetched, "tag": tag}

        if not html:
            print(f"No HTML for {prefix} (status {status})")
            summary.append(entry)
            wait = random.uniform(args.throttle_min, args.throttle_max)
            print(f"Sleeping {wait:.1f}s")
            time.sleep(wait)
            continue

        _process_and_save(html, tag, prefix, entry)
        summary.append(entry)

        # Polite throttle between requests
        wait = random.uniform(args.throttle_min, args.throttle_max)
        print(f"Sleeping {wait:.1f}s before next request")
        time.sleep(wait)

    # Write a small summary CSV
    s_df = pd.DataFrame(summary)
    s_path = os.path.join("data", "preview_summary.csv")
    s_df.to_csv(s_path, index=False)
    print(f"\nSummary written to {s_path}")


if __name__ == "__main__":
    main()
