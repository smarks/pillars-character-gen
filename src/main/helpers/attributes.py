"""
Character attribute generation for Pillars RPG.

This module handles the generation of character attributes using
various methods (dice rolling or point allocation).
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
from main.helpers.dice import roll_dice, roll_with_drop_lowest, roll_demon_die, roll_percentile, roll_die


# Attribute names
CORE_ATTRIBUTES = ["STR", "DEX", "INT", "WIS", "CON", "CHR"]

# Attribute modifier table
ATTRIBUTE_MODIFIERS = {
    3: -5,
    4: -4,
    5: -3,
    6: -2,
    7: -1,
    8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0,
    14: 1,
    15: 2,
    16: 3,
    17: 4,
    18: 5
}


@dataclass
class AttributeRoll:
    """Stores the result of a single attribute roll."""
    attribute_name: str
    all_rolls: List[int]
    kept_rolls: List[int]
    value: int
    modifier: int

    def __str__(self) -> str:
        """Format the roll result for display."""
        all_rolls_str = ", ".join(map(str, self.all_rolls))
        kept_rolls_str = ", ".join(map(str, self.kept_rolls))
        mod_str = f"+{self.modifier}" if self.modifier >= 0 else str(self.modifier)
        return (f"{self.attribute_name}: {self.value} (modifier: {mod_str})\n"
                f"  Rolled: [{all_rolls_str}] → Kept: [{kept_rolls_str}]")


@dataclass
class CharacterAttributes:
    """Stores all character attributes and their modifiers."""
    STR: int
    DEX: int
    INT: int
    WIS: int
    CON: int
    CHR: int
    generation_method: str
    roll_details: List[AttributeRoll] = field(default_factory=list)

    def get_modifier(self, attribute: str) -> int:
        """
        Get the modifier for a given attribute.

        Args:
            attribute: Attribute name (STR, DEX, INT, WIS, CON, CHR)

        Returns:
            Modifier value based on attribute score

        Raises:
            ValueError: If attribute name is invalid
        """
        if attribute not in CORE_ATTRIBUTES:
            raise ValueError(f"Invalid attribute: {attribute}")

        value = getattr(self, attribute)
        return get_attribute_modifier(value)

    def get_all_modifiers(self) -> Dict[str, int]:
        """Get modifiers for all attributes."""
        return {attr: self.get_modifier(attr) for attr in CORE_ATTRIBUTES}

    def __str__(self) -> str:
        """Format attributes for display."""
        lines = [f"Character Attributes (Generated via {self.generation_method})", "=" * 50]

        for attr in CORE_ATTRIBUTES:
            value = getattr(self, attr)
            modifier = self.get_modifier(attr)
            mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
            lines.append(f"{attr}: {value:2d} (modifier: {mod_str})")

        return "\n".join(lines)


def get_attribute_modifier(value: int) -> int:
    """
    Calculate the modifier for an attribute value.

    Args:
        value: Attribute value (typically 3-18)

    Returns:
        Modifier value

    Examples:
        >>> get_attribute_modifier(3)
        -5
        >>> get_attribute_modifier(10)
        0
        >>> get_attribute_modifier(18)
        5
    """
    if value in ATTRIBUTE_MODIFIERS:
        return ATTRIBUTE_MODIFIERS[value]

    # Handle values outside the standard range
    if value < 3:
        return -5  # Floor at -5
    elif value > 18:
        # Extend the pattern: each point above 18 adds +1
        return 5 + (value - 18)
    else:
        # Should not happen with standard table
        return 0


def roll_single_attribute_3d6() -> Tuple[List[int], int]:
    """
    Roll a single attribute using 3d6 method.

    Returns:
        Tuple of (list of rolls, sum)

    Examples:
        >>> import random
        >>> random.seed(42)
        >>> roll_single_attribute_3d6()
        ([2, 6, 2], 10)
    """
    rolls = roll_dice(3, 6)
    return rolls, sum(rolls)


def roll_single_attribute_4d6_drop_lowest() -> Tuple[List[int], List[int], int]:
    """
    Roll a single attribute using 4d6 drop lowest method.

    This is a common method that produces higher average attributes.

    Returns:
        Tuple of (all rolls, kept rolls, sum of kept rolls)

    Examples:
        >>> import random
        >>> random.seed(42)
        >>> roll_single_attribute_4d6_drop_lowest()
        ([2, 6, 2, 4], [2, 6, 4], 12)
    """
    return roll_with_drop_lowest(4, 6, 1)


def generate_attributes_3d6() -> CharacterAttributes:
    """
    Generate all six core attributes using 3d6 method.

    Returns:
        CharacterAttributes object with all attributes and roll details

    Examples:
        >>> import random
        >>> random.seed(42)
        >>> attrs = generate_attributes_3d6()
        >>> attrs.STR
        10
    """
    attributes = {}
    roll_details = []

    for attr_name in CORE_ATTRIBUTES:
        rolls, total = roll_single_attribute_3d6()
        attributes[attr_name] = total

        # Create roll detail
        roll_detail = AttributeRoll(
            attribute_name=attr_name,
            all_rolls=rolls,
            kept_rolls=rolls,  # 3d6 keeps all rolls
            value=total,
            modifier=get_attribute_modifier(total)
        )
        roll_details.append(roll_detail)

    return CharacterAttributes(
        **attributes,
        generation_method="3d6",
        roll_details=roll_details
    )


def generate_attributes_4d6_drop_lowest() -> CharacterAttributes:
    """
    Generate all six core attributes using 4d6 drop lowest method.

    Returns:
        CharacterAttributes object with all attributes and roll details

    Examples:
        >>> import random
        >>> random.seed(42)
        >>> attrs = generate_attributes_4d6_drop_lowest()
        >>> attrs.STR
        12
    """
    attributes = {}
    roll_details = []

    for attr_name in CORE_ATTRIBUTES:
        all_rolls, kept_rolls, total = roll_single_attribute_4d6_drop_lowest()
        attributes[attr_name] = total

        # Create roll detail
        roll_detail = AttributeRoll(
            attribute_name=attr_name,
            all_rolls=all_rolls,
            kept_rolls=kept_rolls,
            value=total,
            modifier=get_attribute_modifier(total)
        )
        roll_details.append(roll_detail)

    return CharacterAttributes(
        **attributes,
        generation_method="4d6 drop lowest",
        roll_details=roll_details
    )


def generate_attributes_point_buy(points: int = 65) -> CharacterAttributes:
    """
    Create attributes using point buy system.

    Note: This returns a template with all attributes set to minimum.
    The actual allocation should be done interactively or via input.

    Args:
        points: Total points to allocate (default: 65)

    Returns:
        CharacterAttributes object with placeholder values
    """
    # For point buy, we start with a base template
    # This would need interactive input to complete
    min_value = 3
    attributes = {attr: min_value for attr in CORE_ATTRIBUTES}

    return CharacterAttributes(
        **attributes,
        generation_method=f"Point Buy ({points} points)",
        roll_details=[]
    )


def validate_point_buy(attributes: Dict[str, int], total_points: int = 65) -> Tuple[bool, str]:
    """
    Validate that point buy allocation is legal.

    Args:
        attributes: Dictionary of attribute values
        total_points: Maximum allowed points

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_point_buy({"STR": 10, "DEX": 10, "INT": 10, "WIS": 10, "CON": 10, "CHR": 15})
        (True, '')
        >>> validate_point_buy({"STR": 20, "DEX": 20, "INT": 20, "WIS": 5, "CON": 0, "CHR": 0})
        (False, 'Total points (65) does not equal allowed points (65)')
    """
    # Check all attributes are present
    for attr in CORE_ATTRIBUTES:
        if attr not in attributes:
            return False, f"Missing attribute: {attr}"

    # Check values are reasonable (assuming min 3, max 18 for starting)
    for attr, value in attributes.items():
        if value < 3:
            return False, f"{attr} value ({value}) is below minimum (3)"
        if value > 18:
            return False, f"{attr} value ({value}) exceeds maximum (18)"

    # Check total points
    total_used = sum(attributes.values())
    if total_used != total_points:
        return False, f"Total points ({total_used}) does not equal allowed points ({total_points})"

    return True, ""


def display_attribute_rolls(character: CharacterAttributes) -> None:
    """
    Display detailed attribute roll information.

    Args:
        character: CharacterAttributes object with roll details
    """
    print(f"\n{character.generation_method.upper()} ATTRIBUTE GENERATION")
    print("=" * 60)

    for roll_detail in character.roll_details:
        print(roll_detail)
        print()

    print("=" * 60)
    print("\nSUMMARY:")
    print(character)
    print()

    # Calculate total and average
    total = sum(getattr(character, attr) for attr in CORE_ATTRIBUTES)
    average = total / len(CORE_ATTRIBUTES)
    print(f"\nTotal: {total}")
    print(f"Average: {average:.2f}")


@dataclass
class Appearance:
    """Stores the result of an appearance roll using a demon die."""
    rolls: List[int]
    intensity: int
    description: str

    def __str__(self) -> str:
        rolls_str = ", ".join(map(str, self.rolls))
        return f"Appearance: {self.description} (Rolled: [{rolls_str}])"


def get_appearance_description(intensity: int) -> str:
    """
    Get the appearance description based on demon die intensity.

    Args:
        intensity: Negative for pretty, positive for ugly, 0 for average

    Returns:
        Description string

    Examples:
        >>> get_appearance_description(-1)
        'Pretty'
        >>> get_appearance_description(0)
        'Average'
        >>> get_appearance_description(3)
        'Very Ugly'
    """
    if intensity == 0:
        return "Average"
    elif intensity < 0:
        # Pretty direction
        count = abs(intensity)
        if count == 1:
            return "Pretty"
        elif count == 2:
            return "Very Pretty"
        else:
            return "Extremely Pretty"
    else:
        # Ugly direction
        if intensity == 1:
            return "Ugly"
        elif intensity == 2:
            return "Very Ugly"
        else:
            return "Extremely Ugly"


def roll_appearance() -> Appearance:
    """
    Roll for character appearance using a demon die.

    Uses the demon die mechanic:
    - Roll 1d6
    - 1: Pretty (keep rolling on 1s for more intensity)
    - 2-5: Average
    - 6: Ugly (keep rolling on 6s for more intensity)

    Returns:
        Appearance object with rolls, intensity, and description

    Examples:
        >>> import random
        >>> random.seed(42)
        >>> app = roll_appearance()
        >>> app.description
        'Average'
    """
    rolls, intensity = roll_demon_die()
    description = get_appearance_description(intensity)

    return Appearance(
        rolls=rolls,
        intensity=intensity,
        description=description
    )


@dataclass
class Height:
    """Stores the result of a height roll."""
    rolls: List[int]
    hands: int
    inches: int

    @property
    def feet(self) -> int:
        """Get the feet component of height."""
        return self.inches // 12

    @property
    def remaining_inches(self) -> int:
        """Get the remaining inches after feet."""
        return self.inches % 12

    @property
    def imperial(self) -> str:
        """Get height in imperial format (e.g., 5'8\")."""
        return f"{self.feet}'{self.remaining_inches}\""

    def __str__(self) -> str:
        rolls_str = ", ".join(map(str, self.rolls))
        return f"Height: {self.hands} hands ({self.imperial}) (Rolled: [{rolls_str}])"


# Height table: d6 value -> (hands, inches)
HEIGHT_TABLE = {
    1: (14, 56),   # 4'8"
    2: (15, 60),   # 5'0"
    3: (16, 64),   # 5'4"
    4: (17, 68),   # 5'8"
    5: (18, 72),   # 6'0"
    6: (19, 76),   # 6'4"
}


def roll_height() -> Height:
    """
    Roll for character height using a demon die.

    Uses the demon die mechanic:
    - Roll 1d6 for base height
    - 1: 14 hands (4'8"), subtract 4" per additional 1 rolled
    - 2-5: Use table directly
    - 6: 19 hands (6'4"), add 4" per additional 6 rolled

    Returns:
        Height object with rolls, hands, and inches
    """
    rolls, intensity = roll_demon_die()
    first_roll = rolls[0]

    if first_roll in [2, 3, 4, 5]:
        # Standard roll, use table directly
        hands, inches = HEIGHT_TABLE[first_roll]
    elif first_roll == 1:
        # Short: start at 14 hands (56"), subtract 4" per 1
        base_hands, base_inches = HEIGHT_TABLE[1]
        ones_count = abs(intensity)  # intensity is negative for 1s
        inches = base_inches - (4 * (ones_count - 1))  # -1 because first 1 is base
        hands = inches // 4
    else:  # first_roll == 6
        # Tall: start at 19 hands (76"), add 4" per 6
        base_hands, base_inches = HEIGHT_TABLE[6]
        sixes_count = intensity  # intensity is positive for 6s
        inches = base_inches + (4 * (sixes_count - 1))  # -1 because first 6 is base
        hands = inches // 4

    return Height(rolls=rolls, hands=hands, inches=inches)


@dataclass
class Weight:
    """Stores the result of a weight roll."""
    rolls: List[int]
    base_stones: int
    str_bonus_stones: float
    total_stones: float

    @property
    def total_pounds(self) -> int:
        """Get total weight in pounds."""
        return int(self.total_stones * 14)

    def __str__(self) -> str:
        rolls_str = ", ".join(map(str, self.rolls))
        return (f"Weight: {self.total_stones:.1f} stones ({self.total_pounds} lbs) "
                f"(Base: {self.base_stones}, STR bonus: {self.str_bonus_stones:.1f}) "
                f"(Rolled: [{rolls_str}])")


# Weight table: d6 value -> base stones
WEIGHT_TABLE = {
    1: 8,
    2: 9,
    3: 10,
    4: 11,
    5: 12,
    6: 13,
}


def roll_weight(strength: int) -> Weight:
    """
    Roll for character weight using a demon die.

    Formula: Base Weight + (STR / 2) stones

    Uses the demon die mechanic:
    - Roll 1d6 for base weight
    - 1: 8 stones, subtract 1 stone per additional 1 rolled
    - 2-5: Use table directly
    - 6: 13 stones, add 1 stone per additional 6 rolled

    Args:
        strength: Character's STR attribute value

    Returns:
        Weight object with rolls, base stones, STR bonus, and total
    """
    rolls, intensity = roll_demon_die()
    first_roll = rolls[0]

    if first_roll in [2, 3, 4, 5]:
        # Standard roll, use table directly
        base_stones = WEIGHT_TABLE[first_roll]
    elif first_roll == 1:
        # Light: start at 8 stones, subtract 1 per additional 1
        ones_count = abs(intensity)
        base_stones = WEIGHT_TABLE[1] - (ones_count - 1)
    else:  # first_roll == 6
        # Heavy: start at 13 stones, add 1 per additional 6
        sixes_count = intensity
        base_stones = WEIGHT_TABLE[6] + (sixes_count - 1)

    str_bonus = strength / 2
    total_stones = base_stones + str_bonus

    return Weight(
        rolls=rolls,
        base_stones=base_stones,
        str_bonus_stones=str_bonus,
        total_stones=total_stones
    )


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

    if main_roll <= 10:
        # Nobility
        social_class = "Nobility"
        sub_roll = roll_percentile()
        sub_class = get_nobility_rank(sub_roll)
    elif main_roll <= 30:
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
        craft_type=craft_type
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
        return (f"Literacy: {result} (Rolled {self.roll} vs INT {self.int_value}{diff_str} = {self.target})")


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
        is_literate=is_literate
    )


