param(
    [string]$Root = "apps"
)

$excludedPatterns = @(
    "\\.venv($|\\)",
    "\\.next($|\\)",
    "\\node_modules($|\\)",
    "\\.pytest_cache($|\\)",
    "\\pytest-cache-files-[^\\]+($|\\)"
)

Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $fullName = $_.FullName
        foreach ($pattern in $excludedPatterns) {
            if ($fullName -match $pattern) {
                return $false
            }
        }
        return $true
    } |
    Select-String -Pattern 'TODO\s*\(Codex\)(\[[^\]]*\])?:' |
    ForEach-Object {
        $relativePath = Resolve-Path -Relative $_.Path
        $line = $_.Line.Trim()
        $sliceId = ""
        if ($line -match 'TODO\s*\(Codex\)\[([^\]]+)\]:') {
            $sliceId = $Matches[1]
        }
        "{0}:{1}:[{2}] {3}" -f $relativePath, $_.LineNumber, $sliceId, $line
    }
