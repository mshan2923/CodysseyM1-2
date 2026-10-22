import csv
from datetime import date
from pathlib import Path

from config import PROJECT_DIR


PLAYER_FILE = PROJECT_DIR / "steamdb_Player_chart.csv"
PRICE_FILE = PROJECT_DIR / "steamdb_Price_chart.csv"
PATCH_FILE = PROJECT_DIR / "patch_analysis.csv"
EVENT_FILE = PROJECT_DIR / "event_analysis.csv"
HUB_FILE = PROJECT_DIR / "steamdb_Hub_chart.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _number(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _round(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if value.is_integer() else round(value, 2)


def get_data_summary() -> dict:
    players = read_csv(PLAYER_FILE)
    prices = read_csv(PRICE_FILE)
    patches = read_csv(PATCH_FILE)
    events = read_csv(EVENT_FILE)
    hubs = read_csv(HUB_FILE)

    average_players = [_number(row.get("Average Players")) for row in players]
    average_players = [value for value in average_players if value is not None]
    changes = [_number(row.get("change_pct_7d")) for row in patches]
    changes = [value for value in changes if value is not None]
    followers = [_number(row.get("Followers")) for row in hubs]
    followers = [value for value in followers if value is not None]

    return {
        "period": "2025-04-03 ~ 2026-10-22",
        "counts": {
            "player_rows": len(players),
            "daily_average_player_values": len(average_players),
            "price_snapshots": len(prices),
            "patch_days": len(patches),
            "patch_events": len(events),
            "hub_days": len(hubs),
        },
        "metrics": {
            "player_average_max": _round(max(average_players, default=None)),
            "patch_change_max_pct": _round(max(changes, default=None)),
            "patch_change_min_pct": _round(min(changes, default=None)),
            "latest_hub_followers": _round(followers[-1] if followers else None),
        },
        "major_findings": [
            "메이저 패치 5개 모두 이후 7일 평균 플레이어 수가 이전보다 높았다.",
            "1.0 정식 출시 이벤트의 7일 변화율은 약 +1,388%였다.",
            "0.8.3, 0.10.0, 0.11.0, 1.0은 플라시보 기준 상위 변동으로 관찰되었다.",
            "가격 데이터는 변경 시점 스냅샷이라 가격과 플레이어 수의 인과관계는 단정할 수 없다.",
        ],
        "data_sources": [
            "steamdb_Player_chart.csv",
            "steamdb_Price_chart.csv",
            "patch_analysis.csv",
            "event_analysis.csv",
            "steamdb_Hub_chart.csv",
        ],
    }


def build_analysis_context() -> str:
    summary = get_data_summary()
    lines = [
        f"분석 기간: {summary['period']}",
        f"데이터 건수: {summary['counts']}",
        f"주요 지표: {summary['metrics']}",
        "주요 관찰:",
        *[f"- {finding}" for finding in summary["major_findings"]],
    ]
    return "\n".join(lines)