@dataclass
class Location:
    """Stores the result of a location roll."""
    roll: int
    location_type: str
    skills: List[str]
    skill_roll: Optional[int]  # For Village skill selection (1-2 = Street Smarts, 3-6 = Survival)
    attribute_modifiers: Dict[str, int]
    attribute_roll: Optional[int]  # For Village attribute selection (1=INT, 2=WIS, 3=STR, 4=DEX)
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
                skills_with_rolls = [f"{skill} ({roll})" for skill, roll in zip(self.skills, self.skill_rolls)]
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
                lines.append(f"  Attribute Modifier: {', '.join(mods)} (Rolled: {self.attribute_roll})")
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
    from main.helpers.dice import roll_die

    roll = roll_percentile()
    skill_roll = None
    attribute_roll = None
    skill_rolls = None

    if roll <= 20:
        # City
        location_type = "City"
        skills = ["Street Smarts"]
        attribute_modifiers = {"CON": -1, "INT": 1}
        literacy_check_modifier = 0

    elif roll <= 70:
        # Village
        location_type = "Village"
        # Random: Street Smarts OR Survival (d6: 1-3 = Street Smarts, 4-6 = Survival)
        skill_roll = roll_die(6)
        if skill_roll <= 3:
            skills = ["Street Smarts"]
        else:
            skills = ["Survival"]
        # Random: +1 to INT, WIS, STR, or DEX (d4: 1=INT, 2=WIS, 3=STR, 4=DEX)
        attribute_roll = roll_die(4)
        attr_options = ["INT", "WIS", "STR", "DEX"]
        bonus_attr = attr_options[attribute_roll - 1]
        attribute_modifiers = {bonus_attr: 1}
        literacy_check_modifier = 2

    elif roll <= 99:
        # Rural
        location_type = "Rural"
        # Pick 2 random survival skills using d5 (d6, reroll 6)
        skill_rolls = []
        selected_indices = []
        while len(selected_indices) < 2:
            skill_die = roll_die(6)
            while skill_die == 6:  # Reroll 6s for d5
                skill_die = roll_die(6)
            if skill_die - 1 not in selected_indices:  # Avoid duplicates
                selected_indices.append(skill_die - 1)
                skill_rolls.append(skill_die)
        skills = [SURVIVAL_SKILLS[i] for i in selected_indices]
        attribute_modifiers = {"STR": 1, "DEX": 1}
        literacy_check_modifier = 4

    else:
        # Special (100)
        location_type = "Special (Off-lander)"
        skills = []
        attribute_modifiers = {}
        literacy_check_modifier = 0

    return Location(
        roll=roll,
        location_type=location_type,
        skills=skills,
        skill_roll=skill_roll,
        attribute_modifiers=attribute_modifiers,
        attribute_roll=attribute_roll,
        skill_rolls=skill_rolls,
        literacy_check_modifier=literacy_check_modifier
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


# Wealth table: percentile range -> (wealth_level, base_coin)
WEALTH_TABLE = {
    (0, 15): ("Subsistence", 10),
    (16, 70): ("Moderate", 100),
    (71, 95): ("Merchant", 100),  # Plus additional percentile roll
    (96, 100): ("Rich", None),  # Consult DM
}


def get_wealth_level(roll: int) -> str:
    """
    Get wealth level from percentile roll.

    Args:
        roll: Percentile roll result (0-100, with 0 representing low roll)

    Returns:
        Wealth level string
    """
    if roll <= 15:
        return "Subsistence"
    elif roll <= 70:
        return "Moderate"
    elif roll <= 95:
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
        bonus_roll=bonus_roll
    )


