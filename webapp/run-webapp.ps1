# Ring MCP Webapp Launcher (reservoir port 10728 per WEBAPP_PORTS.md)
$WebPort = 10728
try { npx --yes kill-port $WebPort 2>$null } catch { }

Write-Host "Ring MCP Webapp Launcher" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

try {
    $nodeVersion = node --version
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js not found. Install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

if (!(Test-Path "package.json")) {
    Write-Host "Not in webapp directory. Run from the webapp folder." -ForegroundColor Red
    exit 1
}

if (!(Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Checking Ring MCP server (port 8123)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8123/api/v1/health" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "Ring MCP server is running on port 8123" -ForegroundColor Green
    }
} catch {
    Write-Host "Ring MCP server not detected on port 8123. Start it first: ring-mcp or docker-compose up -d" -ForegroundColor Yellow
}

Write-Host "Starting webapp on port $WebPort..." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:$WebPort" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

npm run dev