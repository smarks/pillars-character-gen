"""
Unit tests for skills module.
"""

import unittest
from pillars.skills import (
    points_for_level,
    level_from_points,
    to_roman,
    normalize_skill_name,
    SkillPoints,
    CharacterSkills,
)


class TestPointsForLevel(unittest.TestCase):
    """Tests for triangular number calculation."""

    def test_level_zero_returns_zero(self):
        """Level 0 requires 0 points."""
        self.assertEqual(points_for_level(0), 0)

    def test_negative_level_returns_zero(self):
        """Negative levels return 0 points."""
        self.assertEqual(points_for_level(-1), 0)
        self.assertEqual(points_for_level(-5), 0)

    def test_level_one(self):
        """Level 1 requires 1 point."""
        self.assertEqual(points_for_level(1), 1)

    def test_level_two(self):
        """Level 2 requires 3 points (1+2)."""
        self.assertEqual(points_for_level(2), 3)

    def test_level_three(self):
        """Level 3 requires 6 points (1+2+3)."""
        self.assertEqual(points_for_level(3), 6)

    def test_level_four(self):
        """Level 4 requires 10 points (1+2+3+4)."""
        self.assertEqual(points_for_level(4), 10)

    def test_level_five(self):
        """Level 5 requires 15 points."""
        self.assertEqual(points_for_level(5), 15)

    def test_higher_levels(self):
        """Test higher levels follow triangular formula."""
        # Level N = N * (N+1) / 2
        self.assertEqual(points_for_level(10), 55)
        self.assertEqual(points_for_level(20), 210)


class TestLevelFromPoints(unittest.TestCase):
    """Tests for reverse calculation from points to level."""

    def test_zero_points(self):
        """Zero points = level 0."""
        level, excess = level_from_points(0)
        self.assertEqual(level, 0)
        self.assertEqual(excess, 0)

    def test_negative_points(self):
        """Negative points return level 0."""
        level, excess = level_from_points(-5)
        self.assertEqual(level, 0)
        self.assertEqual(excess, 0)

    def test_one_point_level_one(self):
        """1 point = Level I with no excess."""
        level, excess = level_from_points(1)
        self.assertEqual(level, 1)
        self.assertEqual(excess, 0)

    def test_two_points_level_one_excess(self):
        """2 points = Level I with 1 excess."""
        level, excess = level_from_points(2)
        self.assertEqual(level, 1)
        self.assertEqual(excess, 1)

    def test_three_points_level_two(self):
        """3 points = Level II with no excess."""
        level, excess = level_from_points(3)
        self.assertEqual(level, 2)
        self.assertEqual(excess, 0)

    def test_five_points_level_two_excess(self):
        """5 points = Level II with 2 excess."""
        level, excess = level_from_points(5)
        self.assertEqual(level, 2)
        self.assertEqual(excess, 2)

    def test_six_points_level_three(self):
        """6 points = Level III with no excess."""
        level, excess = level_from_points(6)
        self.assertEqual(level, 3)
        self.assertEqual(excess, 0)

    def test_round_trip(self):
        """Converting back and forth preserves levels."""
        for level in range(1, 10):
            points = points_for_level(level)
            result_level, excess = level_from_points(points)
            self.assertEqual(result_level, level)
            self.assertEqual(excess, 0)


class TestToRoman(unittest.TestCase):
    """Tests for Roman numeral conversion."""

    def test_zero_returns_empty(self):
        """Zero returns empty string."""
        self.assertEqual(to_roman(0), "")

    def test_negative_returns_empty(self):
        """Negative numbers return empty string."""
        self.assertEqual(to_roman(-1), "")

    def test_basic_numerals(self):
        """Test basic Roman numerals."""
        self.assertEqual(to_roman(1), "I")
        self.assertEqual(to_roman(2), "II")
        self.assertEqual(to_roman(3), "III")
        self.assertEqual(to_roman(4), "IV")
        self.assertEqual(to_roman(5), "V")

    def test_larger_numerals(self):
        """Test larger Roman numerals."""
        self.assertEqual(to_roman(6), "VI")
        self.assertEqual(to_roman(9), "IX")
        self.assertEqual(to_roman(10), "X")
        self.assertEqual(to_roman(50), "L")
        self.assertEqual(to_roman(100), "C")

    def test_complex_numerals(self):
        """Test complex Roman numerals."""
        self.assertEqual(to_roman(14), "XIV")
        self.assertEqual(to_roman(49), "XLIX")
        self.assertEqual(to_roman(99), "XCIX")


