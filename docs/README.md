# Pillars RPG Player's Aide including Character Generator

## Project Structure
 

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
source .venv/bin/activate 
 cd webapp
  python manage.py runserver

  Or from the project root:

  python webapp/manage.py runserver

  Make sure you activate your virtual environment first:

  source .venv/bin/activate
 