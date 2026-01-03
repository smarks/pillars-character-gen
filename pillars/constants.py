"""
Constants for Pillars RPG character generation.

This module contains all the large data tables and configuration constants
used throughout the character generation system.
"""

from pillars.enums import TrackType, MagicSchool
from pillars.data import get_skill_tracks, get_track

# Magic school spell progressions
MAGIC_SPELL_PROGRESSION = {
    # Elemental schools share the same progression
    MagicSchool.ELEMENTAL_FIRE: [
        "Fire Missile",
        "Fire Ball",
        "Fire Bolt",
        "Fire Shield",
        "Fire Barrier",
        "Fire Elemental",
    ],
    MagicSchool.ELEMENTAL_LIGHTNING: [
        "Lightning Missile",
        "Lightning Ball",
        "Lightning Bolt",
        "Lightning Shield",
        "Lightning Barrier",
        "Lightning Elemental",
    ],
    MagicSchool.ELEMENTAL_WATER: [
        "Water Missile",
        "Water Ball",
        "Water Bolt",
        "Water Shield",
        "Water Barrier",
        "Water Elemental",
    ],
    MagicSchool.ELEMENTAL_EARTH: [
        "Earth Missile",
        "Earth Ball",
        "Earth Bolt",
        "Earth Shield",
        "Earth Barrier",
        "Earth Elemental",
    ],
    MagicSchool.ELEMENTAL_WIND: [
        "Wind Missile",
        "Wind Ball",
        "Wind Bolt",
        "Wind Shield",
        "Wind Barrier",
        "Wind Elemental",
    ],
    MagicSchool.ALL_ELEMENTS: [
        "Elemental Missile",
        "Elemental Ball",
        "Elemental Bolt",
        "Elemental Shield",
        "Elemental Barrier",
        "Summon Elemental",
    ],
    MagicSchool.PASSAGE: [
        "Detect Magic/Light",
        "Knock/Hold/Blur",
        "Transparency/Detect Invisibility/Lock",
        "Breathing",
        "Flying",
        "Pass Wall",
        "Shape Change",
    ],
    MagicSchool.PROTECTION: [
        "Counter 1/Shield/Detect Magic",
        "Counter 2/Shield Wall/Knowledge",
        "Counter 3/Minor Protection from Element",
        "Counter 4/Major Protection from Element",
        "Counter 5/Encase",
    ],
    MagicSchool.MENDING: ["Heal", "Cure", "Web", "Joining", "Breaking", "Shaping"],
    MagicSchool.WEATHER: [
        "Detect Weather",
        "Wind/Wind Counter",
        "Rain/Rain Counter",
        "Storm/Storm Counter",
    ],
    MagicSchool.COUNTER: [
        "Counter 1",
        "Counter 2",
        "Counter 3",
        "Counter 4",
        "Counter 5",
        "Counter 6",
    ],
    MagicSchool.ARCANE_HELP: [
        "Wild Magic",
        "Any Level 2 spell",
        "Controlled Magic",
        "Summon/Control",
        "Bind",
        "Ask",
    ],
    MagicSchool.CONTROL: [
        "Persuade Minor/Calm/Enrage",
        "Minor Illusion/Fatigue",
        "Wound/Effect Mental State",
        "Persuade Major/Illusion",
        "Major Illusion/Area/Effect Senses",
        "Force (Paralyze/Move/etc)",
    ],
}

# Spell skill mastery levels (applies to all spells)
SPELL_SKILL_MASTERY = {
    1: "Cast spell normally",
    2: "Cast without hand gestures",
    3: "Cast without verbal incantation, protection from same spell",
    4: "Costs 1/3 less fatigue, halt same spell",
    5: "Costs 1/2 less fatigue, reflect same spell back onto caster",
    6: "Costs 2/3 less fatigue, invert spell, reflect same spell group back onto caster",
}

# Track survivability and skills are loaded from references/skills.csv
# Use the data module to access track information (imported at top of file)


class _DynamicTrackDict:
    """
    A dict-like class that rebuilds from CSV on each access.

    This ensures the spreadsheet is always the source of truth -
    any edits to references/skills.csv are immediately reflected.
    """

    def __init__(self, builder_func):
        self._builder = builder_func

    def _get_data(self):
        # get_skill_tracks() checks file mtime and reloads if CSV changed
        return self._builder()

    def __getitem__(self, key):
        return self._get_data()[key]

    def __contains__(self, key):
        return key in self._get_data()

    def get(self, key, default=None):
        return self._get_data().get(key, default)

    def keys(self):
        return self._get_data().keys()

    def values(self):
        return self._get_data().values()

    def items(self):
        return self._get_data().items()

    def __iter__(self):
        return iter(self._get_data())

    def __len__(self):
        return len(self._get_data())


def _build_survivability_dict():
    """Build survivability dict from CSV data."""
    result = {}
    for track_data in get_skill_tracks().values():
        track_type = TrackType.from_csv_name(track_data.name)
        if track_type:
            result[track_type] = track_data.survival_target
    return result


def _build_initial_skills_dict():
    """Build initial skills dict from CSV data (first 2 skills)."""
    result = {}
    for track_data in get_skill_tracks().values():
        track_type = TrackType.from_csv_name(track_data.name)
        if track_type:
            result[track_type] = track_data.skills[:2] if track_data.skills else []
    return result


def _build_yearly_skills_dict():
    """Build yearly skills dict from CSV data."""
    result = {}
    for track_data in get_skill_tracks().values():
        track_type = TrackType.from_csv_name(track_data.name)
        if track_type:
            result[track_type] = track_data.skills
    return result


# Dynamic track data - automatically reloads when CSV file changes
TRACK_SURVIVABILITY = _DynamicTrackDict(_build_survivability_dict)
TRACK_INITIAL_SKILLS = _DynamicTrackDict(_build_initial_skills_dict)
TRACK_YEARLY_SKILLS = _DynamicTrackDict(_build_yearly_skills_dict)


def get_track_requirements(track_type: TrackType) -> str:
    """Get requirements string for a track from CSV."""
    track_data = get_track(track_type.value)
    if track_data:
        return track_data.requirements
    return "None"
