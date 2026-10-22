import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_service import EVENT_FILE, HUB_FILE, PATCH_FILE, PLAYER_FILE, PRICE_FILE, read_csv


COLLECTIONS = {
    "players": "players",
    "prices": "prices",
    "patches": "patches",
    "events": "events",
    "hub": "hub",
}


def _collection_name(source: str) -> str:
    prefix = os.getenv("FIRESTORE_COLLECTION_PREFIX", "").strip()
    return f"{prefix}{COLLECTIONS[source]}"


def _client():
    """Firebase Admin SDK를 지연 초기화한다. 인증 설정 전에도 서버가 시작되도록 한다."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise RuntimeError("firebase-admin이 설치되지 않았습니다. pip install -r requirements.txt를 실행하세요.") from exc

    if firebase_admin._apps:
        return firestore.client()

    raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    credential_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    if raw_json:
        credential = credentials.Certificate(json.loads(raw_json))
    elif credential_path:
        path = Path(credential_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        credential = credentials.Certificate(str(path))
    else:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_PATH 또는 FIREBASE_SERVICE_ACCOUNT_JSON이 설정되지 않았습니다.")

    firebase_admin.initialize_app(credential)
    return firestore.client()


def _value(value: str) -> Any:
    if value == "":
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (ValueError, TypeError):
        return value


def _normalized_rows(source: str, path: Path) -> list[dict[str, Any]]:
    rows = read_csv(path)
    result = []
    for index, row in enumerate(rows):
        normalized = {key: _value(value) for key, value in row.items()}
        date_value = row.get("date") or row.get("DateTime", "")[:10]
        normalized.update({
            "source": source,
            "source_file": path.name,
            "source_index": index,
            "date": date_value,
            "imported_at": datetime.now(timezone.utc),
        })
        result.append(normalized)
    return result


def seed_csv_data() -> dict[str, int]:
    client = _client()
    sources = {
        "players": PLAYER_FILE,
        "prices": PRICE_FILE,
        "patches": PATCH_FILE,
        "events": EVENT_FILE,
        "hub": HUB_FILE,
    }
    counts: dict[str, int] = {}
    batch = client.batch()
    batch_size = 0

    for source, path in sources.items():
        collection = client.collection(_collection_name(source))
        rows = _normalized_rows(source, path)
        counts[source] = len(rows)
        for row in rows:
            document_id = f"{source}_{row['source_index']:05d}"
            batch.set(collection.document(document_id), row)
            batch_size += 1
            if batch_size == 450:
                batch.commit()
                batch = client.batch()
                batch_size = 0

    if batch_size:
        batch.commit()
    return counts


def read_firestore_rows(source: str | None = None, limit: int = 5000) -> list[dict[str, Any]]:
    client = _client()
    sources = [source] if source else list(COLLECTIONS)
    rows: list[dict[str, Any]] = []
    for current_source in sources:
        if current_source not in COLLECTIONS:
            raise ValueError(f"알 수 없는 데이터 source: {current_source}")
        query = client.collection(_collection_name(current_source)).limit(limit)
        rows.extend({"id": doc.id, **doc.to_dict()} for doc in query.stream())
        if len(rows) >= limit:
            return rows[:limit]
    return rows


def firestore_is_configured() -> bool:
    return bool(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip() or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip())
