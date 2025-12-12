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
import re
import functools
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
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST
from .models import SavedCharacter
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
    roll_skill_track,
    create_skill_track_for_choice,
    roll_prior_experience,
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
)


# =============================================================================
# Helper Functions
# =============================================================================

# Constants for experience years validation
MIN_EXPERIENCE_YEARS = 1
MAX_EXPERIENCE_YEARS = 50

# Track order for display
TRACK_DISPLAY_ORDER = [
    TrackType.OFFICER, TrackType.RANGER, TrackType.MAGIC, TrackType.NAVY, TrackType.ARMY,
    TrackType.MERCHANT, TrackType.CRAFTS, TrackType.WORKER, TrackType.RANDOM
]


def build_track_info(track_availability):
    """Build track information list for display in templates.

    Args:
        track_availability: Dict from get_track_availability() mapping TrackType to availability info

    Returns:
        List of dicts with track display information, sorted by availability
        (impossible first, requires_roll second, available last)
    """
    track_info = []
    for track in TRACK_DISPLAY_ORDER:
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
    # Sort tracks: impossible (red) first, requires_roll (yellow) second, available (green) last
    track_info.sort(key=lambda t: (0 if t['impossible'] else (1 if t['requires_roll'] else 2)))
    return track_info


def validate_experience_years(years_str, default=5):
    """Validate and return experience years within allowed bounds.

    Args:
        years_str: String value from form input
        default: Default value if parsing fails

    Returns:
        Integer years clamped to MIN_EXPERIENCE_YEARS..MAX_EXPERIENCE_YEARS
    """
    try:
        years = int(years_str) if years_str else default
    except (ValueError, TypeError):
        years = default
    return max(MIN_EXPERIENCE_YEARS, min(years, MAX_EXPERIENCE_YEARS))


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


def dice_roller(request):
    """Standalone dice roller page designed to be opened in a popup window."""
    return render(request, 'generator/dice_roller.html')


def start_over(request):
    """Clear all session data and redirect to welcome page."""
    clear_interactive_session(request)
    clear_pending_session(request)
    # Also clear the current character
    if 'current_character' in request.session:
        del request.session['current_character']
    request.session.modified = True
    return redirect('welcome')


# =============================================================================
# Index View Helper Functions
# =============================================================================

# Constants for movement and encumbrance calculations
MIN_BASE_MOVEMENT = 4
LIGHT_ENCUMBRANCE_MULTIPLIER = 1.5
MEDIUM_ENCUMBRANCE_MULTIPLIER = 2
HEAVY_ENCUMBRANCE_MULTIPLIER = 2.5


def _handle_reroll(request, attribute_focus=None):
    """Handle character reroll with optional attribute focus."""
    character = generate_character(years=0, attribute_focus=attribute_focus, skip_track=True)
    store_current_character(request, character)
    return character


def _handle_start_fresh(request):
    """Clear all session data and generate a fresh character."""
    clear_pending_session(request)
    for key in ['interactive_years', 'interactive_skills', 'interactive_yearly_results',
                'interactive_aging', 'interactive_died', 'interactive_track_name',
                'current_character']:
        request.session.pop(key, None)
    request.session.modified = True
    character = generate_character(years=0, skip_track=True)
    store_current_character(request, character)
    return redirect('generator')


def _get_or_create_skill_track(char_data, character, track_mode, chosen_track_name):
    """Get existing skill track or create a new one based on user selection.

    Returns:
        tuple: (skill_track, char_data, error_message)
        If error_message is not None, track creation failed.
    """
    str_mod = character.attributes.get_modifier('STR')
    dex_mod = character.attributes.get_modifier('DEX')
    int_mod = character.attributes.get_modifier('INT')
    wis_mod = character.attributes.get_modifier('WIS')
    social_class = char_data.get('provenance_social_class', 'Commoner')
    sub_class = char_data.get('provenance_sub_class', 'Laborer')
    wealth_level = char_data.get('wealth_level', 'Moderate')

    if char_data.get('skill_track'):
        # Use existing track
        track_data = char_data['skill_track']
        skill_track = SkillTrack(
            track=TrackType(track_data['track']),
            acceptance_check=None,
            survivability=track_data['survivability'],
            survivability_roll=None,
            initial_skills=track_data['initial_skills'],
            craft_type=CraftType(track_data['craft_type']) if track_data.get('craft_type') else None,
            craft_rolls=None,
            magic_school=MagicSchool(track_data['magic_school']) if track_data.get('magic_school') else None,
            magic_school_rolls=track_data.get('magic_school_rolls'),
        )
        return skill_track, char_data, None

    # Create new track
    if track_mode == 'manual' and chosen_track_name:
        try:
            chosen_track = TrackType[chosen_track_name]
        except KeyError:
            chosen_track = TrackType.RANDOM
        skill_track = create_skill_track_for_choice(
            chosen_track=chosen_track,
            str_mod=str_mod, dex_mod=dex_mod, int_mod=int_mod, wis_mod=wis_mod,
            social_class=social_class, sub_class=sub_class, wealth_level=wealth_level,
        )
    else:
        skill_track = roll_skill_track(
            str_mod=str_mod, dex_mod=dex_mod, int_mod=int_mod, wis_mod=wis_mod,
            social_class=social_class, sub_class=sub_class, wealth_level=wealth_level,
        )

    if skill_track is None or skill_track.track is None:
        return None, char_data, 'Could not create skill track. Try selecting a different track.'

    # Save track to character data
    char_data['skill_track'] = {
        'track': skill_track.track.value,
        'survivability': skill_track.survivability,
        'initial_skills': list(skill_track.initial_skills),
        'craft_type': skill_track.craft_type.value if skill_track.craft_type else None,
        'magic_school': skill_track.magic_school.value if skill_track.magic_school else None,
        'magic_school_rolls': skill_track.magic_school_rolls,
    }
    return skill_track, char_data, None


