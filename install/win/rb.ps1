# ==============================================================================
# Windows 11 RescueBox Environment Setup (WSL, Docker, Ollama, WinFSP)
# ==============================================================================

function Start-DockerEngineWithoutUi {
    Write-Host "Starting Docker Engine (CLI / service, no Desktop UI)..." -ForegroundColor Yellow

	# taskkill /F /IM "Docker Desktop.exe" /T
	taskkill /F /IM "Docker Desktop.exe" /T 2>$null
	
    $started = $false
    foreach ($serviceName in @('com.docker.service', 'docker')) {
        $svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if (-not $svc) { continue }
        if ($svc.Status -ne 'Running') {
            Set-Service -Name $serviceName -StartupType Automatic -ErrorAction SilentlyContinue
            Start-Service -Name $serviceName -ErrorAction Stop
        }
        Write-Host "Docker Windows service '$serviceName' is running." -ForegroundColor Green
        $started = $true
        break
    }

    if (-not $started) {
        $dockerCli = Join-Path ${Env:ProgramFiles} 'Docker\Docker\DockerCli.exe'
        if (Test-Path $dockerCli) {
            & $dockerCli -SwitchDaemon 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "DockerCli -SwitchDaemon succeeded." -ForegroundColor Green
                $started = $true
            }
        }
    }

    if (-not $started -and (Get-Command docker -ErrorAction SilentlyContinue)) {
        $desktopStart = docker desktop start 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "docker desktop start succeeded." -ForegroundColor Green
            $started = $true
        } elseif ($desktopStart) {
            Write-Host "docker desktop start: $desktopStart" -ForegroundColor DarkGray
        }
    }

    if (-not $started) {
        Write-Warning "Could not start Docker via service/CLI yet. If this is right after install, sign out/in or reboot, then run: Start-Service com.docker.service"
    }
}

function Start-PgvectorDatabase {
    Write-Host "Starting pgvector database (docker compose)..." -ForegroundColor Yellow
    $composeDir = $PSScriptRoot
    $composeFile = Join-Path $composeDir 'docker-compose.yml'
    if (-not (Test-Path $composeFile)) {
        Write-Error "Missing docker-compose.yml in $composeDir"
        return
    }

    Push-Location $composeDir
    try {
        docker compose up -d
        if ($LASTEXITCODE -ne 0) {
            Write-Error "docker compose up failed (exit $LASTEXITCODE)"
            return
        }

        Start-Sleep -Seconds 2
        $containerId = docker ps -q --filter 'name=rb-postgres' 2>$null
        if (-not $containerId) {
            Write-Error "pgvector docker not running, fix and rerun"
            return
        }
        Write-Host "pgvector docker running OK" -ForegroundColor Green

        Start-Sleep -Seconds 5
        $ext = docker exec -i rb-postgres psql -U rbuser -d rescuebox -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname = 'vector';" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "pgvector extension not created, fix and rerun"
            if ($ext) { Write-Host $ext }
            return
        }
        Write-Host "pgvector extension created OK" -ForegroundColor Green
        if ($ext) { Write-Host $ext }
    } finally {
        Pop-Location
    }
}

# 1. Enforce Administrator Privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "CRITICAL: This script must be run as Administrator."
    Exit
}

Write-Host "Starting automated environment setup..." -ForegroundColor Cyan

Write-Host "Detecting interactive desktop user..." -ForegroundColor Yellow

# This asks Windows who owns the active desktop session, returning 'COMPUTERNAME\Username'
$interactiveUser = (Get-CimInstance Win32_ComputerSystem).UserName

if ([string]::IsNullOrWhiteSpace($interactiveUser)) {
    Write-Error "CRITICAL: Could not detect the logged-in user. You are running as a background service or SYSTEM."
    Exit
}

