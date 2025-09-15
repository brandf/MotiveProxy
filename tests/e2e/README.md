# E2E Test Suite

This directory contains End-to-End (E2E) tests for MotiveProxy that use real subprocesses and network connections.

## ⚠️ Important: E2E Tests Are Separate

**E2E tests are NOT part of the main pytest suite.** They are designed to be run separately using the `motive-proxy-e2e` command-line tool.

## Running E2E Tests

### Using the E2E CLI Tool (Recommended)
```bash
# Run a specific scenario
motive-proxy-e2e --scenario basic_handshake --turns 3

# Run concurrent clients test
motive-proxy-e2e --scenario concurrent_clients --turns 5 --concurrent 2

# Run all scenarios
motive-proxy-e2e --scenario all
```

### Using pytest (Advanced)
```bash
# Run only E2E tests (slow!)
pytest tests/e2e/ -m e2e

# Run E2E tests with verbose output
pytest tests/e2e/ -m e2e -v

# Skip E2E tests (default behavior)
pytest -m "not e2e"
```

## Test Scenarios

### `basic_handshake`
Tests basic client-server handshake and message exchange.

### `concurrent_clients`
Tests multiple clients connecting simultaneously to the same session.

### `streaming`
Tests streaming response functionality.

### `error_handling`
Tests error handling and recovery scenarios.

## Performance Expectations

- **Individual E2E tests**: 30-90 seconds each
- **Total E2E suite**: 5-10 minutes
- **Network timeouts**: 30-45 seconds per test
- **Cleanup**: Automatic subprocess termination

## Architecture

E2E tests use the following components:

1. **`motive-proxy-e2e` CLI**: Main orchestration tool
2. **`test_client_runner.py`**: Standalone test client processes
3. **`scenarios.py`**: Predefined test scenarios
4. **`log_collector.py`**: Comprehensive log gathering

## Troubleshooting

### Common Issues

1. **Port conflicts**: E2E tests use ports 8000-8010
2. **Subprocess cleanup**: Tests automatically terminate processes
3. **Network timeouts**: Increase `--timeout` parameter if needed
4. **Windows Firewall**: May need to allow Python through firewall

### Debug Mode

```bash
# Run with debug logging
motive-proxy-e2e --scenario basic_handshake --log-level debug

# Check logs in /logs/ directory
ls logs/motive-proxy/
ls logs/test-clients/
```

## Integration with CI/CD

E2E tests should be run:
- **After** all unit/integration tests pass
- **Separately** from the main test suite
- **With longer timeouts** in CI environments
- **Only on** main branch or release candidates
