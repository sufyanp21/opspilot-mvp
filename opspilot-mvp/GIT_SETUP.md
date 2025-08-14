# OpsPilot MVP - Git & GitHub Setup Guide

This guide walks you through setting up version control and CI/CD for the OpsPilot MVP project.

## 🚀 Quick Setup (Automated)

Run the automated setup script:

```powershell
# From the project root directory
.\scripts\git_setup.ps1 -GitHubUsername "your-username" -RepoName "opspilot-mvp"

# For private repository
.\scripts\git_setup.ps1 -GitHubUsername "your-username" -Private
```

## 📋 Manual Setup Steps

### 1. One-time Git Configuration

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global core.autocrlf true  # Windows line endings
git config --global init.defaultBranch main
```

### 2. Initialize Repository

```bash
cd "C:\Users\sufya\OneDrive\Desktop\MVP\opspilot-mvp"
git init
git add .
git commit -m "feat: initial OpsPilot MVP implementation

- Complete FastAPI backend with PostgreSQL
- React + Vite + TypeScript frontend  
- ETD reconciliation with product-aware tolerances
- SPAN margin analysis with delta narratives
- OTC FpML processing for IRS/FX trades
- Exception clustering and SLA workflow
- Immutable audit trail and data lineage
- Comprehensive demo scripts and tests
- Production-ready CI/CD pipeline"
```

### 3. Create GitHub Repository

**Option A: GitHub CLI (Recommended)**
```bash
gh repo create opspilot-mvp --private --source=. --remote=origin --push --description "OpsPilot MVP - Derivatives Data Automation Platform"
```

**Option B: Manual via Browser**
1. Go to https://github.com/new
2. Repository name: `opspilot-mvp`
3. Description: `OpsPilot MVP - Derivatives Data Automation Platform`
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

Then connect your local repo:
```bash
git remote add origin https://github.com/YOUR-USERNAME/opspilot-mvp.git
git branch -M main
git push -u origin main
```

### 4. Set up Development Branch

```bash
git checkout -b develop
git push -u origin develop
git checkout main
```

### 5. Configure Git LFS (Large File Support)

```bash
git lfs install
git lfs track "*.csv"
git lfs track "*.xlsx" 
git lfs track "*.pdf"
git lfs track "*.zip"
git lfs track "demo_data/**"
git add .gitattributes
git commit -m "chore: configure Git LFS for large files"
git push
```

## 🔐 GitHub Secrets Configuration

For CI/CD to work, add these secrets to your GitHub repository:

**Go to:** `https://github.com/YOUR-USERNAME/opspilot-mvp/settings/secrets/actions`

### Required Secrets:
- `DATABASE_URL` - PostgreSQL connection for production
- `REDIS_URL` - Redis connection for production

### Optional Secrets (for deployment):
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
- `SLACK_WEBHOOK` - Slack webhook for notifications

## 🏗️ CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) includes:

### 🧪 **Backend Tests**
- Python 3.11 with PostgreSQL 16 & Redis 7
- Linting with flake8
- Unit tests with pytest and coverage
- Integration tests
- Database migrations

### 🎨 **Frontend Tests**  
- Node.js 18 with npm
- TypeScript type checking
- ESLint linting
- Unit tests with Vitest
- Production build verification

### 🔄 **End-to-End Tests**
- Full stack integration testing
- Demo workflow validation
- API endpoint testing
- Performance benchmarks

### 🔒 **Security Scanning**
- Trivy vulnerability scanner
- SARIF report upload
- Dependency security checks

### 🚀 **Deployment** (main branch only)
- Docker image builds
- Container registry push
- Staging deployment
- Smoke tests
- Slack notifications

## 🌿 Git Workflow

### Branch Strategy:
```
main (production) ← PR ← develop ← PR ← feature/branch-name
```

### Development Workflow:
1. **Create feature branch** from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push -u origin feature/your-feature-name
   ```

3. **Create Pull Request** to `develop`:
   ```bash
   # Using GitHub CLI
   gh pr create --base develop --title "Add new feature" --body "Description of changes"
   
   # Or via GitHub web interface
   ```

4. **Merge to develop** after review and tests pass

5. **Release to main**:
   ```bash
   # Create PR from develop to main
   gh pr create --base main --head develop --title "Release v1.0.0"
   ```

## 📊 Repository Structure

```
opspilot-mvp/
├── .github/workflows/     # CI/CD pipelines
├── .gitignore            # Comprehensive ignore rules
├── apps/
│   ├── backend/          # FastAPI application
│   └── frontend/         # React + Vite application
├── scripts/              # Setup and utility scripts
├── tests/                # Test suites
├── demo_data/           # Generated demo files (ignored)
├── GIT_SETUP.md         # This guide
└── README.md            # Project documentation
```

## 🔧 Useful Git Commands

### Daily Development:
```bash
# Check status
git status

# Switch branches  
git checkout develop
git checkout main

# Create and switch to new branch
git checkout -b feature/new-feature

# Stage and commit changes
git add .
git commit -m "type: description"

# Push changes
git push
git push -u origin feature/new-feature  # First push of new branch

# Pull latest changes
git pull
git pull origin develop
```

### Commit Message Convention:
- `feat:` - New features
- `fix:` - Bug fixes  
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Branch Management:
```bash
# List branches
git branch -a

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# Sync with remote
git fetch --prune
```

## 🚨 Troubleshooting

### OneDrive Issues:
- Pause OneDrive sync during large commits
- Use `git config --global core.autocrlf true` for Windows

### Large Files:
- Use Git LFS for files > 100MB
- Check `.gitattributes` for LFS tracking

### CI/CD Failures:
- Check GitHub Actions logs
- Verify secrets are configured
- Ensure database migrations run

### Authentication:
```bash
# Use personal access token for HTTPS
git remote set-url origin https://YOUR-TOKEN@github.com/USERNAME/REPO.git

# Or use SSH keys
git remote set-url origin git@github.com:USERNAME/REPO.git
```

## 🎯 Best Practices

1. **Never commit secrets** - Use `.env.example` templates
2. **Write descriptive commit messages** - Follow conventional commits
3. **Use Pull Requests** - Enable code reviews and CI checks
4. **Keep branches focused** - One feature per branch
5. **Test before pushing** - Run tests locally first
6. **Update documentation** - Keep README and docs current
7. **Use semantic versioning** - Tag releases (v1.0.0, v1.1.0, etc.)

## 📞 Support

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share ideas  
- **Wiki**: Detailed documentation and guides
- **Actions**: Monitor CI/CD pipeline status

---

**🎉 Happy coding with OpsPilot MVP!** 🚀
