@echo off
setlocal
set "PATH=%LOCALAPPDATA%\syncsub\bin;%PATH%"
where syncsub-gui >nul 2>&1 && (
  syncsub-gui %*
) || (
  py -m syncsub.gui %* 2>nul || python -m syncsub.gui %*
)
