"""Context processors for the generator app."""

import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _get_git_info():
    """Get git commit hash and date. Cached for performance."""
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


def git_info(request):
    """Add git commit info to template context."""
    commit_hash, commit_date = _get_git_info()

    return {
        'git_commit_hash': commit_hash,
        'git_commit_short': commit_hash[:7] if commit_hash else None,
        'git_commit_date': commit_date,
        'git_repo_url': 'https://github.com/smarks/pillars-character-gen',
    }
