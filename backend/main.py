from contextlib import asynccontextmanager
import json
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_service import CustomAIService
from config import settings
from firestore_service import (
    create_conversation, create_data_record, delete_conversation, delete_data_record,
    firestore_is_configured, read_analysis_rows, read_conversation, read_conversations,
    update_conversation, update_data_record,
)
from firestore_summary import clear_summary_cache, get_firestore_summary
from schemas import ChatRequest, ChatResponse, ConversationCreate, ConversationUpdate, DataRecord, HealthResponse


_CHAT_CONTEXT_CACHE: tuple[float, str] | None = None
_CHAT_CONTEXT_CACHE_SECONDS = 3600


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ai_service = CustomAIService(settings)
    yield


app = FastAPI(
    title="Sephiria Insight API",
    description="세피리아 플레이어 분석을 위한 로컬 FastAPI 백엔드",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Sephiria Insight API",
        "docs": "/docs",
        "health": "/api/health",
        "summary": "/api/data/summary",
        "chat": "/api/chat",
    }


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", provider=settings.ai_base_url, model=settings.ai_model)


@app.get("/api/data/summary")
async def data_summary() -> dict:
    if not firestore_is_configured():
        raise HTTPException(status_code=503, detail="Firebase 인증 설정이 필요합니다.")
    try:
        return get_firestore_summary()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore summary failed: {exc}") from exc


@app.get("/api/data")
async def data_list(source: str | None = None, limit: int = 500) -> dict:
    if not firestore_is_configured():
        raise HTTPException(status_code=503, detail="Firebase 인증 설정이 필요합니다.")
    try:
        rows = read_analysis_rows(source, min(limit, 5000))
        return {"source": source or "all", "count": len(rows), "items": rows}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore read failed: {exc}") from exc


@app.post("/api/data")
async def data_create(record: DataRecord) -> dict:
    if not firestore_is_configured():
        raise HTTPException(status_code=503, detail="Firebase 인증 설정이 필요합니다.")
    try:
        payload = record.model_dump()
        record_id = create_data_record(payload)
        clear_summary_cache()
        return {"id": record_id, **payload}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore create failed: {exc}") from exc


@app.put("/api/data/{record_id}")
async def data_update(record_id: str, record: DataRecord) -> dict:
    try:
        payload = record.model_dump()
        update_data_record(record_id, payload)
        clear_summary_cache()
        return {"id": record_id, **payload}
    except KeyError:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore update failed: {exc}") from exc


@app.delete("/api/data/{record_id}")
async def data_delete(record_id: str) -> dict:
    try:
        delete_data_record(record_id)
        clear_summary_cache()
        return {"status": "deleted", "id": record_id}
    except KeyError:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore delete failed: {exc}") from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    global _CHAT_CONTEXT_CACHE
    try:
        if not firestore_is_configured():
            raise RuntimeError("Firebase 인증 설정이 필요합니다.")
        now = time.monotonic()
        if _CHAT_CONTEXT_CACHE and now - _CHAT_CONTEXT_CACHE[0] < _CHAT_CONTEXT_CACHE_SECONDS:
            context = _CHAT_CONTEXT_CACHE[1]
        else:
            summary = get_firestore_summary()
            # 작은 이벤트성 데이터(가격/패치)를 먼저 넣어 전체 컨텍스트가 잘려도
            # 질문에 직접 필요한 시간 정보가 남도록 한다.
            source_limits = {
                "prices": 50_000,
                "patches": 50_000,
                "events": 50_000,
                "hub": 60_000,
                "players": 120_000,
            }
            source_rows = {
                source: read_analysis_rows(source, limit=5000)
                for source in ("prices", "patches", "events", "hub", "players")
            }
            sections = [f"분석 요약:\n{json.dumps(summary, ensure_ascii=False, default=str)}"]
            for source, max_chars in source_limits.items():
                serialized = json.dumps(source_rows[source], ensure_ascii=False, default=str)
                if len(serialized) > max_chars:
                    serialized = serialized[:max_chars] + "... [이 source의 일부 행은 생략됨]"
                sections.append(f"[{source} 데이터]\n{serialized}")
            context = "\n\n".join(sections)
            _CHAT_CONTEXT_CACHE = (now, context)
        answer = await app.state.ai_service.chat(
            message=request.message,
            context=context,
            conversation=request.conversation,
        )
        return ChatResponse(answer=answer, model=settings.ai_model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc


@app.post("/api/conversations")
async def conversation_create(request: ConversationCreate) -> dict:
    try:
        messages = [message.model_dump() for message in request.messages]
        return {"id": create_conversation(request.title, messages), "title": request.title, "messages": messages}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Conversation create failed: {exc}") from exc


@app.get("/api/conversations")
async def conversation_list(limit: int = 50) -> dict:
    try:
        items = read_conversations(min(limit, 100))
        return {"count": len(items), "items": items}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Conversation read failed: {exc}") from exc


@app.get("/api/conversations/{conversation_id}")
async def conversation_detail(conversation_id: str) -> dict:
    item = read_conversation(conversation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return item


@app.put("/api/conversations/{conversation_id}")
async def conversation_update_route(conversation_id: str, request: ConversationUpdate) -> dict:
    try:
        messages = [message.model_dump() for message in request.messages]
        update_conversation(conversation_id, messages)
        return {"id": conversation_id, "messages": messages}
    except KeyError:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")


@app.delete("/api/conversations/{conversation_id}")
async def conversation_delete_route(conversation_id: str) -> dict:
    try:
        delete_conversation(conversation_id)
        return {"status": "deleted", "id": conversation_id}
    except KeyError:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
