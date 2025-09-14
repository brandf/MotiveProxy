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
    # Basic validation - check for empty messages
    if not request.messages:
        raise HTTPException(status_code=422, detail="Messages array cannot be empty")

    # TODO: Implement session management and proxy logic
    # For now, return a placeholder response that matches OpenAI format
    return ChatCompletionResponse(
        id="chatcmpl-placeholder",
        object="chat.completion",
        created=1677652288,
        model=request.model,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a placeholder response from MotiveProxy. Session management not yet implemented."  # noqa: E501,
                },
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": (
                len(request.messages[0].content) if request.messages else 0
            ),
            "completion_tokens": 10,
            "total_tokens": 10
            + (len(request.messages[0].content) if request.messages else 0),
        },
    )
