#!/bin/bash
# Ring MCP Server - DXT Package Build Script
# Cross-platform bash version

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${CYAN}Ring MCP Server - DXT Package Build Script${NC}"
    echo ""
    echo "DESCRIPTION:"
    echo "    Builds a DXT extension package for the Ring MCP Server with all dependencies bundled."
    echo ""
    echo "PARAMETERS:"
    echo "    -h, --help      Show this help message"
    echo "    --no-sign       Build without signing (for development/testing)"
    echo "    --output-dir    Output directory for the DXT package (default: dist)"
    echo "    --clean         Clean output directory before building"
    echo ""
    echo "EXAMPLES:"
    echo "    ./build-dxt.sh                 # Build and sign the package"
    echo "    ./build-dxt.sh --no-sign       # Build without signing"
    echo "    ./build-dxt.sh --output-dir ./builds  # Custom output directory"
    echo "    ./build-dxt.sh --clean         # Clean build"
    echo ""
    echo "REQUIREMENTS:"
    echo "    - Python 3.9+"
    echo "    - fastmcp>=2.12.0"
    echo "    - pip installed"
    echo ""
}

# Parse arguments
NO_SIGN=false
OUTPUT_DIR="dist"
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --no-sign)
            NO_SIGN=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🏗️  Ring MCP Server - DXT Package Builder${NC}"
echo "📂 Source directory: $(pwd)/dxt"
echo "📂 Output directory: $OUTPUT_DIR"
echo "🧹 Clean build: $CLEAN"
echo "🔐 Sign package: $(! $NO_SIGN && echo 'Yes' || echo 'No')"
echo -e "${CYAN}────────────────────────────────────────────────${NC}"

# Check Python installation
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python is not installed or not in PATH${NC}"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}🐍 Python version: $PYTHON_VERSION${NC}"

# Check FastMCP version
if python -c "import fastmcp" 2>/dev/null; then
    FASTMCP_VERSION=$(python -c "import fastmcp; print(fastmcp.__version__)")
    echo -e "${GREEN}📦 FastMCP version: $FASTMCP_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  FastMCP not found or import failed${NC}"
fi

# Create output directory
if [ "$CLEAN" = true ] && [ -d "$OUTPUT_DIR" ]; then
    echo -e "${YELLOW}🧹 Cleaning output directory: $OUTPUT_DIR${NC}"
    rm -rf "$OUTPUT_DIR"
fi

mkdir -p "$OUTPUT_DIR"

# Change to dxt directory
cd dxt

# Check if build script exists
if [ ! -f "dxt_build.py" ]; then
    echo -e "${RED}❌ dxt_build.py not found in dxt directory${NC}"
    cd ..
    exit 1
fi

# Run the Python build script
echo -e "${CYAN}🚀 Starting DXT package build...${NC}"

BUILD_ARGS=(
    "dxt_build.py"
    "--output-dir" "../$OUTPUT_DIR"
)

if [ "$NO_SIGN" = true ]; then
    BUILD_ARGS+=("--no-sign")
fi

if ! python "${BUILD_ARGS[@]}"; then
    echo -e "${RED}❌ DXT package build failed!${NC}"
    cd ..
    exit 1
fi

cd ..

# Show results
echo ""
echo -e "${GREEN}🎉 DXT package build completed successfully!${NC}"
echo -e "${GREEN}📦 Check the $OUTPUT_DIR directory for your package${NC}"

# Show package info
PACKAGE_PATH="$OUTPUT_DIR/ring-mcp-server.dxt"
if [ -f "$PACKAGE_PATH" ]; then
    PACKAGE_SIZE=$(du -h "$PACKAGE_PATH" | cut -f1)
    echo -e "${GREEN}📊 Package size: $PACKAGE_SIZE${NC}"
fi

echo ""
echo -e "${CYAN}📋 Next steps:${NC}"
echo -e "${NC}1. Test the .dxt file in Claude Desktop${NC}"
echo -e "${NC}2. Verify all tools work correctly${NC}"
echo -e "${NC}3. Check that dependencies are properly bundled${NC}"
echo -e "${NC}4. Create a GitHub release with the .dxt file${NC}"
