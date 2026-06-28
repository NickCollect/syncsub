"""Reveal a file in the OS file manager (Finder / Explorer)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def reveal(path: Path) -> None:
    path = Path(path)
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)], check=False)
        elif sys.platform.startswith("win"):
            subprocess.run(["explorer", f"/select,{path}"], check=False)
        else:
            subprocess.run(["xdg-open", str(path.parent)], check=False)
    except Exception:
        pass
