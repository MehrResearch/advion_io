"""Console entry points: launch the bundled marimo MS dashboard.

The notebook itself lives at the repository root (``Analysis.py``) and is
force-included in the wheel next to this module, so the same file serves both
``uvx marimo edit --sandbox Analysis.py`` in a checkout and
``uvx --from git+... ms-dashboard`` from an install.
"""

import sys
from pathlib import Path

NOTEBOOK_NAME = "Analysis.py"


def _notebook_path() -> Path:
    """Locate the dashboard notebook, installed copy first, checkout second."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / NOTEBOOK_NAME,  # wheel: force-included beside this module
        here.parent.parent / NOTEBOOK_NAME,  # checkout: src/advion_io/ -> root
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"could not find {NOTEBOOK_NAME}; looked in "
        + ", ".join(str(candidate.parent) for candidate in candidates)
    )


def _launch(command: str) -> int:
    """Invoke ``marimo <command> --sandbox <notebook>``, forwarding extra args.

    ``--sandbox`` runs the notebook in a venv built from its inline script
    metadata (PEP 723); passing it explicitly also skips marimo's confirmation
    prompt. Remaining command-line arguments go straight to marimo, e.g.
    ``--port 2718`` or ``--headless``.
    """
    from marimo._cli.cli import main as marimo_main

    sys.argv = ["marimo", command, "--sandbox", str(_notebook_path()), *sys.argv[1:]]
    return marimo_main()


def main() -> int:
    """Run the dashboard as an app (``marimo run``)."""
    return _launch("run")


def edit() -> int:
    """Open the dashboard in the marimo editor (``marimo edit``)."""
    return _launch("edit")


if __name__ == "__main__":
    raise SystemExit(main())
