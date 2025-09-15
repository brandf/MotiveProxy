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
    """LLM-enhanced test client for E2E testing with context window management."""
    
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
    
    def set_system_prompt(self, prompt: str):
        """Set a system prompt for the conversation.
        
        Args:
            prompt: System prompt to use for context
        """
        self.system_prompt = prompt
    
    def _get_context_for_llm(self) -> List:
        """Get context for LLM with smart truncation.
        
        Returns:
            List of messages optimized for context window
        """
        if len(self.conversation_history) <= self.max_context_messages:
            # If we're under the limit, return everything
            context = self.conversation_history.copy()
        else:
            # Smart truncation: keep system prompt + recent messages
            recent_messages = self.conversation_history[-self.max_context_messages:]
            
            # If we have a system prompt, prepend it
            if self.system_prompt:
                context = [SystemMessage(content=self.system_prompt)] + recent_messages
            else:
                context = recent_messages
        
        return context
    
    async def process_message(self, message: str) -> str:
        """Process an incoming message and return LLM response.
        
        Args:
            message: Incoming message from MotiveProxy
            
        Returns:
            LLM response message
        """
        import time
        
        # Add human message to conversation history
        self.conversation_history.append(HumanMessage(content=message))
        
        # Get optimized context for LLM
        context = self._get_context_for_llm()
        
        # Track response time
        start_time = time.time()
        print(f"🤖 LLM processing... (context: {len(context)} messages)")
        
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
        
        # Add AI response to conversation history
        self.conversation_history.append(response)
        
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
        context_messages = len(self._get_context_for_llm())
        
        return {
            'total_messages': total_messages,
            'context_messages': context_messages,
            'max_context_messages': self.max_context_messages,
            'context_usage_percent': (context_messages / self.max_context_messages) * 100 if self.max_context_messages > 0 else 0,
            'has_system_prompt': self.system_prompt is not None
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
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
