[Setup]
AppName=DZ PDF Toolkit
AppVersion=1.0.0
AppPublisher=Oussama Boudinar (dzopensource-lab)
AppPublisherURL=https://github.com/dzopensource-lab
AppSupportURL=https://github.com/dzopensource-lab
DefaultDirName={autopf}\DZ PDF Toolkit
DefaultGroupName=DZ PDF Toolkit
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\DZ-PDF-Toolkit.exe
OutputDir=Output
OutputBaseFilename=DZ_PDF_Toolkit_Setup_v1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\DZ-PDF-Toolkit.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DZ PDF Toolkit"; Filename: "{app}\DZ-PDF-Toolkit.exe"; IconFilename: "{app}\DZ-PDF-Toolkit.exe"
Name: "{autodesktop}\DZ PDF Toolkit"; Filename: "{app}\DZ-PDF-Toolkit.exe"; IconFilename: "{app}\DZ-PDF-Toolkit.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DZ-PDF-Toolkit.exe"; Description: "{cm:LaunchProgram,DZ PDF Toolkit}"; Flags: nowait postinstall skipifsilent