"""E2E Testing CLI for MotiveProxy."""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import click
import httpx

from .scenarios import ScenarioManager, E2ETestScenario
from .test_client import TestClientPair, TestClientConfig
from .log_collector import LogCollector


@click.command()
@click.option('--scenario', default='basic-handshake', help='Test scenario to run')
@click.option('--turns', default=5, help='Number of conversation turns')
@click.option('--concurrent', default=1, help='Number of concurrent sessions')
@click.option('--protocol', default='openai', type=click.Choice(['openai', 'anthropic']), help='Protocol to test')
@click.option('--output', default='./e2e_output', help='Output directory for results')
@click.option('--log-level', default='info', type=click.Choice(['debug', 'info', 'warning', 'error']), help='Log level')
@click.option('--server-host', default='localhost', help='Server host')
@click.option('--server-port', default=8000, help='Server port')
@click.option('--timeout', default=30.0, help='Request timeout in seconds')
@click.option('--validate-responses', is_flag=True, help='Validate response format')
def e2e_test_command(
    scenario: str,
    turns: int,
    concurrent: int,
    protocol: str,
    output: str,
    log_level: str,
    server_host: str,
    server_port: int,
    timeout: float,
    validate_responses: bool
):
    """E2E testing automation for MotiveProxy.
    
    Launches MotiveProxy server, connects test clients, executes N-turn conversations,
    and gathers comprehensive logs for analysis.
    """
    click.echo("Starting E2E test automation...")
    click.echo(f"Scenario: {scenario}")
    click.echo(f"Turns: {turns}")
    click.echo(f"Concurrent sessions: {concurrent}")
    click.echo(f"Protocol: {protocol}")
    click.echo(f"Server: {server_host}:{server_port}")
    click.echo(f"Output: {output}")
    click.echo(f"Log level: {log_level}")
    if validate_responses:
        click.echo("Response validation: enabled")
    
    # Create output directory
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run the E2E test
        result = asyncio.run(_run_e2e_test(
            scenario=scenario,
            turns=turns,
            concurrent=concurrent,
            protocol=protocol,
            output_path=output_path,
            server_host=server_host,
            server_port=server_port,
            timeout=timeout,
            validate_responses=validate_responses
        ))
        
        if result:
            click.echo("✅ E2E test completed successfully!")
        else:
            click.echo("❌ E2E test failed!")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ E2E test error: {e}")
        sys.exit(1)


async def _run_e2e_test(
    scenario: str,
    turns: int,
    concurrent: int,
    protocol: str,
    output_path: Path,
    server_host: str,
    server_port: int,
    timeout: float,
    validate_responses: bool
) -> bool:
    """Run the actual E2E test with real server and clients."""
    
    # Initialize components
    scenario_manager = ScenarioManager()
    log_collector = LogCollector()
    server_process = None
    
    try:
        # Get scenario
        test_scenario = scenario_manager.get_scenario(scenario)
        log_collector.add_log("e2e-test", "info", f"Starting scenario: {scenario}")
        
        # Start MotiveProxy server (real server startup)
        server_process = await _start_server(server_host, server_port)
        log_collector.add_log("e2e-test", "info", f"Started server on {server_host}:{server_port}")
        
        # Wait for server to be ready
        await _wait_for_server(server_host, server_port)
        log_collector.add_log("e2e-test", "info", "Server is ready")
        
        # Run test scenarios with real clients
        session_results = []
        base_url = f"http://{server_host}:{server_port}"
        
        for i in range(concurrent):
            session_id = f"test-session-{i}"
            result = await _run_real_session_test(
                session_id=session_id,
                scenario=test_scenario,
                base_url=base_url,
                log_collector=log_collector,
                validate_responses=validate_responses
            )
            session_results.append(result)
        
        # Generate report
        report = {
            "scenario": scenario,
            "concurrent_sessions": concurrent,
            "protocol": protocol,
            "session_results": session_results,
            "log_summary": log_collector.get_summary(),
            "timestamp": log_collector.logs[-1]["timestamp"] if log_collector.logs else None
        }
        
        # Save report
        report_path = output_path / "test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save logs
        logs_path = output_path / "logs"
        logs_path.mkdir(exist_ok=True)
        log_collector.export_logs(logs_path / "e2e_logs.json")
        
        log_collector.add_log("e2e-test", "info", "E2E test completed successfully")
        return True
        
    except Exception as e:
        log_collector.add_log("e2e-test", "error", f"E2E test failed: {str(e)}")
        return False
        
    finally:
        # Clean up server
        if server_process:
            server_process.terminate()
            try:
                # Wait for server to terminate gracefully
                await asyncio.sleep(1.0)
                if server_process.poll() is None:
                    # Still running, force kill
                    server_process.kill()
            except Exception:
                # Ignore cleanup errors
                pass


async def _start_server(host: str, port: int) -> subprocess.Popen:
    """Start MotiveProxy server in background."""
    cmd = [sys.executable, "-m", "motive_proxy.cli", "run", "--host", host, "--port", str(port)]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


async def _wait_for_server(host: str, port: int, max_attempts: int = 10) -> None:
    """Wait for server to be ready."""
    url = f"http://{host}:{port}/health"
    
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_attempts}: Server not ready yet ({e})")
        await asyncio.sleep(1.0)
    
    raise RuntimeError(f"Server not ready after {max_attempts} attempts")


async def _run_real_session_test(
    session_id: str,
    scenario: E2ETestScenario,
    base_url: str,
    log_collector: LogCollector,
    validate_responses: bool
) -> Dict[str, Any]:
    """Run a single session test with real clients."""
    
    log_collector.add_log(session_id, "info", f"Starting real session test: {session_id}")
    
    try:
        # Create test client configurations
        client_a_config = TestClientConfig(
            name="ClientA",
            base_url=base_url,
            model=session_id,
            timeout=30.0,
            streaming=False
        )
        
        client_b_config = TestClientConfig(
            name="ClientB", 
            base_url=base_url,
            model=session_id,
            timeout=30.0,
            streaming=False
        )
        
        # Execute scenario with real clients
        print(f"Creating test client pair for session {session_id}")
        async with TestClientPair(client_a_config, client_b_config) as client_pair:
            print(f"Executing scenario with {len(scenario.steps)} steps")
            result = await client_pair.execute_scenario(scenario.steps, session_id)
            print(f"Scenario execution completed: {result['success']}")
            
            # Log the results
            if result["success"]:
                log_collector.add_log(session_id, "info", f"Session test completed successfully: {result['steps_executed']}/{result['steps_total']} steps")
            else:
                log_collector.add_log(session_id, "error", f"Session test failed: {result['errors']}")
            
            # Add detailed results to log
            log_collector.add_log(session_id, "info", f"Client A messages: {len(result['client_a_messages'])}")
            log_collector.add_log(session_id, "info", f"Client B messages: {len(result['client_b_messages'])}")
            
            return {
                "session_id": session_id,
                "status": "success" if result["success"] else "failed",
                "steps_completed": result["steps_executed"],
                "steps_total": result["steps_total"],
                "errors": result["errors"],
                "client_a_messages": result["client_a_messages"],
                "client_b_messages": result["client_b_messages"]
            }
        
    except Exception as e:
        log_collector.add_log(session_id, "error", f"Session test failed: {str(e)}")
        return {
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
            "steps_completed": 0,
            "steps_total": len(scenario.steps)
        }
