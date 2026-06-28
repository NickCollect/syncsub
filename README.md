# syncsub · 字幕按内嵌时间轴对齐

把**外挂源字幕**对齐到**目标视频内嵌字幕轨**的时间轴上。

适用场景：你有一份翻译质量好但时间轴对不上的字幕（来自另一个版本的视频），目标视频自带一条时间轴正确的内嵌字幕。本工具用目标视频的内嵌字幕作参考，用 [alass](https://github.com/kaegi/alass) 把源字幕对齐过去，输出一份时间轴正确的新字幕。

- **macOS**：Finder 选中视频 + 字幕 → 右键快捷操作或快捷键 `⌃⌥⌘S`
- **Windows**：把视频 + 字幕拖进窗口（顺序不限）
- 核心判别、对齐、命名逻辑两端共用（Python）

---

## 工作原理

1. 用 `ffprobe` 自动判别哪个是视频、哪个是字幕（顺序无关）。
2. 列出视频的内嵌字幕轨；多条时让你选择。
3. 用 `ffmpeg` 抽出所选内嵌字幕作为参考时间轴。
4. 用 `alass` 把源字幕对齐到该参考时间轴。
5. 输出到**源字幕所在目录**，并在文件管理器中定位。

---

## 安装

### 依赖

- [ffmpeg / ffprobe](https://ffmpeg.org/)
- [alass](https://github.com/kaegi/alass)
- Python 3.9+

### macOS

```bash
git clone https://github.com/NickCollect/syncsub.git
cd syncsub
bash scripts/install-macos.sh
```

脚本会用 Homebrew 装 `ffmpeg`、`alass`，用 pipx 装 `syncsub`，并把 Finder 快捷操作装到 `~/Library/Services/`。

最后手动绑定快捷键：**系统设置 → 键盘 → 键盘快捷键 → 服务 → 通用**，给「字幕按内嵌时间轴对齐」设为 `⌃⌥⌘S`。

### Windows

```powershell
git clone https://github.com/NickCollect/syncsub.git
cd syncsub
powershell -ExecutionPolicy Bypass -File platform\windows\install.ps1
```

脚本会自动下载 `ffmpeg`、`alass` 到 `%LOCALAPPDATA%\syncsub\bin`，装好 `syncsub`，并创建「发送到」和开始菜单的快捷方式。

> 拖拽功能需要 `tkinterdnd2`（已作为可选依赖随包安装）。没有它时窗口会退化为「选择文件」按钮。

---

## 用法

### macOS

Finder 同时选中 **1 个视频 + 1 个字幕** → 右键「快捷操作 → 字幕按内嵌时间轴对齐」或按 `⌃⌥⌘S`。

### Windows

开始菜单打开「字幕按内嵌时间轴对齐」，把 **1 个视频 + 1 个字幕** 拖进窗口；或在资源管理器选中两个文件 → 右键 → 发送到 → 字幕按内嵌时间轴对齐。

### 命令行（两端通用）

```bash
syncsub SOURCE_SUB VIDEO [OUTPUT_SUB]   # 对齐
syncsub --list VIDEO                    # 列出内嵌字幕轨
syncsub --sub N SOURCE_SUB VIDEO        # 指定第 N 条内嵌轨
```

---

## 输出命名规则

```
输出名 = 视频名(去扩展名) + "." + 语言标签 + ".synced." + 源字幕扩展名
```

- **语言标签**取源字幕文件名（去扩展名后）最后一个 `.` 之后的部分。
- 源字幕没有语言标签时，回退为 `视频名.synced.扩展名`。

示例：

| | 文件名 |
|---|---|
| 源字幕 | `The Bear S05E01 ...-FLUX.chs.简体&英文.ass` |
| 目标视频 | `The.Bear.S05E01.Soda.2160p...H.265-NTb.mkv` |
| 输出 | `The.Bear.S05E01.Soda.2160p...H.265-NTb.简体&英文.synced.ass` |

---

## 支持格式

字幕：`.srt` `.ass` `.ssa` `.sub` `.idx`　　视频：任何含视频流的容器（`.mkv` / `.mp4` 等）。

---

## 常见问题

- **视频没有内嵌字幕轨** → 工具会提示；本工具依赖内嵌轨作参考，无内嵌轨无法使用。
- **抽轨失败** → 换一条字幕轨重试（某些图形字幕如 PGS 无法抽成文本参考）。
- **同步失败** → 会显示 alass 日志末 30 行，便于排查。

---

## License

[GPL-3.0-or-later](LICENSE)。本项目调用并可分发 ffmpeg、alass，二者许可见各自项目。
