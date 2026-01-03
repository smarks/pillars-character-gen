"""
Admin and DM management views for the Pillars Character Generator.

This module handles admin/DM-restricted functionality:
- dm_required, admin_required decorators
- manage_users: Admin user management
- manage_characters: DM/Admin character browser
- User and character CRUD operations
"""

import functools
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST

from ..models import SavedCharacter, UserProfile, UserNotes
from .forms import AdminUserCreationForm


# =============================================================================
# Access Control Decorators
# =============================================================================


def dm_required_check(request):
    """Check if user has DM access. Returns redirect response if not authorized, None if authorized."""
    if not request.user.is_authenticated:
        return redirect("login")
    if not hasattr(request.user, "profile") or not (
        request.user.profile.is_dm or request.user.profile.is_admin
    ):
        messages.error(request, "You must be a Dungeon Master to access this page.")
        return redirect("welcome")
    return None


def dm_required(view_func):
    """Decorator that requires user to be a DM or Admin."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        redirect_response = dm_required_check(request)
        if redirect_response:
            return redirect_response
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Decorator that requires user to be an Admin."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not hasattr(request.user, "profile") or not request.user.profile.is_admin:
            messages.error(request, "You must be an Admin to access this page.")
            return redirect("welcome")
        return view_func(request, *args, **kwargs)

    return wrapper


# =============================================================================
# Admin Views
# =============================================================================


@admin_required
def manage_users(request):
    """Admin view to manage user roles, create users, and view all characters."""
    users = UserProfile.objects.select_related("user").all()
    role_choices = UserProfile.ROLE_CHOICES

    # Get all user notes
    all_notes = (
        UserNotes.objects.all().select_related("user").order_by("user__username")
    )
    notes_by_user = {note.user.username: note for note in all_notes}

    # Handle user creation form submission
    if request.method == "POST" and "create_user" in request.POST:
        create_form = AdminUserCreationForm(request.POST)
        if create_form.is_valid():
            user = create_form.save()
            messages.success(request, f"Successfully created user: {user.username}")
            return redirect("manage_users")
        else:
            # Form has errors - will be displayed in template
            pass
    else:
        # Create empty form for GET requests
        create_form = AdminUserCreationForm()

    return render(
        request,
        "generator/manage_users.html",
        {
            "users": users,
            "role_choices": role_choices,
            "create_form": create_form,
            "notes_by_user": notes_by_user,
        },
    )


@dm_required
def manage_characters(request):
    """Redirect to unified my_characters view.

    This view is kept for backwards compatibility with existing URLs.
    The my_characters view now handles both regular users and DMs/admins.
    """
    # Preserve any query parameters
    player_filter = request.GET.get("player", "")
    if player_filter:
        return redirect(f"/my-characters/?player={player_filter}")
    return redirect("my_characters")


@dm_required
@require_POST
def bulk_delete_characters(request):
    """DM/Admin view to delete multiple characters at once."""
    character_ids = request.POST.getlist("character_ids")
    if character_ids:
        deleted_count = SavedCharacter.objects.filter(id__in=character_ids).delete()[0]
        messages.success(request, f"Deleted {deleted_count} character(s).")
    else:
        messages.warning(request, "No characters selected.")
    return redirect("manage_characters")


@admin_required
@require_POST
def change_user_role(request, user_id):
    """Change a user's roles (Admin only)."""
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        # Get list of roles from form (checkboxes)
        new_roles = request.POST.getlist("roles")
        valid_roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        new_roles = [r for r in new_roles if r in valid_roles]
        profile.roles = new_roles
        profile.save()
        messages.success(
            request,
            f"Updated {profile.user.username}'s roles to: {profile.get_roles_display() or 'None'}.",
        )
    except UserProfile.DoesNotExist:
        messages.error(request, "User not found.")

    return redirect("manage_users")


@admin_required
def edit_user(request, user_id):
    """Edit a user's details (Admin only)."""
    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "User not found.")
        return redirect("manage_users")

    if request.method == "POST":
        # Update user fields
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        roles = request.POST.getlist("roles")
        phone = request.POST.get("phone", "").strip()
        discord_handle = request.POST.get("discord_handle", "").strip()
        preferred_contact = request.POST.get("preferred_contact", "").strip()

        # Validate username
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                messages.error(request, f'Username "{username}" is already taken.')
                return redirect("edit_user", user_id=user_id)
            user.username = username

        # Update email
        if email:
            user.email = email

        # Update password if provided
        if new_password:
            user.set_password(new_password)

        user.save()

        # Update profile
        valid_roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        profile.roles = [r for r in roles if r in valid_roles]
        profile.phone = phone
        profile.discord_handle = discord_handle
        if preferred_contact in ["email", "phone", "discord"]:
            profile.preferred_contact = preferred_contact
        profile.save()

        messages.success(request, f'User "{user.username}" updated successfully.')
        return redirect("manage_users")

    # GET request - show edit form
    role_choices = UserProfile.ROLE_CHOICES
    return render(
        request,
        "generator/edit_user.html",
        {
            "edit_user": user,
            "profile": profile,
            "role_choices": role_choices,
        },
    )


@admin_required
@require_POST
def delete_user(request, user_id):
    """Delete a user and all their characters (Admin only)."""
    try:
        user = User.objects.get(id=user_id)

        # Don't allow deleting yourself
        if user.id == request.user.id:
            messages.error(request, "You cannot delete your own account.")
            return redirect("manage_users")

        username = user.username
        # Delete user (this will cascade to profile and characters due to foreign keys)
        user.delete()
        messages.success(
            request, f'User "{username}" and all their characters have been deleted.'
        )
    except User.DoesNotExist:
        messages.error(request, "User not found.")

    return redirect("manage_users")


@admin_required
@require_POST
def admin_delete_character(request, char_id):
    """Delete any character (Admin only)."""
    try:
        character = SavedCharacter.objects.get(id=char_id)
        char_name = character.name
        owner = character.user.username
        character.delete()
        messages.success(
            request, f'Character "{char_name}" (owned by {owner}) has been deleted.'
        )
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")

    return redirect("manage_users")
