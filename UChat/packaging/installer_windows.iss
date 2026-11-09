[Setup]
AppName=UChat (Unsafe Chat)
AppVersion=1.0
AppPublisher=Tomrej
DefaultDirName={autopf}\UChat
DefaultGroupName=UChat
OutputDir=..\release_dist
OutputBaseFilename=UChat_Setup_v1.0
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\UChat\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\UChat"; Filename: "{app}\UChat.exe"
Name: "{autodesktop}\UChat"; Filename: "{app}\UChat.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\UChat.exe"; Description: "{cm:LaunchProgram,UChat}"; Flags: nowait postinstall skipifsilent