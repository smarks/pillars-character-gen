"""
Character serialization utilities for the Pillars Character Generator.

This module handles conversion between Character objects and JSON-serializable
dictionaries for session storage.
"""

from pillars.attributes import (
    SkillTrack,
    TrackType,
    CraftType,
    MagicSchool,
)
from ..models import SavedCharacter
from .helpers import get_modifier_for_value, consolidate_skills

# Mapping from old track names to new consolidated track names
# After track consolidation: Army/Navy -> Campaigner, Worker -> Laborer
LEGACY_TRACK_MAPPING = {
    "Army": "Campaigner",
    "Navy": "Campaigner",
    "Worker": "Laborer",
    "Officer": "Campaigner",
}


def migrate_track_name(track_name):
    """Convert old track names to new consolidated names."""
    return LEGACY_TRACK_MAPPING.get(track_name, track_name)


class MinimalCharacter:
    """Lightweight character representation for session storage.

    This class provides a minimal character object for display purposes,
    primarily needed for the skill_track when rolling more years of experience.
    """

    def __init__(self, data):
        self.attributes = type(
            "Attrs",
            (),
            {
                "STR": data["attributes"]["STR"],
                "DEX": data["attributes"]["DEX"],
                "INT": data["attributes"]["INT"],
                "WIS": data["attributes"]["WIS"],
                "CON": data["attributes"]["CON"],
                "CHR": data["attributes"]["CHR"],
                "generation_method": data["attributes"]["generation_method"],
                "fatigue_points": data["attributes"].get("fatigue_points", 0),
                "body_points": data["attributes"].get("body_points", 0),
                "fatigue_roll": data["attributes"].get("fatigue_roll", 0),
                "body_roll": data["attributes"].get("body_roll", 0),
                "get_modifier": lambda self, attr: self._get_mod(attr),
                "get_all_modifiers": lambda self: {
                    "STR": self._get_mod("STR"),
                    "DEX": self._get_mod("DEX"),
                    "INT": self._get_mod("INT"),
                    "WIS": self._get_mod("WIS"),
                    "CON": self._get_mod("CON"),
                    "CHR": self._get_mod("CHR"),
                },
                "_get_mod": lambda self, attr: get_modifier_for_value(
                    getattr(self, attr)
                ),
            },
        )()

        # Handle None skill_track (initial character without track assigned)
        if data.get("skill_track") is not None:
            migrated_track = migrate_track_name(data["skill_track"]["track"])
            self.skill_track = SkillTrack(
                track=TrackType(migrated_track),
                acceptance_check=None,
                survivability=data["skill_track"]["survivability"],
                survivability_roll=None,
                initial_skills=data["skill_track"]["initial_skills"],
                craft_type=(
                    CraftType(data["skill_track"]["craft_type"])
                    if data["skill_track"].get("craft_type")
                    else None
                ),
                craft_rolls=None,
                magic_school=(
                    MagicSchool(data["skill_track"]["magic_school"])
                    if data["skill_track"].get("magic_school")
                    else None
                ),
                magic_school_rolls=data["skill_track"].get("magic_school_rolls"),
            )
        else:
            self.skill_track = None

        self._str_repr = data["str_repr"]

    def __str__(self):
        return self._str_repr


def get_default_equipment():
    """Return default starting equipment for new characters."""
    return {
        "weapons": [
            {
                "name": "Dagger",
                "description": "Simple blade",
                "hit": "+0",
                "crit": "20",
                "damage": "1d4",
                "weight": "1",
                "value": "2 gp",
                "notes": "",
            },
        ],
        "armour": [],
        "misc": [
            {
                "name": "Backpack",
                "description": "Leather pack",
                "attr_mod": "",
                "weight": "2",
                "value": "2 gp",
            },
            {
                "name": "Waterskin",
                "description": "Holds 1 quart",
                "attr_mod": "",
                "weight": "1",
                "value": "1 gp",
            },
            {
                "name": "Rations (1 week)",
                "description": "Trail food",
                "attr_mod": "",
                "weight": "7",
                "value": "5 gp",
            },
            {
                "name": "Flint & Steel",
                "description": "Fire starter",
                "attr_mod": "",
                "weight": "0",
                "value": "1 gp",
            },
            {
                "name": "Torches (3)",
                "description": "1 hour burn each",
                "attr_mod": "",
                "weight": "3",
                "value": "3 cp",
            },
            {
                "name": "Bedroll",
                "description": "Sleeping gear",
                "attr_mod": "",
                "weight": "5",
                "value": "1 gp",
            },
            {
                "name": "Belt Pouch",
                "description": "Small pouch",
                "attr_mod": "",
                "weight": "0",
                "value": "5 sp",
            },
        ],
    }


