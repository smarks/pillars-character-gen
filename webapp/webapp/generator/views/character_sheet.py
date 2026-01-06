"""
Character sheet views for the Pillars Character Generator.

This module handles character sheet display and editing:
- character_sheet: Display editable character sheet
- update_character: AJAX endpoint for saved character updates
- update_session_character: AJAX endpoint for session character updates
- add_experience_to_character: Add experience to saved character
"""

import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.safestring import mark_safe

from pillars.attributes import (
    roll_single_year,
    SkillTrack,
    TrackType,
    AgingEffects,
    CraftType,
    MagicSchool,
    get_track_availability,
    create_skill_track_for_choice,
)

from ..models import SavedCharacter
from .helpers import (
    build_track_info,
    validate_experience_years,
    normalize_skill_name,
    format_attribute_display,
    get_attribute_modifier,
)
from ._character_helpers import (
    build_skill_points_from_char_data,
    allocate_skill_point,
    deallocate_skill_point,
    recalculate_derived,
    calculate_track_info,
    calculate_adjusted_attributes,
)

# Mapping from old track names to new consolidated track names
# After track consolidation: Army/Navy -> Campaigner, Worker -> Laborer
LEGACY_TRACK_MAPPING = {
    "Army": "Campaigner",
    "Navy": "Campaigner",
    "Worker": "Laborer",
    "Officer": "Campaigner",  # Officer was removed, closest is Campaigner
}


def migrate_track_name(track_name):
    """Convert old track names to new consolidated names."""
    return LEGACY_TRACK_MAPPING.get(track_name, track_name)


@login_required
def character_sheet(request, char_id):
    """Display editable character sheet."""
    profile = getattr(request.user, "profile", None)
    is_dm_or_admin = (
        profile and (profile.is_dm or profile.is_admin) if profile else False
    )

    try:
        if is_dm_or_admin:
            # DM/admin can view any character
            character = SavedCharacter.objects.select_related("user").get(id=char_id)
        else:
            character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")
        return redirect("my_characters")

    # Check if this is the owner or a DM viewing someone else's character
    is_owner = character.user == request.user

    char_data = character.character_data.copy()
    # Include model fields (name, description) in char_data for template
    char_data["name"] = character.name
    char_data["description"] = character.description
    attrs = char_data.get("attributes", {})

    # Build skill points data (migrates legacy if needed)
    char_skills = build_skill_points_from_char_data(char_data)
    skills_with_details = char_skills.get_skills_with_details()
    skills = char_skills.get_display_list()
    free_skill_points = char_skills.free_points
    total_xp = char_skills.total_xp

    # Prior experience data
    yearly_results = char_data.get("interactive_yearly_results", [])
    years_served = char_data.get("interactive_years", 0)
    died = char_data.get("interactive_died", False)

    # Build track info for display (always show for reference)
    str_mod = get_attribute_modifier(attrs.get("STR", 10))
    dex_mod = get_attribute_modifier(attrs.get("DEX", 10))
    int_mod = get_attribute_modifier(attrs.get("INT", 10))
    wis_mod = get_attribute_modifier(attrs.get("WIS", 10))
    chr_mod = get_attribute_modifier(attrs.get("CHR", 10))

    social_class = char_data.get("provenance_social_class", "Commoner")
    wealth_level = char_data.get("wealth_level", "Moderate")

    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod, chr_mod, social_class, wealth_level
    )
    track_info = build_track_info(track_availability)

    # Extract aging penalties
    aging = char_data.get("interactive_aging", {})
    aging_penalties = {
        "str": aging.get("str", 0),
        "dex": aging.get("dex", 0),
        "int": aging.get("int", 0),
        "wis": aging.get("wis", 0),
        "con": aging.get("con", 0),
    }

    # Calculate adjusted attributes (base - aging penalties)
    adjusted_attrs = calculate_adjusted_attributes(char_data)

    # Serialize equipment data for JavaScript
    equipment_json = mark_safe(json.dumps(char_data.get("equipment", {})))

    return render(
        request,
        "generator/character_sheet.html",
        {
            "character": character,
            "char_data": char_data,
            "skills": skills,
            "skills_with_details": skills_with_details,
            "free_skill_points": free_skill_points,
            "total_xp": total_xp,
            # Attribute display values
            "str_display": format_attribute_display(attrs.get("STR", 10)),
            "dex_display": format_attribute_display(attrs.get("DEX", 10)),
            "int_display": format_attribute_display(attrs.get("INT", 10)),
            "wis_display": format_attribute_display(attrs.get("WIS", 10)),
            "con_display": format_attribute_display(attrs.get("CON", 10)),
            "chr_display": format_attribute_display(attrs.get("CHR", 10)),
            # Attribute modifiers
            "str_mod": get_attribute_modifier(attrs.get("STR", 10)),
            "dex_mod": get_attribute_modifier(attrs.get("DEX", 10)),
            "int_mod": get_attribute_modifier(attrs.get("INT", 10)),
            "wis_mod": get_attribute_modifier(attrs.get("WIS", 10)),
            "con_mod": get_attribute_modifier(attrs.get("CON", 10)),
            "chr_mod": get_attribute_modifier(attrs.get("CHR", 10)),
            # Adjusted values (after aging)
            "str_adjusted": adjusted_attrs.get("str_adjusted"),
            "dex_adjusted": adjusted_attrs.get("dex_adjusted"),
            "int_adjusted": adjusted_attrs.get("int_adjusted"),
            "wis_adjusted": adjusted_attrs.get("wis_adjusted"),
            "con_adjusted": adjusted_attrs.get("con_adjusted"),
            "chr_adjusted": adjusted_attrs.get("chr_adjusted"),
            "str_adj_mod": adjusted_attrs.get("str_adj_mod"),
            "dex_adj_mod": adjusted_attrs.get("dex_adj_mod"),
            "int_adj_mod": adjusted_attrs.get("int_adj_mod"),
            "wis_adj_mod": adjusted_attrs.get("wis_adj_mod"),
            "con_adj_mod": adjusted_attrs.get("con_adj_mod"),
            "chr_adj_mod": adjusted_attrs.get("chr_adj_mod"),
            # Sources of attribute modifications
            "str_sources": adjusted_attrs.get("str_sources", ""),
            "dex_sources": adjusted_attrs.get("dex_sources", ""),
            "int_sources": adjusted_attrs.get("int_sources", ""),
            "wis_sources": adjusted_attrs.get("wis_sources", ""),
            "con_sources": adjusted_attrs.get("con_sources", ""),
            "chr_sources": adjusted_attrs.get("chr_sources", ""),
            "yearly_results": yearly_results,
            "years_served": years_served,
            "current_age": char_data.get("base_age", 16) + years_served,
            "died": died,
            "track_info": track_info,
            "is_owner": is_owner,
            "character_owner": character.user,
            "aging_penalties": aging_penalties,
            "equipment_json": equipment_json,
        },
    )


