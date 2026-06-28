#!/usr/bin/env bash
# Install syncsub on macOS: dependencies, the CLI, and the Finder Quick Action.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_SRC="$REPO_ROOT/platform/macos/字幕按内嵌时间轴对齐.workflow"
WORKFLOW_DST="$HOME/Library/Services/字幕按内嵌时间轴对齐.workflow"

info()  { printf '\033[0;34m==>\033[0m %s\n' "$*"; }
warn()  { printf '\033[0;33m警告:\033[0m %s\n' "$*"; }

# 1. Homebrew
if ! command -v brew >/dev/null 2>&1; then
	echo "未找到 Homebrew。请先安装：https://brew.sh" >&2
	exit 1
fi

# 2. Runtime dependencies
info "安装依赖 ffmpeg / alass …"
for pkg in ffmpeg alass; do
	if brew list --formula "$pkg" >/dev/null 2>&1; then
		echo "  $pkg 已安装"
	else
		brew install "$pkg"
	fi
done

# 3. pipx + the syncsub package
if ! command -v pipx >/dev/null 2>&1; then
	info "安装 pipx …"
	brew install pipx
fi
pipx ensurepath >/dev/null 2>&1 || true

info "安装 syncsub（含 GUI 可选依赖）…"
pipx install --force "$REPO_ROOT[gui]" 2>/dev/null || pipx install --force "$REPO_ROOT"

# 4. Finder Quick Action
info "安装 Finder 快捷操作 …"
mkdir -p "$HOME/Library/Services"
rm -rf "$WORKFLOW_DST"
cp -R "$WORKFLOW_SRC" "$WORKFLOW_DST"

cat <<'EOF'

安装完成。

最后一步（手动绑定快捷键）：
  系统设置 → 键盘 → 键盘快捷键 → 服务 → 通用
  找到「字幕按内嵌时间轴对齐」，设为  ⌃⌥⌘S

用法：
  Finder 选中 1 个视频 + 1 个字幕 → 右键「快捷操作」或按快捷键。
EOF
