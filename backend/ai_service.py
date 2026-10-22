from dataclasses import dataclass

import httpx

from schemas import ChatMessage


@dataclass(frozen=True)
class AISettings:
    ai_base_url: str
    ai_api_key: str
    ai_model: str
    request_timeout_seconds: float


SYSTEM_PROMPT = """너는 세피리아 게임 데이터 분석 도우미다.
제공된 분석 컨텍스트만 근거로 답하고, 데이터에 없는 사실은 추측하지 않는다.
플레이어 수, 가격, 패치, 허브 팔로워의 시간적 동시 발생은 관찰로 설명한다.
가격이나 패치 때문에 플레이어가 증가했다고 인과관계를 단정하지 않는다.
답변은 한국어로, 핵심 수치와 날짜를 포함해 이해하기 쉽게 작성한다.
M1 분석의 표본 수, overlap, 정식 출시 효과가 섞인 한계도 필요할 때 함께 설명한다.
"""


class CustomAIService:
    def __init__(self, settings: AISettings):
        self.settings = settings

    async def chat(
        self,
        message: str,
        context: str,
        conversation: list[ChatMessage],
    ) -> str:
        if not self.settings.ai_api_key:
            raise RuntimeError("AI_API_KEY가 설정되지 않았습니다. backend/.env를 확인하세요.")

        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n[분석 컨텍스트]\n{context}"},
            *[item.model_dump() for item in conversation],
            {"role": "user", "content": message},
        ]
        payload = {"model": self.settings.ai_model, "messages": messages}
        headers = {
            "Authorization": f"Bearer {self.settings.ai_api_key}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.ai_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("커스텀 제공자의 응답 형식이 Chat Completions와 다릅니다.") from exc
