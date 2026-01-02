"""
Prior experience views for the Pillars Character Generator.

This module handles the track selection and experience rolling:
- select_track: Prior experience page with track selection
- interactive: Year-by-year interactive mode
- Helper functions for experience management
"""

from django.shortcuts import render, redirect
from django.contrib import messages

from pillars import generate_character
from pillars.attributes import (
    roll_single_year,
    SkillTrack,
    TrackType,
    AgingEffects,
    CraftType,
    MagicSchool,
    get_track_availability,
    roll_skill_track,
    create_skill_track_for_choice,
)

from ..models import SavedCharacter
from .session import clear_pending_session, clear_interactive_session
from .helpers import build_track_info, validate_experience_years
from .serialization import (
    serialize_character,
    deserialize_character,
    store_current_character,
)


# =============================================================================
# Helper Functions
# =============================================================================


def _get_or_create_skill_track(char_data, character, track_mode, chosen_track_name):
    """Get existing skill track or create a new one based on user selection.

    Returns:
        tuple: (skill_track, char_data, error_message)
        If error_message is not None, track creation failed.
    """
    str_mod = character.attributes.get_modifier("STR")
    dex_mod = character.attributes.get_modifier("DEX")
    int_mod = character.attributes.get_modifier("INT")
    wis_mod = character.attributes.get_modifier("WIS")
    social_class = char_data.get("provenance_social_class", "Commoner")
    sub_class = char_data.get("provenance_sub_class", "Laborer")
    wealth_level = char_data.get("wealth_level", "Moderate")

    if char_data.get("skill_track"):
        # Use existing track
        track_data = char_data["skill_track"]
        skill_track = SkillTrack(
            track=TrackType(track_data["track"]),
            acceptance_check=None,
            survivability=track_data["survivability"],
            survivability_roll=None,
            initial_skills=track_data["initial_skills"],
            craft_type=(
                CraftType(track_data["craft_type"])
                if track_data.get("craft_type")
                else None
            ),
            craft_rolls=None,
            magic_school=(
                MagicSchool(track_data["magic_school"])
                if track_data.get("magic_school")
                else None
            ),
            magic_school_rolls=track_data.get("magic_school_rolls"),
        )
        return skill_track, char_data, None

    # Create new track
    if track_mode == "manual" and chosen_track_name:
        try:
            chosen_track = TrackType[chosen_track_name]
        except KeyError:
            chosen_track = TrackType.RANDOM
        skill_track = create_skill_track_for_choice(
            chosen_track=chosen_track,
            str_mod=str_mod,
            dex_mod=dex_mod,
            int_mod=int_mod,
            wis_mod=wis_mod,
            social_class=social_class,
            sub_class=sub_class,
            wealth_level=wealth_level,
        )
    else:
        skill_track = roll_skill_track(
            str_mod=str_mod,
            dex_mod=dex_mod,
            int_mod=int_mod,
            wis_mod=wis_mod,
            social_class=social_class,
            sub_class=sub_class,
            wealth_level=wealth_level,
        )

    if skill_track is None or skill_track.track is None:
        return (
            None,
            char_data,
            "Could not create skill track. Try selecting a different track.",
        )

    # Save track to character data
    char_data["skill_track"] = {
        "track": skill_track.track.value,
        "survivability": skill_track.survivability,
        "initial_skills": list(skill_track.initial_skills),
        "craft_type": skill_track.craft_type.value if skill_track.craft_type else None,
        "magic_school": (
            skill_track.magic_school.value if skill_track.magic_school else None
        ),
        "magic_school_rolls": skill_track.magic_school_rolls,
    }
    return skill_track, char_data, None


