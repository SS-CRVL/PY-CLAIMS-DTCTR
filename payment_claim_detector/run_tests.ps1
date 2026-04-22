# Run the package tests from the project root.
# Use PowerShell to run this script.

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"

if (-Not (Test-Path $venvPython)) {
    Write-Error "Virtual environment Python not found at $venvPython. Create the venv first."
    exit 1
}

Write-Host "Using Python: $venvPython"
& $venvPython -m pytest -q tests
