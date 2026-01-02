"""
PDF export generation for character data.
"""

from io import BytesIO
from xml.sax.saxutils import escape

from .helpers import get_attribute_modifier
from ._character_helpers import build_skill_points_from_char_data


def generate_pdf_from_char_data(char_data, character_name="Unnamed Character"):
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
