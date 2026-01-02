"""
Physical attribute generation for Pillars RPG.

This module handles the generation of physical characteristics
including appearance, height, and weight.
"""

from typing import List, Tuple
from dataclasses import dataclass
from pillars.dice import roll_demon_die
from pillars.config import HEIGHT_INCREMENT_INCHES


__all__ = [
    # Classes
    "Appearance",
    "Height",
    "Weight",
    # Constants
    "HEIGHT_TABLE",
    "WEIGHT_TABLE",
    # Functions
    "get_appearance_description",
    "roll_appearance",
    "roll_height",
    "roll_weight",
]


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
        """Get height in imperial format (e.g., 5'8")."""
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
