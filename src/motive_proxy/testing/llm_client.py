"""LLM client for enhanced E2E testing.

This module provides LLM client functionality for test clients,
allowing real LLM conversations through MotiveProxy.
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env file in project root
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Also try loading from current directory
        load_dotenv()
except ImportError:
    # dotenv not available, skip loading
    pass


class LLMTestClient:
    """LLM-enhanced test client for E2E testing with smart context management optimized for Gemini."""
    
    def __init__(self, llm: BaseChatModel, max_context_messages: int = 10, max_response_length: int = 2000):
        """Initialize LLM test client.
        
        Args:
            llm: LangChain chat model instance
            max_context_messages: Maximum number of messages to keep in context
            max_response_length: Maximum length for LLM responses (characters)
        """
        self.llm = llm
        self.conversation_history = []
        self.max_context_messages = max_context_messages
        self.max_response_length = max_response_length
        self.system_prompt = None
        
        # Smart context management
        self.conversation_summary = ""
        self.recent_messages = []
        self.response_cache = {}
        self.summary_threshold = 8  # When to create summary
    
    def set_system_prompt(self, prompt: str):
        """Set a system prompt for the conversation.
        
        Args:
            prompt: System prompt to use for context
        """
        self.system_prompt = prompt
    
    def _build_smart_context(self, message: str) -> List:
        """Build optimized context for Gemini with smart truncation.
        
        Args:
            message: New message to add
            
        Returns:
            List of messages optimized for Gemini's context window
        """
        context = []
        
        # Always include system prompt if available
        if self.system_prompt:
            context.append(SystemMessage(content=self.system_prompt))
        
        # Add conversation summary if we have old history
        if self.conversation_summary:
            context.append(HumanMessage(content=f"[Previous context: {self.conversation_summary}]"))
        
        # Add recent messages (last 3-4 for optimal performance)
        context.extend(self.recent_messages[-4:])
        
        # Add new message
        context.append(HumanMessage(content=message))
        
        return context
    
    def _update_context(self, message: str, response: str):
        """Update conversation context efficiently.
        
        Args:
            message: User message
            response: LLM response
        """
        # Add to recent messages
        self.recent_messages.append(HumanMessage(content=message))
        self.recent_messages.append(AIMessage(content=response))
        
        # Add to full history for logging
        self.conversation_history.append(HumanMessage(content=message))
        self.conversation_history.append(AIMessage(content=response))
        
        # Create summary when we have too many recent messages
        if len(self.recent_messages) > self.summary_threshold:
            self._create_conversation_summary()
    
    def _create_conversation_summary(self):
        """Create a summary of older conversation history."""
        if len(self.recent_messages) <= 2:
            return
        
        # Keep only the last 2 messages in recent_messages
        # and summarize the rest
        old_messages = self.recent_messages[:-2]
        
        # Simple summarization (could be enhanced with LLM summarization)
        if len(old_messages) > 0:
            summary_parts = []
            for i, msg in enumerate(old_messages[::2]):  # Every other message (user messages)
                if hasattr(msg, 'content') and len(msg.content) > 50:
                    summary_parts.append(f"Turn {i+1}: {msg.content[:100]}...")
            
            if summary_parts:
                self.conversation_summary = " | ".join(summary_parts)
        
        # Keep only last 2 messages
        self.recent_messages = self.recent_messages[-2:]
    
    async def process_message(self, message: str) -> str:
        """Process an incoming message and return LLM response with smart context.
        
        Args:
            message: Incoming message from MotiveProxy
            
        Returns:
            LLM response message
        """
        import time
        
        # Check cache first (simple hash-based caching)
        cache_key = hash(message + str(self.recent_messages[-2:]) if len(self.recent_messages) >= 2 else message)
        if cache_key in self.response_cache:
            print(f"🚀 Cache hit! Using cached response")
            return self.response_cache[cache_key]
        
        # Build optimized context
        context = self._build_smart_context(message)
        
        # Track response time
        start_time = time.time()
        print(f"🤖 LLM processing... (context: {len(context)} messages, summary: {'yes' if self.conversation_summary else 'no'})")
        
        # Get LLM response
        response = await self.llm.ainvoke(context)
        
        # Calculate and log response time
        response_time = time.time() - start_time
        print(f"⚡ LLM response time: {response_time:.2f}s")
        
        # Warn if response is slow
        if response_time > 20:
            print(f"⚠️  Slow response detected: {response_time:.2f}s")
        
        # Truncate response if too long
        response_content = response.content
        if len(response_content) > self.max_response_length:
            response_content = response_content[:self.max_response_length] + "..."
            print(f"⚠️  Response truncated to {self.max_response_length} characters")
        
        # Update context efficiently
        self._update_context(message, response_content)
        
        # Cache response
        self.response_cache[cache_key] = response_content
        
        return response_content
    
    def get_conversation_history(self) -> list:
        """Get the full conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history.copy()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context usage.
        
        Returns:
            Dictionary with context statistics
        """
        total_messages = len(self.conversation_history)
        context_messages = len(self._build_smart_context(""))
        
        return {
            'total_messages': total_messages,
            'context_messages': context_messages,
            'max_context_messages': self.max_context_messages,
            'context_usage_percent': (context_messages / self.max_context_messages) * 100 if self.max_context_messages > 0 else 0,
            'has_system_prompt': self.system_prompt is not None,
            'has_conversation_summary': bool(self.conversation_summary),
            'recent_messages_count': len(self.recent_messages),
            'cache_size': len(self.response_cache)
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.recent_messages.clear()
        self.conversation_summary = ""
        self.response_cache.clear()
        self.system_prompt = None


def create_llm_client(
    provider: str, 
    model: str, 
    api_key: Optional[str] = None,
    max_context_messages: int = 10
) -> BaseChatModel:
    """Create LLM client for specified provider.
    
    Args:
        provider: LLM provider ('openai', 'anthropic', 'google', 'cohere')
        model: Model name (e.g., 'gpt-4', 'claude-3-sonnet', 'gemini-2.5-flash')
        api_key: API key (if None, will try to load from environment)
        max_context_messages: Maximum context messages for the client
        
    Returns:
        LangChain chat model instance
        
    Raises:
        ValueError: If provider is not supported
        ImportError: If required provider package is not installed
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = _get_api_key_from_env(provider)
    
    if provider == 'openai':
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key)
    
    elif provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key)
    
    elif provider == 'google':
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, api_key=api_key)
    
    elif provider == 'cohere':
        from langchain_cohere import ChatCohere
        return ChatCohere(model=model, api_key=api_key)
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _get_api_key_from_env(provider: str) -> str:
    """Get API key from environment variables.
    
    Args:
        provider: LLM provider name
        
    Returns:
        API key from environment
        
    Raises:
        ValueError: If API key not found in environment
    """
    env_var_map = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'google': 'GOOGLE_API_KEY',
        'cohere': 'COHERE_API_KEY'
    }
    
    env_var = env_var_map.get(provider)
    if not env_var:
        raise ValueError(f"No environment variable mapping for provider: {provider}")
    
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(f"API key not found in environment variable: {env_var}")
    
    return api_key


def get_supported_providers() -> list:
    """Get list of supported LLM providers.
    
    Returns:
        List of supported provider names
    """
    return ['openai', 'anthropic', 'google', 'cohere']


def get_default_models() -> Dict[str, str]:
    """Get default models for each provider.
    
    Returns:
        Dictionary mapping provider to default model
    """
    return {
        'openai': 'gpt-4',
        'anthropic': 'claude-3-sonnet',
        'google': 'gemini-2.5-flash',
        'cohere': 'command'
    }
