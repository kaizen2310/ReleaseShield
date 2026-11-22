"""
conftest.py – shared pytest configuration for ReleaseShield test suite.
Provides event loop fixture for pytest-asyncio strict mode.
"""
import pytest


@pytest.fixture(scope="function")
def event_loop_policy():
    """Use default event loop policy for all async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