def _roll_experience_years(skill_track, years, existing_years, existing_skills, total_modifier, aging_effects):
    """Roll experience for the specified number of years.

    Returns:
        tuple: (new_skills, new_yearly_results, died, updated_aging_effects)
    """
    new_skills = []
    new_yearly_results = []
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
            'aging': year_result.aging_penalties,
        })

        if not year_result.survived:
            died = True
            break

    return new_skills, new_yearly_results, died, aging_effects


def _update_experience_session(request, char_data, skill_track, existing_years, existing_skills,
                               new_skills, existing_yearly_results, new_yearly_results,
                               died, aging_effects):
    """Update session with new experience data."""
    request.session['interactive_years'] = existing_years + len(new_yearly_results)
    request.session['interactive_skills'] = existing_skills + new_skills
    request.session['interactive_yearly_results'] = existing_yearly_results + new_yearly_results
    request.session['interactive_died'] = died
    request.session['interactive_aging'] = {
        'str': aging_effects.str_penalty,
        'dex': aging_effects.dex_penalty,
        'int': aging_effects.int_penalty,
        'wis': aging_effects.wis_penalty,
        'con': aging_effects.con_penalty,
    }
    request.session['interactive_track_name'] = skill_track.track.value
    request.session['current_character'] = char_data
    request.session.modified = True


def _sync_experience_to_database(request, char_data, existing_years, existing_skills,
                                  new_skills, existing_yearly_results, new_yearly_results,
                                  died, aging_effects):
    """Sync experience data to database for logged-in users."""
    saved_id = request.session.get('current_saved_character_id')
    if not saved_id or not request.user.is_authenticated:
        return

    try:
        saved_char = SavedCharacter.objects.get(id=saved_id, user=request.user)
        saved_char.character_data['skill_track'] = char_data.get('skill_track')
        saved_char.character_data['interactive_years'] = existing_years + len(new_yearly_results)
        saved_char.character_data['interactive_skills'] = existing_skills + new_skills
        saved_char.character_data['interactive_yearly_results'] = existing_yearly_results + new_yearly_results
        saved_char.character_data['interactive_died'] = died
        saved_char.character_data['interactive_aging'] = {
            'str': aging_effects.str_penalty,
            'dex': aging_effects.dex_penalty,
            'int': aging_effects.int_penalty,
            'wis': aging_effects.wis_penalty,
            'con': aging_effects.con_penalty,
        }
        saved_char.save()
    except SavedCharacter.DoesNotExist:
        pass


def _handle_add_experience(request):
    """Handle adding experience years to a character."""
    char_data = request.session.get('current_character')
    if not char_data:
        character = generate_character(years=0, skip_track=True)
        store_current_character(request, character)
        char_data = request.session.get('current_character')

    character = deserialize_character(char_data)

    # Get form parameters
    years = validate_experience_years(request.POST.get('years'), default=5)
    track_mode = request.POST.get('track_mode', 'auto')
    chosen_track_name = request.POST.get('chosen_track', '')

    # Get or create skill track
    skill_track, char_data, error = _get_or_create_skill_track(
        char_data, character, track_mode, chosen_track_name
    )
    if error:
        messages.error(request, error)
        return redirect('generator')

    # Get existing experience data
    existing_years = request.session.get('interactive_years', 0)
    existing_skills = request.session.get('interactive_skills', [])
    existing_yearly_results = request.session.get('interactive_yearly_results', [])
    existing_aging = request.session.get('interactive_aging', {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0})
    died = request.session.get('interactive_died', False)

    if died:
        return redirect('generator')

    # Reconstruct aging effects
    aging_effects = AgingEffects(
        str_penalty=existing_aging.get('str', 0),
        dex_penalty=existing_aging.get('dex', 0),
        int_penalty=existing_aging.get('int', 0),
        wis_penalty=existing_aging.get('wis', 0),
        con_penalty=existing_aging.get('con', 0),
    )

    # Add initial skills if this is the first experience
    if existing_years == 0:
        existing_skills = list(skill_track.initial_skills)

    # Roll experience years
    total_modifier = sum(character.attributes.get_all_modifiers().values())
    new_skills, new_yearly_results, died, aging_effects = _roll_experience_years(
        skill_track, years, existing_years, existing_skills, total_modifier, aging_effects
    )

    # Update session
    _update_experience_session(
        request, char_data, skill_track, existing_years, existing_skills,
        new_skills, existing_yearly_results, new_yearly_results, died, aging_effects
    )

    # Sync to database for logged-in users
    _sync_experience_to_database(
        request, char_data, existing_years, existing_skills,
        new_skills, existing_yearly_results, new_yearly_results, died, aging_effects
    )

    return redirect('generator')


def _get_character_modifiers(char_data):
    """Extract attribute modifiers from character data."""
    if not char_data:
        return {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0, 'chr': 0}

    attrs = char_data.get('attributes', {})
    return {
        'str': get_modifier_for_value(attrs.get('STR', 10)),
        'dex': get_modifier_for_value(attrs.get('DEX', 10)),
        'int': get_modifier_for_value(attrs.get('INT', 10)),
        'wis': get_modifier_for_value(attrs.get('WIS', 10)),
        'con': get_modifier_for_value(attrs.get('CON', 10)),
        'chr': get_modifier_for_value(attrs.get('CHR', 10)),
    }


