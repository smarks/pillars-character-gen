"""
Helper functions for character sheet views.

These are internal helpers for skill points management and attribute calculations.
"""

from pillars.attributes import get_track_availability

from .helpers import (
    build_track_info,
    get_attribute_modifier,
    get_attribute_base_value,
)


def build_skill_points_from_char_data(char_data):
    """Build skill points structure from character data.

    If char_data already has 'skill_points_data', returns it.
    Otherwise, migrates from legacy skill lists.

    Returns:
        CharacterSkills object with all skill point data
    """
    from pillars.skills import CharacterSkills

    # Check if already migrated
    if char_data.get("skill_points_data"):
        return CharacterSkills.from_dict(char_data["skill_points_data"])

    # Migrate from legacy format
    all_skills = []

    # Collect skills from all sources
    all_skills.extend(char_data.get("location_skills", []))
    if char_data.get("skill_track"):
        all_skills.extend(char_data["skill_track"].get("initial_skills", []))
    all_skills.extend(char_data.get("interactive_skills", []))
    all_skills.extend(char_data.get("manual_skills", []))

    # Calculate years from interactive experience
    years = char_data.get("interactive_years", 0)

    # Build CharacterSkills from legacy data
    char_skills = CharacterSkills.from_legacy_skills(all_skills, years)

    return char_skills


def allocate_skill_point(char_data, skill_name):
    """Allocate a free skill point to a skill.

    Updates char_data in place with new skill_points_data.

    Returns:
        (success: bool, error: str or None, updated_skills: list)
    """

    char_skills = build_skill_points_from_char_data(char_data)

    if char_skills.free_points <= 0:
        return False, "No free skill points available", []

    if char_skills.allocate_point(skill_name):
        # Update char_data with new skill_points_data
        char_data["skill_points_data"] = char_skills.to_dict()
        return True, None, char_skills.get_display_list()
    else:
        return False, "Failed to allocate point", []


def deallocate_skill_point(char_data, skill_name):
    """Remove an allocated point from a skill, returning it to free pool.

    Updates char_data in place.

    Returns:
        (success: bool, error: str or None, updated_skills: list)
    """
    char_skills = build_skill_points_from_char_data(char_data)

    if char_skills.deallocate_point(skill_name):
        char_data["skill_points_data"] = char_skills.to_dict()
        return True, None, char_skills.get_display_list()
    else:
        return False, "No allocated points to remove from this skill", []


def recalculate_derived(char_data):
    """Recalculate fatigue_points and body_points based on attributes."""
    attrs = char_data.get("attributes", {})

    # Get base values for calculations (the integer part)
    str_val = get_attribute_base_value(attrs.get("STR", 10))
    dex_val = get_attribute_base_value(attrs.get("DEX", 10))
    con_val = get_attribute_base_value(attrs.get("CON", 10))
    wis_val = get_attribute_base_value(attrs.get("WIS", 10))

    # Get modifiers used in fatigue/body calculations
    wis_mod = get_attribute_modifier(attrs.get("WIS", 10))
    int_mod = get_attribute_modifier(attrs.get("INT", 10))

    # Use existing rolls if available, otherwise default to 3
    fatigue_roll = attrs.get("fatigue_roll", 3)
    body_roll = attrs.get("body_roll", 3)

    # Fatigue = CON + WIS + max(DEX, STR) + 1d6 + int_mod + wis_mod
    fatigue_points = (
        con_val + wis_val + max(dex_val, str_val) + fatigue_roll + int_mod + wis_mod
    )

    # Body = CON + max(DEX, STR) + 1d6 + int_mod + wis_mod
    body_points = con_val + max(dex_val, str_val) + body_roll + int_mod + wis_mod

    # Update in char_data
    char_data["attributes"]["fatigue_points"] = fatigue_points
    char_data["attributes"]["body_points"] = body_points

    return {
        "fatigue_points": fatigue_points,
        "body_points": body_points,
        "fatigue_pool": str_val,  # Fatigue Pool = base STR value
    }


def calculate_track_info(char_data):
    """Calculate track availability info for a character without an assigned track."""
    attrs = char_data.get("attributes", {})
    str_mod = get_attribute_modifier(attrs.get("STR", 10))
    dex_mod = get_attribute_modifier(attrs.get("DEX", 10))
    int_mod = get_attribute_modifier(attrs.get("INT", 10))
    wis_mod = get_attribute_modifier(attrs.get("WIS", 10))
    social_class = char_data.get("provenance_social_class", "Commoner")
    wealth_level = char_data.get("wealth_level", "Moderate")

    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod, social_class, wealth_level
    )
    return build_track_info(track_availability)