# =============================================================================
# SKILL TRACKS
# =============================================================================

class TrackType(Enum):
    """Enumeration of available skill tracks."""
    ARMY = "Army"
    NAVY = "Navy"
    RANGER = "Ranger"
    OFFICER = "Officer"
    RANDOM = "Random"
    WORKER = "Worker"
    CRAFTS = "Crafts"
    MERCHANT = "Merchant"
    MAGIC = "Magic"


class CraftType(Enum):
    """Enumeration of craft specializations."""
    SMITH = "Smith"
    AGRICULTURE = "Agriculture"
    TAILOR = "Tailor"
    SCIENCE_MAPS = "Science (Maps/Logistics/Accounting)"
    SCIENCE_POTIONS = "Science (Potions/Medicine)"
    SCIENCE_PHYSICS = "Science (Physics/Engineering)"
    BUILDER_WAINWRIGHT = "Builder (Wainwright)"
    BUILDER_SHIPWRIGHT = "Builder (Shipwright)"
    BUILDER_MASON = "Builder (Mason)"
    BUILDER_STRUCTURES = "Builder (Structures)"
    MEDICAL = "Medical"
    MAGIC = "Magic"


# Track survivability values
TRACK_SURVIVABILITY = {
    TrackType.ARMY: 5,
    TrackType.NAVY: 5,
    TrackType.RANGER: 6,
    TrackType.OFFICER: 5,
    TrackType.RANDOM: None,  # Roll d8, reroll 5s
    TrackType.WORKER: 4,
    TrackType.CRAFTS: 3,
    TrackType.MERCHANT: 3,
    TrackType.MAGIC: None,  # Varies
}

