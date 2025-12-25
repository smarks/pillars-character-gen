# Character Generator Improvements

## Bug Fixes

### 1. ✅ Name Disappearing Bug (FIXED)
**Issue:** When adding experience, the character name disappears.

**Root Cause:** 
- The name field is stored in `char_data['name']` but wasn't being preserved when `_handle_add_experience` updates the session
- `serialize_character()` didn't preserve user-edited fields like `name`

**Fix:**
- Modified `_handle_add_experience()` to capture name from POST data
- Updated `serialize_character()` to accept `preserve_data` parameter
- Updated `store_current_character()` to preserve existing user-edited fields
- Ensured `_update_experience_session()` preserves name in char_data

## Current Editable Fields

### ✅ Fully Editable (via character sheet component)
1. **Name** - Text input
2. **Attributes** (STR, DEX, INT, WIS, CON, CHR) - Text inputs with decimal support
3. **Appearance** - Text input
4. **Height** - Text input
5. **Weight** - Text input
6. **Provenance** - Text input
7. **Location** - Text input
8. **Literacy** - Dropdown (None, Basic, Literate)
9. **Wealth Level** - Dropdown (Destitute, Poor, Moderate, Comfortable, Rich)
10. **Skills** - Add/remove/allocate points

### ⚠️ Partially Editable
- **Fatigue Points** - Calculated (derived from attributes)
- **Body Points** - Calculated (derived from attributes)
- **Skill Track** - Set when adding experience (not directly editable)
- **Prior Experience** - Added through experience flow (not directly editable)

### ❌ Not Editable (but displayed)
- Attribute modifiers (calculated)
- Track survivability (set by track selection)
- Initial skills (set by track)
- Year-by-year experience log (generated)

## Suggested Improvements

### 1. Auto-save Name Field
**Current:** Name is only saved when form is submitted or via AJAX update
**Improvement:** Auto-save name field on blur/change to prevent data loss

### 2. Better Field Organization
**Current:** All fields in one long list
**Improvement:** 
- Group related fields (Physical, Mental, Social)
- Add collapsible sections
- Better visual hierarchy

### 3. Add Notes Field
**Current:** Notes field exists in saved characters but not in generator view
**Improvement:** Add notes field to generator page for quick character notes

### 4. Real-time Validation
**Current:** Attribute values can be set to invalid ranges
**Improvement:** 
- Validate attribute ranges (1-18+)
- Show warnings for extreme values
- Prevent invalid decimal formats

### 5. Better Experience Flow
**Current:** Adding experience redirects back to generator
**Improvement:**
- Show experience summary before redirect
- Allow editing experience years before finalizing
- Preview what will be added

### 6. Character Summary Panel
**Current:** Full character sheet is always visible
**Improvement:**
- Add collapsible summary panel
- Show key stats at a glance
- Quick access to most-used fields

### 7. Undo/Redo Support
**Current:** No way to undo changes
**Improvement:**
- Add undo/redo for field edits
- Session history for character changes

### 8. Export Options
**Current:** Copy to clipboard only
**Improvement:**
- Export to PDF
- Export to JSON
- Export to markdown
- Print-friendly view

### 9. Character Comparison
**Current:** Can only view one character at a time
**Improvement:**
- Side-by-side comparison
- Attribute comparison charts

### 10. Better Mobile Experience
**Current:** Layout may not be optimal on mobile
**Improvement:**
- Responsive design improvements
- Touch-friendly controls
- Mobile-optimized layout

## Implementation Priority

### High Priority
1. ✅ Fix name disappearing bug
2. Auto-save name field
3. Add notes field to generator
4. Better field validation

### Medium Priority
5. Better field organization
6. Real-time validation
7. Export options
8. Character summary panel

### Low Priority
9. Undo/redo support
10. Character comparison
11. Mobile optimizations