def serialize_character(character, preserve_data=None):
    """Serialize character to JSON-compatible dict for session storage.

    Args:
        character: Character object to serialize
        preserve_data: Optional dict with fields to preserve (like 'name', 'notes')
    """
    data = {
        "attributes": {
            "STR": character.attributes.STR,
            "DEX": character.attributes.DEX,
            "INT": character.attributes.INT,
            "WIS": character.attributes.WIS,
            "CON": character.attributes.CON,
            "CHR": character.attributes.CHR,
            "generation_method": character.attributes.generation_method,
            "fatigue_points": character.attributes.fatigue_points,
            "body_points": character.attributes.body_points,
            "fatigue_roll": character.attributes.fatigue_roll,
            "body_roll": character.attributes.body_roll,
        },
        # Store just the clean values, not full description strings with roll info
        "appearance": (
            character.appearance.description
            if hasattr(character.appearance, "description")
            else str(character.appearance)
        ),
        "height": (
            character.height.imperial
            if hasattr(character.height, "imperial")
            else str(character.height)
        ),
        "weight": (
            str(int(character.weight.total_pounds))
            if hasattr(character.weight, "total_pounds")
            else str(character.weight)
        ),
        "provenance": str(character.provenance),
        "provenance_social_class": (
            character.provenance.social_class
            if hasattr(character.provenance, "social_class")
            else "Commoner"
        ),
        "provenance_sub_class": (
            character.provenance.sub_class
            if hasattr(character.provenance, "sub_class")
            else "Laborer"
        ),
        "location": str(character.location),
        "location_skills": (
            list(character.location.skills) if character.location.skills else []
        ),
        "literacy": str(character.literacy),
        "wealth": str(character.wealth),
        "wealth_level": (
            character.wealth.wealth_level
            if hasattr(character.wealth, "wealth_level")
            else "Moderate"
        ),
        "str_repr": str(character),
    }

    # Store generation rolls log
    generation_log = []

    # Attribute rolls (from roll_details which contains AttributeRoll objects)
    if (
        hasattr(character.attributes, "roll_details")
        and character.attributes.roll_details
    ):
        for roll_detail in character.attributes.roll_details:
            generation_log.append(
                {
                    "type": "attribute",
                    "name": roll_detail.attribute_name,
                    "rolls": list(roll_detail.all_rolls),
                    "result": f"{roll_detail.value} ({roll_detail.modifier:+d})",
                }
            )

    # Fatigue and Body rolls
    if character.attributes.fatigue_roll:
        generation_log.append(
            {
                "type": "derived",
                "name": "Fatigue",
                "rolls": [character.attributes.fatigue_roll],
                "result": character.attributes.fatigue_points,
            }
        )
    if character.attributes.body_roll:
        generation_log.append(
            {
                "type": "derived",
                "name": "Body",
                "rolls": [character.attributes.body_roll],
                "result": character.attributes.body_points,
            }
        )

    # Appearance roll
    if hasattr(character.appearance, "rolls"):
        generation_log.append(
            {
                "type": "physical",
                "name": "Appearance",
                "rolls": list(character.appearance.rolls),
                "result": character.appearance.description,
            }
        )

    # Height roll
    if hasattr(character.height, "rolls"):
        generation_log.append(
            {
                "type": "physical",
                "name": "Height",
                "rolls": list(character.height.rolls),
                "result": (
                    character.height.imperial
                    if hasattr(character.height, "imperial")
                    else str(character.height)
                ),
            }
        )

    # Weight roll
    if hasattr(character.weight, "rolls"):
        generation_log.append(
            {
                "type": "physical",
                "name": "Weight",
                "rolls": list(character.weight.rolls),
                "result": (
                    f"{character.weight.total_stones:.1f} stones"
                    if hasattr(character.weight, "total_stones")
                    else str(character.weight)
                ),
            }
        )

    # Provenance roll
    if hasattr(character.provenance, "main_roll"):
        prov_rolls = [character.provenance.main_roll]
        if character.provenance.sub_roll is not None:
            prov_rolls.append(character.provenance.sub_roll)
        if character.provenance.craft_roll is not None:
            prov_rolls.append(character.provenance.craft_roll)
        prov_result = character.provenance.social_class
        if character.provenance.sub_class:
            prov_result += f" - {character.provenance.sub_class}"
        generation_log.append(
            {
                "type": "background",
                "name": "Provenance",
                "rolls": prov_rolls,
                "result": prov_result,
            }
        )

    # Location roll
    if hasattr(character.location, "roll"):
        generation_log.append(
            {
                "type": "background",
                "name": "Location",
                "rolls": [character.location.roll],
                "result": character.location.location_type,
            }
        )

    # Wealth roll
    if hasattr(character.wealth, "roll"):
        generation_log.append(
            {
                "type": "background",
                "name": "Wealth",
                "rolls": [character.wealth.roll],
                "result": character.wealth.wealth_level,
            }
        )

    # Literacy roll
    if hasattr(character.literacy, "roll"):
        generation_log.append(
            {
                "type": "background",
                "name": "Literacy",
                "rolls": [character.literacy.roll],
                "result": (
                    "Literate" if character.literacy.is_literate else "Illiterate"
                ),
            }
        )

    data["generation_log"] = generation_log

    # Add default equipment if not already present
    data["equipment"] = get_default_equipment()

    # Preserve user-edited fields if provided
    if preserve_data:
        if "name" in preserve_data:
            data["name"] = preserve_data["name"]
        if "notes" in preserve_data:
            data["notes"] = preserve_data["notes"]
        if "skill_points_data" in preserve_data:
            data["skill_points_data"] = preserve_data["skill_points_data"]
        if "equipment" in preserve_data:
            data["equipment"] = preserve_data["equipment"]
        # Preserve generation_log if character object doesn't have roll data
        # (e.g., when updating a deserialized MinimalCharacter)
        if not data.get("generation_log") and "generation_log" in preserve_data:
            data["generation_log"] = preserve_data["generation_log"]

    # Only include skill_track if it exists
    if character.skill_track is not None:
        data["skill_track"] = {
            "track": character.skill_track.track.value,
            "survivability": character.skill_track.survivability,
            "initial_skills": list(character.skill_track.initial_skills),
            "craft_type": (
                character.skill_track.craft_type.value
                if character.skill_track.craft_type
                else None
            ),
            "magic_school": (
                character.skill_track.magic_school.value
                if character.skill_track.magic_school
                else None
            ),
            "magic_school_rolls": character.skill_track.magic_school_rolls,
        }
    else:
        data["skill_track"] = None

    return data