# Initial skills by track (Year 1 only)
TRACK_INITIAL_SKILLS = {
    TrackType.ARMY: ["Sword +1 to hit", "Sword +1 parry"],
    TrackType.NAVY: ["Cutlass +1 to hit", "Cutlass +1 parry", "Swimming"],
    TrackType.RANGER: ["Weapon hit", "Weapon parry", "Tracking", "Wood lore", "Ken", "Literacy"],
    TrackType.OFFICER: ["Morale", "Ken", "Literacy", "Weapon hit", "Weapon parry"],
    TrackType.RANDOM: ["Random skill", "Swimming"],
    TrackType.WORKER: ["Laborer"],  # Additional Laborer if poor/working class
    TrackType.CRAFTS: ["Laborer", "Literacy"],  # Plus craft type
    TrackType.MERCHANT: ["Coins", "Literacy"],
    TrackType.MAGIC: [],  # See Magic spell tables
}


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
            return (f"{self.track.value}: {'Accepted' if self.accepted else 'Rejected'} "
                    f"(Rolled {self.roll} + {mod_str} vs {self.target}+) - {self.reason}")
        return f"{self.track.value}: {'Accepted' if self.accepted else 'Rejected'} - {self.reason}"


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

    def __str__(self) -> str:
        lines = [f"Skill Track: {self.track.value}"]
        if self.survivability_roll is not None:
            lines.append(f"  Survivability: {self.survivability} (Rolled: {self.survivability_roll})")
        else:
            lines.append(f"  Survivability: {self.survivability}")

        if self.craft_type:
            rolls_str = ", ".join(map(str, self.craft_rolls)) if self.craft_rolls else ""
            lines.append(f"  Craft: {self.craft_type.value} (Rolled: [{rolls_str}])")

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


