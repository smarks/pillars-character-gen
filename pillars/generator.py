#!/usr/bin/env python3
"""
Main module for generating Pillars RPG characters.

This module provides the generate_character function that creates
a complete character with all attributes, skills, and prior experience.
"""

from dataclasses import dataclass
from typing import Optional

from pillars.attributes import (
    generate_attributes_4d6_drop_lowest,
    roll_appearance,
    roll_height,
    roll_weight,
    roll_provenance,
    roll_location,
    roll_literacy_check,
    roll_wealth,
    roll_skill_track,
    roll_prior_experience,
    roll_single_year,
    get_track_availability,
    create_skill_track_for_choice,
    CharacterAttributes,
    Appearance,
    Height,
    Weight,
    Provenance,
    Location,
    LiteracyCheck,
    Wealth,
    SkillTrack,
    PriorExperience,
    YearResult,
    AgingEffects,
    TrackType,
)


@dataclass
class Character:
    """Complete character with all generated attributes."""
    attributes: CharacterAttributes
    appearance: Appearance
    height: Height
    weight: Weight
    provenance: Provenance
    location: Location
    literacy: LiteracyCheck
    wealth: Wealth
    skill_track: SkillTrack
    prior_experience: PriorExperience

    @property
    def died(self) -> bool:
        """Check if character died during prior experience."""
        return self.prior_experience.died

    @property
    def age(self) -> int:
        """Get character's final age."""
        return self.prior_experience.final_age

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "PILLARS CHARACTER",
            "=" * 60,
            "",
            str(self.attributes),
            "",
            str(self.appearance),
            str(self.height),
            str(self.weight),
            str(self.provenance),
            str(self.location),
            str(self.literacy),
            str(self.wealth),
            "",
            str(self.skill_track),
            str(self.prior_experience),
        ]

        if self.died:
            lines.append("")
            lines.append("!" * 60)
            lines.append("THIS CHARACTER DIED DURING PRIOR EXPERIENCE!")
            lines.append("!" * 60)

        return "\n".join(lines)


def generate_character(
    years: int = 0,
    chosen_track: Optional[TrackType] = None,
    attribute_focus: Optional[str] = None
) -> Character:
    """
    Generate a complete Pillars RPG character.

    Args:
        years: Years of prior experience (0-18).
               Use -1 for random (0-18 years).
               Default is 0 (no prior experience).
        chosen_track: If provided, attempt to use this track instead of auto-selecting.
                     Will roll for acceptance if required. If acceptance fails,
                     the character will have a failed skill_track.
        attribute_focus: If 'physical', ensure STR or DEX has +1 bonus.
                        If 'mental', ensure INT or WIS has +1 bonus.
                        If None or 'none', no requirement.

    Returns:
        Character object with all attributes, skills, and prior experience
    """
    # Generate attributes, re-rolling if focus requirement not met
    max_attempts = 100  # Prevent infinite loops
    for _ in range(max_attempts):
        attributes = generate_attributes_4d6_drop_lowest()

        # Check if focus requirement is met
        if attribute_focus == 'physical':
            str_mod = attributes.get_modifier("STR")
            dex_mod = attributes.get_modifier("DEX")
            if str_mod >= 1 or dex_mod >= 1:
                break  # Focus requirement met
        elif attribute_focus == 'mental':
            int_mod = attributes.get_modifier("INT")
            wis_mod = attributes.get_modifier("WIS")
            if int_mod >= 1 or wis_mod >= 1:
                break  # Focus requirement met
        else:
            break  # No focus requirement
    appearance = roll_appearance()
    height = roll_height()
    weight = roll_weight(attributes.STR)
    provenance = roll_provenance()
    location = roll_location()
    literacy = roll_literacy_check(attributes.INT, location.literacy_check_modifier)
    wealth = roll_wealth()

    if chosen_track is not None:
        # User chose a specific track - roll for acceptance
        skill_track = create_skill_track_for_choice(
            chosen_track=chosen_track,
            str_mod=attributes.get_modifier("STR"),
            dex_mod=attributes.get_modifier("DEX"),
            int_mod=attributes.get_modifier("INT"),
            wis_mod=attributes.get_modifier("WIS"),
            social_class=provenance.social_class,
            sub_class=provenance.sub_class,
            wealth_level=wealth.wealth_level,
        )
    else:
        # Auto-select optimal track
        skill_track = roll_skill_track(
            str_mod=attributes.get_modifier("STR"),
            dex_mod=attributes.get_modifier("DEX"),
            int_mod=attributes.get_modifier("INT"),
            wis_mod=attributes.get_modifier("WIS"),
            social_class=provenance.social_class,
            sub_class=provenance.sub_class,
            wealth_level=wealth.wealth_level,
            optimize=True
        )

    # Calculate total attribute modifier for survivability checks
    attribute_modifiers = attributes.get_all_modifiers()
    total_modifier = sum(attribute_modifiers.values())
    attribute_scores = {attr: getattr(attributes, attr) for attr in ["STR", "DEX", "INT", "WIS", "CON", "CHR"]}
    prior_experience = roll_prior_experience(
        skill_track,
        years=years,
        total_modifier=total_modifier,
        attribute_scores=attribute_scores,
        attribute_modifiers=attribute_modifiers
    )

    return Character(
        attributes=attributes,
        appearance=appearance,
        height=height,
        weight=weight,
        provenance=provenance,
        location=location,
        literacy=literacy,
        wealth=wealth,
        skill_track=skill_track,
        prior_experience=prior_experience,
    )


def main():
    """Main program loop."""
    print("\nWelcome to Pillars Character Generator!")
    character = generate_character()
    print(character)


if __name__ == "__main__":
    main()