def _roll_experience_years(
    skill_track, years, existing_years, existing_skills, total_modifier, aging_effects
):
    """Roll experience for the specified number of years.

    Returns:
        tuple: (new_skills, new_yearly_results, died, updated_aging_effects)
    """
    new_skills = []
    new_yearly_results = []
    died = False

    for i in range(years):
        year_index = existing_years + i
        year_result = roll_single_year(
            skill_track=skill_track,
            year_index=year_index,
            total_modifier=total_modifier,
            aging_effects=aging_effects,
        )

        new_skills.append(year_result.skill_gained)
        new_yearly_results.append(
            {
                "year": year_result.year,
                "skill": year_result.skill_gained,
                "surv_roll": year_result.survivability_roll,
                "surv_mod": year_result.survivability_modifier,
                "surv_total": year_result.survivability_total,
                "surv_target": year_result.survivability_target,
                "survived": year_result.survived,
                "aging": year_result.aging_penalties,
            }
        )

        if not year_result.survived:
            died = True
            break

    return new_skills, new_yearly_results, died, aging_effects


def _update_experience_session(
    request,
    char_data,
    skill_track,
    existing_years,
    existing_skills,
    new_skills,
    existing_yearly_results,
    new_yearly_results,
    died,
    aging_effects,
):
    """Update session with new experience data."""
    total_years = existing_years + len(new_yearly_results)
    all_skills = existing_skills + new_skills
    all_yearly_results = existing_yearly_results + new_yearly_results

    # Update session
    request.session["interactive_years"] = total_years
    request.session["interactive_skills"] = all_skills
    request.session["interactive_yearly_results"] = all_yearly_results
    request.session["interactive_died"] = died
    request.session["interactive_aging"] = {
        "str": aging_effects.str_penalty,
        "dex": aging_effects.dex_penalty,
        "int": aging_effects.int_penalty,
        "wis": aging_effects.wis_penalty,
        "con": aging_effects.con_penalty,
    }
    request.session["interactive_track_name"] = skill_track.track.value

    # Update char_data with interactive experience data so it's available for skill points calculation
    char_data["interactive_years"] = total_years
    char_data["interactive_skills"] = all_skills
    char_data["interactive_yearly_results"] = all_yearly_results
    char_data["interactive_died"] = died
    char_data["interactive_aging"] = {
        "str": aging_effects.str_penalty,
        "dex": aging_effects.dex_penalty,
        "int": aging_effects.int_penalty,
        "wis": aging_effects.wis_penalty,
        "con": aging_effects.con_penalty,
    }

    request.session["current_character"] = char_data
    request.session.modified = True


def _sync_experience_to_database(
    request,
    char_data,
    existing_years,
    existing_skills,
    new_skills,
    existing_yearly_results,
    new_yearly_results,
    died,
    aging_effects,
):
    """Sync experience data to database for logged-in users."""
    saved_id = request.session.get("current_saved_character_id")
    if not saved_id or not request.user.is_authenticated:
        return

    try:
        saved_char = SavedCharacter.objects.get(id=saved_id, user=request.user)
        saved_char.character_data["skill_track"] = char_data.get("skill_track")
        saved_char.character_data["interactive_years"] = existing_years + len(
            new_yearly_results
        )
        saved_char.character_data["interactive_skills"] = existing_skills + new_skills
        saved_char.character_data["interactive_yearly_results"] = (
            existing_yearly_results + new_yearly_results
        )
        saved_char.character_data["interactive_died"] = died
        saved_char.character_data["interactive_aging"] = {
            "str": aging_effects.str_penalty,
            "dex": aging_effects.dex_penalty,
            "int": aging_effects.int_penalty,
            "wis": aging_effects.wis_penalty,
            "con": aging_effects.con_penalty,
        }
        saved_char.save()
    except SavedCharacter.DoesNotExist:
        pass


