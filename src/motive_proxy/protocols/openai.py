"""OpenAI protocol adapter."""

from typing import Dict, Any, List
from .base import ProtocolAdapter, ProtocolRequest, ProtocolResponse, ProtocolType


class OpenAIAdapter(ProtocolAdapter):
    """Adapter for OpenAI Chat Completions API."""
    
    def __init__(self):
        super().__init__(ProtocolType.OPENAI)
    
    def parse_request(self, raw_request: Dict[str, Any]) -> ProtocolRequest:
        """Parse OpenAI request format."""
        return ProtocolRequest(
            session_id=raw_request.get("model", ""),
            messages=raw_request.get("messages", []),
            stream=raw_request.get("stream", False),
            model=raw_request.get("model"),
            temperature=raw_request.get("temperature"),
            max_tokens=raw_request.get("max_tokens"),
            extra_params={
                "top_p": raw_request.get("top_p"),
                "frequency_penalty": raw_request.get("frequency_penalty"),
                "presence_penalty": raw_request.get("presence_penalty"),
                "stop": raw_request.get("stop"),
            }
        )
    
    def format_response(self, response: ProtocolResponse) -> Dict[str, Any]:
        """Format response in OpenAI format."""
        return {
            "id": f"chatcmpl-{response.session_id[:8]}",
            "object": "chat.completion",
            "created": int(__import__("time").time()),
            "model": response.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.content
                },
                "finish_reason": response.finish_reason or "stop"
            }],
            "usage": response.usage or {
                "prompt_tokens": 0,
                "completion_tokens": len(response.content.split()),
                "total_tokens": len(response.content.split())
            }
        }
    
    def get_endpoint_path(self) -> str:
        """Get OpenAI endpoint path."""
        return "/v1/chat/completions"
    
    def validate_request(self, request: ProtocolRequest) -> bool:
        """Validate OpenAI request."""
        if not request.session_id:
            return False
        if not request.messages:
            return False
        if not isinstance(request.messages, list):
            return False
        
        # Validate message format
        for message in request.messages:
            if not isinstance(message, dict):
                return False
            if "role" not in message or "content" not in message:
                return False
            if message["role"] not in ["user", "assistant", "system"]:
                return False
        
        return True