def _calculate_movement_encumbrance(char_data):
    """Calculate movement allowance and encumbrance thresholds."""
    if char_data:
        attrs = char_data.get('attributes', {})
        str_val = get_attribute_base_value(attrs.get('STR', 10))
        dex_val = get_attribute_base_value(attrs.get('DEX', 10))
    else:
        str_val = 10
        dex_val = 10

    base_ma = max(MIN_BASE_MOVEMENT, dex_val - 2)
    return {
        'base_ma': base_ma,
        'jog_hexes': base_ma // 2,
        'enc_unenc_max': str_val,
        'enc_light_min': str_val + 1,
        'enc_light_max': int(str_val * LIGHT_ENCUMBRANCE_MULTIPLIER),
        'enc_med_min': int(str_val * LIGHT_ENCUMBRANCE_MULTIPLIER) + 1,
        'enc_med_max': str_val * int(MEDIUM_ENCUMBRANCE_MULTIPLIER),
        'enc_heavy_min': str_val * int(MEDIUM_ENCUMBRANCE_MULTIPLIER) + 1,
        'enc_heavy_max': int(str_val * HEAVY_ENCUMBRANCE_MULTIPLIER),
    }


def _get_selected_track_key(char_data):
    """Get the track key for highlighting in UI."""
    if not char_data or not char_data.get('skill_track'):
        return None

    track_value = char_data['skill_track'].get('track')
    for track_type in TrackType:
        if track_type.value == track_value:
            return track_type.name
    return None


def _build_index_context(request, character, char_data):
    """Build the context dictionary for the index template."""
    years_completed = request.session.get('interactive_years', 0)
    skills = request.session.get('interactive_skills', [])
    yearly_results = request.session.get('interactive_yearly_results', [])
    aging_data = request.session.get('interactive_aging', {})
    died = request.session.get('interactive_died', False)
    track_name = request.session.get('interactive_track_name', '')

    # Build complete str_repr if there's prior experience
    if years_completed > 0 and char_data:
        final_str_repr = build_final_str_repr(char_data, years_completed, skills, yearly_results, aging_data, died)
        character._str_repr = final_str_repr

    # Build track info
    mods = _get_character_modifiers(char_data)
    if char_data:
        social_class = char_data.get('provenance_social_class', 'Commoner')
        wealth_level = char_data.get('wealth_level', 'Moderate')
        track_availability = get_track_availability(
            mods['str'], mods['dex'], mods['int'], mods['wis'],
            social_class, wealth_level
        )
        track_info = build_track_info(track_availability)
    else:
        track_info = []

    # Calculate movement and encumbrance
    movement = _calculate_movement_encumbrance(char_data)

    return {
        'character': character,
        'char_data': char_data or {},
        'years_completed': years_completed,
        'years_served': years_completed,
        'current_age': 16 + years_completed,
        'skills': consolidate_skills(skills) if skills else [],
        'yearly_results': yearly_results,
        'has_experience': years_completed > 0,
        'died': died,
        'track_name': track_name,
        'track_info': track_info,
        'selected_track': _get_selected_track_key(char_data),
        'str_mod': mods['str'],
        'dex_mod': mods['dex'],
        'int_mod': mods['int'],
        'wis_mod': mods['wis'],
        'con_mod': mods['con'],
        'chr_mod': mods['chr'],
        **movement,
    }


# =============================================================================
# Main Index View
# =============================================================================

def index(request):
    """Main character generator page.

    Handles character generation, rerolling, and experience addition.
    See helper functions above for implementation details.
    """
    action = request.POST.get('action', '') if request.method == 'POST' else ''

    # Handle POST actions
    if action == 'reroll_none':
        character = _handle_reroll(request, attribute_focus=None)
    elif action == 'reroll_physical':
        character = _handle_reroll(request, attribute_focus='physical')
    elif action == 'reroll_mental':
        character = _handle_reroll(request, attribute_focus='mental')
    elif action == 'start_fresh':
        return _handle_start_fresh(request)
    elif action == 'add_experience':
        return _handle_add_experience(request)
    else:
        # GET request or unknown action
        char_data = request.session.get('current_character')
        if char_data and not action:
            character = deserialize_character(char_data)
        else:
            character = generate_character(years=0, skip_track=True)
            store_current_character(request, character)

    char_data = request.session.get('current_character')
    context = _build_index_context(request, character, char_data)
    return render(request, 'generator/index.html', context)


