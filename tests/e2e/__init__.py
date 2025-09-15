"""E2E Test Suite for MotiveProxy.

This directory contains End-to-End tests that use real subprocesses and network connections.
These tests are separate from the main pytest suite and should be run using the 
motive-proxy-e2e command-line tool.

Usage:
    motive-proxy-e2e --scenario basic_handshake --turns 3
    motive-proxy-e2e --scenario concurrent_clients --turns 5 --concurrent 2
"""
