$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$apiDir = Join-Path $root "apps\\api"

function Get-RepoApiProcesses {
    Get-CimInstance Win32_Process -Filter "name = 'python.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.Contains($apiDir) -and $_.CommandLine.Contains("myflightbook_api.main:app")
    }
}

function Get-RepoWebProcesses {
    Get-CimInstance Win32_Process -Filter "name = 'node.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.Contains($root) -and (
            ($_.CommandLine.Contains("next\\dist\\bin\\next") -and $_.CommandLine.Contains("dev")) -or
            ($_.CommandLine.Contains("npm-cli.js") -and $_.CommandLine.Contains("@myflightbook/web"))
        )
    }
}

function Get-RepoMinioProcesses {
    Get-CimInstance Win32_Process -Filter "name = 'minio.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.Contains($root)
    }
}

function Get-ProcessesByPorts {
    param(
        [int[]]$Ports
    )

    $processIds = foreach ($port in $Ports) {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess
    }

    if (-not $processIds) {
        return @()
    }

    Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -in ($processIds | Select-Object -Unique)
    }
}

$apiProcesses = Get-RepoApiProcesses
$webProcesses = Get-RepoWebProcesses
$minioProcesses = Get-RepoMinioProcesses

if (-not $apiProcesses) {
    $apiProcesses = Get-ProcessesByPorts -Ports @(8000)
}

if (-not $webProcesses) {
    $webProcesses = Get-ProcessesByPorts -Ports @(3000)
}

if (-not $minioProcesses) {
    $minioProcesses = Get-ProcessesByPorts -Ports @(9000, 9001)
}

foreach ($process in @($webProcesses + $apiProcesses + $minioProcesses)) {
    if ($process) {
        Stop-Process -Id $process.ProcessId -Force
    }
}

[pscustomobject]@{
    stopped_web = @($webProcesses).Count
    stopped_api = @($apiProcesses).Count
    stopped_minio = @($minioProcesses).Count
}
