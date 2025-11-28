"""
Pillars RPG Character Generator Library.

This package provides tools for generating characters for the Pillars RPG system.
"""

from pillars.generator import generate_character, Character
from pillars.dice import roll_die, roll_dice, roll_percentile

__all__ = [
    'generate_character',
    'Character',
    'roll_die',
    'roll_dice',
    'roll_percentile',
]
