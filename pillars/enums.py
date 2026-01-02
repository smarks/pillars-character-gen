"""
Enumeration types for Pillars RPG character generation.

This module contains all enums used throughout the character generation system.
By having enums in a separate module, we avoid circular import issues between
attributes.py and constants.py.
"""

from enum import Enum


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


class MagicSchool(Enum):
    """Enumeration of magic schools."""

    # Common Schools (0-70 percentile)
    ELEMENTAL_FIRE = "Elemental Fire"
    ELEMENTAL_LIGHTNING = "Elemental Lightning"
    ELEMENTAL_WATER = "Elemental Water"
    ELEMENTAL_EARTH = "Elemental Earth"
    ELEMENTAL_WIND = "Elemental Wind"
    ALL_ELEMENTS = "All Elements"
    PASSAGE = "Passage"
    PROTECTION = "Protection"
    MENDING = "Mending"
    # Less Common Schools (71-100 percentile)
    WEATHER = "Weather"
    COUNTER = "Counter"
    ARCANE_HELP = "Arcane Help"
    CONTROL = "Control"
