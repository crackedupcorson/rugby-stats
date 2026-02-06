# URC Player Performance Extraction Tool (pilot)

This small scaffold implements the code to reach Validation Checkpoint 1 from the project prompt:

- A GraphQL client that uses the known persisted query for `GetPlayerSeasonStats1`.
- A runner script to fetch one player and log the full raw GraphQL response.

Run the single-player validation (replace with a real Leinster player id):

```bash
python3 scripts/fetch_single_player.py --player-id 12345
```

Or set `PLAYER_ID` in your environment.

Files:
- `src/rugby_stats/client.py` : GraphQL client and helpers
- `scripts/fetch_single_player.py` : validation runner (saves raw JSON to `output/`)
# rugby-stats
contains rugby union player and team stats
