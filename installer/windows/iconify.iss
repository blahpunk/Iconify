#define AppName "Iconify"
#define AppVersion "0.1.0"
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
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath(ExpandConstant('{app}'))
Root: HKCR; Subkey: "*\shell\Iconify"; ValueType: string; ValueName: ""; ValueData: "Convert with Iconify"
Root: HKCR; Subkey: "*\shell\Iconify\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""

[Code]
function NeedsAddPath(Path: string): Boolean;
var
  CurrentPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', CurrentPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Lowercase(Path) + ';', ';' + Lowercase(CurrentPath) + ';') = 0;
end;

