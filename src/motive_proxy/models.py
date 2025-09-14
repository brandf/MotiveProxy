"""Pydantic models for OpenAI-compatible request/response and errors."""

from __future__ import annotations

import time
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


class ChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage
    finish_reason: Literal["stop"] = "stop"


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

    @staticmethod
    def build(model: str, prompt: str, completion: str) -> "ChatCompletionResponse":
        created_ts = int(time.time())
        prompt_tokens = len(prompt)
        completion_tokens = len(completion)
        return ChatCompletionResponse(
            id=f"chatcmpl-{created_ts}-{model}",
            created=created_ts,
            model=model,
            choices=[Choice(message=ChoiceMessage(content=completion))],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )


class ErrorDetails(BaseModel):
    message: str
    type: str
    code: Optional[str] = None
    param: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetails


