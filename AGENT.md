# Agent Development Guidelines

This document establishes expectations for LLM coding agents working on the MotiveProxy project. All development must follow **Test-Driven Development (TDD)** principles.

> 🧭 **IMPORTANT: PLAN.md is the living source of truth.** Read it before starting any work, re-read it frequently during a task, and keep it up to date. No implementation should begin without a corresponding PLAN update.

## Critical Architectural Principles

### MotiveProxy Independence
**MotiveProxy MUST remain completely independent from Motive.** This is a fundamental architectural requirement:

- **Zero Dependencies**: MotiveProxy must have NO dependencies on Motive code, configs, or knowledge
- **Zero References**: MotiveProxy code must NEVER mention, import, or reference Motive
- **Independent Development**: Development of MotiveProxy and Motive must remain completely separate
- **Generic Design**: MotiveProxy should be designed as a generic proxy that could work with any compatible client

### Testing Strategy for External Connections
When testing MotiveProxy with incoming connections, follow this priority order:

#### A) Deterministic Integration Tests (PREFERRED)
- Write deterministic integration tests with **mocked/canned connections**
- Test specific features using **minimal test repositories**
- Use controlled, predictable test scenarios
- Ensure tests can run in CI/CD without external dependencies
- Focus on testing MotiveProxy's behavior, not the external client

#### B) Manual Integration Testing (SECONDARY)
- Provide step-by-step instructions for human manual testing
- Human connects both sessions while agent monitors MotiveProxy logs
- Verify correct behavior through log analysis
- Use this approach only when deterministic tests are insufficient

**Always prefer approach A before B.** Manual testing should be a last resort for complex integration scenarios that cannot be adequately mocked.

## Testing Pyramid Strategy (Must Read)

MotiveProxy requires a comprehensive testing strategy with multiple tiers, each serving specific purposes. All tests must be fast, deterministic, and appropriate for their tier.

### Testing Pyramid Overview

```
    🔺 E2E Tests (Real Network)
   🔺🔺 Integration Tests (Sandboxed)  
  🔺🔺🔺 Unit Tests (Isolated)
```

### Tier 1: Unit Tests ⭐⭐⭐⭐⭐
**Purpose**: Test individual components in complete isolation
- **Scope**: Single functions, classes, methods
- **Speed**: < 10ms per test
- **Dependencies**: None (pure functions) or mocked dependencies
- **Network**: None
- **Examples**: Parser logic, validation functions, data transformations

### Tier 2: Sandboxed Integration Tests ⭐⭐⭐⭐
**Purpose**: Test component interactions without external dependencies
- **Scope**: Multiple components working together
- **Speed**: < 100ms per test
- **Dependencies**: Mocked/canned responses
- **Network**: In-process ASGI clients only
- **Examples**: HTTP request/response flows, WebSocket handshakes, session management

### Tier 3: E2E Tests ⭐⭐⭐
**Purpose**: Validate complete user workflows with real network
- **Scope**: Full system with real clients and servers
- **Speed**: < 30 seconds per test
- **Dependencies**: Real MotiveProxy instance, real test clients
- **Network**: Real TCP/WebSocket connections
- **Examples**: Complete conversation flows, multi-client scenarios, error handling

### Hard Rules for Each Tier

#### Unit Tests (Tier 1)
- **Zero external dependencies**: No imports of network libraries
- **Pure functions preferred**: Test logic without side effects
- **Mock everything**: Use `unittest.mock` for any external calls
- **Fast execution**: Must run in milliseconds

#### Sandboxed Integration Tests (Tier 2)
- **Use in-process ASGI clients**: Test via FastAPI/Starlette without starting a real server
- **Never make real network calls**: No sockets, ports, or external services
- **Short timeouts in tests**: Override protocol timeouts to ≤ 200ms so unpaired requests return quickly
- **No long sleeps**: Replace `time.sleep` with tiny async delays just to yield (e.g., `await asyncio.sleep(0.01)`) when sequencing is needed
- **Deterministic ordering**: Use controlled scheduling instead of timing-based assumptions
- **Canned responses**: Use predefined request/response pairs for external API calls

#### E2E Tests (Tier 3)
- **Real subprocesses**: Launch actual MotiveProxy and test client processes
- **Real network**: Use actual TCP/WebSocket connections
- **Timeout protection**: Set reasonable timeouts (5-30 seconds) to prevent hanging
- **Cleanup required**: Always terminate subprocesses and clean up resources
- **Separate from core**: E2E tests should be external tools, not part of core MotiveProxy

### Critical Testing Workflow Lessons

#### Test Suite Performance Standards ⭐⭐⭐⭐⭐
**All pytest tests MUST be fast and deterministic:**
- **Total suite time**: < 30 seconds for 100+ tests
- **Individual test time**: < 100ms per test (preferably < 10ms)
- **Zero flaky tests**: Tests must pass consistently in CI/CD
- **Zero hanging tests**: No tests should wait indefinitely

#### Test Suite Cleanup Protocol 🧹
**When test suite becomes slow or unreliable:**
1. **Identify slow tests**: Use `pytest --durations=10` to find bottlenecks
2. **Categorize violations**: Separate E2E tests from pytest suite
3. **Remove problematic tests**: Delete tests that violate sandboxing principles
4. **Verify speed**: Ensure total suite runs in < 30 seconds
5. **Document separation**: Move E2E tests to external tools

