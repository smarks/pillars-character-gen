"""
Skill track data loader for Pillars RPG.

Reads skill track data from references/skills.csv - the single source of truth
for skill tracks that is shared between the program and players.
"""

import csv
import io
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# Path to the skills CSV file
SKILLS_CSV = Path(__file__).parent.parent.parent / "references" / "skills.csv"


@dataclass
class SkillTrack:
    """Represents a skill track loaded from CSV."""

    name: str
    requirements: str
    survival: str  # Can be a number or "Per track" for Random
    skills: List[str] = field(default_factory=list)

    @property
    def survival_target(self) -> Optional[int]:
        """Get survival target as integer, or None for Random track."""
        try:
            return int(self.survival)
        except ValueError:
            return None


_cache: Optional[Dict[str, SkillTrack]] = None


def load_skill_tracks(csv_path: Optional[Path] = None) -> Dict[str, SkillTrack]:
    """
    Load skill track data from the CSV file.

    Args:
        csv_path: Optional path to CSV. Defaults to references/skills.csv

    Returns:
        Dict mapping track name (lowercase) to SkillTrack
    """
    if csv_path is None:
        csv_path = SKILLS_CSV

    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the row with track names (starts with "Skill track")
    track_names = []
    requirements = []
    survival = []
    skills_by_track: Dict[str, List[str]] = {}

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    # Row 2 (index 2): Track names
    if len(rows) > 2:
        track_names = [t.strip() for t in rows[2][1:] if t.strip()]

    # Row 3 (index 3): Requirements
    if len(rows) > 3:
        requirements = [r.strip() if r.strip() else "None" for r in rows[3][1:]]

    # Row 4 (index 4): Survival values
    if len(rows) > 4:
        survival = [s.strip() if s.strip() else "-" for s in rows[4][1:]]

    # Initialize skills lists for each track
    for name in track_names:
        skills_by_track[name] = []

    # Rows 5+ (index 5+): Skills by year
    for row_idx in range(5, len(rows)):
        row = rows[row_idx]
        for col_idx, skill in enumerate(row[1:]):
            if col_idx < len(track_names) and skill.strip():
                skills_by_track[track_names[col_idx]].append(skill.strip())

    # Build SkillTrack objects
    tracks = {}
    for i, name in enumerate(track_names):
        req = requirements[i] if i < len(requirements) else "None"
        surv = survival[i] if i < len(survival) else "-"
        tracks[name.lower()] = SkillTrack(
            name=name,
            requirements=req,
            survival=surv,
            skills=skills_by_track.get(name, []),
        )

    return tracks


def get_skill_tracks() -> Dict[str, SkillTrack]:
    """Get cached skill track data, loading from CSV if needed."""
    global _cache
    if _cache is None:
        _cache = load_skill_tracks()
    return _cache


def reload_tracks():
    """Force reload of track data from CSV."""
    global _cache
    _cache = None
    return get_skill_tracks()


def get_track(name: str) -> Optional[SkillTrack]:
    """Get a specific track by name (case-insensitive)."""
    return get_skill_tracks().get(name.lower())


def get_track_names() -> List[str]:
    """Get list of all track names."""
    return [t.name for t in get_skill_tracks().values()]


def get_track_skill(track_name: str, year: int) -> Optional[str]:
    """Get the skill for a specific track and year (1-indexed)."""
    track = get_track(track_name)
    if track and 0 < year <= len(track.skills):
        return track.skills[year - 1]
    return None


__all__ = [
    "SkillTrack",
    "load_skill_tracks",
    "get_skill_tracks",
    "reload_tracks",
    "get_track",
    "get_track_names",
    "get_track_skill",
    "SKILLS_CSV",
]
