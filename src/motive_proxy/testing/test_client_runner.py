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

from .llm_client import LLMTestClient, create_llm_client


def safe_print(text: str) -> None:
    """Print text safely, handling encoding issues with emojis."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: encode as utf-8 and decode as ascii with replacement
        safe_text = text.encode('utf-8', errors='replace').decode('ascii', errors='replace')
        print(safe_text)


# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Look for .env file in project root
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Also try loading from current directory
        load_dotenv()
except ImportError:
    # dotenv not available, skip loading
    pass


@click.command()
@click.option('--name', required=True, help='Client name (ClientA, ClientB, etc.)')
@click.option('--server-url', required=True, help='MotiveProxy server URL')
@click.option('--session-id', required=True, help='Session ID to use')
@click.option('--scenario', help='Test scenario name')
@click.option('--role', required=True, help='Client role (A or B)')
@click.option('--api-key', default='test-key', help='API key for authentication')
@click.option('--timeout', default=30.0, help='Request timeout in seconds')
@click.option('--streaming', is_flag=True, help='Use streaming mode')
@click.option('--output', default='./client_output', help='Output directory for logs')
# LLM configuration options
@click.option('--use-llm', is_flag=True, help='Use real LLM instead of canned responses')
@click.option('--llm-provider', default='google', type=click.Choice(['openai', 'anthropic', 'google', 'cohere']), help='LLM provider')
@click.option('--llm-model', default='gemini-2.5-flash', help='LLM model name')
@click.option('--llm-api-key', help='LLM API key (overrides environment variable)')
@click.option('--conversation-prompt', default='Hello! How are you?', help='Initial conversation prompt')
@click.option('--turns', default=5, help='Number of conversation turns for LLM mode')
@click.option('--max-context-messages', default=10, help='Maximum context messages to keep for LLM')
@click.option('--system-prompt', help='System prompt for LLM conversation context')
def main(
    name: str,
    server_url: str,
    session_id: str,
    scenario: str,
    role: str,
    api_key: str,
    timeout: float,
    streaming: bool,
    output: str,
    use_llm: bool,
    llm_provider: str,
    llm_model: str,
    llm_api_key: Optional[str],
    conversation_prompt: str,
    turns: int,
    max_context_messages: int,
    system_prompt: Optional[str]
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
    
    # Validate mutually exclusive options
    if use_llm and scenario:
        logger.error("Cannot use both --scenario and --use-llm. They are mutually exclusive.")
        print(f"❌ Error: Cannot use both --scenario and --use-llm. They are mutually exclusive.")
        sys.exit(1)
    
    if not use_llm and not scenario:
        logger.error("Must specify either --scenario or --use-llm.")
        print(f"❌ Error: Must specify either --scenario or --use-llm.")
        sys.exit(1)
    
    # Create output directory
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize LLM client if requested
        llm_client = None
        if use_llm:
            try:
                llm_model_instance = create_llm_client(
                    provider=llm_provider,
                    model=llm_model,
                    api_key=llm_api_key
                )
                llm_client = LLMTestClient(llm_model_instance, max_context_messages=max_context_messages)
                
                # Set system prompt if provided
                if system_prompt:
                    llm_client.set_system_prompt(system_prompt)
                    logger.info(f"Set system prompt: {system_prompt[:50]}...")
                
                logger.info(f"Initialized LLM client: {llm_provider}/{llm_model} (max_context={max_context_messages})")
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                print(f"❌ Failed to initialize LLM client: {e}")
                sys.exit(1)
        
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
            output_path=output_path,
            llm_client=llm_client,
            conversation_prompt=conversation_prompt,
            turns=turns
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
    output_path: Path,
    llm_client: Optional[LLMTestClient] = None,
    conversation_prompt: str = "Hello! How are you?",
    turns: int = 5
) -> bool:
    """Run the actual test client."""
    
    try:
        # Create LangChain client pointing to MotiveProxy
        # Encode side into model so server can disambiguate sender identity (session_id|A or session_id|B)
        model_with_side = f"{session_id}|{role}"
        client = ChatOpenAI(
            base_url=f"{server_url}/v1",
            api_key=api_key,
            model=model_with_side,
            streaming=streaming,
            timeout=timeout
        )
        
        print(f"{name}: Connected to MotiveProxy at {server_url}")
        
        # Execute test based on mode
        results = []
        
        if llm_client:
            # LLM mode: Direct conversation flow
            print(f"{name}: Starting LLM conversation mode")
            results = await _run_llm_conversation(name, client, llm_client, conversation_prompt, turns, streaming, role)
        else:
            # Scenario mode: Load and execute scenario steps
            scenario_steps = _load_scenario_steps(scenario, role)
            print(f"{name}: Loaded {len(scenario_steps)} scenario steps")
            results = await _run_scenario_steps(name, client, scenario_steps, streaming)
        
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


async def _run_llm_conversation(
    name: str,
    client: ChatOpenAI,
    llm_client: LLMTestClient,
    conversation_prompt: str,
    turns: int,
    streaming: bool,
    role: str
) -> list:
    """Run LLM-to-LLM conversation through MotiveProxy."""
    results = []
    
    if role == "A":
        # Client A initiates handshake by sending the conversation prompt (content ignored by server)
        print(f"{name}: Starting LLM conversation with prompt: {conversation_prompt}")
        
        # Handshake: send prompt, expect to receive B's first real message
        response = await _send_message(client, conversation_prompt, streaming)
        results.append({
            'step': 0,
            'action': 'handshake',
            'message': conversation_prompt,
            'response': response,
            'timestamp': time.time()
        })
        safe_print(f"{name}: Handshake completed. Received first message from B: {response[:100]}...")
        
        # Continue conversation for specified turns
        # Note: A has already completed handshake above.
        # For T turns, A should perform exactly `turns` additional sends to match B's (turns-1) sends after B0.
        for turn in range(turns):
            # Generate LLM response to the last message received from B
            llm_response = await llm_client.process_message(response)
            safe_print(f"{name}: LLM generated response: {llm_response[:100]}...")
            
            # Log context usage
            context_summary = llm_client.get_context_summary()
            print(f"{name}: Context usage: {context_summary['context_messages']}/{context_summary['max_context_messages']} messages ({context_summary['context_usage_percent']:.1f}%)")
            
            # Send LLM response. The server returns B's next message.
            response = await _send_message(client, llm_response, streaming)
            results.append({
                'step': turn + 1,
                'action': 'llm_turn',
                'message': llm_response,
                'response': response,
                'context_summary': context_summary,
                'timestamp': time.time()
            })
            safe_print(f"{name}: LLM turn {turn + 1} completed! Received: {response[:100]}...")
    
    else:  # role == "B"
        # Client B generates the first real message in response to the conversation prompt
        print(f"{name}: Waiting for handshake from Client A, then sending first LLM message...")
        
        # Send our LLM response to the conversation prompt as Side B's first message
        llm_response = await llm_client.process_message(conversation_prompt)
        safe_print(f"{name}: LLM generated initial message: {llm_response[:100]}...")
        
        # Send LLM response through MotiveProxy. This completes A's handshake and returns A's next message.
        response = await _send_message(client, llm_response, streaming)
        results.append({
            'step': 0,
            'action': 'llm_init',
            'message': llm_response,
            'response': response,
            'timestamp': time.time()
        })
        safe_print(f"{name}: Initial LLM message sent! Received A's reply: {response[:100]}...")
        
        # Continue conversation for specified turns
        # Note: B has already sent the initial message (B0) above.
        # For T turns, run (turns - 1) additional B sends to end without a trailing wait.
        b_additional_turns = max(turns - 1, 0)
        for turn in range(b_additional_turns):
            # Generate LLM response to the last message received
            llm_response = await llm_client.process_message(response)
            safe_print(f"{name}: LLM generated response: {llm_response[:100]}...")
            
            # Log context usage
            context_summary = llm_client.get_context_summary()
            print(f"{name}: Context usage: {context_summary['context_messages']}/{context_summary['max_context_messages']} messages ({context_summary['context_usage_percent']:.1f}%)")
            
            # Send LLM response through MotiveProxy
            response = await _send_message(client, llm_response, streaming)
            results.append({
                'step': turn + 1,
                'action': 'llm_turn',
                'message': llm_response,
                'response': response,
                'context_summary': context_summary,
                'timestamp': time.time()
            })
            safe_print(f"{name}: LLM turn {turn + 1} completed! Response: {response[:100]}...")
    
    return results


async def _run_scenario_steps(
    name: str,
    client: ChatOpenAI,
    scenario_steps: list,
    streaming: bool
) -> list:
    """Run scenario-based test steps."""
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
    
    return results


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
