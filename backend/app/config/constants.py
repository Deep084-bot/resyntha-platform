"""Application-wide constants for Resyntha.

Values defined here are imported by other config modules and by
business-logic modules.  This keeps magic strings and numbers out of
the codebase.

Future constants will include:
  - Pagination defaults (page size, max page size).
  - Timeouts for external service calls.
  - Rate-limit thresholds.
  - CORS origin lists.
  - Redis key prefixes and TTLs.
"""
