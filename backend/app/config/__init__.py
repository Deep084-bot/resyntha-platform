"""Configuration package for Resyntha.

Exports the global Settings singleton, the Environment enum, the
ConfigurationError exception, validation helpers, and application
constants.  Every module in the application sources configuration
from this single canonical entry point.
"""

from app.config.constants import BUILD_TIME, GIT_COMMIT, PYTHON_VERSION
from app.config.environments import Environment
from app.config.settings import Settings, get_settings, parse_retrieval_providers
from app.config.validation import ConfigurationError, validate_settings

__all__ = [
    "BUILD_TIME",
    "ConfigurationError",
    "Environment",
    "GIT_COMMIT",
    "PYTHON_VERSION",
    "Settings",
    "get_settings",
    "parse_retrieval_providers",
    "validate_settings",
]
