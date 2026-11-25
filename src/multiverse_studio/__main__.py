"""Entry point: ``python -m multiverse_studio`` or ``multiverse-studio`` starts the app."""

from __future__ import annotations


def main() -> None:
    from multiverse_studio.gui.launch import run

    run()


if __name__ == "__main__":
    main()
