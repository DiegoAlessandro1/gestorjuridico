; ============================================================================
; INNO SETUP - INSTALADOR WINDOWS
; ============================================================================
; Arquivo: installer/windows/GestorJuridico.iss
; ============================================================================

#define MyAppName "Gestor Jurídico"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gestor Juridico"
#define MyAppExeName "GestorJuridico.exe"

[Setup]
AppId={{6F813FCD-8E93-4FE8-8B8D-8A458D84FB57}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Gestor Juridico
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\output
OutputBaseFilename=GestorJuridicoSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\..\dist\GestorJuridico\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\setup_config_db.bat"; Description: "Configurar acesso ao banco (MongoDB)"; Flags: postinstall runascurrentuser waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: postinstall nowait skipifsilent
