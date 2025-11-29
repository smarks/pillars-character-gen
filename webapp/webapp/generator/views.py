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
    MagicSchool,
    get_track_availability,
    create_skill_track_for_choice,
    roll_prior_experience,
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
)


def start_over(request):
    """Clear all session data and redirect to index."""
    clear_interactive_session(request)
    clear_pending_session(request)
    return redirect('index')


def index(request):
    """Main page with generate button."""
    character = None
    years = 0  # Default value
    mode = request.POST.get('mode', 'standard')
    track_selection = request.POST.get('track_selection', 'auto')

    if request.method == 'POST':
        action = request.POST.get('action', 'generate')

        if action == 'start_over':
            return start_over(request)

        if action == 'generate':
            # Check if user wants to choose their track
            if track_selection == 'choose':
                # Generate base character and redirect to track selection
                character = generate_character(years=0)
                # Store in session for track selection page
                request.session['pending_character'] = serialize_character(character)
                request.session['pending_years'] = int(request.POST.get('years', '0'))
                request.session['pending_mode'] = mode
                # Store character stats needed for track availability
                request.session['pending_str_mod'] = character.attributes.get_modifier("STR")
                request.session['pending_dex_mod'] = character.attributes.get_modifier("DEX")
                request.session['pending_int_mod'] = character.attributes.get_modifier("INT")
                request.session['pending_wis_mod'] = character.attributes.get_modifier("WIS")
                request.session['pending_social_class'] = character.provenance.social_class
                request.session['pending_sub_class'] = character.provenance.sub_class
                request.session['pending_wealth_level'] = character.wealth.wealth_level
                return redirect('select_track')

            if mode == 'interactive':
                # Start interactive mode - generate base character with 0 years
                character = generate_character(years=0)
                # Store character state in session for interactive mode
                request.session['interactive_character'] = serialize_character(character)
                request.session['interactive_years'] = 0
                request.session['interactive_skills'] = []  # No skills until first year completed
                request.session['interactive_skill_points'] = 0
                request.session['interactive_yearly_results'] = []
                request.session['interactive_aging'] = {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0}
                request.session['interactive_died'] = False
                request.session['interactive_track_name'] = character.skill_track.track.value
                request.session['interactive_survivability'] = character.skill_track.survivability
                request.session['interactive_initial_skills'] = list(character.skill_track.initial_skills)

                # Store attribute info for survivability display
                attr_mods = character.attributes.get_all_modifiers()
                total_mod = sum(attr_mods.values())
                request.session['interactive_attr_modifiers'] = attr_mods
                request.session['interactive_total_modifier'] = total_mod

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
                    'attr_modifiers': attr_mods,
                    'total_modifier': total_mod,
                })
            else:
                years_input = request.POST.get('years', '0')
                try:
                    years = int(years_input)
                except ValueError:
                    years = 0
                character = generate_character(years=years)

                # Store character state in session so user can continue interactively
                store_character_in_session(request, character)

        elif action == 'continue_interactive':
            # User wants to continue from standard mode to interactive mode
            return redirect('interactive')

        elif action == 'finish_character':
            # User wants to finalize and show the complete character sheet
            final_character = build_final_character(request.session)
            years_completed = request.session.get('interactive_years', 0)
            clear_interactive_session(request)
            return render(request, 'generator/index.html', {
                'character': final_character,
                'years': years_completed,
                'from_interactive': True,
            })

    return render(request, 'generator/index.html', {
        'character': character,
        'years': years,
        'can_continue': character and not character.died if character else False,
    })


