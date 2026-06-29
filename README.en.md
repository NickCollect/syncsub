# syncsub · Sync subtitles to a video's embedded timeline

[简体中文](README.md) | **English**

Align an **external source subtitle** to the timeline of a **target video's embedded subtitle track**.

Typical case: you have a well-translated subtitle whose timing doesn't match your copy of the video (it was made for a different release), and your target video ships with an embedded subtitle that *is* correctly timed. This tool uses that embedded subtitle as the reference, runs [alass](https://github.com/kaegi/alass) to align your source subtitle to it, and writes a new, correctly-timed subtitle.

- **macOS**: select the video + subtitle in Finder → Quick Action or shortcut `⌃⌥⌘S`
- **Windows**: drag the video + subtitle into the window (order doesn't matter)
- Shared Python core for detection, alignment, and naming on both platforms
- UI and messages **switch between English / Chinese by system locale** (force with `SYNCSUB_LANG=zh|en`)

---

## How it works

1. `ffprobe` figures out which file is the video and which is the subtitle (order-independent).
2. The video's embedded subtitle tracks are listed; if there are several, you pick one.
3. `ffmpeg` extracts the chosen embedded subtitle as the reference timeline.
4. `alass` aligns the source subtitle to that reference.
5. The result is written **next to the source subtitle** and revealed in the file manager.

---

## Step 1: Download the tool

Click the green **"Code"** button at the top of this page → **"Download ZIP"**, then **unzip** it. You'll get a folder named `syncsub-main`.

> The macOS and Windows installers below must be run from inside this unzipped folder.

---

## macOS: step-by-step

### 1. Install Homebrew (skip if you already have it)

Open the **Terminal** app (find it via Spotlight `⌘Space`), paste the line below, press Return, and follow the prompts:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Run the installer

In Terminal, type `cd ` (with a trailing space), then **drag the unzipped `syncsub-main` folder into the Terminal window** (it fills in the path) and press Return. Then paste:

```bash
bash scripts/install-macos.sh
```

It installs `ffmpeg`, `alass`, and the tool itself, and sets up the Finder Quick Action. You're done when you see the completion message.

### 3. Assign the shortcut

Open **System Settings → Keyboard → Keyboard Shortcuts → Services → General**, find **"字幕按内嵌时间轴对齐"** (the Quick Action), and set it to `⌃⌥⌘S` (Control + Option + Command + S).

### Usage

In Finder, **select 1 video + 1 subtitle** (hold `⌘` to click the second), then:

- press `⌃⌥⌘S`, **or**
- right-click → Quick Actions → the action above.

When it finishes, Finder jumps to the newly generated subtitle.

---

## Windows: step-by-step

### Option A (recommended, batteries included): the installer

Download **`syncsub-setup.exe`** from the [Releases](../../releases) page, then **double-click → Next → Next → Finish**.

- **No Python and no manual downloads** — `ffmpeg` and `alass` are bundled inside.
- It adds the app to the Start Menu (and, optionally, the Desktop and "Send to").
- If a blue "Windows protected your PC" dialog appears, click "More info" → "Run anyway".

### Option B (script install, smaller download)

1. **Install Python** 3.9+ from [python.org/downloads](https://www.python.org/downloads/); on the first screen tick **"Add Python to PATH"**.
2. Use the green **Code → Download ZIP**, unzip, open `syncsub-main`, and **double-click `install-windows.cmd`**. It downloads `ffmpeg` and `alass`, installs the tool, and creates shortcuts.

### Usage

**Option A (recommended):** open **"字幕按内嵌时间轴对齐"** from the Start Menu, drag **1 video + 1 subtitle** into the window (order doesn't matter), and click Align.

**Option B:** in File Explorer, select the video + subtitle → right-click → **Send to → 字幕按内嵌时间轴对齐**.

When it finishes, the window shows the output path; click "Show in file manager" to locate the new subtitle.

---

## Advanced: command line (both platforms)

After installing, use it directly from a terminal:

```bash
syncsub SOURCE_SUB VIDEO [OUTPUT_SUB]   # align
syncsub --list VIDEO                    # list the video's embedded subtitle tracks
syncsub --sub N SOURCE_SUB VIDEO        # use embedded track N
```

---

## Output naming

```
output = video_stem + "." + lang_tag + ".synced." + source_extension
```

- The **language tag** is the segment after the last `.` in the source subtitle's stem.
- If the source has no language tag, it falls back to `<video_stem>.synced.<ext>`.

Example:

| | Filename |
|---|---|
| Source subtitle | `The Bear S05E01 ...-FLUX.chs.简体&英文.ass` |
| Target video | `The.Bear.S05E01.Soda.2160p...H.265-NTb.mkv` |
| Output | `The.Bear.S05E01.Soda.2160p...H.265-NTb.简体&英文.synced.ass` |

---

## Supported formats

Subtitles: `.srt` `.ass` `.ssa` `.sub` `.idx`　　Video: any container with a video stream (`.mkv` / `.mp4`, etc.).

Both `.srt` and `.ass` source subtitles are supported; the output keeps the source's original format and extension.

> **About the reference track:** the embedded track used as the timing reference must be a **text subtitle** (srt / ass). If the video's embedded subtitle is an **image subtitle** (PGS, VobSub), it can't be extracted as a text reference — extraction fails and you'll be asked to pick another track. This is independent of whether your source subtitle is ass or srt.

---

## FAQ

- **Video has no embedded subtitle track** → the tool tells you; it relies on an embedded track as the reference, so it can't run without one.
- **Extraction failed** → try another track (some image subtitles such as PGS can't be extracted as a text reference).
- **Sync failed** → the last 30 lines of the alass log are shown to help you debug.

---

## License

[GPL-3.0-or-later](LICENSE). This project invokes and may redistribute ffmpeg and alass; see their projects for their respective licenses.
