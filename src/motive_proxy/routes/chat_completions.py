"""OpenAI Chat Completions API endpoint."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Message(BaseModel):
    """Chat message model."""

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI Chat Completions request model."""

    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    """OpenAI Chat Completions response model."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI Chat Completions API endpoint.

    This endpoint handles the proxy logic for human-in-the-loop interactions.
    """
    # TODO: Implement session management and proxy logic
    # For now, return a placeholder response
    raise HTTPException(
        status_code=501, detail="Chat completions endpoint not yet implemented"
    )
