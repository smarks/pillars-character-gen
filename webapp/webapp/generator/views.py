"""
Django views for the Pillars Character Generator web application.

This module handles all the web UI for character generation. The main user flow is:

1. WELCOME PAGE (welcome view)
   - Entry point with links to Generator, Lore, and Handbook

2. CHARACTER GENERATOR (index view)
   - Auto-generates a character on first load (without skill track)
   - User sees their stats and can:
     - Re-roll with different attribute focus options
     - Add Prior Experience (goes to track selection)
     - Finish (shows final character sheet)

3. TRACK SELECTION (select_track view)
   - User chooses a skill track (Ranger, Army, Magic, etc.)
   - Some tracks require acceptance rolls
   - After selection, redirects to interactive mode

4. INTERACTIVE MODE (interactive view)
   - Year-by-year prior experience
   - Each year: roll survival, gain skill, check for death
   - User can stop anytime and return to generator

5. FINISHED CHARACTER (finished.html template)
   - Pretty-printed character sheet for printing

Session Keys Used:
    - current_character: The main character data (serialized dict)
    - pending_*: Temporary data during track selection flow
    - interactive_*: Data for the interactive prior experience mode
"""
import json
import os
import markdown
from django.shortcuts import render, redirect
from django.conf import settings
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


def welcome(request):
    """Welcome page with links to main sections."""
    return render(request, 'generator/welcome.html')


def lore(request):
    """Lore page - placeholder for now."""
    return render(request, 'generator/lore.html')


def handbook(request):
    """Display the Player's Handbook."""
    # Path to the handbook markdown file
    handbook_path = os.path.join(settings.BASE_DIR, '..', 'A Pillars Handbook.md')

    try:
        with open(handbook_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove the YAML frontmatter if present
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]

        # Convert markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'toc']
        )
    except FileNotFoundError:
        html_content = "<p>Handbook not found.</p>"

    return render(request, 'generator/handbook.html', {'content': html_content})


def start_over(request):
    """Clear all session data and redirect to welcome page."""
    clear_interactive_session(request)
    clear_pending_session(request)
    return redirect('welcome')


def index(request):
    """
    Main character generator page.

    This is the primary view for character creation. On GET request, it either:
    - Generates a new character (if none in session)
    - Displays the existing character (if returning from prior experience)

    On POST request, it handles these actions:
    - 'reroll_none': Generate new character with random attributes
    - 'reroll_physical': Generate new character guaranteed STR or DEX +1
    - 'reroll_mental': Generate new character guaranteed INT or WIS +1
    - 'add_experience': Redirect to track selection, then interactive mode
    - 'finish': Show the final character sheet

    Important: Initial characters are generated with skip_track=True so they
    don't have a skill track or prior experience yet. This lets users review
    their base stats before committing to a career path.

    Template: generator/index.html
    """
    action = request.POST.get('action', '') if request.method == 'POST' else ''

    # Handle different actions
    if action == 'reroll_none':
        # Re-roll with no focus - skip_track for initial character
        character = generate_character(years=0, attribute_focus=None, skip_track=True)
        store_current_character(request, character)

    elif action == 'reroll_physical':
        # Re-roll with physical focus (STR/DEX)
        character = generate_character(years=0, attribute_focus='physical', skip_track=True)
        store_current_character(request, character)

    elif action == 'reroll_mental':
        # Re-roll with mental focus (INT/WIS)
        character = generate_character(years=0, attribute_focus='mental', skip_track=True)
        store_current_character(request, character)

    elif action == 'add_experience':
        # Go to track selection first, then interactive mode
        char_data = request.session.get('current_character')
        if char_data:
            # Store character info for track selection
            character = deserialize_character(char_data)
            request.session['pending_character'] = char_data
            request.session['pending_years'] = 0
            request.session['pending_mode'] = 'interactive'
            request.session['pending_str_mod'] = character.attributes.get_modifier('STR')
            request.session['pending_dex_mod'] = character.attributes.get_modifier('DEX')
            request.session['pending_int_mod'] = character.attributes.get_modifier('INT')
            request.session['pending_wis_mod'] = character.attributes.get_modifier('WIS')
            request.session['pending_social_class'] = char_data.get('provenance_social_class', 'Commoner')
            request.session['pending_sub_class'] = char_data.get('provenance_sub_class', 'Laborer')
            request.session['pending_wealth_level'] = char_data.get('wealth_level', 'Moderate')
            request.session['pending_return_to_generator'] = True
            return redirect('select_track')
        else:
            # No character, generate one
            character = generate_character(years=0, skip_track=True)
            store_current_character(request, character)

    elif action == 'finish':
        # Show finished character page
        char_data = request.session.get('current_character')
        if char_data:
            return render(request, 'generator/finished.html', {
                'character_data': char_data,
                'years': request.session.get('interactive_years', 0),
                'skills': request.session.get('interactive_skills', []),
                'yearly_results': request.session.get('interactive_yearly_results', []),
                'aging': request.session.get('interactive_aging', {}),
                'died': request.session.get('interactive_died', False),
            })
        # No character, redirect to generate
        character = generate_character(years=0, skip_track=True)
        store_current_character(request, character)

    else:
        # GET request or unknown action - check for existing character or generate new
        char_data = request.session.get('current_character')
        if char_data and not action:
            # Return from prior experience - use existing character
            character = deserialize_character(char_data)
        else:
            # Generate new character without track/experience
            character = generate_character(years=0, skip_track=True)
            store_current_character(request, character)

    # Get prior experience info if any
    years_completed = request.session.get('interactive_years', 0)
    skills = request.session.get('interactive_skills', [])
    yearly_results = request.session.get('interactive_yearly_results', [])

    return render(request, 'generator/index.html', {
        'character': character,
        'years_completed': years_completed,
        'skills': skills,
        'yearly_results': yearly_results,
        'has_experience': years_completed > 0,
    })


