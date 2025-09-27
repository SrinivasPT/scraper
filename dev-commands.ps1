# RegScraper Development Scripts
# Usage: .\dev-commands.ps1 <command>

param(
    [Parameter(Mandatory=$true)]
    [string]$Command
)

function Install-Dev {
    Write-Host "Installing development dependencies..." -ForegroundColor Green
    py -m pip install -e .
    py -m pip install ruff pytest pytest-asyncio pytest-cov
}

function Run-Lint {
    Write-Host "Running linter..." -ForegroundColor Blue
    py -m ruff check src/ tests/
}

function Fix-Lint {
    Write-Host "Fixing lint issues..." -ForegroundColor Yellow
    py -m ruff check --fix --unsafe-fixes src/ tests/
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Cyan
    py -m ruff format src/ tests/
}

function Check-Code {
    Write-Host "Running full code check..." -ForegroundColor Magenta
    Format-Code
    Run-Lint
}

function Run-Tests {
    Write-Host "Running tests..." -ForegroundColor Green
    py -m pytest tests/ -v
}

function Run-TestsCov {
    Write-Host "Running tests with coverage..." -ForegroundColor Green
    py -m pytest tests/ -v --cov=regscraper --cov-report=html --cov-report=term
}

function Clean-Cache {
    Write-Host "Cleaning cache directories..." -ForegroundColor Red
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
    if (Test-Path ".pytest_cache") { Remove-Item ".pytest_cache" -Recurse -Force }
    if (Test-Path ".ruff_cache") { Remove-Item ".ruff_cache" -Recurse -Force }
    if (Test-Path "htmlcov") { Remove-Item "htmlcov" -Recurse -Force }
    Write-Host "Clean complete!" -ForegroundColor Green
}

function Dev-Setup {
    Write-Host "Setting up development environment..." -ForegroundColor Green
    Install-Dev
    Fix-Lint
    Run-Tests
    Write-Host "Development setup complete!" -ForegroundColor Green
}

function Show-Help {
    Write-Host @"
RegScraper Development Commands:

  install-dev    - Install development dependencies
  lint          - Run linter
  fix           - Fix lint issues automatically
  format        - Format code with Ruff
  check         - Run lint and format
  test          - Run tests
  test-cov      - Run tests with coverage
  clean         - Clean cache directories
  setup         - Complete development setup
  help          - Show this help

Usage: .\dev-commands.ps1 <command>
Example: .\dev-commands.ps1 setup
"@ -ForegroundColor White
}

# Main command switch
switch ($Command.ToLower()) {
    "install-dev" { Install-Dev }
    "lint" { Run-Lint }
    "fix" { Fix-Lint }
    "format" { Format-Code }
    "check" { Check-Code }
    "test" { Run-Tests }
    "test-cov" { Run-TestsCov }
    "clean" { Clean-Cache }
    "setup" { Dev-Setup }
    "help" { Show-Help }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
    }
}
