param(
    [string]$Host = "wdlnds-pi",
    [string]$User = "qwert",
    [string]$RemoteDir = "",
    [string]$Service = "wdlnds-automat.service",
    [switch]$SkipInstall,
    [switch]$NoRestart
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$archive = Join-Path $env:TEMP "wdlnds_automat_deploy.zip"

if ([string]::IsNullOrWhiteSpace($RemoteDir)) {
    $RemoteDir = "/home/$User/wdlnds_automat"
}

Write-Host "[1/5] Build deployment archive..."
if (Test-Path $archive) {
    Remove-Item -Force $archive
}

$exclude = @(
    ".git",
    ".venv",
    "__pycache__",
    "*.pyc",
    "*.pyo"
)

$items = Get-ChildItem -Path $root -Recurse -File | Where-Object {
    $full = $_.FullName
    foreach ($pattern in $exclude) {
        if ($full -like "*$pattern*") {
            return $false
        }
    }
    return $true
}

if (-not $items) {
    throw "No files found to package."
}

$relativePaths = $items | ForEach-Object { $_.FullName.Substring($root.Length + 1) }
Push-Location $root
try {
    Compress-Archive -Path $relativePaths -DestinationPath $archive -Force
}
finally {
    Pop-Location
}

Write-Host "[2/5] Upload archive to Pi..."
scp $archive "${User}@${Host}:~/wdlnds_automat_deploy.zip"

Write-Host "[3/5] Extract project on Pi..."
ssh "${User}@${Host}" "mkdir -p '$RemoteDir' && unzip -oq ~/wdlnds_automat_deploy.zip -d '$RemoteDir'"

if (-not $SkipInstall) {
    Write-Host "[4/5] Ensure venv and install dependencies..."
    $installCmd = @"
if [ ! -d '$RemoteDir/.venv' ]; then
  python3 -m venv '$RemoteDir/.venv'
fi
'$RemoteDir/.venv/bin/python' -m pip install -r '$RemoteDir/requirements.txt'
"@
    ssh "${User}@${Host}" $installCmd
}
else {
    Write-Host "[4/5] Skip dependency install (--SkipInstall)."
}

if (-not $NoRestart) {
    Write-Host "[5/5] Restart service and print status..."
    ssh "${User}@${Host}" "sudo systemctl restart '$Service' && systemctl status '$Service' --no-pager"
}
else {
    Write-Host "[5/5] Skip service restart (--NoRestart)."
}

Write-Host "Done."
