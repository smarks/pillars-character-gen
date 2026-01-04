"""
Skill track generation for Pillars RPG.

This module handles the generation and management of skill tracks,
including acceptance checks and track selection.

Track data is loaded from references/skills.csv.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random
from pillars.dice import roll_die, roll_percentile
from pillars.enums import TrackType, CraftType, MagicSchool
from pillars.constants import (
    MAGIC_SPELL_PROGRESSION,
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
)
from pillars.config import MAGIC_COMMON_THRESHOLD


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
    "check_civil_service_acceptance",
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
    Requirement: INT or WIS bonus required (from CSV: "Int or Wis bonus")
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


def check_civil_service_acceptance(
    int_mod: int, chr_mod: int, wis_mod: int
) -> AcceptanceCheck:
    """
    Check if character meets Civil Service track requirements.
    Requirement: INT, CHR, or WIS bonus required (from CSV: "Int, Chr or WIs bonus")
    """
    has_bonus = int_mod > 0 or chr_mod > 0 or wis_mod > 0
    accepted = has_bonus

    if has_bonus:
        reason = f"Has INT({int_mod:+d}), CHR({chr_mod:+d}), or WIS({wis_mod:+d}) bonus"
    else:
        reason = "No INT, CHR, or WIS bonus - civil service requires aptitude"

    return AcceptanceCheck(
        track=TrackType.CIVIL_SERVICE,
        accepted=accepted,
        roll=None,
        target=None,
        modifiers={"INT": int_mod, "CHR": chr_mod, "WIS": wis_mod},
        reason=reason,
    )


def get_track_availability(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    chr_mod: int = 0,
    social_class: str = "",
    wealth_level: str = "",
    is_promoted: bool = False,
) -> Dict[TrackType, Dict]:
    """
    Get availability status for all tracks without rolling dice.
    Used to show which tracks are available for user selection.

    Tracks from CSV:
    - Merchant: No requirements
    - Campaigner: No requirements
    - Laborer: No requirements
    - Magic: Int or Wis bonus
    - Underworld: No requirements
    - Civil Service: Int, Chr or Wis bonus
    - Craft: No requirements
    - Hunter/Gatherer: No requirements
    - Random: No requirements

    Returns:
        Dict mapping TrackType to availability info
    """
    availability = {}

    # Tracks with no requirements (most tracks)
    no_req_tracks = [
        TrackType.MERCHANT,
        TrackType.CAMPAIGNER,
        TrackType.LABORER,
        TrackType.UNDERWORLD,
        TrackType.CRAFT,
        TrackType.HUNTER_GATHERER,
        TrackType.RANDOM,
    ]
    for track in no_req_tracks:
        availability[track] = {
            "available": True,
            "requires_roll": False,
            "auto_accept": True,
            "impossible": False,
            "requirement": "No requirements",
            "roll_info": None,
        }

    # Magic: Requires INT or WIS bonus
    has_mental = int_mod > 0 or wis_mod > 0
    availability[TrackType.MAGIC] = {
        "available": has_mental,
        "requires_roll": False,
        "auto_accept": has_mental,
        "impossible": not has_mental,
        "requirement": "Requires INT or WIS bonus",
        "roll_info": None,
    }

    # Civil Service: Requires INT, CHR, or WIS bonus
    has_civil_bonus = int_mod > 0 or chr_mod > 0 or wis_mod > 0
    availability[TrackType.CIVIL_SERVICE] = {
        "available": has_civil_bonus,
        "requires_roll": False,
        "auto_accept": has_civil_bonus,
        "impossible": not has_civil_bonus,
        "requirement": "Requires INT, CHR, or WIS bonus",
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
    sub_class: str = "",
    wealth_level: str = "",
) -> SkillTrack:
    """
    Build a complete SkillTrack object from track type and acceptance check.

    Args:
        track: The track type
        acceptance_check: The acceptance check result
        sub_class: Character's sub-class (unused in new CSV tracks)
        wealth_level: Character's wealth level (unused in new CSV tracks)

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

    # Handle special cases
    craft_type = None
    craft_rolls = None
    magic_school = None
    magic_school_rolls = None

    if track == TrackType.CRAFT:
        # Get initial skills from CSV, then add craft type
        initial_skills = list(TRACK_INITIAL_SKILLS.get(track, []))
        craft_type, craft_rolls = roll_craft_type()
        initial_skills.append(f"Craft: {craft_type.value}")
    elif track == TrackType.MAGIC:
        # Magic uses spell progression, not CSV skills
        magic_school, magic_school_rolls = roll_magic_school()
        initial_skills = get_magic_initial_skills(magic_school)
    else:
        # Get initial skills from CSV for other tracks
        initial_skills = list(TRACK_INITIAL_SKILLS.get(track, []))

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
    str_mod: int = 0,
    dex_mod: int = 0,
    int_mod: int = 0,
    wis_mod: int = 0,
    chr_mod: int = 0,
    social_class: str = "",
    sub_class: str = "",
    wealth_level: str = "",
    is_promoted: bool = False,
) -> SkillTrack:
    """
    Create a skill track for a user-chosen track, checking requirements.

    Args:
        chosen_track: The track the user wants
        Other args: Character stats for acceptance checks

    Returns:
        SkillTrack object (may have accepted=False if requirements not met)
    """
    # Most tracks have no requirements
    no_req_tracks = [
        TrackType.MERCHANT,
        TrackType.CAMPAIGNER,
        TrackType.LABORER,
        TrackType.UNDERWORLD,
        TrackType.CRAFT,
        TrackType.HUNTER_GATHERER,
        TrackType.RANDOM,
    ]

    if chosen_track in no_req_tracks:
        acceptance_check = create_auto_accept_check(chosen_track)
    elif chosen_track == TrackType.MAGIC:
        acceptance_check = check_magic_acceptance(int_mod, wis_mod)
    elif chosen_track == TrackType.CIVIL_SERVICE:
        acceptance_check = check_civil_service_acceptance(int_mod, chr_mod, wis_mod)
    else:
        # Unknown track - auto accept
        acceptance_check = create_auto_accept_check(chosen_track, "Unknown track type")

    # Build the skill track using the helper function
    return build_skill_track(chosen_track, acceptance_check, sub_class, wealth_level)


