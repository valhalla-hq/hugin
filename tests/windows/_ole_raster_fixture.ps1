param([Parameter(Mandatory=$true)][string]$ControlDirectory,
      [Parameter(Mandatory=$true)][uint32]$ExpectedSequence)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing,System.Windows.Forms
Add-Type -Path (Join-Path $PSScriptRoot '_ole_raster_fixture.cs') -ReferencedAssemblies System.Drawing
$huginOleInitialized=$false
$huginRaster=$null
try {
    $huginHr=[HuginRaster]::OleInitialize([IntPtr]::Zero)
    if ($huginHr -ne 0 -and $huginHr -ne 1) { throw 'OLE initialization failed' }
    $huginOleInitialized=$true
    [HuginRaster]::TracePath=(Join-Path $ControlDirectory 'trace')
    $huginRaster=New-Object HuginRaster
    if(-not $huginRaster.ValidatePng() -or -not $huginRaster.ValidateBitmap()) { throw 'fixture self-check failed' }
    $huginPublished=$huginRaster.Publish($ExpectedSequence)
    $huginReady=@{ sequence=$huginPublished; png_sha256=[HuginRaster]::Digest($huginRaster.Png) } | ConvertTo-Json -Compress
    [IO.File]::WriteAllText((Join-Path $ControlDirectory 'ready'),$huginReady)
    $huginDeadline=[DateTime]::UtcNow.AddSeconds(45)
    while ([DateTime]::UtcNow -lt $huginDeadline -and -not (Test-Path -LiteralPath (Join-Path $ControlDirectory 'stop'))) {
        [Windows.Forms.Application]::DoEvents()
        if ((Test-Path -LiteralPath (Join-Path $ControlDirectory 'ownership')) -and -not (Test-Path -LiteralPath (Join-Path $ControlDirectory 'owned'))) {
            [IO.File]::WriteAllText((Join-Path $ControlDirectory 'owned'),[string]$huginRaster.CurrentSequence())
        }
        $huginReadPath=Join-Path $ControlDirectory 'read'
        if ((Test-Path -LiteralPath $huginReadPath) -and -not (Test-Path -LiteralPath (Join-Path $ControlDirectory 'result'))) {
            $huginExpected=[uint32][IO.File]::ReadAllText($huginReadPath)
            $huginDigest=[HuginRaster]::ReadPngStream($huginExpected)
            [IO.File]::WriteAllText((Join-Path $ControlDirectory 'result'),$huginDigest)
        }
        Start-Sleep -Milliseconds 10
    }
} finally {
    if ($null -ne $huginRaster -and [HuginRaster]::OleIsCurrentClipboard($huginRaster) -eq 0) { [void][HuginRaster]::OleFlushClipboard() }
    if ($huginOleInitialized) { [HuginRaster]::OleUninitialize() }
    if ($null -ne $huginRaster) { $huginRaster.CloseBitmaps() }
}
