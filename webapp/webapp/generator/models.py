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
        """Generate a brief auto-description based on character strengths and skills.

        Focuses on high/low attributes and primary skills.
        Example: "Strong and wise, skilled in Sword. Weak DEX."
        """
        if not self.character_data:
            return "New character"

        char_data = self.character_data
        attrs = char_data.get("attributes", {})

        # Get base attribute values (handle both int and dict formats)
        def get_val(attr_name):
            val = attrs.get(attr_name, 10)
            if isinstance(val, dict):
                return val.get("value", 10)
            return val if isinstance(val, int) else 10

        attr_values = {
            "STR": get_val("STR"),
            "DEX": get_val("DEX"),
            "INT": get_val("INT"),
            "WIS": get_val("WIS"),
            "CON": get_val("CON"),
            "CHR": get_val("CHR"),
        }

        # Descriptive words for attributes
        attr_words = {
            "STR": "strong",
            "DEX": "agile",
            "INT": "intelligent",
            "WIS": "wise",
            "CON": "hardy",
            "CHR": "charismatic",
        }

        # Find strengths (13+) and weaknesses (8-)
        strengths = [attr_words[a] for a, v in attr_values.items() if v >= 13]
        weaknesses = [a for a, v in attr_values.items() if v <= 8]

        parts = []

        # Strengths
        if strengths:
            if len(strengths) == 1:
                parts.append(strengths[0].capitalize())
            elif len(strengths) == 2:
                parts.append(f"{strengths[0].capitalize()} and {strengths[1]}")
            else:
                parts.append(
                    f"{strengths[0].capitalize()}, {strengths[1]}, {strengths[2]}"
                )

        # Skills - get top skills from skill_points_data or interactive_skills
        top_skills = []
        skill_data = char_data.get("skill_points_data", {})
        if skill_data and skill_data.get("skills"):
            # Sort by total points, get top 2
            skills_list = [
                (name, data.get("automatic", 0) + data.get("allocated", 0))
                for name, data in skill_data.get("skills", {}).items()
            ]
            skills_list.sort(key=lambda x: x[1], reverse=True)
            top_skills = [s[0] for s in skills_list[:2] if s[1] > 0]
        elif char_data.get("interactive_skills"):
            # Fallback to interactive_skills
            from collections import Counter

            skill_counts = Counter(char_data.get("interactive_skills", []))
            top_skills = [s for s, _ in skill_counts.most_common(2)]

        if top_skills:
            skills_str = " & ".join(top_skills)
            parts.append(f"skilled in {skills_str}")

        # Weaknesses
        if weaknesses:
            weak_str = ", ".join(weaknesses)
            parts.append(f"weak {weak_str}")

        # Age and fatigue
        base_age = char_data.get("base_age", 16)
        years = char_data.get("interactive_years", 0)
        age = base_age + years
        fatigue = attrs.get("fatigue_points", "?")

        # Build final description
        desc_parts = [f"Age {age}"]
        if parts:
            desc_parts.append(". ".join(parts))
        desc_parts.append(f"FP {fatigue}")

        return ", ".join(desc_parts)
