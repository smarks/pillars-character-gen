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
from .helpers import get_attribute_modifier
from .character_sheet import build_skill_points_from_char_data


def _generate_markdown_from_char_data(char_data, character_name="Unnamed Character"):
    """Generate complete markdown representation of character data.

    Exports all character information including:
    - Full attributes with modifiers
    - Derived stats (fatigue, body, rolls)
    - Biographical info (appearance, height, weight)
    - Background (provenance, location, literacy, wealth)
    - Complete skills with levels and points
    - Free skill points and total XP
    - Equipment
    - Full prior experience history (year by year)
    - Aging penalties
    - Death status
    - Notes
    """
    md = f"# {character_name}\n\n"

    # Current Age
    years_served = char_data.get("interactive_years", 0)
    current_age = 16 + years_served
    md += f"**Age:** {current_age}\n\n"

    # Death status
    if char_data.get("interactive_died"):
        md += "> **DECEASED** - Died during prior experience\n\n"

    # Attributes
    md += "## Attributes\n\n"
    md += "| Attr | Value | Modifier |\n"
    md += "|------|-------|----------|\n"

    attrs = char_data.get("attributes", {})
    aging = char_data.get("interactive_aging", {})
    attr_names = ["STR", "DEX", "INT", "WIS", "CON", "CHR"]
    for attr in attr_names:
        val = attrs.get(attr, "-")
        mod = get_attribute_modifier(val) if isinstance(val, int) else 0
        mod_str = f"{mod:+d}" if mod != 0 else "0"
        # Show aging penalty if applicable
        aging_key = attr.lower()
        aging_penalty = aging.get(aging_key, 0)
        if aging_penalty:
            md += f"| {attr} | {val} ({aging_penalty:+d} aging) | {mod_str} |\n"
        else:
            md += f"| {attr} | {val} | {mod_str} |\n"

    md += "\n"

    # Derived Stats
    md += "### Derived Stats\n\n"
    fatigue = attrs.get("fatigue_points", "-")
    body = attrs.get("body_points", "-")
    fatigue_roll = attrs.get("fatigue_roll", "-")
    body_roll = attrs.get("body_roll", "-")
    md += f"- **Fatigue Points:** {fatigue}"
    if fatigue_roll and fatigue_roll != "-":
        md += f" (rolled {fatigue_roll})"
    md += "\n"
    md += f"- **Body Points:** {body}"
    if body_roll and body_roll != "-":
        md += f" (rolled {body_roll})"
    md += "\n"
    md += f"- **Generation Method:** {attrs.get('generation_method', 'Unknown')}\n\n"

    # Biographical
    md += "## Biographical\n\n"
    bio_fields = [
        ("appearance", "Appearance"),
        ("height", "Height"),
        ("weight", "Weight"),
    ]
    for field, label in bio_fields:
        val = char_data.get(field, "")
        if val:
            md += f"- **{label}:** {val}\n"
    md += "\n"

    # Background
    md += "## Background\n\n"
    background_fields = [
        ("provenance", "Provenance"),
        ("provenance_social_class", "Social Class"),
        ("provenance_sub_class", "Sub-Class"),
        ("location", "Location"),
        ("literacy", "Literacy"),
        ("wealth", "Wealth"),
        ("wealth_level", "Wealth Level"),
    ]
    for field, label in background_fields:
        val = char_data.get(field, "")
        if val:
            md += f"- **{label}:** {val}\n"

    # Location skills
    location_skills = char_data.get("location_skills", [])
    if location_skills:
        md += f"- **Location Skills:** {', '.join(location_skills)}\n"
    md += "\n"

    # Skills with full details
    md += "## Skills\n\n"
    char_skills = build_skill_points_from_char_data(char_data)

    # Free points and XP
    if char_skills.free_points > 0:
        md += f"**Free Skill Points:** {char_skills.free_points}\n"
    if char_skills.total_xp > 0:
        md += f"**Total XP:** {char_skills.total_xp}\n"
    md += "\n"

    skills_details = char_skills.get_skills_with_details()
    if skills_details:
        md += "| Skill | Level | Points | To Next |\n"
        md += "|-------|-------|--------|--------|\n"
        for skill in skills_details:
            level_display = skill.get("level_roman", "-")
            if skill.get("excess_points", 0) > 0:
                level_display += f" (+{skill['excess_points']})"
            md += f"| {skill['name']} | {level_display} | {skill['total_points']} | {skill['points_to_next_level']} |\n"
    else:
        md += "_No skills acquired_\n"
    md += "\n"

    # Equipment
    equipment = char_data.get("equipment", [])
    if equipment:
        md += "## Equipment\n\n"
        for item in equipment:
            if isinstance(item, dict):
                name = item.get("name", "Unknown")
                qty = item.get("quantity", 1)
                weight = item.get("weight", 0)
                md += f"- {name}"
                if qty > 1:
                    md += f" (x{qty})"
                if weight:
                    md += f" [{weight} lbs]"
                md += "\n"
            else:
                md += f"- {item}\n"
        md += "\n"

    # Prior Experience - Full History
    yearly_results = char_data.get("interactive_yearly_results", [])
    if years_served > 0 or yearly_results:
        md += "## Prior Experience\n\n"

        # Summary
        md += f"**Years of Experience:** {years_served}\n"
        md += "**Starting Age:** 16\n"
        md += f"**Current Age:** {current_age}\n"

        if char_data.get("skill_track"):
            track = char_data["skill_track"].get("track", "")
            survivability = char_data["skill_track"].get("survivability", "")
            initial_skills = char_data["skill_track"].get("initial_skills", [])
            if track:
                md += f"**Track:** {track}\n"
            if survivability:
                md += f"**Survivability:** {survivability}+\n"
            if initial_skills:
                md += f"**Initial Track Skills:** {', '.join(initial_skills)}\n"

        # Aging penalties summary
        if aging and any(v != 0 for v in aging.values()):
            md += "\n**Aging Penalties:**\n"
            for attr_key, penalty in aging.items():
                if penalty != 0:
                    md += f"- {attr_key.upper()}: {penalty:+d}\n"

        # Year by year log
        if yearly_results:
            md += "\n### Year-by-Year History\n\n"
            for i, year in enumerate(yearly_results, 1):
                age = 16 + i
                md += f"**Year {i} (Age {age}):**\n"

                # Survival
                survival_roll = year.get("survival_roll", "-")
                survived = year.get("survived", True)
                if survived:
                    md += f"- Survival: Rolled {survival_roll} - Survived\n"
                else:
                    md += f"- Survival: Rolled {survival_roll} - **DIED**\n"

                # Skills gained
                skills_gained = year.get("skills", [])
                if skills_gained:
                    md += f"- Skills: {', '.join(skills_gained)}\n"

                # Rewards
                rewards = year.get("rewards", "")
                if rewards:
                    md += f"- Rewards: {rewards}\n"

                # Aging this year
                year_aging = year.get("aging", {})
                if year_aging and any(v != 0 for v in year_aging.values()):
                    aging_parts = [
                        f"{k.upper()} {v:+d}" for k, v in year_aging.items() if v != 0
                    ]
                    md += f"- Aging: {', '.join(aging_parts)}\n"

                md += "\n"

    # Notes
    notes = char_data.get("notes", "")
    if notes and notes.strip():
        md += "## Notes\n\n"
        md += f"{notes}\n\n"

    # Manual skills (if any separate from computed)
    manual_skills = char_data.get("manual_skills", [])
    if manual_skills:
        md += "## Additional Skills (Manually Added)\n\n"
        for skill in manual_skills:
            md += f"- {skill}\n"
        md += "\n"

    # Footer
    md += "---\n"
    md += "*Exported from Pillars Character Generator*\n"

    return md