#### Anti-Patterns to Avoid ❌
- **Real subprocess tests in pytest**: Use external E2E tools instead
- **Real network calls in pytest**: Use TestClient/ASGITransport
- **Long sleeps in tests**: Use `await asyncio.sleep(0.01)` for sequencing
- **Outdated test references**: Remove tests referencing deleted functionality
- **Mixed test tiers**: Keep unit/integration/E2E tests properly separated

#### Test Suite Health Metrics 📊
**Monitor these metrics continuously:**
- **Total execution time**: Should decrease over time, not increase
- **Failure rate**: Should be 0% in CI/CD
- **Test count**: Should grow with features, not shrink due to removals
- **Warning count**: Should decrease over time

- **Recommended patterns**
  - **ASGI client (sync)**
    ```python
    from fastapi.testclient import TestClient
    from motive_proxy.app import create_app

    app = create_app()
    client = TestClient(app)
    resp = client.post("/v1/chat/completions", json={"model": "s1", "messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code in [200, 408]
    ```

  - **ASGI client (async, fully in-process)**
    ```python
    import httpx, asyncio
    from motive_proxy.app import create_app

    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/v1/chat/completions", json={"model": "s1", "messages": [{"role": "user", "content": "hi"}]})
        assert r.status_code in [200, 408]
    ```

  - **Force short protocol timeouts in tests**
    The chat route holds requests open during handshake/turns. In tests, override the session timeouts so unpaired calls return quickly.
    ```python
    import pytest
    from motive_proxy.session_manager import SessionManager
    import motive_proxy.routes.chat_completions as cc

    @pytest.fixture(autouse=True)
    def fast_timeouts():
        # Ensure all tests use short timeouts (≤200ms)
        cc._session_manager = SessionManager(handshake_timeout_seconds=0.2, turn_timeout_seconds=0.2)
        yield
    ```

- **Do / Don’t**
  - **Do**: Patch timeouts low in tests (≤ 200ms)
  - **Do**: Use in-process ASGI clients (no real network)
  - **Do**: Use tiny async sleeps (≤ 50ms) only to sequence concurrent tasks
  - **Don’t**: Start uvicorn or bind to real ports in tests
  - **Don’t**: Depend on external services or the Internet
  - **Don’t**: Use long `sleep` to “wait it out”

- **Checklist for any new integration test**
  - [ ] Uses in-process ASGI client (sync or async)
  - [ ] Overrides protocol timeouts to be short
  - [ ] No real sockets, ports, or external calls
  - [ ] Deterministic ordering without long sleeps
  - [ ] Finishes in under 1 second locally and in CI

## Core TDD Workflow

When adding features or fixing bugs, follow this **mandatory workflow**:

### 0. Understand the Problem
- **For bugs**: Identify the root cause, not just symptoms
- **For features**: Ask clarifying questions if requirements are unclear
- **Always**: Understand the "why" before implementing the "how"

> Operational rule: Do not pause to confirm next steps if the plan is clear. Follow `PLAN.md` autonomously. Only ask for guidance if blocked by missing context, ambiguous requirements, or external dependencies that cannot be mocked.

### 1. Red Phase - Write Tests First
- Write test(s) for the expected behavior
- Choose the most appropriate test type:
  - **Unit tests** for individual functions/classes
  - **Integration tests** for component interactions
  - **End-to-end tests** for full user workflows
- **Tests must fail** because the expected behavior doesn't exist yet
- If tests pass immediately, the test is likely insufficient

### 2. Implement Feature/Fix Bug
- Implement the minimum code needed to make tests pass
- Fix the **root cause** of bugs, not just symptoms
- Follow existing code patterns and architecture
- Use type hints and proper error handling

### 3. Green Phase - Verify Tests Pass
- Re-run the new tests - they should now pass
- This confirms the real code implements the expected behavior
- If tests still fail, proceed to step 4

### 4. Debug if Not Green
- **Implementation bug**: Fix the code logic
- **Test bug**: Fix the test expectations
- **Always fix real problems**, not just to make tests pass
- Never write tests that pass by accident

### 5. Regression Testing
- Run **all existing tests** to ensure no regressions
- Fix any broken existing functionality
- Maintain backward compatibility

### 6. Confidence Analysis Report
- **MANDATORY**: Provide a detailed confidence analysis before running the real application
- Assess confidence across multiple axes with specific reasoning
- Include overall confidence score with improvement recommendations
- Only proceed to manual verification after providing this report

### 7. Manual Verification
- Run the real application to reproduce issues or exercise new features
- Verify the feature works as expected in practice
- Test edge cases and error conditions
- **Always prefer durable testing methods** over ad-hoc manual testing

## Test Quality Standards

### Test Structure
```python
def test_feature_behavior():
    """Test that feature does expected thing."""
    # Arrange - Set up test data and conditions
    session_id = "test-session"
    expected_result = "expected value"
    
    # Act - Execute the behavior being tested
    result = function_under_test(session_id)
    
    # Assert - Verify the expected outcome
    assert result == expected_result
```

### Test Naming
- Use descriptive names: `test_session_manager_creates_session_with_valid_id`
- Include the component being tested
- Describe the expected behavior
- Use underscores, not camelCase

