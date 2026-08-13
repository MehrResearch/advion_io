"""Location of the example ``.datx`` acquisition used by the test-suite.

The bundled file lives in ``tests/data/example.datx``.  Point the
``ADVION_EXAMPLE_DATX`` environment variable at another acquisition to
run the same checks against your own data (a few assertions are
specific to the bundled file and will then need adjusting).

Tests that need the example skip automatically when it is absent, so
the suite still passes on a checkout without it.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

EXAMPLE_DATX = Path(
    os.environ.get("ADVION_EXAMPLE_DATX", REPO_ROOT / "tests" / "data" / "example.datx")
)

SKIP_REASON = f"Example acquisition not present at {EXAMPLE_DATX}"

#: Decorator for tests that read the example file directly (rather than
#: through a fixture that already guards on its presence).
requires_example = pytest.mark.skipif(not EXAMPLE_DATX.exists(), reason=SKIP_REASON)