def get_eligible_tracks(
    str_mod: int = 0,
    dex_mod: int = 0,
    int_mod: int = 0,
    wis_mod: int = 0,
    chr_mod: int = 0,
    social_class: str = "",
    wealth_level: str = "",
    is_promoted: bool = False,
) -> List[Tuple[TrackType, AcceptanceCheck]]:
    """
    Determine which tracks a character is eligible for.

    Returns:
        List of tuples (TrackType, AcceptanceCheck) for eligible tracks
    """
    eligible = []

    # Tracks with no requirements (most tracks from CSV)
    no_req_tracks = [
        TrackType.MERCHANT,
        TrackType.CAMPAIGNER,
        TrackType.LABORER,
        TrackType.UNDERWORLD,
        TrackType.CRAFT,
        TrackType.HUNTER_GATHERER,
        TrackType.RANDOM,
    ]
    for track in no_req_tracks:
        eligible.append((track, create_auto_accept_check(track)))

    # Magic - requires INT or WIS bonus
    magic_check = check_magic_acceptance(int_mod, wis_mod)
    if magic_check.accepted:
        eligible.append((TrackType.MAGIC, magic_check))

    # Civil Service - requires INT, CHR, or WIS bonus
    civil_check = check_civil_service_acceptance(int_mod, chr_mod, wis_mod)
    if civil_check.accepted:
        eligible.append((TrackType.CIVIL_SERVICE, civil_check))

    return eligible


def select_optimal_track(
    str_mod: int = 0,
    dex_mod: int = 0,
    int_mod: int = 0,
    wis_mod: int = 0,
    chr_mod: int = 0,
    social_class: str = "",
    wealth_level: str = "",
    sub_class: str = "",
    is_promoted: bool = False,
) -> Tuple[TrackType, AcceptanceCheck]:
    """
    Select the optimal track for a character based on their attributes.

    Priority order for CSV tracks:
    1. Magic (if eligible) - specialized magical training
    2. Civil Service (if eligible) - good social skills
    3. Merchant - wealth building
    4. Craft - practical skills
    5. Campaigner - combat focus
    6. Underworld - alternative path
    7. Hunter/Gatherer - survival skills
    8. Laborer - basic skills
    9. Random - fallback

    Returns:
        Tuple of (selected TrackType, AcceptanceCheck)
    """
    eligible = get_eligible_tracks(
        str_mod,
        dex_mod,
        int_mod,
        wis_mod,
        chr_mod,
        social_class,
        wealth_level,
        is_promoted,
    )

    eligible_types = {t for t, _ in eligible}

    # Priority selection based on character attributes
    # Magic is valuable if eligible
    if TrackType.MAGIC in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.MAGIC)

    # Civil Service for social characters
    if TrackType.CIVIL_SERVICE in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.CIVIL_SERVICE)

    # Merchant for wealth building
    if TrackType.MERCHANT in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.MERCHANT)

    # Craft for practical skills
    if TrackType.CRAFT in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.CRAFT)

    # Campaigner for combat
    if TrackType.CAMPAIGNER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.CAMPAIGNER)

    # Underworld for rogues
    if TrackType.UNDERWORLD in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.UNDERWORLD)

    # Hunter/Gatherer for survival
    if TrackType.HUNTER_GATHERER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.HUNTER_GATHERER)

    # Laborer as basic option
    if TrackType.LABORER in eligible_types:
        return next((t, c) for t, c in eligible if t == TrackType.LABORER)

    # Random as last resort
    return next((t, c) for t, c in eligible if t == TrackType.RANDOM)


def roll_skill_track(
    str_mod: int = 0,
    dex_mod: int = 0,
    int_mod: int = 0,
    wis_mod: int = 0,
    chr_mod: int = 0,
    social_class: str = "",
    sub_class: str = "",
    wealth_level: str = "",
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
        chr_mod: CHR modifier
        social_class: Character's social class (Nobility, Merchant, Commoner)
        sub_class: Character's sub-class (e.g., Laborer, Crafts, Baron, etc.)
        wealth_level: Character's wealth level
        is_promoted: Whether character has been promoted
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
            chr_mod,
            social_class,
            wealth_level,
            sub_class,
            is_promoted,
        )
    else:
        eligible = get_eligible_tracks(
            str_mod,
            dex_mod,
            int_mod,
            wis_mod,
            chr_mod,
            social_class,
            wealth_level,
            is_promoted,
        )
        track, acceptance_check = random.choice(eligible)

    # Build the skill track using the helper function
    return build_skill_track(track, acceptance_check, sub_class, wealth_level)
