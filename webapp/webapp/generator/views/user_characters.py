"""
User character management views for the Pillars Character Generator.

This module handles user's saved characters:
- save_character: AJAX save current character
- my_characters: List saved characters (unified view for players and DMs/admins)
- load_character: Load character into session
- delete_character: Delete a saved character
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import SavedCharacter


@login_required
@require_POST
def save_character(request):
    """Save the current character for the logged-in user."""
    char_data = request.session.get("current_character")
    if not char_data:
        return JsonResponse(
            {"success": False, "error": "No character to save"}, status=400
        )

    # Get character name from the data or generate one
    name = request.POST.get("name", "")
    if not name:
        # Try to extract name from provenance or use a default
        name = (
            f"Character {SavedCharacter.objects.filter(user=request.user).count() + 1}"
        )

    # Get description, age, and race from the data
    description = char_data.get("description", "")
    age = char_data.get("age")
    race = char_data.get("race", "")

    # Include experience data if present
    save_data = dict(char_data)
    save_data["interactive_years"] = request.session.get("interactive_years", 0)
    save_data["interactive_skills"] = request.session.get("interactive_skills", [])
    save_data["interactive_yearly_results"] = request.session.get(
        "interactive_yearly_results", []
    )
    save_data["interactive_aging"] = request.session.get("interactive_aging", {})
    save_data["interactive_died"] = request.session.get("interactive_died", False)

    # Create or update the saved character
    saved_char = SavedCharacter.objects.create(
        user=request.user,
        name=name,
        age=age,
        race=race,
        description=description,
        character_data=save_data,
    )

    return JsonResponse({"success": True, "id": saved_char.id, "name": saved_char.name})


@login_required
def my_characters(request):
    """List saved characters - unified view for players and DMs/admins.

    - DMs/Admins see all players in dropdown and can view all characters
    - Regular players see only themselves in dropdown (their characters only)
    """
    # Check if user is DM or admin
    is_privileged = hasattr(request.user, "profile") and (
        request.user.profile.is_dm or request.user.profile.is_admin
    )

    # Get filter parameter
    player_filter = request.GET.get("player", "")

    # Build the list of users for the dropdown
    if is_privileged:
        # DMs/admins see all users who have characters
        users_with_characters = (
            User.objects.filter(saved_characters__isnull=False)
            .distinct()
            .order_by("username")
        )
    else:
        # Regular players only see themselves
        users_with_characters = User.objects.filter(id=request.user.id)
        # Force filter to current user for non-privileged users
        player_filter = request.user.username

    # Get characters based on filter
    if player_filter:
        characters = (
            SavedCharacter.objects.filter(user__username=player_filter)
            .select_related("user")
            .order_by("-updated_at")
        )
    elif is_privileged:
        # DMs/admins with no filter see all characters
        characters = (
            SavedCharacter.objects.all().select_related("user").order_by("-updated_at")
        )
    else:
        # Regular players see only their own
        characters = SavedCharacter.objects.filter(user=request.user).order_by(
            "-updated_at"
        )

    return render(
        request,
        "generator/my_characters.html",
        {
            "characters": characters,
            "users_with_characters": users_with_characters,
            "player_filter": player_filter,
            "is_privileged": is_privileged,
        },
    )


@login_required
def load_character(request, char_id):
    """Load a saved character into the session."""
    try:
        saved_char = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")
        return redirect("my_characters")

    # Load character data into session
    char_data = saved_char.character_data.copy()
    # Include model fields (name, age, race, description) in session
    char_data["name"] = saved_char.name
    char_data["age"] = saved_char.age
    char_data["race"] = saved_char.race
    char_data["description"] = saved_char.description
    request.session["current_character"] = {
        k: v for k, v in char_data.items() if not k.startswith("interactive_")
    }

    # Load experience data if present
    request.session["interactive_years"] = char_data.get("interactive_years", 0)
    request.session["interactive_skills"] = char_data.get("interactive_skills", [])
    request.session["interactive_yearly_results"] = char_data.get(
        "interactive_yearly_results", []
    )
    request.session["interactive_aging"] = char_data.get("interactive_aging", {})
    request.session["interactive_died"] = char_data.get("interactive_died", False)
    request.session.modified = True

    messages.success(request, f"Loaded character: {saved_char.name}")
    return redirect("generator")


@login_required
@require_POST
def delete_character(request, char_id):
    """Delete a saved character."""
    try:
        saved_char = SavedCharacter.objects.get(id=char_id, user=request.user)
        name = saved_char.name
        saved_char.delete()
        messages.success(request, f"Deleted character: {name}")
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")

    return redirect("my_characters")
