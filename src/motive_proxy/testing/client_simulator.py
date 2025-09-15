"""Client simulator for E2E testing."""

import asyncio
import httpx
from typing import Optional, AsyncGenerator, Dict, Any


class ClientSimulator:
    """Simulates OpenAI/Anthropic clients for testing."""
    
    def __init__(self, protocol: str, base_url: str, streaming: bool = False):
        """Initialize client simulator.
        
        Args:
            protocol: Protocol to simulate ('openai' or 'anthropic')
            base_url: Base URL of the MotiveProxy server
            streaming: Whether to use streaming mode
        """
        self.protocol = protocol
        self.base_url = base_url
        self.streaming = streaming
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def send_message(self, session_id: str, message: str) -> Optional[str]:
        """Send a message to the session.
        
        Args:
            session_id: Session identifier
            message: Message content
            
        Returns:
            Response content or None if error
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        if self.protocol == "openai":
            return await self._send_openai_message(session_id, message)
        elif self.protocol == "anthropic":
            return await self._send_anthropic_message(session_id, message)
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")
    
    async def _send_openai_message(self, session_id: str, message: str) -> Optional[str]:
        """Send OpenAI format message."""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": session_id,
            "messages": [{"role": "user", "content": message}],
            "stream": self.streaming
        }
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            
            if self.streaming:
                # For streaming, collect all chunks
                content = ""
                async for chunk in self._client.stream("POST", url, json=payload):
                    if chunk.status_code == 200:
                        line = chunk.text.strip()
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            try:
                                data = chunk.json()
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content += delta.get("content", "")
                            except:
                                pass
                return content
            else:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return None
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 408:  # Timeout
                return "TIMEOUT"
            raise
        except Exception:
            return None
    
    async def _send_anthropic_message(self, session_id: str, message: str) -> Optional[str]:
        """Send Anthropic format message."""
        url = f"{self.base_url}/v1/messages"
        payload = {
            "model": session_id,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": message}]
        }
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if "content" in data and len(data["content"]) > 0:
                return data["content"][0]["text"]
            return None
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 408:  # Timeout
                return "TIMEOUT"
            raise
        except Exception:
            return None
    
    async def send_streaming_message(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Send streaming message and yield chunks."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": session_id,
            "messages": [{"role": "user", "content": message}],
            "stream": True
        }
        
        try:
            async with self._client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        try:
                            data = response.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except:
                            pass
        except Exception:
            yield "ERROR"
