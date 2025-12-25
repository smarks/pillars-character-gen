# Missing Character Fields Analysis

## Character Object Structure

From `pillars/generator.py`, a `Character` object has:
- `attributes: CharacterAttributes` (STR, DEX, INT, WIS, CON, CHR + derived stats)
- `appearance: Appearance` (description, intensity, rolls)
- `height: Height` (hands, inches, imperial format)
- `weight: Weight` (stones, pounds, rolls)
- `provenance: Provenance` (social_class, sub_class, craft_type, rolls)
- `location: Location` (name, skills, literacy modifier)
- `literacy: LiteracyCheck` (is_literate, roll, target)
- `wealth: Wealth` (wealth_level, amount)
- `skill_track: Optional[SkillTrack]` (track, survivability, initial_skills, etc.)
- `prior_experience: Optional[PriorExperience]` (years_served, yearly_results, aging)

## Currently Displayed Fields

### ✅ Fully Displayed & Editable
1. **Name** - Text input (editable)
2. **Attributes** (STR, DEX, INT, WIS, CON, CHR) - Text inputs with decimal support (editable)
3. **Fatigue Points** - Calculated display (read-only, derived from attributes)
4. **Body Points** - Calculated display (read-only, derived from attributes)
5. **Appearance** - Text input (editable)
6. **Height** - Text input (editable)
7. **Weight** - Text input (editable)
8. **Provenance** - Text input (editable)
9. **Location** - Text input (editable)
10. **Literacy** - Dropdown (None, Basic, Literate) (editable)
11. **Wealth Level** - Dropdown (Destitute, Poor, Moderate, Comfortable, Rich) (editable)
12. **Skills** - List with add/remove/allocate (editable)
13. **Free Skill Points** - Display (read-only, calculated)
14. **Total XP** - Display (read-only, calculated)
15. **Notes** - Textarea (editable) ✅

### ✅ Displayed but Read-Only
1. **Skill Track** - Display only (track name, survivability, craft_type, magic_school)
2. **Prior Experience** - Year-by-year log (read-only)
3. **Current Age** - Calculated (16 + years_served)
4. **Years Served** - Display only
5. **Movement & Encumbrance** - Calculated tables (read-only)
6. **Equipment** - Separate section with add/remove (editable via equipment system)

## Missing or Partially Missing Fields

### ❌ NOT Displayed (but exist in Character object)

1. **Aging Effects** - `interactive_aging` dict with penalties to STR, DEX, INT, WIS, CON
   - **Status**: Stored in `char_data['interactive_aging']` but NOT displayed
   - **Should be**: Displayed as read-only showing penalties applied
   - **Location**: Should be in Attributes section or Prior Experience section

2. **Attribute Roll Details** - `attributes.roll_details` (List[AttributeRoll])
   - **Status**: Not displayed
   - **Should be**: Optional expandable section showing how attributes were rolled
   - **Use case**: For transparency/debugging

3. **Provenance Details** - `provenance.main_roll`, `provenance.sub_roll`, `provenance.craft_roll`
   - **Status**: Only the string representation is shown
   - **Should be**: Optional display of roll details
   - **Use case**: For transparency

4. **Appearance Details** - `appearance.rolls`, `appearance.intensity`
   - **Status**: Only the description string is shown
   - **Should be**: Optional display of roll details
   - **Use case**: For transparency

5. **Height Details** - `height.rolls`, `height.hands`, `height.feet`, `height.remaining_inches`
   - **Status**: Only the string representation is shown
   - **Should be**: Could show imperial format (5'8") more prominently
   - **Note**: Currently editable as text, so user can override

6. **Weight Details** - `weight.rolls`, `weight.base_stones`, `weight.str_bonus_stones`
   - **Status**: Only the string representation is shown
   - **Should be**: Could show pounds more prominently
   - **Note**: Currently editable as text, so user can override

7. **Literacy Details** - `literacy.roll`, `literacy.target`, `literacy.difficulty_modifier`
   - **Status**: Only the result (None/Basic/Literate) is shown
   - **Should be**: Optional display of roll details
   - **Use case**: For transparency

8. **Wealth Amount** - `wealth.amount` (actual money value)
   - **Status**: Only `wealth_level` is shown
   - **Should be**: Display actual wealth amount if available
   - **Note**: May not always be set

9. **Location Skills** - `location.skills` (skills from location)
   - **Status**: Not explicitly shown as "from location"
   - **Should be**: Could be marked in skills list or shown separately
   - **Note**: These are included in the skills list but not labeled

10. **Initial Skills** - `skill_track.initial_skills` (Year 1 skills)
    - **Status**: Not explicitly shown as "initial skills"
    - **Should be**: Could be marked in skills list
    - **Note**: These are included in the skills list but not labeled

11. **Generation Method** - `attributes.generation_method`
    - **Status**: Not displayed
    - **Should be**: Optional display (e.g., "4d6 drop lowest", "reroll physical")
    - **Use case**: For reference

12. **Fatigue Roll** - `attributes.fatigue_roll` (1d6 roll for fatigue points)
    - **Status**: Not displayed
    - **Should be**: Optional display
    - **Note**: Fatigue points are shown, but not the roll

13. **Body Roll** - `attributes.body_roll` (1d6 roll for body points)
    - **Status**: Not displayed
    - **Should be**: Optional display
    - **Note**: Body points are shown, but not the roll

## Recommendations

### High Priority (Should Add)
1. **Aging Effects Display** - Show attribute penalties from aging in the Attributes section
2. **Wealth Amount** - Display actual wealth value if available

### Medium Priority (Nice to Have)
3. **Roll Details Section** - Collapsible section showing how attributes/provenance/etc. were rolled
4. **Skill Sources** - Mark skills as "from location", "from track", "from experience", "player-added"
5. **Generation Method** - Show how attributes were generated

### Low Priority (Optional/Advanced)
6. **Detailed Height/Weight** - Show imperial/metric conversions more prominently
7. **Fatigue/Body Roll Details** - Show the 1d6 rolls used

## Implementation Notes

- Most "missing" fields are roll details that are useful for transparency but not essential
- Aging effects are important and should be displayed
- Wealth amount should be shown if it exists
- Skill sources would improve clarity but aren't critical
- Roll details could be in a collapsible "Details" section to avoid clutter

