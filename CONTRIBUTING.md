# Contributing to Ring MCP

Thank you for your interest in contributing to Ring MCP! We welcome contributions from the community.

## Development Setup

### Prerequisites
- Python 3.9 or later
- Ring account with API access
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/ring-mcp/ring-mcp.git
cd ring-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your Ring credentials
# RING_USERNAME=your-email@example.com
# RING_PASSWORD=your-password
# RING_TOKEN=optional-api-token
```

## Development Workflow

### 1. Choose an Issue
- Check [GitHub Issues](https://github.com/ring-mcp/ring-mcp/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes
- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Test Your Changes
```bash
# Run tests
pytest tests/

# Run specific tests
pytest tests/test_basic.py -v

# Run with coverage
pytest --cov=ring_mcp tests/

# Run linting
black ring_mcp/
isort ring_mcp/
mypy ring_mcp/
```

### 5. Commit Changes
```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add new camera monitoring tool

- Add get_camera_status tool for real-time camera monitoring
- Add tests for camera status functionality
- Update documentation with camera tool examples
"
```

### 6. Create Pull Request
- Push your branch to GitHub
- Create a Pull Request with a clear description
- Reference any related issues
- Wait for review and address feedback

## Code Standards

### Python Style
- Follow [PEP 8](https://pep8.org/) conventions
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [MyPy](https://mypy.readthedocs.io/) for type checking

### Commit Messages
Follow [Conventional Commits](https://conventionalcommits.org/) format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Documentation
- Update README.md for new features
- Add docstrings to all public functions
- Update API documentation in `docs/`
- Keep CHANGELOG.md current

## Testing

### Unit Tests
- Write tests for all new functionality
- Mock external API calls (Ring API)
- Test error conditions and edge cases
- Maintain >80% code coverage

### Integration Tests
- Test with real Ring API (when possible)
- Test MCP protocol compliance
- Test with Claude Desktop integration

## Architecture Guidelines

### Tool Registration
- Register tools using FastMCP 2.12 decorators
- Provide detailed docstrings with parameter descriptions
- Handle errors gracefully with appropriate error messages
- Use async functions for all API calls

### Error Handling
- Catch and handle Ring API errors appropriately
- Provide meaningful error messages to users
- Log errors with appropriate levels
- Don't expose sensitive information in error messages

### Security
- Never log sensitive credentials or tokens
- Use environment variables for configuration
- Validate all user inputs
- Follow security best practices

## Release Process

1. **Version Bump**: Update version in `pyproject.toml`, `setup.py`, and `mcpb/manifest.json`
2. **Changelog**: Update `CHANGELOG.md` with new features and fixes
3. **Build**: Test MCPB package build process
4. **Tag**: Create git tag for release
5. **Publish**: Push to GitHub and trigger release workflow

## Getting Help

- **Documentation**: Check `docs/` directory for detailed guides
- **Issues**: Search existing issues or create new ones
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Request reviews on Pull Requests

## License

By contributing to Ring MCP, you agree that your contributions will be licensed under the same MIT License that covers the project.

Thank you for contributing to Ring MCP! 🚀
