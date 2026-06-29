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
from .deps import MissingDependency, check_all
from .detect import DetectError, classify, is_subtitle, list_embedded_subs
from .i18n import (
    get_lang,
    has_env_override,
    load_saved_lang,
    save_lang,
    set_lang,
    t,
)
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
        self.root.title(t("app_title"))
        self.root.geometry("560x500")
        self.files: List[Path] = []

        self._build()

    def _build(self) -> None:
        pad = dict(padx=16, pady=6)

        # Top bar: one-line description (left) + language toggle (right).
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill="x", padx=16, pady=(10, 0))
        self._lang_btn = tk.Button(
            top_bar, text=self._lang_btn_text(), command=self._toggle_lang
        )
        self._lang_btn.pack(side="right")
        self._tagline = tk.Label(top_bar, text=t("gui_tagline"), fg="#666", anchor="w")
        self._tagline.pack(side="left", fill="x", expand=True)

        # Step 1: add files.
        self._step1 = tk.Label(
            self.root, text=t("gui_step1"), fg="#222", anchor="w",
            font=("", 11, "bold"),
        )
        self._step1.pack(fill="x", padx=16, pady=(10, 0))

        self.drop = tk.Label(
            self.root,
            text=t("gui_drop_label"),
            relief="ridge",
            bd=2,
            height=5,
            fg="#444",
        )
        self.drop.pack(fill="x", **pad)

        self._pick_btn: Optional[tk.Button] = None
        if _DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)
        else:
            self._pick_btn = tk.Button(self.root, text=t("gui_pick_btn"), command=self._pick)
            self._pick_btn.pack(pady=(0, 4))

        self.listbox = tk.Listbox(self.root, height=2)
        self.listbox.pack(fill="x", **pad)

        # Step 2: track chooser — only revealed when there are multiple tracks.
        # When a video has a single track, a tiny note is shown instead.
        self.step2_frame = tk.Frame(self.root)
        self.step2_frame.pack(fill="x", **pad)
        self._track_prompt = tk.Label(
            self.step2_frame, text=t("gui_choose_prompt"), fg="#b3005e",
            font=("", 11, "bold"), anchor="w",
        )
        self.track_var = tk.StringVar()
        self.track_combo = ttk.Combobox(
            self.step2_frame, textvariable=self.track_var, state="readonly"
        )
        self._auto_note = tk.Label(self.step2_frame, text=t("gui_auto_track"), fg="#888", anchor="w")

        # Step 3: prominent Align button.
        self.run_btn = tk.Button(
            self.root, text=t("gui_step3_btn"), command=self._run, state="disabled",
            font=("", 13, "bold"), height=2,
        )
        try:
            self.run_btn.configure(
                bg="#2e7d32", fg="white",
                activebackground="#256628", activeforeground="white",
                disabledforeground="#dddddd",
            )
        except tk.TclError:
            pass
        self.run_btn.pack(fill="x", **pad)

        self.status = tk.Label(self.root, text="", fg="#444", wraplength=520, justify="left")
        self.status.pack(fill="x", **pad)

        self.reveal_btn = tk.Button(
            self.root, text=t("gui_reveal_btn"), command=self._reveal, state="disabled"
        )
        self.reveal_btn.pack(**pad)
        self._last_output: Optional[Path] = None

    def _set_step2(self, mode: str) -> None:
        """Show the right step-2 widgets: 'hidden', 'single' or 'multi'."""
        self._track_prompt.pack_forget()
        self.track_combo.pack_forget()
        self._auto_note.pack_forget()
        if mode == "multi":
            self._track_prompt.pack(fill="x", anchor="w")
            self.track_combo.pack(fill="x", pady=(4, 0))
        elif mode == "single":
            self._auto_note.pack(fill="x", anchor="w")

    # ---- language toggle ------------------------------------------------
    def _lang_btn_text(self) -> str:
        # Show the language you would switch TO.
        return "English" if get_lang() == "zh" else "中文"

    def _toggle_lang(self) -> None:
        new_lang = "en" if get_lang() == "zh" else "zh"
        set_lang(new_lang)
        save_lang(new_lang)
        self._retext()

    def _retext(self) -> None:
        self.root.title(t("app_title"))
        self._tagline.configure(text=t("gui_tagline"))
        self._step1.configure(text=t("gui_step1"))
        self.drop.configure(text=t("gui_drop_label"))
        if self._pick_btn is not None:
            self._pick_btn.configure(text=t("gui_pick_btn"))
        self._track_prompt.configure(text=t("gui_choose_prompt"))
        self._auto_note.configure(text=t("gui_auto_track"))
        self.run_btn.configure(text=t("gui_step3_btn"))
        self.reveal_btn.configure(text=t("gui_reveal_btn"))
        self._lang_btn.configure(text=self._lang_btn_text())
        # Re-render the status line (and step-2 visibility) in the new language.
        if self.files:
            self._classify()
        else:
            missing = check_all()
            if missing:
                self._set_status(t("missing_cmds", tools=", ".join(missing)), "#b00")
            else:
                self._set_status("", "#444")

    # ---- input handling -------------------------------------------------
    def _on_drop(self, event) -> None:
        paths = self._parse_dnd(event.data)
        self._add_files(paths)

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
        selected = filedialog.askopenfilenames(title=t("gui_pick_title"))
        if selected:
            self._add_files([Path(p) for p in selected])

    def _add_files(self, paths: List[Path]) -> None:
        """Merge dropped files into the current selection.

        Keeps at most one video and one subtitle, each updated to the most
        recent matching file. This lets users drag the two files separately
        (or re-drag to replace just one) without the second drop clearing the
        first.
        """
        video: Optional[Path] = None
        sub: Optional[Path] = None
        for p in [*self.files, *paths]:
            if is_subtitle(p):
                sub = p
            else:
                video = p
        merged = [p for p in (video, sub) if p is not None]
        self._set_files(merged)

    def _set_files(self, paths: List[Path]) -> None:
        self.files = paths
        self.listbox.delete(0, tk.END)
        for p in paths:
            self.listbox.insert(tk.END, p.name)
        self._classify()

    def _classify(self) -> None:
        self.track_combo.set("")
        self._set_step2("hidden")
        self.run_btn["state"] = "disabled"
        self.reveal_btn["state"] = "disabled"
        self._set_status("", "#444")

        try:
            video, source = classify(self.files)
        except (DetectError, MissingDependency) as e:
            self._set_status(str(e), "#b00")
            return

        self.video = video
        self.source = source
        streams = list_embedded_subs(video)
        if not streams:
            self._set_status(t("no_embedded"), "#b00")
            return

        self._streams = streams
        self.track_combo["values"] = [s.label() for s in streams]
        self.track_combo.current(0)
        multi = len(streams) > 1
        self._set_step2("multi" if multi else "single")
        self.run_btn["state"] = "normal"
        tail = t("gui_need_choose") if multi else t("gui_use_first")
        self._set_status(
            t("gui_summary", video=video.name, sub=source.name, count=len(streams), tail=tail),
            "#070",
        )

    # ---- run ------------------------------------------------------------
    def _run(self) -> None:
        sub_index = self.track_combo.current()
        if sub_index < 0:
            sub_index = 0
        self.run_btn["state"] = "disabled"
        self._set_status(t("gui_aligning"), "#444")
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
        self._set_status(t("gui_done", path=output), "#070")
        self.reveal_btn["state"] = "normal"
        self.run_btn["state"] = "normal"

    def _fail(self, message: str, log_tail: str) -> None:
        self._set_status(message, "#b00")
        self.run_btn["state"] = "normal"
        if log_tail:
            messagebox.showerror(t("alass_log_header"), log_tail)

    def _reveal(self) -> None:
        if self._last_output:
            reveal(self._last_output)

    def _set_status(self, text: str, color: str) -> None:
        self.status.configure(text=text, fg=color)

    def run(self) -> None:
        missing = check_all()
        if missing:
            self._set_status(t("missing_cmds", tools=", ".join(missing)), "#b00")
        self.root.mainloop()


def main(argv=None) -> int:
    # Precedence: SYNCSUB_LANG env > saved config > auto-detection.
    if not has_env_override():
        saved = load_saved_lang()
        if saved:
            set_lang(saved)
    app = App()
    args = list(argv) if argv is not None else sys.argv[1:]
    if args:
        app._set_files([Path(a) for a in args])
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
