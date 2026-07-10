"""Security-header configuration builder.

Merges the hard-coded defaults with dynamic values from
``Settings`` (e.g. Content-Security-Policy directives).
"""

from __future__ import annotations

from app.config import get_settings
from app.security.headers import DEFAULT_SECURITY_HEADERS


def build_security_headers() -> dict[str, str]:
    """Return the active set of security response headers.

    Respects ``SECURITY_HEADERS_ENABLED`` and ``CSP_ENABLED``
    from application Settings.
    """
    headers = dict(DEFAULT_SECURITY_HEADERS)

    settings = get_settings()
    if settings.CSP_ENABLED and settings.CSP_DIRECTIVES.strip():
        headers["Content-Security-Policy"] = settings.CSP_DIRECTIVES

    return headers
