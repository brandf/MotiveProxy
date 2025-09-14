"""Base protocol adapter interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ProtocolType(Enum):
    """Supported protocol types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ProtocolRequest:
    """Base protocol request structure."""
    session_id: str
    messages: List[Dict[str, str]]
    stream: bool = False
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extra_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


@dataclass
class ProtocolResponse:
    """Base protocol response structure."""
    content: str
    model: str
    session_id: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    extra_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters."""
    
    def __init__(self, protocol_type: ProtocolType):
        self.protocol_type = protocol_type
    
    @abstractmethod
    def parse_request(self, raw_request: Dict[str, Any]) -> ProtocolRequest:
        """Parse raw request into standardized format."""
        pass
    
    @abstractmethod
    def format_response(self, response: ProtocolResponse) -> Dict[str, Any]:
        """Format standardized response into protocol-specific format."""
        pass
    
    @abstractmethod
    def get_endpoint_path(self) -> str:
        """Get the endpoint path for this protocol."""
        pass
    
    @abstractmethod
    def validate_request(self, request: ProtocolRequest) -> bool:
        """Validate that the request is valid for this protocol."""
        pass
    
    def get_protocol_type(self) -> ProtocolType:
        """Get the protocol type."""
        return self.protocol_type
