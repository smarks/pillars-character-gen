"""
Tests for skill track availability and selection logic.

All tracks have no requirements - any character can choose any track.
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
    """Mock character data for testing track selection."""

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

# Smart character - mental focus
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

# Charismatic character
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


# =============================================================================
# TEST CLASSES
# =============================================================================


class TestTrackAvailability(unittest.TestCase):
    """Test get_track_availability correctly identifies all tracks as available."""

    def test_all_tracks_available(self):
        """All tracks have no requirements and are always available."""
        all_tracks = [
            TrackType.MERCHANT,
            TrackType.CAMPAIGNER,
            TrackType.LABORER,
            TrackType.UNDERWORLD,
            TrackType.CRAFT,
            TrackType.HUNTER_GATHERER,
            TrackType.RANDOM,
            TrackType.MAGIC,
            TrackType.CIVIL_SERVICE,
        ]

        for char in [BASELINE_CHARACTER, SMART_CHARACTER, CHARISMATIC_CHARACTER]:
            availability = char.get_track_availability()

            for track in all_tracks:
                with self.subTest(char=char, track=track):
                    self.assertTrue(availability[track]["available"])
                    self.assertTrue(availability[track]["auto_accept"])
                    self.assertFalse(availability[track]["impossible"])
                    self.assertFalse(availability[track]["requires_roll"])


class TestAcceptanceChecks(unittest.TestCase):
    """Test individual acceptance check functions always accept."""

    def test_magic_acceptance_always_accepts(self):
        """Magic accepts all characters."""
        result = check_magic_acceptance(0, 0)
        self.assertTrue(result.accepted)

        result = check_magic_acceptance(1, 0)
        self.assertTrue(result.accepted)

        result = check_magic_acceptance(0, 1)
        self.assertTrue(result.accepted)

    def test_civil_service_acceptance_always_accepts(self):
        """Civil Service accepts all characters."""
        result = check_civil_service_acceptance(0, 0, 0)
        self.assertTrue(result.accepted)

        result = check_civil_service_acceptance(1, 0, 0)
        self.assertTrue(result.accepted)

        result = check_civil_service_acceptance(0, 1, 0)
        self.assertTrue(result.accepted)


class TestEligibleTracks(unittest.TestCase):
    """Test that all tracks are eligible for all characters."""

    def test_all_characters_eligible_for_all_tracks(self):
        """All characters can access all tracks."""
        all_tracks = {
            TrackType.MERCHANT,
            TrackType.CAMPAIGNER,
            TrackType.LABORER,
            TrackType.UNDERWORLD,
            TrackType.CRAFT,
            TrackType.HUNTER_GATHERER,
            TrackType.RANDOM,
            TrackType.MAGIC,
            TrackType.CIVIL_SERVICE,
        }

        for char in [BASELINE_CHARACTER, SMART_CHARACTER, CHARISMATIC_CHARACTER]:
            eligible = char.get_eligible_tracks()
            eligible_types = {t for t, _ in eligible}

            with self.subTest(char=char):
                self.assertEqual(eligible_types, all_tracks)


class TestCreateTrack(unittest.TestCase):
    """Test that any character can create any track."""

    def test_anyone_can_create_magic(self):
        """Any character can create Magic track."""
        for char in [BASELINE_CHARACTER, SMART_CHARACTER, CHARISMATIC_CHARACTER]:
            with self.subTest(char=char):
                track = char.create_track(TrackType.MAGIC)
                self.assertTrue(track.acceptance_check.accepted)
                self.assertEqual(track.track, TrackType.MAGIC)

    def test_anyone_can_create_civil_service(self):
        """Any character can create Civil Service track."""
        for char in [BASELINE_CHARACTER, SMART_CHARACTER, CHARISMATIC_CHARACTER]:
            with self.subTest(char=char):
                track = char.create_track(TrackType.CIVIL_SERVICE)
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
