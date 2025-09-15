"""Test that captures the session protocol bug and expected fix."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from motive_proxy.session import Session


class TestSessionProtocolFix:
    """Test that captures the session protocol bug and expected fix."""
    
    @pytest.mark.asyncio
    async def test_session_handshake_should_complete_both_sides(self):
        """Test that after handshake, both clients should complete without waiting."""
        session = Session("test-session", handshake_timeout_seconds=2.0, turn_timeout_seconds=2.0)
        
        print("=== Testing handshake completion ===")
        
        # Client A connects (Side A handshake)
        client_a_task = asyncio.create_task(session.process_request("A's first message"))
        
        # Give A a moment to establish connection
        await asyncio.sleep(0.1)
        
        # Client B connects (Side B first message)
        client_b_task = asyncio.create_task(session.process_request("B's first message"))
        
        # Wait for both to complete
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Client A got: '{client_a_response}'")
            print(f"Client B got: '{client_b_response}'")
            
            # After handshake:
            # - Client A should get Client B's message
            # - Client B should get... what? It shouldn't wait for another message!
            
            assert client_a_response == "B's first message"
            
            # This is the bug: Client B is waiting for Client A's next message
            # But Client A isn't sending one!
            # The fix should make Client B complete without waiting
            
            # FAILING TEST: This should fail until we fix the protocol
            assert client_b_response is not None, "Client B should complete without waiting for another message"
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Handshake should complete both sides, but timed out: {e}")
    
    @pytest.mark.asyncio
    async def test_session_alternating_turns_should_work(self):
        """Test that alternating turns work after handshake."""
        session = Session("test-session", handshake_timeout_seconds=2.0, turn_timeout_seconds=2.0)
        
        print("=== Testing alternating turns ===")
        
        # Handshake
        client_a_task = asyncio.create_task(session.process_request("A's handshake"))
        await asyncio.sleep(0.1)
        client_b_task = asyncio.create_task(session.process_request("B's handshake"))
        
        # Wait for handshake to complete
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Handshake - Client A got: '{client_a_response}'")
            print(f"Handshake - Client B got: '{client_b_response}'")
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Handshake failed: {e}")
        
        # Now test alternating turns
        print("\n=== Testing Turn 1 ===")
        
        # Client A sends message first
        client_a_task = asyncio.create_task(session.process_request("A's turn 1"))
        
        # Give A a moment to establish the turn
        await asyncio.sleep(0.1)
        
        # Client B sends message second
        client_b_task = asyncio.create_task(session.process_request("B's turn 1"))
        
        # Wait for both
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Turn 1 - Client A got: '{client_a_response}'")
            print(f"Turn 1 - Client B got: '{client_b_response}'")
            
            # Turn 1 should work
            assert client_a_response == "B's turn 1"
            assert client_b_response == "A's turn 1"
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Turn 1 failed: {e}")
        
        # Test Turn 2
        print("\n=== Testing Turn 2 ===")
        
        # Client A sends message
        client_a_task = asyncio.create_task(session.process_request("A's turn 2"))
        
        # Give A a moment
        await asyncio.sleep(0.1)
        
        # Client B sends message
        client_b_task = asyncio.create_task(session.process_request("B's turn 2"))
        
        # Wait for both
        try:
            client_a_response = await asyncio.wait_for(client_a_task, timeout=5.0)
            client_b_response = await asyncio.wait_for(client_b_task, timeout=5.0)
            
            print(f"Turn 2 - Client A got: '{client_a_response}'")
            print(f"Turn 2 - Client B got: '{client_b_response}'")
            
            # Turn 2 should work
            assert client_a_response == "B's turn 2"
            assert client_b_response == "A's turn 2"
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Turn 2 failed: {e}")