def store_current_character(request, character):
    """Store character in session for the generator flow.

    If user is logged in, also save to database and return the saved character ID.
    """
    char_data = serialize_character(character)
    request.session['current_character'] = char_data
    # Clear any prior experience data when re-rolling
    request.session['interactive_years'] = 0
    request.session['interactive_skills'] = []
    request.session['interactive_yearly_results'] = []
    request.session['interactive_aging'] = {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0}
    request.session['interactive_died'] = False
    request.session.modified = True

    # Auto-save to database if user is logged in
    saved_char_id = None
    if request.user.is_authenticated:
        # Create a new saved character
        char_count = SavedCharacter.objects.filter(user=request.user).count() + 1
        saved_char = SavedCharacter.objects.create(
            user=request.user,
            name=f"Character {char_count}",
            character_data=char_data
        )
        saved_char_id = saved_char.id
        request.session['current_saved_character_id'] = saved_char_id

    return saved_char_id


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
    track_info = build_track_info(track_availability)

    # Reconstruct character for display
    character = deserialize_character(pending_char)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'start_over':
            clear_pending_session(request)
            return redirect('start_over')

        elif action == 'add_experience':
            # Get form data
            interactive_mode = request.POST.get('interactive_mode') == 'on'
            track_mode = request.POST.get('track_mode', 'auto')
            years = validate_experience_years(request.POST.get('years'), default=5) if not interactive_mode else 0
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
        return redirect('generator')

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

        elif action == 'new':
            # Clear session and start over
            clear_interactive_session(request)
            return redirect('generator')

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
    # Map section names to file paths and display titles
    # Most content is now in the consolidated handbook in docs/
    SECTION_CONFIG = {
        'about': {
            'path': os.path.join(settings.BASE_DIR, '..', 'references', 'about.md'),
            'title': 'About',
        },
        'lore': {
            'path': os.path.join(settings.BASE_DIR, '..', 'references', 'lore.md'),
            'title': 'Background',
        },
        'players_handbook': {
            'path': os.path.join(settings.BASE_DIR, '..', 'docs', 'A Pillars Handbook.md'),
            'title': "Player's Handbook",
        },
        'combat': {
            'path': os.path.join(settings.BASE_DIR, '..', 'references', 'Combat_and_Movement.md'),
            'title': 'Combat & Movement',
        },
        'DM_handbook': {
            'path': os.path.join(settings.BASE_DIR, '..', 'references', 'DM_handbook.md'),
            'title': 'DM Handbook',
        },
    }

    config = SECTION_CONFIG.get(section)
    if config:
        section_path = config['path']
        title = config['title']
    else:
        # Fallback for unknown sections - look in references
        section_path = os.path.join(settings.BASE_DIR, '..', 'references', f'{section}.md')
        title = section.replace('_', ' ').title()

    try:
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        html_content = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'toc']
        )

        # Rewrite relative image paths to absolute paths for the web app
        # This allows markdown files to work both standalone and in the browser
        # e.g., src="images/foo.png" becomes src="/images/foo.png"
        html_content = re.sub(
            r'src="images/',
            'src="/images/',
            html_content
        )
    except FileNotFoundError:
        html_content = f"<p>Section '{section}' not found.</p>"

    return render(request, 'generator/handbook_section.html', {
        'content': html_content,
        'title': title,
    })


def serve_reference_image(request, filename):
    """Serve images from the references/images directory."""
    import mimetypes
    image_path = os.path.join(settings.REFERENCES_IMAGES_DIR, filename)

    # Security: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        raise Http404("Invalid filename")

    if not os.path.exists(image_path):
        raise Http404("Image not found")

    content_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(open(image_path, 'rb'), content_type=content_type)


# =============================================================================
# Authentication Views
# =============================================================================

def save_session_character_for_user(request, user):
    """Save the current session character to the database for a user.

    Called after login/registration to preserve any character the user
    was working on before authenticating.
    """
    char_data = request.session.get('current_character')
    if not char_data:
        return None

    # Check if we already have a saved character ID (shouldn't happen, but be safe)
    if request.session.get('current_saved_character_id'):
        return request.session.get('current_saved_character_id')

    # Include any experience data from the session
    if request.session.get('interactive_years', 0) > 0:
        char_data['interactive_years'] = request.session.get('interactive_years', 0)
        char_data['interactive_skills'] = request.session.get('interactive_skills', [])
        char_data['interactive_yearly_results'] = request.session.get('interactive_yearly_results', [])
        char_data['interactive_died'] = request.session.get('interactive_died', False)
        char_data['interactive_aging'] = request.session.get('interactive_aging', {})

    # Create the saved character
    char_count = SavedCharacter.objects.filter(user=user).count() + 1
    saved_char = SavedCharacter.objects.create(
        user=user,
        name=char_data.get('name') or f"Character {char_count}",
        character_data=char_data
    )
    request.session['current_saved_character_id'] = saved_char.id
    request.session['current_character'] = char_data  # Update with experience data
    request.session.modified = True

    return saved_char.id


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Save any character the user was working on
            saved_id = save_session_character_for_user(request, user)
            messages.success(request, 'Account created successfully!')
            # Redirect to generator if they had a character, otherwise welcome
            if saved_id:
                return redirect('generator')
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
            # Save any character the user was working on
            saved_id = save_session_character_for_user(request, user)
            # Redirect to generator if they had a character, otherwise to next_url
            if saved_id:
                return redirect('generator')
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
        return JsonResponse({'success': False, 'error': 'No character to save'}, status=400)

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
    """List saved characters for the logged-in user only."""
    characters = SavedCharacter.objects.filter(user=request.user).order_by('-updated_at')

    return render(request, 'generator/my_characters.html', {
        'characters': characters,
    })


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
    @functools.wraps(view_func)
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
    @functools.wraps(view_func)
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
    """Admin view to manage user roles, create users, and view all characters."""
    users = UserProfile.objects.select_related('user').all()
    role_choices = UserProfile.ROLE_CHOICES

    # Get all characters grouped by user
    all_characters = SavedCharacter.objects.all().select_related('user').order_by('user__username', '-updated_at')
    characters_by_user = {}
    for char in all_characters:
        username = char.user.username
        if username not in characters_by_user:
            characters_by_user[username] = []
        characters_by_user[username].append(char)

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
        'characters_by_user': characters_by_user,
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


