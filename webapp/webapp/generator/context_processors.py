"""Context processors for the generator app.

Git info is loaded once at module import time (server startup) and cached
for the lifetime of the process. This avoids subprocess calls on every request.
"""

import subprocess
from datetime import datetime
from pathlib import Path


def _load_git_info():
    """Load git commit hash and date. Called once at module import."""
    try:
        # Get the project root (where .git is)
        project_root = Path(__file__).resolve().parent.parent.parent.parent

        # Get latest commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        commit_hash = result.stdout.strip() if result.returncode == 0 else None

        # Get commit date
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse git date format: "2025-12-01 10:30:00 -0500"
            date_str = result.stdout.strip()
            commit_date = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
        else:
            commit_date = None

        return commit_hash, commit_date
    except Exception:
        return None, None


# Load git info once at startup
_GIT_COMMIT_HASH, _GIT_COMMIT_DATE = _load_git_info()
_GIT_COMMIT_SHORT = _GIT_COMMIT_HASH[:7] if _GIT_COMMIT_HASH else None
_GIT_REPO_URL = 'https://github.com/smarks/pillars-character-gen'


def git_info(request):
    """Add git commit info to template context.

    Values are loaded once at server startup and reused for all requests.
    """
    return {
        'git_commit_hash': _GIT_COMMIT_HASH,
        'git_commit_short': _GIT_COMMIT_SHORT,
        'git_commit_date': _GIT_COMMIT_DATE,
        'git_repo_url': _GIT_REPO_URL,
    }
