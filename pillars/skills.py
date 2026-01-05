"""Skill points and level calculation for Pillars character system.

Each year of prior experience grants:
- 1 automatic skill point (to the rolled skill)
- 1 free spendable skill point (player choice)
- 1000 XP

Skill levels use triangular numbers:
- Level 1 = 1 point
- Level 2 = 3 points (1 + 2)
- Level 3 = 6 points (3 + 3)
- Level N = N * (N + 1) / 2 points

Display format: "Sword II (+2)" means Level 2 with 2 extra points toward Level 3
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional
import re

# Import spell mastery constants if available
try:
    from pillars.constants import SPELL_SKILL_MASTERY
except ImportError:
    SPELL_SKILL_MASTERY = {}


def points_for_level(level: int) -> int:
    """Total points needed to reach a level (triangular number).

    Level 1 = 1, Level 2 = 3, Level 3 = 6, Level 4 = 10, etc.
    """
    if level <= 0:
        return 0
    return level * (level + 1) // 2


def level_from_points(points: int) -> Tuple[int, int]:
    """Given total points, return (level, excess_points toward next level).

    Examples:
        1 point  -> (1, 0)  = Level I
        2 points -> (1, 1)  = Level I (+1)
        3 points -> (2, 0)  = Level II
        5 points -> (2, 2)  = Level II (+2)
        6 points -> (3, 0)  = Level III
    """
    if points <= 0:
        return 0, 0

    level = 0
    while points_for_level(level + 1) <= points:
        level += 1

    excess = points - points_for_level(level)
    return level, excess


def to_roman(num: int) -> str:
    """Convert integer to Roman numeral."""
    if num <= 0:
        return ""

    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman = ""
    for i, v in enumerate(val):
        while num >= v:
            roman += syms[i]
            num -= v
    return roman


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for point tracking (case-insensitive).

    Groups skills by base name and type, using lowercase for consistent matching.
    'Sword +1 to hit' and 'Sword +1 parry' are kept separate as 'sword to hit' and 'sword parry'.
    'Sword +1 to hit' and 'Sword +2 to hit' both become 'sword to hit' (number stripped).
    'Parry I' and 'parry 1' both become 'parry' (case-insensitive, number stripped).

    For spells (starting with "Spell:"), preserves the full spell name including numbers
    to keep different spells separate (e.g., "Counter 1" vs "Counter 2").
    """
    if not skill:
        return ""

    skill = skill.strip()

    # Special handling for spells - preserve full name including numbers
    # This ensures "Spell: Counter 1" and "Spell: Counter 2" remain separate
    if skill.lower().startswith("spell:"):
        # For spells, just lowercase the entire name but preserve structure
        # This keeps "Spell: Counter 1" and "Spell: Counter 2" as separate skills
        return skill.lower()

    # Extract base name and suffix type, keeping them separate
    # Pattern: "BaseName +N suffix" -> "basename suffix"
    match = re.match(
        r"^(.+?)\s*\+\d+\s+(to\s+hit|parry|damage)(\s*$)", skill, re.IGNORECASE
    )
    if match:
        base = match.group(1).strip().lower()
        suffix = match.group(2).strip().lower()
        return f"{base} {suffix}"

    # For skills with just +N (no specific suffix), strip the number
    skill = re.sub(r"\s*\+\d+\s*$", "", skill, flags=re.IGNORECASE)

    # Remove other patterns
    patterns = [
        r"\s*\(x\d+\)\s*$",
        r"\s+\d+\s*$",  # Trailing numbers with space
        r"\s+[IVXivx]+\s*$",  # Trailing Roman numerals (I, II, III, IV, V, etc.)
    ]

    for pattern in patterns:
        skill = re.sub(pattern, "", skill, flags=re.IGNORECASE)

    return skill.strip().lower()


@dataclass
class SkillPoints:
    """Tracks points for a single skill."""

    automatic: int = 0  # Points from rolled skills during prior experience
    allocated: int = 0  # Points manually allocated by player
    display_name: str = ""  # Original display name (preserves user's casing)

    @property
    def total(self) -> int:
        """Total points in this skill."""
        return self.automatic + self.allocated

    @property
    def level(self) -> int:
        """Current skill level based on total points."""
        return level_from_points(self.total)[0]

    @property
    def excess_points(self) -> int:
        """Points beyond current level, toward next level."""
        return level_from_points(self.total)[1]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "automatic": self.automatic,
            "allocated": self.allocated,
            "total": self.total,
            "display_name": self.display_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillPoints":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            automatic=data.get("automatic", 0),
            allocated=data.get("allocated", 0),
            display_name=data.get("display_name", ""),
        )


