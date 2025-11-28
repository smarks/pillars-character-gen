#!/usr/bin/env python3
"""
Main script for generating Pillars RPG characters.

This script demonstrates character attribute generation using
the 4d6 drop lowest method (or other methods).
"""

import sys
from helpers.attributes import (
    generate_attributes_4d6_drop_lowest,
    display_attribute_rolls,
    roll_appearance,
    roll_height,
    roll_weight,
    roll_provenance,
    roll_location,
    roll_literacy_check,
    roll_wealth,
    roll_skill_track,
    roll_prior_experience
)


def generate_single_character():
    """
    Generate and display a single character.
    """
    character = generate_attributes_4d6_drop_lowest()
    appearance = roll_appearance()
    height = roll_height()
    weight = roll_weight(character.STR)
    provenance = roll_provenance()
    location = roll_location()
    literacy = roll_literacy_check(character.INT, location.literacy_check_modifier)
    wealth = roll_wealth()

    # Determine skill track based on character attributes
    skill_track = roll_skill_track(
        str_mod=character.get_modifier("STR"),
        dex_mod=character.get_modifier("DEX"),
        int_mod=character.get_modifier("INT"),
        wis_mod=character.get_modifier("WIS"),
        social_class=provenance.social_class,
        sub_class=provenance.sub_class,
        wealth_level=wealth.wealth_level,
        optimize=True
    )

    # Generate prior experience (0-18 years, ages 16-34)
    prior_experience = roll_prior_experience(skill_track)

    display_attribute_rolls(character)
    print(appearance)
    print(height)
    print(weight)
    print(provenance)
    print(location)
    print(literacy)
    print(wealth)
    print(skill_track)
    print(prior_experience)

    # Check if character died during prior experience
    if prior_experience.died:
        print("\n" + "!" * 60)
        print("THIS CHARACTER DIED DURING PRIOR EXPERIENCE!")
        print("!" * 60)

    return character, appearance, height, weight, provenance, location, literacy, wealth, skill_track, prior_experience


def main():
    """Main program loop."""
    print("\nWelcome to Pillars Character Generator!")
    generate_single_character()

if __name__ == "__main__":
    main()
