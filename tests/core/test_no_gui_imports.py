"""The core must stay usable without a display (brief: core separate from GUI)."""

from __future__ import annotations

import ast
from pathlib import Path

import multiverse_studio

FORBIDDEN = {"tkinter", "customtkinter", "multiverse_studio.gui"}
PKG = Path(multiverse_studio.__file__).parent


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            if node.level and node.module.startswith("gui"):
                names.add("multiverse_studio.gui")
    return names


def test_core_io_plots_never_import_gui():
    for sub in ("core", "io", "plots"):
        for f in (PKG / sub).rglob("*.py"):
            bad = {
                n for n in _imports(f) if any(n == x or n.startswith(x + ".") for x in FORBIDDEN)
            }
            assert not bad, f"{f.relative_to(PKG)} imports {bad}"


def test_api_imports_cleanly():
    from multiverse_studio.core import api

    assert "build_specs" in api.__all__
