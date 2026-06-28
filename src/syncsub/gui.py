"""Drag-and-drop GUI (primary interaction on Windows).

Drag exactly 1 video + 1 subtitle into the window (order does not matter).
Drag-and-drop from the file manager requires the optional `tkinterdnd2`
package; without it the window falls back to a file-picker button.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import AlassError, SyncError, sync
from .deps import check_all
from .detect import DetectError, classify, list_embedded_subs
from .reveal import reveal

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore

    _DND = True
except Exception:  # pragma: no cover - optional dependency
    _DND = False


class App:
    def __init__(self) -> None:
        if _DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        self.root.title("字幕按内嵌时间轴对齐")
        self.root.geometry("560x420")
        self.files: List[Path] = []

        self._build()

    def _build(self) -> None:
        pad = dict(padx=16, pady=8)

        self.drop = tk.Label(
            self.root,
            text="把 1 个视频 + 1 个字幕拖进来\n（顺序不限）",
            relief="ridge",
            bd=2,
            height=6,
            fg="#444",
        )
        self.drop.pack(fill="x", **pad)

        if _DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)
        else:
            tk.Button(self.root, text="选择文件…", command=self._pick).pack(**pad)

        self.listbox = tk.Listbox(self.root, height=3)
        self.listbox.pack(fill="x", **pad)

        track_frame = tk.Frame(self.root)
        track_frame.pack(fill="x", **pad)
        tk.Label(track_frame, text="内嵌字幕轨：").pack(side="left")
        self.track_var = tk.StringVar()
        self.track_combo = ttk.Combobox(
            track_frame, textvariable=self.track_var, state="disabled", width=40
        )
        self.track_combo.pack(side="left", fill="x", expand=True)

        self.run_btn = tk.Button(
            self.root, text="开始对齐", command=self._run, state="disabled"
        )
        self.run_btn.pack(**pad)

        self.status = tk.Label(self.root, text="", fg="#444", wraplength=520, justify="left")
        self.status.pack(fill="x", **pad)

        self.reveal_btn = tk.Button(
            self.root, text="在文件管理器中显示", command=self._reveal, state="disabled"
        )
        self.reveal_btn.pack(**pad)
        self._last_output: Optional[Path] = None

    # ---- input handling -------------------------------------------------
    def _on_drop(self, event) -> None:
        paths = self._parse_dnd(event.data)
        self._set_files(paths)

    @staticmethod
    def _parse_dnd(data: str) -> List[Path]:
        # tkdnd wraps paths containing spaces in {curly braces}.
        out: List[Path] = []
        token = ""
        in_brace = False
        for ch in data:
            if ch == "{":
                in_brace = True
                token = ""
            elif ch == "}":
                in_brace = False
                out.append(Path(token))
                token = ""
            elif ch == " " and not in_brace:
                if token:
                    out.append(Path(token))
                token = ""
            else:
                token += ch
        if token:
            out.append(Path(token))
        return out

    def _pick(self) -> None:
        selected = filedialog.askopenfilenames(title="选择 1 个视频 + 1 个字幕")
        if selected:
            self._set_files([Path(p) for p in selected])

    def _set_files(self, paths: List[Path]) -> None:
        self.files = paths
        self.listbox.delete(0, tk.END)
        for p in paths:
            self.listbox.insert(tk.END, p.name)
        self._classify()

    def _classify(self) -> None:
        self.track_combo.set("")
        self.track_combo["state"] = "disabled"
        self.run_btn["state"] = "disabled"
        self.reveal_btn["state"] = "disabled"
        self._set_status("", "#444")

        try:
            video, source = classify(self.files)
        except DetectError as e:
            self._set_status(str(e), "#b00")
            return

        self.video = video
        self.source = source
        streams = list_embedded_subs(video)
        if not streams:
            self._set_status("目标视频没有内嵌字幕轨。", "#b00")
            return

        self._streams = streams
        self.track_combo["values"] = [s.label() for s in streams]
        self.track_combo.current(0)
        self.track_combo["state"] = "readonly" if len(streams) > 1 else "disabled"
        self.run_btn["state"] = "normal"
        self._set_status(
            f"视频：{video.name}\n字幕：{source.name}\n共 {len(streams)} 条内嵌轨，"
            + ("请选择后开始。" if len(streams) > 1 else "将使用第 0 条。"),
            "#070",
        )

    # ---- run ------------------------------------------------------------
    def _run(self) -> None:
        sub_index = self.track_combo.current() if self.track_combo["state"] != "disabled" else 0
        self.run_btn["state"] = "disabled"
        self._set_status("对齐中…", "#444")
        threading.Thread(target=self._run_worker, args=(sub_index,), daemon=True).start()

    def _run_worker(self, sub_index: int) -> None:
        try:
            result = sync(self.video, self.source, sub_index=sub_index)
        except AlassError as e:
            self.root.after(0, lambda: self._fail(str(e), e.log_tail))
            return
        except SyncError as e:
            self.root.after(0, lambda: self._fail(str(e), ""))
            return
        self.root.after(0, lambda: self._done(result.output))

    def _done(self, output: Path) -> None:
        self._last_output = output
        self._set_status(f"完成：{output}", "#070")
        self.reveal_btn["state"] = "normal"
        self.run_btn["state"] = "normal"

    def _fail(self, message: str, log_tail: str) -> None:
        self._set_status(message, "#b00")
        self.run_btn["state"] = "normal"
        if log_tail:
            messagebox.showerror("alass 日志（末 30 行）", log_tail)

    def _reveal(self) -> None:
        if self._last_output:
            reveal(self._last_output)

    def _set_status(self, text: str, color: str) -> None:
        self.status.configure(text=text, fg=color)

    def run(self) -> None:
        missing = check_all()
        if missing:
            self._set_status("缺少命令：" + ", ".join(missing), "#b00")
        self.root.mainloop()


def main(argv=None) -> int:
    app = App()
    args = list(argv) if argv is not None else sys.argv[1:]
    if args:
        app._set_files([Path(a) for a in args])
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
