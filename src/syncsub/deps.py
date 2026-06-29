"""External command resolution and presence checks."""

from __future__ import annotations

import os
import shutil
import sys
from typing import Dict, List

from .i18n import t

# Candidate executable names per logical tool, in preference order.
_CANDIDATES: Dict[str, List[str]] = {
    "ffmpeg": ["ffmpeg"],
    "ffprobe": ["ffprobe"],
    "alass": ["alass-cli", "alass"],
}

_HINT_KEY = {
    "ffmpeg": "hint_ffmpeg",
    "ffprobe": "hint_ffmpeg",
    "alass": "hint_alass",
}


class MissingDependency(Exception):
    def __init__(self, tool: str):
        self.tool = tool
        hint = t(_HINT_KEY.get(tool, "hint_ffmpeg"))
        super().__init__(t("missing_dep", tool=tool, hint=hint).rstrip())


def _bundled_dirs() -> List[str]:
    """Directories to search first when running as a frozen (PyInstaller) app."""
    dirs: List[str] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            dirs.append(meipass)
        dirs.append(os.path.dirname(sys.executable))
    return dirs


def resolve(tool: str) -> str:
    """Return the absolute path of an external tool, or raise MissingDependency.

    When frozen, bundled binaries shipped next to the executable take
    precedence over whatever happens to be on PATH.
    """
    for name in _CANDIDATES.get(tool, [tool]):
        for directory in _bundled_dirs():
            for ext in ("", ".exe"):
                candidate = os.path.join(directory, name + ext)
                if os.path.isfile(candidate):
                    return candidate
        found = shutil.which(name)
        if found:
            return found
    raise MissingDependency(tool)


def check_all() -> List[str]:
    """Return the list of missing logical tools (empty if all present)."""
    missing = []
    for tool in _CANDIDATES:
        try:
            resolve(tool)
        except MissingDependency:
            missing.append(tool)
    return missing
