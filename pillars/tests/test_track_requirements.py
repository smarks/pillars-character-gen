"""
Tests for skill track requirements and auto-selection logic.

Uses mock character data to verify that track requirements are properly enforced.
Track data is loaded from references/skills.csv.
"""

import unittest
from dataclasses import dataclass
from typing import Dict

from pillars.attributes import (
    TrackType,
    get_track_availability,
    create_skill_track_for_choice,
    select_optimal_track,
    check_magic_acceptance,
    check_civil_service_acceptance,
    get_eligible_tracks,
)


@dataclass
class MockCharacter:
    """Mock character data for testing track requirements."""

    str_mod: int = 0
    dex_mod: int = 0
    int_mod: int = 0
    wis_mod: int = 0
    chr_mod: int = 0
    social_class: str = "Commoner"
    sub_class: str = "Laborer"
    wealth_level: str = "Moderate"
    is_promoted: bool = False

    def get_track_availability(self) -> Dict[TrackType, Dict]:
        """Get track availability for this mock character."""
        return get_track_availability(
            self.str_mod,
            self.dex_mod,
            self.int_mod,
            self.wis_mod,
            self.chr_mod,
            self.social_class,
            self.wealth_level,
            self.is_promoted,
        )

    def get_eligible_tracks(self):
        """Get list of eligible tracks for this character."""
        return get_eligible_tracks(
            self.str_mod,
            self.dex_mod,
            self.int_mod,
            self.wis_mod,
            self.chr_mod,
            self.social_class,
            self.wealth_level,
            self.is_promoted,
        )

    def select_optimal_track(self):
        """Select optimal track for this character."""
        return select_optimal_track(
            self.str_mod,
            self.dex_mod,
            self.int_mod,
            self.wis_mod,
            self.chr_mod,
            self.social_class,
            self.wealth_level,
            self.sub_class,
            self.is_promoted,
        )

    def create_track(self, track: TrackType):
        """Create a skill track for this character."""
        return create_skill_track_for_choice(
            chosen_track=track,
            str_mod=self.str_mod,
            dex_mod=self.dex_mod,
            int_mod=self.int_mod,
            wis_mod=self.wis_mod,
            chr_mod=self.chr_mod,
            social_class=self.social_class,
            sub_class=self.sub_class,
            wealth_level=self.wealth_level,
            is_promoted=self.is_promoted,
        )


# =============================================================================
# MOCK CHARACTER FIXTURES
# =============================================================================

# Character with no attribute bonuses - baseline peasant
BASELINE_CHARACTER = MockCharacter(
    str_mod=0,
    dex_mod=0,
    int_mod=0,
    wis_mod=0,
    chr_mod=0,
    social_class="Commoner",
    sub_class="Laborer",
    wealth_level="Moderate",
)

# Smart character - mental focus (can do Magic)
SMART_CHARACTER = MockCharacter(
    str_mod=0,
    dex_mod=0,
    int_mod=2,
    wis_mod=1,
    chr_mod=0,
    social_class="Commoner",
    sub_class="Laborer",
    wealth_level="Moderate",
)

# Charismatic character - can do Civil Service
CHARISMATIC_CHARACTER = MockCharacter(
    str_mod=0,
    dex_mod=0,
    int_mod=0,
    wis_mod=0,
    chr_mod=2,
    social_class="Commoner",
    sub_class="Laborer",
    wealth_level="Moderate",
)

# Wise character - can do Magic and Civil Service
WISE_CHARACTER = MockCharacter(
    str_mod=0,
    dex_mod=0,
    int_mod=0,
    wis_mod=2,
    chr_mod=0,
    social_class="Commoner",
    sub_class="Laborer",
    wealth_level="Moderate",
)

# Exceptional character - all positive modifiers
EXCEPTIONAL_CHARACTER = MockCharacter(
    str_mod=2,
    dex_mod=2,
    int_mod=2,
    wis_mod=1,
    chr_mod=1,
    social_class="Gentry",
    sub_class="Professional",
    wealth_level="Rich",
)


# =============================================================================
# TEST CLASSES
# =============================================================================


class TestTrackAvailability(unittest.TestCase):
    """Test get_track_availability correctly identifies track eligibility."""

    def test_always_available_tracks(self):
        """Most tracks have no requirements and are always available."""
        no_req_tracks = [
            TrackType.MERCHANT,
            TrackType.CAMPAIGNER,
            TrackType.LABORER,
            TrackType.UNDERWORLD,
            TrackType.CRAFT,
            TrackType.HUNTER_GATHERER,
            TrackType.RANDOM,
        ]

        for char in [BASELINE_CHARACTER, SMART_CHARACTER]:
            availability = char.get_track_availability()

            for track in no_req_tracks:
                with self.subTest(char=char, track=track):
                    self.assertTrue(availability[track]["available"])
                    self.assertTrue(availability[track]["auto_accept"])
                    self.assertFalse(availability[track]["impossible"])
                    self.assertFalse(availability[track]["requires_roll"])

    def test_magic_requires_int_or_wis_bonus(self):
        """Magic track requires INT or WIS bonus."""
        # Baseline has no bonus - impossible
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]["impossible"])
        self.assertFalse(avail[TrackType.MAGIC]["available"])

        # Smart (has INT bonus) - available
        avail = SMART_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]["available"])
        self.assertTrue(avail[TrackType.MAGIC]["auto_accept"])

        # Wise (has WIS bonus) - available
        avail = WISE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]["available"])

        # Charismatic (no INT/WIS) - impossible
        avail = CHARISMATIC_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.MAGIC]["impossible"])

    def test_civil_service_requires_int_chr_or_wis_bonus(self):
        """Civil Service requires INT, CHR, or WIS bonus."""
        # Baseline has no bonus - impossible
        avail = BASELINE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.CIVIL_SERVICE]["impossible"])

        # Smart (has INT bonus) - available
        avail = SMART_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.CIVIL_SERVICE]["available"])

        # Charismatic (has CHR bonus) - available
        avail = CHARISMATIC_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.CIVIL_SERVICE]["available"])

        # Wise (has WIS bonus) - available
        avail = WISE_CHARACTER.get_track_availability()
        self.assertTrue(avail[TrackType.CIVIL_SERVICE]["available"])


