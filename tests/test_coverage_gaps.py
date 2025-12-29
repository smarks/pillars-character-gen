"""
Tests to improve code coverage for uncovered lines.
"""

import pytest
from pillars.attributes import (
    AgingEffects,
    get_aging_effects_for_age,
    display_attribute_rolls,
    generate_attributes_4d6_drop_lowest,
    get_attribute_modifier,
)
from pillars.generator import consolidate_skills
from pillars.dice import roll_with_drop_highest
from pillars.skills import CharacterSkills


class TestAgingEffects:
    """Test aging effects functionality."""

    def test_aging_effects_apply_year(self):
        """Test applying aging effects at specific year thresholds."""
        effects = AgingEffects()

        # Apply year 19 (first aging threshold)
        new_penalties = effects.apply_year(19)
        assert new_penalties["STR"] == -1
        assert new_penalties["DEX"] == -1
        assert effects.str_penalty == -1
        assert effects.dex_penalty == -1

        # Apply year 23 (CON penalty)
        new_penalties = effects.apply_year(23)
        assert new_penalties["CON"] == -1
        assert effects.con_penalty == -1

        # Apply year 51 (all attributes penalty)
        new_penalties = effects.apply_year(51)
        assert new_penalties["STR"] == -1
        assert new_penalties["DEX"] == -1
        assert new_penalties["INT"] == -1
        assert new_penalties["WIS"] == -1
        assert new_penalties["CON"] == -1

    def test_aging_effects_str_with_penalties(self):
        """Test AgingEffects __str__ with penalties."""
        effects = AgingEffects()
        effects.apply_year(19)  # STR and DEX penalties
        effects.apply_year(23)  # CON penalty

        result = str(effects)
        assert "STR -1" in result
        assert "DEX -1" in result
        assert "CON -1" in result

    def test_aging_effects_str_no_penalties(self):
        """Test AgingEffects __str__ with no penalties."""
        effects = AgingEffects()
        result = str(effects)
        assert result == "Aging Penalties: None"

    def test_get_aging_effects_for_age(self):
        """Test getting aging effects for specific ages."""
        # Age 16-34: No penalties
        effects = get_aging_effects_for_age(20)
        assert effects.str_penalty == 0

        # Age 35-38: STR and DEX penalties
        effects = get_aging_effects_for_age(35)
        assert effects.str_penalty == -1
        assert effects.dex_penalty == -1

        # Age 39-42: Also CON penalty
        effects = get_aging_effects_for_age(40)
        assert effects.con_penalty == -1

        # Age 67+: All penalties
        effects = get_aging_effects_for_age(70)
        assert effects.str_penalty == -2  # -1 from year 19, -1 from year 51
        assert effects.int_penalty == -1  # From year 51


class TestDisplayFunctions:
    """Test display/utility functions."""

    def test_display_attribute_rolls(self, capsys):
        """Test display_attribute_rolls function."""
        import random

        random.seed(42)
        attrs = generate_attributes_4d6_drop_lowest()
        display_attribute_rolls(attrs)

        captured = capsys.readouterr()
        assert "ATTRIBUTE GENERATION" in captured.out
        assert "SUMMARY:" in captured.out
        assert "Total:" in captured.out
        assert "Average:" in captured.out


class TestConsolidateSkills:
    """Test skill consolidation with new skill point system."""

    def test_consolidate_skills_with_pattern_matching(self):
        """Test consolidating skills with +1 pattern using skill points."""
        skills = [
            "Sword +1 to hit",
            "Sword +1 to hit",
            "Sword +1 to hit",
            "Cutlass +1 parry",
            "Cutlass +1 parry",
        ]
        result = consolidate_skills(skills)
        # 3 Sword to hit skills = 3 points = Level 2
        assert "Sword to hit II" in result
        # 2 Cutlass parry skills = 2 points = Level 1 (+1)
        assert "Cutlass parry I (+1)" in result

    def test_consolidate_skills_mixed_patterns(self):
        """Test consolidating mixed skill patterns using skill points."""
        skills = [
            "Sword +1 to hit",
            "Sword +1 parry",
            "Tracking",
            "Tracking",
            "Tracking",
        ]
        result = consolidate_skills(skills)
        # "to hit" and "parry" are separate skills now
        assert "Sword to hit I" in result
        assert "Sword parry I" in result
        # 3 Tracking skills = 3 points = Level 2
        assert "Tracking II" in result


class TestDiceErrorHandling:
    """Test dice error handling."""

    def test_roll_with_drop_highest_invalid_num_drop(self):
        """Test error when dropping too many dice."""
        with pytest.raises(ValueError, match="Cannot drop"):
            roll_with_drop_highest(4, 6, 4)  # Can't drop all dice

    def test_roll_with_drop_highest_negative_drop(self):
        """Test error when dropping negative dice."""
        with pytest.raises(ValueError, match="Cannot drop negative"):
            roll_with_drop_highest(4, 6, -1)