@admin_required
def edit_user(request, user_id):
    """Edit a user's details (Admin only)."""
    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, 'User not found.')
        return redirect('manage_users')

    if request.method == 'POST':
        # Update user fields
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        roles = request.POST.getlist('roles')
        phone = request.POST.get('phone', '').strip()
        discord_handle = request.POST.get('discord_handle', '').strip()
        preferred_contact = request.POST.get('preferred_contact', '').strip()

        # Validate username
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                messages.error(request, f'Username "{username}" is already taken.')
                return redirect('edit_user', user_id=user_id)
            user.username = username

        # Update email
        if email:
            user.email = email

        # Update password if provided
        if new_password:
            user.set_password(new_password)

        user.save()

        # Update profile
        valid_roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        profile.roles = [r for r in roles if r in valid_roles]
        profile.phone = phone
        profile.discord_handle = discord_handle
        if preferred_contact in ['email', 'phone', 'discord']:
            profile.preferred_contact = preferred_contact
        profile.save()

        messages.success(request, f'User "{user.username}" updated successfully.')
        return redirect('manage_users')

    # GET request - show edit form
    role_choices = UserProfile.ROLE_CHOICES
    return render(request, 'generator/edit_user.html', {
        'edit_user': user,
        'profile': profile,
        'role_choices': role_choices,
    })


@admin_required
@require_POST
def delete_user(request, user_id):
    """Delete a user and all their characters (Admin only)."""
    try:
        user = User.objects.get(id=user_id)

        # Don't allow deleting yourself
        if user.id == request.user.id:
            messages.error(request, "You cannot delete your own account.")
            return redirect('manage_users')

        username = user.username
        # Delete user (this will cascade to profile and characters due to foreign keys)
        user.delete()
        messages.success(request, f'User "{username}" and all their characters have been deleted.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')

    return redirect('manage_users')


@admin_required
@require_POST
def admin_delete_character(request, char_id):
    """Delete any character (Admin only)."""
    try:
        character = SavedCharacter.objects.get(id=char_id)
        char_name = character.name
        owner = character.user.username
        character.delete()
        messages.success(request, f'Character "{char_name}" (owned by {owner}) has been deleted.')
    except SavedCharacter.DoesNotExist:
        messages.error(request, 'Character not found.')

    return redirect('manage_users')


# =============================================================================
# Editable Character Sheet Views
# =============================================================================

def normalize_skill_name(skill):
    """Normalize a skill name for consistent matching.

    - Title case for consistent display
    - Strip whitespace
    - Handle common variations
    """
    if not skill:
        return skill

    skill = skill.strip()

    # Handle skills with modifiers like "Sword +1 to hit"
    # Keep the modifier part as-is but title case the skill name
    import re
    match = re.match(r'^([A-Za-z\s]+?)(\s*[+-].*)?$', skill)
    if match:
        name_part = match.group(1).strip().title()
        modifier_part = match.group(2) or ''
        return name_part + modifier_part

    return skill.title()


def consolidate_skills(skills):
    """Consolidate duplicate skills into single entries with counts.

    Case-insensitive matching: 'Weather Sense' and 'Weather sense' are the same.

    Examples:
        ['Tracking', 'Tracking', 'Tracking'] -> ['Tracking 3']
        ['Sword +1', 'Sword +1'] -> ['Sword +1 (x2)']
        ['Tracking', 'Survival', 'Tracking'] -> ['Tracking 2', 'Survival']
        ['Weather Sense', 'Weather sense'] -> ['Weather Sense 2']
    """
    import re
    from collections import Counter, defaultdict

    # Normalize skills and count occurrences (case-insensitive)
    # Track the first seen version for display
    skill_display = {}  # lowercase -> display version
    skill_counts = defaultdict(int)

    for skill in skills:
        if not skill:
            continue
        normalized = normalize_skill_name(skill)
        key = normalized.lower()
        if key not in skill_display:
            skill_display[key] = normalized
        skill_counts[key] += 1

    # Build consolidated list
    consolidated = []
    for key, count in skill_counts.items():
        display_name = skill_display[key]
        if count > 1:
            # Check if skill already has a number suffix (like "Sword +1")
            # If so, use (xN) format to avoid confusion
            if re.search(r'\d+\s*$', display_name) or '+' in display_name:
                consolidated.append(f"{display_name} (x{count})")
            else:
                consolidated.append(f"{display_name} {count}")
        else:
            consolidated.append(display_name)

    # Sort alphabetically for consistent display
    consolidated.sort(key=lambda s: s.lower())
    return consolidated


def format_attribute_display(value):
    """Format attribute value for display.

    Stored as: int (1-18) or string like "18.20", "19.50", etc.
    Display: same format, just ensure it's a string.
    """
    if isinstance(value, str):
        return value
    return str(value)


def get_attribute_modifier(value):
    """Get modifier for an attribute value.

    For values 1-18: use standard ATTRIBUTE_MODIFIERS table.
    For values > 18 (including decimal notation): calculate based on effective value.
    18.10-18.100 counts as 18, 19.10-19.100 counts as 19, etc.
    """
    from pillars.attributes import ATTRIBUTE_MODIFIERS

    if isinstance(value, int):
        return ATTRIBUTE_MODIFIERS.get(value, 0)

    if isinstance(value, str) and '.' in value:
        # Parse decimal notation: "18.20" -> base 18
        try:
            base = int(value.split('.')[0])
            # For values > 18, each whole number adds +1 to the modifier
            # Base modifier at 18 is +5, so 19 is +6, 20 is +7, etc.
            if base >= 18:
                return 5 + (base - 18)
        except ValueError:
            pass

    # Try parsing as int
    try:
        return ATTRIBUTE_MODIFIERS.get(int(value), 0)
    except (ValueError, TypeError):
        return 0


