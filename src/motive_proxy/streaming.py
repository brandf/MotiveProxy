"""Streaming support for OpenAI-compatible Server-Sent Events."""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from dataclasses import dataclass

from motive_proxy.models import ChatCompletionResponse, Message
from motive_proxy.observability import get_logger, time_operation


@dataclass
class StreamChunk:
    """Represents a single streaming chunk."""
    id: str
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = ""
    choices: list = None
    finish_reason: Optional[str] = None
    
    def __post_init__(self):
        if self.choices is None:
            self.choices = []
        if self.created == 0:
            import time
            self.created = int(time.time())


class StreamingResponse:
    """Handles streaming responses for OpenAI-compatible SSE."""
    
    def __init__(self, session_id: str, model: str):
        self.session_id = session_id
        self.model = model
        self.logger = get_logger("motive_proxy.streaming")
        
    async def stream_completion(self, prompt: str, completion: str) -> AsyncGenerator[str, None]:
        """Stream a completion in OpenAI-compatible format."""
        self.logger.info("Starting stream completion", 
                        session_id=self.session_id,
                        prompt_length=len(prompt),
                        completion_length=len(completion))
        
        # Generate response ID (similar to OpenAI format)
        response_id = f"chatcmpl-{self.session_id[:8]}"
        
        # Split completion into words for streaming
        words = completion.split()
        if not words:
            # Handle empty completion
            chunk = StreamChunk(
                id=response_id,
                model=self.model,
                choices=[{
                    "index": 0,
                    "delta": {"content": ""},
                    "finish_reason": "stop"
                }]
            )
            yield self._format_sse_chunk(chunk)
            return
            
        # Stream each word
        for i, word in enumerate(words):
            is_last = i == len(words) - 1
            
            chunk = StreamChunk(
                id=response_id,
                model=self.model,
                choices=[{
                    "index": 0,
                    "delta": {"content": word + (" " if not is_last else "")},
                    "finish_reason": "stop" if is_last else None
                }]
            )
            
            yield self._format_sse_chunk(chunk)
            
            # Small delay to simulate streaming
            await asyncio.sleep(0.05)
        
        self.logger.info("Stream completion finished", 
                        session_id=self.session_id,
                        chunks_sent=len(words))
    
    def _format_sse_chunk(self, chunk: StreamChunk) -> str:
        """Format a chunk as Server-Sent Event."""
        data = {
            "id": chunk.id,
            "object": chunk.object,
            "created": chunk.created,
            "model": chunk.model,
            "choices": chunk.choices
        }
        
        # Add finish_reason if present
        if chunk.finish_reason:
            data["choices"][0]["finish_reason"] = chunk.finish_reason
            
        return f"data: {json.dumps(data)}\n\n"
    
    async def stream_error(self, error_message: str, error_type: str = "error") -> AsyncGenerator[str, None]:
        """Stream an error response."""
        self.logger.warning("Streaming error", 
                          session_id=self.session_id,
                          error_type=error_type,
                          error_message=error_message)
        
        chunk = StreamChunk(
            id=f"chatcmpl-error-{self.session_id[:8]}",
            model=self.model,
            choices=[{
                "index": 0,
                "delta": {"content": ""},
                "finish_reason": "stop"
            }]
        )
        
        # Add error information to the chunk
        error_data = {
            "id": chunk.id,
            "object": chunk.object,
            "created": chunk.created,
            "model": chunk.model,
            "choices": chunk.choices,
            "error": {
                "message": error_message,
                "type": error_type
            }
        }
        
        yield f"data: {json.dumps(error_data)}\n\n"


class StreamingSession:
    """Enhanced session that supports streaming."""
    
    def __init__(self, session_id: str, model: str):
        self.session_id = session_id
        self.model = model
        self.streaming_response = StreamingResponse(session_id, model)
        self.logger = get_logger("motive_proxy.streaming_session")
    
    async def process_streaming_request(self, content: str, session) -> AsyncGenerator[str, None]:
        """Process a streaming request through the session."""
        self.logger.info("Processing streaming request", 
                        session_id=self.session_id,
                        content_length=len(content))
        
        try:
            with time_operation("streaming_session_processing", {"session_id": self.session_id}):
                # Get the counterpart message (this will block until counterpart responds)
                counterpart_message = await session.process_request(content)
                
                # Stream the response
                async for chunk in self.streaming_response.stream_completion(content, counterpart_message):
                    yield chunk
                    
        except TimeoutError:
            self.logger.warning("Streaming request timed out", session_id=self.session_id)
            async for chunk in self.streaming_response.stream_error("Request timed out", "timeout"):
                yield chunk
        except Exception as exc:
            self.logger.error("Streaming request failed", 
                            session_id=self.session_id,
                            error=str(exc),
                            exc_info=True)
            async for chunk in self.streaming_response.stream_error(str(exc), "server_error"):
                yield chunk
