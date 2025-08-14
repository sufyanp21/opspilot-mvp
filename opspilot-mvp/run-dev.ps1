# Simple Development Setup (No Docker Required)
param(
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "OpsPilot MVP - Simple Development Mode" -ForegroundColor Green
    Write-Host "This runs the app without Docker for testing" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  help        Show this help message"
    Write-Host "  check       Check if you have Python and Node.js"
    Write-Host "  install     Install dependencies"
    Write-Host "  backend     Start just the backend (API)"
    Write-Host "  frontend    Start just the frontend (website)"
    Write-Host "  both        Start both backend and frontend"
}

function Check-Requirements {
    Write-Host "Checking requirements..." -ForegroundColor Yellow
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Python not found. Please install Python 3.11+ from python.org" -ForegroundColor Red
        return $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        Write-Host "✅ Found Node.js: $nodeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Node.js not found. Please install Node.js from nodejs.org" -ForegroundColor Red
        return $false
    }
    
    # Check npm
    try {
        $npmVersion = npm --version 2>&1
        Write-Host "✅ Found npm: $npmVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ npm not found" -ForegroundColor Red
        return $false
    }
    
    return $true
}

function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    
    # Install backend dependencies
    Write-Host "Installing Python packages..." -ForegroundColor Cyan
    Set-Location "apps/backend"
    pip install -r requirements.txt
    Set-Location "../.."
    
    # Install frontend dependencies
    Write-Host "Installing Node.js packages..." -ForegroundColor Cyan
    Set-Location "apps/frontend"
    npm install
    Set-Location "../.."
    
    Write-Host "Dependencies installed!" -ForegroundColor Green
}

function Start-Backend {
    Write-Host "Starting Backend API..." -ForegroundColor Green
    Write-Host "This will run on http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    
    Set-Location "apps/backend"
    
    # Set environment variables for development
    $env:DATABASE_URL = "sqlite:///./opspilot.db"
    $env:APP_ENV = "dev"
    
    # Start the backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

function Start-Frontend {
    Write-Host "Starting Frontend Website..." -ForegroundColor Green
    Write-Host "This will run on http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    
    Set-Location "apps/frontend"
    npm run dev
}

function Start-Both {
    Write-Host "Starting both Backend and Frontend..." -ForegroundColor Green
    Write-Host ""
    Write-Host "You'll need to open TWO PowerShell windows:" -ForegroundColor Yellow
    Write-Host "1. In first window: .\run-dev.ps1 backend" -ForegroundColor Cyan
    Write-Host "2. In second window: .\run-dev.ps1 frontend" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use Docker if it's working: .\setup.ps1 demo" -ForegroundColor Magenta
}

# Main script logic
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "check" { Check-Requirements }
    "install" { Install-Dependencies }
    "backend" { Start-Backend }
    "frontend" { Start-Frontend }
    "both" { Start-Both }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
