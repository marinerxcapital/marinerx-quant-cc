# Fix Render deploy: validate Neon DATABASE_URL + print exact Render env values
# Run from repo root. Does NOT print secrets to console by default.

param(
    [switch]$ShowSecrets,
    [switch]$OpenDashboards,
    [string]$ServiceId = "srv-d95d9m4vikkc73dk02kg"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Get-DotEnvValue([string]$Key) {
    if (-not (Test-Path ".env")) { return $null }
    $line = Get-Content .env | Where-Object { $_ -match "^${Key}=" } | Select-Object -First 1
    if (-not $line) { return $null }
    return ($line -replace "^${Key}=", "").Trim().Trim('"').Trim("'")
}

Write-Host "==> MarinerX Render deploy fix" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host "Target commit: bb1c368 (or newer on master)"

$dbUrl = Get-DotEnvValue "DATABASE_URL"
if (-not $dbUrl) {
    Write-Host "FAIL: DATABASE_URL missing in .env" -ForegroundColor Red
    Write-Host "Run: npx neonctl@latest env pull --file .env"
    exit 1
}

# Validate URL shape (no secrets printed unless -ShowSecrets)
$preview = if ($dbUrl.Length -gt 48) { $dbUrl.Substring(0, 48) + "..." } else { $dbUrl }
Write-Host "OK: DATABASE_URL found ($preview)" -ForegroundColor Green

if ($dbUrl -match '^\s*DATABASE_URL=' -or $dbUrl -match '^\s*psql\s') {
    Write-Host "WARN: .env value has extra prefix - strip before pasting into Render" -ForegroundColor Yellow
}

$env:APP_ENV = "production"
$env:DATABASE_URL = $dbUrl
python "$PSScriptRoot\validate_neon_url.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "==> Paste into Render Environment (value ONLY, no quotes, no DATABASE_URL= prefix)" -ForegroundColor Cyan
Write-Host "https://dashboard.render.com/web/$ServiceId/env"
Write-Host ""
Write-Host "DATABASE_URL"
if ($ShowSecrets) {
    Write-Host $dbUrl
} else {
    Write-Host "(hidden - run with -ShowSecrets to print, or copy from Neon Connect / .env)"
}
Write-Host ""
Write-Host "R2_ACCOUNT_ID = b31d3d49151af98fe1125aa40c5fa6c8"
Write-Host "R2_BUCKET_NAME = marinerx-mcc-prod"
Write-Host "R2_ACCESS_KEY_ID = (from Cloudflare R2 API token)"
Write-Host "R2_SECRET_ACCESS_KEY = (from Cloudflare R2 API token)"
Write-Host "R2_PUBLIC_BASE_URL = (leave blank)"
Write-Host ""
Write-Host "After saving env vars:" -ForegroundColor Cyan
Write-Host "https://dashboard.render.com/web/$ServiceId/deploys"
Write-Host "Manual Deploy -> Deploy latest commit (bb1c368+)"
Write-Host ""

if ($OpenDashboards) {
    Start-Process "https://dashboard.render.com/web/$ServiceId/env"
    Start-Process "https://dash.cloudflare.com/b31d3d49151af98fe1125aa40c5fa6c8/r2/api-tokens"
    Start-Process "https://console.neon.tech/app/projects"
}

wrangler r2 bucket list 2>&1 | Out-Host
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: R2 bucket marinerx-mcc-prod exists" -ForegroundColor Green
} else {
    Write-Host "WARN: R2 check failed - create token at Cloudflare R2 API tokens page" -ForegroundColor Yellow
}