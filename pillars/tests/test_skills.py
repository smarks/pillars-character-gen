"""Tests for skill points and level calculation system."""

import pytest
from pillars.skills import (
    points_for_level,
    level_from_points,
    to_roman,
    normalize_skill_name,
    SkillPoints,
    CharacterSkills,
)


class TestPointsForLevel:
    """Tests for triangular number calculation."""

    def test_level_zero_requires_zero_points(self):
        assert points_for_level(0) == 0

    def test_level_one_requires_one_point(self):
        assert points_for_level(1) == 1

    def test_level_two_requires_three_points(self):
        assert points_for_level(2) == 3

    def test_level_three_requires_six_points(self):
        assert points_for_level(3) == 6

    def test_level_four_requires_ten_points(self):
        assert points_for_level(4) == 10

    def test_level_five_requires_fifteen_points(self):
        assert points_for_level(5) == 15

    def test_negative_level_returns_zero(self):
        assert points_for_level(-1) == 0


class TestLevelFromPoints:
    """Tests for level calculation from points."""

    def test_zero_points_is_level_zero(self):
        level, excess = level_from_points(0)
        assert level == 0
        assert excess == 0

    def test_one_point_is_level_one(self):
        level, excess = level_from_points(1)
        assert level == 1
        assert excess == 0

    def test_two_points_is_level_one_plus_one(self):
        level, excess = level_from_points(2)
        assert level == 1
        assert excess == 1

    def test_three_points_is_level_two(self):
        level, excess = level_from_points(3)
        assert level == 2
        assert excess == 0

    def test_five_points_is_level_two_plus_two(self):
        level, excess = level_from_points(5)
        assert level == 2
        assert excess == 2

    def test_six_points_is_level_three(self):
        level, excess = level_from_points(6)
        assert level == 3
        assert excess == 0

    def test_ten_points_is_level_four(self):
        level, excess = level_from_points(10)
        assert level == 4
        assert excess == 0

    def test_negative_points_returns_zero(self):
        level, excess = level_from_points(-1)
        assert level == 0
        assert excess == 0


class TestToRoman:
    """Tests for Roman numeral conversion."""

    def test_one_is_i(self):
        assert to_roman(1) == "I"

    def test_two_is_ii(self):
        assert to_roman(2) == "II"

    def test_three_is_iii(self):
        assert to_roman(3) == "III"

    def test_four_is_iv(self):
        assert to_roman(4) == "IV"

    def test_five_is_v(self):
        assert to_roman(5) == "V"

    def test_nine_is_ix(self):
        assert to_roman(9) == "IX"

    def test_ten_is_x(self):
        assert to_roman(10) == "X"

    def test_zero_returns_empty(self):
        assert to_roman(0) == ""

    def test_negative_returns_empty(self):
        assert to_roman(-1) == ""


class TestNormalizeSkillName:
    """Tests for skill name normalization."""

    def test_basic_skill_unchanged(self):
        assert normalize_skill_name("Sword") == "Sword"

    def test_strips_plus_to_hit(self):
        # "to hit" and "parry" are kept as separate skill types
        assert normalize_skill_name("Sword +1 to hit") == "Sword to hit"

    def test_strips_plus_parry(self):
        # "to hit" and "parry" are kept as separate skill types
        assert normalize_skill_name("Shield +2 parry") == "Shield parry"

    def test_strips_plus_damage(self):
        # "damage" is kept as a separate skill type
        assert normalize_skill_name("Axe +1 damage") == "Axe damage"

    def test_strips_bare_plus(self):
        assert normalize_skill_name("Sword +1") == "Sword"

    def test_strips_multiplier(self):
        assert normalize_skill_name("Bow (x2)") == "Bow"

    def test_strips_trailing_number(self):
        assert normalize_skill_name("Farming 2") == "Farming"

    def test_case_insensitive(self):
        # Case insensitive matching, but keeps the skill type
        assert normalize_skill_name("Sword +1 TO HIT") == "Sword to hit"

    def test_empty_string_returns_empty(self):
        assert normalize_skill_name("") == ""

    def test_whitespace_only_returns_empty(self):
        assert normalize_skill_name("   ") == ""

    def test_preserves_internal_spaces(self):
        assert normalize_skill_name("Two Handed Sword") == "Two Handed Sword"


class TestSkillPoints:
    """Tests for SkillPoints dataclass."""

    def test_default_values_are_zero(self):
        sp = SkillPoints()
        assert sp.automatic == 0
        assert sp.allocated == 0

    def test_total_is_sum_of_automatic_and_allocated(self):
        sp = SkillPoints(automatic=3, allocated=2)
        assert sp.total == 5

    def test_level_calculation(self):
        sp = SkillPoints(automatic=3, allocated=0)
        assert sp.level == 2  # 3 points = Level II

    def test_excess_points_calculation(self):
        sp = SkillPoints(automatic=5, allocated=0)
        assert sp.excess_points == 2  # 5 points = Level II (+2)

    def test_to_dict(self):
        sp = SkillPoints(automatic=2, allocated=1)
        d = sp.to_dict()
        assert d == {"automatic": 2, "allocated": 1, "total": 3}

    def test_from_dict(self):
        d = {"automatic": 2, "allocated": 1}
        sp = SkillPoints.from_dict(d)
        assert sp.automatic == 2
        assert sp.allocated == 1


