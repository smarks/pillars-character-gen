"""
Constants for Pillars RPG character generation.

This module contains all the large data tables and configuration constants
used throughout the character generation system.

Note: TrackType and MagicSchool are imported here. This creates a circular
import, but Python handles it correctly as long as attributes.py imports
this module after defining the enums.
"""

# Import enums - must be done after they're defined in attributes.py
# This is safe because attributes.py imports this module after defining TrackType and MagicSchool
from pillars.attributes import TrackType, MagicSchool

# Magic school spell progressions
MAGIC_SPELL_PROGRESSION = {
    # Elemental schools share the same progression
    MagicSchool.ELEMENTAL_FIRE: [
        "Fire Missile",
        "Fire Ball",
        "Fire Bolt",
        "Fire Shield",
        "Fire Barrier",
        "Fire Elemental",
    ],
    MagicSchool.ELEMENTAL_LIGHTNING: [
        "Lightning Missile",
        "Lightning Ball",
        "Lightning Bolt",
        "Lightning Shield",
        "Lightning Barrier",
        "Lightning Elemental",
    ],
    MagicSchool.ELEMENTAL_WATER: [
        "Water Missile",
        "Water Ball",
        "Water Bolt",
        "Water Shield",
        "Water Barrier",
        "Water Elemental",
    ],
    MagicSchool.ELEMENTAL_EARTH: [
        "Earth Missile",
        "Earth Ball",
        "Earth Bolt",
        "Earth Shield",
        "Earth Barrier",
        "Earth Elemental",
    ],
    MagicSchool.ELEMENTAL_WIND: [
        "Wind Missile",
        "Wind Ball",
        "Wind Bolt",
        "Wind Shield",
        "Wind Barrier",
        "Wind Elemental",
    ],
    MagicSchool.ALL_ELEMENTS: [
        "Elemental Missile",
        "Elemental Ball",
        "Elemental Bolt",
        "Elemental Shield",
        "Elemental Barrier",
        "Summon Elemental",
    ],
    MagicSchool.PASSAGE: [
        "Detect Magic/Light",
        "Knock/Hold/Blur",
        "Transparency/Detect Invisibility/Lock",
        "Breathing",
        "Flying",
        "Pass Wall",
        "Shape Change",
    ],
    MagicSchool.PROTECTION: [
        "Counter 1/Shield/Detect Magic",
        "Counter 2/Shield Wall/Knowledge",
        "Counter 3/Minor Protection from Element",
        "Counter 4/Major Protection from Element",
        "Counter 5/Encase",
    ],
    MagicSchool.MENDING: ["Heal", "Cure", "Web", "Joining", "Breaking", "Shaping"],
    MagicSchool.WEATHER: [
        "Detect Weather",
        "Wind/Wind Counter",
        "Rain/Rain Counter",
        "Storm/Storm Counter",
    ],
    MagicSchool.COUNTER: [
        "Counter 1",
        "Counter 2",
        "Counter 3",
        "Counter 4",
        "Counter 5",
        "Counter 6",
    ],
    MagicSchool.ARCANE_HELP: [
        "Wild Magic",
        "Any Level 2 spell",
        "Controlled Magic",
        "Summon/Control",
        "Bind",
        "Ask",
    ],
    MagicSchool.CONTROL: [
        "Persuade Minor/Calm/Enrage",
        "Minor Illusion/Fatigue",
        "Wound/Effect Mental State",
        "Persuade Major/Illusion",
        "Major Illusion/Area/Effect Senses",
        "Force (Paralyze/Move/etc)",
    ],
}

# Spell skill mastery levels (applies to all spells)
SPELL_SKILL_MASTERY = {
    1: "Cast spell normally",
    2: "Cast without hand gestures",
    3: "Cast without verbal incantation, protection from same spell",
    4: "Costs 1/3 less fatigue, halt same spell",
    5: "Costs 1/2 less fatigue, reflect same spell back onto caster",
    6: "Costs 2/3 less fatigue, invert spell, reflect same spell group back onto caster",
}

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
    TrackType.MAGIC: 7,  # Most dangerous track
}

