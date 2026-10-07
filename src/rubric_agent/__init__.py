"""Evidence-first rubric marking agent (ELEC5623 Group 14 Track A)."""

import os

__version__ = "1.0.0"

# The declared prompt for this build. RMA_PROMPT_VERSION overrides it so a
# dev-split comparison does not need a code edit between runs; whichever value
# is active is recorded in every report's provenance block.
DEFAULT_PROMPT_VERSION = "assessment_v4"
PROMPT_VERSION = os.environ.get("RMA_PROMPT_VERSION") or DEFAULT_PROMPT_VERSION
