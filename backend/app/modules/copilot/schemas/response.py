from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    paper_title: str = ""
    paper_id: str = ""
    relevance: str = ""


class CopilotMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list[Citation] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    created_at: str = ""


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    suggested_questions: list[str] = Field(default_factory=list)
    message_id: str = ""
    conversation_id: str = ""


class CopilotHistoryResponse(BaseModel):
    messages: list[CopilotMessageResponse] = Field(default_factory=list)


class StreamToken(BaseModel):
    type: Literal["token"] = "token"
    content: str


class StreamDone(BaseModel):
    type: Literal["done"] = "done"
    message_id: str
    conversation_id: str
    citations: list[Citation] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


class StreamError(BaseModel):
    type: Literal["error"] = "error"
    message: str