### Test Coverage
- Test **happy path** scenarios
- Test **error conditions** and edge cases
- Test **boundary values**
- Test **async behavior** with proper fixtures

### Test Isolation
- Each test should be independent
- Use proper setup/teardown
- Don't rely on test execution order
- Clean up resources after tests

## Code Quality Standards

### Type Hints
```python
async def create_session(session_id: str) -> Session:
    """Create a new session with the given ID."""
    # Implementation here
```

### Error Handling
```python
async def get_session(session_id: str) -> Optional[Session]:
    """Get session by ID, return None if not found."""
    try:
        return self.sessions[session_id]
    except KeyError:
        return None
```

### Async/Await
- Use `async`/`await` for I/O operations
- Use `pytest-asyncio` for async tests
- Handle async errors properly

### Documentation
- Write docstrings for all public functions
- Include parameter types and return types
- Explain complex logic

## Project-Specific Guidelines

### MotiveProxy Architecture
- **Session Manager**: Handles client pairing and session lifecycle
- **Routes**: FastAPI endpoints for OpenAI API compatibility
- **Models**: Pydantic models for request/response validation
- **Tests**: Comprehensive test coverage for all components

### Session Management
- Sessions are identified by `model` parameter (session ID)
- First client connects and sends "ping" message
- Second client connects with real message
- Messages are forwarded bidirectionally

### API Compatibility
- Must maintain OpenAI Chat Completions API compatibility
- Handle all required and optional parameters
- Return proper error responses for invalid requests
- Support concurrent sessions

## 📘 PLAN.md: Source of Truth & Living Roadmap

### Usage Expectations
- **Read First**: Before any task, read `PLAN.md` to select the next item. Re-read it after each change, before commits, and before opening a PR.
- **Follow the Plan**: Treat `PLAN.md` as the authoritative checklist and guidance for architecture, behavior, and acceptance criteria.
- **Derive Tests from PLAN**: Tests should reflect the behavioral requirements and acceptance criteria described in `PLAN.md`.

### Update & Governance Rules
- **Plan Before Code**: When new requirements/bugs/features arrive, add or update `PLAN.md` with scope, acceptance criteria, and test outline **before** implementing.
- **Keep It Current**: Update `PLAN.md` whenever scope changes, when a design decision is made, or when risks are discovered.
- **Checkbox Discipline**: Use emoji checkboxes to track status and check them when items are completed and merged (tests passing).
- **Traceability**: Link checklist items to commits/PRs in parentheses after the item when possible (e.g., `(PR #123)`).
- **No Drift**: If implementation deviates from `PLAN.md`, revise the plan first, then implement.

### Checklist Conventions
- ☐ TODO: Not started
- ⏳ In Progress: Currently being implemented
- ☑ Done: Implemented, tests pass, merged
- ❌ Cancelled/Not Needed

### PR & Review Requirements
- **PR Template** should include:
  - Referenced `PLAN.md` item(s) and milestone
  - Confirmation that `PLAN.md` was updated (checkboxes adjusted, new items added if needed)
  - Summary of added/updated tests derived from the plan
- **Review Gate**: PRs that change behavior must update `PLAN.md`. If not applicable, explicitly state why.

### When Requirements Change
- Add a new item or adjust the existing one in `PLAN.md` with:
  - Updated description, scope, and rationale
  - Behavioral requirements and acceptance criteria
  - Test plan (unit/integration/E2E)
  - Risks/assumptions
- Only after updating the plan do you proceed with the Red → Green cycle.

## Testing Commands

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=motive_proxy

# Run specific test file
pytest tests/test_session_manager.py

# Run specific test
pytest tests/test_session_manager.py::TestSessionManager::test_create_session

# Run with verbose output
pytest -v

# Run with verbose output and no capture (see print statements)
pytest -v -s
```

**⚠️ IMPORTANT: Always use `pytest` directly, NOT `python -m pytest`**
- `pytest` - ✅ Fast, no manual approval needed
- `python -m pytest` - ❌ Slow, requires manual approval, wastes time

### Code Quality
```bash
# Format code
inv format-code

# Run linters
inv lint

# Run all quality checks
inv format-code && inv lint && inv test
```

## Common Patterns

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function behavior."""
    result = await async_function()
    assert result is not None
```

### Testing FastAPI Endpoints
```python
def test_endpoint(client: TestClient):
    """Test API endpoint."""
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    assert "choices" in response.json()
```

### Testing Session Management
```python
def test_session_pairing():
    """Test that clients are properly paired."""
    manager = SessionManager()
    session = manager.create_session("test-session")
    
    # Test session creation
    assert session.session_id == "test-session"
    assert not session.is_ready()
    
    # Test client connection
    mock_client = Mock()
    session.connect_human(mock_client)
    assert session.is_human_connected()
```

## Error Handling Patterns

### Expected Errors
```python
def test_invalid_session_id():
    """Test handling of invalid session ID."""
    manager = SessionManager()
    
    with pytest.raises(ValueError, match="Invalid session ID"):
        manager.create_session("")
```

### Async Error Handling
```python
@pytest.mark.asyncio
async def test_async_error_handling():
    """Test async error handling."""
    with pytest.raises(httpx.ConnectError):
        await client.send_message("invalid-url", "test")
```

