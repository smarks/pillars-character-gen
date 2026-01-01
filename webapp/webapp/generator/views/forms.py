"""
Form classes for the Pillars Character Generator.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from ..models import UserProfile


class RegistrationForm(UserCreationForm):
    """Custom registration form with optional contact fields."""

    email = forms.EmailField(required=False, help_text="Optional")
    # Only show player/dm choices during registration (admin is assigned manually)
    REGISTRATION_ROLE_CHOICES = [
        ("player", "Player"),
        ("dm", "Dungeon Master"),
    ]
    role = forms.ChoiceField(
        choices=REGISTRATION_ROLE_CHOICES,
        initial="player",
        help_text="Select your role",
    )
    phone = forms.CharField(
        max_length=20, required=False, help_text="Optional - for SMS notifications"
    )
    discord_handle = forms.CharField(
        max_length=100, required=False, help_text="Optional - e.g. username#1234"
    )
    preferred_contact = forms.ChoiceField(
        choices=[("", "Not specified")] + UserProfile.CONTACT_METHOD_CHOICES,
        required=False,
        initial="",
        help_text="How would you like to be contacted for game notifications?",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "role",
            "phone",
            "discord_handle",
            "preferred_contact",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            role = self.cleaned_data.get("role", "player")
            UserProfile.objects.create(
                user=user,
                roles=[role],  # Store as list
                phone=self.cleaned_data.get("phone", ""),
                discord_handle=self.cleaned_data.get("discord_handle", ""),
                preferred_contact=self.cleaned_data.get("preferred_contact", ""),
            )
        return user


class AdminUserCreationForm(UserCreationForm):
    """Admin form for creating users with full role access."""

    email = forms.EmailField(required=False, help_text="Optional")
    roles = forms.MultipleChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select one or more roles for this user",
    )
    phone = forms.CharField(
        max_length=20, required=False, help_text="Optional - for SMS notifications"
    )
    discord_handle = forms.CharField(
        max_length=100, required=False, help_text="Optional - e.g. username#1234"
    )
    preferred_contact = forms.ChoiceField(
        choices=[("", "Not specified")] + UserProfile.CONTACT_METHOD_CHOICES,
        required=False,
        initial="",
        help_text="Preferred contact method",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "roles",
            "phone",
            "discord_handle",
            "preferred_contact",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            roles = self.cleaned_data.get("roles", [])
            UserProfile.objects.create(
                user=user,
                roles=list(roles),  # Store as list
                phone=self.cleaned_data.get("phone", ""),
                discord_handle=self.cleaned_data.get("discord_handle", ""),
                preferred_contact=self.cleaned_data.get("preferred_contact", ""),
            )
        return user