@login_required
def character_sheet(request, char_id):
    """Display editable character sheet."""
    profile = getattr(request.user, 'profile', None)
    is_dm_or_admin = profile and (profile.is_dm or profile.is_admin) if profile else False

    try:
        if is_dm_or_admin:
            # DM/admin can view any character
            character = SavedCharacter.objects.select_related('user').get(id=char_id)
        else:
            character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, 'Character not found.')
        return redirect('my_characters')

    # Check if this is the owner or a DM viewing someone else's character
    is_owner = character.user == request.user

    char_data = character.character_data
    attrs = char_data.get('attributes', {})

    # Build combined skills list
    raw_skills = []
    # Location skills
    raw_skills.extend(char_data.get('location_skills', []))
    # Track initial skills
    if char_data.get('skill_track'):
        raw_skills.extend(char_data['skill_track'].get('initial_skills', []))
    # Prior experience skills
    raw_skills.extend(char_data.get('interactive_skills', []))
    # Manually added skills
    raw_skills.extend(char_data.get('manual_skills', []))

    # Consolidate duplicate skills
    skills = consolidate_skills(raw_skills)

    # Prior experience data
    yearly_results = char_data.get('interactive_yearly_results', [])
    years_served = char_data.get('interactive_years', 0)
    died = char_data.get('interactive_died', False)

    # Build track info for characters that don't have a track yet
    track_info = None
    if not char_data.get('skill_track'):
        str_mod = get_attribute_modifier(attrs.get('STR', 10))
        dex_mod = get_attribute_modifier(attrs.get('DEX', 10))
        int_mod = get_attribute_modifier(attrs.get('INT', 10))
        wis_mod = get_attribute_modifier(attrs.get('WIS', 10))

        social_class = char_data.get('provenance_social_class', 'Commoner')
        wealth_level = char_data.get('wealth_level', 'Moderate')

        track_availability = get_track_availability(
            str_mod, dex_mod, int_mod, wis_mod,
            social_class, wealth_level
        )
        track_info = build_track_info(track_availability)

    return render(request, 'generator/character_sheet.html', {
        'character': character,
        'char_data': char_data,
        'skills': skills,
        # Attribute display values
        'str_display': format_attribute_display(attrs.get('STR', 10)),
        'dex_display': format_attribute_display(attrs.get('DEX', 10)),
        'int_display': format_attribute_display(attrs.get('INT', 10)),
        'wis_display': format_attribute_display(attrs.get('WIS', 10)),
        'con_display': format_attribute_display(attrs.get('CON', 10)),
        'chr_display': format_attribute_display(attrs.get('CHR', 10)),
        # Attribute modifiers
        'str_mod': get_attribute_modifier(attrs.get('STR', 10)),
        'dex_mod': get_attribute_modifier(attrs.get('DEX', 10)),
        'int_mod': get_attribute_modifier(attrs.get('INT', 10)),
        'wis_mod': get_attribute_modifier(attrs.get('WIS', 10)),
        'con_mod': get_attribute_modifier(attrs.get('CON', 10)),
        'chr_mod': get_attribute_modifier(attrs.get('CHR', 10)),
        'yearly_results': yearly_results,
        'years_served': years_served,
        'current_age': 16 + years_served,
        'died': died,
        'track_info': track_info,
        'is_owner': is_owner,
        'character_owner': character.user,
    })


@login_required
@require_POST
def update_character(request, char_id):
    """API endpoint to update a single field on a character."""
    try:
        character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Character not found'}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    field = data.get('field')
    value = data.get('value')
    action = data.get('action')  # For skills: 'add', 'remove', 'edit'
    index = data.get('index')

    if not field:
        return JsonResponse({'success': False, 'error': 'No field specified'}, status=400)

    char_data = character.character_data

    # Handle different field types
    computed = {}

    if field == 'name':
        # Update the model's name field
        character.name = value
    elif field == 'skills':
        # Handle skills list operations
        manual_skills = char_data.get('manual_skills', [])
        if action == 'add':
            # Normalize the skill name before adding
            normalized_skill = normalize_skill_name(value)
            manual_skills.append(normalized_skill)
            char_data['manual_skills'] = manual_skills
            # Return all skills consolidated for display update
            all_skills = []
            all_skills.extend(char_data.get('location_skills', []))
            if char_data.get('skill_track'):
                all_skills.extend(char_data['skill_track'].get('initial_skills', []))
            all_skills.extend(char_data.get('interactive_skills', []))
            all_skills.extend(manual_skills)
            computed['skills'] = consolidate_skills(all_skills)
            computed['index'] = len(manual_skills) - 1
        elif action == 'remove':
            # Need to figure out which list the skill is in
            # For now, just handle manual_skills removal
            if index is not None and 0 <= index < len(manual_skills):
                manual_skills.pop(index)
                char_data['manual_skills'] = manual_skills
        elif action == 'edit':
            # Edit skill at index in manual_skills
            if index is not None and 0 <= index < len(manual_skills):
                manual_skills[index] = value
                char_data['manual_skills'] = manual_skills
    elif field.startswith('attributes.'):
        # Handle nested attribute fields
        attr_name = field.split('.')[1]
        if attr_name in ['STR', 'DEX', 'INT', 'WIS', 'CON', 'CHR']:
            # Store value as-is (int or string like "18.20")
            char_data['attributes'][attr_name] = value
            # Recalculate derived values
            computed.update(recalculate_derived(char_data))
            # Return updated modifier using our enhanced function
            mod = get_attribute_modifier(value)
            computed[f'{attr_name.lower()}_mod'] = mod
    elif field == 'notes':
        char_data['notes'] = value
    elif field in ['appearance', 'height', 'weight', 'provenance', 'location', 'literacy', 'wealth']:
        char_data[field] = value
    else:
        return JsonResponse({'success': False, 'error': f'Unknown field: {field}'}, status=400)

    # Save changes
    character.character_data = char_data
    character.save()

    result = {'success': True}
    if computed:
        result['computed'] = computed
    if action == 'add':
        result['index'] = computed.get('index', 0)

    return JsonResponse(result)


