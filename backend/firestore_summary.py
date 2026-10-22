from typing import Any

from firestore_service import read_firestore_rows


def _numbers(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def get_firestore_summary() -> dict:
    players = read_firestore_rows("players")
    prices = read_firestore_rows("prices")
    patches = read_firestore_rows("patches")
    events = read_firestore_rows("events")
    hubs = read_firestore_rows("hub")
    player_averages = _numbers(players, "Average Players")
    changes = _numbers(patches, "change_pct_7d")
    followers = sorted(hubs, key=lambda row: str(row.get("date", "")))
    follower_values = _numbers(followers, "Followers")

    return {
        "source": "firestore",
        "period": "2025-04-03 ~ 2026-10-22",
        "counts": {
            "player_rows": len(players),
            "daily_average_player_values": len(player_averages),
            "price_snapshots": len(prices),
            "patch_days": len(patches),
            "patch_events": len(events),
            "hub_days": len(hubs),
        },
        "metrics": {
            "player_average_max": max(player_averages, default=None),
            "patch_change_max_pct": max(changes, default=None),
            "patch_change_min_pct": min(changes, default=None),
            "latest_hub_followers": follower_values[-1] if follower_values else None,
        },
    }
