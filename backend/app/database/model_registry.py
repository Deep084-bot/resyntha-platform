"""Model registry — ensures every ORM model is imported before Alembic
reads ``Base.metadata``.

Importing a model that inherits from ``Base`` triggers SQLAlchemy's
table registration, populating ``Base.metadata`` with the model's
table definition.  Alembic ``autogenerate`` requires a fully-populated
``target_metadata`` to diff against the live schema; without it,
migrations would always be empty.

This module exists solely to be imported by ``alembic/env.py`` **before**
``target_metadata = Base.metadata`` is evaluated.  No business logic
lives here.
"""

# investigation
import app.modules.investigation.domain.models  # noqa: F401

# investigation.timeline
import app.modules.investigation.timeline.models  # noqa: F401

# artifact
import app.modules.artifact.domain.models  # noqa: F401

# execution
import app.modules.execution.domain.models  # noqa: F401

# paper
import app.modules.paper.domain.models  # noqa: F401
