param(
    [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"

$services = @("mosquitto", "influxdb", "simulator", "nodered", "grafana", "web")

function Invoke-RequiredCommand {
    param([string]$Description, [scriptblock]$Command)

    Write-Host "[shutdown] $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Shutdown step failed: $Description"
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found. Install Docker Desktop before stopping the stack."
}

Invoke-RequiredCommand "Checking Docker engine" { docker info }
Invoke-RequiredCommand "Validating Compose configuration" { docker compose config --quiet }

$downArguments = @("compose", "down", "--remove-orphans")
if ($RemoveVolumes) {
    Write-Host "[shutdown] Volume removal requested. InfluxDB and Grafana history will be deleted." -ForegroundColor Yellow
    $downArguments += "--volumes"
}

Invoke-RequiredCommand "Stopping all traffic-edge services" { docker @downArguments }

$remainingContainers = @(docker compose ps -q)
if ($remainingContainers.Count -ne 0) {
    throw "Some traffic-edge containers are still present: $($remainingContainers -join ', ')"
}

Write-Host "[shutdown] Stopped services: $($services -join ', ')" -ForegroundColor Green
if ($RemoveVolumes) {
    Write-Host "[shutdown] Project volumes were removed." -ForegroundColor Yellow
}
else {
    Write-Host "[shutdown] Project volumes were preserved. Use -RemoveVolumes to delete stored data." -ForegroundColor Cyan
}