def check_army_acceptance(str_mod: int, dex_mod: int) -> AcceptanceCheck:
    """
    Check if character meets Army track requirements.
    Requirement: 8+ on 2d6 + STR/DEX modifiers
    """
    roll = sum(roll_dice(2, 6))
    total = roll + str_mod + dex_mod
    target = 8
    accepted = total >= target

    return AcceptanceCheck(
        track=TrackType.ARMY,
        accepted=accepted,
        roll=roll,
        target=target,
        modifiers={"STR": str_mod, "DEX": dex_mod},
        reason=f"Total {total} {'≥' if accepted else '<'} {target}"
    )


def check_navy_acceptance(str_mod: int, dex_mod: int, int_mod: int) -> AcceptanceCheck:
    """
    Check if character meets Navy track requirements.
    Requirement: 8+ on 2d6 + STR/DEX/INT modifiers
    """
    roll = sum(roll_dice(2, 6))
    total = roll + str_mod + dex_mod + int_mod
    target = 8
    accepted = total >= target

    return AcceptanceCheck(
        track=TrackType.NAVY,
        accepted=accepted,
        roll=roll,
        target=target,
        modifiers={"STR": str_mod, "DEX": dex_mod, "INT": int_mod},
        reason=f"Total {total} {'≥' if accepted else '<'} {target}"
    )


