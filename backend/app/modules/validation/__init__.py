"""Validation module.

Performs deterministic validation on retrieved papers before
persistence.  Each validation rule is an independent validator
class; ``ValidationService`` orchestrates all of them.

Results are stored as a ``VALIDATED_COLLECTION`` artifact and
inline in the pipeline context as ``validated_papers``.
"""