class TestCharacterSkills:
    """Tests for CharacterSkills container."""

    def test_default_values(self):
        cs = CharacterSkills()
        assert cs.skills == {}
        assert cs.free_points == 0
        assert cs.total_xp == 0

    def test_add_automatic_point(self):
        cs = CharacterSkills()
        cs.add_automatic_point("Sword")
        assert "Sword" in cs.skills
        assert cs.skills["Sword"].automatic == 1

    def test_add_automatic_point_normalizes_name(self):
        cs = CharacterSkills()
        cs.add_automatic_point("Sword +1 to hit")
        # "Sword +1 to hit" normalizes to "Sword to hit" (keeps the type separate)
        assert "Sword to hit" in cs.skills
        assert cs.skills["Sword to hit"].automatic == 1

    def test_add_automatic_point_accumulates(self):
        cs = CharacterSkills()
        cs.add_automatic_point("Sword")
        cs.add_automatic_point("Sword")
        assert cs.skills["Sword"].automatic == 2

    def test_add_free_point(self):
        cs = CharacterSkills()
        cs.add_free_point()
        assert cs.free_points == 1

    def test_allocate_point_success(self):
        cs = CharacterSkills(free_points=3)
        result = cs.allocate_point("Tracking")
        assert result is True
        assert "Tracking" in cs.skills
        assert cs.skills["Tracking"].allocated == 1
        assert cs.free_points == 2

    def test_allocate_point_fails_without_free_points(self):
        cs = CharacterSkills(free_points=0)
        result = cs.allocate_point("Tracking")
        assert result is False
        assert "Tracking" not in cs.skills

    def test_deallocate_point_success(self):
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints(automatic=0, allocated=2)
        result = cs.deallocate_point("Sword")
        assert result is True
        assert cs.skills["Sword"].allocated == 1
        assert cs.free_points == 1

    def test_deallocate_point_fails_without_allocated_points(self):
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints(automatic=2, allocated=0)
        result = cs.deallocate_point("Sword")
        assert result is False
        assert cs.skills["Sword"].automatic == 2
        assert cs.free_points == 0

    def test_add_xp(self):
        cs = CharacterSkills()
        cs.add_xp(1000)
        assert cs.total_xp == 1000
        cs.add_xp(500)
        assert cs.total_xp == 1500

    def test_get_skill_display_level_one(self):
        cs = CharacterSkills()
        cs.add_automatic_point("Sword")
        display = cs.get_skill_display("Sword")
        assert display == "Sword I"

    def test_get_skill_display_with_excess(self):
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints(automatic=5, allocated=0)
        display = cs.get_skill_display("Sword")
        assert display == "Sword II (+2)"

    def test_get_skill_display_unknown_skill(self):
        cs = CharacterSkills()
        display = cs.get_skill_display("Unknown")
        assert display == "Unknown"

    def test_get_display_list(self):
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints(automatic=3, allocated=0)
        cs.skills["Bow"] = SkillPoints(automatic=1, allocated=0)
        display_list = cs.get_display_list()
        assert "Bow I" in display_list
        assert "Sword II" in display_list

    def test_get_skills_with_details(self):
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints(automatic=5, allocated=0)
        details = cs.get_skills_with_details()
        assert len(details) == 1
        sword = details[0]
        assert sword["name"] == "Sword"
        assert sword["display"] == "Sword II (+2)"
        assert sword["level"] == 2
        assert sword["level_roman"] == "II"
        assert sword["total_points"] == 5
        assert sword["automatic_points"] == 5
        assert sword["allocated_points"] == 0
        assert sword["excess_points"] == 2
        assert sword["points_to_next_level"] == 1

    def test_to_dict(self):
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints(automatic=2, allocated=1)
        cs.free_points = 3
        cs.total_xp = 2000
        d = cs.to_dict()
        assert "skill_points" in d
        assert "Sword" in d["skill_points"]
        assert d["free_skill_points"] == 3
        assert d["total_xp"] == 2000

    def test_from_dict(self):
        d = {
            "skill_points": {
                "Sword": {"automatic": 2, "allocated": 1}
            },
            "free_skill_points": 3,
            "total_xp": 2000
        }
        cs = CharacterSkills.from_dict(d)
        assert "Sword" in cs.skills
        assert cs.skills["Sword"].automatic == 2
        assert cs.skills["Sword"].allocated == 1
        assert cs.free_points == 3
        assert cs.total_xp == 2000

    def test_from_legacy_skills(self):
        skill_list = ["Sword", "Sword", "Tracking", "Bow"]
        cs = CharacterSkills.from_legacy_skills(skill_list, years=3)

        assert "Sword" in cs.skills
        assert cs.skills["Sword"].automatic == 2
        assert "Tracking" in cs.skills
        assert cs.skills["Tracking"].automatic == 1
        assert "Bow" in cs.skills
        assert cs.skills["Bow"].automatic == 1
        assert cs.free_points == 3  # years = 3
        assert cs.total_xp == 3000  # years * 1000


class TestSkillLevelProgression:
    """Tests verifying the full skill level progression."""

    def test_skill_level_progression(self):
        """Test that skill levels progress correctly with points."""
        cs = CharacterSkills()
        cs.skills["Sword"] = SkillPoints()

        expected_levels = [
            # (points, expected_level, expected_excess)
            (1, 1, 0),   # Level I
            (2, 1, 1),   # Level I (+1)
            (3, 2, 0),   # Level II
            (4, 2, 1),   # Level II (+1)
            (5, 2, 2),   # Level II (+2)
            (6, 3, 0),   # Level III
            (7, 3, 1),   # Level III (+1)
            (8, 3, 2),   # Level III (+2)
            (9, 3, 3),   # Level III (+3)
            (10, 4, 0),  # Level IV
        ]

        for points, expected_level, expected_excess in expected_levels:
            cs.skills["Sword"] = SkillPoints(automatic=points, allocated=0)
            assert cs.skills["Sword"].level == expected_level, \
                f"With {points} points, expected level {expected_level}"
            assert cs.skills["Sword"].excess_points == expected_excess, \
                f"With {points} points, expected excess {expected_excess}"
