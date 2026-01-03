from django import template
from pillars.skills import normalize_skill_name, level_from_points, to_roman

register = template.Library()


@register.filter
def consolidate_skills(skills):
    """
    Consolidate skills using the skill point system with triangular numbers.

    Each skill occurrence = 1 skill point.
    Skills are grouped by base name (normalized, case-insensitive).
    Display uses triangular numbers: Level 1 = 1pt, Level 2 = 3pts, Level 3 = 6pts, etc.
    Original casing is preserved for display (first occurrence wins).

    Examples:
        ['Cutlass +1 to hit', 'Cutlass +1 to hit', 'Cutlass +1 to hit']
        -> ['Cutlass II'] (3 points = Level 2)

        ['Sword +1 to hit', 'Sword +1 to hit', 'Sword +1 to hit', 'Sword +1 to hit']
        -> ['Sword II (+1)'] (4 points = Level 2 with 1 point toward Level 3)
    """
    if not skills:
        return []

    # Count skill points by normalized skill name
    # Each occurrence = 1 skill point
    # Also track display name (first occurrence wins)
    skill_points = {}
    display_names = {}
    for skill in skills:
        normalized = normalize_skill_name(skill)
        if normalized:
            skill_points[normalized] = skill_points.get(normalized, 0) + 1
            if normalized not in display_names:
                # Use title-cased normalized name for display
                # This removes modifiers like "+1" while preserving the base skill name
                display_names[normalized] = normalized.title()

    # Build result list with proper level display
    result = []
    for skill_name in sorted(skill_points.keys()):
        points = skill_points[skill_name]
        level, excess = level_from_points(points)
        # Use stored display name, or title-case as fallback
        display = display_names.get(skill_name, skill_name.title())

        if level >= 1:
            roman = to_roman(level)
            if excess > 0:
                result.append(f"{display} {roman} (+{excess})")
            else:
                result.append(f"{display} {roman}")
        else:
            # Less than 1 point (shouldn't happen, but handle gracefully)
            result.append(f"{display} (+{points})")

    return result
