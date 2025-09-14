"""Protocol manager for handling different LLM API protocols."""

from typing import Dict, Optional, Type
from motive_proxy.protocols.base import ProtocolAdapter, ProtocolType
from motive_proxy.protocols.openai import OpenAIAdapter
from motive_proxy.protocols.anthropic import AnthropicAdapter
from motive_proxy.observability import get_logger


class ProtocolManager:
    """Manages different protocol adapters."""
    
    def __init__(self):
        self.logger = get_logger("motive_proxy.protocol_manager")
        self._adapters: Dict[ProtocolType, ProtocolAdapter] = {}
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register default protocol adapters."""
        self.register_adapter(OpenAIAdapter())
        self.register_adapter(AnthropicAdapter())
        self.logger.info("Registered default protocol adapters", 
                        protocols=list(self._adapters.keys()))
    
    def register_adapter(self, adapter: ProtocolAdapter):
        """Register a new protocol adapter."""
        self._adapters[adapter.get_protocol_type()] = adapter
        self.logger.info("Registered protocol adapter", 
                        protocol_type=adapter.get_protocol_type().value)
    
    def get_adapter(self, protocol_type: ProtocolType) -> Optional[ProtocolAdapter]:
        """Get adapter for a specific protocol type."""
        return self._adapters.get(protocol_type)
    
    def get_adapter_by_endpoint(self, endpoint_path: str) -> Optional[ProtocolAdapter]:
        """Get adapter by endpoint path."""
        for adapter in self._adapters.values():
            if adapter.get_endpoint_path() == endpoint_path:
                return adapter
        return None
    
    def list_supported_protocols(self) -> list[str]:
        """List all supported protocol types."""
        return [protocol_type.value for protocol_type in self._adapters.keys()]
    
    def get_adapter_for_request(self, raw_request: Dict, endpoint_path: str) -> Optional[ProtocolAdapter]:
        """Determine the best adapter for a request."""
        # First try to match by endpoint
        adapter = self.get_adapter_by_endpoint(endpoint_path)
        if adapter:
            return adapter
        
        # Fallback to OpenAI for unknown endpoints (backward compatibility)
        return self.get_adapter(ProtocolType.OPENAI)
