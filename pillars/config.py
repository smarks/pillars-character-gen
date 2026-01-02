"""
Game configuration constants for Pillars RPG.

This module centralizes all magic numbers and configuration values
used throughout the character generation system. By having these
values in one place, they're easier to maintain and adjust.
"""

# =============================================================================
# CHARACTER GENERATION
# =============================================================================

# Starting age for characters before prior experience
STARTING_AGE = 16

# Maximum years of prior experience allowed
MAX_PRIOR_EXPERIENCE_YEARS = 18

# Maximum attempts for attribute focus re-rolls before giving up
MAX_ATTRIBUTE_FOCUS_ATTEMPTS = 100


# =============================================================================
# ATTRIBUTE SYSTEM
# =============================================================================

# Attribute value bounds
ATTRIBUTE_MIN = 3
ATTRIBUTE_MAX = 18

# Modifier bounds (for values outside normal 3-18 range)
MODIFIER_FLOOR = -5
MODIFIER_CEILING = 5

# Default points for point-buy character creation
POINT_BUY_DEFAULT = 65


# =============================================================================
# TRACK ACCEPTANCE TARGETS
# =============================================================================

# Target numbers for 2d6 rolls to join tracks
ARMY_ACCEPTANCE_TARGET = 8
NAVY_ACCEPTANCE_TARGET = 8

# Merchant targets vary by social class
MERCHANT_ACCEPTANCE_TARGETS = {
    "poor": 10,
    "working": 8,
    "above": 6,
}


# =============================================================================
# SOCIAL CLASS THRESHOLDS (percentile rolls)
# =============================================================================

# Main social class determination (d100)
NOBILITY_THRESHOLD = 10  # 1-10 = Nobility
MERCHANT_THRESHOLD = 30  # 11-30 = Merchant, 31+ = Commoner

# Nobility rank thresholds (d100)
NOBILITY_RANKS = [
    (1, 1, "Monarch"),
    (2, 5, "Royal Family"),
    (6, 12, "Duke"),
    (13, 30, "March/Border Lord"),
    (31, 40, "Count/Earl"),
    (41, 46, "Viscount"),
    (47, 60, "Baron"),
    (61, 85, "Baronet"),
    (86, 100, "Knight/Warrior Nobility"),
]

# Merchant type thresholds (d100)
MERCHANT_TYPES = [
    (1, 70, "Retail"),
    (71, 95, "Wholesale"),
    (96, 100, "Specialty"),
]

# Commoner type thresholds (d100)
COMMONER_TYPES = [
    (1, 70, "Laborer"),
    (71, 100, "Crafts"),
]

# Craft type thresholds (d100)
CRAFT_TYPE_THRESHOLDS = [
    (1, 50, "smith_builder"),  # Smith/Builder/Wainwright
    (51, 85, "medical_maker"),  # Medical/Herb Lore/Maker
    (86, 100, "magic"),  # Magic
]


# =============================================================================
# WEALTH THRESHOLDS (percentile rolls)
# =============================================================================

WEALTH_SUBSISTENCE_MAX = 15  # 1-15 = Subsistence
WEALTH_MODERATE_MAX = 70  # 16-70 = Moderate
WEALTH_MERCHANT_MAX = 95  # 71-95 = Merchant class, 96+ = Rich

# Wealth level table for lookups (range_min, range_max) -> (level, base_coin)
WEALTH_TABLE = {
    (0, 15): ("Subsistence", 10),
    (16, 70): ("Moderate", 100),
    (71, 95): ("Merchant", 100),  # Plus bonus
    (96, 100): ("Rich", None),  # Consult DM
}

# Starting coin by wealth level
STARTING_COIN = {
    "Subsistence": 10,
    "Moderate": 100,
    "Merchant": 100,  # Plus bonus
    "Rich": 0,  # Consult DM
}


# =============================================================================
# LOCATION THRESHOLDS (percentile rolls)
# =============================================================================

LOCATION_CITY_MAX = 20  # 1-20 = City
LOCATION_VILLAGE_MAX = 70  # 21-70 = Village
LOCATION_RURAL_MAX = 99  # 71-99 = Rural, 100 = Special

# Literacy modifiers by location type
LITERACY_MODIFIERS = {
    "city": 0,
    "village": 2,
    "rural": 4,
    "special": 0,
}

# Village skill roll threshold (d6: 1-3 = weapon, 4-6 = survival)
VILLAGE_SKILL_THRESHOLD = 3

# Number of survival skills selected for rural characters
RURAL_SKILL_COUNT = 2


# =============================================================================
# PHYSICAL CHARACTERISTICS
# =============================================================================

# Height adjustment per demon die result (inches)
HEIGHT_INCREMENT_INCHES = 4

# Weight STR bonus divisor
WEIGHT_STR_DIVISOR = 2


# =============================================================================
# MAGIC SCHOOL SELECTION
# =============================================================================

# Percentile threshold for common vs less common schools
MAGIC_COMMON_THRESHOLD = 70  # 1-70 = common schools, 71-100 = less common
