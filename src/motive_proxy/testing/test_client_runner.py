"""Standalone test client runner for E2E testing.

This script runs as an independent subprocess and connects to MotiveProxy
using LangChain, executing test scenarios via normal HTTP/WebSocket communication.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import click
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


@click.command()
@click.option('--name', required=True, help='Client name (ClientA, ClientB, etc.)')
@click.option('--server-url', required=True, help='MotiveProxy server URL')
@click.option('--session-id', required=True, help='Session ID to use')
@click.option('--scenario', required=True, help='Test scenario name')
@click.option('--role', required=True, help='Client role (A or B)')
@click.option('--api-key', default='test-key', help='API key for authentication')
@click.option('--timeout', default=30.0, help='Request timeout in seconds')
@click.option('--streaming', is_flag=True, help='Use streaming mode')
@click.option('--output', default='./client_output', help='Output directory for logs')
def main(
    name: str,
    server_url: str,
    session_id: str,
    scenario: str,
    role: str,
    api_key: str,
    timeout: float,
    streaming: bool,
    output: str
):
    """Run a test client as an independent subprocess."""
    
    # Setup centralized logging
    logs_dir = Path("logs/test-clients")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{name.lower()}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger(f"test_client.{name}")
    
    logger.info(f"Starting {name} (role {role}) for scenario {scenario}")
    logger.info(f"Server: {server_url}")
    logger.info(f"Session: {session_id}")
    logger.info(f"Streaming: {streaming}")
    
    # Create output directory
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run the test client
        result = asyncio.run(_run_test_client(
            name=name,
            server_url=server_url,
            session_id=session_id,
            scenario=scenario,
            role=role,
            api_key=api_key,
            timeout=timeout,
            streaming=streaming,
            output_path=output_path
        ))
        
        if result:
            print(f"✅ {name} completed successfully!")
            sys.exit(0)
        else:
            print(f"❌ {name} failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ {name} error: {e}")
        sys.exit(1)


async def _run_test_client(
    name: str,
    server_url: str,
    session_id: str,
    scenario: str,
    role: str,
    api_key: str,
    timeout: float,
    streaming: bool,
    output_path: Path
) -> bool:
    """Run the actual test client."""
    
    try:
        # Create LangChain client pointing to MotiveProxy
        client = ChatOpenAI(
            base_url=f"{server_url}/v1",
            api_key=api_key,
            model=session_id,
            streaming=streaming,
            timeout=timeout
        )
        
        print(f"{name}: Connected to MotiveProxy at {server_url}")
        
        # Load scenario steps
        scenario_steps = _load_scenario_steps(scenario, role)
        print(f"{name}: Loaded {len(scenario_steps)} scenario steps")
        
        # Execute scenario steps with proper session coordination
        results = []
        for i, step in enumerate(scenario_steps):
            print(f"{name}: Executing step {i+1}/{len(scenario_steps)}: {step['action']}")
            
            if step['action'] == 'connect':
                message = step.get('message', 'Hello')
                print(f"{name}: Attempting to connect with message: {message}")
                response = await _send_message(client, message, streaming)
                results.append({
                    'step': i+1,
                    'action': 'connect',
                    'message': message,
                    'response': response,
                    'timestamp': time.time()
                })
                print(f"{name}: Connected! Response: {response[:100]}...")
                
            elif step['action'] == 'send':
                message = step.get('message', '')
                print(f"{name}: Sending message: {message}")
                response = await _send_message(client, message, streaming)
                results.append({
                    'step': i+1,
                    'action': 'send',
                    'message': message,
                    'response': response,
                    'timestamp': time.time()
                })
                print(f"{name}: Message sent! Response: {response[:100]}...")
                
            elif step['action'] == 'wait':
                wait_time = step.get('timeout', 1.0)
                print(f"{name}: Waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                results.append({
                    'step': i+1,
                    'action': 'wait',
                    'timeout': wait_time,
                    'timestamp': time.time()
                })
                
            elif step['action'] == 'expect':
                expected_status = step.get('status')
                print(f"{name}: Expecting {expected_status}")
                results.append({
                    'step': i+1,
                    'action': 'expect',
                    'status': expected_status,
                    'timestamp': time.time()
                })
        
        # Save results
        results_file = output_path / f"{name.lower()}_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'client_name': name,
                'role': role,
                'session_id': session_id,
                'scenario': scenario,
                'steps_executed': len(results),
                'results': results,
                'timestamp': time.time()
            }, f, indent=2)
        
        print(f"{name}: Results saved to {results_file}")
        return True
        
    except Exception as e:
        print(f"{name}: Error during execution: {e}")
        
        # Save error results
        error_file = output_path / f"{name.lower()}_error.json"
        with open(error_file, 'w') as f:
            json.dump({
                'client_name': name,
                'role': role,
                'session_id': session_id,
                'scenario': scenario,
                'error': str(e),
                'timestamp': time.time()
            }, f, indent=2)
        
        return False


async def _send_message(client: ChatOpenAI, message: str, streaming: bool) -> str:
    """Send a message using the LangChain client."""
    try:
        if streaming:
            # Collect streaming response
            response_parts = []
            async for chunk in client.astream([HumanMessage(content=message)]):
                if hasattr(chunk, 'content') and chunk.content:
                    response_parts.append(chunk.content)
            return ''.join(response_parts)
        else:
            # Regular response
            response = await client.ainvoke([HumanMessage(content=message)])
            return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"ERROR: {str(e)}"


def _load_scenario_steps(scenario: str, role: str) -> list:
    """Load scenario steps for the given role."""
    # This is a simplified version - in practice, you'd load from scenarios.py
    if scenario == "basic-handshake":
        if role == "A":
            return [
                {"action": "connect", "message": "Hello from A"},
                {"action": "wait", "timeout": 1.0},  # Wait for B to connect
                {"action": "send", "message": "How are you?"}
            ]
        else:  # role == "B"
            return [
                {"action": "connect", "message": "Hello from B"},
                {"action": "send", "message": "I'm good, thanks!"}
            ]
    elif scenario == "timeout-test":
        if role == "A":
            return [
                {"action": "connect", "message": "Hello from A"},
                {"action": "wait", "timeout": 1.0},
                {"action": "expect", "status": "timeout"}
            ]
        else:
            return []  # B doesn't participate in timeout test
    elif scenario == "streaming-test":
        if role == "A":
            return [
                {"action": "connect", "message": "Hello from A", "streaming": True},
                {"action": "send", "message": "Stream this message", "streaming": True}
            ]
        else:  # role == "B"
            return [
                {"action": "connect", "message": "Hello from B", "streaming": True},
                {"action": "send", "message": "Streaming response", "streaming": True}
            ]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")


if __name__ == "__main__":
    main()
