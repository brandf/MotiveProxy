# MotiveProxy Implementation Plan

> A comprehensive, actionable plan to implement MotiveProxy to production quality. Designed for iterative delivery with TDD, single-responsibility components, and proven Python/FastAPI patterns.

## 🎯 Goals

- Build a generic, stateful, bidirectional proxy that emulates the OpenAI Chat Completions API to pair two clients that both expect to initiate conversations.
- Require zero code changes for clients; pairing is done via the `model` parameter (session ID).
- Be protocol-agnostic and extensible to other LLM chat protocols.
- Provide production-ready observability, error handling, and configuration.
- Maintain strong TDD discipline, reproducible tests, and clear documentation.

## 🚫 Non-Goals (for initial releases)

- Persistent storage of sessions across restarts (in-memory only at first).
- Full support for every OpenAI feature (e.g., tools/functions, images, vision). We’ll prioritize the core Chat Completions workflow.
- Multi-hop routing or more than two participants per session.

## 🧭 Design Principles

- Single Responsibility: each component does one thing well.
- Explicit Boundaries: clear interfaces; avoid hidden coupling.
- Async by Default: efficient long-polling; future-proof for streaming.
- Fail Fast, Fail Loud: strict validation and structured error responses.
- Observability First: structured logs, metrics, and trace identifiers.
- Backpressure & Timeouts: protect the server and users from stalls.

## 🏗️ High-Level Architecture

```
           +-------------------+          +-------------------+
           |   Client A (UI)   |          |  Client B (App)   |
           +---------+---------+          +---------+---------+
                     |                              |
                     |  POST /v1/chat/completions   |
                     |  { model: session, ... }     |
                     v                              v
                +-----------------------------------------+
                |             MotiveProxy API             |
                |  FastAPI routes (health, chat)          |
                +-------------------+---------------------+
                                    |
                                    v
                +-------------------+---------------------+
                |              Session Layer              |
                |  SessionManager  |  Session  |  Queues  |
                +-------------------+---------------------+
                                    |
                                    v
                +-------------------+---------------------+
                |        Messaging & Routing Core         |
                |  MessageRouter | Validation | Mapping   |
                +-------------------+---------------------+
                                    |
                                    v
                +-------------------+---------------------+
                |   Observability & Ops (logging, metrics) |
                +-----------------------------------------+
```

## 🧩 Components (Single Responsibility)

1) API Layer (FastAPI)
- Responsibility: HTTP interface; request/response mapping to OpenAI format; status codes.
- Interface: `POST /v1/chat/completions`, `GET /health`, future `/metrics`, `/sessions`.
- Key Behavior: Input validation, routing to Session Layer, consistent error responses.

2) Pydantic Models
- Responsibility: Strongly-typed request/response schemas for OpenAI compatibility (non-stream and stream variants).
- Interface: `ChatCompletionRequest`, `Message`, `ChatCompletionResponse`, `ErrorResponse`.

3) SessionManager
- Responsibility: Lifecycle of sessions (create, lookup, cleanup, expiry), concurrency safety.
- Interface: `get_or_create(session_id)`, `get(session_id)`, `cleanup_expired()`, `close(session_id)`.

4) Session
- Responsibility: Encapsulate a pair of clients and their state machine; track participants; hold queues.
- Interface: `accept_message(from_side, message)`, `await_reply(for_side, timeout)`, `transition(event)`.
- Internals: Two `asyncio.Queue` objects (A->B, B->A), timestamps, state enum, timeouts, locks.

5) MessageRouter
- Responsibility: Apply handshake rules and forward messages across the correct queue; enforce ordering and backpressure.
- Interface: `route(request_context) -> ResponseEnvelope`.

6) Validation & Mapping
- Responsibility: Validate input payloads; map OpenAI fields to internal envelopes and back; unify error handling.
- Interface: `validate_request()`, `to_internal()`, `to_openai_response()`.

7) Observability
- Responsibility: Structured logging (structlog), request IDs, session IDs, counters/timers.
- Interface: `log(event, **fields)`, `metrics.increment(name, tags)`, `metrics.timing(name, value)`.

8) Configuration
- Responsibility: Load env vars and CLI flags; expose typed settings.
- Interface: `Settings` (pydantic settings) consumed by app creation and SessionManager.

9) CLI
- Responsibility: Start server with options (host, port, log-level, reload) and env loading.
- Interface: `motive-proxy` entrypoint powered by `click`.

10) Protocol Extension Points (future)
- Responsibility: Abstraction layer to support other LLM chat protocols behind a stable internal interface.
- Interface: Strategy/adapters for Anthropic, Gemini, etc.

## 🔄 Session State Machine

