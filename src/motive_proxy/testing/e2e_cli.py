"""E2E Testing CLI for MotiveProxy with subprocess orchestration."""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import click
import httpx

from .scenarios import ScenarioManager, E2ETestScenario
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
    
    Launches MotiveProxy server and independent test clients as separate processes,
    executing real network communication scenarios.
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
            click.echo("E2E test completed successfully!")
        else:
            click.echo("E2E test failed!")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"E2E test error: {e}")
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
    """Run the actual E2E test with subprocess orchestration."""
    
    # Initialize components
    scenario_manager = ScenarioManager()
    log_collector = LogCollector()
    server_process = None
    client_processes = []
    
    try:
        # Get scenario
        try:
            test_scenario = scenario_manager.get_scenario(scenario)
        except ValueError as e:
            print(f"❌ {e}")
            return False
            
        log_collector.add_log("e2e-test", "info", f"Starting scenario: {scenario}")
        
        # Start MotiveProxy server (real server startup)
        server_process = await _start_server(server_host, server_port)
        log_collector.add_log("e2e-test", "info", f"Started server on {server_host}:{server_port}")
        
        # Wait for server to be ready
        await _wait_for_server(server_host, server_port)
        log_collector.add_log("e2e-test", "info", "Server is ready")
        
        # Run test scenarios with independent client processes
        session_results = []
        server_url = f"http://{server_host}:{server_port}"
        
        for i in range(concurrent):
            session_id = f"test-session-{i}"
            result = await _run_session_with_subprocesses(
                session_id=session_id,
                scenario=test_scenario,
                server_url=server_url,
                output_path=output_path,
                log_collector=log_collector
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
        # Clean up all processes
        await _cleanup_processes(server_process, client_processes)


async def _start_server(host: str, port: int) -> subprocess.Popen:
    """Start MotiveProxy server in background."""
    cmd = [sys.executable, "-m", "motive_proxy.cli", "run", "--host", host, "--port", str(port)]
    print(f"Starting server: {' '.join(cmd)}")
    
    # Windows-specific subprocess handling
    if sys.platform == "win32":
        return subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        return subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )


async def _wait_for_server(host: str, port: int, max_attempts: int = 10) -> None:
    """Wait for server to be ready."""
    url = f"http://{host}:{port}/health"
    
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"Server is ready at {url}")
                    return
        except httpx.ConnectError as e:
            if "10035" in str(e) or "Connection refused" in str(e):
                print(f"Attempt {attempt + 1}/{max_attempts}: Server not ready yet (connection refused)")
                if attempt == 0:
                    print("💡 Note: If you see a Windows Firewall dialog, please allow the connection")
            else:
                print(f"Attempt {attempt + 1}/{max_attempts}: Server not ready yet ({e})")
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_attempts}: Server not ready yet ({e})")
        
        await asyncio.sleep(1.0)
    
    raise RuntimeError(f"Server not ready after {max_attempts} attempts")


