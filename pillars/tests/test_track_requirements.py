"""
Tests for skill track requirements and auto-selection logic.

Uses mock character data to verify that track requirements are properly enforced.
"""
import unittest
from dataclasses import dataclass
from typing import Optional, Dict, Any

from pillars.attributes import (
    TrackType,
    get_track_availability,
    create_skill_track_for_choice,
    select_optimal_track,
    check_army_acceptance,
    check_navy_acceptance,
    check_ranger_acceptance,
    check_officer_acceptance,
    check_merchant_acceptance,
    check_magic_acceptance,
    get_eligible_tracks,
)


@dataclass
class MockCharacter:
    """Mock character data for testing track requirements."""
    str_mod: int = 0
    dex_mod: int = 0
    int_mod: int = 0
    wis_mod: int = 0
    social_class: str = "Commoner"
    sub_class: str = "Laborer"
    wealth_level: str = "Moderate"
    is_promoted: bool = False

    def get_track_availability(self) -> Dict[TrackType, Dict]:
        """Get track availability for this mock character."""
        return get_track_availability(
            self.str_mod, self.dex_mod, self.int_mod, self.wis_mod,
            self.social_class, self.wealth_level, self.is_promoted
        )

    def get_eligible_tracks(self):
        """Get list of eligible tracks for this character."""
        return get_eligible_tracks(
            self.str_mod, self.dex_mod, self.int_mod, self.wis_mod,
            self.social_class, self.wealth_level, self.is_promoted
        )

    def select_optimal_track(self):
        """Select optimal track for this character."""
        return select_optimal_track(
            self.str_mod, self.dex_mod, self.int_mod, self.wis_mod,
            self.social_class, self.wealth_level, self.sub_class, self.is_promoted
        )

    def create_track(self, track: TrackType):
        """Create a skill track for this character."""
        return create_skill_track_for_choice(
            chosen_track=track,
            str_mod=self.str_mod,
            dex_mod=self.dex_mod,
            int_mod=self.int_mod,
            wis_mod=self.wis_mod,
            social_class=self.social_class,
            sub_class=self.sub_class,
            wealth_level=self.wealth_level,
            is_promoted=self.is_promoted
        )


# =============================================================================
# MOCK CHARACTER FIXTURES
# =============================================================================

# Character with no attribute bonuses - baseline peasant
BASELINE_CHARACTER = MockCharacter(
    str_mod=0, dex_mod=0, int_mod=0, wis_mod=0,
    social_class="Commoner", sub_class="Laborer", wealth_level="Moderate"
)

# Strong character - physical focus
STRONG_CHARACTER = MockCharacter(
    str_mod=2, dex_mod=1, int_mod=0, wis_mod=0,
    social_class="Commoner", sub_class="Laborer", wealth_level="Moderate"
)

# Smart character - mental focus
SMART_CHARACTER = MockCharacter(
    str_mod=0, dex_mod=0, int_mod=2, wis_mod=1,
    social_class="Commoner", sub_class="Laborer", wealth_level="Moderate"
)

# Balanced character - can qualify for Ranger
BALANCED_CHARACTER = MockCharacter(
    str_mod=1, dex_mod=0, int_mod=1, wis_mod=0,
    social_class="Commoner", sub_class="Laborer", wealth_level="Moderate"
)

# Rich character - can be Officer
RICH_CHARACTER = MockCharacter(
    str_mod=0, dex_mod=0, int_mod=0, wis_mod=0,
    social_class="Nobility", sub_class="Minor", wealth_level="Rich"
)

# Poor character - harder merchant acceptance
POOR_CHARACTER = MockCharacter(
    str_mod=0, dex_mod=0, int_mod=0, wis_mod=0,
    social_class="Commoner", sub_class="Laborer", wealth_level="Subsistence"
)

# Character with very negative modifiers
WEAK_CHARACTER = MockCharacter(
    str_mod=-2, dex_mod=-1, int_mod=-1, wis_mod=0,
    social_class="Commoner", sub_class="Laborer", wealth_level="Moderate"
)

# Character with all positive modifiers - exceptional
EXCEPTIONAL_CHARACTER = MockCharacter(
    str_mod=2, dex_mod=2, int_mod=2, wis_mod=1,
    social_class="Gentry", sub_class="Professional", wealth_level="Rich"
)


# =============================================================================
# TEST CLASSES
# =============================================================================