## Confidence Analysis Requirements

### Mandatory Confidence Report Format

Before running the real application, **ALWAYS** provide a confidence analysis report with the following structure:

```markdown
## 🎯 Confidence Analysis Report

### Overall Confidence: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)

### Detailed Analysis:

#### 🧪 Test Coverage Confidence: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)
**What**: Extent to which the implementation is covered by tests
**Why**: [Specific reasoning about test quality, coverage, and edge cases]
**Improvement**: [What's needed to reach 5 stars]

#### 🔧 Implementation Quality: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)
**What**: Code quality, architecture adherence, and best practices
**Why**: [Specific reasoning about code structure, error handling, type hints]
**Improvement**: [What's needed to reach 5 stars]

#### 🐛 Bug Fix Confidence: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)
**What**: Confidence that the root cause has been addressed
**Why**: [Specific reasoning about the fix, testing, and edge cases]
**Improvement**: [What's needed to reach 5 stars]

#### 🚀 Feature Completeness: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)
**What**: Extent to which the feature meets all requirements
**Why**: [Specific reasoning about requirement coverage and edge cases]
**Improvement**: [What's needed to reach 5 stars]

#### 🔄 Integration Confidence: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)
**What**: Confidence that changes integrate well with existing code
**Why**: [Specific reasoning about compatibility, dependencies, and side effects]
**Improvement**: [What's needed to reach 5 stars]

#### 📚 Documentation Confidence: ⭐⭐⭐⭐🌟 (X.X/5.0 stars)
**What**: Quality and completeness of code documentation
**Why**: [Specific reasoning about docstrings, comments, and clarity]
**Improvement**: [What's needed to reach 5 stars]

### 🎯 Overall Assessment:
[Detailed explanation of overall confidence level and what would be needed to reach 5 stars across all axes]

### ⭐ Overall Star Rating:
[Overall star rating using the scoring guidelines above]

### ⚠️ Risk Assessment:
[Identify potential risks, edge cases, or areas of concern]

### 🚀 Ready for Manual Testing:
[Yes/No with brief justification]

### ⚠️ **CRITICAL: Confidence Analysis Accuracy**

**NEVER overstate confidence without proper validation:**

#### ❌ **What NOT to Do:**
- **Claim "fully tested"** when only unit/integration tests exist
- **Say "ready for manual testing"** without running the actual E2E scenario
- **Rate confidence highly** based on component tests alone
- **Make definitive statements** about functionality that hasn't been end-to-end validated

#### ✅ **What TO Do Instead:**
- **Be honest about testing scope** (unit vs integration vs E2E)
- **Clearly distinguish** between component validation and full workflow validation
- **Rate confidence appropriately** based on actual testing performed
- **Acknowledge limitations** in testing coverage

#### 🔍 **Confidence Validation Checklist:**
- [ ] **Component tests pass** (unit/integration)
- [ ] **Subprocess orchestration tested** (real processes)
- [ ] **Network communication validated** (actual HTTP/WebSocket)
- [ ] **Complete workflow tested** (full E2E scenario)
- [ ] **Cross-platform validation** (Windows/macOS/Linux)
- [ ] **Error scenarios tested** (failure modes, cleanup)

**Rule: Confidence ratings must reflect the actual scope of testing performed, not just component validation.**

### Confidence Scoring Guidelines

#### ⭐⭐⭐⭐🌟 (5.0 stars) - Excellent
- Comprehensive test coverage including edge cases
- High-quality implementation following all best practices
- Complete feature implementation with proper error handling
- Perfect integration with existing codebase
- Excellent documentation and code clarity
- **Rarely achieved** - indicates exceptional work

#### ⭐⭐⭐⭐⯪ (4.5 stars) - Very Good+
- Excellent test coverage with minor gaps
- High-quality implementation with minimal improvements needed
- Feature complete with excellent error handling
- Very good integration with no side effects
- Very good documentation with minor gaps
- **Target level** for high-quality implementations

#### ⭐⭐⭐⭐☆ (4.0 stars) - Very Good
- Good test coverage with most edge cases covered
- Well-implemented code with minor improvements possible
- Feature mostly complete with good error handling
- Good integration with minimal side effects
- Good documentation with minor gaps
- **Target level** for most implementations

#### ⭐⭐⭐⯪☆ (3.5 stars) - Good+
- Good test coverage with some gaps
- Well-implemented code with room for improvement
- Core feature working well with good error handling
- Good integration with minor concerns
- Good documentation with some gaps
- **Above minimum acceptable level**

#### ⭐⭐⭐☆☆ (3.0 stars) - Good
- Adequate test coverage with some gaps
- Functional implementation with room for improvement
- Core feature working with basic error handling
- Acceptable integration with some concerns
- Basic documentation present
- **Minimum acceptable level**

#### ⭐⭐⯪☆☆ (2.5 stars) - Fair+
- Limited test coverage with significant gaps
- Implementation works but has quality issues
- Partial feature implementation with some functionality
- Integration concerns with some side effects
- Poor documentation with some content
- **Requires improvement before proceeding**

#### ⭐⭐☆☆☆ (2.0 stars) - Fair
- Limited test coverage with significant gaps
- Implementation works but has quality issues
- Partial feature implementation
- Integration concerns or side effects
- Poor or missing documentation
- **Requires improvement before proceeding**

#### ⭐⯪☆☆☆ (1.5 stars) - Poor+
- Minimal test coverage with some gaps
- Implementation has significant issues but partially works
- Feature incomplete with some functionality
- Major integration problems with some working parts
- Minimal documentation
- **Should not proceed to manual testing**

#### ⭐☆☆☆☆ (1.0 stars) - Poor
- Minimal or no test coverage
- Implementation has significant issues
- Feature incomplete or broken
- Major integration problems
- No documentation
- **Should not proceed to manual testing**

### Required Analysis Axes

#### 1. Test Coverage Confidence
- **What**: Extent of test coverage (unit, integration, edge cases)
- **Why**: Reasoning about test quality, coverage gaps, and confidence in test validity
- **Consider**: Happy path, error conditions, boundary values, async behavior

#### 2. Implementation Quality
- **What**: Code quality, architecture adherence, best practices
- **Why**: Reasoning about code structure, error handling, type hints, async patterns
- **Consider**: SOLID principles, error handling, type safety, performance

#### 3. Bug Fix Confidence
- **What**: Confidence that the root cause has been addressed
- **Why**: Reasoning about the fix, testing of the fix, edge cases
- **Consider**: Root cause analysis, fix validation, regression prevention

#### 4. Feature Completeness
- **What**: Extent to which the feature meets all requirements
- **Why**: Reasoning about requirement coverage, edge cases, user scenarios
- **Consider**: All requirements, edge cases, user workflows, error scenarios

#### 5. Integration Confidence
- **What**: Confidence that changes integrate well with existing code
- **Why**: Reasoning about compatibility, dependencies, side effects
- **Consider**: API compatibility, backward compatibility, performance impact

#### 6. Documentation Confidence
- **What**: Quality and completeness of code documentation
- **Why**: Reasoning about docstrings, comments, code clarity
- **Consider**: Function docstrings, type hints, inline comments, README updates

### Confidence Report Examples

#### High Confidence Example
```markdown
## 🎯 Confidence Analysis Report

