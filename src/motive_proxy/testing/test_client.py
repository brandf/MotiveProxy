"""Real test client using LangChain for E2E testing."""

import asyncio
import json
import time
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage


@dataclass
class TestClientConfig:
    """Configuration for test client."""
    name: str
    base_url: str
    api_key: str = "test-key"
    model: str = "test-model"
    timeout: float = 30.0
    streaming: bool = False


class TestClient:
    """Real test client that connects to MotiveProxy using LangChain."""
    
    def __init__(self, config: TestClientConfig):
        """Initialize test client with configuration."""
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self.langchain_client: Optional[ChatOpenAI] = None
        self.session_id: Optional[str] = None
        self.connected = False
        self.messages: List[Dict[str, Any]] = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to MotiveProxy server."""
        if self.connected:
            return
            
        print(f"Connecting {self.config.name} to {self.config.base_url}")
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={"Authorization": f"Bearer {self.config.api_key}"}
        )
        
        # Create LangChain client pointing to MotiveProxy
        self.langchain_client = ChatOpenAI(
            base_url=f"{self.config.base_url}/v1",
            api_key=self.config.api_key,
            model=self.config.model,
            streaming=self.config.streaming,
            timeout=self.config.timeout
        )
        
        self.connected = True
        print(f"{self.config.name} connected successfully")
        
    async def disconnect(self) -> None:
        """Disconnect from server."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.langchain_client = None
        self.connected = False
        
    async def send_message(self, message: str, session_id: Optional[str] = None) -> Optional[str]:
        """Send a message to the session.
        
        Args:
            message: Message content to send
            session_id: Session ID (uses config.model if not provided)
            
        Returns:
            Response content or None if error
        """
        if not self.connected:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        if not session_id:
            session_id = self.config.model
            
        try:
            # Use LangChain to send message
            response = await self.langchain_client.ainvoke([HumanMessage(content=message)])
            
            # Extract content from response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Log the interaction
            self.messages.append({
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "client": self.config.name,
                "message": message,
                "response": content,
                "type": "message"
            })
            
            return content
            
        except Exception as e:
            # Log the error
            self.messages.append({
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "client": self.config.name,
                "message": message,
                "error": str(e),
                "type": "error"
            })
            return None
    
    async def send_streaming_message(self, message: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Send a streaming message and yield chunks.
        
        Args:
            message: Message content to send
            session_id: Session ID (uses config.model if not provided)
            
        Yields:
            Response chunks
        """
        if not self.connected:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        if not session_id:
            session_id = self.config.model
            
        try:
            # Use LangChain streaming
            async for chunk in self.langchain_client.astream([HumanMessage(content=message)]):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            yield f"ERROR: {str(e)}"
    
    async def wait_for_response(self, timeout: float = 5.0) -> Optional[str]:
        """Wait for a response from the other client.
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            Response content or None if timeout
        """
        start_time = time.time()
        last_message_count = len(self.messages)
        
        while time.time() - start_time < timeout:
            if len(self.messages) > last_message_count:
                # New message received
                latest_message = self.messages[-1]
                if latest_message.get("type") == "message":
                    return latest_message.get("response")
            await asyncio.sleep(0.1)
            
        return None
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """Get the message history for this client."""
        return self.messages.copy()
    
    def clear_history(self) -> None:
        """Clear the message history."""
        self.messages.clear()


class TestClientPair:
    """Manages a pair of test clients for E2E testing."""
    
    def __init__(self, client_a_config: TestClientConfig, client_b_config: TestClientConfig):
        """Initialize client pair."""
        self.client_a_config = client_a_config
        self.client_b_config = client_b_config
        self.client_a: Optional[TestClient] = None
        self.client_b: Optional[TestClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect both clients."""
        self.client_a = TestClient(self.client_a_config)
        self.client_b = TestClient(self.client_b_config)
        
        await self.client_a.connect()
        await self.client_b.connect()
        
    async def disconnect(self) -> None:
        """Disconnect both clients."""
        if self.client_a:
            await self.client_a.disconnect()
        if self.client_b:
            await self.client_b.disconnect()
            
    async def execute_scenario(self, scenario_steps: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Execute a test scenario with the client pair.
        
        Args:
            scenario_steps: List of scenario steps
            session_id: Session ID to use
            
        Returns:
            Execution results
        """
        results = {
            "session_id": session_id,
            "steps_executed": 0,
            "steps_total": len(scenario_steps),
            "success": True,
            "errors": [],
            "client_a_messages": [],
            "client_b_messages": []
        }
        
        try:
            for step in scenario_steps:
                client_name = step.get("client", "A")
                action = step.get("action")
                
                if client_name == "A":
                    client = self.client_a
                else:
                    client = self.client_b
                
                if action == "connect":
                    message = step.get("message", "Hello")
                    response = await client.send_message(message, session_id)
                    if response is None:
                        results["errors"].append(f"Client {client_name} failed to connect")
                        results["success"] = False
                        
                elif action == "send":
                    message = step.get("message", "")
                    response = await client.send_message(message, session_id)
                    if response is None:
                        results["errors"].append(f"Client {client_name} failed to send message")
                        results["success"] = False
                        
                elif action == "wait":
                    timeout = step.get("timeout", 1.0)
                    await asyncio.sleep(timeout)
                    
                elif action == "expect":
                    expected_status = step.get("status")
                    if expected_status == "timeout":
                        # Wait a bit to see if we get a timeout
                        await asyncio.sleep(0.5)
                        
                results["steps_executed"] += 1
                
        except Exception as e:
            results["errors"].append(f"Scenario execution failed: {str(e)}")
            results["success"] = False
            
        # Collect message histories
        if self.client_a:
            results["client_a_messages"] = self.client_a.get_message_history()
        if self.client_b:
            results["client_b_messages"] = self.client_b.get_message_history()
            
        return results
