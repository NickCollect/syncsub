"""Tiny runtime i18n: pick zh/en by system locale, look up messages by key.

Override with the SYNCSUB_LANG environment variable ("zh" or "en").
"""

from __future__ import annotations

import json
import locale
import os
import subprocess
import sys


def _norm(value: str) -> str:
    return "zh" if str(value).lower().startswith("zh") else "en"


def _windows_preferred_lang() -> str:
    """'zh' if the Windows user UI language is Chinese, else '' (unknown)."""
    try:
        import ctypes

        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        # Primary language id is the low 10 bits; 0x04 == LANG_CHINESE.
        if (langid & 0x3FF) == 0x04:
            return "zh"
        return "en"
    except Exception:
        return ""


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

    # On Windows (especially the frozen app) POSIX locale env is usually unset
    # and locale.getdefaultlocale() is unreliable, so ask the OS directly.
    if sys.platform.startswith("win"):
        win = _windows_preferred_lang()
        if win:
            return win

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

# The language `t()` actually renders. Starts at the auto-detected default and
# can be overridden at runtime (e.g. by the GUI toggle) via set_lang().
_current_lang = LANG


def set_lang(lang: str) -> None:
    global _current_lang
    _current_lang = _norm(lang)


def get_lang() -> str:
    return _current_lang


def has_env_override() -> bool:
    return bool(os.environ.get("SYNCSUB_LANG", ""))


def _config_path() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
    return os.path.join(base, "syncsub", "config.json")


def load_saved_lang() -> str:
    """Return a normalized saved language, or '' if none/unreadable."""
    try:
        with open(_config_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return ""
    lang = data.get("lang", "") if isinstance(data, dict) else ""
    return _norm(lang) if lang else ""


def save_lang(lang: str) -> None:
    path = _config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"lang": _norm(lang)}, fh)
    except Exception:
        pass


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
    "gui_tagline": {
        "zh": "把字幕对齐到视频内嵌字幕的时间轴",
        "en": "Align a subtitle to the video's embedded subtitle timeline",
    },
    "gui_step1": {
        "zh": "① 把 1 个视频 + 1 个字幕拖入下方区域（顺序不限）",
        "en": "① Add 1 video + 1 subtitle below (order does not matter)",
    },
    "gui_drop_label": {
        "zh": "把 1 个视频 + 1 个字幕拖进来\n（顺序不限）",
        "en": "Drag 1 video + 1 subtitle here\n(order does not matter)",
    },
    "gui_pick_btn": {"zh": "选择文件…", "en": "Choose files…"},
    "gui_track_label": {"zh": "内嵌字幕轨：", "en": "Embedded track:"},
    "gui_choose_prompt": {
        "zh": "② 👉 请选择参考字幕轨：",
        "en": "② 👉 Choose the reference subtitle track:",
    },
    "gui_auto_track": {
        "zh": "✓ 已自动使用视频的内嵌字幕轨",
        "en": "✓ Using the video's embedded track automatically",
    },
    "gui_step3_btn": {"zh": "③ 开始对齐", "en": "③ Align"},
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
    text = entry.get(_current_lang) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
