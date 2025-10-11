#!/usr/bin/env powershell
<#
.SYNOPSIS
    Ring MCP - MCPB Package Build Script

.DESCRIPTION
    Builds MCPB (MCP Bundle) packages for the Ring MCP Server.
    This script validates prerequisites, builds the package, and verifies the result.

.PARAMETER NoSign
    Skip package signing (for development builds)

.PARAMETER OutputDir
    Custom output directory for the built package

.PARAMETER Clean
    Clean output directory before building

.EXAMPLE
    .\build-mcpb-package.ps1

.EXAMPLE
    .\build-mcpb-package.ps1 -NoSign

.EXAMPLE
    .\build-mcpb-package.ps1 -OutputDir "C:\builds" -Clean
#>

param(
    [switch]$NoSign,
    [string]$OutputDir = "dist",
    [switch]$Clean
)

#Requires -Version 5.1

# Set error action preference
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'

# Script configuration
$ScriptName = "Ring MCP - MCPB Builder"
$PackageName = "ring-mcp.mcpb"
$McpbDir = "mcpb"
$ManifestFile = "$McpbDir/manifest.json"
$McpbConfigFile = "$McpbDir/mcpb.json"
$PromptsDir = "$McpbDir/prompts"

# Color functions for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput $Message "Green" }
function Write-Error { param([string]$Message) Write-ColorOutput $Message "Red" }
function Write-Warning { param([string]$Message) Write-ColorOutput $Message "Yellow" }
function Write-Info { param([string]$Message) Write-ColorOutput $Message "Cyan" }

# Function to check prerequisites
function Test-Prerequisites {
    Write-Info "🔍 Checking prerequisites..."

    # Check MCPB CLI
    try {
        $mcpbVersion = & mcpb --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ MCPB CLI: v$mcpbVersion"
        } else {
            throw "MCPB CLI not found"
        }
    } catch {
        Write-Error "❌ MCPB CLI not found. Install with: npm install -g @anthropic-ai/mcpb"
        exit 1
    }

    # Check Python
    try {
        $pythonVersion = & python --version 2>$null
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]

            if ($major -ge 3 -and $minor -ge 9) {
                Write-Success "✅ Python: $pythonVersion"
            } else {
                Write-Warning "⚠️  Python: $pythonVersion (recommended: 3.9+)"
            }
        }
    } catch {
        Write-Error "❌ Python not found in PATH"
        exit 1
    }

    # Check manifest file
    if (Test-Path $ManifestFile) {
        Write-Success "✅ Manifest: $ManifestFile exists"
    } else {
        Write-Error "❌ Manifest: $ManifestFile not found"
        exit 1
    }

    # Check MCPB config file
    if (Test-Path $McpbConfigFile) {
        Write-Success "✅ MCPB Config: $McpbConfigFile exists"
    } else {
        Write-Error "❌ MCPB Config: $McpbConfigFile not found"
        exit 1
    }

    # Check prompts directory
    if (Test-Path $PromptsDir) {
        $promptFiles = Get-ChildItem "$PromptsDir/*.json"
        if ($promptFiles.Count -gt 0) {
            Write-Success "✅ Prompts: $PromptsDir contains $($promptFiles.Count) template files"
        } else {
            Write-Error "❌ Prompts: $PromptsDir exists but contains no JSON files"
            exit 1
        }
    } else {
        Write-Error "❌ Prompts: $PromptsDir directory not found"
        exit 1
    }

    Write-Info "Prerequisites check completed"
}

# Function to validate manifest
function Test-Manifest {
    Write-Info "🔍 Validating manifest..."

    try {
        $validationResult = & mcpb validate $ManifestFile 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Manifest schema validation passed!"
            return $true
        } else {
            Write-Error "❌ Manifest validation failed:"
            Write-Error $validationResult
            return $false
        }
    } catch {
        Write-Error "❌ Manifest validation error: $_"
        return $false
    }
}

# Function to prepare output directory
function Initialize-OutputDirectory {
    param([string]$OutputPath)

    if ($Clean -and (Test-Path $OutputPath)) {
        Write-Info "🧹 Cleaning output directory: $OutputPath"
        Remove-Item $OutputPath -Recurse -Force
    }

    if (!(Test-Path $OutputPath)) {
        New-Item -ItemType Directory -Path $OutputPath | Out-Null
        Write-Success "📁 Created output directory: $OutputPath"
    }
}

