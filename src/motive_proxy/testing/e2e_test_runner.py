#!/usr/bin/env python3
"""
E2E Testing Runner for MotiveProxy

This is a standalone tool that orchestrates E2E testing by:
1. Launching MotiveProxy as an external process
2. Launching test clients as external processes
3. Monitoring and collecting results

MotiveProxy itself has no knowledge of testing scenarios.
"""

import asyncio
import click
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from motive_proxy.testing.e2e_cli import _run_e2e_test
from motive_proxy.testing.scenarios import ScenarioManager
from motive_proxy.testing.log_collector import LogCollector


@click.command()
@click.option('--scenario', required=True, help='Test scenario name')
@click.option('--turns', default=5, help='Number of conversation turns')
@click.option('--concurrent', default=1, help='Number of concurrent sessions')
@click.option('--protocol', default='openai', help='Protocol to test (openai)')
@click.option('--output', default='./e2e_test_results', help='Output directory for results')
@click.option('--log-level', default='info', help='Logging level')
@click.option('--server-host', default='localhost', help='MotiveProxy server host')
@click.option('--server-port', default=8000, help='MotiveProxy server port')
@click.option('--timeout', default=30.0, help='Test timeout in seconds')
@click.option('--validate-responses', is_flag=True, help='Validate response content')
def main(
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
    
    This tool launches MotiveProxy server and independent test clients as separate processes,
    executing real network communication scenarios.
    
    MotiveProxy itself has no knowledge of testing scenarios.
    """
    click.echo("Starting E2E test automation...")
    click.echo(f"Scenario: {scenario}")
    click.echo(f"Turns: {turns}")
    click.echo(f"Concurrent sessions: {concurrent}")
    click.echo(f"Protocol: {protocol}")
    click.echo(f"Server: {server_host}:{server_port}")
    click.echo(f"Output: {output}")
    click.echo(f"Log level: {log_level}")
    
    try:
        # Run the E2E test
        result = asyncio.run(_run_e2e_test(
            scenario=scenario,
            turns=turns,
            concurrent=concurrent,
            protocol=protocol,
            output_path=Path(output),
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


if __name__ == "__main__":
    main()
