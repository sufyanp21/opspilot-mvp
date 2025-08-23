$ErrorActionPreference = 'Stop'
$loginBody = @{ email='demo+admin@opspilot.ai'; password='demo' } | ConvertTo-Json
$loginResp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -ContentType 'application/json' -Body $loginBody
if (-not $loginResp.access_token) { Write-Error 'NO_TOKEN'; exit 1 }
$headers = @{ Authorization = "Bearer $($loginResp.access_token)" }
$train = Invoke-RestMethod -Method Post -Headers $headers -Uri http://127.0.0.1:8000/ml/train/predict-breaks
$train | ConvertTo-Json -Depth 6
$score = Invoke-RestMethod -Method Post -Headers $headers -Uri "http://127.0.0.1:8000/ml/score/predict-breaks?runId=DEMO_RUN_1"
$score | ConvertTo-Json -Depth 6
