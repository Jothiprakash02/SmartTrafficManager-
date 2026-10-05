$ErrorActionPreference = "Stop"

$services = @("mosquitto", "influxdb", "simulator", "opcua-simulator", "opcua-bridge", "nodered", "grafana", "web")
$checks = @(
    @{ Name = "Traffic web app"; Url = "http://localhost:8000/" },
    @{ Name = "Node-RED"; Url = "http://localhost:1880/" },
    @{ Name = "InfluxDB"; Url = "http://localhost:8086/health" },
    @{ Name = "Grafana"; Url = "http://localhost:3000/api/health" }
)

function Invoke-RequiredCommand {
    param([string]$Description, [scriptblock]$Command)

    Write-Host "[startup] $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Startup step failed: $Description"
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found. Install Docker Desktop and start its Linux engine."
}

Invoke-RequiredCommand "Checking Docker engine" { docker info }
Invoke-RequiredCommand "Validating Compose configuration" { docker compose config --quiet }
Invoke-RequiredCommand "Building and starting services" { docker compose up --build --wait --wait-timeout 120 -d }

foreach ($service in $services) {
    $containerId = (docker compose ps -q $service).Trim()
    if (-not $containerId) {
        throw "Service '$service' did not create a container."
    }

    $container = docker inspect $containerId | ConvertFrom-Json
    $state = $container[0].State
    if ($state.Status -ne "running") {
        throw "Service '$service' is not running. Current status: $($state.Status)"
    }

    if ($null -ne $state.Health -and $state.Health.Status -ne "healthy") {
        throw "Service '$service' is not healthy. Current health: $($state.Health.Status)"
    }

    Write-Host "[ready] $service is running" -ForegroundColor Green
}

foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
            throw "HTTP $($response.StatusCode)"
        }
        Write-Host "[ready] $($check.Name) responded at $($check.Url)" -ForegroundColor Green
    }
    catch {
        throw "Endpoint check failed for $($check.Name) at $($check.Url): $($_.Exception.Message)"
    }
}

Write-Host "[startup] All traffic-edge services passed their checks." -ForegroundColor Green
Write-Host "[startup] Opening http://localhost:8000" -ForegroundColor Cyan
Start-Process "http://localhost:8000"