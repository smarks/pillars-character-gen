# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pillars RPG Character Generator - A Python application for generating tabletop RPG characters. Consists of:
1. **Core Library** (`pillars/`) - Dice rolling, attribute generation, skill tracks, prior experience system
2. **Django Web App** (`webapp/`) - Interactive character generation UI with session-based state management

## Commands

### Run Tests
```bash
# All tests (from project root)
python -m pytest tests/ -v

# Single test file
python -m pytest tests/test_dice.py -v

# With coverage
python -m pytest tests/ --cov=pillars
```

### Run Development Server
```bash
source .venv/bin/activate
cd webapp
python manage.py runserver

# Or from project root:
python webapp/manage.py runserver
```

### Database Migrations
```bash
cd webapp
python manage.py makemigrations
python manage.py migrate
```

## Architecture

### Core Library (`pillars/`)

- **`dice.py`** - Dice utilities: `roll_die()`, `roll_dice()`, `roll_with_drop_lowest()`, `roll_demon_die()` (exploding d6 for appearance/height/weight)
- **`attributes.py`** - Character attributes, skill tracks, prior experience. Key types:
  - `CharacterAttributes` - Core stats (STR, DEX, INT, WIS, CON, CHR) with derived fatigue/body points
  - `TrackType` enum - Career paths (ARMY, NAVY, RANGER, OFFICER, MAGIC, WORKER, CRAFTS, MERCHANT, RANDOM)
  - `SkillTrack` - Track with survivability, acceptance checks, initial skills
  - `PriorExperience` - Years of experience with yearly survival rolls
- **`generator.py`** - Main `generate_character()` function and `Character` dataclass

### Character Generation Flow

1. `generate_character(skip_track=True)` - Creates base character without career path
2. User selects skill track via `create_skill_track_for_choice()` - Some tracks require acceptance rolls
3. `roll_prior_experience()` - Year-by-year experience with survivability checks (3d6 + modifiers vs target)
4. Characters can die during prior experience if survival roll fails

### Web App (`webapp/webapp/generator/`)

Session-based state machine for interactive character creation:

- **`views.py`** - Main views: `index`, `select_track`, `interactive`, `finished`
- **Session keys**: `current_character`, `interactive_*` (for year-by-year mode), `pending_*` (track selection)
- **Templates**: `generator/` folder with `index.html`, `select_track.html`, `interactive.html`, `finished.html`
- **`serialize_character()`/`deserialize_character()`** - Convert Character objects to/from session-storable dicts

### Key Patterns

- Attribute modifiers: 3-7 = negative, 8-13 = 0, 14+ = positive (see `ATTRIBUTE_MODIFIERS` dict)
- Survivability: Lower number = safer track (Worker=4, Magic=7)
- Skill consolidation: `consolidate_skills()` combines duplicate skills (e.g., "Sword +1 to hit" x3 becomes "Sword +3 to hit")

## Testing

Tests in `tests/` cover:
- `test_dice.py` - Dice rolling functions
- `test_attributes.py` - Attribute generation, skill tracks
- `test_generator.py` - Full character generation
