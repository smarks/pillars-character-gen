"""
Core character attribute generation for Pillars RPG.

This module handles the generation of character attributes using
various methods (dice rolling or point allocation).
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from pillars.dice import (
    roll_dice,
    roll_with_drop_lowest,
    roll_die,
)
from pillars.config import (
    ATTRIBUTE_MIN,
    ATTRIBUTE_MAX,
    MODIFIER_FLOOR,
    MODIFIER_CEILING,
    POINT_BUY_DEFAULT,
)


__all__ = [
    # Constants
    "CORE_ATTRIBUTES",
    "ATTRIBUTE_MODIFIERS",
    "AGING_EFFECTS",
    # Classes
    "AgingEffects",
    "AttributeRoll",
    "CharacterAttributes",
    # Functions
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
]


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
            f"  Rolled: [{all_rolls_display}] -> Kept: [{kept_rolls_display}]"
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
                    f"- {attr}: {value:2d} ({mod_str})  [rolled {all_str} -> kept {kept_str}]"
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
