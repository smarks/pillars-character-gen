"""
Character export views for the Pillars Character Generator.

This module handles exporting characters:
- export_session_character_markdown: Export session character as Markdown
- export_session_character_pdf: Export session character as PDF
- export_character_markdown: Export saved character as Markdown
- export_character_pdf: Export saved character as PDF
"""

import re
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from ..models import SavedCharacter
from ._export_markdown import generate_markdown_from_char_data
from ._export_pdf import generate_pdf_from_char_data


def export_session_character_markdown(request):
    """Export current session character as Markdown file."""
    try:
        char_data = request.session.get("current_character")
        if not char_data:
            return HttpResponse(
                "No character data found in session. Please generate a character first.",
                status=404,
                content_type="text/plain",
            )

        character_name = char_data.get("name", "Unnamed Character")
        md_content = generate_markdown_from_char_data(char_data, character_name)

        response = HttpResponse(md_content, content_type="text/markdown; charset=utf-8")
        # Sanitize filename
        safe_name = re.sub(r"[^\w\s-]", "", character_name).strip()
        safe_name = re.sub(r"[-\s]+", "_", safe_name)
        filename = f"{safe_name or 'Unnamed_Character'}.md"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        import traceback

        error_msg = f"Error generating Markdown: {str(e)}\n\n{traceback.format_exc()}"
        return HttpResponse(error_msg, status=500, content_type="text/plain")


def export_session_character_pdf(request):
    """Export current session character as PDF file."""
    try:
        char_data = request.session.get("current_character")
        if not char_data:
            return HttpResponse(
                "No character data found in session. Please generate a character first.",
                status=404,
                content_type="text/plain",
            )

        character_name = char_data.get("name", "Unnamed Character")
        pdf_buffer = generate_pdf_from_char_data(char_data, character_name)

        response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
        # Sanitize filename
        safe_name = re.sub(r"[^\w\s-]", "", character_name).strip()
        safe_name = re.sub(r"[-\s]+", "_", safe_name)
        filename = f"{safe_name or 'Unnamed_Character'}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        import traceback

        error_msg = f"Error generating PDF: {str(e)}\n\n{traceback.format_exc()}"
        return HttpResponse(error_msg, status=500, content_type="text/plain")


@login_required
def export_character_markdown(request, char_id):
    """Export saved character as Markdown file."""
    profile = getattr(request.user, "profile", None)
    is_dm_or_admin = (
        profile and (profile.is_dm or profile.is_admin) if profile else False
    )

    try:
        if is_dm_or_admin:
            character = SavedCharacter.objects.get(id=char_id)
        else:
            character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")
        return redirect("my_characters")

    char_data = character.character_data.copy()
    char_data["name"] = character.name
    char_data["notes"] = character.description or char_data.get("notes", "")

    md_content = generate_markdown_from_char_data(char_data, character.name)

    response = HttpResponse(md_content, content_type="text/markdown; charset=utf-8")
    # Sanitize filename
    safe_name = re.sub(r"[^\w\s-]", "", character.name).strip()
    safe_name = re.sub(r"[-\s]+", "_", safe_name)
    filename = f"{safe_name or 'Unnamed_Character'}.md"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_character_pdf(request, char_id):
    """Export saved character as PDF file."""
    profile = getattr(request.user, "profile", None)
    is_dm_or_admin = (
        profile and (profile.is_dm or profile.is_admin) if profile else False
    )

    try:
        if is_dm_or_admin:
            character = SavedCharacter.objects.get(id=char_id)
        else:
            character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, "Character not found.")
        return redirect("my_characters")

    char_data = character.character_data.copy()
    char_data["name"] = character.name
    char_data["notes"] = character.description or char_data.get("notes", "")

    pdf_buffer = generate_pdf_from_char_data(char_data, character.name)

    response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
    # Sanitize filename
    safe_name = re.sub(r"[^\w\s-]", "", character.name).strip()
    safe_name = re.sub(r"[-\s]+", "_", safe_name)
    filename = f"{safe_name or 'Unnamed_Character'}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