def store_current_character(request, character):
    """Store character in session for the generator flow."""
    request.session['current_character'] = serialize_character(character)
    # Clear any prior experience data when re-rolling
    request.session['interactive_years'] = 0
    request.session['interactive_skills'] = []
    request.session['interactive_yearly_results'] = []
    request.session['interactive_aging'] = {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0}
    request.session['interactive_died'] = False
    request.session.modified = True


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
    pending_attribute_focus = request.session.get('pending_attribute_focus', 'none')

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
            # Save return_to_generator flag before clearing pending session
            return_to_generator = request.session.get('pending_return_to_generator', False)

            # Clear pending session data
            clear_pending_session(request)

            # Generate complete character with chosen track
            # Convert 'none' to None for the generator
            focus = pending_attribute_focus if pending_attribute_focus != 'none' else None
            from pillars.generator import TrackType as GT
            final_character = generate_character(
                years=pending_years,
                chosen_track=chosen_track,
                attribute_focus=focus
            )

            if pending_mode == 'interactive':
                # For interactive mode, we track experience separately in session
                # variables, so set prior_experience to None to avoid showing
                # a confusing "Years Served: 0" in the character display
                final_character.prior_experience = None

                # Store character with skill track in session for generator
                request.session['current_character'] = serialize_character(final_character)

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

                # Set return to generator flag if coming from new generator flow
                if return_to_generator:
                    request.session['interactive_return_to_generator'] = True

                attr_mods = final_character.attributes.get_all_modifiers()
                total_mod = sum(attr_mods.values())
                request.session['interactive_attr_modifiers'] = attr_mods
                request.session['interactive_total_modifier'] = total_mod

                # Redirect to interactive page instead of rendering directly
                return redirect('interactive')
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
        'pending_attribute_focus', 'pending_return_to_generator',
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
            # Check if we should return to the generator page
            return_to_generator = request.session.get('interactive_return_to_generator', False)

            if return_to_generator:
                # Clear the flag but keep experience data for the generator
                del request.session['interactive_return_to_generator']
                request.session.modified = True
                return redirect('generator')
            else:
                # Original behavior - clear session and show final character
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
    data = {
        'attributes': {
            'STR': character.attributes.STR,
            'DEX': character.attributes.DEX,
            'INT': character.attributes.INT,
            'WIS': character.attributes.WIS,
            'CON': character.attributes.CON,
            'CHR': character.attributes.CHR,
            'generation_method': character.attributes.generation_method,
            'fatigue_points': character.attributes.fatigue_points,
            'body_points': character.attributes.body_points,
            'fatigue_roll': character.attributes.fatigue_roll,
            'body_roll': character.attributes.body_roll,
        },
        'appearance': str(character.appearance),
        'height': str(character.height),
        'weight': str(character.weight),
        'provenance': str(character.provenance),
        'provenance_social_class': character.provenance.social_class if hasattr(character.provenance, 'social_class') else 'Commoner',
        'provenance_sub_class': character.provenance.sub_class if hasattr(character.provenance, 'sub_class') else 'Laborer',
        'location': str(character.location),
        'literacy': str(character.literacy),
        'wealth': str(character.wealth),
        'wealth_level': character.wealth.wealth_level if hasattr(character.wealth, 'wealth_level') else 'Moderate',
        'str_repr': str(character),
    }

    # Only include skill_track if it exists
    if character.skill_track is not None:
        data['skill_track'] = {
            'track': character.skill_track.track.value,
            'survivability': character.skill_track.survivability,
            'initial_skills': list(character.skill_track.initial_skills),
            'craft_type': character.skill_track.craft_type.value if character.skill_track.craft_type else None,
            'magic_school': character.skill_track.magic_school.value if character.skill_track.magic_school else None,
            'magic_school_rolls': character.skill_track.magic_school_rolls,
        }
    else:
        data['skill_track'] = None

    return data


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
                'fatigue_points': data['attributes'].get('fatigue_points', 0),
                'body_points': data['attributes'].get('body_points', 0),
                'fatigue_roll': data['attributes'].get('fatigue_roll', 0),
                'body_roll': data['attributes'].get('body_roll', 0),
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

            # Handle None skill_track (initial character without track assigned)
            if data.get('skill_track') is not None:
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
            else:
                self.skill_track = None

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
        'interactive_return_to_generator',
    ]
    for key in keys:
        if key in request.session:
            del request.session[key]
