"""
Helper functions for character sheet views.

These are internal helpers for skill points management and attribute calculations.
"""

import re
from pillars.attributes import get_track_availability

from .helpers import (
    build_track_info,
    get_attribute_modifier,
    get_attribute_base_value,
)


def parse_equipment_bonuses(char_data):
    """Parse equipment attr_mod fields and return bonuses by attribute.

    Parses formats like:
    - "+5 STR"
    - "+3 DEX, +2 CON"
    - "STR +5"

    Returns dict like {"STR": 5, "DEX": 3} and sources dict {"STR": ["Girdle"], "DEX": ["Ring"]}
    """
    bonuses = {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0, "CHR": 0}
    sources = {"STR": [], "DEX": [], "INT": [], "WIS": [], "CON": [], "CHR": []}

    equipment = char_data.get("equipment", {})
    if not equipment or not isinstance(equipment, dict):
        return bonuses, sources

    # Check all equipment categories for attr_mod
    for category in ["misc", "armour", "weapons"]:
        items = equipment.get(category, [])
        if not isinstance(items, list):
            continue
        for item in items:
            # Only count equipped items
            if item.get("equipped") is False:
                continue

            attr_mod = item.get("attr_mod", "") or item.get("attrMod", "")
            if not attr_mod:
                continue

            item_name = item.get("name", "Equipment")

            # Parse patterns like "+5 STR" or "STR +5" or "+3 DEX, +2 CON"
            # Pattern: optional sign, number, optional whitespace, attribute name
            # OR: attribute name, optional whitespace, optional sign, number
            pattern = (
                r"([+-]?\d+)\s*(STR|DEX|INT|WIS|CON|CHR)|"
                r"(STR|DEX|INT|WIS|CON|CHR)\s*([+-]?\d+)"
            )

            for match in re.finditer(pattern, attr_mod, re.IGNORECASE):
                if match.group(1) and match.group(2):
                    # Format: "+5 STR"
                    value = int(match.group(1))
                    attr = match.group(2).upper()
                elif match.group(3) and match.group(4):
                    # Format: "STR +5"
                    attr = match.group(3).upper()
                    value = int(match.group(4))
                else:
                    continue

                if attr in bonuses:
                    bonuses[attr] += value
                    sources[attr].append(item_name)

    return bonuses, sources


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
    from pillars.skills import SkillPoints

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

    # Restore allocated points that were spent before rebuild
    allocated_by_skill = char_data.get("allocated_points_by_skill", {})
    for norm_name, alloc_data in allocated_by_skill.items():
        allocated = alloc_data.get("allocated", 0)
        display_name = alloc_data.get("display_name", norm_name)

        if allocated > 0:
            # Create or update the skill with allocated points
            if norm_name not in char_skills.skills:
                char_skills.skills[norm_name] = SkillPoints(display_name=display_name)
            char_skills.skills[norm_name].allocated = allocated
            # Subtract from free points (they were already spent)
            char_skills.free_points = max(0, char_skills.free_points - allocated)

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


def calculate_adjusted_attributes(char_data):
    """Calculate adjusted attribute values after aging penalties and equipment bonuses.

    Returns dict with:
    - {attr}_adjusted: effective value after penalties and bonuses
    - {attr}_adj_mod: modifier based on adjusted value
    - {attr}_sources: list of modification sources (e.g., "aging, Girdle")
    """
    attrs = char_data.get("attributes", {})
    aging = char_data.get("interactive_aging", {})

    # Get equipment bonuses
    equip_bonuses, equip_sources = parse_equipment_bonuses(char_data)

    result = {}
    for attr in ["STR", "DEX", "INT", "WIS", "CON"]:
        base_val = get_attribute_base_value(attrs.get(attr, 10))
        penalty = aging.get(attr.lower(), 0)
        bonus = equip_bonuses.get(attr, 0)

        # Penalty is stored as negative (e.g., -1), so add it to subtract
        # Bonus is positive from equipment
        adjusted = base_val + penalty + bonus
        adj_mod = get_attribute_modifier(adjusted)

        # Track sources of modifications
        sources = []
        if penalty != 0:
            sources.append("aging")
        # Add equipment sources
        sources.extend(equip_sources.get(attr, []))

        result[f"{attr.lower()}_adjusted"] = adjusted
        result[f"{attr.lower()}_adj_mod"] = adj_mod
        result[f"{attr.lower()}_sources"] = ", ".join(sources) if sources else ""

    # CHR has no aging penalty but can have equipment bonuses
    chr_val = get_attribute_base_value(attrs.get("CHR", 10))
    chr_bonus = equip_bonuses.get("CHR", 0)
    chr_adjusted = chr_val + chr_bonus
    chr_sources = equip_sources.get("CHR", [])

    result["chr_adjusted"] = chr_adjusted
    result["chr_adj_mod"] = get_attribute_modifier(chr_adjusted)
    result["chr_sources"] = ", ".join(chr_sources) if chr_sources else ""

    return result


