$ErrorActionPreference = 'Stop'
$body = @{ email='demo@opspilot.ai'; password='demo' } | ConvertTo-Json
$resp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -ContentType 'application/json' -Body $body
if (-not $resp.access_token) { Write-Error 'NO_TOKEN'; exit 1 }
$headers = @{ Authorization = "Bearer $($resp.access_token)" }
$res = Invoke-RestMethod -Method Post -Headers $headers -Uri http://127.0.0.1:8000/demo/auto
$res | ConvertTo-Json -Depth 8

