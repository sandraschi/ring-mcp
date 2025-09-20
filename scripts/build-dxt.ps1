# Ring MCP Server - DXT Package Build Script
# PowerShell version of the build script for Windows users

param(
    [switch]$Help,
    [switch]$NoSign,
    [string]$OutputDir = "dist",
    [switch]$Clean
)

# Show help if requested
if ($Help) {
    Write-Host @"
Ring MCP Server - DXT Package Build Script

DESCRIPTION:
    Builds a DXT extension package for the Ring MCP Server with all dependencies bundled.

PARAMETERS:
    -Help           Show this help message
    -NoSign         Build without signing (for development/testing)
    -OutputDir      Output directory for the DXT package (default: dist)
    -Clean          Clean output directory before building

EXAMPLES:
    .\build-dxt.ps1                    # Build and sign the package
    .\build-dxt.ps1 -NoSign           # Build without signing
    .\build-dxt.ps1 -OutputDir "C:\builds"  # Custom output directory
    .\build-dxt.ps1 -Clean            # Clean build

REQUIREMENTS:
    - Python 3.9+
    - fastmcp>=2.12.0
    - pip installed

"@ -ForegroundColor Yellow
    exit 0
}

# Function to check if a command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
}

# Check Python installation
if (-not (Test-CommandExists python)) {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

# Get Python version
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "🐍 Python version: $pythonVersion" -ForegroundColor Green

# Check FastMCP version
try {
    $fastmcpVersion = python -c "import fastmcp; print(fastmcp.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "📦 FastMCP version: $fastmcpVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️  FastMCP not found or import failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  FastMCP not found or import failed" -ForegroundColor Yellow
}

# Create output directory
if ($Clean -and (Test-Path $OutputDir)) {
    Write-Host "🧹 Cleaning output directory: $OutputDir" -ForegroundColor Yellow
    Remove-Item -Path $OutputDir -Recurse -Force
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# Change to dxt directory
Set-Location "dxt"

# Check if build script exists
if (-not (Test-Path "dxt_build.py")) {
    Write-Error "dxt_build.py not found in dxt directory"
    Set-Location ".."
    exit 1
}

# Run the Python build script
Write-Host "🏗️  Starting DXT package build..." -ForegroundColor Cyan

try {
    $buildArgs = @(
        "dxt_build.py",
        "--output-dir", (Resolve-Path "../$OutputDir").Path
    )

    if ($NoSign) {
        $buildArgs += "--no-sign"
    }

    python $buildArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 DXT package build completed successfully!" -ForegroundColor Green
        Write-Host "📦 Check the $OutputDir directory for your package" -ForegroundColor Green

        # Show package info
        $packagePath = Join-Path "../$OutputDir" "ring-mcp-server.dxt"
        if (Test-Path $packagePath) {
            $packageSize = (Get-Item $packagePath).Length / 1MB
            Write-Host "📊 Package size: $($packageSize.ToString('F2')) MB" -ForegroundColor Green
        }
    } else {
        Write-Error "DXT package build failed!"
        exit 1
    }

} catch {
    Write-Error "Build failed with error: $_"
    Set-Location ".."
    exit 1
} finally {
    Set-Location ".."
}

Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Test the .dxt file in Claude Desktop" -ForegroundColor White
Write-Host "2. Verify all tools work correctly" -ForegroundColor White
Write-Host "3. Check that dependencies are properly bundled" -ForegroundColor White
Write-Host "4. Create a GitHub release with the .dxt file" -ForegroundColor White
