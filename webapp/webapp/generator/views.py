import json
from django.shortcuts import render, redirect
from pillars import generate_character
from pillars.attributes import (
    roll_single_year,
    SkillTrack,
    TrackType,
    YearResult,
    AgingEffects,
    PriorExperience,
    AcceptanceCheck,
    CraftType,
)


def index(request):
    """Main page with generate button."""
    character = None
    years = 0  # Default value
    mode = request.POST.get('mode', 'standard')

    if request.method == 'POST':
        action = request.POST.get('action', 'generate')

        if action == 'generate':
            if mode == 'interactive':
                # Start interactive mode - generate base character with 0 years
                character = generate_character(years=0)
                # Store character state in session for interactive mode
                request.session['interactive_character'] = serialize_character(character)
                request.session['interactive_years'] = 0
                request.session['interactive_skills'] = list(character.skill_track.initial_skills)
                request.session['interactive_skill_points'] = 0
                request.session['interactive_yearly_results'] = []
                request.session['interactive_aging'] = {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0}
                request.session['interactive_died'] = False
                request.session['interactive_track_name'] = character.skill_track.track.value
                request.session['interactive_survivability'] = character.skill_track.survivability
                request.session['interactive_initial_skills'] = list(character.skill_track.initial_skills)

                return render(request, 'generator/interactive.html', {
                    'character': character,
                    'years_completed': 0,
                    'current_age': 16,
                    'yearly_results': [],
                    'can_continue': True,
                    'mode': 'interactive',
                    'track_name': character.skill_track.track.value,
                    'survivability': character.skill_track.survivability,
                    'initial_skills': character.skill_track.initial_skills,
                })
            else:
                years_input = request.POST.get('years', '0')
                try:
                    years = int(years_input)
                except ValueError:
                    years = 0
                character = generate_character(years=years)

    return render(request, 'generator/index.html', {
        'character': character,
        'years': years,
    })


def interactive(request):
    """Handle interactive prior experience mode."""
    # Check if we have an active interactive session
    char_data = request.session.get('interactive_character')
    if not char_data:
        return redirect('index')

    years_completed = request.session.get('interactive_years', 0)
    skills = request.session.get('interactive_skills', [])
    skill_points = request.session.get('interactive_skill_points', 0)
    yearly_results_data = request.session.get('interactive_yearly_results', [])
    aging_data = request.session.get('interactive_aging', {})
    died = request.session.get('interactive_died', False)
    track_name = request.session.get('interactive_track_name', '')
    survivability = request.session.get('interactive_survivability', 0)
    initial_skills = request.session.get('interactive_initial_skills', [])

    # Reconstruct character for display
    character = deserialize_character(char_data)
    current_age = 16 + years_completed
    latest_result = None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'continue' and not died:
            # Roll another year
            skill_track = character.skill_track
            total_modifier = sum(character.attributes.get_all_modifiers().values())

            # Reconstruct aging effects
            aging_effects = AgingEffects(
                str_penalty=aging_data.get('str', 0),
                dex_penalty=aging_data.get('dex', 0),
                int_penalty=aging_data.get('int', 0),
                wis_penalty=aging_data.get('wis', 0),
                con_penalty=aging_data.get('con', 0),
            )

            year_result = roll_single_year(
                skill_track=skill_track,
                year_index=years_completed,
                total_modifier=total_modifier,
                aging_effects=aging_effects
            )

            # Update session state
            years_completed += 1
            skill_points += 1
            skills.append(year_result.skill_gained)

            # Store the year result
            yearly_results_data.append({
                'year': year_result.year,
                'skill': year_result.skill_gained,
                'skill_roll': year_result.skill_roll,
                'surv_roll': year_result.survivability_roll,
                'surv_mod': year_result.survivability_modifier,
                'surv_total': year_result.survivability_total,
                'surv_target': year_result.survivability_target,
                'survived': year_result.survived,
                'aging': year_result.aging_penalties,
            })

            # Update aging in session
            request.session['interactive_aging'] = {
                'str': aging_effects.str_penalty,
                'dex': aging_effects.dex_penalty,
                'int': aging_effects.int_penalty,
                'wis': aging_effects.wis_penalty,
                'con': aging_effects.con_penalty,
            }

            if not year_result.survived:
                died = True
                request.session['interactive_died'] = True

            request.session['interactive_years'] = years_completed
            request.session['interactive_skills'] = skills
            request.session['interactive_skill_points'] = skill_points
            request.session['interactive_yearly_results'] = yearly_results_data

            latest_result = year_result
            current_age = 16 + years_completed

        elif action == 'stop' or action == 'finish':
            # Clear session and show final character
            final_character = build_final_character(request.session)
            clear_interactive_session(request)
            return render(request, 'generator/index.html', {
                'character': final_character,
                'years': years_completed,
                'from_interactive': True,
            })

        elif action == 'new':
            # Clear session and start over
            clear_interactive_session(request)
            return redirect('index')

    return render(request, 'generator/interactive.html', {
        'character': character,
        'years_completed': years_completed,
        'current_age': current_age,
        'yearly_results': yearly_results_data,
        'latest_result': latest_result,
        'skill_points': skill_points,
        'skills': skills,
        'can_continue': not died,
        'died': died,
        'aging': aging_data,
        'mode': 'interactive',
        'track_name': track_name,
        'survivability': survivability,
        'initial_skills': initial_skills,
    })