# Initial skills by track (Year 1 only)
TRACK_INITIAL_SKILLS = {
    TrackType.ARMY: ["Sword +1 to hit", "Sword +1 parry"],
    TrackType.NAVY: ["Cutlass +1 to hit", "Cutlass +1 parry", "Swimming"],
    TrackType.RANGER: [
        "Weapon hit",
        "Weapon parry",
        "Tracking",
        "Wood lore",
        "Ken",
        "Literacy",
    ],
    TrackType.OFFICER: ["Morale", "Ken", "Literacy", "Weapon hit", "Weapon parry"],
    TrackType.RANDOM: ["Random skill", "Swimming"],
    TrackType.WORKER: ["Laborer"],  # Additional Laborer if poor/working class
    TrackType.CRAFTS: ["Laborer", "Literacy"],  # Plus craft type
    TrackType.MERCHANT: ["Coins", "Literacy"],
    TrackType.MAGIC: [],  # See Magic spell tables
}

# Skill tables by track - skills gained each year (roll d6 or use year index)
# These are representative skills; actual tables may vary
TRACK_YEARLY_SKILLS = {
    TrackType.ARMY: [
        "Sword +1 to hit",
        "Sword +1 parry",
        "Shield",
        "Tactics",
        "Formation Fighting",
        "Polearm",
        "Archery",
        "Riding",
        "Survival",
        "First Aid",
        "Intimidation",
        "Leadership",
    ],
    TrackType.NAVY: [
        "Cutlass +1 to hit",
        "Cutlass +1 parry",
        "Swimming",
        "Sailing",
        "Navigation",
        "Rope Use",
        "Climbing",
        "Weather Sense",
        "Ship Knowledge",
        "Trading",
        "Leadership",
    ],
    TrackType.RANGER: [
        "Weapon hit",
        "Weapon parry",
        "Tracking",
        "Wood Lore",
        "Survival",
        "Herb Lore",
        "Stealth",
        "Archery",
        "Animal Handling",
        "Camouflage",
        "Trapping",
        "Ken",
    ],
    TrackType.OFFICER: [
        "Morale",
        "Ken",
        "Tactics",
        "Leadership",
        "Weapon hit",
        "Weapon parry",
        "Riding",
        "Etiquette",
        "Strategy",
        "Logistics",
        "Diplomacy",
        "Command",
    ],
    TrackType.RANDOM: [
        "Random Skill",
        "Swimming",
        "Gambling",
        "Streetwise",
        "Brawling",
        "Running",
        "Climbing",
        "Persuasion",
        "Observation",
        "Luck",
        "Contacts",
        "Survival",
    ],
    TrackType.WORKER: [
        "Laborer",
        "Strength Training",
        "Endurance",
        "Hauling",
        "Tool Use",
        "Construction",
        "Mining",
        "Farming",
        "Animal Handling",
        "Repair",
        "Teamwork",
        "Fortitude",
    ],
    TrackType.CRAFTS: [
        "Craft Skill",
        "Literacy",
        "Mathematics",
        "Drafting",
        "Apprentice Work",
        "Journeyman Work",
        "Master Technique",
        "Teaching",
        "Business",
        "Negotiation",
        "Quality Control",
        "Innovation",
    ],
    TrackType.MERCHANT: [
        "Coins",
        "Literacy",
        "Negotiation",
        "Appraisal",
        "Bookkeeping",
        "Contacts",
        "Trading",
        "Languages",
        "Law",
        "Contracts",
        "Investment",
        "Management",
    ],
    TrackType.MAGIC: [
        "Spell",
        "Ritual",
        "Magical Theory",
        "Concentration",
        "Meditation",
        "Arcane Lore",
        "Spell",
        "Component Knowledge",
        "Enchanting",
        "Warding",
        "Spell",
        "Mastery",
    ],
}
