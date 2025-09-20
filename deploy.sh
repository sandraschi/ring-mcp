#!/bin/bash

# Ring MCP Deployment Script
# This script builds, tests, and deploys the Ring MCP server

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ring-mcp"
CONTAINER_NAME="ring-mcp"
VERSION="$(python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")"
TAG="${VERSION:-latest}"

# Function to print info messages
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Function to print warning messages
warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function to print error messages and exit
error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
for cmd in docker docker-compose python; do
    if ! command_exists "$cmd"; then
        error "Required command not found: $cmd"
    fi
done

# Parse command line arguments
BUILD=false
TEST=false
DEPLOY=false
PUSH=false
CLEAN=false
HELP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build) BUILD=true ;;
        --test) TEST=true ;;
        --deploy) DEPLOY=true ;;
        --push) PUSH=true ;;
        --clean) CLEAN=true ;;
        --help) HELP=true ;;
        *) error "Unknown option: $1" ;;
    esac
    shift
done

# Show help if no arguments or --help is provided
if [ $# -eq 0 ] || [ "$HELP" = true ]; then
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --build    Build the Docker image"
    echo "  --test     Run tests"
    echo "  --deploy   Deploy the application"
    echo "  --push     Push the Docker image to registry"
    echo "  --clean    Clean up resources"
    echo "  --help     Show this help message"
    exit 0
fi

# Clean up resources
if [ "$CLEAN" = true ]; then
    info "Cleaning up resources..."
    
    # Stop and remove containers, networks, and volumes
    docker-compose down -v --remove-orphans || true
    
    # Remove unused Docker resources
    docker system prune -f
    
    # Remove build artifacts
    rm -rf build/ dist/ *.egg-info/
    find . -name '*.pyc' -delete
    find . -name '__pycache__' -exec rm -rf {} +
    
    info "Cleanup complete!"
    exit 0
fi

# Run tests
if [ "$TEST" = true ]; then
    info "Running tests..."
    
    # Check if we're in a virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        warn "Not in a virtual environment. Creating one..."
        python -m venv venv
        source venv/bin/activate
    fi
    
    # Install development dependencies
    pip install -e ".[dev]"
    
    # Run tests
    python -m pytest tests/ -v --cov=ring_mcp --cov-report=term-missing
    
    # Run type checking
    mypy ring_mcp
    
    # Run linting
    black --check ring_mcp tests
    isort --check-only ring_mcp tests
    
    info "Tests completed successfully!"
fi

# Build Docker image
if [ "$BUILD" = true ]; then
    info "Building Docker image..."
    
    # Build the image
    docker build -t "${IMAGE_NAME}:${TAG}" .
    
    # Tag as latest
    docker tag "${IMAGE_NAME}:${TAG}" "${IMAGE_NAME}:latest"
    
    info "Docker image built successfully!"
fi

# Push Docker image
if [ "$PUSH" = true ]; then
    if [ -z "${DOCKER_REGISTRY:-}" ]; then
        error "DOCKER_REGISTRY environment variable is not set"
    fi
    
    info "Pushing Docker image to ${DOCKER_REGISTRY}..."
    
    # Tag for registry
    docker tag "${IMAGE_NAME}:${TAG}" "${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG}"
    docker tag "${IMAGE_NAME}:latest" "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
    
    # Push to registry
    docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG}"
    docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
    
    info "Docker image pushed successfully!"
fi

# Deploy the application
if [ "$DEPLOY" = true ]; then
    info "Deploying Ring MCP..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warn "No .env file found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warn "Please update the .env file with your configuration and run again."
            exit 1
        else
            error "No .env.example file found. Please create a .env file with your configuration."
        fi
    fi
    
    # Start the application
    docker-compose up -d
    
    # Show status
    docker-compose ps
    
    info "Ring MCP has been deployed successfully!"
    info "Access the API at: http://localhost:8000"
    info "Access Prometheus at: http://localhost:9090"
    info "Access Grafana at: http://localhost:3000 (admin/admin)"
fi

info "Deployment completed successfully!"
