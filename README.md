# Pillars RPG Character Generator

A Python-based character generation system for the Pillars tabletop RPG, featuring generalized, reusable dice rolling methods and comprehensive testing.

## Features

- **4d6 Drop Lowest Method**: Roll 4d6 and keep the best 3 for each attribute (recommended)
- **3d6 Method**: Traditional roll 3d6 for each attribute
- **Point Buy System**: Allocate 65 points among attributes
- **Detailed Roll Tracking**: See every die roll and which dice were kept/dropped
- **Attribute Modifiers**: Automatic calculation of modifiers based on attribute values
- **Comprehensive Testing**: 57 unit tests covering all functionality

## Project Structure

```
character_gen/
├── dice.py                          # Core dice rolling utilities
├── attributes.py                    # Character attribute generation
├── test_dice.py                     # Unit tests for dice module
├── test_attributes.py               # Unit tests for attributes module
├── generate_character.py            # Interactive character generator
├── character_generation_steps.txt   # Complete character generation reference
└── README.md                        # This file
```

## Quick Start

### Generate a Character

```bash
python3 generate_character.py
```

This launches an interactive menu where you can:
1. Generate using 3d6 method
2. Generate using 4d6 drop lowest method (recommended)
3. Generate and compare multiple characters
4. Compare both generation methods

### Run Tests

```bash
# Run all tests
python3 -m pytest test_dice.py test_attributes.py -v

# Run only dice tests
python3 -m pytest test_dice.py -v

# Run only attribute tests
python3 -m pytest test_attributes.py -v
```

## Usage Examples

### Generate a Single Character

```python
from helpers.attributes import generate_attributes_4d6_drop_lowest, display_attribute_rolls

# Generate character using 4d6 drop lowest
character = generate_attributes_4d6_drop_lowest()

# Display detailed roll information
display_attribute_rolls(character)
```

Output:
```
4D6 DROP LOWEST ATTRIBUTE GENERATION
============================================================
STR: 16 (modifier: +3)
  Rolled: [6, 5, 5, 1] → Kept: [6, 5, 5]

DEX: 8 (modifier: +0)
  Rolled: [4, 1, 3, 1] → Kept: [4, 3, 1]

...
```

### Use Individual Dice Functions

```python
from helpers.dice import roll_die, roll_dice, roll_with_drop_lowest

# Roll a single d20
result = roll_die(20)

# Roll 3d6
rolls = roll_dice(3, 6)

# Roll 4d6 and drop the lowest
all_rolls, kept_rolls, total = roll_with_drop_lowest(4, 6, 1)
print(f"Rolled {all_rolls}, kept {kept_rolls}, total: {total}")
```

### Access Character Attributes

```python
from helpers.attributes import generate_attributes_4d6_drop_lowest, CORE_ATTRIBUTES

character = generate_attributes_4d6_drop_lowest()

# Get individual attributes
print(f"Strength: {character.STR}")
print(f"Dexterity: {character.DEX}")

# Get modifiers
str_modifier = character.get_modifier("STR")
all_modifiers = character.get_all_modifiers()

# Iterate through all attributes
for attr in CORE_ATTRIBUTES:
    value = getattr(character, attr)
    modifier = character.get_modifier(attr)
    print(f"{attr}: {value} ({modifier:+d})")
```

## Core Attributes

The six core attributes in Pillars:

- **STR (Strength)**: Physical power, melee damage, carrying capacity
- **DEX (Dexterity)**: Agility, ranged attacks, initiative, reflex saves
- **INT (Intelligence)**: Learning, arcane magic, perception
- **WIS (Wisdom)**: Judgment, insight, awareness, willpower
- **CON (Constitution)**: Health, endurance, damage resistance
- **CHR (Charisma)**: Influence, leadership, persuasion

## Attribute Modifiers

| Attribute Value | Modifier |
|----------------|----------|
| 3              | -5       |
| 4              | -4       |
| 5              | -3       |
| 6              | -2       |
| 7              | -1       |
| 8-13           | 0        |
| 14             | +1       |
| 15             | +2       |
| 16             | +3       |
| 17             | +4       |
| 18             | +5       |

## Dice Module API

### Basic Functions

- `roll_die(sides)` - Roll a single die
- `roll_dice(num_dice, sides)` - Roll multiple dice
- `roll_and_sum(num_dice, sides)` - Roll and return both rolls and sum
- `roll_percentile()` - Roll d100

### Advanced Functions

- `roll_with_drop_lowest(num_dice, sides, num_drop)` - Roll and drop lowest dice
- `roll_with_drop_highest(num_dice, sides, num_drop)` - Roll and drop highest dice
- `format_dice_notation(num_dice, sides, modifier)` - Format as "3d6+2" notation

## Attributes Module API

### Generation Functions

- `generate_attributes_3d6()` - Generate using 3d6 method
- `generate_attributes_4d6_drop_lowest()` - Generate using 4d6 drop lowest
- `generate_attributes_point_buy(points)` - Create point buy template

### Utility Functions

- `get_attribute_modifier(value)` - Calculate modifier for an attribute value
- `validate_point_buy(attributes, total_points)` - Validate point buy allocation
- `display_attribute_rolls(character)` - Display formatted character information

## Test Coverage

### Dice Tests (28 tests)
- Single die rolling (d6, d20, d100)
- Multiple dice rolling
- Drop lowest/highest mechanics
- Percentile dice
- Error handling
- Statistical validation

### Attribute Tests (29 tests)
- Modifier calculations
- 3d6 generation
- 4d6 drop lowest generation
- Point buy validation
- Character attribute methods
- Statistical properties

## Complete Character Generation

For the full character generation process including:
- Background (Provenance, Location, Wealth)
- Prior Experience (Skill Tracks)
- Aging Effects
- Derived Attributes (Fatigue Points, Body Points)
- Magic Skills
- Equipment

See `character_generation_steps.txt` for the complete reference guide.

## Requirements

- Python 3.7+
- pytest (for running tests)

## Installation

```bash
# Clone or download the repository
cd character_gen

# Install pytest (if not already installed)
pip install pytest

# Run tests to verify installation
python3 -m pytest test_dice.py test_attributes.py -v
```

## Future Enhancements

Planned features for future versions:
- Complete character sheet generation (Background, Skills, Equipment)
- GUI interface
- Character save/load functionality
- Prior experience and aging system
- Magic spell selection
- Equipment and wealth management
- Export to PDF/JSON

## License

This project is part of the Pillars RPG system.

## Author

Created for the Pillars tabletop RPG campaign.
