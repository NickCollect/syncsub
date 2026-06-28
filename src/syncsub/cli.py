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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="syncsub",
        description="把源字幕对齐到视频的内嵌字幕时间轴。",
    )
    p.add_argument("--version", action="version", version=f"syncsub {__version__}")
    p.add_argument("--list", metavar="VIDEO", help="列出视频的内嵌字幕轨后退出")
    p.add_argument("--sub", type=int, default=0, metavar="N", help="使用第 N 条内嵌字幕轨（默认 0）")
    p.add_argument("args", nargs="*", help="SOURCE_SUB VIDEO [OUTPUT_SUB]")
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
            print("目标视频没有内嵌字幕轨。", file=sys.stderr)
            return 2
        for s in streams:
            print(s.label())
        return 0

    missing = check_all()
    if missing:
        print("缺少命令：" + ", ".join(missing), file=sys.stderr)
        return 3

    if len(ns.args) < 2:
        parser.print_usage(sys.stderr)
        return 64

    source_sub = Path(ns.args[0])
    video = Path(ns.args[1])
    output = Path(ns.args[2]) if len(ns.args) >= 3 else None

    if not source_sub.exists():
        print(f"源字幕不存在：{source_sub}", file=sys.stderr)
        return 2
    if not video.exists():
        print(f"视频不存在：{video}", file=sys.stderr)
        return 2

    try:
        result = sync(video, source_sub, sub_index=ns.sub, output=output)
    except SyncError as e:
        print(str(e), file=sys.stderr)
        tail = getattr(e, "log_tail", "")
        if tail:
            print("--- alass 日志（末 30 行）---", file=sys.stderr)
            print(tail, file=sys.stderr)
        return 1

    print(str(result.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