def select_track(request):
    """Handle skill track selection page."""
    # Check if we have a pending character
    pending_char = request.session.get('pending_character')
    if not pending_char:
        return redirect('index')

    # Get stored character info
    str_mod = request.session.get('pending_str_mod', 0)
    dex_mod = request.session.get('pending_dex_mod', 0)
    int_mod = request.session.get('pending_int_mod', 0)
    wis_mod = request.session.get('pending_wis_mod', 0)
    social_class = request.session.get('pending_social_class', 'Commoner')
    sub_class = request.session.get('pending_sub_class', 'Laborer')
    wealth_level = request.session.get('pending_wealth_level', 'Moderate')
    pending_years = request.session.get('pending_years', 0)
    pending_mode = request.session.get('pending_mode', 'standard')

    # Get track availability
    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod,
        social_class, wealth_level
    )

    # Build track info list for template
    track_info = []
    track_order = [
        TrackType.OFFICER, TrackType.RANGER, TrackType.MAGIC, TrackType.NAVY, TrackType.ARMY,
        TrackType.MERCHANT, TrackType.CRAFTS, TrackType.WORKER, TrackType.RANDOM
    ]
    for track in track_order:
        if track in track_availability:
            info = track_availability[track]
            survivability = TRACK_SURVIVABILITY.get(track, '?')
            initial_skills = TRACK_INITIAL_SKILLS.get(track, [])
            track_info.append({
                'track': track.value,
                'track_key': track.name,
                'survivability': survivability if survivability else 'Variable',
                'initial_skills': initial_skills,
                'available': info['available'],
                'requires_roll': info['requires_roll'],
                'auto_accept': info['auto_accept'],
                'impossible': info['impossible'],
                'requirement': info['requirement'],
                'roll_info': info['roll_info'],
            })

    # Reconstruct character for display
    character = deserialize_character(pending_char)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'select_track':
            chosen_track_name = request.POST.get('chosen_track', '')
            try:
                chosen_track = TrackType[chosen_track_name]
            except KeyError:
                # Invalid track, show error
                return render(request, 'generator/select_track.html', {
                    'character': character,
                    'track_info': track_info,
                    'pending_years': pending_years,
                    'pending_mode': pending_mode,
                    'error': 'Invalid track selected',
                })

            # Attempt to create skill track with chosen track
            skill_track = create_skill_track_for_choice(
                chosen_track=chosen_track,
                str_mod=str_mod,
                dex_mod=dex_mod,
                int_mod=int_mod,
                wis_mod=wis_mod,
                social_class=social_class,
                sub_class=sub_class,
                wealth_level=wealth_level,
            )

            # Check if accepted
            if not skill_track.acceptance_check.accepted:
                # Failed acceptance roll - show result and let them try again
                return render(request, 'generator/select_track.html', {
                    'character': character,
                    'track_info': track_info,
                    'pending_years': pending_years,
                    'pending_mode': pending_mode,
                    'acceptance_failed': True,
                    'failed_track': chosen_track.value,
                    'acceptance_check': skill_track.acceptance_check,
                })

            # Accepted! Now complete the character generation
            # Clear pending session data
            clear_pending_session(request)

            # Generate complete character with chosen track
            from pillars.generator import TrackType as GT
            final_character = generate_character(years=pending_years, chosen_track=chosen_track)

            if pending_mode == 'interactive':
                # Go to interactive mode
                request.session['interactive_character'] = serialize_character(final_character)
                request.session['interactive_years'] = 0
                request.session['interactive_skills'] = []
                request.session['interactive_skill_points'] = 0
                request.session['interactive_yearly_results'] = []
                request.session['interactive_aging'] = {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0}
                request.session['interactive_died'] = False
                request.session['interactive_track_name'] = final_character.skill_track.track.value
                request.session['interactive_survivability'] = final_character.skill_track.survivability
                request.session['interactive_initial_skills'] = list(final_character.skill_track.initial_skills)

                attr_mods = final_character.attributes.get_all_modifiers()
                total_mod = sum(attr_mods.values())
                request.session['interactive_attr_modifiers'] = attr_mods
                request.session['interactive_total_modifier'] = total_mod

                return render(request, 'generator/interactive.html', {
                    'character': final_character,
                    'years_completed': 0,
                    'current_age': 16,
                    'yearly_results': [],
                    'can_continue': True,
                    'mode': 'interactive',
                    'track_name': final_character.skill_track.track.value,
                    'survivability': final_character.skill_track.survivability,
                    'initial_skills': final_character.skill_track.initial_skills,
                    'attr_modifiers': attr_mods,
                    'total_modifier': total_mod,
                })
            else:
                # Standard mode - show completed character
                store_character_in_session(request, final_character)
                return render(request, 'generator/index.html', {
                    'character': final_character,
                    'years': pending_years,
                    'can_continue': not final_character.died,
                    'track_accepted': True,
                    'accepted_track': chosen_track.value,
                })

        elif action == 'cancel':
            clear_pending_session(request)
            return redirect('index')

    return render(request, 'generator/select_track.html', {
        'character': character,
        'track_info': track_info,
        'pending_years': pending_years,
        'pending_mode': pending_mode,
    })


