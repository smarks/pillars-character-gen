# Code Review: Duplication and Cleanup Suggestions

## Summary

This document identifies code duplication and provides cleanup suggestions for the Pillars Character Generator codebase.

---

## 1. Shell Script Duplication

### Issue
The `.env` loading and PostgreSQL fallback logic is duplicated in `run.sh` and `setup.sh`.

**Location:**
- `run.sh` lines 18-39
- `setup.sh` lines 35-46

### Suggestion
Create a shared function or source a common script:

**Option A: Create `scripts/common.sh`**
```bash
#!/bin/bash
# Common functions for Pillars Character Generator scripts

load_env_with_fallback() {
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
        
        # If DATABASE_URL is set but PostgreSQL isn't available, use SQLite instead
        if [ -n "$DATABASE_URL" ]; then
            if command -v psql >/dev/null 2>&1; then
                if ! psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
                    echo "Warning: DATABASE_URL is set but PostgreSQL connection failed."
                    echo "Using SQLite for local development instead."
                    unset DATABASE_URL
                fi
            else
                echo "Note: Using SQLite for local development (PostgreSQL not available)."
                unset DATABASE_URL
            fi
        fi
    fi
}
```

Then source it in both scripts:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/common.sh"
load_env_with_fallback
```

---

## 2. Attribute Modifier Calculation Duplication

### Issue
The pattern of getting all modifiers and summing them is repeated multiple times in `generator.py`.

**Locations:**
- `generator.py` lines 325-326 (chosen_track path)
- `generator.py` lines 348-349 (auto-select path)
- `generator.py` lines 214-215 (Character.__str__)
- `attributes.py` lines 2246-2247 (PriorExperience.__str__)

### Suggestion
Add a helper method to `CharacterAttributes`:

```python
def get_total_modifier(self) -> int:
    """Get the sum of all attribute modifiers."""
    return sum(self.get_all_modifiers().values())
```

Then use it:
```python
total_modifier = attributes.get_total_modifier()
```

---

## 3. AcceptanceCheck Creation Patterns

### Issue
Similar patterns for creating `AcceptanceCheck` objects with default values for auto-accept tracks.

**Locations:**
- `attributes.py` lines 1801-1804, 1806-1809, 1811-1814 (RANDOM, WORKER, CRAFTS)
- `attributes.py` lines 1908-1919 (get_eligible_tracks)

### Suggestion
Create a helper function:

```python
def create_auto_accept_check(track: TrackType, reason: str = "No requirements") -> AcceptanceCheck:
    """Create an AcceptanceCheck for tracks that auto-accept."""
    return AcceptanceCheck(
        track=track,
        accepted=True,
        roll=None,
        target=None,
        modifiers={},
        reason=reason
    )
```

Usage:
```python
acceptance_check = create_auto_accept_check(TrackType.RANDOM)
```

---

## 4. Track Availability Calculation Duplication

### Issue
Similar min/max roll calculation logic for Army and Navy tracks in `get_track_availability()`.

**Location:**
- `attributes.py` lines 1684-1697 (Army)
- `attributes.py` lines 1699-1710 (Navy)

### Suggestion
Create a helper function:

```python
def calculate_roll_availability(
    min_roll: int,
    max_roll: int,
    total_modifier: int,
    target: int
) -> Dict:
    """Calculate track availability based on roll range and modifier."""
    min_total = min_roll + total_modifier
    max_total = max_roll + total_modifier
    
    return {
        'available': max_total >= target,
        'requires_roll': True,
        'auto_accept': min_total >= target,
        'impossible': max_total < target,
        'roll_info': f"Need {target}+, your modifier: {total_modifier:+d}"
    }
```

Usage:
```python
total_mod = str_mod + dex_mod
availability[TrackType.ARMY] = {
    'requirement': f"2d6 + STR({str_mod:+d}) + DEX({dex_mod:+d}) ≥ 8",
    **calculate_roll_availability(2, 12, total_mod, 8)
}
```

---

## 5. Skill Track Creation Duplication

### Issue
Significant duplication between `roll_skill_track()` and `create_skill_track_for_choice()` for building the final `SkillTrack` object.

**Locations:**
- `attributes.py` lines 1847-1887 (create_skill_track_for_choice)
- `attributes.py` lines 2071-2119 (roll_skill_track)

### Suggestion
Extract common logic into a helper function:

```python
def build_skill_track(
    track: TrackType,
    acceptance_check: AcceptanceCheck,
    sub_class: str,
    wealth_level: str,
    skill_track_obj: Optional[SkillTrack] = None
) -> SkillTrack:
    """Build a complete SkillTrack object from track type and acceptance."""
    # Determine survivability
    survivability_roll = None
    if track == TrackType.RANDOM:
        survivability, survivability_roll = roll_survivability_random()
    else:
        survivability = TRACK_SURVIVABILITY.get(track, 5) or 5
    
    # Get initial skills
    initial_skills = list(TRACK_INITIAL_SKILLS.get(track, []))
    
    # Handle special cases
    craft_type = None
    craft_rolls = None
    magic_school = None
    magic_school_rolls = None
    
    if track == TrackType.WORKER:
        if wealth_level == "Subsistence" or sub_class == "Laborer":
            initial_skills.append("Laborer (bonus)")
    elif track == TrackType.CRAFTS:
        craft_type, craft_rolls = roll_craft_type()
        initial_skills.append(f"Craft: {craft_type.value}")
    elif track == TrackType.MAGIC:
        magic_school, magic_school_rolls = roll_magic_school()
        spells = MAGIC_SPELL_PROGRESSION.get(magic_school, [])
        if spells:
            initial_skills.append(f"Spell: {spells[0]}")
        initial_skills.append(f"School: {magic_school.value}")
    
    return SkillTrack(
        track=track,
        acceptance_check=acceptance_check,
        survivability=survivability,
        survivability_roll=survivability_roll,
        initial_skills=initial_skills,
        craft_type=craft_type,
        craft_rolls=craft_rolls,
        magic_school=magic_school,
        magic_school_rolls=magic_school_rolls
    )
