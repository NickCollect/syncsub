"""Command-line entry point.

Usage:
    syncsub SOURCE_SUB VIDEO [OUTPUT_SUB]
    syncsub --list VIDEO
    syncsub --sub N SOURCE_SUB VIDEO [OUTPUT_SUB]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import SyncError, sync
from .deps import MissingDependency, check_all
from .detect import list_embedded_subs
from .i18n import t


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="syncsub", description=t("cli_desc"))
    p.add_argument("--version", action="version", version=f"syncsub {__version__}")
    p.add_argument("--list", metavar="VIDEO", help=t("cli_list_help"))
    p.add_argument("--sub", type=int, default=0, metavar="N", help=t("cli_sub_help"))
    p.add_argument("args", nargs="*", help=t("cli_args_help"))
    return p


def main(argv=None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    if ns.list:
        try:
            streams = list_embedded_subs(Path(ns.list))
        except MissingDependency as e:
            print(str(e), file=sys.stderr)
            return 3
        if not streams:
            print(t("no_embedded"), file=sys.stderr)
            return 2
        for s in streams:
            print(s.label())
        return 0

    missing = check_all()
    if missing:
        print(t("missing_cmds", tools=", ".join(missing)), file=sys.stderr)
        return 3

    if len(ns.args) < 2:
        parser.print_usage(sys.stderr)
        return 64

    source_sub = Path(ns.args[0])
    video = Path(ns.args[1])
    output = Path(ns.args[2]) if len(ns.args) >= 3 else None

    if not source_sub.exists():
        print(t("source_missing", path=source_sub), file=sys.stderr)
        return 2
    if not video.exists():
        print(t("video_missing", path=video), file=sys.stderr)
        return 2

    try:
        result = sync(video, source_sub, sub_index=ns.sub, output=output)
    except SyncError as e:
        print(str(e), file=sys.stderr)
        tail = getattr(e, "log_tail", "")
        if tail:
            print(t("alass_log_header"), file=sys.stderr)
            print(tail, file=sys.stderr)
        return 1

    print(str(result.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