# Split off the computer/domain name and keep just the exact username
$TargetUser = $interactiveUser.Split('\')[1]

Write-Host "Target user identified as: $TargetUser" -ForegroundColor Cyan
Write-Host "==============================================================================`n"

Write-Host "`nChecking for Winget (Windows Package Manager)..." -ForegroundColor Yellow

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Winget is installed and ready." -ForegroundColor Green
} else {
    Write-Host "Winget not found. Downloading the latest official release from Microsoft..." -ForegroundColor Cyan
    
    # Define the download URL for the latest App Installer MSIX bundle
    $wingetUrl = "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    $downloadPath = "$env:TEMP\winget.msixbundle"
    
    # Download the package silently
    Invoke-WebRequest -Uri $wingetUrl -OutFile $downloadPath -UseBasicParsing
    
    Write-Host "Installing Winget..."
    # Install the app package natively
    Add-AppxPackage -Path $downloadPath
    
    # Clean up the downloaded file
    Remove-Item $downloadPath -Force
    
    # CRITICAL: Refresh the terminal's PATH variables so it can actually "see" the new winget command
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Final verification
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Winget installed successfully!" -ForegroundColor Green
    } else {
        Write-Error "CRITICAL: Failed to install Winget. You may need to install 'App Installer' manually from the Microsoft Store."
        Exit 1
    }
}

# 2. Install WSL (Windows Subsystem for Linux)
Write-Host "`n[1/3] Checking WSL Status..." -ForegroundColor Yellow
if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    Write-Host "WSL is installed and available on this system." -ForegroundColor Green
} else {
    Write-Host "WSL not found. Installing WSL default..."
    wsl --install --no-distribution
    Write-Warning "WSL installed the core hypervisor. A SYSTEM REBOOT IS REQUIRED."
    Write-Warning "Please restart your computer, then run this script again to finish the installation."
    Exit
}

# 3. Install Docker Desktop via Winget
Write-Host "`n[2/3] Installing Docker Desktop..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker CLI already installed. Skipping..." -ForegroundColor Green
} else {
    # Using Winget allows silent background installation bypassing the GUI wizard
    winget install --id Docker.DockerDesktop --exact --silent --accept-package-agreements --accept-source-agreements
    Write-Host "Docker Desktop installed successfully." -ForegroundColor Green
}

# Inject the standard user into the Docker security group
Write-Host "Granting Docker permissions to $TargetUser..." -ForegroundColor Yellow
try {
    Add-LocalGroupMember -Group "docker-users" -Member $TargetUser -ErrorAction Stop
    Write-Host "Permissions granted." -ForegroundColor Green
} catch {
    # It throws an error if the user is already in the group, which is safe to ignore
    Write-Host "User is already in the docker-users group." -ForegroundColor Green
}

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "ollama is installed and ready." -ForegroundColor Green
} else {
	# 4. Install Ollama
	$ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
	Write-Host "Downloading the latest OllamaSetup.exe..."

	# Use the native Windows 11 curl executable (-L follows redirects, -o outputs the file)
	curl.exe -L -s -o $ollamaInstaller "https://ollama.com/download/OllamaSetup.exe"

	# 3. Execute the native installer silently
	Write-Host "Running installation..."
	[Environment]::SetEnvironmentVariable("OLLAMA_NO_UI", "1", "Process")

	$proc = Start-Process -FilePath $ollamaInstaller -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES" -PassThru

	# 3. Intelligent Polling: Do not wait for the installer to finish. 
	# wait for the UI to spawn so we can kill it.
	while (-not $proc.HasExited) {
		$ui = Get-Process -Name "ollama app" -ErrorAction SilentlyContinue
		if ($ui) {
			Write-Host "Suppressing auto-launched UI..." -ForegroundColor Cyan
			$ui | Stop-Process -Force
		}
		Start-Sleep -Seconds 1
	}
    
	Start-Sleep -Seconds 10
	
	# 4. Clean up the downloaded executable
	Remove-Item $ollamaInstaller -Force

	Write-Host "Ollama installed successfully." -ForegroundColor Green
}
# ==============================================================================
# CRITICAL: Force terminal to refresh system PATH to see the newly installed CLI
# ==============================================================================
Write-Host "Refreshing terminal environment variables..." -ForegroundColor DarkGray
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# The script can now securely see the actual executable
Write-Host "Pulling Granite model..."