def deserialize_character(data):
    """Deserialize character from session data.

    Args:
        data: Dict from serialize_character or session storage

    Returns:
        MinimalCharacter instance
    """
    return MinimalCharacter(data)


def build_final_str_repr(char_data, years, skills, yearly_results, aging_data, died):
    """Build a complete str_repr for a character with prior experience."""
    # Start with the base character info (without skill track/experience sections)
    base_repr = char_data.get("str_repr", "")

    # If no experience, return base repr
    if years == 0:
        return base_repr

    # Filter out sections we'll rebuild, and location skill/attribute lines
    lines = base_repr.split("\n")
    filtered_lines = []
    skip_section = False
    in_location = False

    for line in lines:
        # Check for sections to skip entirely
        if any(
            marker in line
            for marker in [
                "**Skill Track:**",
                "**Prior Experience**",
                "**Skills**",
                "**Year-by-Year**",
            ]
        ):
            skip_section = True
            continue

        # Track if we're in Location section (to filter its sub-items)
        if line.startswith("Location:"):
            in_location = True
            filtered_lines.append(line)
            continue

        # Skip location sub-items (Skills, Attribute Modifiers)
        if in_location:
            if line.startswith("  "):
                # Skip indented location details (skills, attribute modifiers)
                continue
            else:
                # No longer in location section
                in_location = False

        # Handle skipped sections
        if skip_section:
            # End skip on blank line or new ** section
            if line.strip() == "":
                skip_section = False
                continue
            elif line.startswith("**"):
                skip_section = False
                # Check if this new section should also be skipped
                if any(
                    marker in line
                    for marker in [
                        "**Skill Track:**",
                        "**Prior Experience**",
                        "**Skills**",
                        "**Year-by-Year**",
                    ]
                ):
                    skip_section = True
                    continue
                filtered_lines.append(line)
            continue

        filtered_lines.append(line)

    result_lines = filtered_lines

    # Add skill track info
    if char_data.get("skill_track"):
        track_info = char_data["skill_track"]
        result_lines.append("")
        result_lines.append(f"**Skill Track:** {track_info['track']}")
        result_lines.append(f"Survivability: {track_info['survivability']}+")
        if track_info.get("craft_type"):
            result_lines.append(f"Craft: {track_info['craft_type']}")
        if track_info.get("magic_school"):
            result_lines.append(f"Magic School: {track_info['magic_school']}")

    # Add prior experience section
    result_lines.append("")
    result_lines.append("**Prior Experience**")
    result_lines.append("Starting Age: 16")

    if died and yearly_results:
        death_age = yearly_results[-1]["year"]
        result_lines.append(f"DIED at age {death_age}!")
    else:
        result_lines.append(f"Final Age: {16 + years}")

    result_lines.append(f"Years Served: {years}")

    if yearly_results:
        result_lines.append(
            f"Survivability Target: {yearly_results[0]['surv_target']}+"
        )

        # Calculate total modifier from first year result
        result_lines.append(f"Total Modifier: {yearly_results[0]['surv_mod']:+d}")

    # Show aging penalties if any
    has_aging = any(v != 0 for v in aging_data.values())
    if has_aging:
        penalties = []
        if aging_data.get("str"):
            penalties.append(f"STR {aging_data['str']:+d}")
        if aging_data.get("dex"):
            penalties.append(f"DEX {aging_data['dex']:+d}")
        if aging_data.get("int"):
            penalties.append(f"INT {aging_data['int']:+d}")
        if aging_data.get("wis"):
            penalties.append(f"WIS {aging_data['wis']:+d}")
        if aging_data.get("con"):
            penalties.append(f"CON {aging_data['con']:+d}")
        result_lines.append("")
        result_lines.append(f"**Aging Penalties:** {', '.join(penalties)}")

    if died:
        result_lines.append("")
        result_lines.append("**THIS CHARACTER DIED DURING PRIOR EXPERIENCE!**")

    # Add consolidated skills section
    all_skills = []

    # Add location skills
    location_skills = char_data.get("location_skills", [])
    all_skills.extend(location_skills)

    # Add track initial skills and prior experience skills
    initial_skills = (
        char_data.get("skill_track", {}).get("initial_skills", [])
        if char_data.get("skill_track")
        else []
    )
    all_skills.extend(initial_skills)
    all_skills.extend(skills)

    if all_skills:
        result_lines.append("")
        result_lines.append(f"**Skills** ({len(all_skills)})")
        for skill in consolidate_skills(all_skills):
            result_lines.append(f"- {skill}")

    # Add Year-by-Year log at the bottom
    if yearly_results:
        result_lines.append("")
        result_lines.append("**Year-by-Year Log**")

        for yr in yearly_results:
            status = "Survived" if yr["survived"] else "DIED"
            mod_str = f"{yr['surv_mod']:+d}"
            line = (
                f"Year {yr['year']}: {yr['skill']} (+1 SP) | "
                f"Survival: {yr['surv_roll']}{mod_str}={yr['surv_total']} vs {yr['surv_target']}+ [{status}]"
            )
            if yr.get("aging"):
                penalties = [
                    f"{k.upper()} {v:+d}" for k, v in yr["aging"].items() if v != 0
                ]
                if penalties:
                    line += f" | AGING: {', '.join(penalties)}"
            result_lines.append(line)

    return "\n".join(result_lines)


