"""
Character attribute generation for Pillars RPG.

This module handles the generation of character attributes using
various methods (dice rolling or point allocation).
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import random
from pillars.dice import (
    roll_dice,
    roll_with_drop_lowest,
    roll_demon_die,
    roll_percentile,
    roll_die,
)
from pillars.enums import TrackType, CraftType, MagicSchool
from pillars.constants import (
    MAGIC_SPELL_PROGRESSION,
    SPELL_SKILL_MASTERY,
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
    TRACK_YEARLY_SKILLS,
)
from pillars.config import (
    ATTRIBUTE_MIN,
    ATTRIBUTE_MAX,
    MODIFIER_FLOOR,
    MODIFIER_CEILING,
    POINT_BUY_DEFAULT,
    ARMY_ACCEPTANCE_TARGET,
    NAVY_ACCEPTANCE_TARGET,
    MERCHANT_ACCEPTANCE_TARGETS,
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
    HEIGHT_INCREMENT_INCHES,
    MAGIC_COMMON_THRESHOLD,
)


# Attribute names
CORE_ATTRIBUTES = ["STR", "DEX", "INT", "WIS", "CON", "CHR"]

# Attribute modifier table
ATTRIBUTE_MODIFIERS = {
    3: -5,
    4: -4,
    5: -3,
    6: -2,
    7: -1,
    8: 0,
    9: 0,
    10: 0,
    11: 0,
    12: 0,
    13: 0,
    14: 1,
    15: 2,
    16: 3,
    17: 4,
    18: 5,
}

# Aging effects table: years of experience -> cumulative attribute penalties
# Format: {years: {"STR": penalty, "DEX": penalty, "INT": penalty, "WIS": penalty, "CON": penalty}}
# Note: These are cumulative penalties applied at each threshold
AGING_EFFECTS = {
    # 0-18 years (age 16-34): No penalties
    19: {"STR": -1, "DEX": -1, "INT": 0, "WIS": 0, "CON": 0},  # Age 35-38 (term 5)
    23: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": -1},  # Age 39-42 (term 6)
    27: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0},  # Age 43-46 (term 7)
    31: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0},  # Age 47-50 (term 8)
    35: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0},  # Age 51-54 (term 9)
    39: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0},  # Age 55-58 (term 10)
    43: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0},  # Age 59-62 (term 11)
    47: {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0},  # Age 63-66 (term 12)
    51: {"STR": -1, "DEX": -1, "INT": -1, "WIS": -1, "CON": -1},  # Age 67-70 (term 13)
}


@dataclass
class AgingEffects:
    """Stores cumulative aging penalties for a character."""

    str_penalty: int = 0
    dex_penalty: int = 0
    int_penalty: int = 0
    wis_penalty: int = 0
    con_penalty: int = 0

    def total_penalties(self) -> Dict[str, int]:
        """Return all penalties as a dictionary."""
        return {
            "STR": self.str_penalty,
            "DEX": self.dex_penalty,
            "INT": self.int_penalty,
            "WIS": self.wis_penalty,
            "CON": self.con_penalty,
            "CHR": 0,  # CHR is not affected by aging
        }

    def apply_year(self, years_of_experience: int) -> Dict[str, int]:
        """
        Apply aging effects for reaching a new year of experience.
        Returns any new penalties applied this year.
        """
        new_penalties = {"STR": 0, "DEX": 0, "INT": 0, "WIS": 0, "CON": 0}

        if years_of_experience in AGING_EFFECTS:
            effects = AGING_EFFECTS[years_of_experience]
            self.str_penalty += effects["STR"]
            self.dex_penalty += effects["DEX"]
            self.int_penalty += effects["INT"]
            self.wis_penalty += effects["WIS"]
            self.con_penalty += effects["CON"]
            new_penalties = effects.copy()

        return new_penalties

    def __str__(self) -> str:
        penalties = []
        if self.str_penalty:
            penalties.append(f"STR {self.str_penalty:+d}")
        if self.dex_penalty:
            penalties.append(f"DEX {self.dex_penalty:+d}")
        if self.int_penalty:
            penalties.append(f"INT {self.int_penalty:+d}")
        if self.wis_penalty:
            penalties.append(f"WIS {self.wis_penalty:+d}")
        if self.con_penalty:
            penalties.append(f"CON {self.con_penalty:+d}")

        if penalties:
            return f"Aging Penalties: {', '.join(penalties)}"
        return "Aging Penalties: None"


def get_aging_effects_for_age(age: int) -> AgingEffects:
    """
    Calculate cumulative aging effects for a given age.

    Args:
        age: Character's current age

    Returns:
        AgingEffects object with all cumulative penalties
    """
    years_of_experience = age - 16  # Starting age is 16
    effects = AgingEffects()

    for threshold in sorted(AGING_EFFECTS.keys()):
        if years_of_experience >= threshold:
            effects.apply_year(threshold)

    return effects


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
        all_rolls_display = ", ".join(map(str, self.all_rolls))
        kept_rolls_display = ", ".join(map(str, self.kept_rolls))
        modifier_display = (
            f"+{self.modifier}" if self.modifier >= 0 else str(self.modifier)
        )
        return (
            f"{self.attribute_name}: {self.value} (modifier: {modifier_display})\n"
            f"  Rolled: [{all_rolls_display}] → Kept: [{kept_rolls_display}]"
        )


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
    # Derived stats - calculated from core attributes
    fatigue_points: int = 0
    body_points: int = 0
    fatigue_roll: int = 0  # The 1d6 roll for fatigue
    body_roll: int = 0  # The 1d6 roll for body

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

    def get_total_modifier(self) -> int:
        """Get the sum of all attribute modifiers."""
        return sum(self.get_all_modifiers().values())

    def get_attribute_scores_dict(self) -> Dict[str, int]:
        """Get all attribute scores as a dictionary."""
        return {attr: getattr(self, attr) for attr in CORE_ATTRIBUTES}

    def __str__(self) -> str:
        """Format attributes for display."""
        lines = [f"**Attributes** ({self.generation_method})"]

        # Build a dict of roll details for quick lookup
        roll_by_attr = {r.attribute_name: r for r in self.roll_details}

        for attr in CORE_ATTRIBUTES:
            value = getattr(self, attr)
            modifier = self.get_modifier(attr)
            mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)

            # Include dice rolls if available
            if attr in roll_by_attr:
                roll = roll_by_attr[attr]
                all_str = ",".join(map(str, roll.all_rolls))
                kept_str = ",".join(map(str, roll.kept_rolls))
                lines.append(
                    f"- {attr}: {value:2d} ({mod_str})  [rolled {all_str} → kept {kept_str}]"
                )
            else:
                lines.append(f"- {attr}: {value:2d} ({mod_str})")

        # Add derived stats with calculation breakdown
        higher_phys = max(self.STR, self.DEX)
        higher_phys_name = "STR" if self.STR >= self.DEX else "DEX"
        int_mod = self.get_modifier("INT")
        wis_mod = self.get_modifier("WIS")
        int_mod_str = f"{int_mod:+d}" if int_mod != 0 else ""
        wis_mod_str = f"{wis_mod:+d}" if wis_mod != 0 else ""
        mod_str = (
            f"{int_mod_str}{wis_mod_str}" if (int_mod != 0 or wis_mod != 0) else ""
        )

        # Fatigue: CON + WIS + max(STR,DEX) + 1d6 + INT/WIS mods
        fatigue_calc = (
            f"{self.CON}+{self.WIS}+{higher_phys}+{self.fatigue_roll}{mod_str}"
        )
        lines.append(
            f"- Fatigue Points: {self.fatigue_points}  (CON+WIS+{higher_phys_name}+1d6 = {fatigue_calc})"
        )

        # Body: CON + max(STR,DEX) + 1d6 + INT/WIS mods
        body_calc = f"{self.CON}+{higher_phys}+{self.body_roll}{mod_str}"
        lines.append(
            f"- Body Points: {self.body_points}  (CON+{higher_phys_name}+1d6 = {body_calc})"
        )

        return "\n".join(lines)


def format_total_modifier(modifiers: Dict[str, int]) -> str:
    """
    Format total modifier as a string with sign.

    Args:
        modifiers: Dictionary of attribute modifiers

    Returns:
        Formatted string like "+5" or "-2"
    """
    total = sum(modifiers.values())
    return f"+{total}" if total >= 0 else str(total)


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
    if value < ATTRIBUTE_MIN:
        return MODIFIER_FLOOR
    elif value > ATTRIBUTE_MAX:
        # Extend the pattern: each point above max adds +1
        return MODIFIER_CEILING + (value - ATTRIBUTE_MAX)
    else:
        # Should not happen with standard table
        return 0


def calculate_fatigue_points(
    con: int, wis: int, str_val: int, dex: int, int_mod: int, wis_mod: int, roll: int
) -> int:
    """
    Calculate Fatigue Points for a character.

    Formula: CON + WIS + max(STR, DEX) + 1d6 + INT modifier + WIS modifier

    Args:
        con: Constitution score
        wis: Wisdom score
        str_val: Strength score
        dex: Dexterity score
        int_mod: Intelligence modifier
        wis_mod: Wisdom modifier
        roll: The 1d6 roll result

    Returns:
        Total fatigue points
    """
    higher_physical = max(str_val, dex)
    return con + wis + higher_physical + roll + int_mod + wis_mod


def calculate_body_points(
    con: int, str_val: int, dex: int, int_mod: int, wis_mod: int, roll: int
) -> int:
    """
    Calculate Body Points for a character.

    Formula: CON + max(STR, DEX) + 1d6 + INT modifier + WIS modifier

    Args:
        con: Constitution score
        str_val: Strength score
        dex: Dexterity score
        int_mod: Intelligence modifier
        wis_mod: Wisdom modifier
        roll: The 1d6 roll result

    Returns:
        Total body points
    """
    higher_physical = max(str_val, dex)
    return con + higher_physical + roll + int_mod + wis_mod


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
            modifier=get_attribute_modifier(total),
        )
        roll_details.append(roll_detail)

    return CharacterAttributes(
        **attributes, generation_method="3d6", roll_details=roll_details
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
            modifier=get_attribute_modifier(total),
        )
        roll_details.append(roll_detail)

    # Calculate derived stats
    int_mod = get_attribute_modifier(attributes["INT"])
    wis_mod = get_attribute_modifier(attributes["WIS"])

    # Roll 1d6 for fatigue and body points
    fatigue_roll = roll_die(6)
    body_roll = roll_die(6)

    fatigue_points = calculate_fatigue_points(
        con=attributes["CON"],
        wis=attributes["WIS"],
        str_val=attributes["STR"],
        dex=attributes["DEX"],
        int_mod=int_mod,
        wis_mod=wis_mod,
        roll=fatigue_roll,
    )

    body_points = calculate_body_points(
        con=attributes["CON"],
        str_val=attributes["STR"],
        dex=attributes["DEX"],
        int_mod=int_mod,
        wis_mod=wis_mod,
        roll=body_roll,
    )

    return CharacterAttributes(
        **attributes,
        generation_method="4d6 drop lowest",
        roll_details=roll_details,
        fatigue_points=fatigue_points,
        body_points=body_points,
        fatigue_roll=fatigue_roll,
        body_roll=body_roll,
    )


def generate_attributes_point_buy(
    points: int = POINT_BUY_DEFAULT,
) -> CharacterAttributes:
    """
    Create attributes using point buy system.

    Note: This returns a template with all attributes set to minimum.
    The actual allocation should be done interactively or via input.

    Args:
        points: Total points to allocate (default: POINT_BUY_DEFAULT)

    Returns:
        CharacterAttributes object with placeholder values
    """
    # For point buy, we start with a base template
    # This would need interactive input to complete
    attributes = {attr: ATTRIBUTE_MIN for attr in CORE_ATTRIBUTES}

    return CharacterAttributes(
        **attributes, generation_method=f"Point Buy ({points} points)", roll_details=[]
    )


def validate_point_buy(
    attributes: Dict[str, int], total_points: int = POINT_BUY_DEFAULT
) -> Tuple[bool, str]:
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

    # Check values are reasonable
    for attr, value in attributes.items():
        if value < ATTRIBUTE_MIN:
            return False, f"{attr} value ({value}) is below minimum ({ATTRIBUTE_MIN})"
        if value > ATTRIBUTE_MAX:
            return False, f"{attr} value ({value}) exceeds maximum ({ATTRIBUTE_MAX})"

    # Check total points
    total_used = sum(attributes.values())
    if total_used != total_points:
        return (
            False,
            f"Total points ({total_used}) does not equal allowed points ({total_points})",
        )

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

    return Appearance(rolls=rolls, intensity=intensity, description=description)


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
    1: (14, 56),  # 4'8"
    2: (15, 60),  # 5'0"
    3: (16, 64),  # 5'4"
    4: (17, 68),  # 5'8"
    5: (18, 72),  # 6'0"
    6: (19, 76),  # 6'4"
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
        # Short: start at 14 hands (56"), subtract HEIGHT_INCREMENT_INCHES per 1
        base_hands, base_inches = HEIGHT_TABLE[1]
        ones_count = abs(intensity)  # intensity is negative for 1s
        inches = base_inches - (HEIGHT_INCREMENT_INCHES * (ones_count - 1))
        hands = inches // HEIGHT_INCREMENT_INCHES
    else:  # first_roll == 6
        # Tall: start at 19 hands (76"), add HEIGHT_INCREMENT_INCHES per 6
        base_hands, base_inches = HEIGHT_TABLE[6]
        sixes_count = intensity  # intensity is positive for 6s
        inches = base_inches + (HEIGHT_INCREMENT_INCHES * (sixes_count - 1))
        hands = inches // HEIGHT_INCREMENT_INCHES

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
        return (
            f"Weight: {self.total_stones:.1f} stones ({self.total_pounds} lbs) "
            f"(Base: {self.base_stones}, STR bonus: {self.str_bonus_stones:.1f}) "
            f"(Rolled: [{rolls_str}])"
        )


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
        total_stones=total_stones,
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


# =============================================================================
# SKILL TRACKS
# =============================================================================


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
    magic_school: Optional["MagicSchool"] = None  # For Magic track
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
        requirement_desc=f"2d6 + STR({str_mod:+d}) + DEX({dex_mod:+d}) ≥ 8",
    )

    # Navy: 8+ on 2d6 + STR + DEX + INT
    total_mod = str_mod + dex_mod + int_mod
    availability[TrackType.NAVY] = calculate_roll_availability(
        min_roll=2,
        max_roll=12,
        total_modifier=total_mod,
        target=8,
        requirement_desc=f"2d6 + STR({str_mod:+d}) + DEX({dex_mod:+d}) + INT({int_mod:+d}) ≥ 8",
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
        requirement_desc=f"2d6 ≥ {target} ({class_desc})",
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


# =============================================================================
# PRIOR EXPERIENCE (Years 16-34)
# =============================================================================

# TRACK_YEARLY_SKILLS is now imported from constants.py above


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
) -> YearResult:
    """
    Roll a single year of prior experience.

    Args:
        skill_track: The character's chosen skill track
        year_index: Which year of service (0-based)
        total_modifier: Sum of all attribute modifiers (before aging)
        aging_effects: Current aging effects (will be updated if crossing threshold)

    Returns:
        YearResult for this year
    """
    starting_age = 16
    current_age = starting_age + year_index
    years_of_experience = year_index + 1
    track = skill_track.track
    survivability = skill_track.survivability

    # Check for aging effects this year
    aging_this_year = aging_effects.apply_year(years_of_experience)
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
