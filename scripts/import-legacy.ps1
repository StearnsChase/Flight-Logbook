param(
    [int]$LimitUsers = 25,
    [int]$LimitFlights = 5000,
    [string]$Username
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$apiDir = Join-Path $root "apps\\api"
$apiPython = Join-Path $apiDir ".venv\\Scripts\\python.exe"

if (-not (Test-Path $apiPython)) {
    throw "Missing API virtualenv at $apiPython"
}

$arguments = @("-m", "myflightbook_api.jobs.import_legacy_core", "--limit-users", $LimitUsers, "--limit-flights", $LimitFlights)
if ($Username) {
    $arguments += @("--username", $Username)
}

Push-Location $apiDir
try {
    & $apiPython @arguments
} finally {
    Pop-Location
}
