# Sign PyInstaller sidecars bundled under src-tauri (same cert as bundle.windows in tauri.conf.json).
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Resolve-SignTool.ps1")

$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $repoRoot "src-tauri\tauri.conf.json"))) {
    $repoRoot = (Get-Location).Path
}

$targets = @(
    (Join-Path $repoRoot "src-tauri\frontend\frontend-x86_64-pc-windows-msvc.exe"),
    (Join-Path $repoRoot "src-tauri\backend\rescuebox-x86_64-pc-windows-msvc.exe")
)

$signOne = Join-Path $PSScriptRoot "sign_one_exe.ps1"
foreach ($path in $targets) {
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Warning "Skip signing (missing): $path"
        continue
    }
    & $signOne -BinaryPath $path
}
