# PyInstaller spec — build a standalone (no-Python-needed) GUI bundle.
#
# Run from this directory (platform/windows):
#   pyinstaller syncsub.spec
#
# Expects ffmpeg.exe / ffprobe.exe / alass.exe in ./bin (the CI workflow
# downloads them there before building).
import glob

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("tkinterdnd2")

# Bundle the external tools next to the app so deps.resolve() finds them.
binaries += [(path, ".") for path in glob.glob("bin/*.exe")]

hiddenimports += ["syncsub", "syncsub.gui", "syncsub.core", "syncsub.detect"]

a = Analysis(
    ["gui_entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="syncsub-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="syncsub-gui",
)
