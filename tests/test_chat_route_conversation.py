import asyncio
import os
import pytest
import httpx

from motive_proxy.app import create_app


@pytest.mark.asyncio
async def test_chat_route_handshake_and_two_turns():
    """Validate handshake and alternating turns via /v1/chat/completions using in-process ASGI client.

    Flow:
      - A handshakes (content ignored)
      - B sends first real message (B0) → delivered to A
      - A sends A1 → delivered to B (completes B0 request)
      - B sends B1 → delivered to A (completes A1 request)
    """
    # Use short timeouts for fast deterministic test
    os.environ["MOTIVE_PROXY_HANDSHAKE_TIMEOUT_SECONDS"] = "1.0"
    os.environ["MOTIVE_PROXY_TURN_TIMEOUT_SECONDS"] = "1.0"

    app = create_app()

    # Ensure FastAPI lifespan executes so app.state.session_manager exists
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Helpers
            async def post_chat(model: str, content: str) -> httpx.Response:
                body = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "stream": False,
                }
                return await client.post("/v1/chat/completions", json=body, timeout=5.0)

            session = "t-session"
            model_a = f"{session}|A"
            model_b = f"{session}|B"

            # Step 0: Start A handshake and B initial concurrently
            a_handshake_task = asyncio.create_task(post_chat(model_a, "A-handshake"))
            await asyncio.sleep(0)  # yield
            b0_task = asyncio.create_task(post_chat(model_b, "B0"))

            # A should receive B0
            a_resp = await a_handshake_task
            assert a_resp.status_code == 200
            a_json = a_resp.json()
            assert a_json["choices"][0]["message"]["content"] == "B0"

            # Step 1: A sends A1
            a1_task = asyncio.create_task(post_chat(model_a, "A1"))

            # B0 should now complete delivering A1
            b0_resp = await b0_task
            assert b0_resp.status_code == 200
            b0_json = b0_resp.json()
            assert b0_json["choices"][0]["message"]["content"] == "A1"

            # Step 2: B sends B1
            b1_task = asyncio.create_task(post_chat(model_b, "B1"))

            # A1 should now complete delivering B1
            a1_resp = await a1_task
            assert a1_resp.status_code == 200
            a1_json = a1_resp.json()
            assert a1_json["choices"][0]["message"]["content"] == "B1"

            # Step 3: Optional second alternation to ensure stability
            a2_task = asyncio.create_task(post_chat(model_a, "A2"))
            b1_resp = await b1_task
            assert b1_resp.status_code == 200
            b1_json = b1_resp.json()
            assert b1_json["choices"][0]["message"]["content"] == "A2"

            # Finalize by sending B2 to complete A2
            b2_task = asyncio.create_task(post_chat(model_b, "B2"))
            a2_resp = await a2_task
            assert a2_resp.status_code == 200
            a2_json = a2_resp.json()
            assert a2_json["choices"][0]["message"]["content"] == "B2"

            # Cancel B2 task (no counterpart waiting yet)
            b2_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await b2_task


@pytest.mark.asyncio
async def test_out_of_order_concurrent_turns_buffering():
    """After handshake, send A1 and B1 concurrently and ensure correct delivery using buffers."""
    os.environ["MOTIVE_PROXY_HANDSHAKE_TIMEOUT_SECONDS"] = "1.0"
    os.environ["MOTIVE_PROXY_TURN_TIMEOUT_SECONDS"] = "1.0"

    app = create_app()

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            async def post_chat(model: str, content: str) -> httpx.Response:
                body = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "stream": False,
                }
                return await client.post("/v1/chat/completions", json=body, timeout=5.0)

            session = "t2-session"
            model_a = f"{session}|A"
            model_b = f"{session}|B"

            # Handshake
            a_handshake_task = asyncio.create_task(post_chat(model_a, "A-handshake"))
            await asyncio.sleep(0)
            b0_task = asyncio.create_task(post_chat(model_b, "B0"))
            await a_handshake_task
            await b0_task

            # Next expected is A. Send A1 and B1 nearly simultaneously.
            a1_task = asyncio.create_task(post_chat(model_a, "A1"))
            await asyncio.sleep(0)
            b1_task = asyncio.create_task(post_chat(model_b, "B1"))

            a1_resp = await a1_task
            b1_resp = await b1_task

            assert a1_resp.status_code == 200
            assert b1_resp.status_code == 200

            # A should receive B1; B should receive A1
            assert a1_resp.json()["choices"][0]["message"]["content"] == "B1"
            assert b1_resp.json()["choices"][0]["message"]["content"] == "A1"
