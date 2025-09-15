"""E2E Test Scenarios for MotiveProxy.

These are the actual E2E test scenarios that can be run using the motive-proxy-e2e tool.
Each scenario tests real subprocess behavior with actual network connections.
"""

import pytest
import subprocess
import sys
import asyncio
import tempfile
from pathlib import Path
from motive_proxy.testing.scenarios import ScenarioManager


class TestE2EScenarios:
    """E2E test scenarios using real subprocesses."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_basic_handshake_scenario(self):
        """Test basic handshake scenario using motive-proxy-e2e tool."""
        # This test runs the E2E tool as a subprocess
        cmd = [
            "motive-proxy-e2e",
            "--scenario", "basic-handshake",
            "--turns", "3",
            "--timeout", "30"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # Give the E2E test time to complete
        )
        
        # Check that the E2E test passed
        assert result.returncode == 0, f"E2E test failed: {result.stderr}"
        assert "✅ E2E test completed successfully" in result.stdout
        
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_concurrent_clients_scenario(self):
        """Test concurrent clients scenario using motive-proxy-e2e tool."""
        cmd = [
            "motive-proxy-e2e",
            "--scenario", "basic-handshake",
            "--turns", "2",
            "--concurrent", "2",
            "--timeout", "45"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90  # Give concurrent test more time
        )
        
        assert result.returncode == 0, f"Concurrent E2E test failed: {result.stderr}"
        assert "✅ E2E test completed successfully" in result.stdout
        
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_streaming_scenario(self):
        """Test streaming scenario using motive-proxy-e2e tool."""
        cmd = [
            "motive-proxy-e2e",
            "--scenario", "timeout-test",
            "--turns", "2",
            "--timeout", "30"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Streaming E2E test failed: {result.stderr}"
        assert "✅ E2E test completed successfully" in result.stdout
        
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_error_handling_scenario(self):
        """Test error handling scenario using motive-proxy-e2e tool."""
        cmd = [
            "motive-proxy-e2e",
            "--scenario", "timeout-test",
            "--turns", "2",
            "--timeout", "30"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Error handling E2E test failed: {result.stderr}"
        assert "✅ E2E test completed successfully" in result.stdout


class TestE2EInfrastructure:
    """Test the E2E testing infrastructure itself."""
    
    def test_scenario_manager_has_required_scenarios(self):
        """Test that ScenarioManager has all required scenarios."""
        manager = ScenarioManager()
        
        required_scenarios = [
            "basic-handshake",
            "timeout-test"
        ]
        
        for scenario_name in required_scenarios:
            assert scenario_name in manager.scenarios, f"Missing scenario: {scenario_name}"
            
    def test_e2e_cli_help(self):
        """Test that E2E CLI shows help information."""
        cmd = ["motive-proxy-e2e", "--help"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "--scenario" in result.stdout
        assert "--turns" in result.stdout
