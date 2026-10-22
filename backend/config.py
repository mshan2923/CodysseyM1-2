import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # 개발 환경에서 의존성 설치 전에도 기본 진단이 가능하도록 함
    def load_dotenv(*args, **kwargs):
        return False


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")


def _allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    ai_base_url: str = os.getenv("AI_BASE_URL", "https://copa.codyssey.kr/v1").rstrip("/")
    ai_api_key: str = os.getenv("AI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gpt-5-mini")
    allowed_origins: list[str] = None  # type: ignore[assignment]
    request_timeout_seconds: float = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "60"))
    firebase_service_account_path: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    firestore_data_collection: str = os.getenv("FIRESTORE_DATA_COLLECTION", "analysis_data")

    def __post_init__(self) -> None:
        if self.allowed_origins is None:
            object.__setattr__(self, "allowed_origins", _allowed_origins())


settings = Settings()