ollama pull ibm/granite4.1:3b
ollama pull moondream:latest
ollama pull gemma3:1b
ollama pull gemma3:4b


# 5. Asynchronous Boot and Verification
Write-Host "`n[Finalizing] Booting engines and verifying pathways..." -ForegroundColor Yellow

Start-DockerEngineWithoutUi

# Timeout loop: Wait for Docker to expose its API (Max 60 seconds)
$timeout = 60
$elapsed = 0
Write-Host "Waiting for Docker daemon to become responsive..."
while ($elapsed -lt $timeout) {
    # Checking docker info is the most reliable way to confirm the engine is fully up
    $dockerCheck = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is online and fully linked!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if ($elapsed -ge $timeout) {
    Write-Error "Timed out waiting for Docker to initialize. Try: Start-Service com.docker.service ; docker info"
    Exit
}
Start-PgvectorDatabase

# 2. Define target variables
$downloadUrl = "https://github.com/winfsp/winfsp/releases/download/v2.1/winfsp-2.1.25156.msi"
$tempPath = "$env:TEMP\winfsp-installer.msi"

# 3. Download the MSI
Write-Host "`n[1/3] Downloading WinFSP..." -ForegroundColor Yellow
try {
    # -UseBasicParsing ensures compatibility across older PowerShell versions
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath -UseBasicParsing -ErrorAction Stop
    Write-Host "Download complete." -ForegroundColor Green
} catch {
    Write-Error "CRITICAL: Failed to download the MSI file. Check your network or the URL."
    Exit 1
}

# 4. Execute the silent installation
Write-Host "`n[2/3] Installing WinFSP silently (This may take a moment)..." -ForegroundColor Yellow
# /i = Install, /qn = Quiet No-UI, /norestart = Prevents unexpected server reboots
$installArgs = "/i `"$tempPath`" /qn /norestart"

# Start-Process with -Wait ensures the script pauses until msiexec is completely finished
$installProcess = Start-Process -FilePath "msiexec.exe" -ArgumentList $installArgs -Wait -PassThru

# 5. Verify and Clean Up
Write-Host "`n[3/3] Verifying and cleaning up..." -ForegroundColor Yellow
if ($installProcess.ExitCode -eq 0) {
    Write-Host "SUCCESS: WinFSP installed correctly." -ForegroundColor Green
} else {
    Write-Error "WARNING: Installation completed with a non-zero exit code: $($installProcess.ExitCode)"
}

# Delete the downloaded MSI to free up space
if (Test-Path $tempPath) {
    Remove-Item -Path $tempPath -Force
    Write-Host "Temporary installation files removed." -ForegroundColor DarkGray
}

# ==============================================================================
# 6. Post-Installation UI Recovery (Smart Check)
# ==============================================================================
Write-Host "`n[4/4] Rebuilding Windows 11 Desktop Environment..." -ForegroundColor Yellow

# Forcefully kill the desktop and modern taskbar hosts
Stop-Process -Name "explorer" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "StartMenuExperienceHost" -Force -ErrorAction SilentlyContinue

# Give Windows 3 seconds to trigger its own AutoRestartShell protocol
Start-Sleep -Seconds 3

# Check if Windows successfully auto-restarted the shell
if (-not (Get-Process -Name "explorer" -ErrorAction SilentlyContinue)) {
    Write-Host "Windows failed to auto-restart the shell. Forcing manual boot..." -ForegroundColor Cyan
    Start-Process "explorer.exe"
} else {
    Write-Host "Windows automatically revived the shell. Skipping manual boot to prevent folder popup." -ForegroundColor Cyan
}

Write-Host "Taskbar and Desktop successfully restored." -ForegroundColor Green
Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "WinFSP Setup Finished Completely." -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

Import-Certificate -FilePath "rescuebox.cer" -CertStoreLocation Cert:\LocalMachine\Root

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "SUCCESS: Windows Environment is ready." -ForegroundColor Cyan
Write-Host "You can now install rescuebox" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan