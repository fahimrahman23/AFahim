; Inno Setup 6 Script for MeWe AutoFollow
; Generates Windows 11 Desktop Setup Installer (MeWe_AutoFollow_Setup.exe)

#define MyAppName "MeWe AutoFollow"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MeWe Tools"
#define MyAppURL "https://github.com/mewe-autofollow/mewe-autofollow"
#define MyAppExeName "MeWeAutoFollow.exe"

[Setup]
AppId={{9C4D3812-7086-4F54-9E59-C4345B0A21E8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\MeWeAutoFollow
DefaultGroupName={#MyAppName}
OutputDir=release
OutputBaseFilename=MeWe_AutoFollow_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\MeWeAutoFollow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
