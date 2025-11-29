import re
from django import template

register = template.Library()


@register.filter
def consolidate_skills(skills):
    """
    Consolidate duplicate skills and sum their bonuses.

    "Cutlass +1 to hit" x 5 becomes "Cutlass +5 to hit"
    "Swimming" x 3 becomes "Swimming (3)"
    """
    if not skills:
        return []

    # Count occurrences
    skill_counts = {}
    for skill in skills:
        skill_counts[skill] = skill_counts.get(skill, 0) + 1

    # Consolidate skills with +1 pattern
    consolidated = {}
    for skill, count in skill_counts.items():
        # Match patterns like "Sword +1 to hit" or "Cutlass +1 parry"
        match = re.match(r'^(.+?)\s*\+1\s+(.+)$', skill)
        if match:
            base = match.group(1).strip()
            suffix = match.group(2).strip()
            key = (base, suffix)
            consolidated[key] = consolidated.get(key, 0) + count
        else:
            # Non-bonus skill
            key = ('_plain_', skill)
            consolidated[key] = consolidated.get(key, 0) + count

    # Build result list
    result = []
    for key, total in consolidated.items():
        if key[0] == '_plain_':
            skill_name = key[1]
            if total > 1:
                result.append(f"{skill_name} ({total})")
            else:
                result.append(skill_name)
        else:
            base, suffix = key
            result.append(f"{base} +{total} {suffix}")

    return result
