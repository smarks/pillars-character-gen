"""
Core views for the Pillars Character Generator.

This module contains the main entry points and navigation views:
- welcome: Welcome page
- dice_roller: Standalone dice roller popup
- start_over: Clear session and redirect
- index: Main generator page
"""

import os
import markdown
from django.shortcuts import render, redirect
from django.conf import settings

from pillars import generate_character
from pillars.attributes import TrackType, get_track_availability

from .session import clear_pending_session, clear_interactive_session
from .helpers import (
    build_track_info,
    get_modifier_for_value,
    get_attribute_base_value,
    consolidate_skills,
)
from .serialization import (
    deserialize_character,
    build_final_str_repr,
    store_current_character,
)


# =============================================================================
# Constants
# =============================================================================

# Movement and encumbrance calculations
MIN_BASE_MOVEMENT = 4
LIGHT_ENCUMBRANCE_MULTIPLIER = 1.5
MEDIUM_ENCUMBRANCE_MULTIPLIER = 2
HEAVY_ENCUMBRANCE_MULTIPLIER = 2.5


# =============================================================================
# Navigation Views
# =============================================================================


def welcome(request):
    """Welcome page with links to main sections.

    Clears any existing character data so clicking 'Character Generator'
    starts a fresh character.
    """
    # Clear character session data
    request.session.pop("current_character", None)
    request.session.pop("interactive_years", None)
    request.session.pop("interactive_skills", None)
    request.session.pop("interactive_yearly_results", None)
    request.session.pop("interactive_aging", None)
    request.session.pop("interactive_died", None)
    request.session.pop("pending_character", None)
    request.session.modified = True

    # Load welcome content from markdown file
    welcome_content = ""
    welcome_file = os.path.join(settings.BASE_DIR, "..", "references", "welcome.md")
    if os.path.exists(welcome_file):
        with open(welcome_file, "r", encoding="utf-8") as f:
            welcome_content = markdown.markdown(f.read())

    return render(
        request, "generator/welcome.html", {"welcome_content": welcome_content}
    )


def dice_roller(request):
    """Standalone dice roller page designed to be opened in a popup window."""
    return render(request, "generator/dice_roller.html")


def start_over(request):
    """Clear all session data and redirect to welcome page."""
    clear_interactive_session(request)
    clear_pending_session(request)
    # Also clear the current character
    if "current_character" in request.session:
        del request.session["current_character"]
    request.session.modified = True
    return redirect("welcome")


# =============================================================================
# Index View Helper Functions
# =============================================================================


def _handle_reroll(request, attribute_focus=None):
    """Handle character reroll with optional attribute focus."""
    character = generate_character(
        years=0, attribute_focus=attribute_focus, skip_track=True
    )
    store_current_character(request, character)
    return character


def _handle_start_fresh(request):
    """Clear all session data and generate a fresh character."""
    clear_pending_session(request)
    for key in [
        "interactive_years",
        "interactive_skills",
        "interactive_yearly_results",
        "interactive_aging",
        "interactive_died",
        "interactive_track_name",
        "current_character",
    ]:
        request.session.pop(key, None)
    request.session.modified = True
    character = generate_character(years=0, skip_track=True)
    store_current_character(request, character)
    return redirect("generator")


def _get_character_modifiers(char_data):
    """Extract attribute modifiers from character data."""
    if not char_data:
        return {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0, "chr": 0}

    attrs = char_data.get("attributes", {})
    return {
        "str": get_modifier_for_value(attrs.get("STR", 10)),
        "dex": get_modifier_for_value(attrs.get("DEX", 10)),
        "int": get_modifier_for_value(attrs.get("INT", 10)),
        "wis": get_modifier_for_value(attrs.get("WIS", 10)),
        "con": get_modifier_for_value(attrs.get("CON", 10)),
        "chr": get_modifier_for_value(attrs.get("CHR", 10)),
    }


def _calculate_movement_encumbrance(char_data):
    """Calculate movement allowance and encumbrance thresholds."""
    if char_data:
        attrs = char_data.get("attributes", {})
        str_val = get_attribute_base_value(attrs.get("STR", 10))
        dex_val = get_attribute_base_value(attrs.get("DEX", 10))
    else:
        str_val = 10
        dex_val = 10

    base_ma = max(MIN_BASE_MOVEMENT, dex_val - 2)
    return {
        "base_ma": base_ma,
        "jog_hexes": base_ma // 2,
        "enc_unenc_max": str_val,
        "enc_light_min": str_val + 1,
        "enc_light_max": int(str_val * LIGHT_ENCUMBRANCE_MULTIPLIER),
        "enc_med_min": int(str_val * LIGHT_ENCUMBRANCE_MULTIPLIER) + 1,
        "enc_med_max": str_val * int(MEDIUM_ENCUMBRANCE_MULTIPLIER),
        "enc_heavy_min": str_val * int(MEDIUM_ENCUMBRANCE_MULTIPLIER) + 1,
        "enc_heavy_max": int(str_val * HEAVY_ENCUMBRANCE_MULTIPLIER),
    }


