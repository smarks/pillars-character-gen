"""
Prior experience generation for Pillars RPG.

This module handles the generation of prior experience for characters,
including yearly skills, survivability checks, and aging effects.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random
from pillars.dice import roll_dice, roll_die
from pillars.enums import TrackType, MagicSchool
from pillars.constants import (
    MAGIC_SPELL_PROGRESSION,
    SPELL_SKILL_MASTERY,
    TRACK_YEARLY_SKILLS,
)
from pillars.attributes.core import AgingEffects, format_total_modifier
from pillars.attributes.tracks import SkillTrack


__all__ = [
    # Classes
    "YearResult",
    "PriorExperience",
    # Functions
    "roll_yearly_skill",
    "roll_survivability_check",
    "roll_single_year",
    "roll_prior_experience",
]


@dataclass
class YearResult:
    """Result of a single year of prior experience."""

    year: int  # Age (16+)
    track: TrackType
    skill_gained: str
    skill_roll: int
    skill_points: int  # Always 1 (automatic point for the rolled skill)
    survivability_target: int
    survivability_roll: int  # Base 3d6 roll
    survivability_modifier: int  # Sum of all attribute modifiers
    survivability_total: int  # Roll + modifier
    survived: bool
    aging_penalties: Optional[Dict[str, int]] = (
        None  # Any new aging penalties this year
    )
    free_skill_points: int = 1  # Free point to allocate to any skill
    xp_gained: int = 1000  # Experience points gained this year

    def __str__(self) -> str:
        status = "Survived" if self.survived else "DIED"
        mod_str = (
            f"{self.survivability_modifier:+d}"
            if self.survivability_modifier != 0
            else "+0"
        )
        result = (
            f"Year {self.year}: {self.skill_gained} (+1 SP, +1 free, +{self.xp_gained} XP) | "
            f"Survival: {self.survivability_roll}{mod_str}={self.survivability_total} vs {self.survivability_target}+ [{status}]"
        )

        # Show aging penalties if any were applied this year
        if self.aging_penalties:
            penalties = [
                f"{k} {v:+d}" for k, v in self.aging_penalties.items() if v != 0
            ]
            if penalties:
                result += f" | AGING: {', '.join(penalties)}"

        return result


@dataclass
class PriorExperience:
    """Complete prior experience record for a character."""

    starting_age: int  # Always 16
    final_age: int  # Age at end (or death)
    years_served: int
    track: TrackType
    survivability_target: int
    yearly_results: List[YearResult]
    total_skill_points: int  # Automatic points (1 per year to rolled skill)
    all_skills: List[str]
    died: bool
    death_year: Optional[int]
    attribute_scores: Optional[Dict[str, int]] = None  # Raw attribute scores
    attribute_modifiers: Optional[Dict[str, int]] = None  # Attribute modifiers
    aging_effects: Optional[AgingEffects] = None  # Cumulative aging penalties
    total_free_points: int = 0  # Free points to allocate (1 per year)
    total_xp: int = 0  # Experience points (1000 per year)

    def __str__(self) -> str:
        lines = [
            f"\n**Prior Experience** ({self.track.value} Track)",
            f"Starting Age: {self.starting_age}",
        ]

        if self.died:
            lines.append(f"DIED at age {self.death_year}!")
            lines.append(f"Years Served: {self.years_served}")
        else:
            lines.append(f"Final Age: {self.final_age}")
            lines.append(f"Years Served: {self.years_served}")

        # Display survivability with attribute breakdown
        lines.append(f"Survivability Target: {self.survivability_target}+")

        if self.attribute_scores and self.attribute_modifiers:
            # Show total modifier calculation
            total_str = format_total_modifier(self.attribute_modifiers)
            lines.append(f"Total Modifier: {total_str}")

        lines.append("\n**Year-by-Year**")

        for result in self.yearly_results:
            lines.append(str(result))

        lines.append(f"\n**Skills** ({len(self.all_skills)})")

        # Group and count skills
        skill_counts: Dict[str, int] = {}
        for skill in self.all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        for skill, count in sorted(skill_counts.items()):
            if count > 1:
                lines.append(f"- {skill} x{count}")
            else:
                lines.append(f"- {skill}")

        # Show cumulative aging effects if any
        if self.aging_effects:
            penalties = self.aging_effects.total_penalties()
            has_penalties = any(v != 0 for v in penalties.values())
            if has_penalties:
                lines.append(f"\n{self.aging_effects}")

        return "\n".join(lines)


def roll_yearly_skill(
    track: TrackType, year_index: int, magic_school: Optional[MagicSchool] = None
) -> Tuple[str, int]:
    """
    Roll for a skill from the track's skill table.

    Args:
        track: The character's skill track
        year_index: Which year of service (0-based)
        magic_school: For Magic track, the character's magic school

    Returns:
        Tuple of (skill name, roll used)
    """
    # Special handling for Magic track - progress through school spells
    if track == TrackType.MAGIC and magic_school:
        spells = MAGIC_SPELL_PROGRESSION.get(magic_school, [])
        if spells:
            # Progress through spells sequentially
            # year_index 0 = already got spell 0 as initial, so start at 1
            spell_index = (year_index + 1) % len(spells)
            roll = spell_index + 1  # Pseudo-roll for display
            spell_name = spells[spell_index]
            mastery_level = min(spell_index + 1, 6)  # Mastery 1-6
            mastery_name = SPELL_SKILL_MASTERY.get(mastery_level, "")
            return f"Spell: {spell_name} ({mastery_name})", roll

    skill_table = TRACK_YEARLY_SKILLS.get(track, TRACK_YEARLY_SKILLS[TrackType.RANDOM])

    # Roll d12 (or use modulo for year progression variety)
    roll = roll_die(12)
    skill_index = (roll - 1) % len(skill_table)
    skill = skill_table[skill_index]

    return skill, roll


def roll_survivability_check(
    survivability: int, total_modifier: int = 0
) -> Tuple[int, int, bool]:
    """
    Roll a survivability check (3d6 + all attribute modifiers >= survivability target).

    Args:
        survivability: Target number to meet or exceed
        total_modifier: Sum of all attribute modifiers (STR + DEX + INT + WIS + CON + CHR)

    Returns:
        Tuple of (base roll, total with modifiers, survived boolean)
    """
    roll = sum(roll_dice(3, 6))
    total = roll + total_modifier
    survived = total >= survivability
    return roll, total, survived


def roll_single_year(
    skill_track: SkillTrack,
    year_index: int,
    total_modifier: int,
    aging_effects: AgingEffects,
    starting_age: int = 16,
) -> YearResult:
    """
    Roll a single year of prior experience.

    Args:
        skill_track: The character's chosen skill track
        year_index: Which year of service (0-based)
        total_modifier: Sum of all attribute modifiers (before aging)
        aging_effects: Current aging effects (will be updated if crossing threshold)
        starting_age: Character's age before any prior experience (default 16)

    Returns:
        YearResult for this year
    """
    current_age = starting_age + year_index
    # For aging calculations, use effective years from the standard base age of 16
    effective_years_of_experience = current_age - 16 + 1
    track = skill_track.track
    survivability = skill_track.survivability

    # Check for aging effects this year (based on actual age, not just experience years)
    aging_this_year = aging_effects.apply_year(effective_years_of_experience)
    has_aging = any(v != 0 for v in aging_this_year.values())

    # Adjust modifier for aging penalties
    aging_modifier = sum(aging_effects.total_penalties().values())
    adjusted_modifier = total_modifier + aging_modifier

    # Gain skill (pass magic_school for Magic track)
    skill, skill_roll = roll_yearly_skill(track, year_index, skill_track.magic_school)

    # Survivability check (3d6 + all attribute modifiers >= target)
    surv_roll, surv_total, survived = roll_survivability_check(
        survivability, adjusted_modifier
    )

    return YearResult(
        year=current_age,
        track=track,
        skill_gained=skill,
        skill_roll=skill_roll,
        skill_points=1,
        survivability_target=survivability,
        survivability_roll=surv_roll,
        survivability_modifier=adjusted_modifier,
        survivability_total=surv_total,
        survived=survived,
        aging_penalties=aging_this_year if has_aging else None,
    )


def roll_prior_experience(
    skill_track: SkillTrack,
    years: int = 0,
    total_modifier: int = 0,
    attribute_scores: Optional[Dict[str, int]] = None,
    attribute_modifiers: Optional[Dict[str, int]] = None,
    allow_aging: bool = False,
) -> PriorExperience:
    """
    Generate prior experience for a character.

    Characters can have 0-18 years of prior experience (ages 16-34).
    If allow_aging is True, can go beyond 18 years with aging penalties.
    Each year they gain:
    - 1 skill point
    - 1 skill from their track's skill table
    - Must pass a survivability roll (3d6 + all attribute modifiers >= target) or die

    Args:
        skill_track: The character's chosen skill track
        years: Years of prior experience.
               Use -1 for random (0-18 years).
               Default is 0 (no prior experience).
               If allow_aging=True, can exceed 18.
        total_modifier: Sum of all attribute modifiers (STR+DEX+INT+WIS+CON+CHR)
        attribute_scores: Dict of raw attribute scores (for display)
        attribute_modifiers: Dict of attribute modifiers (for display)
        allow_aging: If True, allow more than 18 years with aging effects

    Returns:
        PriorExperience object with complete record
    """
    starting_age = 16
    track = skill_track.track
    survivability = skill_track.survivability

    # Determine target years
    if years == -1:
        # Random years (0-18)
        target_years = random.randint(0, 18)
    elif allow_aging:
        # Allow any number of years
        target_years = max(0, years)
    else:
        # Clamp to valid range (0-18)
        target_years = max(0, min(18, years))

    yearly_results = []
    all_skills = []
    total_skill_points = 0
    total_free_points = 0
    total_xp = 0
    died = False
    death_year = None
    years_served = 0
    aging_effects = AgingEffects()
    initial_skills_granted = False

    for year_index in range(target_years):
        years_served = year_index + 1

        year_result = roll_single_year(
            skill_track=skill_track,
            year_index=year_index,
            total_modifier=total_modifier,
            aging_effects=aging_effects,
        )

        # Grant initial skills after completing first year (age 17)
        if not initial_skills_granted:
            all_skills.extend(skill_track.initial_skills)
            initial_skills_granted = True

        all_skills.append(year_result.skill_gained)
        total_skill_points += year_result.skill_points
        total_free_points += year_result.free_skill_points
        total_xp += year_result.xp_gained
        yearly_results.append(year_result)

        if not year_result.survived:
            died = True
            death_year = year_result.year
            break

    final_age = starting_age + years_served if not died else death_year

    return PriorExperience(
        starting_age=starting_age,
        final_age=final_age,
        years_served=years_served,
        track=track,
        survivability_target=survivability,
        yearly_results=yearly_results,
        total_skill_points=total_skill_points,
        all_skills=all_skills,
        died=died,
        death_year=death_year,
        attribute_scores=attribute_scores,
        attribute_modifiers=attribute_modifiers,
        aging_effects=aging_effects if years_served > 18 else None,
        total_free_points=total_free_points,
        total_xp=total_xp,
    )