def _generate_pdf_from_char_data(char_data, character_name="Unnamed Character"):
    """Generate complete PDF representation of character data using reportlab.

    Exports all character information matching the markdown export.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib import colors
    from io import BytesIO
    from xml.sax.saxutils import escape

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6,
        spaceBefore=10,
    )
    subheading_style = ParagraphStyle(
        "CustomSubheading",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4,
        spaceBefore=8,
    )

    years_served = char_data.get("interactive_years", 0)
    current_age = 16 + years_served
    aging = char_data.get("interactive_aging", {})

    # Title and age
    safe_character_name = escape(str(character_name or "Unnamed Character"))
    story.append(Paragraph(safe_character_name, title_style))
    story.append(Paragraph(f"<b>Age:</b> {current_age}", styles["Normal"]))

    # Death status
    if char_data.get("interactive_died"):
        death_style = ParagraphStyle(
            "DeathNotice",
            parent=styles["Normal"],
            textColor=colors.red,
            fontSize=12,
            spaceBefore=4,
        )
        story.append(
            Paragraph("<b>DECEASED</b> - Died during prior experience", death_style)
        )

    story.append(Spacer(1, 0.15 * inch))

    # Attributes with aging
    story.append(Paragraph("Attributes", heading_style))
    attrs = char_data.get("attributes", {})
    attr_data = [["Attr", "Value", "Mod"]]
    attr_names = ["STR", "DEX", "INT", "WIS", "CON", "CHR"]
    for attr in attr_names:
        val = attrs.get(attr, "-")
        mod = get_attribute_modifier(val) if isinstance(val, int) else 0
        mod_str = f"{mod:+d}" if mod != 0 else "0"
        aging_key = attr.lower()
        aging_penalty = aging.get(aging_key, 0)
        if aging_penalty:
            val_str = f"{val} ({aging_penalty:+d})"
        else:
            val_str = str(val)
        attr_data.append([attr, val_str, mod_str])

    attr_table = Table(attr_data, colWidths=[0.8 * inch, 1.2 * inch, 0.8 * inch])
    attr_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(attr_table)
    story.append(Spacer(1, 0.1 * inch))

    # Derived stats
    fatigue = attrs.get("fatigue_points", "-")
    body = attrs.get("body_points", "-")
    fatigue_roll = attrs.get("fatigue_roll", "")
    body_roll = attrs.get("body_roll", "")
    gen_method = attrs.get("generation_method", "Unknown")

    fatigue_str = f"<b>Fatigue:</b> {fatigue}"
    if fatigue_roll:
        fatigue_str += f" (rolled {fatigue_roll})"
    body_str = f"<b>Body:</b> {body}"
    if body_roll:
        body_str += f" (rolled {body_roll})"

    story.append(Paragraph(fatigue_str, styles["Normal"]))
    story.append(Paragraph(body_str, styles["Normal"]))
    story.append(Paragraph(f"<b>Generation:</b> {gen_method}", styles["Normal"]))
    story.append(Spacer(1, 0.1 * inch))

    # Biographical
    story.append(Paragraph("Biographical", heading_style))
    bio_fields = [
        ("appearance", "Appearance"),
        ("height", "Height"),
        ("weight", "Weight"),
    ]
    for field, label in bio_fields:
        val = char_data.get(field, "")
        if val:
            safe_val = escape(str(val))
            story.append(Paragraph(f"<b>{label}:</b> {safe_val}", styles["Normal"]))
    story.append(Spacer(1, 0.1 * inch))

    # Background
    story.append(Paragraph("Background", heading_style))
    background_fields = [
        ("provenance", "Provenance"),
        ("provenance_social_class", "Social Class"),
        ("location", "Location"),
        ("literacy", "Literacy"),
        ("wealth", "Wealth"),
        ("wealth_level", "Wealth Level"),
    ]
    for field, label in background_fields:
        val = char_data.get(field, "")
        if val:
            safe_val = escape(str(val))
            story.append(Paragraph(f"<b>{label}:</b> {safe_val}", styles["Normal"]))

    location_skills = char_data.get("location_skills", [])
    if location_skills:
        story.append(
            Paragraph(
                f"<b>Location Skills:</b> {', '.join(location_skills)}",
                styles["Normal"],
            )
        )
    story.append(Spacer(1, 0.1 * inch))

    # Skills with details
    story.append(Paragraph("Skills", heading_style))
    char_skills = build_skill_points_from_char_data(char_data)

    if char_skills.free_points > 0:
        story.append(
            Paragraph(
                f"<b>Free Skill Points:</b> {char_skills.free_points}", styles["Normal"]
            )
        )
    if char_skills.total_xp > 0:
        story.append(
            Paragraph(f"<b>Total XP:</b> {char_skills.total_xp}", styles["Normal"])
        )

    skills_details = char_skills.get_skills_with_details()
    if skills_details:
        skill_data = [["Skill", "Level", "Points", "To Next"]]
        for skill in skills_details:
            level_display = skill.get("level_roman", "-")
            if skill.get("excess_points", 0) > 0:
                level_display += f" (+{skill['excess_points']})"
            skill_data.append(
                [
                    skill["name"],
                    level_display,
                    str(skill["total_points"]),
                    str(skill["points_to_next_level"]),
                ]
            )

        skill_table = Table(
            skill_data, colWidths=[2 * inch, 0.8 * inch, 0.6 * inch, 0.7 * inch]
        )
        skill_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(skill_table)
    else:
        story.append(Paragraph("<i>No skills acquired</i>", styles["Normal"]))
    story.append(Spacer(1, 0.1 * inch))

    # Equipment
    equipment = char_data.get("equipment", [])
    if equipment:
        story.append(Paragraph("Equipment", heading_style))
        for item in equipment:
            if isinstance(item, dict):
                name = item.get("name", "Unknown")
                qty = item.get("quantity", 1)
                weight = item.get("weight", 0)
                item_str = f"• {escape(name)}"
                if qty > 1:
                    item_str += f" (x{qty})"
                if weight:
                    item_str += f" [{weight} lbs]"
                story.append(Paragraph(item_str, styles["Normal"]))
            else:
                story.append(Paragraph(f"• {escape(str(item))}", styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))

    # Prior Experience
    yearly_results = char_data.get("interactive_yearly_results", [])
    if years_served > 0 or yearly_results:
        story.append(Paragraph("Prior Experience", heading_style))
        story.append(
            Paragraph(
                f"<b>Years:</b> {years_served} | <b>Starting Age:</b> 16 | <b>Current Age:</b> {current_age}",
                styles["Normal"],
            )
        )

        if char_data.get("skill_track"):
            track = char_data["skill_track"].get("track", "")
            survivability = char_data["skill_track"].get("survivability", "")
            initial_skills = char_data["skill_track"].get("initial_skills", [])
            if track:
                story.append(
                    Paragraph(f"<b>Track:</b> {escape(str(track))}", styles["Normal"])
                )
            if survivability:
                story.append(
                    Paragraph(
                        f"<b>Survivability:</b> {survivability}+", styles["Normal"]
                    )
                )
            if initial_skills:
                story.append(
                    Paragraph(
                        f"<b>Initial Skills:</b> {', '.join(initial_skills)}",
                        styles["Normal"],
                    )
                )

        # Aging penalties summary
        if aging and any(v != 0 for v in aging.values()):
            aging_parts = [f"{k.upper()} {v:+d}" for k, v in aging.items() if v != 0]
            story.append(
                Paragraph(
                    f"<b>Aging Penalties:</b> {', '.join(aging_parts)}",
                    styles["Normal"],
                )
            )

        # Year by year log
        if yearly_results:
            story.append(Paragraph("Year-by-Year History", subheading_style))
            for i, year in enumerate(yearly_results, 1):
                age = 16 + i
                survival_roll = year.get("survival_roll", "-")
                survived = year.get("survived", True)
                skills_gained = year.get("skills", [])
                rewards = year.get("rewards", "")
                year_aging = year.get("aging", {})

                year_str = f"<b>Year {i} (Age {age}):</b> "
                if survived:
                    year_str += f"Survived (rolled {survival_roll})"
                else:
                    year_str += (
                        f"<font color='red'>DIED (rolled {survival_roll})</font>"
                    )

                if skills_gained:
                    year_str += f" | Skills: {', '.join(skills_gained)}"
                if rewards:
                    year_str += f" | Rewards: {escape(str(rewards))}"
                if year_aging and any(v != 0 for v in year_aging.values()):
                    aging_parts = [
                        f"{k.upper()} {v:+d}" for k, v in year_aging.items() if v != 0
                    ]
                    year_str += f" | Aging: {', '.join(aging_parts)}"

                story.append(Paragraph(year_str, styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))

    # Notes
    notes = char_data.get("notes", "")
    if notes and notes.strip():
        story.append(Paragraph("Notes", heading_style))
        safe_notes = escape(str(notes))
        story.append(Paragraph(safe_notes, styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))

    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        spaceBefore=20,
    )
    story.append(Paragraph("Exported from Pillars Character Generator", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


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
        md_content = _generate_markdown_from_char_data(char_data, character_name)

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
        pdf_buffer = _generate_pdf_from_char_data(char_data, character_name)

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

    md_content = _generate_markdown_from_char_data(char_data, character.name)

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

    pdf_buffer = _generate_pdf_from_char_data(char_data, character.name)

    response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
    # Sanitize filename
    safe_name = re.sub(r"[^\w\s-]", "", character.name).strip()
    safe_name = re.sub(r"[-\s]+", "_", safe_name)
    filename = f"{safe_name or 'Unnamed_Character'}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
