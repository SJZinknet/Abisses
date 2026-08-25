#ifndef AppVersion
  #define AppVersion "56"
#endif

[Setup]
AppId={{2F3B63D9-6C47-4D4F-91C7-EB964E69D572}
AppName=Abisses
AppVersion={#AppVersion}
AppVerName=Abisses {#AppVersion}
AppPublisher=Projet Abisses
AppPublisherURL=https://github.com/SJZinknet/Abisses
AppSupportURL=https://github.com/SJZinknet/Abisses/issues
AppUpdatesURL=https://github.com/SJZinknet/Abisses/releases
DefaultDirName={localappdata}\Programs\Abisses
DefaultGroupName=Abisses
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
OutputDir=..\..\release
OutputBaseFilename=Abisses-Setup-v{#AppVersion}-Windows-x64
SetupIconFile=..\icons\abisses.ico
UninstallDisplayIcon={app}\Abisses.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=yes
SetupLogging=yes
UsePreviousAppDir=yes
UsePreviousGroup=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\Abisses\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Abisses"; Filename: "{app}\Abisses.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Abisses"; Filename: "{app}\Abisses.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\Abisses.exe"; Description: "Lancer Abisses"; Flags: nowait postinstall skipifsilent