async def _run_session_with_subprocesses(
    session_id: str,
    scenario: E2ETestScenario,
    server_url: str,
    output_path: Path,
    log_collector: LogCollector
) -> Dict[str, Any]:
    """Run a session test with independent client subprocesses."""
    
    print(f"Starting session test: {session_id}")
    log_collector.add_log(session_id, "info", f"Starting session test: {session_id}")
    
    client_processes = []
    
    try:
        # Start Client A
        client_a_cmd = [
            sys.executable, "-m", "motive_proxy.testing.test_client_runner",
            "--name=ClientA",
            f"--server-url={server_url}",
            f"--session-id={session_id}",
            f"--scenario={scenario.name}",
            "--role=A",
            f"--output={output_path}"
        ]
        print(f"Starting Client A: {' '.join(client_a_cmd)}")
        
        # Windows-specific subprocess handling
        if sys.platform == "win32":
            client_a_process = subprocess.Popen(
                client_a_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            client_a_process = subprocess.Popen(
                client_a_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
        client_processes.append(client_a_process)
        
        # Wait for Client A to establish connection
        print(f"Waiting for Client A to connect...")
        await asyncio.sleep(2.0)
        
        # Start Client B
        client_b_cmd = [
            sys.executable, "-m", "motive_proxy.testing.test_client_runner",
            "--name=ClientB",
            f"--server-url={server_url}",
            f"--session-id={session_id}",
            f"--scenario={scenario.name}",
            "--role=B",
            f"--output={output_path}"
        ]
        print(f"Starting Client B: {' '.join(client_b_cmd)}")
        
        # Windows-specific subprocess handling
        if sys.platform == "win32":
            client_b_process = subprocess.Popen(
                client_b_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            client_b_process = subprocess.Popen(
                client_b_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
        client_processes.append(client_b_process)
        
        # Wait for both clients to complete
        print(f"Waiting for clients to complete...")
        await asyncio.gather(
            _wait_for_client(client_a_process, "ClientA", log_collector, session_id),
            _wait_for_client(client_b_process, "ClientB", log_collector, session_id)
        )
        
        # Collect results
        client_a_results = _load_client_results(output_path / "clienta_results.json")
        client_b_results = _load_client_results(output_path / "clientb_results.json")
        
        success = (client_a_results is not None and client_b_results is not None)
        
        return {
            "session_id": session_id,
            "status": "success" if success else "failed",
            "client_a_results": client_a_results,
            "client_b_results": client_b_results,
            "steps_completed": len(scenario.steps)
        }
        
    except Exception as e:
        log_collector.add_log(session_id, "error", f"Session test failed: {str(e)}")
        return {
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
            "steps_completed": 0
        }


async def _wait_for_client(process: subprocess.Popen, client_name: str, log_collector: LogCollector, session_id: str) -> None:
    """Wait for a client process to complete and log its output."""
    try:
        # Wait for the process to complete with timeout
        return_code = await asyncio.wait_for(
            asyncio.to_thread(process.wait),
            timeout=30.0
        )
        
        if return_code == 0:
            log_collector.add_log(session_id, "info", f"{client_name} completed successfully")
            print(f"{client_name} completed successfully")
        else:
            log_collector.add_log(session_id, "error", f"{client_name} failed with return code {return_code}")
            print(f"{client_name} failed with return code {return_code}")
            
    except asyncio.TimeoutError:
        log_collector.add_log(session_id, "error", f"{client_name} timed out")
        print(f"{client_name} timed out")
        if sys.platform == "win32":
            process.terminate()
        else:
            process.terminate()


def _load_client_results(results_file: Path) -> Optional[Dict[str, Any]]:
    """Load client results from JSON file."""
    try:
        if results_file.exists():
            with open(results_file) as f:
                return json.load(f)
    except Exception:
        pass
    return None


async def _cleanup_processes(server_process: Optional[subprocess.Popen], client_processes: List[subprocess.Popen]) -> None:
    """Clean up all processes with Windows/macOS compatibility."""
    print("Cleaning up processes...")
    
    # Terminate client processes
    for process in client_processes:
        if process.poll() is None:  # Still running
            if sys.platform == "win32":
                # Windows: Use terminate() for graceful shutdown
                process.terminate()
            else:
                # macOS/Linux: Use terminate() for graceful shutdown
                process.terminate()
    
    # Wait for clients to terminate
    for process in client_processes:
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                # Windows: Force kill
                process.kill()
            else:
                # macOS/Linux: Send SIGKILL
                process.kill()
    
    # Terminate server
    if server_process and server_process.poll() is None:
        if sys.platform == "win32":
            # Windows: Use terminate() for graceful shutdown
            server_process.terminate()
        else:
            # macOS/Linux: Use terminate() for graceful shutdown
            server_process.terminate()
        
        try:
            server_process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                # Windows: Force kill
                server_process.kill()
            else:
                # macOS/Linux: Send SIGKILL
                server_process.kill()
    
    print("Process cleanup complete")