@login_required
@require_POST
def update_character(request, char_id):
    """API endpoint to update a single field on a character."""
    try:
        character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Character not found"}, status=404
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    field = data.get("field")
    value = data.get("value")
    action = data.get("action")  # For skills: 'add', 'remove', 'edit'

    if not field:
        return JsonResponse(
            {"success": False, "error": "No field specified"}, status=400
        )

    char_data = character.character_data

    # Handle different field types
    computed = {}

    if field == "name":
        # Update the model's name field
        character.name = value
    elif field == "age":
        # Update the model's age field (convert to int if provided)
        if value:
            try:
                character.age = int(value)
            except (ValueError, TypeError):
                character.age = None
        else:
            character.age = None
    elif field == "race":
        # Update the model's race field
        character.race = value or ""
    elif field == "description":
        # Update the model's description field
        character.description = value
    elif field == "skills":
        # Handle skills list operations using skill points system
        if action == "add":
            # Use skill points system to add the skill

            char_skills = build_skill_points_from_char_data(char_data)

            # Normalize the skill name
            normalized_skill = normalize_skill_name(value)

            # If we have free points, allocate one to this skill
            if char_skills.free_points > 0:
                char_skills.allocate_point(normalized_skill)
            else:
                # No free points - add an automatic point (for initial skills etc.)
                char_skills.add_automatic_point(normalized_skill)

            # Save back to char_data
            char_data["skill_points_data"] = char_skills.to_dict()

            # Return updated skills for display
            computed["skills"] = char_skills.get_skills_with_details()
            computed["free_skill_points"] = char_skills.free_points
            computed["total_xp"] = char_skills.total_xp
        elif action == "remove":
            # Handle skill removal - deallocate points if possible

            char_skills = build_skill_points_from_char_data(char_data)
            skill_name = normalize_skill_name(value)
            char_skills.deallocate_point(skill_name)
            char_data["skill_points_data"] = char_skills.to_dict()
            computed["skills"] = char_skills.get_skills_with_details()
            computed["free_skill_points"] = char_skills.free_points
        elif action == "rename":
            # Rename a skill's display name
            old_name = data.get("old_name", "")
            new_name = data.get("new_name", "")
            if not old_name or not new_name:
                return JsonResponse(
                    {"success": False, "error": "old_name and new_name required"},
                    status=400,
                )
            char_skills = build_skill_points_from_char_data(char_data)
            success = char_skills.rename_skill(old_name, new_name)
            if success:
                char_data["skill_points_data"] = char_skills.to_dict()
                computed["skills"] = char_skills.get_skills_with_details()
                computed["free_skill_points"] = char_skills.free_points
            else:
                return JsonResponse(
                    {"success": False, "error": f"Skill '{old_name}' not found"},
                    status=400,
                )
    elif field.startswith("attributes."):
        # Handle nested attribute fields
        attr_name = field.split(".")[1]
        if attr_name in ["STR", "DEX", "INT", "WIS", "CON", "CHR"]:
            # Store value as-is (int or string like "18.20")
            char_data["attributes"][attr_name] = value
            # Recalculate derived values
            computed.update(recalculate_derived(char_data))
            # Return updated modifier using our enhanced function
            mod = get_attribute_modifier(value)
            computed[f"{attr_name.lower()}_mod"] = mod
    elif field == "notes":
        char_data["notes"] = value
    elif field in [
        "appearance",
        "height",
        "weight",
        "provenance",
        "location",
        "literacy",
        "wealth",
    ]:
        char_data[field] = value
    elif field == "skill_points":
        # Handle skill point allocation/deallocation
        skill_name = data.get("skill_name", "")
        if action == "allocate":
            success, error, skills = allocate_skill_point(char_data, skill_name)
            if not success:
                return JsonResponse({"success": False, "error": error}, status=400)
            char_skills = build_skill_points_from_char_data(char_data)
            computed["skills"] = skills
            computed["skills_with_details"] = char_skills.get_skills_with_details()
            computed["free_skill_points"] = char_skills.free_points
            computed["total_xp"] = char_skills.total_xp
        elif action == "deallocate":
            success, error, skills = deallocate_skill_point(char_data, skill_name)
            if not success:
                return JsonResponse({"success": False, "error": error}, status=400)
            char_skills = build_skill_points_from_char_data(char_data)
            computed["skills"] = skills
            computed["skills_with_details"] = char_skills.get_skills_with_details()
            computed["free_skill_points"] = char_skills.free_points
            computed["total_xp"] = char_skills.total_xp
        else:
            return JsonResponse(
                {"success": False, "error": f"Unknown skill_points action: {action}"},
                status=400,
            )
    else:
        return JsonResponse(
            {"success": False, "error": f"Unknown field: {field}"}, status=400
        )

    # Save changes
    character.character_data = char_data
    character.save()

    result = {"success": True}
    if computed:
        result["computed"] = computed
    if action == "add":
        result["index"] = computed.get("index", 0)

    return JsonResponse(result)


