@echo off
REM Ring MCP Webapp Launcher (Windows Batch)
REM This script sets up and runs the React webapp for testing Ring MCP

echo 🚀 Ring MCP Webapp Launcher
echo ================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Node.js not found. Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js found: %NODE_VERSION%

REM Check if we're in the right directory
if not exist "package.json" (
    echo ✗ Not in webapp directory. Please run from the webapp folder.
    pause
    exit /b 1
)

REM Check if dependencies are installed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ✗ Failed to install dependencies
        pause
        exit /b 1
    }
)

REM Check if Ring MCP server is running (simple check)
echo 🔍 Checking Ring MCP server connection...
curl -s http://localhost:8123/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Ring MCP server is running on port 8123
) else (
    echo ⚠ Ring MCP server not detected on port 8123
    echo   Make sure to start the Ring MCP server first:
    echo   cd .. ^&^& ring-mcp
    echo   or via Docker: docker-compose up -d
    echo.
)

REM Start the development server
echo 🌐 Starting Ring MCP Webapp...
echo Dashboard: http://localhost:10728
echo 🔄 Press Ctrl+C to stop the server
echo.

npm run dev