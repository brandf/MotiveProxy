"""Session and turn-based routing primitives for MotiveProxy.

Implements the handshake and simple turn protocol using asyncio futures.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import time
from enum import Enum
from typing import Optional


class Side(str, Enum):
    A = "A"
    B = "B"


@dataclass
class Session:
    """Represents a bidirectional session with turn-based message exchange.

    Protocol rules:
    - First request for a new session is Side A (handshake). Its content is ignored.
    - Second request is Side B's first real message; it completes A's handshake.
    - Thereafter, requests alternate A/B. Each request returns the other side's next message.
    """

    session_id: str
    handshake_timeout_seconds: float = 30.0
    turn_timeout_seconds: float = 30.0

    # Internal state
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _side_a_connected: bool = field(default=False, init=False)
    _side_b_connected: bool = field(default=False, init=False)
    _next_expected: Side = field(default=Side.A, init=False)
    _pending_for_a: Optional[asyncio.Future[str]] = field(default=None, init=False)
    _pending_for_b: Optional[asyncio.Future[str]] = field(default=None, init=False)
    # Buffers to handle out-of-order sends when counterpart isn't yet waiting
    _buffer_for_a: Optional[str] = field(default=None, init=False, repr=False)
    _buffer_for_b: Optional[str] = field(default=None, init=False, repr=False)
    _created_ts: float = field(default_factory=lambda: time.time(), init=False, repr=False)
    _last_activity_ts: float = field(default_factory=lambda: time.time(), init=False, repr=False)

    async def process_request(self, content: str, sender_side: Optional[Side] = None) -> str:
        """Process an incoming request content and wait for counterpart reply.

        Returns the counterpart's next message content or raises asyncio.TimeoutError.
        """

        # Determine behavior under lock and produce a future to await afterward
        async with self._lock:
            loop = asyncio.get_running_loop()
            self._last_activity_ts = time.time()

            if not self._side_a_connected:
                # First ever request → becomes A handshake; ignore content; wait for B
                self._side_a_connected = True
                self._pending_for_a = loop.create_future()
                wait_future = self._pending_for_a
                timeout = self.handshake_timeout_seconds
                self._next_expected = Side.B
                # Return future to wait outside lock
                # A's content is not forwarded
                pass
                # release lock implicitly at end of block
            elif not self._side_b_connected:
                # Second unique request → becomes B first; deliver B's content to A and wait for A's next
                self._side_b_connected = True
                if self._pending_for_a and not self._pending_for_a.done():
                    self._pending_for_a.set_result(content)  # A gets B's content
                # Now B waits for A's next
                self._pending_for_b = loop.create_future()
                wait_future = self._pending_for_b
                timeout = self.turn_timeout_seconds
                self._next_expected = Side.A
            else:
                # Both connected → alternate by expected side
                side_to_treat = sender_side or self._next_expected
                if side_to_treat == Side.A:
                    # Treat this request as coming from A
                    if self._pending_for_b and not self._pending_for_b.done():
                        self._pending_for_b.set_result(content)
                    else:
                        # Counterpart not waiting yet; buffer for B
                        self._buffer_for_b = content
                    # A waits for B's next message (serve from buffer if present)
                    if self._buffer_for_a is not None:
                        buffered = self._buffer_for_a
                        self._buffer_for_a = None
                        fut = loop.create_future()
                        fut.set_result(buffered)
                        wait_future = fut
                    else:
                        self._pending_for_a = loop.create_future()
                        wait_future = self._pending_for_a
                    timeout = self.turn_timeout_seconds
                    self._next_expected = Side.B
                else:
                    # Treat this request as coming from B
                    if self._pending_for_a and not self._pending_for_a.done():
                        self._pending_for_a.set_result(content)
                    else:
                        # Counterpart not waiting yet; buffer for A
                        self._buffer_for_a = content
                    # B waits for A's next message (serve from buffer if present)
                    if self._buffer_for_b is not None:
                        buffered = self._buffer_for_b
                        self._buffer_for_b = None
                        fut = loop.create_future()
                        fut.set_result(buffered)
                        wait_future = fut
                    else:
                        self._pending_for_b = loop.create_future()
                        wait_future = self._pending_for_b
                    timeout = self.turn_timeout_seconds
                    self._next_expected = Side.A

        # Wait outside the lock to avoid deadlocks
        return await asyncio.wait_for(wait_future, timeout=timeout)

    def metadata(self) -> dict:
        """Return minimal, non-sensitive metadata for admin queries."""
        return {
            "session_id": self.session_id,
            "created_ts": self._created_ts,
            "last_activity_ts": self._last_activity_ts,
        }