def store_current_character(request, character, preserve_data=None):
    """Store character in session for the generator flow.

    If user is logged in, also save to database and return the saved character ID.

    Args:
        request: Django request object
        character: Character object to store
        preserve_data: Optional dict with fields to preserve (like 'name', 'notes')
    """
    # Get existing char_data to preserve user-edited fields
    existing_data = request.session.get("current_character", {})
    if preserve_data:
        existing_data.update(preserve_data)

    char_data = serialize_character(character, preserve_data=existing_data)

    # Set default name from player username if not already set
    if not char_data.get("name") and request.user.is_authenticated:
        char_data["name"] = request.user.username

    request.session["current_character"] = char_data
    # Clear any prior experience data when re-rolling
    request.session["interactive_years"] = 0
    request.session["interactive_skills"] = []
    request.session["interactive_yearly_results"] = []
    request.session["interactive_aging"] = {
        "str": 0,
        "dex": 0,
        "int": 0,
        "wis": 0,
        "con": 0,
    }
    request.session["interactive_died"] = False
    request.session.modified = True

    # Auto-save to database if user is logged in
    saved_char_id = None
    if request.user.is_authenticated:
        # Create a new saved character
        char_count = SavedCharacter.objects.filter(user=request.user).count() + 1
        saved_char = SavedCharacter.objects.create(
            user=request.user,
            name=f"Character {char_count}",
            description=char_data.get("description", ""),
            character_data=char_data,
        )
        saved_char_id = saved_char.id
        request.session["current_saved_character_id"] = saved_char_id

    return saved_char_id
