"""Test scenarios for E2E testing."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class E2ETestScenario:
    """Represents a test scenario with steps."""
    name: str
    description: str
    steps: List[Dict[str, Any]]
    expected_duration: Optional[float] = None
    timeout: Optional[float] = None


class ScenarioManager:
    """Manages available test scenarios."""
    
    def __init__(self):
        """Initialize scenario manager with predefined scenarios."""
        self.scenarios = self._create_predefined_scenarios()
    
    def _create_predefined_scenarios(self) -> Dict[str, E2ETestScenario]:
        """Create predefined test scenarios."""
        scenarios = {}
        
        # Basic handshake scenario
        scenarios["basic-handshake"] = E2ETestScenario(
            name="basic-handshake",
            description="Test basic handshake between two clients",
            steps=[
                {"client": "A", "action": "connect", "message": "Hello from A"},
                {"client": "B", "action": "connect", "message": "Hello from B"},
                {"client": "A", "action": "send", "message": "How are you?"},
                {"client": "B", "action": "send", "message": "I'm good, thanks!"}
            ],
            expected_duration=5.0
        )
        
        # Timeout test scenario
        scenarios["timeout-test"] = E2ETestScenario(
            name="timeout-test",
            description="Test timeout handling",
            steps=[
                {"client": "A", "action": "connect", "message": "Hello from A"},
                {"client": "A", "action": "wait", "timeout": 1.0},
                {"client": "A", "action": "expect", "status": "timeout"}
            ],
            timeout=2.0
        )
        
        # Streaming test scenario
        scenarios["streaming-test"] = E2ETestScenario(
            name="streaming-test",
            description="Test streaming functionality",
            steps=[
                {"client": "A", "action": "connect", "message": "Hello from A", "streaming": True},
                {"client": "B", "action": "connect", "message": "Hello from B", "streaming": True},
                {"client": "A", "action": "send", "message": "Stream this message", "streaming": True},
                {"client": "B", "action": "send", "message": "Streaming response", "streaming": True}
            ],
            expected_duration=8.0
        )
        
        # LLM conversation scenario (minimal steps since LLM logic handles the conversation)
        scenarios["llm-conversation"] = E2ETestScenario(
            name="llm-conversation",
            description="LLM-to-LLM conversation through MotiveProxy",
            steps=[
                {"client": "A", "action": "connect", "message": "LLM conversation start"},
                {"client": "B", "action": "connect", "message": "LLM conversation start"}
            ],
            expected_duration=30.0  # LLM conversations take longer
        )
        
        return scenarios
    
    def get_scenario(self, name: str) -> E2ETestScenario:
        """Get a scenario by name."""
        if name not in self.scenarios:
            raise ValueError(f"Scenario '{name}' not found")
        return self.scenarios[name]
    
    def list_scenarios(self) -> List[str]:
        """List all available scenario names."""
        return list(self.scenarios.keys())
    
    def add_scenario(self, scenario: E2ETestScenario) -> None:
        """Add a custom scenario."""
        self.scenarios[scenario.name] = scenario
