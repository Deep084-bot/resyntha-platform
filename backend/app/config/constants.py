from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone


def _detect_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=__file__ and None,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def _detect_build_time() -> str:
    return datetime.now(timezone.utc).isoformat()


BUILD_TIME: str = _detect_build_time()
GIT_COMMIT: str = _detect_git_commit()
PYTHON_VERSION: str = sys.version.split()[0]
