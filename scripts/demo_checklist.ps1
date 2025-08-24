# Windows PowerShell checklist to run OpsPilot demo
Write-Host "== OpsPilot Demo Checklist =="

Write-Host "1) Doctor script"
python scripts/demo_doctor.py
if ($LASTEXITCODE -ne 0) { Write-Error "Doctor checks failed. See artifacts/diagnostics/doctor_report.json"; exit 1 }

Write-Host "2) Seed demo data (optional)"
if (Test-Path opspilot-mvp\scripts\demo_seed.py) {
  python opspilot-mvp\scripts\demo_seed.py
}

Write-Host "3) Start backend"
powershell -NoLogo -NoProfile -Command "Push-Location backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" &

Start-Sleep -Seconds 2
try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing) | Out-Null } catch { Write-Error "Backend health failed"; exit 1 }

Write-Host "4) Start frontend"
powershell -NoLogo -NoProfile -Command "Push-Location apps/web; npm run dev" &

Write-Host "5) Open UI"
Start-Process http://localhost:5173/login



