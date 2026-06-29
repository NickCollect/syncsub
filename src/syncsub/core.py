"""Orchestration: extract reference track, run alass, produce synced subtitle."""

from __future__ import annotations

import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .deps import resolve
from .detect import has_video_stream, list_embedded_subs
from .i18n import t
from .naming import build_output_path


class SyncError(Exception):
    pass


class ExtractError(SyncError):
    """Failed to extract the embedded reference subtitle."""


class AlassError(SyncError):
    """alass failed; carries the tail of its log."""

    def __init__(self, message: str, log_tail: str = ""):
        super().__init__(message)
        self.log_tail = log_tail


@dataclass
class SyncResult:
    output: Path
    sub_index: int


def extract_reference(video: Path, sub_index: int, dest: Path) -> None:
    out = subprocess.run(
        [
            resolve("ffmpeg"),
            "-y",
            "-v",
            "error",
            "-i",
            str(video),
            "-map",
            f"0:s:{sub_index}",
            str(dest),
        ],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        raise ExtractError(
            t("extract_failed", idx=sub_index) + "\n" + (out.stderr or "").strip()
        )


def run_alass(reference: Path, source_sub: Path, output: Path) -> None:
    out = subprocess.run(
        [resolve("alass"), str(reference), str(source_sub), str(output)],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0 or not output.exists():
        combined = ((out.stdout or "") + "\n" + (out.stderr or "")).strip()
        tail = "\n".join(deque(combined.splitlines(), maxlen=30))
        raise AlassError(t("alass_failed"), tail)


def sync(
    video: Path,
    source_sub: Path,
    sub_index: int = 0,
    output: Optional[Path] = None,
) -> SyncResult:
    """Align `source_sub` to embedded track `sub_index` of `video`."""
    if not has_video_stream(video):
        raise SyncError(t("not_a_video", name=video.name))
    embedded = list_embedded_subs(video)
    if not embedded:
        raise SyncError(t("no_embedded"))
    if sub_index < 0 or sub_index >= len(embedded):
        raise SyncError(t("index_out_of_range", idx=sub_index, total=len(embedded)))

    out_path = output or build_output_path(video, source_sub)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="syncsub_") as tmp:
        reference = Path(tmp) / "reference.srt"
        extract_reference(video, sub_index, reference)
        run_alass(reference, source_sub, out_path)

    return SyncResult(output=out_path, sub_index=sub_index)