def _handle_add_experience(request):
    """Handle adding experience years to a character."""
    char_data = request.session.get("current_character")
    if not char_data:
        character = generate_character(years=0, skip_track=True)
        store_current_character(request, character)
        char_data = request.session.get("current_character")

    # Preserve name and other editable fields from form submission
    if request.method == "POST":
        char_name = request.POST.get("char_name", "").strip()
        if char_name:
            char_data["name"] = char_name
        # Also preserve any existing name if form field is empty but we have one
        elif not char_data.get("name"):
            # Try to get from existing session data
            existing_name = request.session.get("current_character", {}).get("name")
            if existing_name:
                char_data["name"] = existing_name

    character = deserialize_character(char_data)

    # Get form parameters
    years = validate_experience_years(request.POST.get("years"), default=5)
    track_mode = request.POST.get("track_mode", "auto")
    chosen_track_name = request.POST.get("chosen_track", "")

    # Get or create skill track
    skill_track, char_data, error = _get_or_create_skill_track(
        char_data, character, track_mode, chosen_track_name
    )
    if error:
        messages.error(request, error)
        return redirect("generator")

    # Get existing experience data
    existing_years = request.session.get("interactive_years", 0)
    existing_skills = request.session.get("interactive_skills", [])
    existing_yearly_results = request.session.get("interactive_yearly_results", [])
    existing_aging = request.session.get(
        "interactive_aging", {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0}
    )
    died = request.session.get("interactive_died", False)

    if died:
        return redirect("generator")

    # Reconstruct aging effects
    aging_effects = AgingEffects(
        str_penalty=existing_aging.get("str", 0),
        dex_penalty=existing_aging.get("dex", 0),
        int_penalty=existing_aging.get("int", 0),
        wis_penalty=existing_aging.get("wis", 0),
        con_penalty=existing_aging.get("con", 0),
    )

    # Add initial skills if this is the first experience
    if existing_years == 0:
        existing_skills = list(skill_track.initial_skills)

    # Roll experience years
    total_modifier = sum(character.attributes.get_all_modifiers().values())
    new_skills, new_yearly_results, died, aging_effects = _roll_experience_years(
        skill_track,
        years,
        existing_years,
        existing_skills,
        total_modifier,
        aging_effects,
    )

    # Update session
    _update_experience_session(
        request,
        char_data,
        skill_track,
        existing_years,
        existing_skills,
        new_skills,
        existing_yearly_results,
        new_yearly_results,
        died,
        aging_effects,
    )

    # Sync to database for logged-in users
    _sync_experience_to_database(
        request,
        char_data,
        existing_years,
        existing_skills,
        new_skills,
        existing_yearly_results,
        new_yearly_results,
        died,
        aging_effects,
    )

    return redirect("generator")


# =============================================================================
# Main Views
# =============================================================================


