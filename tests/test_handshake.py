"""Handshake and turn-based routing tests for MotiveProxy.

These tests validate the A/B pairing and the initial handshake:
- Client A sends a handshake "ping" and waits
- Client B sends the first real prompt; A receives it as the response
- Client A replies; B receives it as the response to its first request
"""

import asyncio

import httpx
import pytest


@pytest.mark.asyncio
async def test_handshake_and_first_turn(app):
    """Validate handshake and first turn between two clients using the same session."""
    session_id = "handshake-session-1"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Client A sends handshake ping and waits for Client B
        async def client_a_handshake():
            resp = await client.post(
                "/v1/chat/completions",
                json={
                    "model": session_id,
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
            return resp

        # Client B sends the first real prompt
        async def client_b_first():
            await asyncio.sleep(0.05)  # ensure A arrives first
            resp = await client.post(
                "/v1/chat/completions",
                json={
                    "model": session_id,
                    "messages": [
                        {"role": "user", "content": "Hello from B"}
                    ],
                },
            )
            return resp

        task_a = asyncio.create_task(client_a_handshake())
        task_b = asyncio.create_task(client_b_first())

        # A's handshake should complete with B's first message
        a_resp = await task_a
        assert a_resp.status_code == 200
        a_data = a_resp.json()
        assert a_data["choices"][0]["message"]["content"] == "Hello from B"

        # Now Client A replies; this should complete Client B's first request
        async def client_a_reply():
            resp = await client.post(
                "/v1/chat/completions",
                json={
                    "model": session_id,
                    "messages": [
                        {"role": "user", "content": "Reply from A"}
                    ],
                },
            )
            return resp

        task_a2 = asyncio.create_task(client_a_reply())
        b_resp = await task_b
        assert b_resp.status_code == 200
        b_data = b_resp.json()
        assert b_data["choices"][0]["message"]["content"] == "Reply from A"

        # A's second request should now wait for B's next turn
        async def client_b_second():
            await asyncio.sleep(0.05)
            resp = await client.post(
                "/v1/chat/completions",
                json={
                    "model": session_id,
                    "messages": [
                        {"role": "user", "content": "Another from B"}
                    ],
                },
            )
            return resp

        task_b2 = asyncio.create_task(client_b_second())

        a2_resp = await task_a2
        assert a2_resp.status_code == 200
        a2_data = a2_resp.json()
        assert a2_data["choices"][0]["message"]["content"] == "Another from B"

        # And B's second should now wait for A's next turn; send a final reply
        async def client_a_third():
            await asyncio.sleep(0.05)
            resp = await client.post(
                "/v1/chat/completions",
                json={
                    "model": session_id,
                    "messages": [
                        {"role": "user", "content": "Final from A"}
                    ],
                },
            )
            return resp

        task_a3 = asyncio.create_task(client_a_third())
        b2_resp = await task_b2
        assert b2_resp.status_code == 200
        b2_data = b2_resp.json()
        assert b2_data["choices"][0]["message"]["content"] == "Final from A"


