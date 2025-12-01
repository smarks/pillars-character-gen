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
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.decorators import login_required


class RegistrationForm(UserCreationForm):
    """Custom registration form with optional contact fields."""
    email = forms.EmailField(required=False, help_text='Optional')
    # Only show player/dm choices during registration (admin is assigned manually)
    REGISTRATION_ROLE_CHOICES = [
        ('player', 'Player'),
        ('dm', 'Dungeon Master'),
    ]
    role = forms.ChoiceField(choices=REGISTRATION_ROLE_CHOICES, initial='player', help_text='Select your role')
    phone = forms.CharField(max_length=20, required=False, help_text='Optional - for SMS notifications')
    discord_handle = forms.CharField(max_length=100, required=False, help_text='Optional - e.g. username#1234')
    preferred_contact = forms.ChoiceField(
        choices=[('', 'Not specified')] + UserProfile.CONTACT_METHOD_CHOICES,
        required=False,
        initial='',
        help_text='How would you like to be contacted for game notifications?'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'phone', 'discord_handle', 'preferred_contact')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            role = self.cleaned_data.get('role', 'player')
            UserProfile.objects.create(
                user=user,
                roles=[role],  # Store as list
                phone=self.cleaned_data.get('phone', ''),
                discord_handle=self.cleaned_data.get('discord_handle', ''),
                preferred_contact=self.cleaned_data.get('preferred_contact', ''),
            )
        return user


class AdminUserCreationForm(UserCreationForm):
    """Admin form for creating users with full role access."""
    email = forms.EmailField(required=False, help_text='Optional')
    roles = forms.MultipleChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Select one or more roles for this user'
    )
    phone = forms.CharField(max_length=20, required=False, help_text='Optional - for SMS notifications')
    discord_handle = forms.CharField(max_length=100, required=False, help_text='Optional - e.g. username#1234')
    preferred_contact = forms.ChoiceField(
        choices=[('', 'Not specified')] + UserProfile.CONTACT_METHOD_CHOICES,
        required=False,
        initial='',
        help_text='Preferred contact method'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'roles', 'phone', 'discord_handle', 'preferred_contact')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            roles = self.cleaned_data.get('roles', [])
            UserProfile.objects.create(
                user=user,
                roles=list(roles),  # Store as list
                phone=self.cleaned_data.get('phone', ''),
                discord_handle=self.cleaned_data.get('discord_handle', ''),
                preferred_contact=self.cleaned_data.get('preferred_contact', ''),
            )
        return user


from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import SavedCharacter
from pillars import generate_character
from pillars.generator import consolidate_skills
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
    """Welcome page with links to main sections.

    Clears any existing character data so clicking 'Character Generator'
    starts a fresh character.
    """
    # Clear character session data
    request.session.pop('current_character', None)
    request.session.pop('interactive_years', None)
    request.session.pop('interactive_skills', None)
    request.session.pop('interactive_yearly_results', None)
    request.session.pop('interactive_aging', None)
    request.session.pop('interactive_died', None)
    request.session.pop('pending_character', None)
    request.session.modified = True

    return render(request, 'generator/welcome.html')


def extract_section(content, start_tag, end_patterns):
    """Extract content between tags from the handbook.

    Args:
        content: Full file content
        start_tag: Tag to search for (e.g., '-- meta --')
        end_patterns: List of possible end tag patterns to try

    Returns:
        Extracted content or None if not found
    """
    import re

    # Find start tag
    start_match = re.search(re.escape(start_tag), content, re.IGNORECASE)
    if not start_match:
        return None

    start_pos = start_match.end()

    # Try each end pattern
    end_pos = len(content)
    for end_pattern in end_patterns:
        end_match = re.search(end_pattern, content[start_pos:], re.IGNORECASE)
        if end_match:
            end_pos = start_pos + end_match.start()
            break

    return content[start_pos:end_pos].strip()


