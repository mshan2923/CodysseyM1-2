from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str
    model: str


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str


class DataRecord(BaseModel):
    type: str = Field(min_length=1, max_length=40)
    date: str = Field(min_length=1, max_length=40)
    value: float | str | None = None
    memo: str = Field(default="", max_length=2000)
    metadata: dict = Field(default_factory=dict)


class ConversationCreate(BaseModel):
    title: str = Field(default="새 분석 대화", max_length=200)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=100)


class ConversationUpdate(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list, max_length=100)