def check_ranger_acceptance(str_mod: int, dex_mod: int, int_mod: int, wis_mod: int) -> AcceptanceCheck:
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
        reason="; ".join(reason_parts)
    )


def check_officer_acceptance(is_rich: bool, is_promoted: bool = False) -> AcceptanceCheck:
    """
    Check if character meets Officer track requirements.
    Requirement: Must be promoted OR be Rich
    """
    accepted = is_rich or is_promoted

    if is_promoted:
        reason = "Promoted to Officer"
    elif is_rich:
        reason = "Rich wealth level"
    else:
        reason = "Not promoted and not Rich"

    return AcceptanceCheck(
        track=TrackType.OFFICER,
        accepted=accepted,
        roll=None,
        target=None,
        modifiers={},
        reason=reason
    )


def check_merchant_acceptance(social_class: str, wealth_level: str) -> AcceptanceCheck:
    """
    Check if character meets Merchant track requirements.
    Requirements based on social standing:
    - 10+ on 2d6 if poor (Subsistence)
    - 8+ on 2d6 if working class (Moderate + Commoner/Laborer)
    - 6+ on 2d6 if above working class
    """
    roll = sum(roll_dice(2, 6))

    # Determine target based on social standing
    is_poor = wealth_level == "Subsistence"
    is_working_class = (wealth_level == "Moderate" and
                       social_class in ["Commoner", "Laborer"])

    if is_poor:
        target = 10
        class_desc = "poor"
    elif is_working_class:
        target = 8
        class_desc = "working class"
    else:
        target = 6
        class_desc = "above working class"

    accepted = roll >= target

    return AcceptanceCheck(
        track=TrackType.MERCHANT,
        accepted=accepted,
        roll=roll,
        target=target,
        modifiers={},
        reason=f"Roll {roll} {'≥' if accepted else '<'} {target} ({class_desc})"
    )


def get_eligible_tracks(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    wealth_level: str,
    is_promoted: bool = False
) -> List[Tuple[TrackType, AcceptanceCheck]]:
    """
    Determine which tracks a character is eligible for.

    Returns:
        List of tuples (TrackType, AcceptanceCheck) for eligible tracks
    """
    eligible = []

    # Always eligible tracks
    eligible.append((TrackType.RANDOM, AcceptanceCheck(
        track=TrackType.RANDOM, accepted=True, roll=None, target=None,
        modifiers={}, reason="No requirements"
    )))
    eligible.append((TrackType.WORKER, AcceptanceCheck(
        track=TrackType.WORKER, accepted=True, roll=None, target=None,
        modifiers={}, reason="No requirements"
    )))
    eligible.append((TrackType.CRAFTS, AcceptanceCheck(
        track=TrackType.CRAFTS, accepted=True, roll=None, target=None,
        modifiers={}, reason="No requirements"
    )))

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

    is_rich = wealth_level == "Rich"
    officer_check = check_officer_acceptance(is_rich, is_promoted)
    if officer_check.accepted:
        eligible.append((TrackType.OFFICER, officer_check))

    merchant_check = check_merchant_acceptance(social_class, wealth_level)
    if merchant_check.accepted:
        eligible.append((TrackType.MERCHANT, merchant_check))

    # Magic track - placeholder, requires separate magic system
    # eligible.append((TrackType.MAGIC, ...))

    return eligible