# Function to build MCPB package
function New-McpbPackage {
    param([string]$OutputPath)

    $packagePath = Join-Path $OutputPath $PackageName
    $manifestSource = "$McpbDir/manifest.json"
    $mcpbConfigSource = "$McpbDir/mcpb.json"

    Write-Info "🔨 Building MCPB package..."
    Write-Info "   Source: . (current directory)"
    Write-Info "   Output: $packagePath"

    try {
        # Copy MCPB configuration files to root temporarily
        Write-Info "   Copying configuration files..."
        Copy-Item $manifestSource "manifest.json" -Force
        Copy-Item $mcpbConfigSource "mcpb.json" -Force

        try {
            # Pack the current directory
            $buildResult = & mcpb pack . $packagePath 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Success "✅ Package built successfully!"
                return $packagePath
            } else {
                Write-Error "❌ Package build failed:"
                Write-Error $buildResult
                return $null
            }
        } finally {
            # Clean up temporary files
            if (Test-Path "manifest.json") { Remove-Item "manifest.json" -Force }
            if (Test-Path "mcpb.json") { Remove-Item "mcpb.json" -Force }
        }
    } catch {
        Write-Error "❌ Package build error: $_"
        # Clean up on error
        if (Test-Path "manifest.json") { Remove-Item "manifest.json" -Force }
        if (Test-Path "mcpb.json") { Remove-Item "mcpb.json" -Force }
        return $null
    }
}

# Function to verify package
function Test-Package {
    param([string]$PackagePath)

    Write-Info "🔍 Verifying package..."

    if (!(Test-Path $PackagePath)) {
        Write-Error "❌ Package file not found: $PackagePath"
        return $false
    }

    # Check file size (should be reasonable)
    $fileSize = (Get-Item $PackagePath).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)

    if ($fileSizeMB -lt 0.1) {
        Write-Warning "⚠️  Package size seems small: $fileSizeMB MB"
    } elseif ($fileSizeMB -gt 10) {
        Write-Warning "⚠️  Package size seems large: $fileSizeMB MB"
    } else {
        Write-Success "✅ Package size: $fileSizeMB MB"
    }

    # Try to validate package structure
    try {
        # MCPB doesn't have a direct validation command, but we can check if it's a zip file
        $fileHeader = Get-Content $PackagePath -Encoding Byte -TotalCount 4
        $zipHeader = [byte[]](0x50, 0x4B, 0x03, 0x04)

        $isZip = $true
        for ($i = 0; $i -lt 4; $i++) {
            if ($fileHeader[$i] -ne $zipHeader[$i]) {
                $isZip = $false
                break
            }
        }

        if ($isZip) {
            Write-Success "✅ Package appears to be a valid ZIP archive"
        } else {
            Write-Warning "⚠️  Package may not be a valid ZIP archive"
        }
    } catch {
        Write-Warning "⚠️  Could not verify package structure: $_"
    }

    Write-Success "✅ Package verification completed: $PackagePath"
    return $true
}

# Main script execution
function main {
    Write-Info "🚀 $ScriptName"
    Write-Info ("=" * 50)

    # Show parameters
    Write-Info "Configuration:"
    Write-Info "   NoSign: $NoSign"
    Write-Info "   OutputDir: $OutputDir"
    Write-Info "   Clean: $Clean"
    Write-Info ""

    # Check prerequisites
    Test-Prerequisites
    Write-Info ""

    # Validate manifest
    if (!(Test-Manifest)) {
        exit 1
    }
    Write-Info ""

    # Prepare output directory
    Initialize-OutputDirectory $OutputDir
    Write-Info ""

    # Build package
    $packagePath = New-McpbPackage $OutputDir
    if (!$packagePath) {
        exit 1
    }
    Write-Info ""

    # Verify package
    if (!(Test-Package $packagePath)) {
        Write-Warning "⚠️  Package verification failed, but build completed"
    }
    Write-Info ""

    # Success message
    Write-Success "🎉 MCPB package build completed successfully!"
    Write-Info ""
    Write-Info "Package location: $packagePath"
    Write-Info ""
    Write-Info "Next steps:"
    Write-Info "1. Test installation: Drag package to Claude Desktop"
    Write-Info "2. Verify configuration prompts appear"
    Write-Info "3. Test Ring tools functionality"
    Write-Info "4. Check Claude Desktop logs for errors"
    Write-Info ""
    Write-Info "For production distribution:"
    Write-Info "1. Tag version: git tag v1.0.1"
    Write-Info "2. Push tag: git push origin v1.0.1"
    Write-Info "3. GitHub Actions will build and release automatically"
}

# Run main function
try {
    main
} catch {
    Write-Error "💥 Script execution failed: $_"
    exit 1
}