def serialize_character(character):
    """Serialize character to JSON-compatible dict for session storage."""
    return {
        'attributes': {
            'STR': character.attributes.STR,
            'DEX': character.attributes.DEX,
            'INT': character.attributes.INT,
            'WIS': character.attributes.WIS,
            'CON': character.attributes.CON,
            'CHR': character.attributes.CHR,
            'generation_method': character.attributes.generation_method,
        },
        'appearance': str(character.appearance),
        'height': str(character.height),
        'weight': str(character.weight),
        'provenance': str(character.provenance),
        'location': str(character.location),
        'literacy': str(character.literacy),
        'wealth': str(character.wealth),
        'skill_track': {
            'track': character.skill_track.track.value,
            'survivability': character.skill_track.survivability,
            'initial_skills': list(character.skill_track.initial_skills),
            'craft_type': character.skill_track.craft_type.value if character.skill_track.craft_type else None,
        },
        'str_repr': str(character),
    }


def deserialize_character(data):
    """Deserialize character from session data."""
    from pillars.attributes import (
        CharacterAttributes,
        generate_attributes_4d6_drop_lowest,
    )

    # Create a minimal character object for display purposes
    # We mainly need the skill_track for rolling more years
    class MinimalCharacter:
        def __init__(self, data):
            self.attributes = type('Attrs', (), {
                'STR': data['attributes']['STR'],
                'DEX': data['attributes']['DEX'],
                'INT': data['attributes']['INT'],
                'WIS': data['attributes']['WIS'],
                'CON': data['attributes']['CON'],
                'CHR': data['attributes']['CHR'],
                'generation_method': data['attributes']['generation_method'],
                'get_modifier': lambda self, attr: self._get_mod(attr),
                'get_all_modifiers': lambda self: {
                    'STR': self._get_mod('STR'),
                    'DEX': self._get_mod('DEX'),
                    'INT': self._get_mod('INT'),
                    'WIS': self._get_mod('WIS'),
                    'CON': self._get_mod('CON'),
                    'CHR': self._get_mod('CHR'),
                },
                '_get_mod': lambda self, attr: get_modifier_for_value(getattr(self, attr)),
            })()
            self.skill_track = SkillTrack(
                track=TrackType(data['skill_track']['track']),
                acceptance_check=None,
                survivability=data['skill_track']['survivability'],
                survivability_roll=None,
                initial_skills=data['skill_track']['initial_skills'],
                craft_type=CraftType(data['skill_track']['craft_type']) if data['skill_track']['craft_type'] else None,
                craft_rolls=None,
            )
            self._str_repr = data['str_repr']

        def __str__(self):
            return self._str_repr

    return MinimalCharacter(data)


