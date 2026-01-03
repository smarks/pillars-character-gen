from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile with optional contact fields."""

    ROLE_CHOICES = [
        ("player", "Player"),
        ("dm", "Dungeon Master"),
        ("admin", "Admin"),
    ]

    CONTACT_METHOD_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("discord", "Discord"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    roles = models.JSONField(
        default=list
    )  # List of role strings: ['player'], ['dm', 'admin'], etc.
    phone = models.CharField(max_length=20, blank=True, default="")
    discord_handle = models.CharField(max_length=100, blank=True, default="")
    preferred_contact = models.CharField(
        max_length=10,
        choices=CONTACT_METHOD_CHOICES,
        blank=True,
        default="",
        help_text="Preferred method for game notifications",
    )

    def __str__(self):
        return f"Profile for {self.user.username}"

    def has_role(self, role):
        """Check if user has a specific role."""
        return role in self.roles

    @property
    def is_admin(self):
        """Check if user is an admin."""
        return "admin" in self.roles

    @property
    def is_dm(self):
        """Check if user is a DM."""
        return "dm" in self.roles

    @property
    def is_player(self):
        """Check if user is a player."""
        return "player" in self.roles

    def get_roles_display(self):
        """Get human-readable list of roles."""
        role_map = dict(self.ROLE_CHOICES)
        return ", ".join(role_map.get(r, r) for r in self.roles) or "None"


class UserNotes(models.Model):
    """Stores notes for a user. One notes document per user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notes")
    content = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Notes"
        verbose_name_plural = "User Notes"

    def __str__(self):
        return f"Notes for {self.user.username}"


class SavedCharacter(models.Model):
    """Stores a saved character for a user."""

    RACE_CHOICES = [
        ("human", "Human"),
        ("elf", "Elf"),
        ("dwarf", "Dwarf"),
        ("giant", "Giant"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_characters"
    )
    name = models.CharField(max_length=200)
    age = models.IntegerField(null=True, blank=True)
    race = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    character_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def auto_description(self):
        """Generate a brief auto-description based on character data.

        Format: "Age X, [Provenance] from [Location], [Track]"
        Example: "Age 23, Noble from the City, Ranger"
        """
        if not self.character_data:
            return "New character"

        parts = []
        char_data = self.character_data

        # Age
        base_age = char_data.get("base_age", 16)
        years = char_data.get("interactive_years", 0)
        age = base_age + years
        parts.append(f"Age {age}")

        # Provenance (social class or sub-class if available)
        provenance = char_data.get("provenance_sub_class") or char_data.get(
            "provenance_social_class"
        )
        if provenance:
            parts.append(provenance)

        # Location
        location = char_data.get("location")
        if location:
            parts.append(f"from {location}")

        # Track (if has prior experience)
        skill_track = char_data.get("skill_track", {})
        if skill_track:
            track_name = skill_track.get("track")
            if track_name:
                parts.append(track_name)

        return ", ".join(parts) if parts else "New character"
