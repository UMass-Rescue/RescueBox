function Resolve-SignTool {
    if ($env:SIGNTOOL_PATH -and (Test-Path -LiteralPath $env:SIGNTOOL_PATH)) {
        return (Resolve-Path -LiteralPath $env:SIGNTOOL_PATH).Path
    }

    $onPath = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($onPath) {
        return $onPath.Source
    }

    $roots = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin"
    )

    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }

        # e.g. ...\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe
        $versioned = Get-ChildItem -LiteralPath $root -Directory -Filter "10.0.*" -ErrorAction SilentlyContinue |
            ForEach-Object {
                $p = Join-Path $_.FullName "x64\signtool.exe"
                if (Test-Path -LiteralPath $p) { Get-Item -LiteralPath $p }
            } |
            Sort-Object FullName -Descending
        if ($versioned) {
            return $versioned[0].FullName
        }

        $candidates = Get-ChildItem -LiteralPath $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
            Sort-Object FullName -Descending
        if ($candidates) {
            return $candidates[0].FullName
        }
    }

    $appCertKit = "${env:ProgramFiles(x86)}\Windows Kits\10\App Certification Kit\signtool.exe"
    if (Test-Path -LiteralPath $appCertKit) {
        return $appCertKit
    }

    return $null
}

# Dot-source (`. .\Resolve-SignTool.ps1`) only defines the function; `-File` prints the path.
if ($MyInvocation.InvocationName -ne '.') {
    $tool = Resolve-SignTool
    if ($tool) {
        Write-Output $tool
    } else {
        Write-Error "signtool.exe not found (set SIGNTOOL_PATH or install Windows SDK Signing Tools)."
        exit 1
    }
}
