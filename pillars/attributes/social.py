"""
Social attribute generation for Pillars RPG.

This module handles the generation of social characteristics
including provenance, literacy, location, and wealth.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from pillars.dice import roll_dice, roll_die, roll_percentile
from pillars.config import (
    NOBILITY_THRESHOLD,
    MERCHANT_THRESHOLD,
    WEALTH_SUBSISTENCE_MAX,
    WEALTH_MODERATE_MAX,
    WEALTH_MERCHANT_MAX,
    LOCATION_CITY_MAX,
    LOCATION_VILLAGE_MAX,
    LOCATION_RURAL_MAX,
    LITERACY_MODIFIERS,
    VILLAGE_SKILL_THRESHOLD,
    RURAL_SKILL_COUNT,
)


__all__ = [
    # Classes
    "Provenance",
    "LiteracyCheck",
    "Location",
    "Wealth",
    # Constants
    "SURVIVAL_SKILLS",
    # Functions
    "get_nobility_rank",
    "get_merchant_type",
    "get_commoner_type",
    "get_craft_type",
    "roll_provenance",
    "roll_literacy_check",
    "roll_location",
    "get_wealth_level",
    "roll_wealth",
]


@dataclass
class Provenance:
    """Stores the result of a provenance (social class) roll."""

    main_roll: int
    sub_roll: Optional[int]
    craft_roll: Optional[int]
    social_class: str
    sub_class: str
    craft_type: Optional[str]

    def __str__(self) -> str:
        result = f"Provenance: {self.social_class}"
        if self.sub_class:
            result += f" - {self.sub_class}"
        if self.craft_type:
            result += f" ({self.craft_type})"
        rolls = [str(self.main_roll)]
        if self.sub_roll is not None:
            rolls.append(str(self.sub_roll))
        if self.craft_roll is not None:
            rolls.append(str(self.craft_roll))
        result += f" (Rolled: [{', '.join(rolls)}])"
        return result


def get_nobility_rank(roll: int) -> str:
    """
    Get nobility rank from d100 roll.

    Args:
        roll: d100 roll result (1-100)

    Returns:
        Nobility rank string
    """
    if roll == 1:
        return "Monarch"
    elif roll <= 5:
        return "Royal Family"
    elif roll <= 12:
        return "Duke"
    elif roll <= 30:
        return "March/Border Lord"
    elif roll <= 40:
        return "Count/Earl"
    elif roll <= 46:
        return "Viscount"
    elif roll <= 60:
        return "Baron"
    elif roll <= 85:
        return "Baronet"
    else:
        return "Knight/Warrior Nobility"


def get_merchant_type(roll: int) -> str:
    """
    Get merchant type from d100 roll.

    Args:
        roll: d100 roll result (1-100)

    Returns:
        Merchant type string
    """
    if roll <= 70:
        return "Retail"
    elif roll <= 95:
        return "Wholesale"
    else:
        return "Specialty"


def get_commoner_type(roll: int) -> str:
    """
    Get commoner type from d100 roll.

    Args:
        roll: d100 roll result (1-100)

    Returns:
        Commoner type string
    """
    if roll <= 70:
        return "Laborer"
    else:
        return "Crafts"


def get_craft_type(roll: int) -> str:
    """
    Get craft specialization from d100 roll.

    Args:
        roll: d100 roll result (1-100)

    Returns:
        Craft type string
    """
    if roll <= 50:
        return "Smith/Builder/Wainwright"
    elif roll <= 85:
        return "Medical/Herb Lore/Maker"
    else:
        return "Magic"


def roll_provenance() -> Provenance:
    """
    Roll for character provenance (social class) using percentile dice.

    Rolls d100 to determine social class:
    - 1-10: Nobility (rolls again on nobility sub-table)
    - 11-30: Merchant (rolls again on merchant sub-table)
    - 31-100: Commoner (rolls again on commoner sub-table)

    Returns:
        Provenance object with rolls, social class, and sub-class
    """
    main_roll = roll_percentile()
    sub_roll = None
    craft_roll = None
    craft_type = None

    if main_roll <= NOBILITY_THRESHOLD:
        # Nobility
        social_class = "Nobility"
        sub_roll = roll_percentile()
        sub_class = get_nobility_rank(sub_roll)
    elif main_roll <= MERCHANT_THRESHOLD:
        # Merchant
        social_class = "Merchant"
        sub_roll = roll_percentile()
        sub_class = get_merchant_type(sub_roll)
    else:
        # Commoner
        social_class = "Commoner"
        sub_roll = roll_percentile()
        sub_class = get_commoner_type(sub_roll)

        # If Crafts, roll for craft type
        if sub_class == "Crafts":
            craft_roll = roll_percentile()
            craft_type = get_craft_type(craft_roll)

    return Provenance(
        main_roll=main_roll,
        sub_roll=sub_roll,
        craft_roll=craft_roll,
        social_class=social_class,
        sub_class=sub_class,
        craft_type=craft_type,
    )


# Survival skills for Rural characters
SURVIVAL_SKILLS = ["Survival", "Hunting", "Tracking", "Wood Lore", "Herb Lore"]


@dataclass
class LiteracyCheck:
    """Stores the result of a literacy check using 3d6 roll-under."""

    roll: int
    int_value: int
    difficulty_modifier: int
    target: int
    is_literate: bool

    def __str__(self) -> str:
        diff_str = ""
        if self.difficulty_modifier > 0:
            diff_str = f"-{self.difficulty_modifier}"
        elif self.difficulty_modifier < 0:
            diff_str = f"+{abs(self.difficulty_modifier)}"

        result = "Literate" if self.is_literate else "Illiterate"
        return f"Literacy: {result} (Rolled {self.roll} vs INT {self.int_value}{diff_str} = {self.target})"


def roll_literacy_check(int_value: int, difficulty_modifier: int = 0) -> LiteracyCheck:
    """
    Roll a literacy check based on INT using 3d6 roll-under.

    Mechanic: Roll 3d6, must roll LESS THAN (INT - difficulty_modifier) to pass.

    Args:
        int_value: Character's INT attribute value
        difficulty_modifier: Penalty to INT (higher = harder, e.g. +4 for Rural)

    Returns:
        LiteracyCheck object with roll details and result

    Example:
        INT 10, Rural (+4 difficulty): must roll < 6 on 3d6
    """
    roll = sum(roll_dice(3, 6))
    target = int_value - difficulty_modifier
    is_literate = roll < target

    return LiteracyCheck(
        roll=roll,
        int_value=int_value,
        difficulty_modifier=difficulty_modifier,
        target=target,
        is_literate=is_literate,
    )


@dataclass
class Location:
    """Stores the result of a location roll."""

    roll: int
    location_type: str
    skills: List[str]
    skill_roll: Optional[
        int
    ]  # For Village skill selection (1-2 = Street Smarts, 3-6 = Survival)
    attribute_modifiers: Dict[str, int]
    attribute_roll: Optional[
        int
    ]  # For Village attribute selection (1=INT, 2=WIS, 3=STR, 4=DEX)
    skill_rolls: Optional[List[int]]  # For Rural skill selection
    literacy_check_modifier: int

    def __str__(self) -> str:
        lines = [f"Location: {self.location_type} (Rolled: {self.roll})"]

        # Skills with rolls
        if self.skills:
            if self.skill_roll is not None:
                # Village: show the roll
                lines.append(f"  Skill: {self.skills[0]} (Rolled: {self.skill_roll})")
            elif self.skill_rolls is not None:
                # Rural: show the rolls for each skill
                skills_with_rolls = [
                    f"{skill} ({roll})"
                    for skill, roll in zip(self.skills, self.skill_rolls)
                ]
                lines.append(f"  Skills: {', '.join(skills_with_rolls)}")
            else:
                # City: fixed skill
                lines.append(f"  Skill: {', '.join(self.skills)}")
        else:
            lines.append("  Skills: None")

        # Attribute modifiers with rolls
        if self.attribute_modifiers:
            mods = []
            for attr, mod in self.attribute_modifiers.items():
                if mod > 0:
                    mods.append(f"+{mod} {attr}")
                elif mod < 0:
                    mods.append(f"{mod} {attr}")
            if self.attribute_roll is not None:
                # Village: show the roll
                lines.append(
                    f"  Attribute Modifier: {', '.join(mods)} (Rolled: {self.attribute_roll})"
                )
            else:
                # City/Rural: fixed modifiers
                lines.append(f"  Attribute Modifiers: {', '.join(mods)}")
        else:
            lines.append("  Attribute Modifiers: None")

        return "\n".join(lines)


def roll_location() -> Location:
    """
    Roll for character location using percentile dice.

    Rolls d100 to determine location:
    - 1-20: City (Street smarts, -1 CON +1 INT, literacy INT check)
    - 21-70: Village (Street smarts OR Survival random, +1 to random stat, literacy INT check +2)
    - 71-99: Rural (2 random survival skills, +1 STR +1 DEX, literacy INT check +4)
    - 100: Special (Off-lander, consult DM)

    Returns:
        Location object with roll, location type, skills, and modifiers
    """
    roll = roll_percentile()
    skill_roll = None
    attribute_roll = None
    skill_rolls = None

    if roll <= LOCATION_CITY_MAX:
        # City
        location_type = "City"
        skills = ["Street Smarts"]
        attribute_modifiers = {"CON": -1, "INT": 1}
        literacy_check_modifier = LITERACY_MODIFIERS["city"]

    elif roll <= LOCATION_VILLAGE_MAX:
        # Village
        location_type = "Village"
        # Random: Street Smarts OR Survival (d6: 1-3 = Street Smarts, 4-6 = Survival)
        skill_roll = roll_die(6)
        if skill_roll <= VILLAGE_SKILL_THRESHOLD:
            skills = ["Street Smarts"]
        else:
            skills = ["Survival"]
        # Random: +1 to INT, WIS, STR, or DEX (d4: 1=INT, 2=WIS, 3=STR, 4=DEX)
        attribute_roll = roll_die(4)
        attr_options = ["INT", "WIS", "STR", "DEX"]
        bonus_attr = attr_options[attribute_roll - 1]
        attribute_modifiers = {bonus_attr: 1}
        literacy_check_modifier = LITERACY_MODIFIERS["village"]

    elif roll <= LOCATION_RURAL_MAX:
        # Rural
        location_type = "Rural"
        # Pick 2 random survival skills using d5 (d6, reroll 6)
        skill_rolls = []
        selected_indices = []
        while len(selected_indices) < RURAL_SKILL_COUNT:
            skill_die = roll_die(6)
            while skill_die == 6:  # Reroll 6s for d5
                skill_die = roll_die(6)
            if skill_die - 1 not in selected_indices:  # Avoid duplicates
                selected_indices.append(skill_die - 1)
                skill_rolls.append(skill_die)
        skills = [SURVIVAL_SKILLS[i] for i in selected_indices]
        attribute_modifiers = {"STR": 1, "DEX": 1}
        literacy_check_modifier = LITERACY_MODIFIERS["rural"]

    else:
        # Special (100)
        location_type = "Special (Off-lander)"
        skills = []
        attribute_modifiers = {}
        literacy_check_modifier = LITERACY_MODIFIERS["special"]

    return Location(
        roll=roll,
        location_type=location_type,
        skills=skills,
        skill_roll=skill_roll,
        attribute_modifiers=attribute_modifiers,
        attribute_roll=attribute_roll,
        skill_rolls=skill_rolls,
        literacy_check_modifier=literacy_check_modifier,
    )


@dataclass
class Wealth:
    """Stores the result of a wealth roll."""

    roll: int
    wealth_level: str
    starting_coin: int
    bonus_roll: Optional[int]  # For Merchant level (additional percentile roll)

    def __str__(self) -> str:
        result = f"Wealth: {self.wealth_level} ({self.starting_coin} coin)"
        if self.bonus_roll is not None:
            result += f" (Rolled: {self.roll}, bonus: {self.bonus_roll})"
        else:
            result += f" (Rolled: {self.roll})"
        return result


def get_wealth_level(roll: int) -> str:
    """
    Get wealth level from percentile roll.

    Args:
        roll: Percentile roll result (0-100, with 0 representing low roll)

    Returns:
        Wealth level string
    """
    if roll <= WEALTH_SUBSISTENCE_MAX:
        return "Subsistence"
    elif roll <= WEALTH_MODERATE_MAX:
        return "Moderate"
    elif roll <= WEALTH_MERCHANT_MAX:
        return "Merchant"
    else:
        return "Rich"


def roll_wealth(allow_rich: bool = True) -> Wealth:
    """
    Roll for character wealth using percentile dice.

    Rolls d100 to determine wealth level:
    - 0-15: Subsistence (10 coin)
    - 16-70: Moderate (100 coin)
    - 71-95: Merchant (100 + percentile dice coin)
    - 96-100: Rich (Consult DM)

    Note: If choosing wealth level (not rolling), Rich cannot be chosen.

    Args:
        allow_rich: Whether Rich result is allowed (False when choosing instead of rolling)

    Returns:
        Wealth object with roll, level, and starting coin
    """
    roll = roll_percentile()
    bonus_roll = None

    # Handle the case where Rich is not allowed (reroll)
    if not allow_rich:
        while roll >= 96:
            roll = roll_percentile()

    wealth_level = get_wealth_level(roll)

    if roll <= 15:
        starting_coin = 10
    elif roll <= 70:
        starting_coin = 100
    elif roll <= 95:
        # Merchant: 100 + percentile dice
        bonus_roll = roll_percentile()
        starting_coin = 100 + bonus_roll
    else:
        # Rich: Consult DM, use 0 as placeholder
        starting_coin = 0

    return Wealth(
        roll=roll,
        wealth_level=wealth_level,
        starting_coin=starting_coin,
        bonus_roll=bonus_roll,
    )
