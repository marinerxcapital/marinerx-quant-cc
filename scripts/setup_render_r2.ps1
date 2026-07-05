# MarinerX - Render + R2 setup helper
# Run from repo root after Neon .env exists and R2 is enabled in Cloudflare.

param(
    [switch]$TestR2,
    [switch]$TestPostgres,
    [switch]$PrintRenderChecklist,
    [string]$RenderHealthUrl = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "WARN: $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "FAIL: $msg" -ForegroundColor Red }

Write-Step "MarinerX Render + R2 setup helper"
Write-Host "Repo: $RepoRoot"

if ($TestPostgres -or $PrintRenderChecklist) {
    if (-not (Test-Path ".env")) {
        Write-Fail ".env missing. Run: npx neonctl@latest checkout production; npx neonctl@latest env pull --file .env"
        exit 1
    }
    $dbLine = Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
    if (-not $dbLine) {
        Write-Fail "DATABASE_URL not found in .env"
        exit 1
    }
    Write-Ok "DATABASE_URL present in .env (not printed)"
}

if ($TestPostgres) {
    Write-Step "Testing Neon Postgres via app"
    $env:PYTHONPATH = "src"
    python -c "from mcc.core.config import reset_settings_cache; from mcc.storage.database import check_database_connectivity, reset_engine; reset_settings_cache(); reset_engine(); print(check_database_connectivity())"
}

if ($TestR2) {
    Write-Step "Checking Cloudflare R2"
    $bucketName = "marinerx-mcc-prod"
    $accountId = "b31d3d49151af98fe1125aa40c5fa6c8"
    wrangler r2 bucket list 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "R2 not enabled or wrangler auth issue."
        Write-Host "Enable at: https://dash.cloudflare.com/$accountId/r2/overview"
        exit 1
    }
    wrangler r2 bucket create $bucketName 2>&1 | Out-Host
    Write-Ok "Bucket step complete (create is idempotent if exists)"
    Write-Warn "Create R2 API token: https://dash.cloudflare.com/$accountId/r2/api-tokens"
}

if ($PrintRenderChecklist) {
    Write-Step "Render Blueprint + secrets checklist"
    Write-Host "1. Open: https://dashboard.render.com/blueprint/new"
    Write-Host "2. Connect GitHub: marinerxcapital/marinerx-quant-cc branch master"
    Write-Host "3. Apply render.yaml (marinerx-labs-api + marinerx-labs-worker)"
    Write-Host "4. Set secrets on BOTH services:"
    Write-Host "   DATABASE_URL (from .env pooled)"
    Write-Host "   R2_ACCOUNT_ID=b31d3d49151af98fe1125aa40c5fa6c8"
    Write-Host "   R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME=marinerx-mcc-prod"
    Write-Host "   CORS_ALLOWED_ORIGINS, PUBLIC_FRONTEND_URL, BACKEND_PUBLIC_URL (after deploy URL known)"
    Write-Host "5. Smoke: Invoke-RestMethod https://marinerx-labs-api.onrender.com/health"
}

if ($RenderHealthUrl) {
    Write-Step "Smoke test Render: $RenderHealthUrl"
    try {
        $health = Invoke-RestMethod -Uri $RenderHealthUrl -TimeoutSec 30
        $health | ConvertTo-Json -Depth 6
        if ($health.live_execution_enabled -eq $true) {
            Write-Fail "live_execution_enabled is true - must be false"
            exit 1
        }
        Write-Ok "Render health check passed"
    } catch {
        Write-Fail $_.Exception.Message
        exit 1
    }
}

if (-not ($TestR2 -or $TestPostgres -or $PrintRenderChecklist -or $RenderHealthUrl)) {
    Write-Host "Usage:"
    Write-Host "  .\scripts\setup_render_r2.ps1 -PrintRenderChecklist"
    Write-Host "  .\scripts\setup_render_r2.ps1 -TestPostgres"
    Write-Host "  .\scripts\setup_render_r2.ps1 -TestR2"
    Write-Host "  .\scripts\setup_render_r2.ps1 -RenderHealthUrl <your-render-health-url>"
}