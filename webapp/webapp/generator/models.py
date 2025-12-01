from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile with optional contact fields."""

    ROLE_CHOICES = [
        ('player', 'Player'),
        ('dm', 'Dungeon Master'),
        ('admin', 'Admin'),
    ]

    CONTACT_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('discord', 'Discord'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.JSONField(default=list)  # List of role strings: ['player'], ['dm', 'admin'], etc.
    phone = models.CharField(max_length=20, blank=True, default='')
    discord_handle = models.CharField(max_length=100, blank=True, default='')
    preferred_contact = models.CharField(
        max_length=10,
        choices=CONTACT_METHOD_CHOICES,
        blank=True,
        default='',
        help_text='Preferred method for game notifications'
    )

    def __str__(self):
        return f"Profile for {self.user.username}"

    def has_role(self, role):
        """Check if user has a specific role."""
        return role in self.roles

    @property
    def is_admin(self):
        """Check if user is an admin."""
        return 'admin' in self.roles

    @property
    def is_dm(self):
        """Check if user is a DM."""
        return 'dm' in self.roles

    @property
    def is_player(self):
        """Check if user is a player."""
        return 'player' in self.roles

    def get_roles_display(self):
        """Get human-readable list of roles."""
        role_map = dict(self.ROLE_CHOICES)
        return ', '.join(role_map.get(r, r) for r in self.roles) or 'None'


class SavedCharacter(models.Model):
    """Stores a saved character for a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_characters')
    name = models.CharField(max_length=200)
    character_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"