```

---

## 6. Magic School Spell Handling Duplication

### Issue
Similar code for getting first spell from magic school progression appears in multiple places.

**Locations:**
- `attributes.py` line 1872-1874 (create_skill_track_for_choice)
- `attributes.py` lines 2103-2107 (roll_skill_track)

### Suggestion
Create a helper function:

```python
def get_magic_initial_skills(magic_school: MagicSchool) -> List[str]:
    """Get initial skills for a magic school track."""
    spells = MAGIC_SPELL_PROGRESSION.get(magic_school, [])
    skills = []
    if spells:
        skills.append(f"Spell: {spells[0]}")
    skills.append(f"School: {magic_school.value}")
    return skills
```

---

## 7. Total Modifier String Formatting

### Issue
Similar pattern for formatting total modifier as string appears in multiple places.

**Locations:**
- `generator.py` lines 214-216
- `attributes.py` lines 2246-2248

### Suggestion
Create a helper function:

```python
def format_total_modifier(modifiers: Dict[str, int]) -> str:
    """Format total modifier as a string with sign."""
    total = sum(modifiers.values())
    return f"+{total}" if total >= 0 else str(total)
```

---

## 8. Attribute Scores Dictionary Creation

### Issue
Repeated pattern for creating attribute scores dictionary.

**Locations:**
- `generator.py` line 327
- `generator.py` line 350

### Suggestion
Add a method to `CharacterAttributes`:

```python
def get_attribute_scores_dict(self) -> Dict[str, int]:
    """Get all attribute scores as a dictionary."""
    return {attr: getattr(self, attr) for attr in CORE_ATTRIBUTES}
```

---

## 9. Wealth Level Checking Duplication

### Issue
Similar patterns for checking if character is rich or working class.

**Locations:**
- `attributes.py` lines 1621-1623 (check_merchant_acceptance)
- `attributes.py` lines 1738-1740 (get_track_availability)
- `attributes.py` lines 1934, 1985 (get_eligible_tracks, select_optimal_track)

### Suggestion
Create helper functions:

```python
def is_rich(wealth_level: str) -> bool:
    """Check if wealth level is Rich."""
    return wealth_level == "Rich"

def is_poor(wealth_level: str) -> bool:
    """Check if wealth level is Subsistence."""
    return wealth_level == "Subsistence"

def is_working_class(wealth_level: str, social_class: str) -> bool:
    """Check if character is working class."""
    return (wealth_level == "Moderate" and 
            social_class in ["Commoner", "Laborer"])
```

---

## 10. Roll Display Formatting

### Issue
Similar patterns for formatting roll displays with commas.

**Locations:**
- Multiple places using `", ".join(map(str, rolls))`

### Suggestion
Create a helper function:

```python
def format_rolls(rolls: List[int]) -> str:
    """Format a list of rolls as a comma-separated string."""
    return ", ".join(map(str, rolls))
```

---

## 11. Missing Type Hints

### Issue
Some functions are missing return type hints or parameter type hints.

**Examples:**
- `consolidate_skills()` - could use more specific return type
- Some helper functions in attributes.py

### Suggestion
Add complete type hints throughout for better IDE support and type checking.

---

## 12. Magic Track Acceptance Check

### Issue
The `check_magic_acceptance()` function has a slightly different pattern than other checks (no roll).

### Suggestion
Consider standardizing all acceptance checks to use the same structure, even if some don't require rolls.

---

## 13. Constants Organization

### Issue
Large constant dictionaries (like `MAGIC_SPELL_PROGRESSION`, `TRACK_YEARLY_SKILLS`) could be moved to a separate `constants.py` file for better organization.

### Suggestion
Create `pillars/constants.py` and move:
- `MAGIC_SPELL_PROGRESSION`
- `SPELL_SKILL_MASTERY`
- `TRACK_SURVIVABILITY`
- `TRACK_INITIAL_SKILLS`
- `TRACK_YEARLY_SKILLS`
- `HEIGHT_TABLE`
- `WEIGHT_TABLE`
- `WEALTH_TABLE`
- `AGING_EFFECTS`

---

## 14. Error Handling

### Issue
Some functions don't handle edge cases or invalid inputs gracefully.

**Examples:**
- `roll_skill_track()` with invalid track type
- Missing validation in some roll functions

### Suggestion
Add input validation and clear error messages for invalid inputs.

---

## Priority Recommendations

1. **High Priority:**
   - Extract `.env` loading to shared script (#1)
   - Add `get_total_modifier()` method (#2)
   - Extract skill track building logic (#5)

2. **Medium Priority:**
   - Create helper functions for acceptance checks (#3)
   - Extract roll availability calculation (#4)
   - Add wealth level helper functions (#9)

3. **Low Priority:**
   - Organize constants (#13)
   - Add type hints (#11)
   - Improve error handling (#14)

---

## Testing Considerations

When refactoring, ensure:
- All existing tests still pass
- New helper functions are tested
- Edge cases are covered
- No behavior changes (only structure improvements)

