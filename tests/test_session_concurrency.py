"""Concurrency tests for Session deterministic A/B assignment."""

import asyncio
import contextlib
import pytest

from motive_proxy.session import Session


@pytest.mark.asyncio
async def test_simultaneous_connect_deterministic_ab_assignment():
    session = Session(session_id="simul-1", handshake_timeout_seconds=0.2, turn_timeout_seconds=0.2)

    async def client_a():
        # Arrives at the same time nominally; whichever acquires lock first becomes A
        return await session.process_request("A-handshake")

    async def client_b():
        return await session.process_request("B-first")

    # Launch tasks nearly simultaneously
    task_a = asyncio.create_task(client_a())
    task_b = asyncio.create_task(client_b())

    # One of them (A's handshake) should complete with B's first message
    done, pending = await asyncio.wait({task_a, task_b}, return_when=asyncio.FIRST_COMPLETED)
    assert len(done) == 1
    first_result = next(iter(done)).result()
    assert first_result == "B-first"

    # The other task would be waiting for a counterpart message; cancel it to avoid timeout
    for t in pending:
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError, TimeoutError):
            await t