class TestAcceptanceChecks(unittest.TestCase):
    """Test individual acceptance check functions."""

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

    def test_civil_service_acceptance(self):
        """Civil Service needs INT, CHR, or WIS bonus."""
        result = check_civil_service_acceptance(0, 0, 0)
        self.assertFalse(result.accepted)

        result = check_civil_service_acceptance(1, 0, 0)
        self.assertTrue(result.accepted)

        result = check_civil_service_acceptance(0, 1, 0)
        self.assertTrue(result.accepted)

        result = check_civil_service_acceptance(0, 0, 1)
        self.assertTrue(result.accepted)


class TestAutoSelectTrack(unittest.TestCase):
    """Test that auto-selection respects requirements."""

    def test_baseline_cannot_get_restricted_tracks(self):
        """Baseline character should not get Magic or Civil Service."""
        eligible = BASELINE_CHARACTER.get_eligible_tracks()
        eligible_types = {t for t, _ in eligible}

        # Should not have restricted tracks
        self.assertNotIn(TrackType.MAGIC, eligible_types)
        self.assertNotIn(TrackType.CIVIL_SERVICE, eligible_types)

        # Should have always-available tracks
        self.assertIn(TrackType.MERCHANT, eligible_types)
        self.assertIn(TrackType.CAMPAIGNER, eligible_types)
        self.assertIn(TrackType.LABORER, eligible_types)
        self.assertIn(TrackType.RANDOM, eligible_types)

    def test_smart_character_can_get_magic(self):
        """Smart character with INT bonus should be eligible for Magic."""
        eligible = SMART_CHARACTER.get_eligible_tracks()
        eligible_types = {t for t, _ in eligible}

        self.assertIn(TrackType.MAGIC, eligible_types)
        self.assertIn(TrackType.CIVIL_SERVICE, eligible_types)

    def test_optimal_track_prefers_magic_when_available(self):
        """Magic should be preferred when available."""
        track, _ = SMART_CHARACTER.select_optimal_track()
        self.assertEqual(track, TrackType.MAGIC)

    def test_optimal_track_prefers_civil_service_for_charismatic(self):
        """Civil Service should be preferred for charismatic non-magic characters."""
        track, _ = CHARISMATIC_CHARACTER.select_optimal_track()
        self.assertEqual(track, TrackType.CIVIL_SERVICE)


class TestCreateTrackEnforcesRequirements(unittest.TestCase):
    """Test that create_skill_track_for_choice enforces requirements."""

    def test_baseline_cannot_create_magic(self):
        """Baseline character cannot create Magic track."""
        track = BASELINE_CHARACTER.create_track(TrackType.MAGIC)
        self.assertFalse(track.acceptance_check.accepted)

    def test_baseline_cannot_create_civil_service(self):
        """Baseline character cannot create Civil Service track."""
        track = BASELINE_CHARACTER.create_track(TrackType.CIVIL_SERVICE)
        self.assertFalse(track.acceptance_check.accepted)

    def test_smart_can_create_magic(self):
        """Smart character can create Magic track."""
        track = SMART_CHARACTER.create_track(TrackType.MAGIC)
        self.assertTrue(track.acceptance_check.accepted)
        self.assertEqual(track.track, TrackType.MAGIC)

    def test_charismatic_can_create_civil_service(self):
        """Charismatic character can create Civil Service track."""
        track = CHARISMATIC_CHARACTER.create_track(TrackType.CIVIL_SERVICE)
        self.assertTrue(track.acceptance_check.accepted)
        self.assertEqual(track.track, TrackType.CIVIL_SERVICE)

    def test_anyone_can_create_laborer(self):
        """Any character can create Laborer track."""
        for char in [BASELINE_CHARACTER, SMART_CHARACTER, CHARISMATIC_CHARACTER]:
            with self.subTest(char=char):
                track = char.create_track(TrackType.LABORER)
                self.assertTrue(track.acceptance_check.accepted)
                self.assertEqual(track.track, TrackType.LABORER)

    def test_anyone_can_create_craft(self):
        """Any character can create Craft track."""
        for char in [BASELINE_CHARACTER, SMART_CHARACTER, CHARISMATIC_CHARACTER]:
            with self.subTest(char=char):
                track = char.create_track(TrackType.CRAFT)
                self.assertTrue(track.acceptance_check.accepted)
                self.assertEqual(track.track, TrackType.CRAFT)


if __name__ == "__main__":
    unittest.main()
