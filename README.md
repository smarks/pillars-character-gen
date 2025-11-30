# Pillars RPG Player's Aide including Character Generator

## Project Structure

```
character_gen/
├── dice.py                          # Core dice rolling utilities
├── attributes.py                    # Character attribute generation
├── test_dice.py                     # Unit tests for dice module
├── test_attributes.py               # Unit tests for attributes module
├── generate_character.py            # Interactive character generator
└── README.md                        # This file
```

## Quick Start

### Generate a Character

```bash
python3 generate_character.py
```

### Run Tests

```bash
# Run all tests
python3 -m pytest test_dice.py test_attributes.py -v

# Run only dice tests
python3 -m pytest test_dice.py -v

# Run only attribute tests
python3 -m pytest test_attributes.py -v
```

```run the server
 cd webapp
  python manage.py runserver

  Or from the project root:

  python webapp/manage.py runserver

  Make sure you activate your virtual environment first:

  source .venv/bin/activate

year 