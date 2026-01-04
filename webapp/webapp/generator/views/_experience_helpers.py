"""
Helper functions for prior experience views.

These are internal helpers for managing track selection and experience rolling.
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

from pillars import generate_character
from pillars.attributes import (
    roll_single_year,
    SkillTrack,
    TrackType,
    AgingEffects,
    CraftType,
    MagicSchool,
    roll_skill_track,
    create_skill_track_for_choice,
    get_aging_effects_for_age,
)

from ..models import SavedCharacter
from .helpers import validate_experience_years
from .serialization import (
    deserialize_character,
    store_current_character,
    migrate_track_name,
)


def get_or_create_skill_track(char_data, character, chosen_track_name):
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
        # Use existing track (migrate old track names if needed)
        track_data = char_data["skill_track"]
        migrated_track = migrate_track_name(track_data["track"])
        skill_track = SkillTrack(
            track=TrackType(migrated_track),
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

    # Create new track - use selected track from radio button if provided
    if chosen_track_name:
        try:
            # Track keys come in lowercase from the form, enum names are uppercase
            chosen_track = TrackType[chosen_track_name.upper()]
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


def roll_experience_years(
    skill_track,
    years,
    existing_years,
    existing_skills,
    total_modifier,
    aging_effects,
    base_age=16,
):
    """Roll experience for the specified number of years.

    Args:
        skill_track: The character's skill track
        years: Number of years to roll
        existing_years: Years of experience already completed
        existing_skills: Skills already gained
        total_modifier: Sum of all attribute modifiers
        aging_effects: Current aging effects
        base_age: Character's age before any prior experience (default 16)

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
            starting_age=base_age,
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


def update_experience_session(
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

    # Update char_data with interactive experience data
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

    # Clear skill_points_data so it gets rebuilt with updated skills
    char_data.pop("skill_points_data", None)

    # Update age based on base_age + years of experience
    char_data["age"] = char_data.get("base_age", 16) + total_years

    request.session["current_character"] = char_data
    request.session.modified = True
    # Force session save for AJAX requests
    request.session.save()


def sync_experience_to_database(
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
        # Clear skill_points_data so it gets rebuilt with updated skills
        saved_char.character_data.pop("skill_points_data", None)
        saved_char.save()
    except SavedCharacter.DoesNotExist:
        pass


def handle_add_experience(request):
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

        # Capture manually entered age as base_age (before any prior experience)
        char_age = request.POST.get("char_age", "").strip()
        if char_age:
            try:
                age_val = int(char_age)
                # Store the user's age minus any existing experience years
                existing_years = char_data.get("interactive_years", 0)
                # base_age is the age before any prior experience was added
                char_data["base_age"] = age_val - existing_years
                char_data["age"] = age_val
            except ValueError:
                pass

    character = deserialize_character(char_data)

    # Get form parameters
    years = validate_experience_years(request.POST.get("years"), default=5)
    chosen_track_name = request.POST.get("chosen_track", "")

    # Get or create skill track
    skill_track, char_data, error = get_or_create_skill_track(
        char_data, character, chosen_track_name
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

    # Get base_age (user's manually set age before experience, defaults to 16)
    base_age = char_data.get("base_age", 16)

    # Reconstruct aging effects
    if existing_years == 0 and base_age > 16:
        # First time adding experience with custom age - calculate aging from base_age
        aging_effects = get_aging_effects_for_age(base_age)
    else:
        # Continue with existing aging effects
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
    new_skills, new_yearly_results, died, aging_effects = roll_experience_years(
        skill_track,
        years,
        existing_years,
        existing_skills,
        total_modifier,
        aging_effects,
        base_age=base_age,
    )

    # Update session
    update_experience_session(
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
    sync_experience_to_database(
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


def handle_add_experience_ajax(request):
    """Handle adding experience years via AJAX, returning JSON response."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    char_data = request.session.get("current_character")
    if not char_data:
        character = generate_character(years=0, skip_track=True)
        store_current_character(request, character)
        char_data = request.session.get("current_character")

    # Preserve name from form submission
    char_name = request.POST.get("char_name", "").strip()
    if char_name:
        char_data["name"] = char_name

    # Capture manually entered age as base_age - but only on FIRST experience call
    # (when there's no existing experience yet, otherwise we'd mess up the calculation)
    char_age = request.POST.get("char_age", "").strip()
    existing_interactive_years = char_data.get("interactive_years", 0)
    if char_age and existing_interactive_years == 0:
        try:
            age_val = int(char_age)
            char_data["base_age"] = age_val
            char_data["age"] = age_val
        except ValueError:
            pass

    character = deserialize_character(char_data)

    # Get form parameters
    years = validate_experience_years(request.POST.get("years"), default=5)
    chosen_track_name = request.POST.get("chosen_track", "")

    # Get or create skill track
    skill_track, char_data, error = get_or_create_skill_track(
        char_data, character, chosen_track_name
    )
    if error:
        return JsonResponse({"error": error}, status=400)

    # Get existing experience data from char_data (more reliable than session keys)
    existing_years = char_data.get("interactive_years", 0)
    existing_skills = char_data.get("interactive_skills", [])
    existing_yearly_results = char_data.get("interactive_yearly_results", [])
    existing_aging = char_data.get(
        "interactive_aging", {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0}
    )
    died = char_data.get("interactive_died", False)

    if died:
        return JsonResponse({"error": "Character is deceased"}, status=400)

    # Get base_age
    base_age = char_data.get("base_age", 16)

    # Reconstruct aging effects
    if existing_years == 0 and base_age > 16:
        aging_effects = get_aging_effects_for_age(base_age)
    else:
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
    new_skills, new_yearly_results, died, aging_effects = roll_experience_years(
        skill_track,
        years,
        existing_years,
        existing_skills,
        total_modifier,
        aging_effects,
        base_age=base_age,
    )

    # Update session
    update_experience_session(
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
    sync_experience_to_database(
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

    # Build response with new experience data
    total_years = existing_years + len(new_yearly_results)
    current_age = base_age + total_years
    all_skills = existing_skills + new_skills

    return JsonResponse(
        {
            "success": True,
            "new_yearly_results": new_yearly_results,
            "new_skills": new_skills,
            "all_skills": all_skills,
            "total_years": total_years,
            "current_age": current_age,
            "died": died,
            "track_name": skill_track.track.value,
            "aging": {
                "str": aging_effects.str_penalty,
                "dex": aging_effects.dex_penalty,
                "int": aging_effects.int_penalty,
                "wis": aging_effects.wis_penalty,
                "con": aging_effects.con_penalty,
            },
        }
    )