def recalculate_derived(char_data):
    """Recalculate fatigue_points, body_points, and adjusted attributes."""
    attrs = char_data.get("attributes", {})
    aging = char_data.get("interactive_aging", {})

    # Get equipment bonuses
    equip_bonuses, _ = parse_equipment_bonuses(char_data)

    # Get base values for calculations (the integer part)
    str_val = get_attribute_base_value(attrs.get("STR", 10))
    dex_val = get_attribute_base_value(attrs.get("DEX", 10))
    con_val = get_attribute_base_value(attrs.get("CON", 10))
    wis_val = get_attribute_base_value(attrs.get("WIS", 10))
    int_val = get_attribute_base_value(attrs.get("INT", 10))

    # Apply aging penalties (stored as negative) and equipment bonuses
    # aging.get("str", 0) is negative (e.g., -1), so we ADD it to subtract
    str_adj = str_val + aging.get("str", 0) + equip_bonuses.get("STR", 0)
    dex_adj = dex_val + aging.get("dex", 0) + equip_bonuses.get("DEX", 0)
    con_adj = con_val + aging.get("con", 0) + equip_bonuses.get("CON", 0)
    wis_adj = wis_val + aging.get("wis", 0) + equip_bonuses.get("WIS", 0)
    int_adj = int_val + aging.get("int", 0) + equip_bonuses.get("INT", 0)

    # Get modifiers from adjusted values
    wis_mod = get_attribute_modifier(wis_adj)
    int_mod = get_attribute_modifier(int_adj)

    # Use existing rolls if available, otherwise default to 3
    fatigue_roll = attrs.get("fatigue_roll", 3)
    body_roll = attrs.get("body_roll", 3)

    # Fatigue = CON + WIS + max(DEX, STR) + 1d6 + int_mod + wis_mod
    fatigue_points = (
        con_adj + wis_adj + max(dex_adj, str_adj) + fatigue_roll + int_mod + wis_mod
    )

    # Body = CON + max(DEX, STR) + 1d6 + int_mod + wis_mod
    body_points = con_adj + max(dex_adj, str_adj) + body_roll + int_mod + wis_mod

    # Update in char_data
    char_data["attributes"]["fatigue_points"] = fatigue_points
    char_data["attributes"]["body_points"] = body_points

    result = {
        "fatigue_points": fatigue_points,
        "body_points": body_points,
        "fatigue_pool": str_adj,  # Fatigue Pool = adjusted STR value
    }

    # Add adjusted attribute values and modifiers
    result.update(calculate_adjusted_attributes(char_data))

    return result


def calculate_track_info(char_data):
    """Calculate track availability info for a character without an assigned track."""
    attrs = char_data.get("attributes", {})
    str_mod = get_attribute_modifier(attrs.get("STR", 10))
    dex_mod = get_attribute_modifier(attrs.get("DEX", 10))
    int_mod = get_attribute_modifier(attrs.get("INT", 10))
    wis_mod = get_attribute_modifier(attrs.get("WIS", 10))
    chr_mod = get_attribute_modifier(attrs.get("CHR", 10))
    social_class = char_data.get("provenance_social_class", "Commoner")
    wealth_level = char_data.get("wealth_level", "Moderate")

    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod, chr_mod, social_class, wealth_level
    )
    return build_track_info(track_availability)


def generate_brief_description(char_data):
    """Generate a brief auto-description for a character.

    Format: "Age X, [Provenance] from [Location], [Track]"
    Example: "Age 23, Noble from the City, Ranger"
    """
    parts = []

    # Age
    base_age = char_data.get("base_age", 16)
    years = char_data.get("interactive_years", 0)
    age = base_age + years
    parts.append(f"Age {age}")

    # Provenance (social class or sub-class if available)
    provenance = char_data.get("provenance_sub_class") or char_data.get(
        "provenance_social_class"
    )
    if provenance:
        parts.append(provenance)

    # Location
    location = char_data.get("location")
    if location:
        parts.append(f"from {location}")

    # Track (if has prior experience)
    skill_track = char_data.get("skill_track", {})
    if skill_track:
        track_name = skill_track.get("track")
        if track_name:
            parts.append(track_name)

    return ", ".join(parts) if parts else "New character"