def select_optimal_track(
    str_mod: int,
    dex_mod: int,
    int_mod: int,
    wis_mod: int,
    social_class: str,
    wealth_level: str,
    sub_class: str,
    is_promoted: bool = False
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
        str_mod, dex_mod, int_mod, wis_mod,
        social_class, wealth_level, is_promoted
    )

    eligible_types = {t for t, _ in eligible}

    # Priority selection
    is_rich = wealth_level == "Rich"

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
        if social_class == "Merchant" or is_rich:
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
    optimize: bool = True
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
            str_mod, dex_mod, int_mod, wis_mod,
            social_class, wealth_level, sub_class, is_promoted
        )
    else:
        eligible = get_eligible_tracks(
            str_mod, dex_mod, int_mod, wis_mod,
            social_class, wealth_level, is_promoted
        )
        track, acceptance_check = random.choice(eligible)

    # Determine survivability
    survivability_roll = None
    if track == TrackType.RANDOM:
        survivability, survivability_roll = roll_survivability_random()
    else:
        survivability = TRACK_SURVIVABILITY.get(track, 5)
        if survivability is None:
            survivability = 5  # Default for Magic or unknown

    # Get initial skills
    initial_skills = list(TRACK_INITIAL_SKILLS.get(track, []))

    # Handle special cases
    craft_type = None
    craft_rolls = None

    if track == TrackType.WORKER:
        # Additional Laborer if poor/working class
        if wealth_level == "Subsistence" or sub_class == "Laborer":
            initial_skills.append("Laborer (bonus)")

    elif track == TrackType.CRAFTS:
        # Roll for craft type
        craft_type, craft_rolls = roll_craft_type()
        initial_skills.append(f"Craft: {craft_type.value}")

    return SkillTrack(
        track=track,
        acceptance_check=acceptance_check,
        survivability=survivability,
        survivability_roll=survivability_roll,
        initial_skills=initial_skills,
        craft_type=craft_type,
        craft_rolls=craft_rolls
    )


# =============================================================================
# PRIOR EXPERIENCE (Years 16-34)
# =============================================================================

# Skill tables by track - skills gained each year (roll d6 or use year index)
# These are representative skills; actual tables may vary
TRACK_YEARLY_SKILLS = {
    TrackType.ARMY: [
        "Sword +1 to hit", "Sword +1 parry", "Shield", "Tactics",
        "Formation Fighting", "Polearm", "Archery", "Riding",
        "Survival", "First Aid", "Intimidation", "Leadership"
    ],
    TrackType.NAVY: [
        "Cutlass +1 to hit", "Cutlass +1 parry", "Swimming", "Sailing",
        "Navigation", "Rope Use", "Climbing", "Weather Sense",
        "Ship Knowledge", "Trading", "Leadership"
    ],
    TrackType.RANGER: [
        "Weapon hit", "Weapon parry", "Tracking", "Wood Lore",
        "Survival", "Herb Lore", "Stealth", "Archery",
        "Animal Handling", "Camouflage", "Trapping", "Ken"
    ],
    TrackType.OFFICER: [
        "Morale", "Ken", "Tactics", "Leadership",
        "Weapon hit", "Weapon parry", "Riding", "Etiquette",
        "Strategy", "Logistics", "Diplomacy", "Command"
    ],
    TrackType.RANDOM: [
        "Random Skill", "Swimming", "Gambling", "Streetwise",
        "Brawling", "Running", "Climbing", "Persuasion",
        "Observation", "Luck", "Contacts", "Survival"
    ],
    TrackType.WORKER: [
        "Laborer", "Strength Training", "Endurance", "Hauling",
        "Tool Use", "Construction", "Mining", "Farming",
        "Animal Handling", "Repair", "Teamwork", "Fortitude"
    ],
    TrackType.CRAFTS: [
        "Craft Skill", "Literacy", "Mathematics", "Drafting",
        "Apprentice Work", "Journeyman Work", "Master Technique", "Teaching",
        "Business", "Negotiation", "Quality Control", "Innovation"
    ],
    TrackType.MERCHANT: [
        "Coins", "Literacy", "Negotiation", "Appraisal",
        "Bookkeeping", "Contacts", "Trading", "Languages",
        "Law", "Contracts", "Investment", "Management"
    ],
    TrackType.MAGIC: [
        "Spell", "Ritual", "Magical Theory", "Concentration",
        "Meditation", "Arcane Lore", "Spell", "Component Knowledge",
        "Enchanting", "Warding", "Spell", "Mastery"
    ],
}


@dataclass
class YearResult:
    """Result of a single year of prior experience."""
    year: int  # Age (16-34)
    track: TrackType
    skill_gained: str
    skill_roll: int
    skill_points: int  # Always 1
    survivability_target: int
    survivability_roll: int
    survived: bool

    def __str__(self) -> str:
        status = "Survived" if self.survived else "DIED"
        return (f"Year {self.year}: {self.skill_gained} (+1 SP) | "
                f"Survival: {self.survivability_roll} vs {self.survivability_target}+ [{status}]")


