import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COLLECTIONS = {
    "players": "players",
    "prices": "prices",
    "patches": "patches",
    "events": "events",
    "hub": "hub",
}
DATA_COLLECTION = "data"
CONVERSATIONS_COLLECTION = "conversations"
_ROWS_CACHE: dict[tuple[str | None, int], tuple[float, list[dict[str, Any]]]] = {}
_CACHE_SECONDS = 3600


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


def _data_rows(limit: int = 5000) -> list[dict[str, Any]]:
    client = _client()
    query = client.collection(DATA_COLLECTION).limit(limit)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def read_analysis_rows(source: str | None = None, limit: int = 5000) -> list[dict[str, Any]]:
    """운영 데이터는 Firestore만 읽는다. 기존 source별 컬렉션과 수동 입력 data를 모두 지원한다."""
    cache_key = (source, limit)
    cached = _ROWS_CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < _CACHE_SECONDS:
        return cached[1]
    rows = read_firestore_rows(source, limit)
    if rows:
        _ROWS_CACHE[cache_key] = (time.monotonic(), rows)
        return rows
    manual = _data_rows(limit)
    if source:
        manual = [row for row in manual if row.get("type") == source]
    manual = manual[:limit]
    _ROWS_CACHE[cache_key] = (time.monotonic(), manual)
    return manual


def clear_read_cache() -> None:
    _ROWS_CACHE.clear()


def create_data_record(record: dict[str, Any]) -> str:
    client = _client()
    ref = client.collection(DATA_COLLECTION).document()
    record = {**record, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}
    ref.set(record)
    clear_read_cache()
    return ref.id


def update_data_record(record_id: str, record: dict[str, Any]) -> None:
    client = _client()
    ref = client.collection(DATA_COLLECTION).document(record_id)
    if not ref.get().exists:
        raise KeyError(record_id)
    ref.set({**record, "updated_at": datetime.now(timezone.utc)}, merge=True)
    clear_read_cache()


def delete_data_record(record_id: str) -> None:
    client = _client()
    ref = client.collection(DATA_COLLECTION).document(record_id)
    if not ref.get().exists:
        raise KeyError(record_id)
    ref.delete()
    clear_read_cache()


def create_conversation(title: str, messages: list[dict[str, Any]]) -> str:
    client = _client()
    ref = client.collection(CONVERSATIONS_COLLECTION).document()
    now = datetime.now(timezone.utc)
    ref.set({"title": title, "messages": messages, "created_at": now, "updated_at": now})
    return ref.id


def read_conversations(limit: int = 50) -> list[dict[str, Any]]:
    client = _client()
    docs = client.collection(CONVERSATIONS_COLLECTION).order_by("updated_at", direction="DESCENDING").limit(limit).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def read_conversation(conversation_id: str) -> dict[str, Any] | None:
    doc = _client().collection(CONVERSATIONS_COLLECTION).document(conversation_id).get()
    return {"id": doc.id, **doc.to_dict()} if doc.exists else None


def update_conversation(conversation_id: str, messages: list[dict[str, Any]]) -> None:
    ref = _client().collection(CONVERSATIONS_COLLECTION).document(conversation_id)
    if not ref.get().exists:
        raise KeyError(conversation_id)
    ref.set({"messages": messages, "updated_at": datetime.now(timezone.utc)}, merge=True)


def delete_conversation(conversation_id: str) -> None:
    ref = _client().collection(CONVERSATIONS_COLLECTION).document(conversation_id)
    if not ref.get().exists:
        raise KeyError(conversation_id)
    ref.delete()


def firestore_is_configured() -> bool:
    return bool(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip() or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip())
