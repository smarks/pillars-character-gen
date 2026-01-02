"""
Skill track generation for Pillars RPG.

This module handles the generation and management of skill tracks,
including acceptance checks and track selection.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random
from pillars.dice import roll_dice, roll_die, roll_percentile
from pillars.enums import TrackType, CraftType, MagicSchool
from pillars.constants import (
    MAGIC_SPELL_PROGRESSION,
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
)
from pillars.config import (
    ARMY_ACCEPTANCE_TARGET,
    NAVY_ACCEPTANCE_TARGET,
    MERCHANT_ACCEPTANCE_TARGETS,
    MAGIC_COMMON_THRESHOLD,
)


__all__ = [
    # Classes
    "AcceptanceCheck",
    "SkillTrack",
    # Functions
    "create_auto_accept_check",
    "roll_survivability_random",
    "roll_craft_type",
    "roll_magic_school",
    "check_magic_acceptance",
    "check_army_acceptance",
    "check_navy_acceptance",
    "check_ranger_acceptance",
    "check_officer_acceptance",
    "check_merchant_acceptance",
    "is_rich",
    "is_poor",
    "is_working_class",
    "calculate_roll_availability",
    "get_track_availability",
    "get_magic_initial_skills",
    "build_skill_track",
    "create_skill_track_for_choice",
    "get_eligible_tracks",
    "select_optimal_track",
    "roll_skill_track",
]


@dataclass
class AcceptanceCheck:
    """Stores the result of a track acceptance check."""

    track: TrackType
    accepted: bool
    roll: Optional[int]
    target: Optional[int]
    modifiers: Dict[str, int]
    reason: str

    def __str__(self) -> str:
        if self.roll is not None:
            mod_parts = [f"{attr} {mod:+d}" for attr, mod in self.modifiers.items()]
            mod_str = " + ".join(mod_parts) if mod_parts else "no modifiers"
            return (
                f"{self.track.value}: {'Accepted' if self.accepted else 'Rejected'} "
                f"(Rolled {self.roll} + {mod_str} vs {self.target}+) - {self.reason}"
            )
        return f"{self.track.value}: {'Accepted' if self.accepted else 'Rejected'} - {self.reason}"


def create_auto_accept_check(
    track: TrackType, reason: str = "No requirements"
) -> AcceptanceCheck:
    """Create an AcceptanceCheck for tracks that auto-accept."""
    return AcceptanceCheck(
        track=track, accepted=True, roll=None, target=None, modifiers={}, reason=reason
    )


@dataclass
class SkillTrack:
    """Stores the selected skill track and related information."""

    track: TrackType
    acceptance_check: Optional[AcceptanceCheck]
    survivability: int
    survivability_roll: Optional[int]  # For Random track
    initial_skills: List[str]
    craft_type: Optional[CraftType]  # For Crafts track
    craft_rolls: Optional[List[int]]  # Rolls made to determine craft
    magic_school: Optional[MagicSchool] = None  # For Magic track
    magic_school_rolls: Optional[Dict[str, int]] = (
        None  # Rolls made to determine school
    )

    def __str__(self) -> str:
        lines = [f"Skill Track: {self.track.value}"]
        if self.survivability_roll is not None:
            lines.append(
                f"  Survivability: {self.survivability} (Rolled: {self.survivability_roll})"
            )
        else:
            lines.append(f"  Survivability: {self.survivability}")

        if self.craft_type:
            rolls_str = (
                ", ".join(map(str, self.craft_rolls)) if self.craft_rolls else ""
            )
            lines.append(f"  Craft: {self.craft_type.value} (Rolled: [{rolls_str}])")

        if self.magic_school:
            rolls_info = ""
            if self.magic_school_rolls:
                rolls_info = f" (Percentile: {self.magic_school_rolls.get('percentile', '?')}, School: {self.magic_school_rolls.get('school', '?')})"
            lines.append(f"  Magic School: {self.magic_school.value}{rolls_info}")

        lines.append(f"  Initial Skills: {', '.join(self.initial_skills)}")

        if self.acceptance_check:
            lines.append(f"  {self.acceptance_check}")

        return "\n".join(lines)


def roll_survivability_random() -> Tuple[int, int]:
    """
    Roll survivability for Random track (d8, reroll 5s).

    Returns:
        Tuple of (final survivability value, the roll that produced it)
    """
    roll = roll_die(8)
    while roll == 5:
        roll = roll_die(8)
    return roll, roll


def roll_craft_type() -> Tuple[CraftType, List[int]]:
    """
    Roll for craft specialization using the crafts sub-table.

    Returns:
        Tuple of (CraftType, list of rolls made)
    """
    rolls = []
    main_roll = roll_die(6)
    rolls.append(main_roll)

    if main_roll == 1:
        return CraftType.SMITH, rolls
    elif main_roll == 2:
        return CraftType.AGRICULTURE, rolls
    elif main_roll == 3:
        return CraftType.TAILOR, rolls
    elif main_roll == 4:
        # Science OR Builder - roll again to determine
        sub_roll = roll_die(6)
        rolls.append(sub_roll)
        if sub_roll <= 2:
            return CraftType.SCIENCE_MAPS, rolls
        elif sub_roll <= 4:
            return CraftType.SCIENCE_POTIONS, rolls
        else:
            # Physics OR Builder - roll d4 for builder type
            builder_roll = roll_die(4)
            rolls.append(builder_roll)
            if builder_roll == 1:
                return CraftType.BUILDER_WAINWRIGHT, rolls
            elif builder_roll == 2:
                return CraftType.BUILDER_SHIPWRIGHT, rolls
            elif builder_roll == 3:
                return CraftType.BUILDER_MASON, rolls
            else:
                return CraftType.BUILDER_STRUCTURES, rolls
    elif main_roll == 5:
        return CraftType.MEDICAL, rolls
    else:  # main_roll == 6
        return CraftType.MAGIC, rolls


def roll_magic_school() -> Tuple[MagicSchool, Dict[str, int]]:
    """
    Roll for magic school using percentile and sub-tables.

    PERCENTILE | SCHOOL TYPE
    0-70       | Common Schools of Magic
    71-100     | Less Common Schools of Magic

    Returns:
        Tuple of (MagicSchool, dict of rolls made)
    """
    rolls = {}

    # Roll percentile (1-100)
    percentile = roll_percentile()
    rolls["percentile"] = percentile

    if percentile <= MAGIC_COMMON_THRESHOLD:
        # Common Schools - roll d12
        school_roll = roll_die(12)
        rolls["school"] = school_roll

        if school_roll <= 3:
            return MagicSchool.ELEMENTAL_FIRE, rolls
        elif school_roll <= 5:
            return MagicSchool.ELEMENTAL_LIGHTNING, rolls
        elif school_roll == 6:
            return MagicSchool.ELEMENTAL_WATER, rolls
        elif school_roll == 7:
            return MagicSchool.ELEMENTAL_EARTH, rolls
        elif school_roll == 8:
            return MagicSchool.ELEMENTAL_WIND, rolls
        elif school_roll == 9:
            return MagicSchool.ALL_ELEMENTS, rolls
        elif school_roll == 10:
            return MagicSchool.PASSAGE, rolls
        elif school_roll == 11:
            return MagicSchool.PROTECTION, rolls
        else:  # school_roll == 12
            return MagicSchool.MENDING, rolls
    else:
        # Less Common Schools - roll d6
        school_roll = roll_die(6)
        rolls["school"] = school_roll

        if school_roll <= 3:
            return MagicSchool.WEATHER, rolls
        elif school_roll == 4:
            return MagicSchool.COUNTER, rolls
        elif school_roll == 5:
            return MagicSchool.ARCANE_HELP, rolls
        else:  # school_roll == 6
            return MagicSchool.CONTROL, rolls


def check_magic_acceptance(int_mod: int, wis_mod: int) -> AcceptanceCheck:
    """
    Check if character meets Magic track requirements.
    Requirement: INT or WIS bonus required (magic requires mental aptitude)
    """
    has_mental = int_mod > 0 or wis_mod > 0
    accepted = has_mental

    if has_mental:
        reason = f"Has INT({int_mod:+d}) or WIS({wis_mod:+d}) bonus"
    else:
        reason = "No INT or WIS bonus - magic requires mental aptitude"

    return AcceptanceCheck(
        track=TrackType.MAGIC,
        accepted=accepted,
        roll=None,
        target=None,
        modifiers={"INT": int_mod, "WIS": wis_mod},
        reason=reason,
    )


def check_army_acceptance(str_mod: int, dex_mod: int) -> AcceptanceCheck:
    """
    Check if character meets Army track requirements.
    Requirement: ARMY_ACCEPTANCE_TARGET+ on 2d6 + STR/DEX modifiers
    """
    roll = sum(roll_dice(2, 6))
    total = roll + str_mod + dex_mod
    target = ARMY_ACCEPTANCE_TARGET
    accepted = total >= target

    return AcceptanceCheck(
        track=TrackType.ARMY,
        accepted=accepted,
        roll=roll,
        target=target,
        modifiers={"STR": str_mod, "DEX": dex_mod},
        reason=f"Total {total} {'≥' if accepted else '<'} {target}",
    )


def check_navy_acceptance(str_mod: int, dex_mod: int, int_mod: int) -> AcceptanceCheck:
    """
    Check if character meets Navy track requirements.
    Requirement: NAVY_ACCEPTANCE_TARGET+ on 2d6 + STR/DEX/INT modifiers
    """
    roll = sum(roll_dice(2, 6))
    total = roll + str_mod + dex_mod + int_mod
    target = NAVY_ACCEPTANCE_TARGET
    accepted = total >= target

    return AcceptanceCheck(
        track=TrackType.NAVY,
        accepted=accepted,
        roll=roll,
        target=target,
        modifiers={"STR": str_mod, "DEX": dex_mod, "INT": int_mod},
        reason=f"Total {total} {'≥' if accepted else '<'} {target}",
    )


def check_ranger_acceptance(
    str_mod: int, dex_mod: int, int_mod: int, wis_mod: int
) -> AcceptanceCheck:
    """
    Check if character meets Ranger track requirements.
    Requirement: STR or DEX bonus required AND INT or WIS bonus required
    """
    has_physical = str_mod > 0 or dex_mod > 0
    has_mental = int_mod > 0 or wis_mod > 0
    accepted = has_physical and has_mental

    reason_parts = []
    if has_physical:
        reason_parts.append("Has STR/DEX bonus")
    else:
        reason_parts.append("No STR/DEX bonus")
    if has_mental:
        reason_parts.append("Has INT/WIS bonus")
    else:
        reason_parts.append("No INT/WIS bonus")

    return AcceptanceCheck(
        track=TrackType.RANGER,
        accepted=accepted,
        roll=None,
        target=None,
        modifiers={"STR": str_mod, "DEX": dex_mod, "INT": int_mod, "WIS": wis_mod},
        reason="; ".join(reason_parts),
    )


def check_officer_acceptance(
    wealth_level: str, is_promoted: bool = False
) -> AcceptanceCheck:
    """
    Check if character meets Officer track requirements.
    Requirement: Must be promoted OR be Rich
    """
    rich = is_rich(wealth_level)
    accepted = rich or is_promoted

    if is_promoted:
        reason = "Promoted to Officer"
    elif rich:
        reason = "Rich wealth level"
    else:
        reason = "Not promoted and not Rich"

    return AcceptanceCheck(
        track=TrackType.OFFICER,
        accepted=accepted,
        roll=None,
        target=None,
        modifiers={},
        reason=reason,
    )


def is_rich(wealth_level: str) -> bool:
    """Check if wealth level is Rich."""
    return wealth_level == "Rich"


def is_poor(wealth_level: str) -> bool:
    """Check if wealth level is Subsistence."""
    return wealth_level == "Subsistence"


def is_working_class(wealth_level: str, social_class: str) -> bool:
    """Check if character is working class."""
    return wealth_level == "Moderate" and social_class in ["Commoner", "Laborer"]


def check_merchant_acceptance(social_class: str, wealth_level: str) -> AcceptanceCheck:
    """
    Check if character meets Merchant track requirements.
    Requirements based on social standing (see MERCHANT_ACCEPTANCE_TARGETS).
    """
    roll = sum(roll_dice(2, 6))

    # Determine target based on social standing
    is_poor_val = is_poor(wealth_level)
    is_working_class_val = is_working_class(wealth_level, social_class)

    if is_poor_val:
        target = MERCHANT_ACCEPTANCE_TARGETS["poor"]
        class_desc = "poor"
    elif is_working_class_val:
        target = MERCHANT_ACCEPTANCE_TARGETS["working"]
        class_desc = "working class"
    else:
        target = MERCHANT_ACCEPTANCE_TARGETS["above"]
        class_desc = "above working class"

    accepted = roll >= target

    return AcceptanceCheck(
        track=TrackType.MERCHANT,
        accepted=accepted,
        roll=roll,
        target=target,
        modifiers={},
        reason=f"Roll {roll} {'≥' if accepted else '<'} {target} ({class_desc})",
    )


def calculate_roll_availability(
    min_roll: int,
    max_roll: int,
    total_modifier: int,
    target: int,
    requirement_desc: str,
) -> Dict:
    """
    Calculate track availability based on roll range and modifier.

    Args:
        min_roll: Minimum possible roll (e.g., 2 for 2d6)
        max_roll: Maximum possible roll (e.g., 12 for 2d6)
        total_modifier: Total modifier to add to roll
        target: Target number to meet or exceed
        requirement_desc: Description of the requirement

    Returns:
        Dictionary with availability information
    """
    min_total = min_roll + total_modifier
    max_total = max_roll + total_modifier

    return {
        "available": max_total >= target,
        "requires_roll": True,
        "auto_accept": min_total >= target,
        "impossible": max_total < target,
        "requirement": requirement_desc,
        "roll_info": f"Need {target}+, your modifier: {total_modifier:+d}",
    }


def get_track_availability(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    wealth_level: str,
    is_promoted: bool = False,
) -> Dict[TrackType, Dict]:
    """
    Get availability status for all tracks without rolling dice.
    Used to show which tracks are available for user selection.

    Returns:
        Dict mapping TrackType to availability info:
        {
            'available': bool - True if always available or can attempt
            'requires_roll': bool - True if acceptance requires dice roll
            'auto_accept': bool - True if no requirements
            'impossible': bool - True if character can never qualify
            'requirement': str - Description of requirements
            'roll_info': str - Info about the acceptance roll if applicable
        }
    """
    availability = {}

    # Always available tracks (no requirements)
    for track in [TrackType.RANDOM, TrackType.WORKER, TrackType.CRAFTS]:
        availability[track] = {
            "available": True,
            "requires_roll": False,
            "auto_accept": True,
            "impossible": False,
            "requirement": "No requirements",
            "roll_info": None,
        }

    # Army: 8+ on 2d6 + STR + DEX
    total_mod = str_mod + dex_mod
    availability[TrackType.ARMY] = calculate_roll_availability(
        min_roll=2,
        max_roll=12,
        total_modifier=total_mod,
        target=8,
        requirement_desc=f"2d6 + STR({str_mod:+d}) + DEX({dex_mod:+d}) >= 8",
    )

    # Navy: 8+ on 2d6 + STR + DEX + INT
    total_mod = str_mod + dex_mod + int_mod
    availability[TrackType.NAVY] = calculate_roll_availability(
        min_roll=2,
        max_roll=12,
        total_modifier=total_mod,
        target=8,
        requirement_desc=f"2d6 + STR({str_mod:+d}) + DEX({dex_mod:+d}) + INT({int_mod:+d}) >= 8",
    )

    # Ranger: Need STR or DEX bonus AND INT or WIS bonus (no roll)
    has_physical = str_mod > 0 or dex_mod > 0
    has_mental = int_mod > 0 or wis_mod > 0
    ranger_eligible = has_physical and has_mental
    availability[TrackType.RANGER] = {
        "available": ranger_eligible,
        "requires_roll": False,
        "auto_accept": ranger_eligible,
        "impossible": not ranger_eligible,
        "requirement": "Requires STR or DEX bonus AND INT or WIS bonus",
        "roll_info": None,
    }

    # Officer: Must be Rich or promoted (no roll)
    officer_eligible = is_rich(wealth_level) or is_promoted
    availability[TrackType.OFFICER] = {
        "available": officer_eligible,
        "requires_roll": False,
        "auto_accept": officer_eligible,
        "impossible": not officer_eligible,
        "requirement": "Requires Rich wealth or promotion",
        "roll_info": None,
    }

    # Merchant: 2d6 vs variable target based on social standing
    if is_poor(wealth_level):
        target = MERCHANT_ACCEPTANCE_TARGETS["poor"]
        class_desc = "poor"
    elif is_working_class(wealth_level, social_class):
        target = MERCHANT_ACCEPTANCE_TARGETS["working"]
        class_desc = "working class"
    else:
        target = MERCHANT_ACCEPTANCE_TARGETS["above"]
        class_desc = "above working class"

    availability[TrackType.MERCHANT] = calculate_roll_availability(
        min_roll=2,
        max_roll=12,
        total_modifier=0,  # No attribute modifiers for merchant
        target=target,
        requirement_desc=f"2d6 >= {target} ({class_desc})",
    )

    # Magic track: Requires INT or WIS bonus (no roll, just attribute check)
    has_mental = int_mod > 0 or wis_mod > 0
    availability[TrackType.MAGIC] = {
        "available": has_mental,
        "requires_roll": False,
        "auto_accept": has_mental,
        "impossible": not has_mental,
        "requirement": "Requires INT or WIS bonus",
        "roll_info": None,
    }

    return availability


def get_magic_initial_skills(magic_school: MagicSchool) -> List[str]:
    """Get initial skills for a magic school track."""
    spells = MAGIC_SPELL_PROGRESSION.get(magic_school, [])
    skills = []
    if spells:
        skills.append(f"Spell: {spells[0]}")
    skills.append(f"School: {magic_school.value}")
    return skills


def build_skill_track(
    track: TrackType,
    acceptance_check: AcceptanceCheck,
    sub_class: str,
    wealth_level: str,
) -> SkillTrack:
    """
    Build a complete SkillTrack object from track type and acceptance check.

    Args:
        track: The track type
        acceptance_check: The acceptance check result
        sub_class: Character's sub-class
        wealth_level: Character's wealth level

    Returns:
        Complete SkillTrack object
    """
    # If not accepted, return with failure
    if not acceptance_check.accepted:
        return SkillTrack(
            track=track,
            acceptance_check=acceptance_check,
            survivability=0,
            survivability_roll=None,
            initial_skills=[],
            craft_type=None,
            craft_rolls=None,
        )

    # Determine survivability
    survivability_roll = None
    if track == TrackType.RANDOM:
        survivability, survivability_roll = roll_survivability_random()
    else:
        survivability = TRACK_SURVIVABILITY.get(track, 5)
        if survivability is None:
            survivability = 5

    # Get initial skills
    initial_skills = list(TRACK_INITIAL_SKILLS.get(track, []))

    # Handle special cases
    craft_type = None
    craft_rolls = None
    magic_school = None
    magic_school_rolls = None

    if track == TrackType.WORKER:
        if wealth_level == "Subsistence" or sub_class == "Laborer":
            initial_skills.append("Laborer (bonus)")
    elif track == TrackType.CRAFTS:
        craft_type, craft_rolls = roll_craft_type()
        initial_skills.append(f"Craft: {craft_type.value}")
    elif track == TrackType.MAGIC:
        magic_school, magic_school_rolls = roll_magic_school()
        initial_skills.extend(get_magic_initial_skills(magic_school))

    return SkillTrack(
        track=track,
        acceptance_check=acceptance_check,
        survivability=survivability,
        survivability_roll=survivability_roll,
        initial_skills=initial_skills,
        craft_type=craft_type,
        craft_rolls=craft_rolls,
        magic_school=magic_school,
        magic_school_rolls=magic_school_rolls,
    )


def create_skill_track_for_choice(
    chosen_track: TrackType,
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    sub_class: str,
    wealth_level: str,
    is_promoted: bool = False,
) -> SkillTrack:
    """
    Create a skill track for a user-chosen track, rolling for acceptance if needed.

    Args:
        chosen_track: The track the user wants
        Other args: Character stats for acceptance checks

    Returns:
        SkillTrack object (may have accepted=False if roll failed)
    """
    # Determine acceptance
    acceptance_check = None

    if chosen_track == TrackType.RANDOM:
        acceptance_check = create_auto_accept_check(TrackType.RANDOM)
    elif chosen_track == TrackType.WORKER:
        acceptance_check = create_auto_accept_check(TrackType.WORKER)
    elif chosen_track == TrackType.CRAFTS:
        acceptance_check = create_auto_accept_check(TrackType.CRAFTS)
    elif chosen_track == TrackType.ARMY:
        acceptance_check = check_army_acceptance(str_mod, dex_mod)
    elif chosen_track == TrackType.NAVY:
        acceptance_check = check_navy_acceptance(str_mod, dex_mod, int_mod)
    elif chosen_track == TrackType.RANGER:
        acceptance_check = check_ranger_acceptance(str_mod, dex_mod, int_mod, wis_mod)
    elif chosen_track == TrackType.OFFICER:
        acceptance_check = check_officer_acceptance(wealth_level, is_promoted)
    elif chosen_track == TrackType.MERCHANT:
        acceptance_check = check_merchant_acceptance(social_class, wealth_level)
    elif chosen_track == TrackType.MAGIC:
        acceptance_check = check_magic_acceptance(int_mod, wis_mod)
    else:
        # Unknown track
        acceptance_check = AcceptanceCheck(
            track=chosen_track,
            accepted=False,
            roll=None,
            target=None,
            modifiers={},
            reason="Unknown track",
        )

    # Build the skill track using the helper function
    return build_skill_track(chosen_track, acceptance_check, sub_class, wealth_level)


def get_eligible_tracks(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    wealth_level: str,
    is_promoted: bool = False,
) -> List[Tuple[TrackType, AcceptanceCheck]]:
    """
    Determine which tracks a character is eligible for.

    Returns:
        List of tuples (TrackType, AcceptanceCheck) for eligible tracks
    """
    eligible = []

    # Always eligible tracks
    eligible.append((TrackType.RANDOM, create_auto_accept_check(TrackType.RANDOM)))
    eligible.append((TrackType.WORKER, create_auto_accept_check(TrackType.WORKER)))
    eligible.append((TrackType.CRAFTS, create_auto_accept_check(TrackType.CRAFTS)))

    # Tracks with requirements
    army_check = check_army_acceptance(str_mod, dex_mod)
    if army_check.accepted:
        eligible.append((TrackType.ARMY, army_check))

    navy_check = check_navy_acceptance(str_mod, dex_mod, int_mod)
    if navy_check.accepted:
        eligible.append((TrackType.NAVY, navy_check))

    ranger_check = check_ranger_acceptance(str_mod, dex_mod, int_mod, wis_mod)
    if ranger_check.accepted:
        eligible.append((TrackType.RANGER, ranger_check))

    officer_check = check_officer_acceptance(wealth_level, is_promoted)
    if officer_check.accepted:
        eligible.append((TrackType.OFFICER, officer_check))

    merchant_check = check_merchant_acceptance(social_class, wealth_level)
    if merchant_check.accepted:
        eligible.append((TrackType.MERCHANT, merchant_check))

    # Magic track - requires INT or WIS bonus
    magic_check = check_magic_acceptance(int_mod, wis_mod)
    if magic_check.accepted:
        eligible.append((TrackType.MAGIC, magic_check))

    return eligible


def select_optimal_track(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    wealth_level: str,
    sub_class: str,
    is_promoted: bool = False,
) -> Tuple[TrackType, AcceptanceCheck]:
    """
    Select the optimal track for a character based on their attributes.

    Priority order (can be adjusted):
    1. Officer (if Rich or promoted) - prestigious
    2. Ranger (if eligible) - elite
    3. Navy (if eligible) - good skills
    4. Army (if eligible) - military
    5. Merchant (if eligible) - wealth building
    6. Crafts (if from crafts background) - matches background
    7. Worker (if laborer background) - matches background
    8. Random - fallback

    Returns:
        Tuple of (selected TrackType, AcceptanceCheck)
    """
    eligible = get_eligible_tracks(
        str_mod, dex_mod, int_mod, wis_mod, social_class, wealth_level, is_promoted
    )

    eligible_types = {t for t, _ in eligible}

    # Priority selection
    # Officer is best if available (Rich or promoted)
    if TrackType.OFFICER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.OFFICER)

    # Ranger is elite - prioritize if eligible
    if TrackType.RANGER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.RANGER)

    # Navy has good skill variety
    if TrackType.NAVY in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.NAVY)

    # Army for combat focus
    if TrackType.ARMY in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.ARMY)

    # Merchant for wealth building (especially if already merchant class)
    if TrackType.MERCHANT in eligible_types:
        if social_class == "Merchant" or is_rich(wealth_level):
            return next((t, c) for t, c in eligible if t == TrackType.MERCHANT)

    # Match background if possible
    if sub_class == "Crafts" and TrackType.CRAFTS in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.CRAFTS)

    if sub_class == "Laborer" and TrackType.WORKER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.WORKER)

    # Merchant as general fallback if eligible
    if TrackType.MERCHANT in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.MERCHANT)

    # Crafts over Worker (literacy skill)
    if TrackType.CRAFTS in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.CRAFTS)

    # Worker
    if TrackType.WORKER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.WORKER)

    # Random as last resort
    return next((t, c) for t, c in eligible if t == TrackType.RANDOM)


def roll_skill_track(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    sub_class: str,
    wealth_level: str,
    is_promoted: bool = False,
    optimize: bool = True,
) -> SkillTrack:
    """
    Determine and roll for a character's skill track.

    Args:
        str_mod: STR modifier
        dex_mod: DEX modifier
        int_mod: INT modifier
        wis_mod: WIS modifier
        social_class: Character's social class (Nobility, Merchant, Commoner)
        sub_class: Character's sub-class (e.g., Laborer, Crafts, Baron, etc.)
        wealth_level: Character's wealth level
        is_promoted: Whether character has been promoted (for Officer track)
        optimize: If True, select optimal track; if False, select randomly from eligible

    Returns:
        SkillTrack object with all track information
    """
    if optimize:
        track, acceptance_check = select_optimal_track(
            str_mod,
            dex_mod,
            int_mod,
            wis_mod,
            social_class,
            wealth_level,
            sub_class,
            is_promoted,
        )
    else:
        eligible = get_eligible_tracks(
            str_mod, dex_mod, int_mod, wis_mod, social_class, wealth_level, is_promoted
        )
        track, acceptance_check = random.choice(eligible)

    # Build the skill track using the helper function
    return build_skill_track(track, acceptance_check, sub_class, wealth_level)
