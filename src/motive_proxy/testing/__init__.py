"""E2E Testing Automation for MotiveProxy."""

from .e2e_cli import e2e_test_command
from .scenarios import E2ETestScenario, ScenarioManager
from .test_client import TestClient, TestClientPair, TestClientConfig
from .log_collector import LogCollector

__all__ = [
    "e2e_test_command",
    "E2ETestScenario", 
    "ScenarioManager",
    "TestClient",
    "TestClientPair", 
    "TestClientConfig",
    "LogCollector"
]
