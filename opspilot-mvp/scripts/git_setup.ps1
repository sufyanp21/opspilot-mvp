# OpsPilot MVP - Git Setup Script
# PowerShell script to initialize Git repository and set up GitHub

param(
    [string]$GitHubUsername = "",
    [string]$RepoName = "opspilot-mvp",
    [switch]$Private = $false,
    [switch]$SkipGitHubCLI = $false
)

Write-Host "🚀 OpsPilot MVP - Git Setup Script" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if we're in the right directory
$currentDir = Get-Location
if (-not (Test-Path "apps/backend") -or -not (Test-Path "apps/frontend")) {
    Write-Host "❌ Error: Please run this script from the OpsPilot MVP root directory" -ForegroundColor Red
    Write-Host "Expected structure: apps/backend/ and apps/frontend/" -ForegroundColor Yellow
    exit 1
}

# Step 1: Git Configuration
Write-Host "`n📝 Step 1: Git Configuration" -ForegroundColor Green

$gitUserName = git config --global user.name
$gitUserEmail = git config --global user.email

if (-not $gitUserName) {
    $userName = Read-Host "Enter your Git username"
    git config --global user.name "$userName"
    Write-Host "✅ Set Git username: $userName" -ForegroundColor Green
} else {
    Write-Host "✅ Git username already set: $gitUserName" -ForegroundColor Green
}

if (-not $gitUserEmail) {
    $userEmail = Read-Host "Enter your Git email"
    git config --global user.email "$userEmail"
    Write-Host "✅ Set Git email: $userEmail" -ForegroundColor Green
} else {
    Write-Host "✅ Git email already set: $gitUserEmail" -ForegroundColor Green
}

# Set Windows-specific Git settings
git config --global core.autocrlf true
git config --global init.defaultBranch main
Write-Host "✅ Configured Windows-specific Git settings" -ForegroundColor Green

# Step 2: Initialize Git Repository
Write-Host "`n🔧 Step 2: Initialize Git Repository" -ForegroundColor Green

if (-not (Test-Path ".git")) {
    git init
    Write-Host "✅ Initialized Git repository" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already initialized" -ForegroundColor Green
}

# Step 3: Add and Commit Files
Write-Host "`n📁 Step 3: Add and Commit Files" -ForegroundColor Green

# Check if there are any commits
$hasCommits = git rev-parse --verify HEAD 2>$null
if (-not $hasCommits) {
    Write-Host "Adding files to Git..." -ForegroundColor Yellow
    git add .
    
    $commitMessage = "feat: initial OpsPilot MVP implementation

- Complete FastAPI backend with PostgreSQL
- React + Vite + TypeScript frontend
- ETD reconciliation with product-aware tolerances
- SPAN margin analysis with delta narratives
- OTC FpML processing for IRS/FX trades
- Exception clustering and SLA workflow
- Immutable audit trail and data lineage
- Comprehensive demo scripts and tests
- Production-ready CI/CD pipeline"

    git commit -m "$commitMessage"
    Write-Host "✅ Created initial commit" -ForegroundColor Green
} else {
    Write-Host "✅ Repository already has commits" -ForegroundColor Green
}

# Step 4: Create GitHub Repository
Write-Host "`n🌐 Step 4: Create GitHub Repository" -ForegroundColor Green

if (-not $GitHubUsername) {
    $GitHubUsername = Read-Host "Enter your GitHub username"
}

$repoUrl = "https://github.com/$GitHubUsername/$RepoName.git"

