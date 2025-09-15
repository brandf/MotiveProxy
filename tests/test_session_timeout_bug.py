"""Test that captures the session timeout bug."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from motive_proxy.session import Session


class TestSessionTimeoutBug:
    """Test that captures the session timeout bug."""
    
    @pytest.mark.asyncio
    async def test_session_timeout_after_first_exchange(self):
        """Test that sessions timeout after the first exchange."""
        session = Session("test-session", handshake_timeout_seconds=2.0, turn_timeout_seconds=2.0)
        
        # Turn 1: Handshake
        print("=== Turn 1: Handshake ===")
        
        # Client A connects (Side A handshake)
        client_a_task = asyncio.create_task(session.process_request("Hello from A"))
        
        # Give A a moment to establish connection
        await asyncio.sleep(0.1)
        
        # Client B connects (Side B first message)
        client_b_task = asyncio.create_task(session.process_request("Hello from B"))
        
        # Wait for both to complete
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Turn 1 - Client A got: '{client_a_response}'")
            print(f"Turn 1 - Client B got: '{client_b_response}'")
            
            # Turn 1 should work
            assert client_a_response == "Hello from B"
            assert client_b_response == "Hello from A"  # This might be wrong based on protocol
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Turn 1 timed out: {e}")
        
        # Turn 2: This should work but currently fails
        print("\n=== Turn 2: First real exchange ===")
        
        # Client A sends message
        client_a_task = asyncio.create_task(session.process_request("Message 2 from A"))
        
        # Give A a moment
        await asyncio.sleep(0.1)
        
        # Client B sends message
        client_b_task = asyncio.create_task(session.process_request("Message 2 from B"))
        
        # Wait for both to complete
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Turn 2 - Client A got: '{client_a_response}'")
            print(f"Turn 2 - Client B got: '{client_b_response}'")
            
            # Turn 2 should work
            assert client_a_response == "Message 2 from B"
            assert client_b_response == "Message 2 from A"
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Turn 2 timed out: {e}")
        
        # Turn 3: This should also work
        print("\n=== Turn 3: Second real exchange ===")
        
        # Client A sends message
        client_a_task = asyncio.create_task(session.process_request("Message 3 from A"))
        
        # Give A a moment
        await asyncio.sleep(0.1)
        
        # Client B sends message
        client_b_task = asyncio.create_task(session.process_request("Message 3 from B"))
        
        # Wait for both to complete
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Turn 3 - Client A got: '{client_a_response}'")
            print(f"Turn 3 - Client B got: '{client_b_response}'")
            
            # Turn 3 should work
            assert client_a_response == "Message 3 from B"
            assert client_b_response == "Message 3 from A"
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Turn 3 timed out: {e}")
    
    @pytest.mark.asyncio
    async def test_session_protocol_expectations(self):
        """Test what the session protocol actually does vs what we expect."""
        session = Session("test-session", handshake_timeout_seconds=2.0, turn_timeout_seconds=2.0)
        
        # Test the actual protocol behavior
        print("=== Testing actual protocol behavior ===")
        
        # Client A connects first
        client_a_task = asyncio.create_task(session.process_request("A's first message"))
        
        # Give A a moment
        await asyncio.sleep(0.1)
        
        # Client B connects second
        client_b_task = asyncio.create_task(session.process_request("B's first message"))
        
        # Wait for both
        client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
        client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
        
        print(f"Client A got: '{client_a_response}'")
        print(f"Client B got: '{client_b_response}'")
        
        # According to the protocol:
        # - A's first message content is ignored
        # - B's first message content is delivered to A
        # - B waits for A's next message
        
        # So A should get B's message, B should get... what?
        # This test documents the actual behavior
        assert client_a_response == "B's first message"
        
        # B should get A's next message, but A hasn't sent one yet
        # So B should be waiting... but what does it get?
        # This is where the protocol might be confusing
