"""Tiny runtime i18n: pick zh/en by system locale, look up messages by key.

Override with the SYNCSUB_LANG environment variable ("zh" or "en").
"""

from __future__ import annotations

import locale
import os
import subprocess
import sys


def _norm(value: str) -> str:
    return "zh" if str(value).lower().startswith("zh") else "en"


def _macos_preferred_lang() -> str:
    """First entry of macOS AppleLanguages, e.g. 'zh-Hans-CN'. Empty if unknown."""
    try:
        out = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return ""
    if out.returncode != 0:
        return ""
    for line in out.stdout.splitlines():
        token = line.strip().strip(",").strip('"')
        if token and token not in ("(", ")"):
            return token
    return ""


def _detect_lang() -> str:
    override = os.environ.get("SYNCSUB_LANG", "")
    if override:
        return _norm(override)

    # On macOS the user's real UI language lives in AppleLanguages, not in a
    # terminal's LANG (which is often a generic C.UTF-8). Prefer it.
    if sys.platform == "darwin":
        mac = _macos_preferred_lang()
        if mac:
            return _norm(mac)

    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(var)
        if value:
            return _norm(value)
    loc = ""
    try:
        loc = locale.getlocale()[0] or ""
    except Exception:
        loc = ""
    if not loc:
        try:
            loc = locale.getdefaultlocale()[0] or ""  # noqa: DEP008 (fallback)
        except Exception:
            loc = ""
    return _norm(loc)


LANG = _detect_lang()

MESSAGES = {
    # ---- detection ----
    "need_one_each": {
        "zh": "请同时选中 1 个视频文件和 1 个字幕文件。",
        "en": "Please select exactly 1 video file and 1 subtitle file.",
    },
    "one_sub_only": {
        "zh": "只选 1 个源字幕。",
        "en": "Please select only 1 source subtitle.",
    },
    "one_video_only": {
        "zh": "只选 1 个目标视频。",
        "en": "Please select only 1 target video.",
    },
    "not_a_video": {
        "zh": "无法识别视频文件：{name}",
        "en": "Not a recognizable video file: {name}",
    },
    # ---- streams / sync ----
    "no_embedded": {
        "zh": "目标视频没有内嵌字幕轨。",
        "en": "The target video has no embedded subtitle track.",
    },
    "index_out_of_range": {
        "zh": "内嵌字幕轨编号越界：#{idx}（共 {total} 条）。",
        "en": "Embedded track index out of range: #{idx} (of {total}).",
    },
    "extract_failed": {
        "zh": "抽取内嵌字幕轨 #{idx} 失败，请尝试选择另一条字幕轨。",
        "en": "Failed to extract embedded subtitle track #{idx}; try another track.",
    },
    "alass_failed": {
        "zh": "字幕同步失败（alass）。",
        "en": "Subtitle sync failed (alass).",
    },
    "alass_log_header": {
        "zh": "--- alass 日志（末 30 行）---",
        "en": "--- alass log (last 30 lines) ---",
    },
    # ---- dependencies ----
    "missing_dep": {
        "zh": "缺少命令：{tool}。{hint}",
        "en": "Missing command: {tool}. {hint}",
    },
    "missing_cmds": {
        "zh": "缺少命令：{tools}",
        "en": "Missing command(s): {tools}",
    },
    "hint_ffmpeg": {
        "zh": "macOS: brew install ffmpeg  |  Windows: 运行 install.ps1 自动下载",
        "en": "macOS: brew install ffmpeg  |  Windows: run install.ps1 to auto-download",
    },
    "hint_alass": {
        "zh": "macOS: brew install alass  |  Windows: 运行 install.ps1 自动下载",
        "en": "macOS: brew install alass  |  Windows: run install.ps1 to auto-download",
    },
    "mac_install_hint": {
        "zh": "请先安装：brew install ffmpeg alass",
        "en": "Install first: brew install ffmpeg alass",
    },
    # ---- cli ----
    "cli_desc": {
        "zh": "把源字幕对齐到视频的内嵌字幕时间轴。",
        "en": "Align a source subtitle to a video's embedded subtitle timeline.",
    },
    "cli_list_help": {
        "zh": "列出视频的内嵌字幕轨后退出",
        "en": "List the video's embedded subtitle tracks and exit",
    },
    "cli_sub_help": {
        "zh": "使用第 N 条内嵌字幕轨（默认 0）",
        "en": "Use embedded subtitle track N (default 0)",
    },
    "cli_args_help": {
        "zh": "SOURCE_SUB VIDEO [OUTPUT_SUB]",
        "en": "SOURCE_SUB VIDEO [OUTPUT_SUB]",
    },
    "source_missing": {
        "zh": "源字幕不存在：{path}",
        "en": "Source subtitle not found: {path}",
    },
    "video_missing": {
        "zh": "视频不存在：{path}",
        "en": "Video not found: {path}",
    },
    "too_many_args": {
        "zh": "参数过多，最多 3 个：SOURCE_SUB VIDEO [OUTPUT_SUB]",
        "en": "Too many arguments; at most 3: SOURCE_SUB VIDEO [OUTPUT_SUB]",
    },
    # ---- shared title ----
    "app_title": {
        "zh": "字幕按内嵌时间轴对齐",
        "en": "Sync Subtitle to Embedded Timeline",
    },
    # ---- track chooser ----
    "choose_title": {
        "zh": "选择内嵌字幕轨",
        "en": "Choose embedded subtitle track",
    },
    "choose_prompt": {
        "zh": "该视频有多条内嵌字幕轨，请选择参考时间轴：",
        "en": "This video has several embedded subtitle tracks; pick the reference:",
    },
    "ok_button": {"zh": "好", "en": "OK"},
    # ---- gui ----
    "gui_drop_label": {
        "zh": "把 1 个视频 + 1 个字幕拖进来\n（顺序不限）",
        "en": "Drag 1 video + 1 subtitle here\n(order does not matter)",
    },
    "gui_pick_btn": {"zh": "选择文件…", "en": "Choose files…"},
    "gui_track_label": {"zh": "内嵌字幕轨：", "en": "Embedded track:"},
    "gui_run_btn": {"zh": "开始对齐", "en": "Align"},
    "gui_reveal_btn": {"zh": "在文件管理器中显示", "en": "Show in file manager"},
    "gui_pick_title": {
        "zh": "选择 1 个视频 + 1 个字幕",
        "en": "Select 1 video + 1 subtitle",
    },
    "gui_summary": {
        "zh": "视频：{video}\n字幕：{sub}\n共 {count} 条内嵌轨，{tail}",
        "en": "Video: {video}\nSubtitle: {sub}\n{count} embedded track(s). {tail}",
    },
    "gui_need_choose": {"zh": "请选择后开始。", "en": "Choose one, then Align."},
    "gui_use_first": {"zh": "将使用第 0 条。", "en": "Track #0 will be used."},
    "gui_aligning": {"zh": "对齐中…", "en": "Aligning…"},
    "gui_done": {"zh": "完成：{path}", "en": "Done: {path}"},
}


def t(key: str, **kwargs) -> str:
    entry = MESSAGES.get(key, {})
    text = entry.get(LANG) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