States
- `EMPTY`: No participants.
- `AWAITING_PEER`: One participant connected (first message is handshake ping).
- `ACTIVE`: Both participants connected; relay messages turn-by-turn.
- `DORMANT`: Temporarily idle; waiting for next request from either side.
- `CLOSING`: Server initiated shutdown/timeout/cleanup.
- `CLOSED`: Session removed.

Events
- `CONNECT_A`, `CONNECT_B`, `TIMEOUT`, `MESSAGE_FROM_A`, `MESSAGE_FROM_B`, `DISCONNECT_A`, `DISCONNECT_B`, `CLOSE`.

Rules (Behavioral Requirements)
- First client to send a valid request for a new `session_id` becomes Side A; its first message is treated as handshake ping and is not forwarded as chat content.
- The request from Side A during handshake is held open until Side B connects (or until `handshake_timeout`).
- Side B’s first real prompt is returned as Side A’s response for the handshake request.
- After handshake, every request is a single turn: a message from one side produces a response from the other side’s last message.
- If the counterpart is not available within `turn_timeout`, return 408 with a standard error body.
- Sessions expire after `session_ttl` of inactivity; all pending waits are completed with 408 and session is closed.
- If both connect simultaneously, the first request the server receives is Side A; the next becomes Side B.

## 📦 Data Contracts (OpenAI Compatibility)

Request (subset initially)
- `model: str` (session_id)
- `messages: [{ role: "user"|"assistant"|"system", content: str }]`
- Optional (future): `stream: bool`, `temperature`, `max_tokens`, etc. (ignored initially; must not break clients)

Response (non-stream initially)
- `id: str`, `object: "chat.completion"`, `created: int`
- `model: str` (echo session_id)
- `choices: [{ index: 0, message: { role: "assistant", content: str }, finish_reason: "stop" }]`
- `usage` (optional placeholder for compatibility)

Errors
- Status codes: 400 (validation), 408 (timeout), 409 (session conflict), 422 (schema), 500 (server), 503 (overloaded)
- Error shape: `{ "error": { "message": str, "type": str, "code": str } }`

## 🧪 Testing Strategy (TDD)

- Unit: SessionManager lifecycle, Session state machine, MessageRouter routing, validation/converters.
- Integration: API endpoints for handshake, normal turns, timeouts, concurrent sessions, invalid payloads.
- Concurrency: Many sessions in parallel; race conditions (simultaneous connect); backpressure.
- E2E: Example clients (httpx) simulating both sides; durable tests over ad-hoc shell.
- Regression: Add tests for every bug found.

## 🔐 Security & Limits

- Basic rate limiting (per IP and per session) — protect from abuse.
- Size limits on payloads; reject oversized messages with 413.
- CORS configuration for browser-based chat UIs.
- Optional auth (API key) for deployments, disabled by default in dev.

## 📊 Observability

- Structured logs via structlog with fields: `session_id`, `request_id`, `side`, `state`.
- Metrics: `sessions_active`, `messages_total`, `handshake_time_ms`, `turn_latency_ms`, `timeouts_total`.
- Optional `/metrics` endpoint (Prometheus) behind a flag.

## 🧰 Configuration (pydantic settings)

- `HOST`, `PORT`, `LOG_LEVEL`
- `SESSION_TTL_SECONDS` (default 3600)
- `HANDSHAKE_TIMEOUT_SECONDS` (default 30)
- `TURN_TIMEOUT_SECONDS` (default 30)
- `MAX_SESSIONS` (default 100)
- `MAX_MESSAGE_BYTES` (default 64 KiB)
- `ENABLE_PROMETHEUS` (default false)

## 📜 Execution Plan & Milestones

### M0: Baseline (existing)
- Routes: `/health`, `/v1/chat/completions` stub.
- CI locally with `invoke`, pytest, linting, formatting, pre-commit.

### M1: Handshake + Simple Turn (non-stream)
- Implement SessionManager and Session with in-memory queues and timeouts.
- Implement handshake semantics and first-turn behavior.
- Return proper OpenAI-shaped responses and 408 on timeouts.

### M2: Robust Session Management
- Session TTL cleanup task; graceful close; max sessions limit.
- Concurrency safety (locks) and race handling.
- Error taxonomy and consistent error payloads.

### M3: Observability ✅ **COMPLETE**
- structlog fields, correlation IDs, counters/timers. ✅
- Optional `/metrics` (Prometheus) behind a flag. ✅

### M4: Streaming (Optional but highly desired)
- Support `stream: true` via Server-Sent Events for OpenAI-compatible streaming.
- Maintain backpressure; chunk forwarding.

### M5: Protocol Extensions (behind feature flags)
- Abstraction for protocol adapters; add a second protocol (e.g., Anthropic) to validate design.