def select_track(request):
    """
    Handle prior experience page with track selection.

    This page allows the user to:
    - Choose years of experience (1-10) or interactive mode
    - Auto-select or manually select a skill track
    - Finish without experience, or add experience
    """
    # Check if we have a pending character
    pending_char = request.session.get("pending_character")
    if not pending_char:
        return redirect("generator")

    # Get stored character info
    str_mod = request.session.get("pending_str_mod", 0)
    dex_mod = request.session.get("pending_dex_mod", 0)
    int_mod = request.session.get("pending_int_mod", 0)
    wis_mod = request.session.get("pending_wis_mod", 0)
    social_class = request.session.get("pending_social_class", "Commoner")
    sub_class = request.session.get("pending_sub_class", "Laborer")
    wealth_level = request.session.get("pending_wealth_level", "Moderate")

    # Get track availability
    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod, social_class, wealth_level
    )
    track_info = build_track_info(track_availability)

    # Reconstruct character for display
    character = deserialize_character(pending_char)

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "start_over":
            clear_pending_session(request)
            return redirect("start_over")

        elif action == "add_experience":
            # Get form data
            interactive_mode = request.POST.get("interactive_mode") == "on"
            track_mode = request.POST.get("track_mode", "auto")
            years = (
                validate_experience_years(request.POST.get("years"), default=5)
                if not interactive_mode
                else 0
            )
            chosen_track_name = request.POST.get("chosen_track", "")

            # Determine the track to use
            chosen_track = None
            if track_mode == "manual":
                if not chosen_track_name:
                    return render(
                        request,
                        "generator/select_track.html",
                        {
                            "character": character,
                            "track_info": track_info,
                            "current_age": 16,
                            "error": "Please select a track when using manual selection",
                        },
                    )
                try:
                    chosen_track = TrackType[chosen_track_name]
                except KeyError:
                    return render(
                        request,
                        "generator/select_track.html",
                        {
                            "character": character,
                            "track_info": track_info,
                            "current_age": 16,
                            "error": "Invalid track selected",
                        },
                    )

                # Check acceptance for manual track
                skill_track = create_skill_track_for_choice(
                    chosen_track=chosen_track,
                    str_mod=str_mod,
                    dex_mod=dex_mod,
                    int_mod=int_mod,
                    wis_mod=wis_mod,
                    social_class=social_class,
                    sub_class=sub_class,
                    wealth_level=wealth_level,
                )

                if not skill_track.acceptance_check.accepted:
                    return render(
                        request,
                        "generator/select_track.html",
                        {
                            "character": character,
                            "track_info": track_info,
                            "current_age": 16,
                            "acceptance_failed": True,
                            "failed_track": chosen_track.value,
                            "acceptance_check": skill_track.acceptance_check,
                        },
                    )

            # Clear pending session data
            clear_pending_session(request)

            # Generate character with experience
            if interactive_mode:
                # Interactive mode - generate character with track but no years yet
                final_character = generate_character(
                    years=0,
                    chosen_track=chosen_track,  # None for auto, or specific track
                )
                final_character.prior_experience = None

                # Store character and go to interactive mode
                request.session["current_character"] = serialize_character(
                    final_character
                )
                request.session["interactive_character"] = serialize_character(
                    final_character
                )
                request.session["interactive_years"] = 0
                request.session["interactive_skills"] = []
                request.session["interactive_skill_points"] = 0
                request.session["interactive_yearly_results"] = []
                request.session["interactive_aging"] = {
                    "str": 0,
                    "dex": 0,
                    "int": 0,
                    "wis": 0,
                    "con": 0,
                }
                request.session["interactive_died"] = False
                request.session["interactive_track_name"] = (
                    final_character.skill_track.track.value
                )
                request.session["interactive_survivability"] = (
                    final_character.skill_track.survivability
                )
                request.session["interactive_initial_skills"] = list(
                    final_character.skill_track.initial_skills
                )
                request.session["interactive_return_to_generator"] = True

                attr_mods = final_character.attributes.get_all_modifiers()
                total_mod = sum(attr_mods.values())
                request.session["interactive_attr_modifiers"] = attr_mods
                request.session["interactive_total_modifier"] = total_mod

                return redirect("interactive")
            else:
                # Standard mode - add years of experience
                # Check if we already have experience (adding more years)
                existing_years = request.session.get("interactive_years", 0)
                existing_skills = request.session.get("interactive_skills", [])
                existing_yearly_results = request.session.get(
                    "interactive_yearly_results", []
                )
                existing_aging = request.session.get(
                    "interactive_aging",
                    {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0},
                )

                if existing_years > 0:
                    # Adding MORE experience to existing character
                    character = deserialize_character(pending_char)
                    skill_track = character.skill_track
                    total_modifier = sum(
                        character.attributes.get_all_modifiers().values()
                    )

                    # Reconstruct aging effects from session
                    aging_effects = AgingEffects(
                        str_penalty=existing_aging.get("str", 0),
                        dex_penalty=existing_aging.get("dex", 0),
                        int_penalty=existing_aging.get("int", 0),
                        wis_penalty=existing_aging.get("wis", 0),
                        con_penalty=existing_aging.get("con", 0),
                    )

                    # Roll additional years
                    new_yearly_results = []
                    new_skills = []
                    died = False
                    for i in range(years):
                        year_index = existing_years + i
                        year_result = roll_single_year(
                            skill_track=skill_track,
                            year_index=year_index,
                            total_modifier=total_modifier,
                            aging_effects=aging_effects,
                        )
                        new_skills.append(year_result.skill_gained)
                        new_yearly_results.append(
                            {
                                "year": year_result.year,
                                "skill": year_result.skill_gained,
                                "surv_roll": year_result.survivability_roll,
                                "surv_mod": year_result.survivability_modifier,
                                "surv_total": year_result.survivability_total,
                                "surv_target": year_result.survivability_target,
                                "survived": year_result.survived,
                            }
                        )
                        if not year_result.survived:
                            died = True
                            break

                    # Append to existing experience
                    all_skills = existing_skills + new_skills
                    all_yearly_results = existing_yearly_results + new_yearly_results
                    total_years = existing_years + len(new_yearly_results)

                    # Store updated experience data in session
                    request.session["interactive_years"] = total_years
                    request.session["interactive_skills"] = all_skills
                    request.session["interactive_yearly_results"] = all_yearly_results
                    request.session["interactive_died"] = died
                    request.session["interactive_aging"] = {
                        "str": aging_effects.str_penalty,
                        "dex": aging_effects.dex_penalty,
                        "int": aging_effects.int_penalty,
                        "wis": aging_effects.wis_penalty,
                        "con": aging_effects.con_penalty,
                    }

                    # Redirect back to prior experience page
                    return redirect("select_track")

                # First time adding experience - generate character with track
                final_character = generate_character(
                    years=years,
                    chosen_track=chosen_track,  # None for auto, or specific track
                )

                # Store character in session
                request.session["current_character"] = serialize_character(
                    final_character
                )

                # Build yearly results for display and store in session
                yearly_results = []
                skills = []
                if final_character.prior_experience:
                    skills = list(final_character.skill_track.initial_skills)
                    for yr in final_character.prior_experience.yearly_results:
                        skills.append(yr.skill_gained)
                        yearly_results.append(
                            {
                                "year": yr.year,
                                "skill": yr.skill_gained,
                                "surv_roll": yr.survivability_roll,
                                "surv_mod": yr.survivability_modifier,
                                "surv_total": yr.survivability_total,
                                "surv_target": yr.survivability_target,
                                "survived": yr.survived,
                            }
                        )

                # Store experience data in session
                request.session["interactive_years"] = years
                request.session["interactive_skills"] = skills
                request.session["interactive_yearly_results"] = yearly_results
                request.session["interactive_died"] = final_character.died
                request.session["interactive_track_name"] = (
                    final_character.skill_track.track.value
                )
                request.session["interactive_survivability"] = (
                    final_character.skill_track.survivability
                )

                # Keep pending session so we stay on prior experience page
                request.session["pending_character"] = serialize_character(
                    final_character
                )
                request.session["pending_str_mod"] = (
                    final_character.attributes.get_modifier("STR")
                )
                request.session["pending_dex_mod"] = (
                    final_character.attributes.get_modifier("DEX")
                )
                request.session["pending_int_mod"] = (
                    final_character.attributes.get_modifier("INT")
                )
                request.session["pending_wis_mod"] = (
                    final_character.attributes.get_modifier("WIS")
                )

                # Redirect back to prior experience page
                return redirect("select_track")

    # Get experience data if any
    years_completed = request.session.get("interactive_years", 0)
    skills = request.session.get("interactive_skills", [])
    yearly_results = request.session.get("interactive_yearly_results", [])
    died = request.session.get("interactive_died", False)
    track_name = request.session.get("interactive_track_name", "")

    return render(
        request,
        "generator/select_track.html",
        {
            "character": character,
            "track_info": track_info,
            "years_completed": years_completed,
            "current_age": 16 + years_completed,
            "skills": skills,
            "yearly_results": yearly_results,
            "died": died,
            "has_experience": years_completed > 0,
            "current_track": track_name,
        },
    )


