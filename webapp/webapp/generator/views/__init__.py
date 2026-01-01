"""
Views package for the Pillars Character Generator.

This package splits the monolithic views.py into logical modules:
- forms.py: Form classes
- helpers.py: Utility functions
- session.py: Session management (CharacterSessionManager)

For backward compatibility, this module re-exports everything from
the original views module until migration is complete.
"""

# Re-export everything from the original views.py for backward compatibility
# This allows gradual migration without breaking existing imports
from ..views_legacy import *  # noqa: F401, F403

# New modular exports
from .forms import RegistrationForm, AdminUserCreationForm
from .session import (
    CharacterSessionManager,
    clear_pending_session,
    clear_interactive_session,
    SESSION_CURRENT_CHARACTER,
    SESSION_PENDING_CHARACTER,
    SESSION_PENDING_TRACK,
    SESSION_PENDING_YEARS,
    SESSION_INTERACTIVE_YEARS,
    SESSION_INTERACTIVE_SKILLS,
    SESSION_INTERACTIVE_YEARLY_RESULTS,
    SESSION_INTERACTIVE_AGING,
    SESSION_INTERACTIVE_DIED,
    SESSION_INTERACTIVE_TRACK_NAME,
)
from .helpers import (
    MIN_EXPERIENCE_YEARS,
    MAX_EXPERIENCE_YEARS,
    TRACK_DISPLAY_ORDER,
    build_track_info,
    validate_experience_years,
    normalize_skill_name,
    consolidate_skills,
    get_modifier_for_value,
    format_attribute_display,
    get_attribute_modifier,
    get_attribute_base_value,
)
