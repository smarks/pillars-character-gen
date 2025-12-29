"""
Dice rolling utilities for Pillars character generation.

This module provides generalized, reusable dice rolling functions
for character creation and gameplay.
"""

import random
from typing import List, Tuple


def roll_die(sides: int) -> int:
    """
    Roll a single die with the specified number of sides.

    Args:
        sides: Number of sides on the die (e.g., 6 for d6, 20 for d20)

    Returns:
        Random integer between 1 and sides (inclusive)

    Raises:
        ValueError: If sides is less than 1

    Examples:
        >>> random.seed(42)
        >>> roll_die(6)
        2
        >>> roll_die(20)
        18
    """
    if sides < 1:
        raise ValueError("Die must have at least 1 side")
    return random.randint(1, sides)


def roll_dice(num_dice: int, sides: int) -> List[int]:
    """
    Roll multiple dice with the specified number of sides.

    Args:
        num_dice: Number of dice to roll
        sides: Number of sides on each die

    Returns:
        List of integers representing each die roll

    Raises:
        ValueError: If num_dice or sides is less than 1

    Examples:
        >>> random.seed(42)
        >>> roll_dice(3, 6)
        [2, 6, 2]
        >>> roll_dice(4, 6)
        [2, 6, 2, 4]
    """
    if num_dice < 1:
        raise ValueError("Must roll at least 1 die")
    if sides < 1:
        raise ValueError("Die must have at least 1 side")

    return [roll_die(sides) for _ in range(num_dice)]


def roll_and_sum(num_dice: int, sides: int) -> Tuple[List[int], int]:
    """
    Roll multiple dice and return both individual rolls and their sum.

    Args:
        num_dice: Number of dice to roll
        sides: Number of sides on each die

    Returns:
        Tuple of (list of individual rolls, sum of all rolls)

    Examples:
        >>> random.seed(42)
        >>> roll_and_sum(3, 6)
        ([2, 6, 2], 10)
    """
    rolls = roll_dice(num_dice, sides)
    return rolls, sum(rolls)


def roll_with_drop_lowest(
    num_dice: int, sides: int, num_drop: int = 1
) -> Tuple[List[int], List[int], int]:
    """
    Roll multiple dice and drop the lowest rolls.

    Common for RPG character generation (e.g., 4d6 drop lowest).

    Args:
        num_dice: Number of dice to roll
        sides: Number of sides on each die
        num_drop: Number of lowest dice to drop (default: 1)

    Returns:
        Tuple of (all rolls, kept rolls, sum of kept rolls)

    Raises:
        ValueError: If num_drop >= num_dice

    Examples:
        >>> random.seed(42)
        >>> roll_with_drop_lowest(4, 6, 1)
        ([2, 6, 2, 4], [2, 6, 4], 12)
    """
    if num_drop >= num_dice:
        raise ValueError(f"Cannot drop {num_drop} dice when only rolling {num_dice}")
    if num_drop < 0:
        raise ValueError("Cannot drop negative number of dice")

    all_rolls = roll_dice(num_dice, sides)
    sorted_rolls = sorted(all_rolls, reverse=True)
    kept_rolls = sorted_rolls[:-num_drop] if num_drop > 0 else sorted_rolls

    return all_rolls, kept_rolls, sum(kept_rolls)


def roll_with_drop_highest(
    num_dice: int, sides: int, num_drop: int = 1
) -> Tuple[List[int], List[int], int]:
    """
    Roll multiple dice and drop the highest rolls.

    Less common but useful for certain game mechanics.

    Args:
        num_dice: Number of dice to roll
        sides: Number of sides on each die
        num_drop: Number of highest dice to drop (default: 1)

    Returns:
        Tuple of (all rolls, kept rolls, sum of kept rolls)

    Raises:
        ValueError: If num_drop >= num_dice

    Examples:
        >>> random.seed(42)
        >>> roll_with_drop_highest(4, 6, 1)
        ([2, 6, 2, 4], [2, 2, 4], 8)
    """
    if num_drop >= num_dice:
        raise ValueError(f"Cannot drop {num_drop} dice when only rolling {num_dice}")
    if num_drop < 0:
        raise ValueError("Cannot drop negative number of dice")

    all_rolls = roll_dice(num_dice, sides)
    sorted_rolls = sorted(all_rolls)
    kept_rolls = sorted_rolls[:-num_drop] if num_drop > 0 else sorted_rolls

    return all_rolls, kept_rolls, sum(kept_rolls)


def roll_percentile() -> int:
    """
    Roll percentile dice (d100).

    Returns:
        Random integer between 1 and 100 (inclusive)

    Examples:
        >>> random.seed(42)
        >>> roll_percentile()
        82
    """
    return roll_die(100)


def roll_demon_die() -> Tuple[List[int], int]:
    """
    Roll a demon die (d6 with exploding 1s and 6s).

    A demon die works as follows:
    - Roll 1d6
    - If a 1 is rolled, roll again (only continuing on 1s)
    - If a 6 is rolled, roll again (only continuing on 6s)
    - Stop when a non-1 (if started with 1) or non-6 (if started with 6) is rolled

    Returns:
        Tuple of (list of all rolls, final value based on first roll direction)
        Final value is negative count for 1s, positive count for 6s, 0 for 2-5

    Examples:
        [1, 1, 3] -> rolls, -2 (two 1s = very pretty direction)
        [6, 6, 6, 2] -> rolls, 3 (three 6s = very ugly direction)
        [4] -> rolls, 0 (average, no explosion)
    """
    rolls = []
    first_roll = roll_die(6)
    rolls.append(first_roll)

    if first_roll == 1:
        # Keep rolling while we get 1s
        while rolls[-1] == 1:
            next_roll = roll_die(6)
            rolls.append(next_roll)
            if next_roll != 1:
                break
        # Count the 1s (negative direction = pretty)
        ones_count = sum(1 for r in rolls if r == 1)
        return rolls, -ones_count

    elif first_roll == 6:
        # Keep rolling while we get 6s
        while rolls[-1] == 6:
            next_roll = roll_die(6)
            rolls.append(next_roll)
            if next_roll != 6:
                break
        # Count the 6s (positive direction = ugly)
        sixes_count = sum(1 for r in rolls if r == 6)
        return rolls, sixes_count

    else:
        # 2-5: no explosion, average result
        return rolls, 0


def format_dice_notation(num_dice: int, sides: int, modifier: int = 0) -> str:
    """
    Format dice rolls in standard notation (e.g., "3d6+2", "2d10").

    Args:
        num_dice: Number of dice
        sides: Number of sides per die
        modifier: Bonus or penalty to add to total (default: 0)

    Returns:
        String in dice notation format

    Examples:
        >>> format_dice_notation(3, 6)
        '3d6'
        >>> format_dice_notation(2, 10, 5)
        '2d10+5'
        >>> format_dice_notation(1, 20, -2)
        '1d20-2'
    """
    notation = f"{num_dice}d{sides}"
    if modifier > 0:
        notation += f"+{modifier}"
    elif modifier < 0:
        notation += f"{modifier}"
    return notation