### Overall Confidence: ⭐⭐⭐⭐ (4.2/5.0 stars)

#### 🧪 Test Coverage Confidence: ⭐⭐⭐⭐ (4.0/5.0 stars)
**What**: Comprehensive unit tests covering happy path and error conditions
**Why**: Tests cover session creation, client pairing, message forwarding, and error scenarios. Missing some edge cases around concurrent access.
**Improvement**: Add tests for race conditions and high-concurrency scenarios.

#### 🔧 Implementation Quality: ⭐⭐⭐⭐ (4.5/5.0 stars)
**What**: Clean, well-structured code following project patterns
**Why**: Proper async/await usage, type hints, error handling, and follows existing architecture.
**Improvement**: Could add more detailed error messages and logging.

### 🎯 Overall Assessment:
Strong implementation with good test coverage. Ready for manual testing with confidence that core functionality works correctly.
```

#### Low Confidence Example
```markdown
## 🎯 Confidence Analysis Report

### Overall Confidence: ⭐⭐ (2.3/5.0 stars)

#### 🧪 Test Coverage Confidence: ⭐⭐ (2.0/5.0 stars)
**What**: Basic tests cover happy path only
**Why**: Missing error condition tests, edge cases, and integration tests. Tests may not catch real-world issues.
**Improvement**: Add comprehensive error handling tests and integration tests.

#### 🔧 Implementation Quality: ⭐⭐ (2.5/5.0 stars)
**What**: Functional but has quality issues
**Why**: Code works but lacks proper error handling, type hints, and follows some anti-patterns.
**Improvement**: Refactor for better error handling, add type hints, improve code structure.

### ⚠️ Risk Assessment:
High risk of runtime errors and integration issues. Implementation needs significant improvement before manual testing.

### 🚀 Ready for Manual Testing: No
```

## 🧪 Durable Testing Guidelines

### ✅ **Always Prefer Durable Testing Methods**

**Never use ad-hoc manual testing** when durable alternatives exist:

#### ❌ **Avoid These Fragile Approaches:**
- **Manual `curl` commands** in chat/terminal
- **Ad-hoc `Invoke-WebRequest` PowerShell commands**
- **Manual Python scripts** run once and forgotten (`python -c "..."`)
- **One-off command-line testing** with temporary scripts
- **Browser-based manual testing** without automation
- **Interactive debugging sessions** that aren't captured in tests
- **Ad-hoc subprocess testing** that isn't repeatable

#### ✅ **Use These Durable Approaches:**
- **pytest tests** for all functionality
- **Integration tests** for API endpoints
- **End-to-end tests** for complete workflows
- **Automated test suites** that run in CI/CD
- **Test fixtures** for consistent test data

### 🎯 **Testing Hierarchy (Best to Worst):**

1. **🏆 Unit Tests** - Test individual functions/classes
2. **🔗 Integration Tests** - Test component interactions
3. **🌐 End-to-End Tests** - Test complete user workflows
4. **📊 Performance Tests** - Test under load/stress
5. **⚠️ Manual Testing** - Only for exploratory testing

### 📋 **When Manual Testing is Acceptable:**
- **Exploratory testing** to understand behavior
- **Debugging** specific issues
- **Demonstration** of functionality
- **Initial development** before writing tests

### 🚫 **When Manual Testing is NOT Acceptable:**
- **Regression testing** (use automated tests)
- **Feature validation** (write proper tests)
- **API endpoint testing** (use pytest + httpx)
- **Performance validation** (use automated benchmarks)
- **Subprocess testing** (use pytest with proper fixtures)
- **Server startup testing** (use pytest with TestClient or httpx.ASGITransport)
- **Cross-platform compatibility** (use pytest with platform-specific fixtures)
- **Debugging production issues** (capture in reproducible tests)

### 💡 **Best Practices:**

#### **For API Testing:**
```python
def test_api_endpoint_integration(client: TestClient):
    """Test API endpoint with real HTTP requests."""
    response = client.post("/v1/chat/completions", json={
        "model": "test-session",
        "messages": [{"role": "user", "content": "Hello"}]
    })
    assert response.status_code == 200
    assert "choices" in response.json()
