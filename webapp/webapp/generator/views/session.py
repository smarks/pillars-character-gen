"""
Session management for character generation.

This module provides centralized session state management for the character
generator, replacing scattered session key access throughout the codebase.
"""

# Session key constants
SESSION_CURRENT_CHARACTER = "current_character"
SESSION_PENDING_CHARACTER = "pending_character"
SESSION_PENDING_TRACK = "pending_track"
SESSION_PENDING_YEARS = "pending_years"

# Interactive mode session keys
SESSION_INTERACTIVE_YEARS = "interactive_years"
SESSION_INTERACTIVE_SKILLS = "interactive_skills"
SESSION_INTERACTIVE_YEARLY_RESULTS = "interactive_yearly_results"
SESSION_INTERACTIVE_AGING = "interactive_aging"
SESSION_INTERACTIVE_DIED = "interactive_died"
SESSION_INTERACTIVE_TRACK_NAME = "interactive_track_name"

# All pending session keys
PENDING_SESSION_KEYS = [
    SESSION_PENDING_CHARACTER,
    SESSION_PENDING_TRACK,
    SESSION_PENDING_YEARS,
]

# All interactive session keys
INTERACTIVE_SESSION_KEYS = [
    SESSION_INTERACTIVE_YEARS,
    SESSION_INTERACTIVE_SKILLS,
    SESSION_INTERACTIVE_YEARLY_RESULTS,
    SESSION_INTERACTIVE_AGING,
    SESSION_INTERACTIVE_DIED,
    SESSION_INTERACTIVE_TRACK_NAME,
]


