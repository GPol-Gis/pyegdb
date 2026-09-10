from collections.abc import Iterator

import pytest

import pyegdb.layout


@pytest.fixture(autouse=True)
def reset_egdb_state() -> Iterator[None]:
    """Reset EGDB module state before each test."""
    pyegdb.layout.debug_reset()
    yield
