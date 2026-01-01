"""
Django admin configuration for the Pillars Character Generator.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, SavedCharacter, UserNotes


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""

    list_display = ("user", "get_roles_display", "preferred_contact", "discord_handle")
    list_filter = ("preferred_contact",)
    search_fields = ("user__username", "user__email", "discord_handle", "phone")
    readonly_fields = ("user",)
    ordering = ("user__username",)

    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Roles", {"fields": ("roles",)}),
        (
            "Contact Information",
            {"fields": ("phone", "discord_handle", "preferred_contact")},
        ),
    )

    def get_roles_display(self, obj):
        """Display roles as a comma-separated list."""
        return obj.get_roles_display()

    get_roles_display.short_description = "Roles"


@admin.register(SavedCharacter)
class SavedCharacterAdmin(admin.ModelAdmin):
    """Admin interface for SavedCharacter model."""

    list_display = ("name", "user", "race", "age", "created_at", "updated_at")
    list_filter = ("race", "created_at", "updated_at")
    search_fields = ("name", "user__username", "description")
    readonly_fields = ("created_at", "updated_at", "formatted_character_data")
    ordering = ("-updated_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("user", "name")}),
        ("Character Info", {"fields": ("race", "age", "description")}),
        (
            "Character Data",
            {
                "fields": ("formatted_character_data",),
                "classes": ("collapse",),
                "description": "Raw character data stored as JSON",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def formatted_character_data(self, obj):
        """Display character data as formatted JSON."""
        import json

        try:
            formatted = json.dumps(obj.character_data, indent=2)
            return format_html("<pre>{}</pre>", formatted)
        except (TypeError, ValueError):
            return str(obj.character_data)

    formatted_character_data.short_description = "Character Data (JSON)"


@admin.register(UserNotes)
class UserNotesAdmin(admin.ModelAdmin):
    """Admin interface for UserNotes model."""

    list_display = ("user", "content_preview", "updated_at")
    search_fields = ("user__username", "content")
    readonly_fields = ("user", "updated_at")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"

    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Notes", {"fields": ("content",)}),
        ("Timestamps", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    def content_preview(self, obj):
        """Display a preview of the notes content."""
        max_length = 100
        content = obj.content or ""
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content or "(empty)"

    content_preview.short_description = "Content Preview"
