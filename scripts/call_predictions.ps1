$ErrorActionPreference = 'Stop'
$loginBody = @{ email='demo+admin@opspilot.ai'; password='demo' } | ConvertTo-Json
$resp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -ContentType 'application/json' -Body $loginBody
if (-not $resp.access_token) { Write-Error 'NO_TOKEN'; exit 1 }
$headers = @{ Authorization = "Bearer $($resp.access_token)" }
$preds = Invoke-RestMethod -Method Get -Headers $headers -Uri http://127.0.0.1:8000/runs/DEMO_RUN_1/predictions
$preds | ConvertTo-Json -Depth 6
