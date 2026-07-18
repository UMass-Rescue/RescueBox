# Signs one PE file (Tauri signCommand %1 or manual). Same cert as src-tauri/tauri.conf.json.
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BinaryPath,
    [string]$Thumbprint = "721DC6509D5643BC3232C43D3A27EF8AF06A1651",
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [ValidateSet("sha1", "sha256")]
    [string]$FileDigest = "sha256"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Resolve-SignTool.ps1")

if ($env:RESCUEBOX_SKIP_SIGN -eq "1") {
    Write-Warning "RESCUEBOX_SKIP_SIGN=1; not signing $BinaryPath"
    exit 0
}

$signtool = Resolve-SignTool
if (-not $signtool) {
    Write-Error @"
signtool.exe not found. Install the Windows SDK signing tools, then rebuild.

  Visual Studio Installer -> Modify -> Individual components ->
  search "SDK" -> enable "Windows SDK Signing Tools for Desktop Apps"
  (or install Windows SDK 10/11 with Signing Tools).

Optional: set SIGNTOOL_PATH to the full path of signtool.exe.
Optional: set RESCUEBOX_SKIP_SIGN=1 to build unsigned (not for release).
"@
}

if (-not (Test-Path -LiteralPath $BinaryPath)) {
    Write-Error "Binary not found: $BinaryPath"
}

Write-Host "Signing with $signtool : $BinaryPath"
& $signtool sign /sha1 $Thumbprint /fd $FileDigest /td $FileDigest /tr $TimestampUrl /v $BinaryPath
if ($LASTEXITCODE -ne 0) {
    throw "signtool failed (exit $LASTEXITCODE)"
}
