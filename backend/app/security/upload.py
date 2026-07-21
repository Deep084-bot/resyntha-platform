"""Upload validation utilities for file-upload endpoints.

Provides a reusable FastAPI dependency that checks MIME type,
file extension, and file size before the handler processes
the upload.

Usage::

    @router.post("/upload")
    async def upload(
        file: UploadFile = Depends(validate_upload),
    ):
        ...
"""

from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass

from fastapi import HTTPException, status
from fastapi import UploadFile as FastAPIUploadFile

from app.config import get_settings

# ── Allowed sets ──────────────────────────────────────────────────────────────

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/json",
        "text/plain",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "application/zip",
    }
)

ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".json",
        ".txt",
        ".csv",
        ".xlsx",
        ".xls",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".zip",
    }
)


# ── Exceptions ────────────────────────────────────────────────────────────────


class UploadValidationError(HTTPException):
    """Raised when an uploaded file fails validation."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"error": "invalid_upload", "message": detail},
        )


# ── Validation result ─────────────────────────────────────────────────────────


@dataclass
class ValidatedUpload:
    """Wraps a validated upload file with pre-computed metadata."""

    filename: str
    content_type: str
    size: int
    file: FastAPIUploadFile


# ── Validator ─────────────────────────────────────────────────────────────────


def validate_upload(file: FastAPIUploadFile) -> ValidatedUpload:
    """FastAPI dependency that validates an uploaded file.

    Checks:
    - File size does not exceed ``MAX_UPLOAD_SIZE``.
    - MIME type is in the allowed set.
    - File extension is in the allowed set.
    """
    settings = get_settings()

    # --- Size ---
    if file.size is not None and file.size > settings.MAX_UPLOAD_SIZE:
        raise UploadValidationError(
            f"File size ({file.size} bytes) exceeds the maximum "
            f"upload size of {settings.MAX_UPLOAD_SIZE} bytes"
        )

    # --- MIME type ---
    content_type = (file.content_type or "").lower().strip()
    if not content_type:
        # Guess from extension
        guessed, _ = mimetypes.guess_type(file.filename or "")
        if guessed:
            content_type = guessed

    if not content_type:
        raise UploadValidationError("Could not determine MIME type for uploaded file")
    if content_type not in ALLOWED_MIME_TYPES:
        raise UploadValidationError(f"MIME type '{content_type}' is not allowed for upload")

    # --- Extension ---
    filename = (file.filename or "").lower()
    ext = _extension(filename)
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(f"File extension '{ext}' is not allowed for upload")

    safe_filename = os.path.basename(file.filename or "unknown")
    if not safe_filename or safe_filename.startswith("."):
        raise UploadValidationError("Invalid filename")
    return ValidatedUpload(
        filename=safe_filename,
        content_type=content_type or "application/octet-stream",
        size=file.size or 0,
        file=file,
    )


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    _, dot_ext = filename.rsplit(".", 1)
    return f".{dot_ext}" if dot_ext else ""
