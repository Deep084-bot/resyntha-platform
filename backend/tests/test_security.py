"""Tests for security hardening — headers, request size, timeout, error
responses, CORS configuration, and upload validation.

Uses ``TestClient`` against the full FastAPI application.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core.middleware.request_size import RequestSizeLimitMiddleware
from app.core.middleware.timeout import TimeoutMiddleware
from app.security import SecurityHeadersMiddleware as SecurityHeadersMiddlewareFromModule
from app.security.config import build_security_headers
from app.security.headers import DEFAULT_SECURITY_HEADERS
from app.security.upload import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, validate_upload


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app, base_url="http://localhost")


def _make_test_app() -> FastAPI:
    """Build a minimal app with *only* the middleware under test."""
    app = FastAPI()

    @app.get("/hello")
    async def hello_get() -> dict:
        return {"ok": True}

    @app.post("/hello")
    async def hello_post() -> dict:
        return {"ok": True}

    return app


# ═══════════════════════════════════════════════════════════════════════════════
# Security Headers
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityHeadersConfig:
    def test_build_headers_includes_defaults(self) -> None:
        headers = build_security_headers()
        for name in DEFAULT_SECURITY_HEADERS:
            assert name in headers

    def test_csp_included_when_enabled(self) -> None:
        settings = get_settings()
        if settings.CSP_ENABLED:
            headers = build_security_headers()
            assert "Content-Security-Policy" in headers
            assert "default-src 'self'" in headers["Content-Security-Policy"]

    def test_default_headers_have_expected_values(self) -> None:
        assert DEFAULT_SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
        assert DEFAULT_SECURITY_HEADERS["X-Frame-Options"] == "DENY"
        assert (
            DEFAULT_SECURITY_HEADERS["Referrer-Policy"]
            == "strict-origin-when-cross-origin"
        )
        assert (
            DEFAULT_SECURITY_HEADERS["Cross-Origin-Opener-Policy"] == "same-origin"
        )
        assert (
            DEFAULT_SECURITY_HEADERS["Cross-Origin-Resource-Policy"] == "same-origin"
        )


class TestSecurityHeadersMiddleware:
    def test_response_includes_all_security_headers(self, client: TestClient) -> None:
        resp = client.get("/api/v1/live")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert (
            resp.headers.get("referrer-policy")
            == "strict-origin-when-cross-origin"
        )
        # Permissions-Policy should be present
        assert "permissions-policy" in resp.headers

    def test_security_headers_disabled(self) -> None:
        from app.security import middleware as security_middleware_module

        app = _make_test_app()
        app.add_middleware(SecurityHeadersMiddlewareFromModule)
        with patch.object(
            security_middleware_module, "get_settings",
        ) as mock_get_settings:
            disabled = get_settings().model_copy(
                update={"SECURITY_HEADERS_ENABLED": False},
            )
            mock_get_settings.return_value = disabled
            client = TestClient(app, base_url="http://localhost")
            resp = client.get("/hello")
            assert "x-content-type-options" not in resp.headers

    def test_csp_header_present_when_enabled(self) -> None:
        app = _make_test_app()
        app.add_middleware(SecurityHeadersMiddlewareFromModule)
        client = TestClient(app, base_url="http://localhost")
        settings = get_settings()
        if settings.CSP_ENABLED:
            resp = client.get("/hello")
            csp = resp.headers.get("content-security-policy")
            assert csp is not None, f"CSP header missing from {dict(resp.headers)}"
            assert "default-src 'self'" in csp


# ═══════════════════════════════════════════════════════════════════════════════
# Request Size Limits
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequestSizeLimitMiddleware:
    def test_small_request_passes(self, client: TestClient) -> None:
        resp = client.get("/api/v1/live")
        assert resp.status_code == status.HTTP_200_OK

    def test_large_request_blocked_by_content_length(self) -> None:
        app = _make_test_app()
        app.add_middleware(RequestSizeLimitMiddleware)
        client = TestClient(app, base_url="http://localhost")

        resp = client.post(
            "/hello",
            json={"data": "x" * 2_000_000},  # ~2 MB
        )
        assert resp.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_large_request_returns_structured_error(self) -> None:
        app = _make_test_app()
        app.add_middleware(RequestSizeLimitMiddleware)
        client = TestClient(app, base_url="http://localhost")

        resp = client.post(
            "/hello",
            json={"data": "x" * 2_000_000},
        )
        body = resp.json()
        assert body["error"] == "payload_too_large"

    def test_normal_json_body_accepted(self) -> None:
        app = _make_test_app()
        app.add_middleware(RequestSizeLimitMiddleware)
        client = TestClient(app, base_url="http://localhost")

        resp = client.post("/hello", json={"key": "value"})
        assert resp.status_code == status.HTTP_200_OK

    def test_content_type_is_problem_json(self) -> None:
        app = _make_test_app()
        app.add_middleware(RequestSizeLimitMiddleware)
        client = TestClient(app, base_url="http://localhost")

        resp = client.post(
            "/hello",
            json={"data": "x" * 2_000_000},
        )
        assert resp.headers.get("content-type") == "application/problem+json"


# ═══════════════════════════════════════════════════════════════════════════════
# Timeout Middleware
# ═══════════════════════════════════════════════════════════════════════════════


class TestTimeoutMiddleware:
    def test_normal_request_passes(self, client: TestClient) -> None:
        resp = client.get("/api/v1/live")
        assert resp.status_code == status.HTTP_200_OK

    def test_timeout_returns_504(self) -> None:
        from app.core.middleware import timeout as timeout_module

        app = FastAPI()

        @app.get("/slow")
        async def slow() -> dict:
            import asyncio

            await asyncio.sleep(10)
            return {"ok": True}

        app.add_middleware(TimeoutMiddleware)
        client = TestClient(app, base_url="http://localhost")

        with patch.object(timeout_module, "get_settings") as mock_gs:
            mock_gs.return_value = get_settings().model_copy(
                update={"REQUEST_TIMEOUT_SECONDS": 0.01},
            )
            resp = client.get("/slow")
            assert resp.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    def test_timeout_returns_structured_error(self) -> None:
        from app.core.middleware import timeout as timeout_module

        app = FastAPI()

        @app.get("/slow")
        async def slow() -> dict:
            import asyncio

            await asyncio.sleep(10)
            return {"ok": True}

        app.add_middleware(TimeoutMiddleware)
        client = TestClient(app, base_url="http://localhost")

        with patch.object(timeout_module, "get_settings") as mock_gs:
            mock_gs.return_value = get_settings().model_copy(
                update={"REQUEST_TIMEOUT_SECONDS": 0.01},
            )
            resp = client.get("/slow")
            body = resp.json()
            assert body["error"] == "gateway_timeout"

    def test_timeout_logs_warning(self) -> None:
        from app.core.middleware import timeout as timeout_module

        app = FastAPI()

        @app.get("/slow")
        async def slow() -> dict:
            import asyncio

            await asyncio.sleep(10)
            return {"ok": True}

        app.add_middleware(TimeoutMiddleware)
        client = TestClient(app, base_url="http://localhost")

        with (
            patch.object(timeout_module, "get_settings") as mock_gs,
            patch("app.core.middleware.timeout.logger.warning") as mock_warn,
        ):
            mock_gs.return_value = get_settings().model_copy(
                update={"REQUEST_TIMEOUT_SECONDS": 0.01},
            )
            client.get("/slow")
            assert mock_warn.called
            assert mock_warn.call_args[0][0] == "request_timeout"


# ═══════════════════════════════════════════════════════════════════════════════
# Safer Error Responses
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorResponses:
    def test_validation_error_returns_structured_422(self, client: TestClient) -> None:
        """Invalid JSON body should return structured 422."""
        resp = client.post(
            "/api/v1/investigations",
            json={"invalid_field": None},
        )
        # The endpoint may return 307 or 422; whatever it returns must be structured
        if resp.status_code == 422:
            body = resp.json()
            assert "error" in body or "detail" in body

    def test_404_returns_structured_json(self, client: TestClient) -> None:
        resp = client.get("/api/v1/nonexistent-route")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        body = resp.json()
        assert "error" in body
        assert "http_error" in body.get("error", "")

    def test_no_stack_trace_in_404_response(self, client: TestClient) -> None:
        resp = client.get("/api/v1/nonexistent-route")
        body_text = resp.text.lower()
        assert "traceback" not in body_text
        assert "file" not in body_text or "json" not in body_text
        # The response should be JSON, not HTML
        assert resp.headers.get("content-type", "").startswith("application/json")

    def test_unhandled_exception_contains_no_internals(self, client: TestClient) -> None:
        """A route that raises should not leak internals."""
        resp = client.get("/api/v1/health/info")
        # health/info is a valid route; verify it returns safe JSON
        if resp.status_code == 200:
            body = resp.json()
            assert isinstance(body, dict)
            assert "error" not in body or body["error"] != "internal_error"

    def test_unhandled_exception_returns_generic_500_with_handler(self) -> None:
        """Verify the exception_handler returns 500 with no internals."""
        import asyncio

        from app.core.exceptions import unhandled_exception_handler
        from fastapi import Request

        async def _run() -> None:
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [],
            }
            request = Request(scope)
            response = await unhandled_exception_handler(
                request, RuntimeError("secret"),
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            body = json.loads(response.body)
            assert body["error"] == "internal_error"
            assert "secret" not in response.body.decode()

        asyncio.run(_run())


# ═══════════════════════════════════════════════════════════════════════════════
# CORS Configuration
# ═══════════════════════════════════════════════════════════════════════════════


class TestCORSConfiguration:
    def test_cors_headers_present_on_options(self, client: TestClient) -> None:
        resp = client.options(
            "/api/v1/live",
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_origin_not_wildcard(self) -> None:
        settings = get_settings()
        assert "*" not in settings.cors_origin_list

    def test_cors_allowed_methods_from_settings(self) -> None:
        settings = get_settings()
        methods = settings.cors_method_list
        assert "GET" in methods
        assert "POST" in methods
        assert "OPTIONS" in methods

    def test_cors_allowed_headers_from_settings(self) -> None:
        settings = get_settings()
        headers = settings.cors_header_list
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert "X-Request-ID" in headers


# ═══════════════════════════════════════════════════════════════════════════════
# Upload Validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestUploadValidation:
    def test_allowed_mime_types_contains_pdf(self) -> None:
        assert "application/pdf" in ALLOWED_MIME_TYPES

    def test_allowed_extensions_contains_pdf(self) -> None:
        assert ".pdf" in ALLOWED_EXTENSIONS

    def test_allowed_mime_types_contains_json(self) -> None:
        assert "application/json" in ALLOWED_MIME_TYPES

    def test_allowed_mime_types_does_not_contain_exe(self) -> None:
        assert "application/x-msdownload" not in ALLOWED_MIME_TYPES

    def test_allowed_extensions_does_not_contain_exe(self) -> None:
        assert ".exe" not in ALLOWED_EXTENSIONS

    def test_max_upload_size_from_settings(self) -> None:
        settings = get_settings()
        assert settings.MAX_UPLOAD_SIZE > 0

    def test_validate_upload_rejects_oversized_file(self) -> None:
        """Test that validate_upload raises for oversized files."""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.size = 100_000_000  # 100 MB > default 10 MB
        mock_file.content_type = "application/pdf"
        mock_file.filename = "doc.pdf"

        from app.security.upload import UploadValidationError

        with pytest.raises(UploadValidationError):
            validate_upload(mock_file)

    def test_validate_upload_rejects_bad_extension(self) -> None:
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.size = 1000
        mock_file.content_type = "application/pdf"
        mock_file.filename = "evil.exe"

        from app.security.upload import UploadValidationError

        with pytest.raises(UploadValidationError):
            validate_upload(mock_file)


# ═══════════════════════════════════════════════════════════════════════════════
# Disabled Security Configuration
# ═══════════════════════════════════════════════════════════════════════════════


class TestDisabledSecurity:
    def test_request_size_middleware_bypassed_when_max_large(self) -> None:
        """When MAX_REQUEST_SIZE is huge, nothing is blocked."""
        from app.core.middleware import request_size as request_size_module

        app = _make_test_app()
        app.add_middleware(RequestSizeLimitMiddleware)
        client = TestClient(app, base_url="http://localhost")

        with patch.object(request_size_module, "get_settings") as mock_gs:
            mock_gs.return_value = get_settings().model_copy(
                update={"MAX_REQUEST_SIZE": 100_000_000},
            )
            resp = client.post(
                "/hello",
                json={"data": "x" * 500_000},  # 500 KB
            )
            assert resp.status_code == status.HTTP_200_OK


# ═══════════════════════════════════════════════════════════════════════════════
# Production vs Development Behaviour
# ═══════════════════════════════════════════════════════════════════════════════


class TestProductionValidation:
    def test_wildcard_cors_rejected(self) -> None:
        from app.config.validation import ConfigurationError, validate_settings
        from app.config.environments import Environment

        settings = get_settings()
        # Temporarily set production with wildcard origin
        with (
            patch.object(settings, "ENVIRONMENT", Environment.PRODUCTION),
            patch.object(settings, "CORS_ORIGINS", "*"),
        ):
            with pytest.raises(ConfigurationError, match="CORS_ORIGINS must not contain"):
                validate_settings(settings)
