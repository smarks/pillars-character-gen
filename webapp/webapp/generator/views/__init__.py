"""
Views package for the Pillars Character Generator.

This package organizes views into logical modules:
- forms.py: Form classes (RegistrationForm, AdminUserCreationForm)
- helpers.py: Utility functions (attribute modifiers, skill normalization)
- session.py: Session management (CharacterSessionManager, session keys)
- serialization.py: Character serialization/deserialization
- core.py: Main entry points (welcome, index, dice_roller)
- prior_experience.py: Track selection and experience (select_track, interactive)
- character_sheet.py: Character editing (character_sheet, update_character)
- auth.py: Authentication views (login, logout, register, profile)
- user_characters.py: User's saved characters (my_characters, load, save, delete)
- references.py: Reference pages and handbooks
- admin.py: Admin/DM management views
- notes.py: User notes functionality
- export.py: Character export (markdown, PDF)
"""

# Forms
from .forms import RegistrationForm, AdminUserCreationForm

# Session management
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

# Helpers
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

# Serialization
from .serialization import (
    serialize_character,
    deserialize_character,
    MinimalCharacter,
    build_final_str_repr,
    store_current_character,
)

# Core views
from .core import (
    welcome,
    dice_roller,
    start_over,
    index,
    add_session_experience_ajax,
)

# Prior experience
from .prior_experience import (
    select_track,
    interactive,
)

# Character sheet
from .character_sheet import (
    character_sheet,
    update_character,
    update_session_character,
    add_experience_to_character,
    build_skill_points_from_char_data,
    recalculate_derived,
)

# Authentication
from .auth import (
    register_view,
    login_view,
    logout_view,
    my_profile,
    save_session_character_for_user,
)

# User characters
from .user_characters import (
    save_character,
    my_characters,
    load_character,
    delete_character,
)

# References
from .references import (
    handbook_section,
    reference_html,
    serve_reference_html,
    serve_reference_image,
    serve_reference_file,
    dm_handbook,
    spells_tabbed,
)

# Admin
from .admin import (
    dm_required,
    admin_required,
    dm_required_check,
    manage_users,
    manage_characters,
    bulk_delete_characters,
    change_user_role,
    edit_user,
    delete_user,
    admin_delete_character,
)

# Notes
from .notes import (
    user_notes,
    save_user_notes,
    admin_notes,
    admin_edit_note,
    admin_delete_note,
)

# Export
from .export import (
    export_session_character_markdown,
    export_session_character_pdf,
    export_character_markdown,
    export_character_pdf,
)

# Define __all__ for explicit exports
__all__ = [
    # Forms
    "RegistrationForm",
    "AdminUserCreationForm",
    # Session
    "CharacterSessionManager",
    "clear_pending_session",
    "clear_interactive_session",
    "SESSION_CURRENT_CHARACTER",
    "SESSION_PENDING_CHARACTER",
    "SESSION_PENDING_TRACK",
    "SESSION_PENDING_YEARS",
    "SESSION_INTERACTIVE_YEARS",
    "SESSION_INTERACTIVE_SKILLS",
    "SESSION_INTERACTIVE_YEARLY_RESULTS",
    "SESSION_INTERACTIVE_AGING",
    "SESSION_INTERACTIVE_DIED",
    "SESSION_INTERACTIVE_TRACK_NAME",
    # Helpers
    "MIN_EXPERIENCE_YEARS",
    "MAX_EXPERIENCE_YEARS",
    "TRACK_DISPLAY_ORDER",
    "build_track_info",
    "validate_experience_years",
    "normalize_skill_name",
    "consolidate_skills",
    "get_modifier_for_value",
    "format_attribute_display",
    "get_attribute_modifier",
    "get_attribute_base_value",
    # Serialization
    "serialize_character",
    "deserialize_character",
    "MinimalCharacter",
    "build_final_str_repr",
    "store_current_character",
    # Core views
    "welcome",
    "dice_roller",
    "start_over",
    "index",
    "add_session_experience_ajax",
    # Prior experience
    "select_track",
    "interactive",
    # Character sheet
    "character_sheet",
    "update_character",
    "update_session_character",
    "add_experience_to_character",
    "build_skill_points_from_char_data",
    "recalculate_derived",
    # Authentication
    "register_view",
    "login_view",
    "logout_view",
    "my_profile",
    "save_session_character_for_user",
    # User characters
    "save_character",
    "my_characters",
    "load_character",
    "delete_character",
    # References
    "handbook_section",
    "reference_html",
    "serve_reference_html",
    "serve_reference_image",
    "serve_reference_file",
    "dm_handbook",
    "spells_tabbed",
    # Admin
    "dm_required",
    "admin_required",
    "dm_required_check",
    "manage_users",
    "manage_characters",
    "bulk_delete_characters",
    "change_user_role",
    "edit_user",
    "delete_user",
    "admin_delete_character",
    # Notes
    "user_notes",
    "save_user_notes",
    "admin_notes",
    "admin_edit_note",
    "admin_delete_note",
    # Export
    "export_session_character_markdown",
    "export_session_character_pdf",
    "export_character_markdown",
    "export_character_pdf",
]