def get_modifier_for_value(value):
    """Get attribute modifier for a value."""
    from pillars.attributes import ATTRIBUTE_MODIFIERS
    return ATTRIBUTE_MODIFIERS.get(value, 0)


def build_final_character(session):
    """Build final character string from session data."""
    char_data = session.get('interactive_character', {})
    years = session.get('interactive_years', 0)
    skills = session.get('interactive_skills', [])
    skill_points = session.get('interactive_skill_points', 0)
    yearly_results = session.get('interactive_yearly_results', [])
    aging_data = session.get('interactive_aging', {})
    died = session.get('interactive_died', False)

    # Build a display string
    lines = [char_data.get('str_repr', '').split('\n\n')[0]]  # Base character info

    lines.append("\n" + "=" * 60)
    lines.append(f"PRIOR EXPERIENCE ({char_data['skill_track']['track']} Track)")
    lines.append("=" * 60)
    lines.append(f"Starting Age: 16")

    if died and yearly_results:
        death_age = yearly_results[-1]['year']
        lines.append(f"DIED at age {death_age}!")
    else:
        lines.append(f"Final Age: {16 + years}")

    lines.append(f"Years Served: {years}")

    if yearly_results:
        lines.append(f"\nSurvivability Target: {yearly_results[0]['surv_target']}+")
        lines.append("Survivability Roll: 3d6 + attribute modifiers")

        lines.append("\nYear-by-Year Progression:")
        lines.append("-" * 60)

        for yr in yearly_results:
            status = "Survived" if yr['survived'] else "DIED"
            mod_str = f"{yr['surv_mod']:+d}"
            line = (f"Year {yr['year']}: {yr['skill']} (+1 SP) | "
                    f"Survival: {yr['surv_roll']}{mod_str}={yr['surv_total']} vs {yr['surv_target']}+ [{status}]")
            if yr.get('aging'):
                penalties = [f"{k} {v:+d}" for k, v in yr['aging'].items() if v != 0]
                if penalties:
                    line += f" | AGING: {', '.join(penalties)}"
            lines.append(line)

        lines.append("-" * 60)

    lines.append(f"\nTOTAL SKILL POINTS: {skill_points}")
    lines.append(f"SKILLS GAINED ({len(skills)}):")

    # Group and count skills
    skill_counts = {}
    for skill in skills:
        skill_counts[skill] = skill_counts.get(skill, 0) + 1

    for skill, count in sorted(skill_counts.items()):
        if count > 1:
            lines.append(f"  - {skill} x{count}")
        else:
            lines.append(f"  - {skill}")

    # Show aging penalties if any
    has_aging = any(v != 0 for v in aging_data.values())
    if has_aging:
        penalties = []
        if aging_data.get('str'): penalties.append(f"STR {aging_data['str']:+d}")
        if aging_data.get('dex'): penalties.append(f"DEX {aging_data['dex']:+d}")
        if aging_data.get('int'): penalties.append(f"INT {aging_data['int']:+d}")
        if aging_data.get('wis'): penalties.append(f"WIS {aging_data['wis']:+d}")
        if aging_data.get('con'): penalties.append(f"CON {aging_data['con']:+d}")
        lines.append(f"\nAging Penalties: {', '.join(penalties)}")

    if died:
        lines.append("\n" + "!" * 60)
        lines.append("THIS CHARACTER DIED DURING PRIOR EXPERIENCE!")
        lines.append("!" * 60)

    class FinalDisplay:
        def __init__(self, text, died):
            self.text = text
            self.died = died

        def __str__(self):
            return self.text

    return FinalDisplay("\n".join(lines), died)


def clear_interactive_session(request):
    """Clear interactive mode session data."""
    keys = [
        'interactive_character',
        'interactive_years',
        'interactive_skills',
        'interactive_skill_points',
        'interactive_yearly_results',
        'interactive_aging',
        'interactive_died',
        'interactive_track_name',
        'interactive_survivability',
        'interactive_initial_skills',
    ]
    for key in keys:
        if key in request.session:
            del request.session[key]