class CharacterSessionManager:
    """Centralized manager for character session state.

    This class provides a clean interface for storing and retrieving
    character data from the Django session, replacing scattered
    session key access throughout the views.

    Usage:
        manager = CharacterSessionManager(request)
        manager.store_character(character_data)
        char_data = manager.get_current_character()
        manager.clear_all()
    """

    def __init__(self, request):
        """Initialize with a Django request object."""
        self.request = request
        self.session = request.session

    # =========================================================================
    # Current Character Methods
    # =========================================================================

    def get_current_character(self):
        """Get the current character data from session.

        Returns:
            dict or None: The serialized character data, or None if not set.
        """
        return self.session.get(SESSION_CURRENT_CHARACTER)

    def store_character(self, char_data, preserve_data=None):
        """Store character data in the session.

        Args:
            char_data: The serialized character data dict.
            preserve_data: Optional dict of data to preserve/merge.
        """
        if preserve_data:
            char_data = {**char_data, **preserve_data}
        self.session[SESSION_CURRENT_CHARACTER] = char_data
        self.session.modified = True

    def update_character(self, updates):
        """Update specific fields in the current character.

        Args:
            updates: Dict of fields to update.
        """
        char_data = self.get_current_character()
        if char_data:
            char_data.update(updates)
            self.session[SESSION_CURRENT_CHARACTER] = char_data
            self.session.modified = True

    def has_character(self):
        """Check if there's a character in the session."""
        return SESSION_CURRENT_CHARACTER in self.session

    def clear_character(self):
        """Remove the current character from session."""
        self.session.pop(SESSION_CURRENT_CHARACTER, None)
        self.session.modified = True

    # =========================================================================
    # Pending State Methods (for track selection flow)
    # =========================================================================

    def get_pending_character(self):
        """Get pending character data (during track selection)."""
        return self.session.get(SESSION_PENDING_CHARACTER)

    def get_pending_track(self):
        """Get pending track selection."""
        return self.session.get(SESSION_PENDING_TRACK)

    def get_pending_years(self):
        """Get pending experience years."""
        return self.session.get(SESSION_PENDING_YEARS)

    def store_pending(self, character=None, track=None, years=None):
        """Store pending data for track selection flow.

        Args:
            character: Optional character data to store.
            track: Optional track name to store.
            years: Optional years value to store.
        """
        if character is not None:
            self.session[SESSION_PENDING_CHARACTER] = character
        if track is not None:
            self.session[SESSION_PENDING_TRACK] = track
        if years is not None:
            self.session[SESSION_PENDING_YEARS] = years
        self.session.modified = True

    def clear_pending(self):
        """Clear all pending session data."""
        for key in PENDING_SESSION_KEYS:
            self.session.pop(key, None)
        self.session.modified = True

    # =========================================================================
    # Interactive Mode Methods (for year-by-year experience)
    # =========================================================================

    def get_interactive_state(self):
        """Get all interactive mode state as a dict.

        Returns:
            dict with keys: years, skills, yearly_results, aging, died, track_name
        """
        return {
            "years": self.session.get(SESSION_INTERACTIVE_YEARS),
            "skills": self.session.get(SESSION_INTERACTIVE_SKILLS),
            "yearly_results": self.session.get(SESSION_INTERACTIVE_YEARLY_RESULTS),
            "aging": self.session.get(SESSION_INTERACTIVE_AGING),
            "died": self.session.get(SESSION_INTERACTIVE_DIED),
            "track_name": self.session.get(SESSION_INTERACTIVE_TRACK_NAME),
        }

    def store_interactive(
        self,
        years=None,
        skills=None,
        yearly_results=None,
        aging=None,
        died=None,
        track_name=None,
    ):
        """Store interactive mode state.

        Args:
            years: Number of years of experience.
            skills: List of skills gained.
            yearly_results: List of year-by-year results.
            aging: Aging effects data.
            died: Whether character died.
            track_name: Name of the skill track.
        """
        if years is not None:
            self.session[SESSION_INTERACTIVE_YEARS] = years
        if skills is not None:
            self.session[SESSION_INTERACTIVE_SKILLS] = skills
        if yearly_results is not None:
            self.session[SESSION_INTERACTIVE_YEARLY_RESULTS] = yearly_results
        if aging is not None:
            self.session[SESSION_INTERACTIVE_AGING] = aging
        if died is not None:
            self.session[SESSION_INTERACTIVE_DIED] = died
        if track_name is not None:
            self.session[SESSION_INTERACTIVE_TRACK_NAME] = track_name
        self.session.modified = True

    def update_interactive_skills(self, new_skill):
        """Add a skill to the interactive skills list."""
        skills = self.session.get(SESSION_INTERACTIVE_SKILLS, [])
        skills.append(new_skill)
        self.session[SESSION_INTERACTIVE_SKILLS] = skills
        self.session.modified = True

    def update_interactive_yearly_results(self, year_result):
        """Add a year result to the interactive yearly results."""
        results = self.session.get(SESSION_INTERACTIVE_YEARLY_RESULTS, [])
        results.append(year_result)
        self.session[SESSION_INTERACTIVE_YEARLY_RESULTS] = results
        self.session.modified = True

    def clear_interactive(self):
        """Clear all interactive session data."""
        for key in INTERACTIVE_SESSION_KEYS:
            self.session.pop(key, None)
        self.session.modified = True

    def is_in_interactive_mode(self):
        """Check if currently in interactive mode."""
        return SESSION_INTERACTIVE_YEARS in self.session

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def clear_all(self):
        """Clear all character-related session data."""
        self.clear_character()
        self.clear_pending()
        self.clear_interactive()

    def clear_generation_state(self):
        """Clear pending and interactive state, keeping current character."""
        self.clear_pending()
        self.clear_interactive()


# =============================================================================
# Standalone functions for backward compatibility
# =============================================================================


def clear_pending_session(request):
    """Clear pending session data. For backward compatibility."""
    manager = CharacterSessionManager(request)
    manager.clear_pending()


def clear_interactive_session(request):
    """Clear interactive session data. For backward compatibility."""
    manager = CharacterSessionManager(request)
    manager.clear_interactive()
