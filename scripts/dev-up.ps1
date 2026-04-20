param(
    [switch]$Seed
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$apiDir = Join-Path $root "apps\\api"
$webDir = Join-Path $root "apps\\web"
$logDir = Join-Path $root ".tools\\logs"
$apiPython = Join-Path $apiDir ".venv\\Scripts\\python.exe"
$npm = Join-Path $env:ProgramFiles "nodejs\\npm.cmd"
$minioStdout = Join-Path $logDir "minio-stdout.log"
$minioStderr = Join-Path $logDir "minio-stderr.log"
$apiStdout = Join-Path $logDir "uvicorn-stdout.log"
$apiStderr = Join-Path $logDir "uvicorn-stderr.log"
$webStdout = Join-Path $logDir "next-dev-stdout.log"
$webStderr = Join-Path $logDir "next-dev-stderr.log"

function Ensure-FileFromExample {
    param(
        [string]$TargetPath,
        [string]$ExamplePath
    )

    if (-not (Test-Path $TargetPath)) {
        Copy-Item -LiteralPath $ExamplePath -Destination $TargetPath
    }
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return
            }
        } catch {
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    throw "Timed out waiting for $Url"
}

function Test-HttpOk {
    param(
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Test-Path $apiPython)) {
    throw "Missing API virtualenv at $apiPython"
}

if (-not (Test-Path $npm)) {
    throw "npm was not found at $npm"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Ensure-FileFromExample -TargetPath (Join-Path $apiDir ".env") -ExamplePath (Join-Path $apiDir ".env.example")
Ensure-FileFromExample -TargetPath (Join-Path $webDir ".env.local") -ExamplePath (Join-Path $webDir ".env.example")

$postgresService = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if ($postgresService -and $postgresService.Status -ne "Running") {
    Start-Service -Name $postgresService.Name
    $postgresService.WaitForStatus("Running", [TimeSpan]::FromSeconds(15))
}

Push-Location $apiDir
try {
    & $apiPython -m alembic upgrade head
} finally {
    Pop-Location
}

& (Join-Path $root "infra\\start-minio.ps1") -Background -StdoutPath $minioStdout -StderrPath $minioStderr | Out-Null
Wait-HttpOk -Url "http://127.0.0.1:9000/minio/health/live"

if (-not (Test-HttpOk -Url "http://127.0.0.1:8000/healthz")) {
    if (Test-Path $apiStdout) { Remove-Item -LiteralPath $apiStdout -Force }
    if (Test-Path $apiStderr) { Remove-Item -LiteralPath $apiStderr -Force }
    Start-Process -FilePath $apiPython `
        -ArgumentList @("-m", "uvicorn", "myflightbook_api.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $apiDir `
        -RedirectStandardOutput $apiStdout `
        -RedirectStandardError $apiStderr | Out-Null
}

Wait-HttpOk -Url "http://127.0.0.1:8000/healthz"

if (-not (Test-HttpOk -Url "http://127.0.0.1:3000/api/health")) {
    if (Test-Path $webStdout) { Remove-Item -LiteralPath $webStdout -Force }
    if (Test-Path $webStderr) { Remove-Item -LiteralPath $webStderr -Force }
    Start-Process -FilePath $npm `
        -ArgumentList @("run", "dev", "--workspace", "@myflightbook/web", "--", "--hostname", "127.0.0.1") `
        -WorkingDirectory $root `
        -RedirectStandardOutput $webStdout `
        -RedirectStandardError $webStderr | Out-Null
}

Wait-HttpOk -Url "http://127.0.0.1:3000/api/health"

if ($Seed) {
    & (Join-Path $PSScriptRoot "dev-seed.ps1")
}

[pscustomobject]@{
    postgres = if ($postgresService) { $postgresService.Status } else { "external" }
    minio = "http://127.0.0.1:9000"
    api = "http://127.0.0.1:8000"
    web = "http://127.0.0.1:3000"
    seeded = [bool]$Seed
}