class TestTrackAvailability(unittest.TestCase):
    """Test get_track_availability correctly identifies track eligibility."""

    def test_always_available_tracks(self):
        """Worker, Crafts, and Random are always available."""
        for char in [BASELINE_CHARACTER, WEAK_CHARACTER, POOR_CHARACTER]:
            availability = char.get_track_availability()

            for track in [TrackType.WORKER, TrackType.CRAFTS, TrackType.RANDOM]:
                with self.subTest(char=char, track=track):
                    self.assertTrue(availability[track]['available'])
                    self.assertTrue(availability[track]['auto_accept'])
                    self.assertFalse(availability[track]['impossible'])
                    self.assertFalse(availability[track]['requires_roll'])

    def test_ranger_requires_physical_and_mental_bonus(self):
        """Ranger requires both STR/DEX bonus AND INT/WIS bonus."""
        # Baseline has neither - impossible
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.RANGER]['impossible'])
        self.assertFalse(avail[TrackType.RANGER]['available'])

        # Strong has physical only - still impossible
        avail = STRONG_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.RANGER]['impossible'])

        # Smart has mental only - still impossible
        avail = SMART_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.RANGER]['impossible'])

        # Balanced has both - available
        avail = BALANCED_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.RANGER]['available'])
        self.assertTrue(avail[TrackType.RANGER]['auto_accept'])
        self.assertFalse(avail[TrackType.RANGER]['impossible'])

    def test_officer_requires_rich_or_promotion(self):
        """Officer requires Rich wealth or promotion."""
        # Baseline is not rich - impossible
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.OFFICER]['impossible'])

        # Rich character - available
        avail = RICH_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.OFFICER]['available'])
        self.assertTrue(avail[TrackType.OFFICER]['auto_accept'])

        # Promoted character (not rich) - available
        promoted = MockCharacter(
            str_mod=0, dex_mod=0, int_mod=0, wis_mod=0,
            wealth_level="Moderate", is_promoted=True
        )
        avail = promoted.get_track_availability()
        self.assertTrue(avail[TrackType.OFFICER]['available'])

    def test_magic_requires_int_or_wis_bonus(self):
        """Magic track requires INT or WIS bonus."""
        # Baseline has no bonus - impossible
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]['impossible'])

        # Strong (physical only) - impossible
        avail = STRONG_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]['impossible'])

        # Smart (has INT bonus) - available
        avail = SMART_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]['available'])
        self.assertTrue(avail[TrackType.MAGIC]['auto_accept'])

        # Character with only WIS bonus - also available
        wis_char = MockCharacter(str_mod=0, dex_mod=0, int_mod=0, wis_mod=1)
        avail = wis_char.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]['available'])

    def test_army_requires_acceptance_roll(self):
        """Army always requires acceptance roll (2d6 + STR + DEX >= 8)."""
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.ARMY]['requires_roll'])
        self.assertTrue(avail[TrackType.ARMY]['available'])  # Can attempt

        # Character with very low modifiers may be impossible
        very_weak = MockCharacter(str_mod=-3, dex_mod=-3, int_mod=0, wis_mod=0)
        avail = very_weak.get_track_availability()
        # With -6 total, max roll is 12 + (-6) = 6, need 8+, so impossible
        self.assertTrue(avail[TrackType.ARMY]['impossible'])

        # Strong character - easier acceptance
        avail = STRONG_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.ARMY]['available'])
        # With +3 modifier, min roll is 2 + 3 = 5, max is 15, so can succeed but not guaranteed

    def test_navy_requires_acceptance_roll(self):
        """Navy requires 2d6 + STR + DEX + INT >= 8."""
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.NAVY]['requires_roll'])
        self.assertTrue(avail[TrackType.NAVY]['available'])

    def test_merchant_acceptance_varies_by_social_class(self):
        """Merchant target varies: poor=10, working class=8, above=6."""
        # All characters can attempt merchant (requires roll)
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MERCHANT]['requires_roll'])

        avail = POOR_CHARACTER.get_track_availability()
        self.assertIn("10", avail[TrackType.MERCHANT]['roll_info'])

        avail = RICH_CHARACTER.get_track_availability()
        self.assertIn("6", avail[TrackType.MERCHANT]['roll_info'])


class TestAcceptanceChecks(unittest.TestCase):
    """Test individual acceptance check functions."""

    def test_ranger_acceptance_both_required(self):
        """Ranger needs physical AND mental bonus."""
        # Neither bonus
        result = check_ranger_acceptance(0, 0, 0, 0)
        self.assertFalse(result.accepted)

        # Physical only
        result = check_ranger_acceptance(1, 0, 0, 0)
        self.assertFalse(result.accepted)

        # Mental only
        result = check_ranger_acceptance(0, 0, 1, 0)
        self.assertFalse(result.accepted)

        # Both (STR and INT)
        result = check_ranger_acceptance(1, 0, 1, 0)
        self.assertTrue(result.accepted)

        # Both (DEX and WIS)
        result = check_ranger_acceptance(0, 1, 0, 1)
        self.assertTrue(result.accepted)

    def test_magic_acceptance_mental_required(self):
        """Magic needs INT or WIS bonus."""
        result = check_magic_acceptance(0, 0)
        self.assertFalse(result.accepted)

        result = check_magic_acceptance(1, 0)
        self.assertTrue(result.accepted)

        result = check_magic_acceptance(0, 1)
        self.assertTrue(result.accepted)

        result = check_magic_acceptance(1, 1)
        self.assertTrue(result.accepted)

    def test_officer_acceptance_rich_or_promoted(self):
        """Officer needs Rich or promotion."""
        result = check_officer_acceptance(is_rich=False, is_promoted=False)
        self.assertFalse(result.accepted)

        result = check_officer_acceptance(is_rich=True, is_promoted=False)
        self.assertTrue(result.accepted)

        result = check_officer_acceptance(is_rich=False, is_promoted=True)
        self.assertTrue(result.accepted)


