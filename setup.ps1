# Verify python is installed
if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed!" -ForegroundColor Red
    exit 1
}
Write-Host "Python 3 found: $((Get-Command python3).Source)"

# Check for existing virtual environment
if (Test-Path ./venv -PathType Container) {
    Write-Host "venv exists"
} else {
    Write-Host "venv does not exist. Creating now..." -ForegroundColor Yellow
    python3 -m venv ./venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "venv creation failed." -ForegroundColor Red
        exit 1
    }
}

# Resolve the venv python executable (Windows layout)
$venvPython = "./venv/Scripts/python.exe"

# Check that Selenium is installed
& $venvPython -m pip show selenium *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Selenium is installed. Skipping installation..." -ForegroundColor Green
} else {
    # Install if missing
    Write-Host "Selenium is not installed. Installing now..." -ForegroundColor Yellow
    & $venvPython -m pip install selenium
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error installing Selenium!" -ForegroundColor Red
        exit 1
    }
}

# Success
Write-Host "Environment successfully setup." -ForegroundColor Green
Write-Host "To run the scripts, activate the venv with: .\venv\Scripts\Activate.ps1"