def _get_selected_track_key(char_data):
    """Get the track key for highlighting in UI."""
    if not char_data or not char_data.get("skill_track"):
        return None

    track_value = char_data["skill_track"].get("track")
    for track_type in TrackType:
        if track_type.value == track_value:
            return track_type.name
    return None


def _build_index_context(request, character, char_data):
    """Build the context dictionary for the index template."""
    # Late import to avoid circular dependency
    from .character_sheet import build_skill_points_from_char_data

    years_completed = request.session.get("interactive_years", 0)
    skills = request.session.get("interactive_skills", [])
    yearly_results = request.session.get("interactive_yearly_results", [])
    aging_data = request.session.get("interactive_aging", {})
    died = request.session.get("interactive_died", False)
    track_name = request.session.get("interactive_track_name", "")

    # Build complete str_repr if there's prior experience
    if years_completed > 0 and char_data:
        final_str_repr = build_final_str_repr(
            char_data, years_completed, skills, yearly_results, aging_data, died
        )
        character._str_repr = final_str_repr

    # Build track info
    mods = _get_character_modifiers(char_data)
    if char_data:
        social_class = char_data.get("provenance_social_class", "Commoner")
        wealth_level = char_data.get("wealth_level", "Moderate")
        track_availability = get_track_availability(
            mods["str"],
            mods["dex"],
            mods["int"],
            mods["wis"],
            social_class,
            wealth_level,
        )
        track_info = build_track_info(track_availability)
    else:
        track_info = []

    # Calculate movement and encumbrance
    movement = _calculate_movement_encumbrance(char_data)

    # Build skill points data (migrates legacy if needed)
    char_skills = build_skill_points_from_char_data(char_data or {})
    skills_with_details = char_skills.get_skills_with_details()
    free_skill_points = char_skills.free_points
    total_xp = char_skills.total_xp

    # Use skills_with_details for component (has name/display structure), or fall back to simple list
    if skills_with_details:
        skills = skills_with_details
    else:
        # Fall back to legacy format - convert to dict structure for consistency
        legacy_skills = consolidate_skills(skills) if skills else []
        skills = [{"name": s, "display": s} for s in legacy_skills]

    # Extract aging penalties
    aging = char_data.get("interactive_aging", {}) if char_data else {}
    aging_penalties = {
        "str": aging.get("str", 0),
        "dex": aging.get("dex", 0),
        "int": aging.get("int", 0),
        "wis": aging.get("wis", 0),
        "con": aging.get("con", 0),
    }

    return {
        "character": character,
        "char_data": char_data or {},
        "years_completed": years_completed,
        "years_served": years_completed,
        "current_age": 16 + years_completed,
        "skills": skills,
        "aging_penalties": aging_penalties,
        "skills_with_details": skills_with_details,
        "free_skill_points": free_skill_points,
        "total_xp": total_xp,
        "yearly_results": yearly_results,
        "has_experience": years_completed > 0,
        "died": died,
        "track_name": track_name,
        "track_info": track_info,
        "selected_track": _get_selected_track_key(char_data),
        "str_mod": mods["str"],
        "dex_mod": mods["dex"],
        "int_mod": mods["int"],
        "wis_mod": mods["wis"],
        "con_mod": mods["con"],
        "chr_mod": mods["chr"],
        **movement,
    }


# =============================================================================
# Main Index View
# =============================================================================


def index(request):
    """Main character generator page.

    Handles character generation, rerolling, and experience addition.
    See helper functions above for implementation details.
    """
    # Late import to avoid circular dependency
    from .prior_experience import _handle_add_experience

    action = request.POST.get("action", "") if request.method == "POST" else ""

    # Handle POST actions
    if action == "reroll_none":
        character = _handle_reroll(request, attribute_focus=None)
    elif action == "reroll_physical":
        character = _handle_reroll(request, attribute_focus="physical")
    elif action == "reroll_mental":
        character = _handle_reroll(request, attribute_focus="mental")
    elif action == "start_fresh":
        return _handle_start_fresh(request)
    elif action == "add_experience":
        return _handle_add_experience(request)
    else:
        # GET request or unknown action
        char_data = request.session.get("current_character")
        if char_data and not action:
            character = deserialize_character(char_data)
        else:
            character = generate_character(years=0, skip_track=True)
            store_current_character(request, character)

    char_data = request.session.get("current_character")
    context = _build_index_context(request, character, char_data)
    return render(request, "generator/index.html", context)
