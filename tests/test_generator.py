"""Tests for pillars/generator.py module."""

import unittest
from unittest.mock import patch
from io import StringIO

from pillars.generator import Character, generate_character, main
from pillars.attributes import (
    TrackType,
    CharacterAttributes,
    Appearance,
    Height,
    Weight,
    Provenance,
    Location,
    LiteracyCheck,
    Wealth,
    SkillTrack,
    PriorExperience,
)


class TestCharacterClass(unittest.TestCase):
    """Tests for the Character dataclass."""

    def test_character_died_without_prior_experience(self):
        """Test that died returns False when no prior experience."""
        char = generate_character(skip_track=True)
        self.assertFalse(char.died)
        self.assertIsNone(char.prior_experience)

    def test_character_died_with_prior_experience_alive(self):
        """Test that died returns False when character survived."""
        char = generate_character(years=1, chosen_track=TrackType.WORKER)
        if char.prior_experience and not char.prior_experience.died:
            self.assertFalse(char.died)

    def test_character_age_without_prior_experience(self):
        """Test that age returns 16 when no prior experience."""
        char = generate_character(skip_track=True)
        self.assertEqual(char.age, 16)

    def test_character_age_with_prior_experience(self):
        """Test that age reflects years of experience."""
        char = generate_character(years=5, chosen_track=TrackType.WORKER)
        if char.prior_experience and not char.prior_experience.died:
            self.assertEqual(char.age, char.prior_experience.final_age)

    def test_character_str_without_track(self):
        """Test __str__ when no skill track assigned."""
        char = generate_character(skip_track=True)
        result = str(char)
        self.assertIn("Pillars Character", result)
        self.assertIn("STR:", result)
        # Should not have skill track or prior experience sections
        self.assertNotIn("Track)", result)
        self.assertNotIn("Prior Experience", result)

    def test_character_str_with_track_and_experience(self):
        """Test __str__ with skill track and prior experience."""
        char = generate_character(years=2, chosen_track=TrackType.WORKER)
        result = str(char)
        self.assertIn("Pillars Character", result)
        self.assertIn("STR:", result)
        # Should have skill track info
        self.assertIn("Worker", result)

    def test_character_str_with_dead_character(self):
        """Test __str__ shows death message when character died."""
        # Try many times to get a dead character (survivability check failure)
        for _ in range(100):
            char = generate_character(years=18, chosen_track=TrackType.MAGIC)
            if char.died:
                result = str(char)
                self.assertIn("DIED DURING PRIOR EXPERIENCE", result)
                break


class TestGenerateCharacterFunction(unittest.TestCase):
    """Tests for the generate_character function."""

    def test_generate_character_default(self):
        """Test default character generation."""
        char = generate_character()
        self.assertIsNotNone(char.attributes)
        self.assertIsNotNone(char.appearance)
        self.assertIsNotNone(char.height)
        self.assertIsNotNone(char.weight)
        self.assertIsNotNone(char.provenance)
        self.assertIsNotNone(char.location)
        self.assertIsNotNone(char.literacy)
        self.assertIsNotNone(char.wealth)
        # Default has skill track but 0 years
        self.assertIsNotNone(char.skill_track)

    def test_generate_character_skip_track(self):
        """Test character generation with skip_track=True."""
        char = generate_character(skip_track=True)
        self.assertIsNone(char.skill_track)
        self.assertIsNone(char.prior_experience)

    def test_generate_character_with_chosen_track(self):
        """Test character generation with a chosen track."""
        char = generate_character(years=3, chosen_track=TrackType.NAVY)
        self.assertEqual(char.skill_track.track, TrackType.NAVY)
        self.assertIsNotNone(char.prior_experience)
        if not char.died:
            self.assertEqual(char.prior_experience.years_served, 3)

    def test_generate_character_auto_track(self):
        """Test character generation with auto-selected track."""
        char = generate_character(years=2)
        self.assertIsNotNone(char.skill_track)
        self.assertIsNotNone(char.prior_experience)

    def test_generate_character_physical_focus(self):
        """Test character generation with physical attribute focus."""
        for _ in range(10):
            char = generate_character(skip_track=True, attribute_focus="physical")
            str_mod = char.attributes.get_modifier("STR")
            dex_mod = char.attributes.get_modifier("DEX")
            self.assertTrue(
                str_mod >= 1 or dex_mod >= 1,
                f"Physical focus should have STR({str_mod}) or DEX({dex_mod}) >= 1",
            )

    def test_generate_character_mental_focus(self):
        """Test character generation with mental attribute focus."""
        for _ in range(10):
            char = generate_character(skip_track=True, attribute_focus="mental")
            int_mod = char.attributes.get_modifier("INT")
            wis_mod = char.attributes.get_modifier("WIS")
            self.assertTrue(
                int_mod >= 1 or wis_mod >= 1,
                f"Mental focus should have INT({int_mod}) or WIS({wis_mod}) >= 1",
            )

    def test_generate_character_no_focus(self):
        """Test character generation with no attribute focus."""
        char = generate_character(skip_track=True, attribute_focus=None)
        self.assertIsNotNone(char.attributes)

    def test_generate_character_with_years(self):
        """Test character generation with various years."""
        for years in [0, 1, 5, 10]:
            char = generate_character(years=years, chosen_track=TrackType.WORKER)
            if not char.died and char.prior_experience:
                self.assertEqual(char.prior_experience.years_served, years)

    def test_generate_character_all_tracks(self):
        """Test character generation can use all track types."""
        for track in [
            TrackType.WORKER,
            TrackType.ARMY,
            TrackType.NAVY,
            TrackType.RANGER,
            TrackType.CRAFTS,
            TrackType.MERCHANT,
        ]:
            char = generate_character(years=1, chosen_track=track)
            self.assertEqual(char.skill_track.track, track)


class TestMainFunction(unittest.TestCase):
    """Tests for the main() function."""

    def test_main_prints_character(self):
        """Test that main() prints a character."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("Welcome to Pillars Character Generator", output)
            self.assertIn("Pillars Character", output)


class TestCharacterIntegration(unittest.TestCase):
    """Integration tests for character generation."""

    def test_character_has_all_required_attributes(self):
        """Test that generated character has all expected fields."""
        char = generate_character(years=1, chosen_track=TrackType.ARMY)

        # Check all basic attributes exist
        self.assertIsInstance(char.attributes, CharacterAttributes)
        self.assertIsInstance(char.appearance, Appearance)
        self.assertIsInstance(char.height, Height)
        self.assertIsInstance(char.weight, Weight)
        self.assertIsInstance(char.provenance, Provenance)
        self.assertIsInstance(char.location, Location)
        self.assertIsInstance(char.literacy, LiteracyCheck)
        self.assertIsInstance(char.wealth, Wealth)
        self.assertIsInstance(char.skill_track, SkillTrack)

        if not char.died:
            self.assertIsInstance(char.prior_experience, PriorExperience)

    def test_character_attribute_scores_valid(self):
        """Test that attribute scores are in valid range."""
        char = generate_character(skip_track=True)
        for attr in ["STR", "DEX", "INT", "WIS", "CON", "CHR"]:
            score = getattr(char.attributes, attr)
            self.assertGreaterEqual(score, 3)
            self.assertLessEqual(score, 18)

    def test_multiple_characters_are_different(self):
        """Test that multiple characters have different attributes."""
        chars = [generate_character(skip_track=True) for _ in range(5)]
        # At least some should have different STR values
        str_values = [c.attributes.STR for c in chars]
        self.assertGreater(len(set(str_values)), 1)


if __name__ == "__main__":
    unittest.main()
