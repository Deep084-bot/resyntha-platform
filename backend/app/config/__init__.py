"""Configuration package for Resyntha.

Exports the global Settings singleton and the cached factory function
so that every module in the application sources configuration from a single
canonical entry point — never from os.getenv or load_dotenv directly.
"""

from app.config.settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]