def calculate_track_info(char_data):
    """Calculate track availability info for a character without an assigned track."""
    attrs = char_data.get('attributes', {})
    str_mod = get_attribute_modifier(attrs.get('STR', 10))
    dex_mod = get_attribute_modifier(attrs.get('DEX', 10))
    int_mod = get_attribute_modifier(attrs.get('INT', 10))
    wis_mod = get_attribute_modifier(attrs.get('WIS', 10))
    social_class = char_data.get('provenance_social_class', 'Commoner')
    wealth_level = char_data.get('wealth_level', 'Moderate')

    track_availability = get_track_availability(
        str_mod, dex_mod, int_mod, wis_mod,
        social_class, wealth_level
    )
    return build_track_info(track_availability)


def update_session_character(request):
    """API endpoint to update a single field on the session-based character."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    char_data = request.session.get('current_character')
    if not char_data:
        return JsonResponse({'success': False, 'error': 'No character in session'}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    field = data.get('field')
    value = data.get('value')
    action = data.get('action')  # For skills: 'add', 'remove', 'edit'

    if not field:
        return JsonResponse({'success': False, 'error': 'No field specified'}, status=400)

    computed = {}
    # Track whether we need to recalculate track availability
    recalc_tracks = False

    if field == 'name':
        char_data['name'] = value
    elif field == 'skills':
        # Handle skills list operations
        manual_skills = char_data.get('manual_skills', [])
        if action == 'add':
            normalized_skill = normalize_skill_name(value)
            manual_skills.append(normalized_skill)
            char_data['manual_skills'] = manual_skills
            # Return all skills consolidated for display update
            all_skills = []
            all_skills.extend(char_data.get('location_skills', []))
            if char_data.get('skill_track'):
                all_skills.extend(char_data['skill_track'].get('initial_skills', []))
            all_skills.extend(request.session.get('interactive_skills', []))
            all_skills.extend(manual_skills)
            computed['skills'] = consolidate_skills(all_skills)
    elif field.startswith('attributes.'):
        attr_name = field.split('.')[1]
        if attr_name in ['STR', 'DEX', 'INT', 'WIS', 'CON', 'CHR']:
            char_data['attributes'][attr_name] = value
            computed.update(recalculate_derived(char_data))
            mod = get_attribute_modifier(value)
            computed[f'{attr_name.lower()}_mod'] = mod
            recalc_tracks = True  # Attributes affect track availability
    elif field == 'notes':
        char_data['notes'] = value
    elif field in ['appearance', 'height', 'weight', 'provenance', 'location', 'literacy']:
        char_data[field] = value
    elif field == 'wealth_level':
        char_data['wealth_level'] = value
        # Update display wealth too
        wealth_map = {
            'Destitute': 'Destitute',
            'Poor': 'Poor',
            'Moderate': 'Moderate',
            'Comfortable': 'Comfortable',
            'Rich': 'Rich',
        }
        char_data['wealth'] = wealth_map.get(value, value)
        recalc_tracks = True  # Wealth affects track availability (Officer requires Rich)
    else:
        return JsonResponse({'success': False, 'error': f'Unknown field: {field}'}, status=400)

    # Recalculate track availability if needed and character doesn't have a track yet
    if recalc_tracks and not char_data.get('skill_track'):
        computed['track_info'] = calculate_track_info(char_data)

    # Save to session
    request.session['current_character'] = char_data
    request.session.modified = True

    result = {'success': True}
    if computed:
        result['computed'] = computed

    return JsonResponse(result)


def get_attribute_base_value(value):
    """Get the base integer value from an attribute.

    For int values: return as-is.
    For string like "18.20": return the base (18).
    For string like "19.50": return the base (19).
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if '.' in value:
            try:
                return int(value.split('.')[0])
            except ValueError:
                pass
        try:
            return int(value)
        except ValueError:
            pass
    return 10  # Default