```

#### **For Server Testing:**
```python
@pytest.mark.asyncio
async def test_server_startup():
    """Test that server can start and respond."""
    from motive_proxy.app import create_app
    app = create_app()
    
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app)
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
```

#### **For Subprocess Testing:**
```python
@pytest.mark.asyncio
async def test_server_subprocess_startup():
    """Test that server can start as subprocess and respond."""
    import subprocess
    import sys
    import time
    
    cmd = [sys.executable, "-m", "motive_proxy.cli", "run", "--host", "localhost", "--port", "8000"]
    
    # Start server subprocess
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    try:
        # Wait for server to start
        await asyncio.sleep(2)
        assert process.poll() is None, "Server should be running"
        
        # Test health endpoint
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            
    finally:
        # Clean up
        process.terminate()
        process.wait()
```

#### **For End-to-End Testing:**
```python
def test_complete_workflow():
    """Test complete user workflow from start to finish."""
    # Test the entire flow, not just individual components
    pass
```

### 🔄 **Test-Driven Development for Server Features:**

1. **🔴 Write integration tests** for new endpoints
2. **🛠️ Implement the endpoint** to make tests pass
3. **🟢 Verify tests pass** with real server
4. **🔄 Add edge case tests** for robustness
5. **📊 Add performance tests** if needed

### ⚠️ **CRITICAL: No Ad-Hoc Testing**

**NEVER use these anti-patterns during development:**

#### ❌ **What NOT to Do:**
```bash
# DON'T: Ad-hoc command testing
python -c "import subprocess; ..."

# DON'T: One-off manual testing
curl http://localhost:8000/health

# DON'T: Temporary debugging scripts
python debug_server.py
```

#### ✅ **What TO Do Instead:**
```python
# DO: Write proper pytest tests
@pytest.mark.asyncio
async def test_server_health_endpoint():
    """Test server health endpoint."""
    # Proper test implementation
    pass

# DO: Use fixtures for reusable test components
@pytest.fixture
async def test_server():
    """Fixture for test server."""
    # Proper fixture implementation
    pass
