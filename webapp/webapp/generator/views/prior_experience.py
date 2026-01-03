"""
Prior experience views for the Pillars Character Generator.

This module handles the track selection and experience rolling:
- select_track: Prior experience page with track selection
- interactive: Year-by-year interactive mode
"""

from django.shortcuts import render, redirect

from pillars import generate_character
from pillars.attributes import (
    roll_single_year,
    TrackType,
    AgingEffects,
    get_track_availability,
    create_skill_track_for_choice,
)

from .session import clear_pending_session, clear_interactive_session
from .helpers import build_track_info, validate_experience_years
from .serialization import serialize_character, deserialize_character
from ._experience_helpers import (
    roll_experience_years,
)


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
    chr_mod = request.session.get("pending_chr_mod", 0)
    social_class = request.session.get("pending_social_class", "Commoner")
    sub_class = request.session.get("pending_sub_class", "Laborer")
    wealth_level = request.session.get("pending_wealth_level", "Moderate")

    # Get track availability
    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod, chr_mod, social_class, wealth_level
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
            years = (
                validate_experience_years(request.POST.get("years"), default=5)
                if not interactive_mode
                else 0
            )
            chosen_track_name = request.POST.get("chosen_track", "")

            # Determine the track to use (always use selected track)
            chosen_track = None
            if chosen_track_name:
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

                # Check acceptance for chosen track
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
                    new_skills, new_yearly_results, died, aging_effects = (
                        roll_experience_years(
                            skill_track,
                            years,
                            existing_years,
                            existing_skills,
                            total_modifier,
                            aging_effects,
                        )
                    )

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

    # Get base_age from pending_char or default to 16
    base_age = pending_char.get("base_age", 16) if pending_char else 16

    return render(
        request,
        "generator/select_track.html",
        {
            "character": character,
            "track_info": track_info,
            "years_completed": years_completed,
            "current_age": base_age + years_completed,
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
    base_age = char_data.get("base_age", 16)
    current_age = base_age + years_completed
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
                starting_age=base_age,
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
            current_age = base_age + years_completed

        elif action == "stop":
            # Go back to where we came from
            if "interactive_return_to_generator" in request.session:
                del request.session["interactive_return_to_generator"]
            request.session.modified = True
            # If we came from a saved character, redirect back to it
            saved_char_id = request.session.get("current_saved_character_id")
            if saved_char_id:
                return redirect("character_sheet", char_id=saved_char_id)
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
