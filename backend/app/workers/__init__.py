"""Background workers.

All long-running or pipeline-style work moves into ARQ worker
functions registered here.  Workers never import FastAPI — they
operate on the application layer directly, loading everything
from the database.
"""