```

**Rule: If you find yourself typing `python -c "..."` or running manual commands, STOP and write a proper test instead.**

### 🚨 **CRITICAL: E2E Testing Validation**

**ALWAYS validate that E2E functionality actually works end-to-end:**

#### ❌ **What NOT to Do:**
- **Claim E2E is "tested"** when only unit/integration tests exist
- **Use in-process tests** (`TestClient`, `httpx.ASGITransport`) and assume they validate subprocess functionality
- **Skip actual subprocess testing** because "the components work in isolation"
- **Make confident claims** about E2E functionality without running it
- **Overstate confidence** based on component tests alone

#### ✅ **What TO Do Instead:**
- **Test the actual E2E scenario** with real subprocesses and network communication
- **Validate subprocess orchestration** works correctly
- **Test network binding** and port accessibility
- **Run the complete E2E workflow** before claiming it's ready
- **Test with real LLM APIs** to validate actual functionality

#### 🔍 **E2E Testing Checklist:**
- [ ] **In-process tests pass** (unit/integration validation)
- [ ] **Subprocess tests pass** (real process orchestration)
- [ ] **Network communication works** (actual HTTP/WebSocket)
- [ ] **Complete workflow tested** (full E2E scenario)
- [ ] **Cross-platform validation** (Windows/macOS/Linux)
- [ ] **Real LLM integration tested** (actual AI-to-AI conversations)

#### 🧪 **LLM-to-LLM E2E Testing**
**The gold standard for MotiveProxy validation:**
- **Real AI Models**: Use actual LLM APIs (Google Gemini, OpenAI, Anthropic)
- **Multi-turn Conversations**: Test 5-20 turn conversations
- **Performance Validation**: Measure response times and throughput
- **Error Handling**: Test timeout scenarios and network failures
- **Cross-Platform**: Validate on Windows, macOS, and Linux

**Rule: E2E testing is not complete until the actual end-to-end scenario works with real subprocesses, network communication, and real LLM APIs.**

### 🔥 **Windows Firewall Considerations**

**When running E2E tests on Windows, be aware of firewall interactions:**

#### ⚠️ **What to Expect:**
- **Windows Firewall Dialog**: May appear when server binds to network interface
- **User Approval Required**: User must allow the connection for tests to proceed
- **One-time Setup**: Usually only needed once per application

#### ✅ **Best Practices:**
- **Inform users** about potential firewall dialogs in documentation
- **Provide clear instructions** for allowing connections
- **Use consistent ports** to minimize firewall prompts
- **Test firewall scenarios** in CI/CD environments

#### 🔧 **Technical Solutions:**
- **Use localhost/127.0.0.1** to minimize firewall interactions
- **Configure firewall rules** programmatically for automated testing
- **Handle connection errors** gracefully with appropriate user guidance

**Rule: Always inform users about potential firewall interactions in E2E testing scenarios.**

### ⚡ **Performance Optimization Lessons**

**Key learnings from implementing LLM-to-LLM E2E testing:**

#### 🧠 **Context Management**
- **Smart Truncation**: Keep only system prompt + conversation summary + last 3-4 messages
- **Automatic Summarization**: Summarize older conversation history when context gets too long
- **Response Caching**: Cache identical responses to reduce redundant API calls
- **Token Efficiency**: Optimize for specific LLM providers (e.g., Gemini works best with 6-8 context messages)

#### 🔄 **Retry Logic**
- **Exponential Backoff**: Use 2^attempt delays (1s, 2s, 4s) for transient failures
- **Timeout Handling**: Distinguish between network timeouts and LLM processing delays
- **Graceful Degradation**: Provide clear error messages for different failure types

#### 📊 **Performance Monitoring**
- **Real-time Metrics**: Track response times, throughput, and error rates
- **Response Length Limits**: Prevent overly verbose LLM responses (default: 1000-2000 chars)
- **Context Usage Tracking**: Monitor token usage and truncation events

#### 🎯 **LLM Provider Optimization**
- **Google Gemini**: Fast, free credits, works well with shorter contexts
- **OpenAI GPT**: Comprehensive API, good for complex conversations
- **Anthropic Claude**: High-quality responses, good for nuanced discussions
- **Provider Selection**: Choose based on speed, cost, and quality requirements

#### 🔧 **Implementation Patterns**
```python
# Smart context building
def _build_smart_context(self, message: str) -> List:
    context = []
    if self.system_prompt:
        context.append(SystemMessage(content=self.system_prompt))
    if self.conversation_summary:
        context.append(HumanMessage(content=f"[Previous context: {self.conversation_summary}]"))
    context.extend(self.recent_messages[-4:])  # Last 4 messages
    context.append(HumanMessage(content=message))
    return context

# Response caching
cache_key = hash(message + str(self.recent_messages[-2:]))
if cache_key in self.response_cache:
    return self.response_cache[cache_key]

# Retry logic with exponential backoff
for attempt in range(max_retries + 1):
    try:
        response = await self.llm.ainvoke(context)
        break
    except Exception as e:
        if "timeout" in str(e).lower() and attempt < max_retries:
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
            continue
        raise
```

**Rule: Always optimize for the specific LLM provider and use case. Generic optimizations may not work well for all scenarios.**

### 📝 **Documentation Testing:**
- **Always test examples** in documentation
- **Verify code snippets** actually work
- **Update tests** when documentation changes
- **Include test coverage** for all documented features

## Debugging Guidelines

### When Tests Fail
1. **Read the error message carefully**
2. **Check if the test expectation is correct**
3. **Verify the implementation logic**
4. **Use debugger or print statements if needed**
5. **Don't just make tests pass - fix real issues**

### When Features Don't Work
1. **Write a failing test** that reproduces the issue
2. **Use pytest debugging** with `--pdb` flag
3. **Check logs** in test output
4. **Verify test data** and fixtures
5. **Test edge cases** systematically

## Commit Standards

### Commit Messages
```
feat: add session timeout handling

- Add configurable session timeout
- Implement automatic cleanup of expired sessions
- Add tests for timeout behavior

Fixes #123
```

### Pre-commit Checks
- All tests must pass
- Code must be formatted (black, isort)
- Linting must pass (flake8, mypy)
- No regressions in existing functionality

## Anti-Patterns to Avoid

### ❌ Don't Do This
- Write tests after implementing features
- Make tests pass by changing expectations instead of fixing code
- Skip the "Red" phase of TDD
- Ignore failing tests
- Write tests that depend on external state
- Implement features without understanding requirements

### ✅ Do This Instead
- Write tests first, then implement
- Fix real problems, not just test failures
- Always start with failing tests
- Investigate and fix all test failures
- Write isolated, independent tests
- Ask clarifying questions about requirements

## Getting Help

### When Stuck
1. **Re-read the requirements** - Make sure you understand the problem
2. **Check existing tests** - Look for similar patterns
3. **Run the application** - See how it behaves in practice
4. **Ask questions** - Clarify requirements if unclear
5. **Start small** - Implement minimal functionality first

### Resources
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup and practices
- [README.md](README.md) - Project overview and usage
- [PLAN.md](PLAN.md) - Living roadmap and source of truth
- [examples/](examples/) - Usage examples and patterns

## 📝 Documentation and Communication Guidelines

### 🎨 Emoji Usage Standards

**Use emojis strategically** to make documentation and responses more visually scannable and engaging:

#### ✅ **When to Use Emojis:**
- **Section headings** in documentation and responses
- **TDD phase indicators** (🔴 Red, 🟢 Green, 🔄 Refactor)
- **Key workflow steps** and milestones
- **Status indicators** (✅ Complete, ❌ Failed, ⚠️ Warning)
- **Important callouts** and highlights
- **Development workflow phases**

#### ❌ **When NOT to Use Emojis:**
- Every single list item (use sparingly)
- In code comments or technical specifications
- Overly frequently (aim for 1-2 per major section)
- In commit messages (keep professional)

#### 🎯 **Examples of Good Emoji Usage:**

```markdown
## 🚀 Getting Started
### 🔧 Setup Requirements
### 🧪 Testing Your Changes

