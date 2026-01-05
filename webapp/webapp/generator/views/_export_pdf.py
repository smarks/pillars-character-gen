"""
PDF export generation for character data.
"""

from io import BytesIO
from xml.sax.saxutils import escape

from .helpers import get_attribute_modifier, get_attribute_base_value
from ._character_helpers import (
    build_skill_points_from_char_data,
    calculate_adjusted_attributes,
)


# Movement and encumbrance constants (same as core.py)
MIN_BASE_MOVEMENT = 4
LIGHT_ENCUMBRANCE_MULTIPLIER = 1.5
MEDIUM_ENCUMBRANCE_MULTIPLIER = 2
HEAVY_ENCUMBRANCE_MULTIPLIER = 2.5


def _calculate_movement_encumbrance(char_data):
    """Calculate movement allowance and encumbrance thresholds."""
    attrs = char_data.get("attributes", {})
    str_val = get_attribute_base_value(attrs.get("STR", 10))
    dex_val = get_attribute_base_value(attrs.get("DEX", 10))

    base_ma = max(MIN_BASE_MOVEMENT, dex_val - 2)
    return {
        "base_ma": base_ma,
        "jog_hexes": base_ma // 2,
        "fatigue_pool": str_val,
        "enc_unenc_max": str_val,
        "enc_light_min": str_val + 1,
        "enc_light_max": int(str_val * LIGHT_ENCUMBRANCE_MULTIPLIER),
        "enc_med_min": int(str_val * LIGHT_ENCUMBRANCE_MULTIPLIER) + 1,
        "enc_med_max": str_val * int(MEDIUM_ENCUMBRANCE_MULTIPLIER),
        "enc_heavy_min": str_val * int(MEDIUM_ENCUMBRANCE_MULTIPLIER) + 1,
        "enc_heavy_max": int(str_val * HEAVY_ENCUMBRANCE_MULTIPLIER),
    }


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
    base_age = char_data.get("base_age", 16)
    current_age = base_age + years_served
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
    has_aging = any(v != 0 for v in aging.values())
    adjusted = calculate_adjusted_attributes(char_data) if has_aging else {}

    if has_aging:
        attr_data = [["Attr", "Base", "Adjusted", "Mod"]]
    else:
        attr_data = [["Attr", "Value", "Mod"]]

    attr_names = ["STR", "DEX", "INT", "WIS", "CON", "CHR"]
    for attr in attr_names:
        val = attrs.get(attr, "-")
        base_val = get_attribute_base_value(val) if val != "-" else "-"
        aging_key = attr.lower()
        aging_penalty = aging.get(aging_key, 0)

        if has_aging and attr != "CHR":  # CHR has no aging
            adj_val = adjusted.get(f"{aging_key}_adjusted", base_val)
            adj_mod = adjusted.get(f"{aging_key}_adj_mod", 0)
            mod_str = f"{adj_mod:+d}" if adj_mod != 0 else "0"
            if aging_penalty:
                adj_str = f"{adj_val} ({aging_penalty:+d})"
            else:
                adj_str = str(adj_val)
            attr_data.append([attr, str(base_val), adj_str, mod_str])
        else:
            mod = get_attribute_modifier(val) if val != "-" else 0
            mod_str = f"{mod:+d}" if mod != 0 else "0"
            if has_aging:
                attr_data.append([attr, str(base_val), str(base_val), mod_str])
            else:
                attr_data.append([attr, str(base_val), mod_str])

    if has_aging:
        attr_table = Table(
            attr_data, colWidths=[0.6 * inch, 0.8 * inch, 1.0 * inch, 0.8 * inch]
        )
    else:
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
        skill_data = [["Skill", "Level", "Points", "Acquired"]]
        for skill in skills_details:
            level_display = skill.get("level_roman", "-") or "-"
            excess = skill.get("excess_points", 0)
            points_display = f"+{excess}" if excess > 0 else "-"
            skill_data.append(
                [
                    skill.get("display_name", skill["name"]),
                    level_display,
                    points_display,
                    skill.get("acquired", "Automatic"),
                ]
            )

        skill_table = Table(
            skill_data, colWidths=[2 * inch, 0.7 * inch, 0.6 * inch, 0.8 * inch]
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

    # Movement & Encumbrance
    movement = _calculate_movement_encumbrance(char_data)
    story.append(Paragraph("Movement &amp; Encumbrance", heading_style))
    story.append(
        Paragraph(
            f"<b>Base MA:</b> {movement['base_ma']} (DEX − 2, min 4) | "
            f"<b>Fatigue Pool:</b> {movement['fatigue_pool']} (= STR)",
            styles["Normal"],
        )
    )

    story.append(Paragraph("Encumbrance Thresholds", subheading_style))
    enc_data = [
        ["Load Level", "Weight (lbs)", "MA Mod", "Restrictions"],
        ["Unencumbered", f"0–{movement['enc_unenc_max']}", "0", "—"],
        [
            "Light",
            f"{movement['enc_light_min']}–{movement['enc_light_max']}",
            "−1",
            "—",
        ],
        [
            "Medium",
            f"{movement['enc_med_min']}–{movement['enc_med_max']}",
            "−2",
            "Cannot Run",
        ],
        [
            "Heavy",
            f"{movement['enc_heavy_min']}–{movement['enc_heavy_max']}",
            "−4",
            "Cannot Run/Jog",
        ],
        ["Overloaded", f">{movement['enc_heavy_max']}", "Walk only", "1 hex max"],
    ]
    enc_table = Table(
        enc_data, colWidths=[1.2 * inch, 1.1 * inch, 0.7 * inch, 1.2 * inch]
    )
    enc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(enc_table)

    story.append(Paragraph("Movement Speeds", subheading_style))
    move_data = [
        ["Speed", "Hexes", "Fatigue", "Actions"],
        ["Run", str(movement["base_ma"]), "1/turn", "None"],
        ["Jog", str(movement["jog_hexes"]), "1/4 turns", "Charge, Dodge, Drop"],
        ["Walk", "≤2", "None", "Ready Weapon"],
        ["Walk (slow)", "≤1", "None", "Cast, Missile, Disbelieve"],
        ["Stand Still", "0", "None", "Stand Up, Pick Up"],
    ]
    move_table = Table(
        move_data, colWidths=[1 * inch, 0.7 * inch, 0.8 * inch, 1.8 * inch]
    )
    move_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(move_table)
    story.append(
        Paragraph(
            "<b>Engaged:</b> Can only Shift (1 hex, stay adjacent) or Stand Still. "
            "<b>Exhausted:</b> MA halved, −2 DX, cannot Run.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    # Equipment & Encumbrance
    story.append(Paragraph("Equipment &amp; Encumbrance", heading_style))
    equipment = char_data.get("equipment", {})
    weapons = equipment.get("weapons", []) if isinstance(equipment, dict) else []
    armour = equipment.get("armour", []) if isinstance(equipment, dict) else []
    misc = equipment.get("misc", []) if isinstance(equipment, dict) else []

    # Handle legacy format (list of items)
    if isinstance(equipment, list):
        misc = equipment
        weapons = []
        armour = []

    # Weapons table
    story.append(Paragraph("Weapons", subheading_style))
    weapon_data = [["Name", "Desc", "Hit", "Crit", "Dmg", "Wt", "Value"]]
    if weapons:
        for item in weapons:
            if isinstance(item, dict):
                weapon_data.append(
                    [
                        item.get("name", ""),
                        item.get("description", ""),
                        item.get("hit", ""),
                        item.get("crit", ""),
                        item.get("damage", ""),
                        item.get("weight", ""),
                        item.get("value", ""),
                    ]
                )
    else:
        weapon_data.append(["", "", "", "", "", "", ""])
    weapon_table = Table(
        weapon_data,
        colWidths=[
            1.2 * inch,
            1.2 * inch,
            0.5 * inch,
            0.5 * inch,
            0.5 * inch,
            0.4 * inch,
            0.5 * inch,
        ],
    )
    weapon_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(weapon_table)

    # Armour table
    story.append(Paragraph("Armour", subheading_style))
    armour_data = [["Name", "Description", "Absorb", "Wt", "Value"]]
    if armour:
        for item in armour:
            if isinstance(item, dict):
                armour_data.append(
                    [
                        item.get("name", ""),
                        item.get("description", ""),
                        item.get("absorb", ""),
                        item.get("weight", ""),
                        item.get("value", ""),
                    ]
                )
    else:
        armour_data.append(["", "", "", "", ""])
    armour_table = Table(
        armour_data,
        colWidths=[1.2 * inch, 1.8 * inch, 0.6 * inch, 0.5 * inch, 0.6 * inch],
    )
    armour_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(armour_table)

    # Miscellaneous table
    story.append(Paragraph("Miscellaneous", subheading_style))
    misc_data = [["Name", "Description", "Attr Mod", "Wt", "Value"]]
    if misc:
        for item in misc:
            if isinstance(item, dict):
                misc_data.append(
                    [
                        item.get("name", ""),
                        item.get("description", ""),
                        item.get("attr_mod", ""),
                        item.get("weight", ""),
                        item.get("value", ""),
                    ]
                )
            else:
                misc_data.append([str(item), "", "", "", ""])
    else:
        misc_data.append(["", "", "", "", ""])
    misc_table = Table(
        misc_data,
        colWidths=[1.2 * inch, 1.8 * inch, 0.7 * inch, 0.5 * inch, 0.5 * inch],
    )
    misc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(misc_table)
    story.append(Spacer(1, 0.1 * inch))

    # Prior Experience
    yearly_results = char_data.get("interactive_yearly_results", [])
    if years_served > 0 or yearly_results:
        story.append(Paragraph("Prior Experience", heading_style))
        story.append(
            Paragraph(
                f"<b>Years:</b> {years_served} | <b>Starting Age:</b> {base_age} | <b>Current Age:</b> {current_age}",
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

    # Notes (always include section)
    story.append(Paragraph("Notes", heading_style))
    notes = char_data.get("notes", "")
    if notes and notes.strip():
        safe_notes = escape(str(notes))
        story.append(Paragraph(safe_notes, styles["Normal"]))
    else:
        story.append(Paragraph("<i>No notes</i>", styles["Normal"]))
    story.append(Spacer(1, 0.1 * inch))

    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        spaceBefore=20,
    )
    story.append(Paragraph("Exported from Pillars Character Editor", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
