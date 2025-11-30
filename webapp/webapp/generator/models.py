from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile with optional contact fields."""

    ROLE_CHOICES = [
        ('player', 'Player'),
        ('dm', 'Dungeon Master'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='player')
    phone = models.CharField(max_length=20, blank=True, default='')
    discord_handle = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"Profile for {self.user.username}"


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
