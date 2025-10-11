# Security Policy

## Supported Versions

We take security seriously and actively maintain security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Ring MCP, please report it responsibly by:

1. **Email**: security@ring-mcp.dev (create this email for security reports)
2. **GitHub Security Advisories**: Use [GitHub's private vulnerability reporting](https://github.com/ring-mcp/ring-mcp/security/advisories/new)

Please include:
- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested mitigation if available

## Security Considerations

### Authentication
- Ring credentials are handled securely using environment variables
- No credentials are stored in the codebase or configuration files
- Authentication tokens are managed by the Ring API client library

### Network Security
- All communication with Ring API uses HTTPS
- No sensitive data is logged in plain text
- MCP protocol communication is secured by the host application

### Data Handling
- Device information and events are processed in memory only
- No persistent storage of sensitive Ring data
- Live stream URLs are time-limited and secure

### Dependencies
- All dependencies are regularly updated and scanned for vulnerabilities
- Security updates are applied promptly
- Only trusted, well-maintained packages are used

## Security Best Practices for Users

1. **Environment Variables**: Store Ring credentials in secure environment variables
2. **Access Control**: Limit access to Ring MCP to authorized users only
3. **Network Security**: Ensure MCP communication happens over secure channels
4. **Regular Updates**: Keep Ring MCP and dependencies updated
5. **Monitoring**: Monitor logs for unusual activity

## Responsible Disclosure

We kindly ask that you:
- Give us reasonable time to fix the issue before public disclosure
- Avoid accessing or modifying user data without permission
- Respect the privacy and security of Ring users

Thank you for helping keep Ring MCP and its users secure!
