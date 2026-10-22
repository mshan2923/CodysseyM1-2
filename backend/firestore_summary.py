from typing import Any

from firestore_service import read_analysis_rows


def _numbers(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def get_firestore_summary() -> dict:
    players = read_analysis_rows("players")
    prices = read_analysis_rows("prices")
    patches = read_analysis_rows("patches")
    events = read_analysis_rows("events")
    hubs = read_analysis_rows("hub")
    player_averages = _numbers(players, "Average Players") or _numbers(players, "value")
    changes = _numbers(patches, "change_pct_7d") or _numbers(patches, "value")
    followers = sorted(hubs, key=lambda row: str(row.get("date", "")))
    follower_values = _numbers(followers, "Followers") or _numbers(followers, "value")

    return {
        "source": "firestore",
        "period": _period(players, prices, patches, events, hubs),
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


def _period(*groups: list[dict[str, Any]]) -> str:
    dates = [str(row.get("date"))[:10] for group in groups for row in group if row.get("date")]
    if not dates:
        return "데이터 없음"
    return f"{min(dates)} ~ {max(dates)}"
