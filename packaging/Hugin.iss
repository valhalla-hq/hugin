#ifndef Payload
  #error Payload is required
#endif
#ifndef Version
  #error Version is required
#endif
#ifndef Output
  #error Output is required
#endif

[Setup]
AppId={{9835C52D-2C14-48B5-B03C-637F14587661}
AppName=Hugin
AppVersion={#Version}
AppPublisher=Brian
DefaultDirName={localappdata}\Programs\Hugin
DefaultGroupName=Hugin
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.19041
OutputDir={#Output}
OutputBaseFilename=Hugin-{#Version}-Setup
SetupIconFile={#Payload}\Hugin.ico
UninstallDisplayIcon={app}\Hugin.exe
Compression=lzma2/fast
SolidCompression=no
DiskSpanning=yes
DiskSliceSize=2100000000
CloseApplications=no
RestartApplications=no
SetupMutex=Local\Hugin.ProductionSetup.v1
WizardStyle=modern
WizardSizePercent=115
DisableProgramGroupPage=yes
UninstallFilesDir={app}\.installer

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; Flags: unchecked

[Files]
Source: "{#Payload}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Hugin"; Filename: "{app}\Hugin.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Hugin"; Filename: "{app}\Hugin.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Retained ownership fact permits reinstalling into retained user state after uninstall.
Root: HKCU; Subkey: "Software\Hugin\Installer"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"

[Run]
Filename: "{app}\Hugin.exe"; Parameters: "--show"; Description: "Hugin starten"; Flags: nowait postinstall skipifsilent

[Code]
type
  THuginFileTime = record Low, High: Cardinal; end;
function HuginCurrentProcess: THandle; external 'GetCurrentProcess@kernel32.dll stdcall';
function HuginCurrentProcessId: Cardinal; external 'GetCurrentProcessId@kernel32.dll stdcall';
function HuginProcessTimes(Process: THandle; var Creation, ExitTime, KernelTime, UserTime: THuginFileTime): Boolean;
  external 'GetProcessTimes@kernel32.dll stdcall';

var GuardReady, GuardRelease, UninstallHelper: String;
    GuardHeld: Boolean;

function AcquireGuard(Helper: String): Boolean;
var Creation, ExitTime, KernelTime, UserTime: THuginFileTime; Started: Int64;
    Code, Count: Integer; Status: AnsiString;
begin
  Result := False;
  if not HuginProcessTimes(HuginCurrentProcess, Creation, ExitTime, KernelTime, UserTime) then exit;
  Started := (Int64(Creation.High) shl 32) or Creation.Low;
  GuardReady := GetTempDir + 'hugin-' + IntToStr(HuginCurrentProcessId) + '-' + IntToStr(Random(1000000000));
  GuardRelease := GuardReady + '.release';
  if not Exec(Helper, '--install-guard ' + IntToStr(HuginCurrentProcessId) + ' ' + IntToStr(Started) +
      ' "' + GuardReady + '" "' + GuardRelease + '"', '', SW_HIDE, ewNoWait, Code) then exit;
  for Count := 1 to 50 do begin
    if LoadStringFromFile(GuardReady, Status) then begin
      Result := Status = 'ready'; GuardHeld := Result; exit;
    end;
    Sleep(100);
  end;
end;

procedure ReleaseGuard;
var Count: Integer;
begin
  if GuardRelease = '' then exit;
  if not SaveStringToFile(GuardRelease, 'release', False) then
    RaiseException('Die Installationssperre konnte nicht freigegeben werden.');
  if not GuardHeld then begin GuardRelease := ''; exit; end;
  for Count := 1 to 50 do begin
    if FileExists(GuardReady + '.closed') then begin GuardRelease := ''; GuardHeld := False; exit; end;
    Sleep(100);
  end;
  RaiseException('Die Installationssperre hat noch keine Freigabe bestätigt.');
end;

function InitializeSetup: Boolean;
begin
  Result := IsDotNetInstalled(net48, 0);
  if not Result then MsgBox('Hugin benötigt die in Windows enthaltene .NET-Framework-4.8-Laufzeit. Es wurde nichts installiert.', mbError, MB_OK);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Existing: String; Found: TFindRec; NonEmpty: Boolean;
begin
  ExtractTemporaryFile('Hugin.exe');
  NonEmpty := False;
  if FindFirst(AddBackslash(WizardDirValue) + '*', Found) then begin
    try
      repeat
        if (Found.Name <> '.') and (Found.Name <> '..') then NonEmpty := True;
      until not FindNext(Found);
    finally FindClose(Found); end;
  end;
  if NonEmpty then
    if not RegQueryStringValue(HKCU, 'Software\Hugin\Installer', 'InstallLocation', Existing) or
       not SameText(RemoveBackslashUnlessRoot(Existing), RemoveBackslashUnlessRoot(WizardDirValue)) then begin
      Result := 'Der Zielordner enthält Dateien einer unbekannten Installation. Bitte einen leeren Ordner wählen.'; exit;
    end;
  if not GuardHeld then
    if not AcquireGuard(ExpandConstant('{tmp}\Hugin.exe')) then begin
      ReleaseGuard;
      Result := 'Bitte Hugin über sein Symbol im Infobereich regulär beenden und erneut versuchen. Es werden keine Apps automatisch beendet.';
    end;
end;

procedure ConfigureInstalled(Uninstall: Boolean);
var Python, Params: String; Code: Integer;
begin
  Python := ExpandConstant('{app}\.runtime\controller\Scripts\python.exe');
  Params := '-B "' + ExpandConstant('{app}\tools\install_setup.py') + '" --root "' + ExpandConstant('{app}') + '"';
  if Uninstall then Params := Params + ' --uninstall';
  if not Exec(Python, Params, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Code) or (Code <> 0) then
    RaiseException('Die Hugin-Einrichtung konnte nicht sicher abgeschlossen werden. Einstellungen und Sicherungen bleiben erhalten.');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin ConfigureInstalled(False); ReleaseGuard; end;
end;

function InitializeUninstall: Boolean;
begin
  UninstallHelper := GetTempDir + 'hugin-uninstall-' + IntToStr(HuginCurrentProcessId) + '-' + IntToStr(Random(1000000000)) + '.exe';
  Result := CopyFile(ExpandConstant('{app}\Hugin.exe'), UninstallHelper, True);
  if Result then Result := AcquireGuard(UninstallHelper);
  if not Result then MsgBox('Bitte Hugin regulär beenden. Die Deinstallation wurde nicht gestartet.', mbError, MB_OK);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then ConfigureInstalled(True);
end;

procedure DeinitializeSetup;
begin
  if GuardRelease <> '' then ReleaseGuard;
end;

procedure DeinitializeUninstall;
begin
  if GuardRelease <> '' then ReleaseGuard;
  if UninstallHelper <> '' then DeleteFile(UninstallHelper);
end;