### M6: Hardening & Ops
- Rate limiting, payload limits, CORS refinements, API key auth (optional).
- Admin endpoints: list sessions (masked), health details. ✅ Basic admin endpoint implemented

## ✅ Detailed Checklist (Emoji Checkboxes)

### Foundation
- ☑ README, DEVELOPMENT, AGENT present and linked
- ☑ `invoke` tasks for test, lint, format, run
- ☑ Basic FastAPI app and health route

### API Models & Validation
- ☑ Define `Message`, `ChatCompletionRequest`, `ChatCompletionResponse` (non-stream)
- ☑ Centralize validation errors → `ErrorResponse` (global 422 handler)
- ☑ Map internal envelopes ⇄ OpenAI response structure (non-stream)

### Session Layer
- ☑ Implement `Session` state and structure (locks, futures; M1 minimal)
- ☑ Implement handshake logic and `await_reply()` with timeouts
- ☑ Implement `SessionManager` (get_or_create, close, max sessions) — background cleanup pending
- ☑ Background cleanup task for expired sessions (lifespan + admin endpoint)

### Routing & Behavior
- ☐ Implement `MessageRouter.route()` for A/B turns (Session handles turns in M1)
- ☑ Enforce handshake rules and first message ignore for A
- ☑ Implement 408 for handshake/turn timeout with standard error body
- ☑ Handle simultaneous connect; deterministic A/B assignment (tested)

### Observability
- ☑ Integrate structlog; add session/request fields
- ☑ Add counters and timers; expose optionally via `/metrics`

### Configuration & CLI
- ☑ Add pydantic settings for timeouts, limits, flags
- ☑ Wire settings into app and SessionManager
- ☑ Ensure `motive-proxy --help` shows effective config

### Streaming (Optional Milestone)
- ☐ Add `stream: true` support via SSE
- ☐ Stream deltas in OpenAI-compatible format

### Protocol Extensions (Optional Milestone)
- ☐ Define adapter interface for alternate protocols
- ☐ Add one additional protocol to validate design

### Security & Limits
- ☐ Add basic rate limiting (per IP/session)
- ☐ Enforce payload size limit; 413 on exceed
- ☐ CORS configuration and tests
- ☐ Optional API key auth

### Admin & Ops
- ☐ `/sessions` admin endpoint (redacted info, behind flag)
- ☐ Health details endpoint (uptime, active sessions)

### Testing (expand existing suite)
- ☑ Unit tests: Session, SessionManager (minimal); validators; Router TBD
- ☑ Integration: handshake, turns, timeouts, concurrent sessions
- ☑ Concurrency & race: simultaneous connect (burst load pending)
- ☐ E2E: example clients covering end-to-end flows
- ☐ Regression: add tests for each discovered bug

## 📐 Acceptance Criteria (per Milestone)

- M1: Handshake works deterministically; A’s first call returns B’s first prompt or 408 within timeout. Basic turn completes with 200 and OpenAI-shaped response.
- M2: Sessions expire and clean up; max sessions enforced; concurrent sessions do not leak memory; consistent 408/409/422/500 errors.
- M3: Logs include `session_id`, `request_id`, `side`; metrics report active sessions, timeouts, and latencies.
- M4: Streaming interoperates with common OpenAI-compatible UIs; non-stream remains unaffected.

## 🧱 Directory & Module Layout (proposed)

- `src/motive_proxy/app.py` — FastAPI app factory, wiring
- `src/motive_proxy/routes/health.py` — health endpoint
- `src/motive_proxy/routes/chat_completions.py` — chat endpoint(s)
- `src/motive_proxy/models.py` — pydantic models (request/response/errors)
- `src/motive_proxy/session_manager.py` — SessionManager (lifecycle)
- `src/motive_proxy/session.py` — Session (state, queues, rules)
- `src/motive_proxy/router.py` — MessageRouter
- `src/motive_proxy/settings.py` — pydantic settings
- `src/motive_proxy/observability.py` — logging/metrics helpers
- `src/motive_proxy/cli.py` — CLI entrypoint

## 📉 Risks & Mitigations

- Deadlocks/races in async flows → Use clear ownership, minimal shared state, `asyncio.Queue`, and thorough concurrency tests.
- Long-poll resource usage → Reasonable timeouts, limits, and backpressure via queues.
- API compatibility drift → Constrain scope; add compatibility tests against known client expectations.
- Memory growth → TTL cleanup, max sessions, payload limits.

## 📎 References

- README: project overview and usage
- AGENT.md: TDD workflow, confidence report, durable testing expectations
- DEVELOPMENT.md: local environment and commands

---

When implementing, follow AGENT.md’s TDD workflow. Before running the real app, supply the required Confidence Analysis Report. Then move through the checklist above, marking items as complete.


