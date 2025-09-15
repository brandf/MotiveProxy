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
@click.option('--scenario', help='Test scenario name (not needed when using LLMs)')
@click.option('--turns', default=5, help='Number of conversation turns')
@click.option('--concurrent', default=1, help='Number of concurrent sessions')
@click.option('--protocol', default='openai', help='Protocol to test (openai)')
@click.option('--output', default='./e2e_test_results', help='Output directory for results')
@click.option('--log-level', default='info', help='Logging level')
@click.option('--server-host', default='localhost', help='MotiveProxy server host')
@click.option('--server-port', default=8000, help='MotiveProxy server port')
@click.option('--timeout', default=30.0, help='Test timeout in seconds')
@click.option('--validate-responses', is_flag=True, help='Validate response content')
# LLM configuration options
@click.option('--use-llms', is_flag=True, help='Use real LLMs instead of canned responses')
@click.option('--llm-provider-a', default='google', type=click.Choice(['openai', 'anthropic', 'google', 'cohere']), help='LLM provider for Client A')
@click.option('--llm-model-a', default='gemini-2.5-flash', help='LLM model for Client A')
@click.option('--llm-provider-b', default='google', type=click.Choice(['openai', 'anthropic', 'google', 'cohere']), help='LLM provider for Client B')
@click.option('--llm-model-b', default='gemini-2.5-flash', help='LLM model for Client B')
@click.option('--conversation-prompt', default='Hello! Let\'s have a conversation about artificial intelligence.', help='Initial conversation prompt')
@click.option('--max-context-messages', default=10, help='Maximum context messages to keep for LLM')
@click.option('--system-prompt', help='System prompt for LLM conversation context')
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
    validate_responses: bool,
    use_llms: bool,
    llm_provider_a: str,
    llm_model_a: str,
    llm_provider_b: str,
    llm_model_b: str,
    conversation_prompt: str,
    max_context_messages: int,
    system_prompt: Optional[str]
):
    """E2E testing automation for MotiveProxy.
    
    This tool launches MotiveProxy server and independent test clients as separate processes,
    executing real network communication scenarios.
    
    MotiveProxy itself has no knowledge of testing scenarios.
    """
    click.echo("Starting E2E test automation...")
    if use_llms:
        click.echo("Mode: LLM-to-LLM conversation")
        click.echo(f"LLM Provider A: {llm_provider_a}/{llm_model_a}")
        click.echo(f"LLM Provider B: {llm_provider_b}/{llm_model_b}")
        click.echo(f"Conversation prompt: {conversation_prompt}")
    else:
        click.echo(f"Scenario: {scenario}")
    click.echo(f"Turns: {turns}")
    click.echo(f"Concurrent sessions: {concurrent}")
    click.echo(f"Protocol: {protocol}")
    click.echo(f"Server: {server_host}:{server_port}")
    click.echo(f"Output: {output}")
    click.echo(f"Log level: {log_level}")
    
    try:
        # Validate scenario requirement for non-LLM tests
        if not use_llms and not scenario:
            click.echo("❌ Error: --scenario is required when not using LLMs")
            sys.exit(1)
        
        # For LLM tests, scenario should be None (not used)
        if use_llms:
            scenario = None
        
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
            validate_responses=validate_responses,
            use_llms=use_llms,
            llm_provider_a=llm_provider_a,
            llm_model_a=llm_model_a,
            llm_provider_b=llm_provider_b,
            llm_model_b=llm_model_b,
            conversation_prompt=conversation_prompt,
            max_context_messages=max_context_messages,
            system_prompt=system_prompt
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
