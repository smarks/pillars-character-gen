"""
Character attribute generation package for Pillars RPG.

This package handles the generation of character attributes using
various methods (dice rolling or point allocation), as well as
physical characteristics, social attributes, skill tracks, and
prior experience.

Modules:
    core: Core attribute generation (stats, modifiers, aging)
    physical: Physical characteristics (appearance, height, weight)
    social: Social characteristics (provenance, literacy, location, wealth)
    tracks: Skill track generation and acceptance checks
    experience: Prior experience generation (yearly skills, survivability)
"""

# === core.py ===
from pillars.attributes.core import (
    CORE_ATTRIBUTES,
    ATTRIBUTE_MODIFIERS,
    AGING_EFFECTS,
    AgingEffects,
    AttributeRoll,
    CharacterAttributes,
    get_aging_effects_for_age,
    format_total_modifier,
    get_attribute_modifier,
    calculate_fatigue_points,
    calculate_body_points,
    roll_single_attribute_3d6,
    roll_single_attribute_4d6_drop_lowest,
    generate_attributes_3d6,
    generate_attributes_4d6_drop_lowest,
    generate_attributes_point_buy,
    validate_point_buy,
    display_attribute_rolls,
)

# === physical.py ===
from pillars.attributes.physical import (
    Appearance,
    Height,
    Weight,
    HEIGHT_TABLE,
    WEIGHT_TABLE,
    get_appearance_description,
    roll_appearance,
    roll_height,
    roll_weight,
)

# === social.py ===
from pillars.attributes.social import (
    Provenance,
    LiteracyCheck,
    Location,
    Wealth,
    SURVIVAL_SKILLS,
    get_nobility_rank,
    get_merchant_type,
    get_commoner_type,
    get_craft_type,
    roll_provenance,
    roll_literacy_check,
    roll_location,
    get_wealth_level,
    roll_wealth,
)

# === tracks.py ===
from pillars.attributes.tracks import (
    AcceptanceCheck,
    SkillTrack,
    create_auto_accept_check,
    roll_survivability_random,
    roll_craft_type,
    roll_magic_school,
    check_magic_acceptance,
    check_army_acceptance,
    check_navy_acceptance,
    check_ranger_acceptance,
    check_officer_acceptance,
    check_merchant_acceptance,
    is_rich,
    is_poor,
    is_working_class,
    calculate_roll_availability,
    get_track_availability,
    get_magic_initial_skills,
    build_skill_track,
    create_skill_track_for_choice,
    get_eligible_tracks,
    select_optimal_track,
    roll_skill_track,
)

# === experience.py ===
from pillars.attributes.experience import (
    YearResult,
    PriorExperience,
    roll_yearly_skill,
    roll_survivability_check,
    roll_single_year,
    roll_prior_experience,
)

# Re-export enums for backward compatibility (originally imported at module level)
from pillars.enums import TrackType, CraftType, MagicSchool

# Re-export constants from pillars.constants for backward compatibility
from pillars.constants import (
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
    TRACK_YEARLY_SKILLS,
)

__all__ = [
    # === Re-exported enums (for backward compatibility) ===
    "TrackType",
    "CraftType",
    "MagicSchool",
    # === Re-exported constants from pillars.constants ===
    "TRACK_SURVIVABILITY",
    "TRACK_INITIAL_SKILLS",
    "TRACK_YEARLY_SKILLS",
    # === core.py ===
    "CORE_ATTRIBUTES",
    "ATTRIBUTE_MODIFIERS",
    "AGING_EFFECTS",
    "AgingEffects",
    "AttributeRoll",
    "CharacterAttributes",
    "get_aging_effects_for_age",
    "format_total_modifier",
    "get_attribute_modifier",
    "calculate_fatigue_points",
    "calculate_body_points",
    "roll_single_attribute_3d6",
    "roll_single_attribute_4d6_drop_lowest",
    "generate_attributes_3d6",
    "generate_attributes_4d6_drop_lowest",
    "generate_attributes_point_buy",
    "validate_point_buy",
    "display_attribute_rolls",
    # === physical.py ===
    "Appearance",
    "Height",
    "Weight",
    "HEIGHT_TABLE",
    "WEIGHT_TABLE",
    "get_appearance_description",
    "roll_appearance",
    "roll_height",
    "roll_weight",
    # === social.py ===
    "Provenance",
    "LiteracyCheck",
    "Location",
    "Wealth",
    "SURVIVAL_SKILLS",
    "get_nobility_rank",
    "get_merchant_type",
    "get_commoner_type",
    "get_craft_type",
    "roll_provenance",
    "roll_literacy_check",
    "roll_location",
    "get_wealth_level",
    "roll_wealth",
    # === tracks.py ===
    "AcceptanceCheck",
    "SkillTrack",
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
    # === experience.py ===
    "YearResult",
    "PriorExperience",
    "roll_yearly_skill",
    "roll_survivability_check",
    "roll_single_year",
    "roll_prior_experience",
]