@login_required
@require_POST
def add_experience_to_character(request, char_id):
    """Add prior experience years to a saved character."""
    try:
        character = SavedCharacter.objects.get(id=char_id, user=request.user)
    except SavedCharacter.DoesNotExist:
        messages.error(request, 'Character not found.')
        return redirect('my_characters')

    years = validate_experience_years(request.POST.get('years'), default=5)
    track_choice = request.POST.get('track', 'auto')

    char_data = character.character_data
    attrs = char_data.get('attributes', {})

    # Get attribute modifiers
    str_mod = get_attribute_modifier(attrs.get('STR', 10))
    dex_mod = get_attribute_modifier(attrs.get('DEX', 10))
    int_mod = get_attribute_modifier(attrs.get('INT', 10))
    wis_mod = get_attribute_modifier(attrs.get('WIS', 10))
    con_mod = get_attribute_modifier(attrs.get('CON', 10))
    total_modifier = str_mod + dex_mod + int_mod + wis_mod + con_mod

    # Get or create skill track
    if char_data.get('skill_track'):
        # Use existing skill track
        track_data = char_data['skill_track']
        skill_track = SkillTrack(
            track=TrackType(track_data['track']),
            acceptance_check=None,
            survivability=track_data['survivability'],
            survivability_roll=None,
            initial_skills=track_data['initial_skills'],
            craft_type=CraftType(track_data['craft_type']) if track_data.get('craft_type') else None,
            craft_rolls=None,
            magic_school=MagicSchool(track_data['magic_school']) if track_data.get('magic_school') else None,
            magic_school_rolls=track_data.get('magic_school_rolls'),
        )
    else:
        # Create new skill track
        social_class = char_data.get('provenance_social_class', 'Commoner')
        sub_class = char_data.get('provenance_sub_class', 'Laborer')
        wealth_level = char_data.get('wealth_level', 'Moderate')

        chosen_track = None
        if track_choice != 'auto':
            try:
                chosen_track = TrackType[track_choice]
            except KeyError:
                pass

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

        if skill_track is None or skill_track.track is None:
            messages.error(request, 'Could not create skill track. Try selecting a different track.')
            return redirect('character_sheet', char_id=char_id)

        # Save track to character data
        char_data['skill_track'] = {
            'track': skill_track.track.value,
            'survivability': skill_track.survivability,
            'initial_skills': list(skill_track.initial_skills),
            'craft_type': skill_track.craft_type.value if skill_track.craft_type else None,
            'magic_school': skill_track.magic_school.value if skill_track.magic_school else None,
            'magic_school_rolls': skill_track.magic_school_rolls,
        }

    # Get existing experience data
    existing_years = char_data.get('interactive_years', 0)
    existing_skills = char_data.get('interactive_skills', [])
    existing_yearly_results = char_data.get('interactive_yearly_results', [])
    existing_aging = char_data.get('interactive_aging', {'str': 0, 'dex': 0, 'int': 0, 'wis': 0, 'con': 0})

    # Reconstruct aging effects
    aging_effects = AgingEffects(
        str_penalty=existing_aging.get('str', 0),
        dex_penalty=existing_aging.get('dex', 0),
        int_penalty=existing_aging.get('int', 0),
        wis_penalty=existing_aging.get('wis', 0),
        con_penalty=existing_aging.get('con', 0),
    )

    # Roll new years
    new_skills = []
    new_yearly_results = []
    died = char_data.get('interactive_died', False)

    # Add initial skills if this is the first experience
    if existing_years == 0:
        existing_skills = list(skill_track.initial_skills)

    for i in range(years):
        if died:
            break

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
            'aging': year_result.aging_penalties,
        })

        if not year_result.survived:
            died = True

    # Update character data
    char_data['interactive_years'] = existing_years + len(new_yearly_results)
    char_data['interactive_skills'] = existing_skills + new_skills
    char_data['interactive_yearly_results'] = existing_yearly_results + new_yearly_results
    char_data['interactive_died'] = died
    char_data['interactive_aging'] = {
        'str': aging_effects.str_penalty,
        'dex': aging_effects.dex_penalty,
        'int': aging_effects.int_penalty,
        'wis': aging_effects.wis_penalty,
        'con': aging_effects.con_penalty,
    }

    # Save character
    character.character_data = char_data
    character.save()

    if died and new_yearly_results:
        messages.warning(request, f'Character died during year {new_yearly_results[-1]["year"]}!')
    elif died:
        messages.warning(request, 'Character is already dead. No experience can be added.')
    elif new_yearly_results:
        messages.success(request, f'Added {len(new_yearly_results)} years of experience.')
    else:
        messages.info(request, 'No experience years were added.')

    return redirect('character_sheet', char_id=char_id)


def recalculate_derived(char_data):
    """Recalculate fatigue_points and body_points based on attributes."""
    attrs = char_data.get('attributes', {})

    # Get base values for calculations (the integer part)
    str_val = get_attribute_base_value(attrs.get('STR', 10))
    dex_val = get_attribute_base_value(attrs.get('DEX', 10))
    con_val = get_attribute_base_value(attrs.get('CON', 10))
    wis_val = get_attribute_base_value(attrs.get('WIS', 10))
    int_val = get_attribute_base_value(attrs.get('INT', 10))

    # Get modifiers using our enhanced function
    str_mod = get_attribute_modifier(attrs.get('STR', 10))
    dex_mod = get_attribute_modifier(attrs.get('DEX', 10))
    con_mod = get_attribute_modifier(attrs.get('CON', 10))
    wis_mod = get_attribute_modifier(attrs.get('WIS', 10))
    int_mod = get_attribute_modifier(attrs.get('INT', 10))

    # Use existing rolls if available, otherwise default to 3
    fatigue_roll = attrs.get('fatigue_roll', 3)
    body_roll = attrs.get('body_roll', 3)

    # Fatigue = CON + WIS + max(DEX, STR) + 1d6 + int_mod + wis_mod
    fatigue_points = con_val + wis_val + max(dex_val, str_val) + fatigue_roll + int_mod + wis_mod

    # Body = CON + max(DEX, STR) + 1d6 + int_mod + wis_mod
    body_points = con_val + max(dex_val, str_val) + body_roll + int_mod + wis_mod

    # Update in char_data
    char_data['attributes']['fatigue_points'] = fatigue_points
    char_data['attributes']['body_points'] = body_points

    # STR is used for fatigue pool (maximum fatigue capacity) and encumbrance thresholds
    str_display = attrs.get('STR', 10)

    return {
        'fatigue_points': fatigue_points,
        'body_points': body_points,
        'fatigue_pool': str_val,  # Fatigue Pool = base STR value
    }
