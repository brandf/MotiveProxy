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

## Sandboxed Integration Tests (Must Read)

Integration tests MUST be fast, deterministic, and completely isolated from external systems. The goals are: no real network, no real services, no long sleeps, and predictable outcomes in CI.

- **Why this matters**
  - **Speed**: Slow tests block iteration and mask real regressions
  - **Determinism**: Flaky tests erode trust and waste time
  - **Isolation**: CI must never depend on real services or ports

- **Hard rules for sandboxed integration tests**
  - **Use in-process ASGI clients**: Test via FastAPI/Starlette without starting a real server
  - **Never make real network calls**: No sockets, ports, or external services
  - **Short timeouts in tests**: Override protocol timeouts to ≤ 200ms so unpaired requests return quickly
  - **No long sleeps**: Replace `time.sleep` with tiny async delays just to yield (e.g., `await asyncio.sleep(0.01)`) when sequencing is needed
  - **Deterministic ordering**: Use controlled scheduling instead of timing-based assumptions

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
inv test

# Run with coverage
inv test-cov

# Run specific test file
pytest tests/test_session_manager.py

# Run specific test
pytest tests/test_session_manager.py::TestSessionManager::test_create_session
```

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

### Overall Confidence: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)

### Detailed Analysis:

#### 🧪 Test Coverage Confidence: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)
**What**: Extent to which the implementation is covered by tests
**Why**: [Specific reasoning about test quality, coverage, and edge cases]
**Improvement**: [What's needed to reach 5 stars]

#### 🔧 Implementation Quality: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)
**What**: Code quality, architecture adherence, and best practices
**Why**: [Specific reasoning about code structure, error handling, type hints]
**Improvement**: [What's needed to reach 5 stars]

#### 🐛 Bug Fix Confidence: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)
**What**: Confidence that the root cause has been addressed
**Why**: [Specific reasoning about the fix, testing, and edge cases]
**Improvement**: [What's needed to reach 5 stars]

#### 🚀 Feature Completeness: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)
**What**: Extent to which the feature meets all requirements
**Why**: [Specific reasoning about requirement coverage and edge cases]
**Improvement**: [What's needed to reach 5 stars]

#### 🔄 Integration Confidence: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)
**What**: Confidence that changes integrate well with existing code
**Why**: [Specific reasoning about compatibility, dependencies, and side effects]
**Improvement**: [What's needed to reach 5 stars]

#### 📚 Documentation Confidence: ⭐⭐⭐⭐⭐ (X.X/5.0 stars)
**What**: Quality and completeness of code documentation
**Why**: [Specific reasoning about docstrings, comments, and clarity]
**Improvement**: [What's needed to reach 5 stars]

### 🎯 Overall Assessment:
[Detailed explanation of overall confidence level and what would be needed to reach 5 stars across all axes]

### ⚠️ Risk Assessment:
[Identify potential risks, edge cases, or areas of concern]

### 🚀 Ready for Manual Testing:
[Yes/No with brief justification]
```

### Confidence Scoring Guidelines

#### ⭐⭐⭐⭐⭐ (5.0 stars) - Excellent
- Comprehensive test coverage including edge cases
- High-quality implementation following all best practices
- Complete feature implementation with proper error handling
- Perfect integration with existing codebase
- Excellent documentation and code clarity
- **Rarely achieved** - indicates exceptional work

#### ⭐⭐⭐⭐ (4.0-4.5 stars) - Very Good
- Good test coverage with most edge cases covered
- Well-implemented code with minor improvements possible
- Feature mostly complete with good error handling
- Good integration with minimal side effects
- Good documentation with minor gaps
- **Target level** for most implementations

#### ⭐⭐⭐ (3.0-3.5 stars) - Good
- Adequate test coverage with some gaps
- Functional implementation with room for improvement
- Core feature working with basic error handling
- Acceptable integration with some concerns
- Basic documentation present
- **Minimum acceptable level**

#### ⭐⭐ (2.0-2.5 stars) - Fair
- Limited test coverage with significant gaps
- Implementation works but has quality issues
- Partial feature implementation
- Integration concerns or side effects
- Poor or missing documentation
- **Requires improvement before proceeding**

#### ⭐ (1.0-1.5 stars) - Poor
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
- Manual `curl` commands in chat/terminal
- Ad-hoc `Invoke-WebRequest` PowerShell commands
- Manual Python scripts run once and forgotten
- Browser-based manual testing without automation
- One-off command-line testing

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

## Summary

**Remember**: TDD is not just about writing tests - it's about **thinking through the problem first**, **designing the interface**, and **ensuring quality**. Every feature should start with a failing test that describes the expected behavior, then implementation that makes it pass.

The goal is **reliable, maintainable code** that works correctly and continues to work as the project evolves.
