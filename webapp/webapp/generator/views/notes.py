"""
User notes views for the Pillars Character Generator.

This module handles user notes functionality:
- user_notes: View personal notes page
- save_user_notes: AJAX save notes
- admin_notes: Admin view all notes
- admin_edit_note: Admin edit a user's notes
- admin_delete_note: Admin delete notes
"""

import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import UserNotes
from .admin import admin_required


@login_required
def user_notes(request):
    """View for user's personal notes page."""
    notes, created = UserNotes.objects.get_or_create(user=request.user)
    return render(
        request,
        "generator/notes.html",
        {
            "notes": notes,
        },
    )


@login_required
@require_POST
def save_user_notes(request):
    """API endpoint to save user notes. Called on blur/focus loss."""
    try:
        data = json.loads(request.body)
        content = data.get("content", "")

        notes, created = UserNotes.objects.get_or_create(user=request.user)
        notes.content = content
        notes.save()

        return JsonResponse(
            {
                "success": True,
                "updated_at": notes.updated_at.isoformat(),
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@admin_required
def admin_notes(request):
    """Admin view to browse and search all user notes."""
    search_query = request.GET.get("q", "").strip()
    user_filter = request.GET.get("user", "").strip()

    notes = UserNotes.objects.all().select_related("user").order_by("-updated_at")

    # Filter by user
    if user_filter:
        notes = notes.filter(user__username__icontains=user_filter)

    # Search in content
    if search_query:
        notes = notes.filter(content__icontains=search_query)

    # Get list of users who have notes for the filter dropdown
    users_with_notes = (
        UserNotes.objects.values_list("user__username", flat=True)
        .distinct()
        .order_by("user__username")
    )

    return render(
        request,
        "generator/admin_notes.html",
        {
            "notes": notes,
            "search_query": search_query,
            "user_filter": user_filter,
            "users_with_notes": users_with_notes,
        },
    )


@admin_required
def admin_edit_note(request, note_id):
    """Admin view to edit a user's notes."""
    try:
        note = UserNotes.objects.select_related("user").get(id=note_id)
    except UserNotes.DoesNotExist:
        messages.error(request, "Note not found.")
        return redirect("admin_notes")

    if request.method == "POST":
        note.content = request.POST.get("content", "")
        note.save()
        messages.success(request, f"Updated notes for {note.user.username}.")
        return redirect("admin_notes")

    return render(
        request,
        "generator/admin_edit_note.html",
        {
            "note": note,
        },
    )


@admin_required
@require_POST
def admin_delete_note(request, note_id):
    """Admin view to delete a user's notes."""
    try:
        note = UserNotes.objects.select_related("user").get(id=note_id)
        username = note.user.username
        note.delete()
        messages.success(request, f"Deleted notes for {username}.")
    except UserNotes.DoesNotExist:
        messages.error(request, "Note not found.")

    return redirect("admin_notes")
