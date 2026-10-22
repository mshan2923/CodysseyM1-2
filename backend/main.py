from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_service import CustomAIService
from config import settings
from data_service import build_analysis_context, get_data_summary
from firestore_service import firestore_is_configured, read_firestore_rows, seed_csv_data
from firestore_summary import get_firestore_summary
from schemas import ChatRequest, ChatResponse, HealthResponse


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
    """Firestore 요약을 우선 사용하고, 인증 전에는 CSV 요약으로 대체한다."""
    if firestore_is_configured():
        try:
            summary = get_firestore_summary()
            if any(summary["counts"].values()):
                return summary
        except RuntimeError:
            pass
    return get_data_summary()


@app.get("/api/data")
async def data_list(source: str | None = None, limit: int = 500) -> dict:
    if not firestore_is_configured():
        raise HTTPException(status_code=503, detail="Firebase 인증 설정이 필요합니다.")
    try:
        return {"source": source or "all", "count": min(limit, 5000), "items": read_firestore_rows(source, min(limit, 5000))}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore read failed: {exc}") from exc


@app.post("/api/admin/seed")
async def seed_data() -> dict:
    """현재 CSV를 Firestore에 업로드한다. 로컬 초기화용 엔드포인트."""
    if not firestore_is_configured():
        raise HTTPException(status_code=503, detail="Firebase 인증 설정이 필요합니다.")
    try:
        return {"status": "ok", "collections": ["players", "prices", "patches", "events", "hub"], "counts": seed_csv_data()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Firestore seed failed: {exc}") from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        context = build_analysis_context()
        answer = await app.state.ai_service.chat(
            message=request.message,
            context=context,
            conversation=request.conversation,
        )
        return ChatResponse(answer=answer, model=settings.ai_model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc
