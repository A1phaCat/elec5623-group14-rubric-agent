class RubricParseError(ValueError):
    """Raised when a rubric cannot be ingested."""


class SubmissionParseError(ValueError):
    """Raised when a submission cannot be converted to searchable text."""


class ExportBlocked(RuntimeError):
    """Raised when a final export is requested before every criterion is confirmed."""
