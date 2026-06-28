"""macOS Finder Quick Action wrapper.

Receives two file paths from Finder, auto-detects video/subtitle, prompts to
pick an embedded track when several exist, runs the sync, and reveals the
output in Finder. All user-facing messages go through AppleScript dialogs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .core import AlassError, SyncError, sync
from .deps import check_all
from .detect import DetectError, classify, list_embedded_subs
from .i18n import t
from .reveal import reveal


def _dialog(message: str, title: Optional[str] = None) -> None:
    title = title or t("app_title")
    ok = t("ok_button")
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display dialog {_q(message)} with title {_q(title)} '
            f'buttons {{{_q(ok)}}} default button {_q(ok)} with icon caution',
        ],
        check=False,
    )


def _choose(prompt: str, items: List[str]) -> Optional[int]:
    quoted = ", ".join(_q(i) for i in items)
    script = (
        f'set theList to {{{quoted}}}\n'
        f'set theChoice to choose from list theList with prompt {_q(prompt)} '
        f'with title {_q(t("choose_title"))}\n'
        f'if theChoice is false then return "__CANCEL__"\n'
        f'return item 1 of theChoice'
    )
    out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    chosen = out.stdout.strip()
    if not chosen or chosen == "__CANCEL__":
        return None
    try:
        return items.index(chosen)
    except ValueError:
        return None


def _q(text: str) -> str:
    """Quote a Python string as an AppleScript string literal."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main(argv=None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    paths = [Path(a) for a in args]

    missing = check_all()
    if missing:
        _dialog(t("missing_cmds", tools="、".join(missing)) + "\n\n" + t("mac_install_hint"))
        return 3

    try:
        video, source = classify(paths)
    except DetectError as e:
        _dialog(str(e))
        return 2

    streams = list_embedded_subs(video)
    if not streams:
        _dialog(t("no_embedded"))
        return 2

    if len(streams) == 1:
        sub_index = 0
    else:
        labels = [s.label() for s in streams]
        choice = _choose(t("choose_prompt"), labels)
        if choice is None:
            return 0
        sub_index = choice

    try:
        result = sync(video, source, sub_index=sub_index)
    except AlassError as e:
        _dialog(str(e) + "\n\n" + t("alass_log_header") + "\n" + e.log_tail)
        return 1
    except SyncError as e:
        _dialog(str(e))
        return 1

    reveal(result.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
