# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it privately before public disclosure.

**Do not report security vulnerabilities through public GitHub issues.**

### How to Report

Send details to **[opensource@anomalyco.com](mailto:opensource@anomalyco.com)** with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Investigation**: We will assess the report and determine impact
- **Fix timeline**: Depends on severity, typically within 7 days for critical issues
- **Disclosure**: We coordinate disclosure with the reporter

## Security Features

Resyntha includes several built-in security mechanisms:

- **SecurityHeadersMiddleware**: Default security headers (HSTS, X-Content-Type-Options, X-Frame-Options, etc.) with configurable Content Security Policy
- **RequestSizeLimitMiddleware**: Body size enforcement (413 on oversized requests)
- **TimeoutMiddleware**: Wall-clock request timeout (504 on timeout)
- **CORS**: Configurable origins, methods, headers — no wildcards in production
- **TrustedHostMiddleware**: Validates Host header against whitelist
- **Structured error handling**: No internal detail in production error responses
- **Rate limiting**: Sliding window rate limiting to prevent abuse
- **Secret key validation**: Minimum 32 characters enforced in production

## Security Best Practices for Deployment

See [docs/production-checklist.md](docs/production-checklist.md) for a comprehensive deployment security checklist.

Key items:

1. Generate a strong `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Set `ENVIRONMENT=production` — enables security validations
3. Configure `TRUSTED_HOSTS` and `CORS_ORIGINS` for your domain
4. Use HTTPS/TLS in production
5. Keep dependencies updated: `pip-audit` and `npm audit` run in CI
6. Never commit `.env` files to version control
7. Use managed PostgreSQL and Redis with TLS connections
