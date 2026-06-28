"""Output filename construction and language-tag extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def extract_lang_tag(source_sub: Path) -> Optional[str]:
    """Last dot-separated segment of the source subtitle stem, or None."""
    stem = source_sub.name[: -len(source_sub.suffix)] if source_sub.suffix else source_sub.name
    if "." in stem:
        tag = stem.rsplit(".", 1)[-1].strip()
        return tag or None
    return None


def build_output_path(video: Path, source_sub: Path) -> Path:
    """Output path = video stem + [.lang] + .synced + source ext, in the source dir.

    Falls back to `<video_stem>.synced.<ext>` when no language tag is present.
    """
    video_stem = video.name[: -len(video.suffix)] if video.suffix else video.name
    src_ext = source_sub.suffix.lstrip(".")
    lang = extract_lang_tag(source_sub)

    if lang:
        filename = f"{video_stem}.{lang}.synced.{src_ext}"
    else:
        filename = f"{video_stem}.synced.{src_ext}"

    return source_sub.parent / filename
