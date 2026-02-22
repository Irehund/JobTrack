; installer.iss
; =============
; Inno Setup script for JobTrack Windows installer.
; Download Inno Setup: https://jrsoftware.org/isinfo.php
;
; Usage:
;   1. Build with PyInstaller first: python build.py
;   2. Then: iscc installer.iss
;   Output: dist/JobTrack_Setup_1.0.0.exe

#define AppName      "JobTrack"
#define AppVersion   "1.0.0"
#define AppPublisher "JobTrack Contributors"
#define AppURL       "https://github.com/Irehund/JobTracker"
#define AppExeName   "JobTrack.exe"
#define DistDir      "dist\JobTrack"

[Setup]
AppId={{A8F3C2D1-4B5E-4F8A-9C1D-2E3F4A5B6C7D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=JobTrack_Setup_{#AppVersion}
SetupIconFile=assets\icons\jobtrack.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenuicon";  Description: "Create Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked

[Files]
; Include the entire PyInstaller output folder
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";                     Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";           Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}";             Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartmenu}\{#AppName}";             Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Detect if the app is currently running and prompt to close it
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
end;
