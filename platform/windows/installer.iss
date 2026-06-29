; Inno Setup script — wrap the PyInstaller bundle into a single setup.exe.
; Compile from this directory (platform/windows) after PyInstaller has
; produced dist\syncsub-gui:
;   iscc installer.iss

#define MyAppName "字幕按内嵌时间轴对齐"
#define MyAppNameEn "SyncSub"
#define MyAppVersion "0.1.0"
#define MyAppExe "syncsub-gui.exe"

[Setup]
AppId={{8F3A1C2D-5B6E-4A7F-9C8D-1E2F3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=syncsub
DefaultDirName={autopf}\{#MyAppNameEn}
DefaultGroupName={#MyAppNameEn}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExe}
UninstallDisplayName={#MyAppName}
OutputDir=Output
OutputBaseFilename=syncsub-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut / 创建桌面快捷方式"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\syncsub-gui\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Uninstall {#MyAppNameEn}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon
Name: "{sendto}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch now / 立即运行"; Flags: nowait postinstall skipifsilent
