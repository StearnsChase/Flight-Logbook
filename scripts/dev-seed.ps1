$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$apiDir = Join-Path $root "apps\\api"
$apiPython = Join-Path $apiDir ".venv\\Scripts\\python.exe"

if (-not (Test-Path $apiPython)) {
    throw "Missing API virtualenv at $apiPython"
}

Push-Location $apiDir
try {
    & $apiPython -m myflightbook_api.jobs.seed_demo
} finally {
    Pop-Location
}
