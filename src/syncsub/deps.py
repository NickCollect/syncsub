"""External command resolution and presence checks."""

from __future__ import annotations

import shutil
from typing import Dict, List

# Candidate executable names per logical tool, in preference order.
_CANDIDATES: Dict[str, List[str]] = {
    "ffmpeg": ["ffmpeg"],
    "ffprobe": ["ffprobe"],
    "alass": ["alass-cli", "alass"],
}

_INSTALL_HINT = {
    "ffmpeg": "macOS: brew install ffmpeg  |  Windows: 运行 install.ps1 自动下载",
    "ffprobe": "macOS: brew install ffmpeg  |  Windows: 运行 install.ps1 自动下载",
    "alass": "macOS: brew install alass  |  Windows: 运行 install.ps1 自动下载",
}


class MissingDependency(Exception):
    def __init__(self, tool: str):
        self.tool = tool
        hint = _INSTALL_HINT.get(tool, "")
        super().__init__(f"缺少命令：{tool}。{hint}".rstrip())


def resolve(tool: str) -> str:
    """Return the absolute path of an external tool, or raise MissingDependency."""
    for name in _CANDIDATES.get(tool, [tool]):
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
