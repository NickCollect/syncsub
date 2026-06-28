"""File classification and embedded subtitle stream enumeration via ffprobe."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from .deps import resolve
from .i18n import t

SUBTITLE_EXTS = {".srt", ".ass", ".ssa", ".sub", ".idx"}


class DetectError(Exception):
    """Raised when inputs cannot be unambiguously classified."""


@dataclass
class SubStream:
    """An embedded subtitle stream. `index` is the relative 0:s:N index."""

    index: int
    language: str = ""
    title: str = ""

    def label(self) -> str:
        parts = [f"#{self.index}"]
        if self.language:
            parts.append(self.language)
        if self.title:
            parts.append(self.title)
        return "  ".join(parts)


def has_video_stream(path: Path) -> bool:
    out = subprocess.run(
        [
            resolve("ffprobe"),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    return out.returncode == 0 and out.stdout.strip() != ""


def is_subtitle(path: Path) -> bool:
    return path.suffix.lower() in SUBTITLE_EXTS


def classify(files: Sequence[Path]) -> tuple[Path, Path]:
    """Return (video, subtitle) from exactly two inputs, order-independent."""
    paths = [Path(f) for f in files]
    if len(paths) != 2:
        raise DetectError(t("need_one_each"))

    subs = [p for p in paths if is_subtitle(p)]
    others = [p for p in paths if not is_subtitle(p)]

    if len(subs) == 2:
        raise DetectError(t("one_sub_only"))
    if len(subs) == 0:
        if all(has_video_stream(p) for p in others):
            raise DetectError(t("one_video_only"))
        raise DetectError(t("need_one_each"))

    source_sub = subs[0]
    video = others[0]
    if not has_video_stream(video):
        if is_subtitle(video):
            raise DetectError(t("need_one_each"))
        raise DetectError(t("not_a_video", name=video.name))
    return video, source_sub


def list_embedded_subs(video: Path) -> List[SubStream]:
    out = subprocess.run(
        [
            resolve("ffprobe"),
            "-v",
            "error",
            "-select_streams",
            "s",
            "-show_entries",
            "stream=index:stream_tags=language,title",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return []
    try:
        data = json.loads(out.stdout or "{}")
    except json.JSONDecodeError:
        return []

    streams = data.get("streams", [])
    result: List[SubStream] = []
    for relative_index, stream in enumerate(streams):
        tags = stream.get("tags", {}) or {}
        result.append(
            SubStream(
                index=relative_index,
                language=str(tags.get("language", "") or ""),
                title=str(tags.get("title", "") or ""),
            )
        )
    return result