class TestNormalizeSkillName(unittest.TestCase):
    """Tests for skill name normalization (case-insensitive, lowercase output)."""

    def test_empty_string(self):
        """Empty string returns empty."""
        self.assertEqual(normalize_skill_name(""), "")

    def test_simple_name_lowercased(self):
        """Simple names are lowercased."""
        self.assertEqual(normalize_skill_name("Sword"), "sword")
        self.assertEqual(normalize_skill_name("Tracking"), "tracking")

    def test_strips_whitespace(self):
        """Whitespace is stripped."""
        self.assertEqual(normalize_skill_name("  Sword  "), "sword")

    def test_to_hit_suffix_preserved(self):
        """'to hit' suffix is kept but number stripped, lowercase."""
        self.assertEqual(normalize_skill_name("Sword +1 to hit"), "sword to hit")
        self.assertEqual(normalize_skill_name("Sword +2 to hit"), "sword to hit")

    def test_parry_suffix_preserved(self):
        """'parry' suffix is kept but number stripped, lowercase."""
        self.assertEqual(normalize_skill_name("Sword +1 parry"), "sword parry")
        self.assertEqual(normalize_skill_name("Sword +2 parry"), "sword parry")

    def test_damage_suffix_preserved(self):
        """'damage' suffix is kept but number stripped, lowercase."""
        self.assertEqual(normalize_skill_name("Bow +1 damage"), "bow damage")

    def test_different_suffixes_kept_separate(self):
        """Different suffixes result in different normalized names."""
        to_hit = normalize_skill_name("Sword +1 to hit")
        parry = normalize_skill_name("Sword +1 parry")
        self.assertNotEqual(to_hit, parry)

    def test_same_suffix_different_levels_same_result(self):
        """Same suffix with different bonuses normalizes to same name."""
        sword1 = normalize_skill_name("Sword +1 to hit")
        sword2 = normalize_skill_name("Sword +2 to hit")
        self.assertEqual(sword1, sword2)

    def test_trailing_number_stripped(self):
        """Trailing '+N' without suffix is stripped."""
        self.assertEqual(normalize_skill_name("Haggle +1"), "haggle")
        self.assertEqual(normalize_skill_name("Stealth +2"), "stealth")

    def test_x_multiplier_stripped(self):
        """'(x2)' patterns are stripped."""
        self.assertEqual(normalize_skill_name("Climbing (x2)"), "climbing")


class TestSkillPoints(unittest.TestCase):
    """Tests for SkillPoints dataclass."""

    def test_default_values(self):
        """New SkillPoints has zero values."""
        sp = SkillPoints()
        self.assertEqual(sp.automatic, 0)
        self.assertEqual(sp.allocated, 0)
        self.assertEqual(sp.total, 0)

    def test_total_property(self):
        """Total is sum of automatic and allocated."""
        sp = SkillPoints(automatic=2, allocated=3)
        self.assertEqual(sp.total, 5)

    def test_level_property(self):
        """Level is calculated from total points."""
        sp = SkillPoints(automatic=3, allocated=0)
        self.assertEqual(sp.level, 2)  # 3 points = Level II

    def test_excess_points_property(self):
        """Excess points shows progress to next level."""
        sp = SkillPoints(automatic=4, allocated=1)  # 5 total
        self.assertEqual(sp.level, 2)  # Level II (needs 3)
        self.assertEqual(sp.excess_points, 2)  # 5 - 3 = 2

    def test_to_dict(self):
        """Can serialize to dict."""
        sp = SkillPoints(automatic=2, allocated=3)
        d = sp.to_dict()
        self.assertEqual(d["automatic"], 2)
        self.assertEqual(d["allocated"], 3)
        self.assertEqual(d["total"], 5)

    def test_from_dict(self):
        """Can deserialize from dict."""
        d = {"automatic": 4, "allocated": 2}
        sp = SkillPoints.from_dict(d)
        self.assertEqual(sp.automatic, 4)
        self.assertEqual(sp.allocated, 2)

    def test_from_dict_missing_keys(self):
        """Missing keys default to zero."""
        d = {}
        sp = SkillPoints.from_dict(d)
        self.assertEqual(sp.automatic, 0)
        self.assertEqual(sp.allocated, 0)