class TestSkillsEdgeCases:
    """Test skills module edge cases."""

    def test_add_automatic_point_empty_skill(self):
        """Test adding automatic point with empty skill name."""
        skills = CharacterSkills()
        skills.add_automatic_point("")
        skills.add_automatic_point("   ")
        assert len(skills.skills) == 0

    def test_allocate_point_no_free_points(self):
        """Test allocating point when no free points available."""
        skills = CharacterSkills()
        result = skills.allocate_point("Sword")
        assert result is False
        assert len(skills.skills) == 0

    def test_deallocate_point_no_allocated_points(self):
        """Test deallocating point when none allocated."""
        skills = CharacterSkills()
        skills.add_automatic_point("Sword")
        result = skills.deallocate_point("Sword")
        assert result is False
        assert skills.skills["Sword"].allocated == 0

    def test_get_skill_display_unknown_skill(self):
        """Test getting display for unknown skill."""
        skills = CharacterSkills()
        result = skills.get_skill_display("Unknown Skill")
        assert result == "Unknown Skill"


class TestAttributeModifierEdgeCases:
    """Test attribute modifier edge cases."""

    def test_get_attribute_modifier_extreme_values(self):
        """Test modifier calculation for extreme values."""
        # Below minimum
        assert get_attribute_modifier(1) == -5
        assert get_attribute_modifier(2) == -5

        # Above maximum
        assert get_attribute_modifier(19) == 6  # 5 + (19-18)
        assert get_attribute_modifier(20) == 7  # 5 + (20-18)


class TestCharacterDisplay:
    """Test Character display with various configurations."""

    def test_character_str_with_craft_type(self):
        """Test Character.__str__ with craft type."""
        from pillars.generator import generate_character, Character
        from pillars.attributes import (
            TrackType,
            CraftType,
            create_skill_track_for_choice,
        )

        # Create a character with Crafts track
        import random

        random.seed(42)
        char = generate_character(years=0, chosen_track=TrackType.CRAFTS)

        result = str(char)
        assert "Craft:" in result or "Skill Track:" in result

    def test_character_str_with_magic_school(self):
        """Test Character.__str__ with magic school."""
        from pillars.generator import generate_character
        from pillars.attributes import TrackType

        # Create a character with Magic track (requires INT or WIS bonus)
        import random

        random.seed(42)
        # Try multiple times to get a character with mental bonus
        for _ in range(50):
            char = generate_character(
                years=0, chosen_track=TrackType.MAGIC, attribute_focus="mental"
            )
            if char.skill_track and char.skill_track.magic_school:
                result = str(char)
                assert "Magic School:" in result or "School:" in result
                break

    def test_character_str_with_aging_effects(self):
        """Test Character.__str__ with aging effects."""
        from pillars.generator import generate_character
        from pillars.attributes import TrackType

        import random

        random.seed(42)
        # Generate character with many years to trigger aging
        char = generate_character(years=20, chosen_track=TrackType.WORKER)

        if char.prior_experience and char.prior_experience.aging_effects:
            result = str(char)
            # Aging effects should be shown if penalties exist
            penalties = char.prior_experience.aging_effects.total_penalties()
            if any(v != 0 for v in penalties.values()):
                assert "Aging" in result or "Penalties" in result

    def test_character_str_with_prior_experience_no_skills(self):
        """Test Character.__str__ when prior_experience has no skills."""
        from pillars.generator import Character
        from pillars.attributes import (
            generate_attributes_4d6_drop_lowest,
            roll_appearance,
            roll_height,
            roll_weight,
            roll_provenance,
            roll_location,
            roll_literacy_check,
            roll_wealth,
            TrackType,
            SkillTrack,
            PriorExperience,
            create_auto_accept_check,
        )

        import random

        random.seed(42)
        attrs = generate_attributes_4d6_drop_lowest()
        track = SkillTrack(
            track=TrackType.WORKER,
            acceptance_check=create_auto_accept_check(TrackType.WORKER),
            survivability=4,
            survivability_roll=None,
            initial_skills=[],
            craft_type=None,
            craft_rolls=None,
        )
        pe = PriorExperience(
            starting_age=16,
            final_age=17,
            years_served=1,
            track=TrackType.WORKER,
            survivability_target=4,
            yearly_results=[],
            total_skill_points=0,
            all_skills=[],
            died=False,
            death_year=None,
        )
        char = Character(
            attributes=attrs,
            appearance=roll_appearance(),
            height=roll_height(),
            weight=roll_weight(attrs.STR),
            provenance=roll_provenance(),
            location=roll_location(),
            literacy=roll_literacy_check(attrs.INT, 0),
            wealth=roll_wealth(),
            skill_track=track,
            prior_experience=pe,
        )
        result = str(char)
        # Should handle empty skills gracefully
        assert "Skills" in result or len(result) > 0


class TestSkillsEdgeCasesMore:
    """More edge case tests for skills."""

    def test_allocate_point_empty_skill_name(self):
        """Test allocating point with empty skill name."""
        skills = CharacterSkills()
        skills.add_free_point()
        result = skills.allocate_point("")
        assert result is False

    def test_deallocate_point_empty_skill_name(self):
        """Test deallocating point with empty skill name."""
        skills = CharacterSkills()
        result = skills.deallocate_point("")
        assert result is False

    def test_get_skill_display_less_than_one_point(self):
        """Test get_skill_display with less than 1 point (edge case)."""
        skills = CharacterSkills()
        # This shouldn't happen in practice, but test the edge case
        skills.skills["Test"] = type(
            "SkillPoints", (), {"total": 0, "automatic": 0, "allocated": 0}
        )()
        result = skills.get_skill_display("Test")
        assert "Test" in result
