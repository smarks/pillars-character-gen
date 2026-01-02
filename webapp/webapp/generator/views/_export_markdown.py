"""
Markdown export generation for character data.
"""

from .helpers import get_attribute_modifier
from ._character_helpers import build_skill_points_from_char_data


def generate_markdown_from_char_data(char_data, character_name="Unnamed Character"):
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
