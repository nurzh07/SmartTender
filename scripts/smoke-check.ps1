$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== SmartTender smoke check =="

$health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
if ($health.status -ne "healthy") {
    throw "Health check failed: $($health | ConvertTo-Json -Compress)"
}
Write-Host "Health OK: redis=$($health.redis) db=$($health.database)"

$loginBody = @{
    email = "manager@smarttender.kz"
    password = "manager123"
} | ConvertTo-Json

$login = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/auth/login" `
    -Method Post `
    -ContentType "application/json" `
    -Body $loginBody

if (-not $login.access_token) {
    throw "Login failed: access_token missing"
}
Write-Host "Login OK"

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}

$tenders = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/tenders?page=1&limit=5" `
    -Headers $headers `
    -Method Get

Write-Host "Tenders OK: count=$($tenders.Count)"

$reports = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/reports" `
    -Headers $headers `
    -Method Get

Write-Host "Reports OK: count=$($reports.Count)"
Write-Host "Smoke check passed."