# Check if GitHub CLI is available and not skipped
$useGitHubCLI = $false
if (-not $SkipGitHubCLI) {
    try {
        $ghVersion = gh --version 2>$null
        if ($ghVersion) {
            $useGitHubCLI = $true
            Write-Host "✅ GitHub CLI detected" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ GitHub CLI not found - will use manual setup" -ForegroundColor Yellow
    }
}

if ($useGitHubCLI) {
    Write-Host "Creating GitHub repository using GitHub CLI..." -ForegroundColor Yellow
    
    $visibility = if ($Private) { "--private" } else { "--public" }
    $description = "OpsPilot MVP - Derivatives Data Automation Platform with ETD reconciliation, SPAN analysis, OTC processing, and audit trails"
    
    try {
        gh repo create $RepoName $visibility --source=. --remote=origin --push --description "$description"
        Write-Host "✅ GitHub repository created and pushed!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to create repository with GitHub CLI" -ForegroundColor Red
        Write-Host "Please create the repository manually at: https://github.com/new" -ForegroundColor Yellow
        $useGitHubCLI = $false
    }
}

if (-not $useGitHubCLI) {
    Write-Host "`n📋 Manual GitHub Setup Instructions:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/new" -ForegroundColor White
    Write-Host "2. Repository name: $RepoName" -ForegroundColor White
    Write-Host "3. Description: OpsPilot MVP - Derivatives Data Automation Platform" -ForegroundColor White
    Write-Host "4. Choose Public or Private" -ForegroundColor White
    Write-Host "5. DO NOT initialize with README, .gitignore, or license" -ForegroundColor White
    Write-Host "6. Click 'Create repository'" -ForegroundColor White
    
    Read-Host "`nPress Enter after creating the GitHub repository..."
    
    # Add remote and push
    Write-Host "`nAdding remote and pushing..." -ForegroundColor Yellow
    
    try {
        git remote add origin $repoUrl
        git branch -M main
        git push -u origin main
        Write-Host "✅ Repository pushed to GitHub!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to push to GitHub" -ForegroundColor Red
        Write-Host "Please check your repository URL and credentials" -ForegroundColor Yellow
    }
}

# Step 5: Create Development Branch
Write-Host "`n🌿 Step 5: Create Development Branch" -ForegroundColor Green

try {
    git checkout -b develop
    git push -u origin develop
    Write-Host "✅ Created and pushed 'develop' branch" -ForegroundColor Green
    
    # Switch back to main
    git checkout main
} catch {
    Write-Host "⚠️ Could not create develop branch (may already exist)" -ForegroundColor Yellow
}

# Step 6: Set up Git LFS (for large files)
Write-Host "`n📦 Step 6: Set up Git LFS" -ForegroundColor Green

try {
    git lfs install
    
    # Track common large file types
    git lfs track "*.csv"
    git lfs track "*.xlsx"
    git lfs track "*.pdf"
    git lfs track "*.zip"
    git lfs track "*.tar.gz"
    git lfs track "demo_data/**"
    
    if (Test-Path ".gitattributes") {
        git add .gitattributes
        git commit -m "chore: configure Git LFS for large files"
        git push
        Write-Host "✅ Git LFS configured for large files" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Git LFS not available - large files will be tracked normally" -ForegroundColor Yellow
}

# Step 7: GitHub Secrets Setup
Write-Host "`n🔐 Step 7: GitHub Secrets Setup" -ForegroundColor Green
Write-Host "For CI/CD to work properly, add these secrets to your GitHub repository:" -ForegroundColor Yellow
Write-Host "Go to: https://github.com/$GitHubUsername/$RepoName/settings/secrets/actions" -ForegroundColor White

$secrets = @(
    "DATABASE_URL - PostgreSQL connection string for production",
    "REDIS_URL - Redis connection string for production", 
    "DOCKER_USERNAME - Docker Hub username (optional)",
    "DOCKER_PASSWORD - Docker Hub password (optional)",
    "SLACK_WEBHOOK - Slack webhook for notifications (optional)"
)

foreach ($secret in $secrets) {
    Write-Host "  • $secret" -ForegroundColor Cyan
}

# Step 8: Summary
Write-Host "`n" + "=" * 50
Write-Host "🎉 Git Setup Complete!" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📊 Repository Summary:" -ForegroundColor Cyan
Write-Host "  • Repository: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor White
Write-Host "  • Main branch: main (production)" -ForegroundColor White
Write-Host "  • Develop branch: develop (development)" -ForegroundColor White
Write-Host "  • CI/CD: GitHub Actions configured" -ForegroundColor White
Write-Host "  • Large files: Git LFS configured" -ForegroundColor White

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Set up GitHub secrets for CI/CD" -ForegroundColor White
Write-Host "  2. Create feature branches from 'develop'" -ForegroundColor White
Write-Host "  3. Use Pull Requests for code reviews" -ForegroundColor White
Write-Host "  4. Deploy from 'main' branch" -ForegroundColor White

Write-Host "`n💡 Workflow:" -ForegroundColor Cyan
Write-Host "  feature-branch → PR → develop → PR → main → deploy" -ForegroundColor White

Write-Host "`n🔗 Useful Commands:" -ForegroundColor Cyan
Write-Host "  git checkout develop          # Switch to develop branch" -ForegroundColor White
Write-Host "  git checkout -b feature/xyz   # Create feature branch" -ForegroundColor White
Write-Host "  git push -u origin feature/xyz # Push feature branch" -ForegroundColor White
Write-Host "  gh pr create                  # Create pull request (with GitHub CLI)" -ForegroundColor White

Write-Host "`nSetup complete! Happy coding! 🚀" -ForegroundColor Green
