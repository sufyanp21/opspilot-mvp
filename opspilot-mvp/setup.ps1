# OpsPilot MVP Setup Script for Windows
param(
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "OpsPilot MVP Setup Script" -ForegroundColor Green
    Write-Host "Usage: .\setup.ps1 [command]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  help        Show this help message"
    Write-Host "  setup       Initial project setup"
    Write-Host "  demo        Full demo setup with sample data"
    Write-Host "  start       Start the application"
    Write-Host "  stop        Stop the application"
    Write-Host "  logs        View application logs"
    Write-Host "  clean       Clean up containers and volumes"
}

function Setup-Project {
    Write-Host "Setting up OpsPilot MVP..." -ForegroundColor Green
    
    # Copy environment file
    if (!(Test-Path ".env")) {
        Copy-Item "infra\.env.example" ".env"
        Write-Host "Environment file created. Please update .env with your settings." -ForegroundColor Yellow
    }
    
    Write-Host "Setup complete! Run '.\setup.ps1 demo' to start the application." -ForegroundColor Green
}

function Start-Demo {
    Write-Host "Starting OpsPilot MVP Demo..." -ForegroundColor Green
    
    # Ensure environment file exists
    if (!(Test-Path ".env")) {
        Setup-Project
    }
    
    # Start Docker containers
    Write-Host "Starting Docker containers..." -ForegroundColor Yellow
    docker-compose -f infra/docker-compose.yml up -d --build
    
    # Wait for services to start
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Run database migrations
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    docker-compose -f infra/docker-compose.yml exec -T backend alembic upgrade head
    
    # Load sample data
    Write-Host "Loading sample data..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    try {
        $internalFile = Get-Item "sample_data/internal_trades.csv"
        $clearedFile = Get-Item "sample_data/cleared_trades.csv"
        $spanFile = Get-Item "sample_data/span_margins.csv"
        
        # Upload internal trades
        curl.exe -X POST -F "file=@$($internalFile.FullName)" -F "kind=internal" http://localhost:8000/api/v1/files/upload
        
        # Upload cleared trades  
        curl.exe -X POST -F "file=@$($clearedFile.FullName)" -F "kind=cleared" http://localhost:8000/api/v1/files/upload
        
        # Upload SPAN margins
        curl.exe -X POST -F "file=@$($spanFile.FullName)" -F "kind=span" http://localhost:8000/api/v1/files/upload
        
        Write-Host "Sample data loaded successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Note: Sample data upload may require manual upload through the UI" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🚀 OpsPilot MVP is ready!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Use '.\setup.ps1 logs' to view application logs" -ForegroundColor Yellow
    Write-Host "Use '.\setup.ps1 stop' to stop the application" -ForegroundColor Yellow
}

function Start-Application {
    Write-Host "Starting OpsPilot MVP..." -ForegroundColor Green
    docker-compose -f infra/docker-compose.yml up -d
    Write-Host "Application started!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
}

function Stop-Application {
    Write-Host "Stopping OpsPilot MVP..." -ForegroundColor Yellow
    docker-compose -f infra/docker-compose.yml down
    Write-Host "Application stopped!" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "Showing application logs..." -ForegroundColor Yellow
    docker-compose -f infra/docker-compose.yml logs -f
}

function Clean-Application {
    Write-Host "Cleaning up containers and volumes..." -ForegroundColor Yellow
    docker-compose -f infra/docker-compose.yml down -v
    docker system prune -f
    Write-Host "Cleanup complete!" -ForegroundColor Green
}

# Main script logic
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Setup-Project }
    "demo" { Start-Demo }
    "start" { Start-Application }
    "stop" { Stop-Application }
    "logs" { Show-Logs }
    "clean" { Clean-Application }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