@dataclass
class CharacterSkills:
    """Container for all character skills, free points, and XP."""

    skills: Dict[str, SkillPoints] = field(default_factory=dict)
    free_points: int = 0  # Unallocated free skill points
    total_xp: int = 0  # Total experience points

    def add_automatic_point(self, skill_name: str) -> None:
        """Add 1 automatic point from a rolled skill.

        The skill name is normalized to group related skills.
        The original skill name is preserved as display_name.

        For spells with slashes (e.g., "Spell: Counter 1/Shield/Detect Magic"),
        splits them into separate spell skills.
        """
        skill_name = skill_name.strip()

        # Handle spell names with slashes - split into separate spells
        if skill_name.startswith("Spell:") and "/" in skill_name:
            # Split "Spell: Counter 1/Shield/Detect Magic" into separate spells
            spell_prefix = "Spell: "
            spell_content = skill_name[len(spell_prefix) :].strip()
            spell_names = [s.strip() for s in spell_content.split("/") if s.strip()]

            # Add each spell separately
            for spell in spell_names:
                full_spell_name = f"{spell_prefix}{spell}"
                normalized = normalize_skill_name(full_spell_name)
                if normalized:
                    if normalized not in self.skills:
                        self.skills[normalized] = SkillPoints(
                            display_name=full_spell_name
                        )
                    self.skills[normalized].automatic += 1
            return

        # Normal handling for non-split skills
        normalized = normalize_skill_name(skill_name)
        if not normalized:
            return

        if normalized not in self.skills:
            # Preserve the original name (stripped but not lowercased) as display
            display = skill_name.strip()
            self.skills[normalized] = SkillPoints(display_name=display)
        self.skills[normalized].automatic += 1

    def add_free_point(self) -> None:
        """Add 1 unallocated free skill point."""
        self.free_points += 1

    def allocate_point(self, skill_name: str) -> bool:
        """Allocate a free point to a skill.

        Returns True if successful, False if no free points available.
        The original skill name is preserved as display_name if this is a new skill.

        For spells with slashes (e.g., "Spell: Counter 1/Shield/Detect Magic"),
        splits them into separate spell skills.
        """
        if self.free_points <= 0:
            return False

        skill_name = skill_name.strip()

        # Handle spell names with slashes - split into separate spells
        if skill_name.startswith("Spell:") and "/" in skill_name:
            # Split "Spell: Counter 1/Shield/Detect Magic" into separate spells
            spell_prefix = "Spell: "
            spell_content = skill_name[len(spell_prefix) :].strip()
            spell_names = [s.strip() for s in spell_content.split("/") if s.strip()]

            # Need at least one free point per spell
            if self.free_points < len(spell_names):
                return False

            # Add each spell separately
            for spell in spell_names:
                full_spell_name = f"{spell_prefix}{spell}"
                normalized = normalize_skill_name(full_spell_name)
                if normalized:
                    if normalized not in self.skills:
                        self.skills[normalized] = SkillPoints(
                            display_name=full_spell_name
                        )
                    self.skills[normalized].allocated += 1
                    self.free_points -= 1
            return True

        # Normal handling for non-split skills
        normalized = normalize_skill_name(skill_name)
        if not normalized:
            return False

        if normalized not in self.skills:
            # Preserve the original name as display
            display = skill_name.strip()
            self.skills[normalized] = SkillPoints(display_name=display)

        self.skills[normalized].allocated += 1
        self.free_points -= 1
        return True

    def deallocate_point(self, skill_name: str) -> bool:
        """Remove an allocated point from a skill, returning it to free pool.

        Returns True if successful, False if no allocated points to remove.
        """
        normalized = normalize_skill_name(skill_name)
        if not normalized or normalized not in self.skills:
            return False

        if self.skills[normalized].allocated <= 0:
            return False

        self.skills[normalized].allocated -= 1
        self.free_points += 1
        return True

    def add_xp(self, amount: int) -> None:
        """Add XP to the character."""
        self.total_xp += amount

    def _get_spell_mastery_description(self, level: int) -> Optional[str]:
        """Get mastery description for a spell at the given level.

        Returns None for level 1 (no mastery description needed).
        Returns mastery text for level 2+.
        """
        if level <= 1:
            return None
        # Cap mastery level at 6
        mastery_level = min(level, 6)
        return SPELL_SKILL_MASTERY.get(mastery_level, "")

    def get_skill_display(self, skill_name: str) -> str:
        """Get display string for a single skill.

        Returns format like "Sword II (+2)" or "Tracking I".
        For spells with level > 1, includes mastery description.
        Uses the stored display_name if available, otherwise falls back to
        title-casing the normalized name.
        """
        normalized = normalize_skill_name(skill_name)
        if normalized not in self.skills:
            return skill_name

        sp = self.skills[normalized]
        # Use stored display name, or title-case the normalized name as fallback
        display = sp.display_name if sp.display_name else normalized.title()
        level, excess = level_from_points(sp.total)

        # Check if this is a spell (starts with "Spell:")
        is_spell = display.strip().startswith("Spell:") or normalized.startswith(
            "spell:"
        )

        # Strip any existing mastery description from display name (in parentheses at the end)
        # This handles legacy characters that had mastery baked into the name
        if is_spell:
            # Remove pattern like " (Cast spell normally)" from the end
            display = re.sub(r"\s*\([^)]+\)\s*$", "", display).strip()

        if level >= 1:
            roman = to_roman(level)
            mastery_desc = None
            # Only show mastery description for spells with level > 1
            if is_spell and level > 1:
                mastery_desc = self._get_spell_mastery_description(level)

            # Build the display string
            if excess > 0:
                base = f"{display} {roman} (+{excess})"
            else:
                base = f"{display} {roman}"

            # Append mastery description if present
            if mastery_desc:
                return f"{base} ({mastery_desc})"
            else:
                return base
        else:
            # Less than 1 point - shouldn't happen but handle gracefully
            return f"{display} (+{sp.total})"

    def get_display_list(self) -> List[str]:
        """Get formatted skill list for display.

        Returns list of strings like ["Sword II (+2)", "Tracking I"].
        """
        result = []
        for name in sorted(self.skills.keys()):
            display = self.get_skill_display(name)
            result.append(display)
        return result

    def get_skills_with_details(self) -> List[dict]:
        """Get skills with full details for UI rendering.

        Returns list of dicts with name, display, level, points, etc.
        """
        result = []
        for name in sorted(self.skills.keys()):
            sp = self.skills[name]
            level, excess = level_from_points(sp.total)
            points_needed = points_for_level(level + 1) - sp.total
            # Raw display name for editing (without level suffix)
            display_name = sp.display_name if sp.display_name else name.title()

            result.append(
                {
                    "name": name,  # normalized key (lowercase)
                    "display_name": display_name,  # editable display name
                    "display": self.get_skill_display(name),  # full display with level
                    "level": level,
                    "level_roman": to_roman(level) if level > 0 else "",
                    "total_points": sp.total,
                    "automatic_points": sp.automatic,
                    "allocated_points": sp.allocated,
                    "excess_points": excess,
                    "points_to_next_level": points_needed,
                    "acquired": "Assigned" if sp.allocated > 0 else "Automatic",
                }
            )
        return result

    def rename_skill(self, old_name: str, new_name: str) -> bool:
        """Rename a skill's display name.

        The normalized key remains the same if the new name normalizes to the same value.
        If it normalizes to a different value, the skill is moved to the new key.
        Returns True if successful, False if skill not found.
        """
        old_normalized = normalize_skill_name(old_name)
        if old_normalized not in self.skills:
            return False

        new_normalized = normalize_skill_name(new_name)
        if not new_normalized:
            return False

        sp = self.skills[old_normalized]

        if old_normalized == new_normalized:
            # Same key, just update display name
            sp.display_name = new_name.strip()
        else:
            # Different key - merge into existing or create new
            if new_normalized in self.skills:
                # Merge into existing skill
                existing = self.skills[new_normalized]
                existing.automatic += sp.automatic
                existing.allocated += sp.allocated
                # Keep the new display name
                existing.display_name = new_name.strip()
            else:
                # Move to new key with new display name
                sp.display_name = new_name.strip()
                self.skills[new_normalized] = sp
            # Remove old entry
            del self.skills[old_normalized]

        return True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "skill_points": {name: sp.to_dict() for name, sp in self.skills.items()},
            "free_skill_points": self.free_points,
            "total_xp": self.total_xp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterSkills":
        """Create from dictionary (JSON deserialization)."""
        skills = {}
        for name, sp_data in data.get("skill_points", {}).items():
            skills[name] = SkillPoints.from_dict(sp_data)

        return cls(
            skills=skills,
            free_points=data.get("free_skill_points", 0),
            total_xp=data.get("total_xp", 0),
        )

    @classmethod
    def from_legacy_skills(
        cls, skill_list: List[str], years: int = 0
    ) -> "CharacterSkills":
        """Create from legacy skill list format.

        Used for migrating existing characters.
        Each skill in the list becomes 1 automatic point.
        Free points = years (all unallocated for legacy characters).
        XP = years * 1000.
        """
        char_skills = cls(skills={}, free_points=years, total_xp=years * 1000)

        for skill in skill_list:
            if skill:
                char_skills.add_automatic_point(skill)

        return char_skills
