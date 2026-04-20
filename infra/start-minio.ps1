param(
    [switch]$Background,
    [string]$StdoutPath,
    [string]$StderrPath,
    [int]$WaitSeconds = 10
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$binaryDir = Join-Path $root ".tools\\minio"
$binary = Join-Path $binaryDir "minio.exe"
$dataDir = Join-Path $root "infra\\minio-data"
$healthUrl = "http://127.0.0.1:9000/minio/health/live"

if (-not (Test-Path $binary)) {
    throw "MinIO binary not found at $binary. Download minio.exe there first."
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if (-not $Background) {
    $env:MINIO_ROOT_USER = "myflightbook"
    $env:MINIO_ROOT_PASSWORD = "myflightbook"
    & $binary server $dataDir --console-address ":9001"
    exit $LASTEXITCODE
}

$existing = Get-CimInstance Win32_Process -Filter "name = 'minio.exe'" | Where-Object {
    $_.CommandLine -like "*$dataDir*"
} | Select-Object -First 1

if ($existing) {
    [pscustomobject]@{
        MinioProcessId = $existing.ProcessId
        HealthUrl = $healthUrl
        DataDirectory = $dataDir
        AlreadyRunning = $true
    }
    return
}

if ($StdoutPath) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StdoutPath) | Out-Null
}

if ($StderrPath) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StderrPath) | Out-Null
}

$powershell = Join-Path $env:WINDIR "System32\\WindowsPowerShell\\v1.0\\powershell.exe"
$command = '$env:MINIO_ROOT_USER=''myflightbook''; $env:MINIO_ROOT_PASSWORD=''myflightbook''; & ''' + $binary + ''' server ''' + $dataDir + ''' --console-address '':9001'''
$startInfo = @{
    FilePath = $powershell
    ArgumentList = @("-NoProfile", "-Command", $command)
    PassThru = $true
}

if ($StdoutPath) {
    $startInfo.RedirectStandardOutput = $StdoutPath
}

if ($StderrPath) {
    $startInfo.RedirectStandardError = $StderrPath
}

$wrapper = Start-Process @startInfo
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$minio = $null

do {
    Start-Sleep -Milliseconds 500
    $minio = Get-CimInstance Win32_Process -Filter "name = 'minio.exe'" | Where-Object {
        $_.CommandLine -like "*$dataDir*"
    } | Select-Object -First 1

    if ($minio) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                break
            }
        } catch {
        }
    }
} while ((Get-Date) -lt $deadline)

if (-not $minio) {
    throw "MinIO failed to start for data directory $dataDir."
}

[pscustomobject]@{
    WrapperProcessId = $wrapper.Id
    MinioProcessId = $minio.ProcessId
    HealthUrl = $healthUrl
    DataDirectory = $dataDir
    AlreadyRunning = $false
}
