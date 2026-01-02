"""
Authentication views for the Pillars Character Generator.

This module handles user authentication:
- register_view: User registration
- login_view: User login
- logout_view: User logout
- my_profile: User profile management
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from ..models import SavedCharacter, UserProfile
from .forms import RegistrationForm


def save_session_character_for_user(request, user):
    """Save the current session character to the database for a user.

    Called after login/registration to preserve any character the user
    was working on before authenticating.
    """
    char_data = request.session.get("current_character")
    if not char_data:
        return None

    # Check if we already have a saved character ID (shouldn't happen, but be safe)
    if request.session.get("current_saved_character_id"):
        return request.session.get("current_saved_character_id")

    # Include any experience data from the session
    if request.session.get("interactive_years", 0) > 0:
        char_data["interactive_years"] = request.session.get("interactive_years", 0)
        char_data["interactive_skills"] = request.session.get("interactive_skills", [])
        char_data["interactive_yearly_results"] = request.session.get(
            "interactive_yearly_results", []
        )
        char_data["interactive_died"] = request.session.get("interactive_died", False)
        char_data["interactive_aging"] = request.session.get("interactive_aging", {})

    # Create the saved character
    char_count = SavedCharacter.objects.filter(user=user).count() + 1
    saved_char = SavedCharacter.objects.create(
        user=user,
        name=char_data.get("name") or f"Character {char_count}",
        age=char_data.get("age"),
        race=char_data.get("race", ""),
        description=char_data.get("description", ""),
        character_data=char_data,
    )
    request.session["current_saved_character_id"] = saved_char.id
    request.session["current_character"] = char_data  # Update with experience data
    request.session.modified = True

    return saved_char.id


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect("welcome")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Save any character the user was working on
            saved_id = save_session_character_for_user(request, user)
            messages.success(request, "Account created successfully!")
            # Redirect to generator if they had a character, otherwise welcome
            if saved_id:
                return redirect("generator")
            return redirect("welcome")
    else:
        form = RegistrationForm()

    return render(request, "generator/register.html", {"form": form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect("welcome")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Save any character the user was working on
            saved_id = save_session_character_for_user(request, user)
            # Redirect to generator if they had a character, otherwise to next_url
            if saved_id:
                return redirect("generator")
            next_url = request.GET.get("next", "welcome")
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, "generator/login.html", {"form": form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("welcome")


@login_required
def my_profile(request):
    """User profile page - view and edit own profile."""
    profile = request.user.profile

    if request.method == "POST":
        # Handle profile updates
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        discord = request.POST.get("discord", "").strip()
        preferred_contact = request.POST.get("preferred_contact", "").strip()

        # Update user email
        if email:
            request.user.email = email
            request.user.save()

        # Update profile fields
        profile.phone = phone
        profile.discord_handle = discord
        if preferred_contact in ["email", "sms", "discord", ""]:
            profile.preferred_contact = preferred_contact
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("my_profile")

    return render(
        request,
        "generator/my_profile.html",
        {
            "profile": profile,
            "contact_choices": UserProfile.CONTACT_METHOD_CHOICES,
        },
    )
