# Generated migration for skill points system
from django.db import migrations


def migrate_skill_points(apps, schema_editor):
    """Migrate existing characters to use skill_points_data format.

    For each character:
    - Count skill points from all skill sources (location, track, interactive, manual)
    - Calculate XP based on years of prior experience
    - Set free_skill_points equal to years (all unallocated for legacy)
    """
    SavedCharacter = apps.get_model('generator', 'SavedCharacter')

    for character in SavedCharacter.objects.all():
        char_data = character.character_data

        # Skip if already migrated
        if char_data.get('skill_points_data'):
            continue

        # Collect all skills
        all_skills = []
        all_skills.extend(char_data.get('location_skills', []))
        if char_data.get('skill_track'):
            all_skills.extend(char_data['skill_track'].get('initial_skills', []))
        all_skills.extend(char_data.get('interactive_skills', []))
        all_skills.extend(char_data.get('manual_skills', []))

        # Build skill points from skill list
        skill_points = {}
        for skill in all_skills:
            if not skill:
                continue
            # Normalize skill name (strip modifiers)
            import re
            normalized = skill.strip()
            patterns = [
                r'\s*\+\d+\s*to\s*hit\s*$',
                r'\s*\+\d+\s*parry\s*$',
                r'\s*\+\d+\s*damage\s*$',
                r'\s*\+\d+\s*$',
                r'\s*\(x\d+\)\s*$',
                r'\s+\d+\s*$',
            ]
            for pattern in patterns:
                normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
            normalized = normalized.strip()

            if not normalized:
                continue

            if normalized not in skill_points:
                skill_points[normalized] = {'automatic': 0, 'allocated': 0}
            skill_points[normalized]['automatic'] += 1

        # Calculate years and XP
        years = char_data.get('interactive_years', 0)
        total_xp = years * 1000

        # All free points are unallocated for legacy characters
        free_points = years

        # Save skill_points_data
        char_data['skill_points_data'] = {
            'skill_points': skill_points,
            'free_skill_points': free_points,
            'total_xp': total_xp
        }

        character.character_data = char_data
        character.save()


def reverse_migrate_skill_points(apps, schema_editor):
    """Remove skill_points_data from all characters."""
    SavedCharacter = apps.get_model('generator', 'SavedCharacter')

    for character in SavedCharacter.objects.all():
        char_data = character.character_data
        if 'skill_points_data' in char_data:
            del char_data['skill_points_data']
            character.character_data = char_data
            character.save()


class Migration(migrations.Migration):

    dependencies = [
        ('generator', '0007_add_usernotes'),
    ]

    operations = [
        migrations.RunPython(migrate_skill_points, reverse_migrate_skill_points),
    ]
