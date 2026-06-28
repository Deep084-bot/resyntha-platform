"""Validator registry — exports every validator for easy import."""

from app.modules.validation.validators.base import BaseValidator
from app.modules.validation.validators.citation import CitationValidator
from app.modules.validation.validators.doi_format import DOIFormatValidator
from app.modules.validation.validators.duplicate_doi import DuplicateDOIValidator
from app.modules.validation.validators.duplicate_title import DuplicateTitleValidator
from app.modules.validation.validators.duplicate_url import DuplicateURLValidator
from app.modules.validation.validators.metadata import MetadataValidator
from app.modules.validation.validators.publication import PublicationValidator
from app.modules.validation.validators.url_format import URLFormatValidator

__all__ = [
    "BaseValidator",
    "CitationValidator",
    "DOIFormatValidator",
    "DuplicateDOIValidator",
    "DuplicateTitleValidator",
    "DuplicateURLValidator",
    "MetadataValidator",
    "PublicationValidator",
    "URLFormatValidator",
]