def clear_pending_session(request):
    """Clear pending character session data."""
    keys = [
        'pending_character', 'pending_years', 'pending_mode',
        'pending_str_mod', 'pending_dex_mod', 'pending_int_mod', 'pending_wis_mod',
        'pending_social_class', 'pending_sub_class', 'pending_wealth_level',
    ]
    for key in keys:
        if key in request.session:
            del request.session[key]


def store_character_in_session(request, character):
    """Store character state in session for interactive continuation."""
    request.session['interactive_character'] = serialize_character(character)
    request.session['interactive_years'] = character.prior_experience.years_served
    # Build skills list from yearly results
    skills = []
    if character.prior_experience.years_served >= 1:
        skills.extend(character.skill_track.initial_skills)
    for yr in character.prior_experience.yearly_results:
        skills.append(yr.skill_gained)
    request.session['interactive_skills'] = skills
    request.session['interactive_skill_points'] = character.prior_experience.total_skill_points
    # Convert yearly results to session format
    yearly_results_data = []
    for yr in character.prior_experience.yearly_results:
        yearly_results_data.append({
            'year': yr.year,
            'skill': yr.skill_gained,
            'skill_roll': yr.skill_roll,
            'surv_roll': yr.survivability_roll,
            'surv_mod': yr.survivability_modifier,
            'surv_total': yr.survivability_total,
            'surv_target': yr.survivability_target,
            'survived': yr.survived,
            'aging': yr.aging_penalties or {},
        })
    request.session['interactive_yearly_results'] = yearly_results_data
    # Store aging effects
    aging_effects = character.prior_experience.aging_effects
    if aging_effects:
        request.session['interactive_aging'] = {
            'str': aging_effects.str_penalty,
            'dex': aging_effects.dex_penalty,
            'int': aging_effects.int_penalty,
            'wis': aging_effects.wis_penalty,
            'con': aging_effects.con_penalty,
        }
    else:
        request.session['interactive_aging'] = {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0}
    request.session['interactive_died'] = character.prior_experience.died
    request.session['interactive_track_name'] = character.skill_track.track.value
    request.session['interactive_survivability'] = character.skill_track.survivability
    request.session['interactive_initial_skills'] = list(character.skill_track.initial_skills)

    # Store attribute info for survivability display
    attr_mods = character.attributes.get_all_modifiers()
    total_mod = sum(attr_mods.values())
    request.session['interactive_attr_modifiers'] = attr_mods
    request.session['interactive_total_modifier'] = total_mod

    # Ensure session is saved
    request.session.modified = True
    request.session.save()


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
    attr_modifiers = request.session.get('interactive_attr_modifiers', {})
    total_modifier = request.session.get('interactive_total_modifier', 0)

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

            # Grant initial skills after completing first year (age 17)
            if years_completed == 1:
                skills.extend(initial_skills)

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
        'attr_modifiers': attr_modifiers,
        'total_modifier': total_modifier,
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
            'magic_school': character.skill_track.magic_school.value if character.skill_track.magic_school else None,
            'magic_school_rolls': character.skill_track.magic_school_rolls,
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
                craft_type=CraftType(data['skill_track']['craft_type']) if data['skill_track'].get('craft_type') else None,
                craft_rolls=None,
                magic_school=MagicSchool(data['skill_track']['magic_school']) if data['skill_track'].get('magic_school') else None,
                magic_school_rolls=data['skill_track'].get('magic_school_rolls'),
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

    # Build a display string - include full character info
    lines = [char_data.get('str_repr', '')]  # Full base character info

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
        'interactive_attr_modifiers',
        'interactive_total_modifier',
    ]
    for key in keys:
        if key in request.session:
            del request.session[key]
