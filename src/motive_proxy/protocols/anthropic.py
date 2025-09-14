"""Anthropic Claude protocol adapter."""

from typing import Dict, Any, List
from .base import ProtocolAdapter, ProtocolRequest, ProtocolResponse, ProtocolType


class AnthropicAdapter(ProtocolAdapter):
    """Adapter for Anthropic Claude API."""
    
    def __init__(self):
        super().__init__(ProtocolType.ANTHROPIC)
    
    def parse_request(self, raw_request: Dict[str, Any]) -> ProtocolRequest:
        """Parse Anthropic request format."""
        # Anthropic uses different field names
        messages = raw_request.get("messages", [])
        
        # Convert Anthropic format to standard format
        standard_messages = []
        for msg in messages:
            standard_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        return ProtocolRequest(
            session_id=raw_request.get("model", ""),
            messages=standard_messages,
            stream=raw_request.get("stream", False),
            model=raw_request.get("model"),
            temperature=raw_request.get("temperature"),
            max_tokens=raw_request.get("max_tokens"),
            extra_params={
                "top_p": raw_request.get("top_p"),
                "stop_sequences": raw_request.get("stop_sequences"),
                "system": raw_request.get("system"),
            }
        )
    
    def format_response(self, response: ProtocolResponse) -> Dict[str, Any]:
        """Format response in Anthropic format."""
        return {
            "id": f"msg-{response.session_id[:8]}",
            "type": "message",
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": response.content
            }],
            "model": response.model,
            "stop_reason": response.finish_reason or "end_turn",
            "stop_sequence": None,
            "usage": response.usage or {
                "input_tokens": 0,
                "output_tokens": len(response.content.split()),
            }
        }
    
    def get_endpoint_path(self) -> str:
        """Get Anthropic endpoint path."""
        return "/v1/messages"
    
    def validate_request(self, request: ProtocolRequest) -> bool:
        """Validate Anthropic request."""
        if not request.session_id:
            return False
        if not request.messages:
            return False
        if not isinstance(request.messages, list):
            return False
        
        # Anthropic has stricter validation
        for message in request.messages:
            if not isinstance(message, dict):
                return False
            if "role" not in message or "content" not in message:
                return False
            # Anthropic only supports user and assistant roles
            if message["role"] not in ["user", "assistant"]:
                return False
        
        return True
