#ifndef Payload
  #error Payload is required
#endif
#ifndef Version
  #error Version is required
#endif
#ifndef CommitShort
  #error CommitShort is required
#endif
#ifndef ManifestSHA
  #error ManifestSHA is required
#endif
#ifndef FileList
  #error FileList is required
#endif
#ifndef Output
  #error Output is required
#endif

[Setup]
AppId={{9835C52D-2C14-48B5-B03C-637F14587661}
AppName=Hugin
AppVersion={#Version}
AppPublisher=Brian
DefaultDirName={localappdata}\Programs\Hugin\releases\{#Version}-{#CommitShort}
UsePreviousAppDir=no
DisableDirPage=yes
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
#include FileList

[Icons]
Name: "{group}\Hugin"; Filename: "{app}\Hugin.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Hugin"; Filename: "{app}\Hugin.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Hugin.exe"; Parameters: "--show"; Description: "Hugin starten"; Flags: nowait postinstall skipifsilent; Check: SetupCompleted

[Code]
type
  THuginFileTime = record Low, High: Cardinal; end;
function HuginCurrentProcess: THandle; external 'GetCurrentProcess@kernel32.dll stdcall';
function HuginCurrentProcessId: Cardinal; external 'GetCurrentProcessId@kernel32.dll stdcall';
function HuginProcessTimes(Process: THandle; var Creation, ExitTime, KernelTime, UserTime: THuginFileTime): Boolean;
  external 'GetProcessTimes@kernel32.dll stdcall';

var GuardReady, GuardRelease, UninstallHelper: String;
    GuardHeld, SetupSucceeded, SetupAttempted: Boolean;

function AcquireGuard(Helper, Target, Manifest: String): Boolean;
var Creation, ExitTime, KernelTime, UserTime: THuginFileTime; Started: Int64;
    Code, Count: Integer; Status: AnsiString;
begin
  Result := False;
  if not HuginProcessTimes(HuginCurrentProcess, Creation, ExitTime, KernelTime, UserTime) then exit;
  Started := (Int64(Creation.High) shl 32) or Creation.Low;
  GuardReady := GetTempDir + 'hugin-' + IntToStr(HuginCurrentProcessId) + '-' + IntToStr(Random(1000000000));
  GuardRelease := GuardReady + '.release';
  if not Exec(Helper, '--install-guard ' + IntToStr(HuginCurrentProcessId) + ' ' + IntToStr(Started) +
      ' "' + GuardReady + '" "' + GuardRelease + '" "' + RemoveBackslashUnlessRoot(Target) +
      '" "' + Manifest + '" {#ManifestSHA}', '', SW_HIDE, ewNoWait, Code) then exit;
  for Count := 1 to 3000 do begin
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
begin
  ExtractTemporaryFile('Hugin.exe');
  ExtractTemporaryFile('release-manifest.json');
  if not GuardHeld then
    if not AcquireGuard(ExpandConstant('{tmp}\Hugin.exe'), WizardDirValue,
        ExpandConstant('{tmp}\release-manifest.json')) then begin
      ReleaseGuard;
      Result := 'Hugin muss regulär beendet sein. Der Zielordner muss leer sein oder zu genau diesem unveränderten Build gehören. Es wurden keine Programmdateien installiert.';
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
  if CurStep = ssPostInstall then begin
    SetupAttempted := True;
    try
      ConfigureInstalled(False);
      ReleaseGuard;
      SetupSucceeded := True;
    finally
      if GuardRelease <> '' then ReleaseGuard;
    end;
  end;
end;

function InitializeUninstall: Boolean;
begin
  UninstallHelper := GetTempDir + 'hugin-uninstall-' + IntToStr(HuginCurrentProcessId) + '-' + IntToStr(Random(1000000000)) + '.exe';
  Result := CopyFile(ExpandConstant('{app}\Hugin.exe'), UninstallHelper, True);
  if Result then Result := AcquireGuard(UninstallHelper, ExpandConstant('{app}'),
      ExpandConstant('{app}\.hugin-installation\manifest.json'));
  if Result then begin
    try ConfigureInstalled(True);
    except Result := False; end;
  end;
  if not Result then MsgBox('Bitte Hugin regulär beenden. Die Deinstallation wurde nicht gestartet.', mbError, MB_OK);
end;

function SetupCompleted: Boolean;
begin Result := SetupSucceeded; end;

function GetCustomSetupExitCode: Integer;
begin
  Result := 0;
  if SetupAttempted and not SetupSucceeded then Result := 11;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and SetupAttempted and not SetupSucceeded then begin
    WizardForm.FinishedHeadingLabel.Caption := 'Hugin wurde nicht fertig eingerichtet';
    WizardForm.FinishedLabel.Caption := 'Die Einrichtung ist fehlgeschlagen. Hugin wird nicht gestartet. Einstellungen und Sicherungen bleiben erhalten. Bitte das Installationsprotokoll prüfen.';
  end;
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