def update_session_character(request):
    """API endpoint to update a single field on the session-based character."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    char_data = request.session.get("current_character")
    if not char_data:
        return JsonResponse(
            {"success": False, "error": "No character in session"}, status=404
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    field = data.get("field")
    value = data.get("value")
    action = data.get("action")  # For skills: 'add', 'remove', 'edit'

    if not field:
        return JsonResponse(
            {"success": False, "error": "No field specified"}, status=400
        )

    computed = {}
    # Track whether we need to recalculate track availability
    recalc_tracks = False

    if field == "name":
        char_data["name"] = value
    elif field == "skills":
        # Handle skills list operations using skill points system
        if action == "add":

            char_skills = build_skill_points_from_char_data(char_data)
            normalized_skill = normalize_skill_name(value)

            # If we have free points, allocate one to this skill
            if char_skills.free_points > 0:
                char_skills.allocate_point(normalized_skill)
            else:
                # No free points - add an automatic point
                char_skills.add_automatic_point(normalized_skill)

            char_data["skill_points_data"] = char_skills.to_dict()
            computed["skills"] = char_skills.get_skills_with_details()
            computed["free_skill_points"] = char_skills.free_points
            computed["total_xp"] = char_skills.total_xp
        elif action == "rename":
            # Rename a skill's display name
            old_name = data.get("old_name", "")
            new_name = data.get("new_name", "")
            if not old_name or not new_name:
                return JsonResponse(
                    {"success": False, "error": "old_name and new_name required"},
                    status=400,
                )
            char_skills = build_skill_points_from_char_data(char_data)
            success = char_skills.rename_skill(old_name, new_name)
            if success:
                char_data["skill_points_data"] = char_skills.to_dict()
                computed["skills"] = char_skills.get_skills_with_details()
                computed["free_skill_points"] = char_skills.free_points
            else:
                return JsonResponse(
                    {"success": False, "error": f"Skill '{old_name}' not found"},
                    status=400,
                )
    elif field.startswith("attributes."):
        attr_name = field.split(".")[1]
        if attr_name in ["STR", "DEX", "INT", "WIS", "CON", "CHR"]:
            char_data["attributes"][attr_name] = value
            # Ensure aging data is included in char_data for adjusted calculations
            if "interactive_aging" not in char_data:
                char_data["interactive_aging"] = request.session.get(
                    "interactive_aging",
                    {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0},
                )
            computed.update(recalculate_derived(char_data))
            mod = get_attribute_modifier(value)
            computed[f"{attr_name.lower()}_mod"] = mod
            recalc_tracks = True  # Attributes affect track availability
    elif field == "notes":
        char_data["notes"] = value
    elif field in [
        "appearance",
        "height",
        "weight",
        "provenance",
        "location",
        "literacy",
    ]:
        char_data[field] = value
    elif field == "wealth_level":
        char_data["wealth_level"] = value
        # Update display wealth too
        wealth_map = {
            "Destitute": "Destitute",
            "Poor": "Poor",
            "Moderate": "Moderate",
            "Comfortable": "Comfortable",
            "Rich": "Rich",
        }
        char_data["wealth"] = wealth_map.get(value, value)
        recalc_tracks = (
            True  # Wealth affects track availability (Officer requires Rich)
        )
    else:
        return JsonResponse(
            {"success": False, "error": f"Unknown field: {field}"}, status=400
        )

    # Recalculate track availability if needed and character doesn't have a track yet
    if recalc_tracks and not char_data.get("skill_track"):
        computed["track_info"] = calculate_track_info(char_data)

    # Save to session
    request.session["current_character"] = char_data
    request.session.modified = True

    result = {"success": True}
    if computed:
        result["computed"] = computed

    return JsonResponse(result)


@login_required
@require_POST
def add_experience_to_character(request, char_id):
    """Add prior experience years to a saved character."""
    try:
        character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")
        return redirect("my_characters")

    interactive_mode = request.POST.get("interactive_mode") == "on"
    years = validate_experience_years(request.POST.get("years"), default=5)
    track_choice = request.POST.get("track", "auto")

    char_data = character.character_data

    # Check if character has died - cannot add more experience
    if char_data.get("interactive_died", False):
        messages.error(request, "Cannot add experience to a dead character.")
        return redirect("character_sheet", char_id=char_id)

    attrs = char_data.get("attributes", {})

    # Get attribute modifiers
    str_mod = get_attribute_modifier(attrs.get("STR", 10))
    dex_mod = get_attribute_modifier(attrs.get("DEX", 10))
    int_mod = get_attribute_modifier(attrs.get("INT", 10))
    wis_mod = get_attribute_modifier(attrs.get("WIS", 10))
    con_mod = get_attribute_modifier(attrs.get("CON", 10))
    total_modifier = str_mod + dex_mod + int_mod + wis_mod + con_mod

    # Get or create skill track
    if char_data.get("skill_track"):
        # Use existing skill track (migrate old track names if needed)
        track_data = char_data["skill_track"]
        migrated_track_name = migrate_track_name(track_data["track"])
        skill_track = SkillTrack(
            track=TrackType(migrated_track_name),
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
        # Update stored track name if it was migrated
        if migrated_track_name != track_data["track"]:
            char_data["skill_track"]["track"] = migrated_track_name
    else:
        # Create new skill track
        social_class = char_data.get("provenance_social_class", "Commoner")
        sub_class = char_data.get("provenance_sub_class", "Laborer")
        wealth_level = char_data.get("wealth_level", "Moderate")

        chosen_track = None
        if track_choice != "auto":
            try:
                chosen_track = TrackType[track_choice]
            except KeyError:
                pass

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

        if skill_track is None or skill_track.track is None:
            messages.error(
                request,
                "Could not create skill track. Try selecting a different track.",
            )
            return redirect("character_sheet", char_id=char_id)

        # Save track to character data
        char_data["skill_track"] = {
            "track": skill_track.track.value,
            "survivability": skill_track.survivability,
            "initial_skills": list(skill_track.initial_skills),
            "craft_type": (
                skill_track.craft_type.value if skill_track.craft_type else None
            ),
            "magic_school": (
                skill_track.magic_school.value if skill_track.magic_school else None
            ),
            "magic_school_rolls": skill_track.magic_school_rolls,
        }

    # Handle interactive mode - set up session and redirect to interactive page
    if interactive_mode:
        # Save track to character before redirecting
        character.character_data = char_data
        character.save()

        # Set up session for interactive mode
        request.session["interactive_character"] = char_data
        request.session["current_saved_character_id"] = char_id

        # Get existing experience data for session
        existing_years = char_data.get("interactive_years", 0)
        existing_skills = char_data.get("interactive_skills", [])
        existing_yearly_results = char_data.get("interactive_yearly_results", [])
        existing_aging = char_data.get(
            "interactive_aging", {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0}
        )

        # Set up initial skills if this is the first experience
        if existing_years == 0:
            existing_skills = list(skill_track.initial_skills)

        # Set all session variables needed for interactive mode
        request.session["interactive_years"] = existing_years
        request.session["interactive_skills"] = existing_skills
        request.session["interactive_skill_points"] = existing_years  # 1 point per year
        request.session["interactive_yearly_results"] = existing_yearly_results
        request.session["interactive_aging"] = existing_aging
        request.session["interactive_died"] = char_data.get("interactive_died", False)
        request.session["interactive_track_name"] = skill_track.track.value
        request.session["interactive_survivability"] = skill_track.survivability
        request.session["interactive_initial_skills"] = list(skill_track.initial_skills)
        request.session["interactive_total_modifier"] = (
            get_attribute_modifier(attrs.get("STR", 10))
            + get_attribute_modifier(attrs.get("DEX", 10))
            + get_attribute_modifier(attrs.get("INT", 10))
            + get_attribute_modifier(attrs.get("WIS", 10))
            + get_attribute_modifier(attrs.get("CON", 10))
        )
        request.session.modified = True

        return redirect("interactive")

    # Get existing experience data
    existing_years = char_data.get("interactive_years", 0)
    existing_skills = char_data.get("interactive_skills", [])
    existing_yearly_results = char_data.get("interactive_yearly_results", [])
    existing_aging = char_data.get(
        "interactive_aging", {"str": 0, "dex": 0, "int": 0, "wis": 0, "con": 0}
    )

    # Reconstruct aging effects
    aging_effects = AgingEffects(
        str_penalty=existing_aging.get("str", 0),
        dex_penalty=existing_aging.get("dex", 0),
        int_penalty=existing_aging.get("int", 0),
        wis_penalty=existing_aging.get("wis", 0),
        con_penalty=existing_aging.get("con", 0),
    )

    # Roll new years
    new_skills = []
    new_yearly_results = []
    died = char_data.get("interactive_died", False)

    # Add initial skills if this is the first experience
    if existing_years == 0:
        existing_skills = list(skill_track.initial_skills)

    for i in range(years):
        if died:
            break

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

    # Update character data
    char_data["interactive_years"] = existing_years + len(new_yearly_results)
    char_data["interactive_skills"] = existing_skills + new_skills
    char_data["interactive_yearly_results"] = (
        existing_yearly_results + new_yearly_results
    )
    char_data["interactive_died"] = died
    char_data["interactive_aging"] = {
        "str": aging_effects.str_penalty,
        "dex": aging_effects.dex_penalty,
        "int": aging_effects.int_penalty,
        "wis": aging_effects.wis_penalty,
        "con": aging_effects.con_penalty,
    }

    # Update skill_points_data with new skills from experience
    # This is needed because build_skill_points_from_char_data returns early
    # if skill_points_data already exists
    if new_skills:
        char_skills = build_skill_points_from_char_data(char_data)
        for skill in new_skills:
            char_skills.add_automatic_point(skill)
        char_data["skill_points_data"] = char_skills.to_dict()

    # Also add initial skills if this was the first experience
    if existing_years == 0 and skill_track.initial_skills:
        char_skills = build_skill_points_from_char_data(char_data)
        for skill in skill_track.initial_skills:
            # Only add if not already present (avoid duplicates)
            if skill not in [s["name"] for s in char_skills.get_skills_with_details()]:
                char_skills.add_automatic_point(skill)
        char_data["skill_points_data"] = char_skills.to_dict()

    # Save character
    character.character_data = char_data
    character.save()

    if died and new_yearly_results:
        messages.warning(
            request, f'Character died during year {new_yearly_results[-1]["year"]}!'
        )
    elif died:
        messages.warning(
            request, "Character is already dead. No experience can be added."
        )
    elif new_yearly_results:
        messages.success(
            request, f"Added {len(new_yearly_results)} years of experience."
        )
    else:
        messages.info(request, "No experience years were added.")

    return redirect("character_sheet", char_id=char_id)
