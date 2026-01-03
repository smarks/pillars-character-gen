"""
Helper functions and utilities for the Pillars Character Generator views.
"""

import re
from pillars.attributes import TrackType

# Constants for experience years validation
MIN_EXPERIENCE_YEARS = 1
MAX_EXPERIENCE_YEARS = 50

# Track order for display
TRACK_DISPLAY_ORDER = [
    TrackType.OFFICER,
    TrackType.RANGER,
    TrackType.MAGIC,
    TrackType.NAVY,
    TrackType.ARMY,
    TrackType.MERCHANT,
    TrackType.CRAFTS,
    TrackType.WORKER,
    TrackType.RANDOM,
]


def build_track_info(track_availability):
    """Build track information list for display in templates.

    Args:
        track_availability: Dict from get_track_availability() mapping TrackType to availability info

    Returns:
        List of dicts with track info sorted by TRACK_DISPLAY_ORDER
    """
    from pillars.attributes import TRACK_SURVIVABILITY

    track_info = []
    for track_type in TRACK_DISPLAY_ORDER:
        if track_type not in track_availability:
            continue

        avail = track_availability[track_type]
        survivability = TRACK_SURVIVABILITY.get(track_type, 6)

        track_info.append(
            {
                "track": track_type.value,
                "track_key": track_type.name.lower(),
                "survivability": survivability,
                "requires_roll": avail["requires_roll"],
                "impossible": avail["impossible"],
                "requirement": avail["requirement"],
            }
        )

    return track_info


def validate_experience_years(years_str, default=5):
    """Validate and parse experience years input.

    Args:
        years_str: String input for years
        default: Default value if parsing fails

    Returns:
        int: Validated years value clamped to MIN_EXPERIENCE_YEARS..MAX_EXPERIENCE_YEARS
    """
    try:
        years = int(years_str)
        return max(MIN_EXPERIENCE_YEARS, min(MAX_EXPERIENCE_YEARS, years))
    except (ValueError, TypeError):
        return default


def normalize_skill_name(skill):
    """Normalize a skill name for consistent matching.

    - Title case for consistent display
    - Strip whitespace
    - Handle common variations
    """
    if not skill:
        return skill

    skill = skill.strip()

    # Handle skills with modifiers like "Sword +1 to hit"
    # Keep the modifier part as-is but title case the skill name
    match = re.match(r"^([A-Za-z\s]+?)(\s*[+-].*)?$", skill)
    if match:
        name_part = match.group(1).strip().title()
        modifier_part = match.group(2) or ""
        return name_part + modifier_part

    return skill.title()


def consolidate_skills(skills):
    """Consolidate skills using the skill point system with triangular numbers.

    Each skill occurrence = 1 skill point.
    Skills are grouped by base name (normalized, case-insensitive).
    Display uses triangular numbers: Level 1 = 1pt, Level 2 = 3pts, Level 3 = 6pts, etc.
    Original casing is preserved for display (first occurrence wins).

    Examples:
        ['Cutlass +1 to hit', 'Cutlass +1 to hit', 'Cutlass +1 to hit']
        -> ['Cutlass II'] (3 points = Level 2)

        ['Sword +1 to hit', 'Sword +1 to hit', 'Sword +1 to hit', 'Sword +1 to hit']
        -> ['Sword II (+1)'] (4 points = Level 2 with 1 point toward Level 3)
    """
    from pillars.skills import normalize_skill_name, level_from_points, to_roman
    from collections import defaultdict

    if not skills:
        return []

    # Count skill points by normalized skill name (now lowercase)
    skill_points = defaultdict(int)
    skill_display = (
        {}
    )  # normalized key -> display version (first seen, original casing)

    for skill in skills:
        if not skill:
            continue
        normalized = normalize_skill_name(skill)
        if normalized:
            if normalized not in skill_display:
                # Use title-cased normalized name for display
                # This removes modifiers like "+1" while preserving the base skill name
                skill_display[normalized] = normalized.title()
            skill_points[normalized] += 1

    # Build consolidated list using skill point system with triangular numbers
    consolidated = []
    for key, points in skill_points.items():
        # Use stored display name, or title-case as fallback
        display_name = skill_display.get(key, key.title())
        level, excess = level_from_points(points)

        if level >= 1:
            roman = to_roman(level)
            if excess > 0:
                consolidated.append(f"{display_name} {roman} (+{excess})")
            else:
                consolidated.append(f"{display_name} {roman}")
        else:
            # Less than 1 point (shouldn't happen, but handle gracefully)
            consolidated.append(f"{display_name} (+{points})")

    # Sort alphabetically for consistent display
    consolidated.sort(key=lambda s: s.lower())
    return consolidated


def get_modifier_for_value(value):
    """Get attribute modifier for a given value."""
    from pillars.attributes import get_attribute_modifier

    return get_attribute_modifier(value)


def format_attribute_display(value):
    """Format attribute value for display.

    Stored as: int (1-18) or string like "18.20", "19.50", etc.
    Display: same format, just ensure it's a string.
    """
    if isinstance(value, str):
        return value
    return str(value)


def get_attribute_modifier(value):
    """Get modifier for an attribute value.

    For values 1-18: use standard ATTRIBUTE_MODIFIERS table.
    For values > 18 (including decimal notation): calculate based on effective value.
    18.10-18.100 counts as 18, 19.10-19.100 counts as 19, etc.
    """
    from pillars.attributes import ATTRIBUTE_MODIFIERS

    if isinstance(value, int):
        return ATTRIBUTE_MODIFIERS.get(value, 0)

    if isinstance(value, str) and "." in value:
        # Parse decimal notation: "18.20" -> base 18
        try:
            base = int(value.split(".")[0])
            # For values > 18, each whole number adds +1 to the modifier
            # Base modifier at 18 is +5, so 19 is +6, 20 is +7, etc.
            if base >= 18:
                return 5 + (base - 18)
        except ValueError:
            pass

    # Try parsing as int
    try:
        return ATTRIBUTE_MODIFIERS.get(int(value), 0)
    except (ValueError, TypeError):
        return 0


def get_attribute_base_value(value):
    """Get the base integer value from an attribute.

    For int values: return as-is.
    For string like "18.20": return the base (18).
    For string like "19.50": return the base (19).
    For dict values: extract from 'value' or 'base' key.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if "." in value:
            try:
                return int(value.split(".")[0])
            except ValueError:
                pass
        try:
            return int(value)
        except ValueError:
            pass
    if isinstance(value, dict):
        if "value" in value:
            return get_attribute_base_value(value["value"])
        if "base" in value:
            return get_attribute_base_value(value["base"])
        if "total" in value:
            return value.get("total", 10)
    return 10  # Default
