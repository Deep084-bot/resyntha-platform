"""Workflow layer.

Workflows coordinate multiple services to execute a business process.
They own the orchestration — loading entities, invoking services,
recording timeline events, creating artifacts, and managing the
return value for the API layer.

Services remain reusable and independent of each other.
"""
