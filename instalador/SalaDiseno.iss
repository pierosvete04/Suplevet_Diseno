; Instalador de la Sala de diseño (Inno Setup). Lo compila GitHub Actions en cada versión:
;   iscc /DVersion=0.1.0 /DOrigen=..\dist\SalaDiseno instalador\SalaDiseno.iss
; Se instala en la carpeta del usuario (no pide permisos de administrador), así la sala se actualiza sola después.
; Los datos (datos\) nunca se borran: ni al actualizar ni al desinstalar.

#ifndef Version
  #define Version "0.0.0"
#endif
#ifndef Origen
  #define Origen "..\dist\SalaDiseno"
#endif

[Setup]
AppId={{9B4E2D71-3C6A-4F0E-8D2B-44495345C3F1}
AppName=Sala de diseño
AppVersion={#Version}
AppPublisher=Piero Svete
DefaultDirName={localappdata}\SalaDiseno
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..
OutputBaseFilename=SalaDiseno-Instalador-v{#Version}
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\SalaDiseno.exe
UninstallDisplayName=Sala de diseño
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "{#Origen}\*"; DestDir: "{app}"; Excludes: "datos\*"; Flags: recursesubdirs ignoreversion createallsubdirs
Source: "icono.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\datos"; Flags: uninsneveruninstall

[Icons]
Name: "{userprograms}\Sala de diseño"; Filename: "{app}\SalaDiseno.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icono.ico"
Name: "{userdesktop}\Sala de diseño"; Filename: "{app}\SalaDiseno.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icono.ico"; Tasks: escritorio

[Run]
Filename: "{app}\SalaDiseno.exe"; Description: "Abrir la Sala de diseño ahora"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
