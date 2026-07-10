"""Default security header definitions.

These are used when ``SECURITY_HEADERS_ENABLED`` is true.
Individual headers can be overridden via environment variables
in future iterations.
"""

from __future__ import annotations

DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": (
        "camera=(), "
        "display-capture=(), "
        "fullscreen=(self), "
        "geolocation=(), "
        "microphone=(), "
        "midi=(), "
        "payment=(), "
        "picture-in-picture=(), "
        "screen-wake-lock=(), "
        "sync-xhr=(), "
        "usb=(), "
        "web-share=(self)"
    ),
}