## 🔴 Red Phase - Write Failing Tests
## 🟢 Green Phase - Make Tests Pass
## 🔄 Refactor Phase - Improve Code

## ✅ Completed Tasks
## ⚠️ Known Issues
## 🎯 Next Steps
```

#### 📋 **TDD Workflow with Emojis:**
```markdown
### 🔍 0. Understand the Problem
### 🔴 1. Red Phase - Write Tests First
### 🛠️ 2. Implement Feature/Fix Bug
### 🟢 3. Green Phase - Verify Tests Pass
### 🐛 4. Debug if Not Green
### 🔄 5. Regression Testing
### 📊 6. Confidence Analysis Report
### 🚀 7. Manual Verification
```

#### 💡 **Communication Best Practices:**
- Use emojis to **draw attention** to important sections
- Make it **easy to scan** and skip over details
- **Balance professionalism** with visual appeal
- Use **consistent emoji choices** for similar concepts
- **Don't overdo it** - quality over quantity

## 🌐 Cross-Platform Development Guidelines

### Windows and macOS/Linux Compatibility

**MotiveProxy MUST support both Windows and macOS/Linux platforms** with consistent behavior across all operating systems.

#### 🔧 **Platform-Specific Considerations:**

##### **Subprocess Handling**
- **Windows**: Use `subprocess.CREATE_NEW_PROCESS_GROUP` for proper process management
- **macOS/Linux**: Standard subprocess handling works correctly
- **Process Termination**: Handle `terminate()` vs `kill()` behavior differences
- **Path Handling**: Use `pathlib.Path` for cross-platform path operations

```python
import sys
import subprocess
from pathlib import Path

# Cross-platform subprocess creation
if sys.platform == "win32":
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
else:
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )

# Cross-platform path handling
config_path = Path("config") / "settings.yaml"  # Works on all platforms
```

##### **File System Operations**
- **Use `pathlib.Path`** instead of `os.path` for all file operations
- **Handle path separators** automatically with `Path` objects
- **Test file permissions** on both platforms when relevant

##### **Network and Port Handling**
- **Use `localhost`** instead of `127.0.0.1` for consistency
- **Handle port binding** differences between platforms
- **Test network timeouts** on both platforms

##### **Environment Variables**
- **Use `os.environ`** for cross-platform environment variable access
- **Handle case sensitivity** differences (Windows vs Unix)
- **Provide platform-specific defaults** when needed

#### 🧪 **Cross-Platform Testing Requirements:**

##### **Test Coverage**
- **Test on both platforms** when possible
- **Use platform-specific test fixtures** when needed
- **Mock platform-specific behavior** in unit tests
- **Document platform differences** in test documentation

##### **CI/CD Considerations**
- **Run tests on multiple platforms** in CI/CD pipeline
- **Use platform-specific build steps** when necessary
- **Handle platform-specific dependencies** in requirements files

#### 📋 **Cross-Platform Checklist:**

For any new feature or bug fix, ensure:

- [ ] **Subprocess operations** work on both Windows and macOS/Linux
- [ ] **File paths** use `pathlib.Path` for cross-platform compatibility
- [ ] **Network operations** use standard libraries that work on all platforms
- [ ] **Environment variables** are accessed in a platform-agnostic way
- [ ] **Process management** handles platform differences correctly
- [ ] **Error handling** accounts for platform-specific error messages
- [ ] **Documentation** mentions any platform-specific requirements or limitations

#### ⚠️ **Common Cross-Platform Pitfalls:**

##### **❌ Avoid These:**
- Hardcoded path separators (`/` or `\`)
- Platform-specific command execution
- Windows-specific registry access
- Unix-specific file permissions
- Platform-specific environment variable names

##### **✅ Use These Instead:**
- `pathlib.Path` for all file operations
- `subprocess` with proper platform handling
- Cross-platform configuration files (YAML, JSON)
- Standard library functions that work everywhere
- Environment variable handling with fallbacks

#### 🔄 **Cross-Platform Development Workflow:**

1. **🔍 Design** with cross-platform compatibility in mind
2. **🧪 Write tests** that work on both platforms
3. **🛠️ Implement** using cross-platform libraries and patterns
4. **✅ Test** on both Windows and macOS/Linux when possible
5. **📚 Document** any platform-specific requirements or limitations

## Summary

**Remember**: TDD is not just about writing tests - it's about **thinking through the problem first**, **designing the interface**, and **ensuring quality**. Every feature should start with a failing test that describes the expected behavior, then implementation that makes it pass.

**Cross-platform compatibility** is essential for MotiveProxy's success. Always consider Windows and macOS/Linux compatibility when implementing features, and test on both platforms when possible.

The goal is **reliable, maintainable code** that works correctly and continues to work as the project evolves across all supported platforms.
