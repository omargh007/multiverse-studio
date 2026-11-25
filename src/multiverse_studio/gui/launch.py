"""Start the Streamlit app on this computer only.

``multiverse-studio`` and ``python -m multiverse_studio`` call :func:`run`, which
starts Streamlit's local server on ``localhost`` (never on the network), turns off
usage statistics, applies the design tokens as Streamlit's light and dark themes,
and opens the browser. Extra command-line options are passed to Streamlit, for
example ``multiverse-studio --server.port 8600``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .theme import streamlit_theme_flags

APP = Path(__file__).with_name("app.py")


def streamlit_args(extra: list[str] | None = None) -> list[str]:
    """The full ``streamlit run`` command line (without the program name)."""
    return [
        "run",
        str(APP),
        "--server.address=localhost",
        "--browser.serverAddress=localhost",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
        "--server.runOnSave=false",
        "--server.maxUploadSize=500",
        "--client.toolbarMode=minimal",
        "--client.showErrorDetails=true",
        *streamlit_theme_flags(),
        *(extra or []),
    ]


def run(extra: list[str] | None = None) -> None:
    from streamlit.web import cli as stcli

    sys.argv = ["streamlit", *streamlit_args(extra if extra is not None else sys.argv[1:])]
    sys.exit(stcli.main())