def get_handbook_content():
    """Read the handbook file."""
    handbook_path = os.path.join(settings.BASE_DIR, '..', 'A Pillars Handbook.md')
    try:
        with open(handbook_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def meta(request):
    """Display the Meta/About section."""
    content = get_handbook_content()

    if content:
        section = extract_section(
            content,
            '-- meta --',
            [r'--\s*/\s*meta\s*--', r'--\s*lore\s*--']
        )
        if section:
            html_content = markdown.markdown(
                section,
                extensions=['tables', 'fenced_code', 'toc']
            )
        else:
            html_content = "<p>Meta section not found.</p>"
    else:
        html_content = "<p>Handbook not found.</p>"

    return render(request, 'generator/meta.html', {'content': html_content})


def lore(request):
    """Display the Lore/Background section."""
    content = get_handbook_content()

    if content:
        section = extract_section(
            content,
            '-- lore --',
            [r'--\s*/\s*lore\s*--', r'--\s*players_handbook\s*--']
        )
        if section:
            html_content = markdown.markdown(
                section,
                extensions=['tables', 'fenced_code', 'toc']
            )
        else:
            html_content = "<p>Lore section not found.</p>"
    else:
        html_content = "<p>Handbook not found.</p>"

    return render(request, 'generator/lore.html', {'content': html_content})


def handbook(request):
    """Display the Player's Handbook."""
    content = get_handbook_content()

    if content:
        section = extract_section(
            content,
            '-- players_handbook --',
            [r'--\s*/\s*Player.handoo?k\s*--', r'--\s*DM_handbook\s*--']
        )
        if section:
            html_content = markdown.markdown(
                section,
                extensions=['tables', 'fenced_code', 'toc']
            )
        else:
            html_content = "<p>Player's Handbook section not found.</p>"
    else:
        html_content = "<p>Handbook not found.</p>"

    return render(request, 'generator/handbook.html', {'content': html_content})


def dm_handbook(request):
    """Display the DM Handbook section."""
    content = get_handbook_content()

    if content:
        section = extract_section(
            content,
            '-- DM_handbook --',
            [r'--\s*/\s*DM_handbook\s*--']
        )
        if section:
            html_content = markdown.markdown(
                section,
                extensions=['tables', 'fenced_code', 'toc']
            )
        else:
            html_content = "<p>DM Handbook section not found.</p>"
    else:
        html_content = "<p>Handbook not found.</p>"

    return render(request, 'generator/dm_handbook.html', {'content': html_content})


def start_over(request):
    """Clear all session data and redirect to welcome page."""
    clear_interactive_session(request)
    clear_pending_session(request)
    # Also clear the current character
    if 'current_character' in request.session:
        del request.session['current_character']
    request.session.modified = True
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
            # No character in session - generate one and then redirect to track selection
            character = generate_character(years=0, skip_track=True)
            store_current_character(request, character)
            # Now redirect to track selection with the new character
            char_data = request.session.get('current_character')
            request.session['pending_character'] = char_data
            request.session['pending_years'] = 0
            request.session['pending_mode'] = 'interactive'
            request.session['pending_str_mod'] = character.attributes.get_modifier('STR')
            request.session['pending_dex_mod'] = character.attributes.get_modifier('DEX')
            request.session['pending_int_mod'] = character.attributes.get_modifier('INT')
            request.session['pending_wis_mod'] = character.attributes.get_modifier('WIS')
            request.session['pending_social_class'] = str(character.provenance.social_class) if hasattr(character.provenance, 'social_class') else 'Commoner'
            request.session['pending_sub_class'] = str(character.provenance.sub_class) if hasattr(character.provenance, 'sub_class') else 'Laborer'
            request.session['pending_wealth_level'] = character.wealth.wealth_level if hasattr(character.wealth, 'wealth_level') else 'Moderate'
            request.session['pending_return_to_generator'] = True
            return redirect('select_track')

    elif action == 'finish':
        # Show finished character page
        char_data = request.session.get('current_character')
        if char_data:
            years = request.session.get('interactive_years', 0)
            skills = request.session.get('interactive_skills', [])
            yearly_results = request.session.get('interactive_yearly_results', [])
            aging = request.session.get('interactive_aging', {})
            died = request.session.get('interactive_died', False)

            # Build complete str_repr with experience data
            final_str_repr = build_final_str_repr(char_data, years, skills, yearly_results, aging, died)
            char_data_with_repr = dict(char_data)
            char_data_with_repr['str_repr'] = final_str_repr

            return render(request, 'generator/finished.html', {
                'character_data': char_data_with_repr,
                'has_experience': years > 0,
                'died': died,
            })
        # No character in session - generate one and show finished page
        character = generate_character(years=0, skip_track=True)
        store_current_character(request, character)
        char_data = request.session.get('current_character')
        return render(request, 'generator/finished.html', {
            'character_data': char_data,
            'has_experience': False,
            'died': False,
        })

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
        'current_age': 16 + years_completed,
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
    """
    Handle prior experience page with track selection.

    This page allows the user to:
    - Choose years of experience (1-10) or interactive mode
    - Auto-select or manually select a skill track
    - Finish without experience, or add experience
    """
    # Check if we have a pending character
    pending_char = request.session.get('pending_character')
    if not pending_char:
        return redirect('generator')

    # Get stored character info
    str_mod = request.session.get('pending_str_mod', 0)
    dex_mod = request.session.get('pending_dex_mod', 0)
    int_mod = request.session.get('pending_int_mod', 0)
    wis_mod = request.session.get('pending_wis_mod', 0)
    social_class = request.session.get('pending_social_class', 'Commoner')
    sub_class = request.session.get('pending_sub_class', 'Laborer')
    wealth_level = request.session.get('pending_wealth_level', 'Moderate')

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

        if action == 'start_over':
            clear_pending_session(request)
            return redirect('start_over')

        elif action == 'finish':
            # Finish without experience - go to final character display
            clear_pending_session(request)
            char_data = request.session.get('current_character')
            if char_data:
                # Use str_repr as-is since no experience was added
                return render(request, 'generator/finished.html', {
                    'character_data': char_data,
                    'has_experience': False,
                    'died': False,
                })
            return redirect('generator')

        elif action == 'add_experience':
            # Get form data
            interactive_mode = request.POST.get('interactive_mode') == 'on'
            track_mode = request.POST.get('track_mode', 'auto')
            years = int(request.POST.get('years', 5)) if not interactive_mode else 0
            chosen_track_name = request.POST.get('chosen_track', '')

            # Determine the track to use
            chosen_track = None
            if track_mode == 'manual':
                if not chosen_track_name:
                    return render(request, 'generator/select_track.html', {
                        'character': character,
                        'track_info': track_info,
                        'current_age': 16,
                        'error': 'Please select a track when using manual selection',
                    })
                try:
                    chosen_track = TrackType[chosen_track_name]
                except KeyError:
                    return render(request, 'generator/select_track.html', {
                        'character': character,
                        'track_info': track_info,
                        'current_age': 16,
                        'error': 'Invalid track selected',
                    })

                # Check acceptance for manual track
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

                if not skill_track.acceptance_check.accepted:
                    return render(request, 'generator/select_track.html', {
                        'character': character,
                        'track_info': track_info,
                        'current_age': 16,
                        'acceptance_failed': True,
                        'failed_track': chosen_track.value,
                        'acceptance_check': skill_track.acceptance_check,
                    })

            # Clear pending session data
            clear_pending_session(request)

            # Generate character with experience
            if interactive_mode:
                # Interactive mode - generate character with track but no years yet
                final_character = generate_character(
                    years=0,
                    chosen_track=chosen_track,  # None for auto, or specific track
                )
                final_character.prior_experience = None

                # Store character and go to interactive mode
                request.session['current_character'] = serialize_character(final_character)
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
                request.session['interactive_return_to_generator'] = True

                attr_mods = final_character.attributes.get_all_modifiers()
                total_mod = sum(attr_mods.values())
                request.session['interactive_attr_modifiers'] = attr_mods
                request.session['interactive_total_modifier'] = total_mod

                return redirect('interactive')
            else:
                # Standard mode - add years of experience
                # Check if we already have experience (adding more years)
                existing_years = request.session.get('interactive_years', 0)
                existing_skills = request.session.get('interactive_skills', [])
                existing_yearly_results = request.session.get('interactive_yearly_results', [])
                existing_aging = request.session.get('interactive_aging', {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0})

                if existing_years > 0:
                    # Adding MORE experience to existing character
                    character = deserialize_character(pending_char)
                    skill_track = character.skill_track
                    total_modifier = sum(character.attributes.get_all_modifiers().values())

                    # Reconstruct aging effects from session
                    aging_effects = AgingEffects(
                        str_penalty=existing_aging.get('str', 0),
                        dex_penalty=existing_aging.get('dex', 0),
                        int_penalty=existing_aging.get('int', 0),
                        wis_penalty=existing_aging.get('wis', 0),
                        con_penalty=existing_aging.get('con', 0),
                    )

                    # Roll additional years
                    new_yearly_results = []
                    new_skills = []
                    died = False
                    for i in range(years):
                        year_index = existing_years + i
                        year_result = roll_single_year(
                            skill_track=skill_track,
                            year_index=year_index,
                            total_modifier=total_modifier,
                            aging_effects=aging_effects
                        )
                        new_skills.append(year_result.skill_gained)
                        new_yearly_results.append({
                            'year': year_result.year,
                            'skill': year_result.skill_gained,
                            'surv_roll': year_result.survivability_roll,
                            'surv_mod': year_result.survivability_modifier,
                            'surv_total': year_result.survivability_total,
                            'surv_target': year_result.survivability_target,
                            'survived': year_result.survived,
                        })
                        if not year_result.survived:
                            died = True
                            break

                    # Append to existing experience
                    all_skills = existing_skills + new_skills
                    all_yearly_results = existing_yearly_results + new_yearly_results
                    total_years = existing_years + len(new_yearly_results)

                    # Store updated experience data in session
                    request.session['interactive_years'] = total_years
                    request.session['interactive_skills'] = all_skills
                    request.session['interactive_yearly_results'] = all_yearly_results
                    request.session['interactive_died'] = died
                    request.session['interactive_aging'] = {
                        'str': aging_effects.str_penalty,
                        'dex': aging_effects.dex_penalty,
                        'int': aging_effects.int_penalty,
                        'wis': aging_effects.wis_penalty,
                        'con': aging_effects.con_penalty,
                    }

                    # Redirect back to prior experience page
                    return redirect('select_track')

                # First time adding experience - generate character with track
                final_character = generate_character(
                    years=years,
                    chosen_track=chosen_track,  # None for auto, or specific track
                )

                # Store character in session
                request.session['current_character'] = serialize_character(final_character)

                # Build yearly results for display and store in session
                yearly_results = []
                skills = []
                if final_character.prior_experience:
                    skills = list(final_character.skill_track.initial_skills)
                    for yr in final_character.prior_experience.yearly_results:
                        skills.append(yr.skill_gained)
                        yearly_results.append({
                            'year': yr.year,
                            'skill': yr.skill_gained,
                            'surv_roll': yr.survivability_roll,
                            'surv_mod': yr.survivability_modifier,
                            'surv_total': yr.survivability_total,
                            'surv_target': yr.survivability_target,
                            'survived': yr.survived,
                        })

                # Store experience data in session
                request.session['interactive_years'] = years
                request.session['interactive_skills'] = skills
                request.session['interactive_yearly_results'] = yearly_results
                request.session['interactive_died'] = final_character.died
                request.session['interactive_track_name'] = final_character.skill_track.track.value
                request.session['interactive_survivability'] = final_character.skill_track.survivability

                # Keep pending session so we stay on prior experience page
                request.session['pending_character'] = serialize_character(final_character)
                request.session['pending_str_mod'] = final_character.attributes.get_modifier('STR')
                request.session['pending_dex_mod'] = final_character.attributes.get_modifier('DEX')
                request.session['pending_int_mod'] = final_character.attributes.get_modifier('INT')
                request.session['pending_wis_mod'] = final_character.attributes.get_modifier('WIS')

                # Redirect back to prior experience page
                return redirect('select_track')

    # Get experience data if any
    years_completed = request.session.get('interactive_years', 0)
    skills = request.session.get('interactive_skills', [])
    yearly_results = request.session.get('interactive_yearly_results', [])
    died = request.session.get('interactive_died', False)
    track_name = request.session.get('interactive_track_name', '')

    return render(request, 'generator/select_track.html', {
        'character': character,
        'track_info': track_info,
        'years_completed': years_completed,
        'current_age': 16 + years_completed,
        'skills': skills,
        'yearly_results': yearly_results,
        'died': died,
        'has_experience': years_completed > 0,
        'current_track': track_name,
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

        elif action == 'stop':
            # Go back to generator to add more experience
            if 'interactive_return_to_generator' in request.session:
                del request.session['interactive_return_to_generator']
            request.session.modified = True
            return redirect('generator')

        elif action == 'finish':
            # Show the finished character sheet
            char_data = request.session.get('current_character')
            if char_data:
                # Build complete str_repr with experience data
                final_str_repr = build_final_str_repr(char_data, years_completed, skills, yearly_results_data, aging_data, died)
                char_data_with_repr = dict(char_data)
                char_data_with_repr['str_repr'] = final_str_repr

                return render(request, 'generator/finished.html', {
                    'character_data': char_data_with_repr,
                    'has_experience': years_completed > 0,
                    'died': died,
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
        'location_skills': list(character.location.skills) if character.location.skills else [],
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


def build_final_str_repr(char_data, years, skills, yearly_results, aging_data, died):
    """Build a complete str_repr for a character with prior experience."""
    # Start with the base character info (without skill track/experience sections)
    base_repr = char_data.get('str_repr', '')

    # If no experience, return base repr
    if years == 0:
        return base_repr

    # Filter out sections we'll rebuild, and location skill/attribute lines
    lines = base_repr.split('\n')
    filtered_lines = []
    skip_section = False
    in_location = False

    for line in lines:
        # Check for sections to skip entirely
        if any(marker in line for marker in ['**Skill Track:**', '**Prior Experience**', '**Skills**', '**Year-by-Year**']):
            skip_section = True
            continue

        # Track if we're in Location section (to filter its sub-items)
        if line.startswith('Location:'):
            in_location = True
            filtered_lines.append(line)
            continue

        # Skip location sub-items (Skills, Attribute Modifiers)
        if in_location:
            if line.startswith('  '):
                # Skip indented location details (skills, attribute modifiers)
                continue
            else:
                # No longer in location section
                in_location = False

        # Handle skipped sections
        if skip_section:
            # End skip on blank line or new ** section
            if line.strip() == '':
                skip_section = False
                continue
            elif line.startswith('**'):
                skip_section = False
                # Check if this new section should also be skipped
                if any(marker in line for marker in ['**Skill Track:**', '**Prior Experience**', '**Skills**', '**Year-by-Year**']):
                    skip_section = True
                    continue
                filtered_lines.append(line)
            continue

        filtered_lines.append(line)

    result_lines = filtered_lines

    # Add skill track info
    if char_data.get('skill_track'):
        track_info = char_data['skill_track']
        result_lines.append('')
        result_lines.append(f"**Skill Track:** {track_info['track']}")
        result_lines.append(f"Survivability: {track_info['survivability']}+")
        if track_info.get('craft_type'):
            result_lines.append(f"Craft: {track_info['craft_type']}")
        if track_info.get('magic_school'):
            result_lines.append(f"Magic School: {track_info['magic_school']}")

    # Add prior experience section
    result_lines.append('')
    result_lines.append('**Prior Experience**')
    result_lines.append('Starting Age: 16')

    if died and yearly_results:
        death_age = yearly_results[-1]['year']
        result_lines.append(f"DIED at age {death_age}!")
    else:
        result_lines.append(f"Final Age: {16 + years}")

    result_lines.append(f"Years Served: {years}")

    if yearly_results:
        result_lines.append(f"Survivability Target: {yearly_results[0]['surv_target']}+")

        # Calculate total modifier from first year result
        result_lines.append(f"Total Modifier: {yearly_results[0]['surv_mod']:+d}")

    # Show aging penalties if any
    has_aging = any(v != 0 for v in aging_data.values())
    if has_aging:
        penalties = []
        if aging_data.get('str'): penalties.append(f"STR {aging_data['str']:+d}")
        if aging_data.get('dex'): penalties.append(f"DEX {aging_data['dex']:+d}")
        if aging_data.get('int'): penalties.append(f"INT {aging_data['int']:+d}")
        if aging_data.get('wis'): penalties.append(f"WIS {aging_data['wis']:+d}")
        if aging_data.get('con'): penalties.append(f"CON {aging_data['con']:+d}")
        result_lines.append('')
        result_lines.append(f"**Aging Penalties:** {', '.join(penalties)}")

    if died:
        result_lines.append('')
        result_lines.append('**THIS CHARACTER DIED DURING PRIOR EXPERIENCE!**')

    # Add consolidated skills section
    all_skills = []

    # Add location skills
    location_skills = char_data.get('location_skills', [])
    all_skills.extend(location_skills)

    # Add track initial skills and prior experience skills
    initial_skills = char_data.get('skill_track', {}).get('initial_skills', []) if char_data.get('skill_track') else []
    all_skills.extend(initial_skills)
    all_skills.extend(skills)

    if all_skills:
        result_lines.append('')
        result_lines.append(f"**Skills** ({len(all_skills)})")
        for skill in consolidate_skills(all_skills):
            result_lines.append(f"- {skill}")

    # Add Year-by-Year log at the bottom
    if yearly_results:
        result_lines.append('')
        result_lines.append('**Year-by-Year Log**')

        for yr in yearly_results:
            status = "Survived" if yr['survived'] else "DIED"
            mod_str = f"{yr['surv_mod']:+d}"
            line = (f"Year {yr['year']}: {yr['skill']} (+1 SP) | "
                    f"Survival: {yr['surv_roll']}{mod_str}={yr['surv_total']} vs {yr['surv_target']}+ [{status}]")
            if yr.get('aging'):
                penalties = [f"{k.upper()} {v:+d}" for k, v in yr['aging'].items() if v != 0]
                if penalties:
                    line += f" | AGING: {', '.join(penalties)}"
            result_lines.append(line)

    return '\n'.join(result_lines)


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

def handbook_section(request, section: str):
    """Generic view for handbook sections loaded from markdown files."""
    import os
    from django.conf import settings

    # Path to the docs directory
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    section_path = os.path.join(docs_dir, f'{section}.md')

    try:
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        html_content = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'toc']
        )
    except FileNotFoundError:
        html_content = f"<p>Section '{section}' not found.</p>"

    # Load section manifest for title
    manifest_path = os.path.join(docs_dir, 'sections.json')
    title = section.replace('_', ' ').title()
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            for s in manifest.get('sections', []):
                if s.get('tag') == section:
                    title = s.get('display_name', title)
                    break
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return render(request, 'generator/handbook_section.html', {
        'content': html_content,
        'title': title,
    })


# =============================================================================
# Authentication Views
# =============================================================================

def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('welcome')
    else:
        form = RegistrationForm()

    return render(request, 'generator/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'welcome')
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'generator/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('welcome')


# =============================================================================
# Character Save/Load Views
# =============================================================================

@login_required
@require_POST
def save_character(request):
    """Save the current character for the logged-in user."""
    char_data = request.session.get('current_character')
    if not char_data:
        return JsonResponse({'error': 'No character to save'}, status=400)

    # Get character name from the data or generate one
    name = request.POST.get('name', '')
    if not name:
        # Try to extract name from provenance or use a default
        name = f"Character {SavedCharacter.objects.filter(user=request.user).count() + 1}"

    # Include experience data if present
    save_data = dict(char_data)
    save_data['interactive_years'] = request.session.get('interactive_years', 0)
    save_data['interactive_skills'] = request.session.get('interactive_skills', [])
    save_data['interactive_yearly_results'] = request.session.get('interactive_yearly_results', [])
    save_data['interactive_aging'] = request.session.get('interactive_aging', {})
    save_data['interactive_died'] = request.session.get('interactive_died', False)

    # Create or update the saved character
    saved_char = SavedCharacter.objects.create(
        user=request.user,
        name=name,
        character_data=save_data
    )

    return JsonResponse({
        'success': True,
        'id': saved_char.id,
        'name': saved_char.name
    })


@login_required
def my_characters(request):
    """List all saved characters for the logged-in user."""
    characters = SavedCharacter.objects.filter(user=request.user)
    return render(request, 'generator/my_characters.html', {'characters': characters})


@login_required
def load_character(request, char_id):
    """Load a saved character into the session."""
    try:
        saved_char = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, 'Character not found.')
        return redirect('my_characters')

    # Load character data into session
    char_data = saved_char.character_data
    request.session['current_character'] = {
        k: v for k, v in char_data.items()
        if not k.startswith('interactive_')
    }

    # Load experience data if present
    request.session['interactive_years'] = char_data.get('interactive_years', 0)
    request.session['interactive_skills'] = char_data.get('interactive_skills', [])
    request.session['interactive_yearly_results'] = char_data.get('interactive_yearly_results', [])
    request.session['interactive_aging'] = char_data.get('interactive_aging', {})
    request.session['interactive_died'] = char_data.get('interactive_died', False)
    request.session.modified = True

    messages.success(request, f'Loaded character: {saved_char.name}')
    return redirect('generator')


@login_required
@require_POST
def delete_character(request, char_id):
    """Delete a saved character."""
    try:
        saved_char = SavedCharacter.objects.get(id=char_id, user=request.user)
        name = saved_char.name
        saved_char.delete()
        messages.success(request, f'Deleted character: {name}')
    except SavedCharacter.DoesNotExist:
        messages.error(request, 'Character not found.')

    return redirect('my_characters')


# =============================================================================
# DM-Only Views
# =============================================================================

def dm_required(view_func):
    """Decorator that requires user to be a DM or Admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not (request.user.profile.is_dm or request.user.profile.is_admin):
            messages.error(request, 'You must be a Dungeon Master to access this page.')
            return redirect('welcome')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator that requires user to be an Admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
            messages.error(request, 'You must be an Admin to access this page.')
            return redirect('welcome')
        return view_func(request, *args, **kwargs)
    return wrapper


@dm_required
def dm_handbook(request):
    """DM Handbook - requires DM or Admin role."""
    return handbook_section(request, 'DM_handbook')


@admin_required
def manage_users(request):
    """Admin view to manage user roles and create new users."""
    users = UserProfile.objects.select_related('user').all()
    role_choices = UserProfile.ROLE_CHOICES

    # Handle user creation form submission
    if request.method == 'POST' and 'create_user' in request.POST:
        create_form = AdminUserCreationForm(request.POST)
        if create_form.is_valid():
            user = create_form.save()
            messages.success(request, f"Successfully created user: {user.username}")
            return redirect('manage_users')
        else:
            # Form has errors - will be displayed in template
            pass
    else:
        # Create empty form for GET requests
        create_form = AdminUserCreationForm()

    return render(request, 'generator/manage_users.html', {
        'users': users,
        'role_choices': role_choices,
        'create_form': create_form,
    })


@admin_required
@require_POST
def change_user_role(request, user_id):
    """Change a user's roles (Admin only)."""
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        # Get list of roles from form (checkboxes)
        new_roles = request.POST.getlist('roles')
        valid_roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        new_roles = [r for r in new_roles if r in valid_roles]
        profile.roles = new_roles
        profile.save()
        messages.success(request, f"Updated {profile.user.username}'s roles to: {profile.get_roles_display() or 'None'}.")
    except UserProfile.DoesNotExist:
        messages.error(request, 'User not found.')

    return redirect('manage_users')