def interactive(request):
    """Handle interactive prior experience mode."""
    # Check if we have an active interactive session
    char_data = request.session.get("interactive_character")
    if not char_data:
        return redirect("generator")

    years_completed = request.session.get("interactive_years", 0)
    skills = request.session.get("interactive_skills", [])
    skill_points = request.session.get("interactive_skill_points", 0)
    yearly_results_data = request.session.get("interactive_yearly_results", [])
    aging_data = request.session.get("interactive_aging", {})
    died = request.session.get("interactive_died", False)
    track_name = request.session.get("interactive_track_name", "")
    survivability = request.session.get("interactive_survivability", 0)
    initial_skills = request.session.get("interactive_initial_skills", [])
    attr_modifiers = request.session.get("interactive_attr_modifiers", {})
    total_modifier = request.session.get("interactive_total_modifier", 0)

    # Reconstruct character for display
    character = deserialize_character(char_data)
    current_age = 16 + years_completed
    latest_result = None

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "continue" and not died:
            # Roll another year
            skill_track = character.skill_track
            total_modifier = sum(character.attributes.get_all_modifiers().values())

            # Reconstruct aging effects
            aging_effects = AgingEffects(
                str_penalty=aging_data.get("str", 0),
                dex_penalty=aging_data.get("dex", 0),
                int_penalty=aging_data.get("int", 0),
                wis_penalty=aging_data.get("wis", 0),
                con_penalty=aging_data.get("con", 0),
            )

            year_result = roll_single_year(
                skill_track=skill_track,
                year_index=years_completed,
                total_modifier=total_modifier,
                aging_effects=aging_effects,
            )

            # Update session state
            years_completed += 1
            skill_points += 1

            # Grant initial skills after completing first year (age 17)
            if years_completed == 1:
                skills.extend(initial_skills)

            skills.append(year_result.skill_gained)

            # Store the year result
            yearly_results_data.append(
                {
                    "year": year_result.year,
                    "skill": year_result.skill_gained,
                    "skill_roll": year_result.skill_roll,
                    "surv_roll": year_result.survivability_roll,
                    "surv_mod": year_result.survivability_modifier,
                    "surv_total": year_result.survivability_total,
                    "surv_target": year_result.survivability_target,
                    "survived": year_result.survived,
                    "aging": year_result.aging_penalties,
                }
            )

            # Update aging in session
            request.session["interactive_aging"] = {
                "str": aging_effects.str_penalty,
                "dex": aging_effects.dex_penalty,
                "int": aging_effects.int_penalty,
                "wis": aging_effects.wis_penalty,
                "con": aging_effects.con_penalty,
            }

            if not year_result.survived:
                died = True
                request.session["interactive_died"] = True

            request.session["interactive_years"] = years_completed
            request.session["interactive_skills"] = skills
            request.session["interactive_skill_points"] = skill_points
            request.session["interactive_yearly_results"] = yearly_results_data

            latest_result = year_result
            current_age = 16 + years_completed

        elif action == "stop":
            # Go back to generator to add more experience
            if "interactive_return_to_generator" in request.session:
                del request.session["interactive_return_to_generator"]
            request.session.modified = True
            return redirect("generator")

        elif action == "new":
            # Clear session and start over
            clear_interactive_session(request)
            return redirect("generator")

    return render(
        request,
        "generator/interactive.html",
        {
            "character": character,
            "years_completed": years_completed,
            "current_age": current_age,
            "yearly_results": yearly_results_data,
            "latest_result": latest_result,
            "skill_points": skill_points,
            "skills": skills,
            "can_continue": not died,
            "died": died,
            "aging": aging_data,
            "mode": "interactive",
            "track_name": track_name,
            "survivability": survivability,
            "initial_skills": initial_skills,
            "attr_modifiers": attr_modifiers,
            "total_modifier": total_modifier,
        },
    )