class TestCharacterSkills(unittest.TestCase):
    """Tests for CharacterSkills class."""

    def test_default_values(self):
        """New CharacterSkills is empty."""
        cs = CharacterSkills()
        self.assertEqual(len(cs.skills), 0)
        self.assertEqual(cs.free_points, 0)
        self.assertEqual(cs.total_xp, 0)

    def test_add_automatic_point(self):
        """Adding automatic point creates/updates skill (lowercase key)."""
        cs = CharacterSkills()
        cs.add_automatic_point("Sword")
        self.assertEqual(cs.skills["sword"].automatic, 1)
        self.assertEqual(cs.skills["sword"].display_name, "Sword")

        cs.add_automatic_point("Sword")
        self.assertEqual(cs.skills["sword"].automatic, 2)

    def test_add_automatic_point_normalizes(self):
        """Automatic points normalize skill names."""
        cs = CharacterSkills()
        cs.add_automatic_point("Sword +1 to hit")
        cs.add_automatic_point("Sword +2 to hit")
        self.assertEqual(cs.skills["sword to hit"].automatic, 2)

    def test_add_automatic_point_empty_ignored(self):
        """Empty skill names are ignored."""
        cs = CharacterSkills()
        cs.add_automatic_point("")
        self.assertEqual(len(cs.skills), 0)

    def test_add_free_point(self):
        """Adding free point increments counter."""
        cs = CharacterSkills()
        cs.add_free_point()
        self.assertEqual(cs.free_points, 1)
        cs.add_free_point()
        self.assertEqual(cs.free_points, 2)

    def test_add_xp(self):
        """Adding XP increments total."""
        cs = CharacterSkills()
        cs.add_xp(1000)
        self.assertEqual(cs.total_xp, 1000)
        cs.add_xp(500)
        self.assertEqual(cs.total_xp, 1500)

    def test_allocate_point_success(self):
        """Can allocate free point to skill (lowercase key)."""
        cs = CharacterSkills()
        cs.free_points = 2
        result = cs.allocate_point("Tracking")
        self.assertTrue(result)
        self.assertEqual(cs.free_points, 1)
        self.assertEqual(cs.skills["tracking"].allocated, 1)
        self.assertEqual(cs.skills["tracking"].display_name, "Tracking")

    def test_allocate_point_no_free_points(self):
        """Cannot allocate without free points."""
        cs = CharacterSkills()
        result = cs.allocate_point("Tracking")
        self.assertFalse(result)
        self.assertEqual(cs.free_points, 0)

    def test_allocate_point_empty_name(self):
        """Cannot allocate to empty skill name."""
        cs = CharacterSkills()
        cs.free_points = 1
        result = cs.allocate_point("")
        self.assertFalse(result)
        self.assertEqual(cs.free_points, 1)

    def test_deallocate_point_success(self):
        """Can deallocate point back to free pool."""
        cs = CharacterSkills()
        cs.skills["sword"] = SkillPoints(automatic=0, allocated=2, display_name="Sword")
        cs.free_points = 0

        result = cs.deallocate_point("Sword")  # Can use any case
        self.assertTrue(result)
        self.assertEqual(cs.free_points, 1)
        self.assertEqual(cs.skills["sword"].allocated, 1)

    def test_deallocate_point_no_allocated(self):
        """Cannot deallocate if no allocated points."""
        cs = CharacterSkills()
        cs.skills["sword"] = SkillPoints(automatic=2, allocated=0)

        result = cs.deallocate_point("Sword")
        self.assertFalse(result)

    def test_deallocate_point_unknown_skill(self):
        """Cannot deallocate from unknown skill."""
        cs = CharacterSkills()
        result = cs.deallocate_point("Unknown")
        self.assertFalse(result)

    def test_get_skill_display_level_one(self):
        """Display for level 1 skill uses display_name."""
        cs = CharacterSkills()
        cs.skills["sword"] = SkillPoints(automatic=1, allocated=0, display_name="Sword")
        display = cs.get_skill_display("Sword")
        self.assertEqual(display, "Sword I")

    def test_get_skill_display_level_with_excess(self):
        """Display shows excess points with display_name."""
        cs = CharacterSkills()
        cs.skills["sword"] = SkillPoints(
            automatic=4, allocated=1, display_name="Sword"
        )  # 5 points
        display = cs.get_skill_display("Sword")
        self.assertEqual(display, "Sword II (+2)")

    def test_get_skill_display_unknown_skill(self):
        """Unknown skills return original name."""
        cs = CharacterSkills()
        display = cs.get_skill_display("Unknown")
        self.assertEqual(display, "Unknown")

    def test_get_display_list(self):
        """Display list returns sorted formatted strings."""
        cs = CharacterSkills()
        cs.skills["tracking"] = SkillPoints(
            automatic=1, allocated=0, display_name="Tracking"
        )
        cs.skills["sword"] = SkillPoints(automatic=3, allocated=0, display_name="Sword")

        display_list = cs.get_display_list()
        self.assertEqual(len(display_list), 2)
        self.assertEqual(display_list[0], "Sword II")  # S before T
        self.assertEqual(display_list[1], "Tracking I")

    def test_get_skills_with_details(self):
        """Details includes all skill information."""
        cs = CharacterSkills()
        cs.skills["sword"] = SkillPoints(
            automatic=2, allocated=2, display_name="Sword"
        )  # 4 points

        details = cs.get_skills_with_details()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]["name"], "sword")  # lowercase key
        self.assertEqual(details[0]["display_name"], "Sword")  # preserved casing
        self.assertEqual(details[0]["level"], 2)  # 4 points = Level II
        self.assertEqual(details[0]["level_roman"], "II")
        self.assertEqual(details[0]["total_points"], 4)
        self.assertEqual(details[0]["automatic_points"], 2)
        self.assertEqual(details[0]["allocated_points"], 2)
        self.assertEqual(details[0]["excess_points"], 1)  # 4 - 3 = 1
        self.assertEqual(details[0]["points_to_next_level"], 2)  # 6 - 4 = 2

    def test_to_dict_and_from_dict_round_trip(self):
        """Serialization round trip preserves data."""
        cs = CharacterSkills()
        cs.skills["sword"] = SkillPoints(automatic=2, allocated=1, display_name="Sword")
        cs.skills["bow"] = SkillPoints(automatic=1, allocated=0, display_name="Bow")
        cs.free_points = 5
        cs.total_xp = 3000

        data = cs.to_dict()
        restored = CharacterSkills.from_dict(data)

        self.assertEqual(restored.free_points, 5)
        self.assertEqual(restored.total_xp, 3000)
        self.assertEqual(restored.skills["sword"].automatic, 2)
        self.assertEqual(restored.skills["sword"].allocated, 1)
        self.assertEqual(restored.skills["bow"].automatic, 1)

    def test_from_legacy_skills(self):
        """Legacy migration creates proper skill structure."""
        skill_list = ["Sword +1 to hit", "Sword +2 to hit", "Tracking", "Bow +1 damage"]
        cs = CharacterSkills.from_legacy_skills(skill_list, years=5)

        # Check free points and XP
        self.assertEqual(cs.free_points, 5)
        self.assertEqual(cs.total_xp, 5000)

        # Check normalized skills (lowercase keys)
        self.assertEqual(cs.skills["sword to hit"].automatic, 2)  # Two sword hits
        self.assertEqual(cs.skills["tracking"].automatic, 1)
        self.assertEqual(cs.skills["bow damage"].automatic, 1)

    def test_from_legacy_skills_empty_list(self):
        """Legacy migration handles empty list."""
        cs = CharacterSkills.from_legacy_skills([], years=3)
        self.assertEqual(cs.free_points, 3)
        self.assertEqual(cs.total_xp, 3000)
        self.assertEqual(len(cs.skills), 0)

    def test_from_legacy_skills_filters_empty_strings(self):
        """Legacy migration ignores empty strings."""
        skill_list = ["Sword", "", "Bow", ""]
        cs = CharacterSkills.from_legacy_skills(skill_list, years=2)
        self.assertEqual(len(cs.skills), 2)


if __name__ == "__main__":
    unittest.main()