@dataclass
class PriorExperience:
    """Complete prior experience record for a character."""
    starting_age: int  # Always 16
    final_age: int  # Age at end (or death)
    years_served: int
    track: TrackType
    yearly_results: List[YearResult]
    total_skill_points: int
    all_skills: List[str]
    died: bool
    death_year: Optional[int]

    def __str__(self) -> str:
        lines = [
            f"\n{'='*60}",
            f"PRIOR EXPERIENCE ({self.track.value} Track)",
            f"{'='*60}",
            f"Starting Age: {self.starting_age}",
        ]

        if self.died:
            lines.append(f"DIED at age {self.death_year}!")
            lines.append(f"Years Served: {self.years_served}")
        else:
            lines.append(f"Final Age: {self.final_age}")
            lines.append(f"Years Served: {self.years_served}")

        lines.append(f"\nYear-by-Year Progression:")
        lines.append("-" * 60)

        for result in self.yearly_results:
            lines.append(str(result))

        lines.append("-" * 60)
        lines.append(f"\nTOTAL SKILL POINTS: {self.total_skill_points}")
        lines.append(f"SKILLS GAINED ({len(self.all_skills)}):")

        # Group and count skills
        skill_counts: Dict[str, int] = {}
        for skill in self.all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        for skill, count in sorted(skill_counts.items()):
            if count > 1:
                lines.append(f"  - {skill} x{count}")
            else:
                lines.append(f"  - {skill}")

        return "\n".join(lines)


def roll_yearly_skill(track: TrackType, year_index: int) -> Tuple[str, int]:
    """
    Roll for a skill from the track's skill table.

    Args:
        track: The character's skill track
        year_index: Which year of service (0-based)

    Returns:
        Tuple of (skill name, roll used)
    """
    skill_table = TRACK_YEARLY_SKILLS.get(track, TRACK_YEARLY_SKILLS[TrackType.RANDOM])

    # Roll d12 (or use modulo for year progression variety)
    roll = roll_die(12)
    skill_index = (roll - 1) % len(skill_table)
    skill = skill_table[skill_index]

    return skill, roll


def roll_survivability_check(survivability: int) -> Tuple[int, bool]:
    """
    Roll a survivability check (2d6 >= survivability target).

    Args:
        survivability: Target number to meet or exceed

    Returns:
        Tuple of (roll result, survived boolean)
    """
    roll = sum(roll_dice(2, 6))
    survived = roll >= survivability
    return roll, survived


def roll_prior_experience(
    skill_track: SkillTrack,
    min_years: int = 0,
    max_years: int = 18
) -> PriorExperience:
    """
    Generate prior experience for a character.

    Characters can have 0-18 years of prior experience (ages 16-34).
    Each year they gain:
    - 1 skill point
    - 1 skill from their track's skill table
    - Must pass a survivability roll or die

    Args:
        skill_track: The character's chosen skill track
        min_years: Minimum years of service (default 0)
        max_years: Maximum years of service (default 18, for age 34)

    Returns:
        PriorExperience object with complete record
    """
    starting_age = 16
    track = skill_track.track
    survivability = skill_track.survivability

    # Randomly determine how many years the character attempts
    target_years = random.randint(min_years, max_years)

    yearly_results = []
    all_skills = []
    total_skill_points = 0
    died = False
    death_year = None
    years_served = 0

    # Add initial skills from track (Year 1 skills)
    all_skills.extend(skill_track.initial_skills)

    for year_index in range(target_years):
        current_age = starting_age + year_index
        years_served = year_index + 1

        # Gain skill
        skill, skill_roll = roll_yearly_skill(track, year_index)
        all_skills.append(skill)

        # Gain skill point
        total_skill_points += 1

        # Survivability check
        surv_roll, survived = roll_survivability_check(survivability)

        year_result = YearResult(
            year=current_age,
            track=track,
            skill_gained=skill,
            skill_roll=skill_roll,
            skill_points=1,
            survivability_target=survivability,
            survivability_roll=surv_roll,
            survived=survived
        )
        yearly_results.append(year_result)

        if not survived:
            died = True
            death_year = current_age
            break

    final_age = starting_age + years_served if not died else death_year

    return PriorExperience(
        starting_age=starting_age,
        final_age=final_age,
        years_served=years_served,
        track=track,
        yearly_results=yearly_results,
        total_skill_points=total_skill_points,
        all_skills=all_skills,
        died=died,
        death_year=death_year
    )