class TestAutoSelectTrack(unittest.TestCase):
    """Test that auto-selection respects requirements."""

    def test_baseline_cannot_get_restricted_tracks(self):
        """Baseline character should not get Ranger, Officer, or Magic."""
        eligible = BASELINE_CHARACTER.get_eligible_tracks()
        eligible_types = {t for t, _ in eligible}

        # Should not have restricted tracks
        self.assertNotIn(TrackType.RANGER, eligible_types)
        self.assertNotIn(TrackType.OFFICER, eligible_types)
        self.assertNotIn(TrackType.MAGIC, eligible_types)

        # Should have always-available tracks
        self.assertIn(TrackType.WORKER, eligible_types)
        self.assertIn(TrackType.CRAFTS, eligible_types)
        self.assertIn(TrackType.RANDOM, eligible_types)

    def test_smart_character_can_get_magic(self):
        """Smart character with INT bonus should be eligible for Magic."""
        eligible = SMART_CHARACTER.get_eligible_tracks()
        eligible_types = {t for t, _ in eligible}

        self.assertIn(TrackType.MAGIC, eligible_types)

    def test_balanced_character_can_get_ranger(self):
        """Balanced character with physical AND mental bonus gets Ranger."""
        eligible = BALANCED_CHARACTER.get_eligible_tracks()
        eligible_types = {t for t, _ in eligible}

        self.assertIn(TrackType.RANGER, eligible_types)

    def test_rich_character_can_get_officer(self):
        """Rich character should be eligible for Officer."""
        eligible = RICH_CHARACTER.get_eligible_tracks()
        eligible_types = {t for t, _ in eligible}

        self.assertIn(TrackType.OFFICER, eligible_types)

    def test_optimal_track_prefers_officer_when_available(self):
        """Officer should be preferred when available (Rich character)."""
        track, _ = EXCEPTIONAL_CHARACTER.select_optimal_track()
        self.assertEqual(track, TrackType.OFFICER)

    def test_optimal_track_prefers_ranger_for_balanced(self):
        """Ranger should be preferred for balanced non-rich characters."""
        track, _ = BALANCED_CHARACTER.select_optimal_track()
        # Ranger is preferred over Army/Navy for balanced characters
        self.assertEqual(track, TrackType.RANGER)


class TestCreateTrackEnforcesRequirements(unittest.TestCase):
    """Test that create_skill_track_for_choice enforces requirements."""

    def test_baseline_cannot_create_ranger(self):
        """Baseline character cannot create Ranger track."""
        track = BASELINE_CHARACTER.create_track(TrackType.RANGER)
        self.assertFalse(track.acceptance_check.accepted)

    def test_baseline_cannot_create_officer(self):
        """Baseline character cannot create Officer track."""
        track = BASELINE_CHARACTER.create_track(TrackType.OFFICER)
        self.assertFalse(track.acceptance_check.accepted)

    def test_baseline_cannot_create_magic(self):
        """Baseline character cannot create Magic track."""
        track = BASELINE_CHARACTER.create_track(TrackType.MAGIC)
        self.assertFalse(track.acceptance_check.accepted)

    def test_balanced_can_create_ranger(self):
        """Balanced character can create Ranger track."""
        track = BALANCED_CHARACTER.create_track(TrackType.RANGER)
        self.assertTrue(track.acceptance_check.accepted)
        self.assertEqual(track.track, TrackType.RANGER)

    def test_smart_can_create_magic(self):
        """Smart character can create Magic track."""
        track = SMART_CHARACTER.create_track(TrackType.MAGIC)
        self.assertTrue(track.acceptance_check.accepted)
        self.assertEqual(track.track, TrackType.MAGIC)

    def test_rich_can_create_officer(self):
        """Rich character can create Officer track."""
        track = RICH_CHARACTER.create_track(TrackType.OFFICER)
        self.assertTrue(track.acceptance_check.accepted)
        self.assertEqual(track.track, TrackType.OFFICER)

    def test_anyone_can_create_worker(self):
        """Any character can create Worker track."""
        for char in [BASELINE_CHARACTER, WEAK_CHARACTER, POOR_CHARACTER]:
            with self.subTest(char=char):
                track = char.create_track(TrackType.WORKER)
                self.assertTrue(track.acceptance_check.accepted)
                self.assertEqual(track.track, TrackType.WORKER)

    def test_anyone_can_create_crafts(self):
        """Any character can create Crafts track."""
        for char in [BASELINE_CHARACTER, WEAK_CHARACTER, POOR_CHARACTER]:
            with self.subTest(char=char):
                track = char.create_track(TrackType.CRAFTS)
                self.assertTrue(track.acceptance_check.accepted)
                self.assertEqual(track.track, TrackType.CRAFTS)


if __name__ == '__main__':
    unittest.main()
