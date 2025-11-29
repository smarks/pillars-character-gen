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
    """
    Complete Pillars RPG character with all generated attributes.

    A Character represents a fully generated RPG character. In the web UI flow:
    1. Initial generation creates a character WITHOUT skill_track/prior_experience
       (using skip_track=True) so the user can review their base stats first.
    2. When the user chooses to add prior experience, they select a skill track,
       then the character gains skill_track and prior_experience.

    Attributes:
        attributes: Core stats (STR, DEX, INT, WIS, CON, CHR) plus derived stats
        appearance: Physical appearance description
        height: Character height in hands/feet
        weight: Character weight in stones/lbs
        provenance: Social class and background (Nobility, Merchant, Commoner)
        location: Where character grew up (affects literacy and skills)
        literacy: Whether character can read/write
        wealth: Starting money
        skill_track: Career path (Ranger, Army, Magic, etc.) - None until selected
        prior_experience: Years of experience before play - None until added

    Example:
        # Generate basic character for initial display (no track yet)
        char = generate_character(skip_track=True)

        # Generate complete character with track and experience
        char = generate_character(years=5, chosen_track=TrackType.RANGER)
    """
    attributes: CharacterAttributes
    appearance: Appearance
    height: Height
    weight: Weight
    provenance: Provenance
    location: Location
    literacy: LiteracyCheck
    wealth: Wealth
    skill_track: Optional[SkillTrack] = None
    prior_experience: Optional[PriorExperience] = None

    @property
    def died(self) -> bool:
        """
        Check if character died during prior experience.

        Characters can die during the prior experience phase if they fail
        a survivability check. Dead characters cannot be played.

        Returns:
            True if character died, False if alive or no prior experience yet.
        """
        if self.prior_experience is None:
            return False
        return self.prior_experience.died

    @property
    def age(self) -> int:
        """
        Get character's current age.

        All characters start at age 16. Each year of prior experience
        adds one year to their age.

        Returns:
            Character's age (16 + years of prior experience).
        """
        if self.prior_experience is None:
            return 16  # Starting age
        return self.prior_experience.final_age

    def __str__(self) -> str:
        """
        Generate a formatted text display of the character.

        The output includes all basic character info. Skill track and
        prior experience are only shown if they have been assigned
        (i.e., not None). This allows the web UI to show a "clean"
        character sheet before the user selects a track.

        Returns:
            Multi-line string with formatted character information.
        """
        lines = [
            "**Pillars Character**",
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
        ]

        # Only show skill track and prior experience if assigned
        # This keeps the initial character display clean in the web UI
        if self.skill_track is not None:
            lines.append("")
            lines.append(str(self.skill_track))

        if self.prior_experience is not None:
            lines.append(str(self.prior_experience))

            if self.died:
                lines.append("")
                lines.append("**THIS CHARACTER DIED DURING PRIOR EXPERIENCE!**")

        return "\n".join(lines)


def generate_character(
    years: int = 0,
    chosen_track: Optional[TrackType] = None,
    attribute_focus: Optional[str] = None,
    skip_track: bool = False
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
        skip_track: If True, don't assign a skill track or prior experience.
                   Used for initial character generation in web UI.

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

    if skip_track:
        # Don't assign a skill track or prior experience - for initial web UI display
        skill_track = None
        prior_experience = None
    elif chosen_track is not None:
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
