#define AppName "Iconify"
#define AppVersion "0.2.1"
#define AppPublisher "Iconify contributors"
#define AppExeName "iconify.exe"

[Setup]
AppId={{7DBDE97F-3AE2-4C0E-988A-F8C4790D8E7E}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Iconify
DefaultGroupName={#AppName}
OutputDir=..\..\dist\installer
OutputBaseFilename=IconifySetup-{#AppVersion}
SetupIconFile=..\..\icon.ico
UninstallDisplayIcon={app}\iconify.exe
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\..\dist\Iconify\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Iconify"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\Iconify"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Registry]
Root: HKCR; Subkey: "*\shell\Iconify"; ValueType: string; ValueName: ""; ValueData: "Convert with Iconify"
Root: HKCR; Subkey: "*\shell\Iconify\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""
