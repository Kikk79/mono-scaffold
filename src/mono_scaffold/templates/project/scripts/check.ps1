# Qualitäts-Gate vor jedem Merge (Windows): ruff, Modulgrenzen (import-linter), Tests.
# Alle Schritte laufen auch nach einem Fehler weiter; Exit-Code 1, sobald einer scheitert.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

$failed = @()
function Run-Step {
    param([string]$Label, [string[]]$Command)
    Write-Host "==> $Label`: $($Command -join ' ')"
    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -eq 0) { Write-Host "==> $Label`: OK" } else { Write-Host "==> $Label`: FEHLGESCHLAGEN"; $script:failed += $Label }
    Write-Host ""
}

Run-Step "ruff" @("uv", "run", "ruff", "check", "app", "tests", "scripts", "alembic")
Run-Step "lint-imports" @("uv", "run", "lint-imports", "--no-cache")
Run-Step "pytest" @("uv", "run", "pytest", "-q")
if (Test-Path "frontend") {
    Push-Location frontend
    Run-Step "frontend-test" @("bun", "test")
    Pop-Location
}

if ($failed.Count -gt 0) {
    Write-Host "check.ps1: fehlgeschlagen: $($failed -join ', ')"
    exit 1
}
Write-Host "check.ps1: alle Prüfungen grün"
exit 0
