"""Environment type enumeration for Resyntha.

Provides a canonical set of deployment environments so that the rest of
the application can compare against typed constants instead of raw
strings.
"""

from enum import Enum


class Environment(Enum):
    """Supported deployment environments for the Resyntha platform."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
