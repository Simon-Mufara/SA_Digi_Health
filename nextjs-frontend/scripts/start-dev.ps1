$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Kill any Next.js process tied to this workspace to avoid stale runtime/chunk errors.
$workspaceToken = "\\OneDrive\\Documents\\YARA\\nextjs-frontend"
$targets = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -ieq "node.exe" -or $_.Name -ieq "cmd.exe" -or $_.Name -ieq "pwsh.exe") -and
    $_.CommandLine -match "next dev|npm run dev|start-server\\.js|next-server|next start" -and
    $_.CommandLine -match [regex]::Escape($workspaceToken)
}

foreach ($proc in $targets) {
    try { Stop-Process -Id $proc.ProcessId -Force } catch {}
}

Start-Sleep -Seconds 1

if (Test-Path ".next") {
    Remove-Item ".next" -Recurse -Force
}

# Build once, then serve via next start for presentation stability.
$env:NODE_OPTIONS = "--max-old-space-size=6144"
$env:NEXT_DISABLE_SWC_WORKER = "1"
$env:NEXT_PRIVATE_BUILD_WORKER = "1"
$env:CI = "1"

Write-Host "Building South African DigiHealth in stable mode..."
& npx next build --no-lint
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$env:NODE_OPTIONS = "--max-old-space-size=4096"
Write-Host "Starting stable server on http://127.0.0.1:3100"
& npx next start -p 3100
