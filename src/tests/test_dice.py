"""
Unit tests for dice rolling utilities.
"""

import unittest
import random
from main.helpers.dice import (
    roll_die,
    roll_dice,
    roll_and_sum,
    roll_with_drop_lowest,
    roll_with_drop_highest,
    roll_percentile,
    roll_demon_die,
    format_dice_notation
)


class TestRollDie(unittest.TestCase):
    """Test single die rolling."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_roll_d6(self):
        """Test rolling a 6-sided die."""
        result = roll_die(6)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 6)

    def test_roll_d20(self):
        """Test rolling a 20-sided die."""
        result = roll_die(20)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 20)

    def test_roll_d100(self):
        """Test rolling a 100-sided die."""
        result = roll_die(100)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 100)

    def test_invalid_sides(self):
        """Test that rolling a die with < 1 sides raises ValueError."""
        with self.assertRaises(ValueError):
            roll_die(0)
        with self.assertRaises(ValueError):
            roll_die(-1)

    def test_distribution(self):
        """Test that die rolls are reasonably distributed."""
        # Roll many times and check we get all possible values
        rolls = [roll_die(6) for _ in range(1000)]
        unique_values = set(rolls)

        # Should get all values 1-6 in 1000 rolls
        self.assertEqual(unique_values, {1, 2, 3, 4, 5, 6})


class TestRollDice(unittest.TestCase):
    """Test multiple dice rolling."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_roll_3d6(self):
        """Test rolling 3d6."""
        result = roll_dice(3, 6)
        self.assertEqual(len(result), 3)
        for die in result:
            self.assertGreaterEqual(die, 1)
            self.assertLessEqual(die, 6)

    def test_roll_4d6(self):
        """Test rolling 4d6."""
        result = roll_dice(4, 6)
        self.assertEqual(len(result), 4)

    def test_roll_1d20(self):
        """Test rolling 1d20."""
        result = roll_dice(1, 20)
        self.assertEqual(len(result), 1)
        self.assertGreaterEqual(result[0], 1)
        self.assertLessEqual(result[0], 20)

    def test_invalid_num_dice(self):
        """Test that rolling < 1 dice raises ValueError."""
        with self.assertRaises(ValueError):
            roll_dice(0, 6)
        with self.assertRaises(ValueError):
            roll_dice(-1, 6)

    def test_invalid_sides(self):
        """Test that invalid sides raises ValueError."""
        with self.assertRaises(ValueError):
            roll_dice(3, 0)


class TestRollAndSum(unittest.TestCase):
    """Test rolling and summing dice."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_roll_and_sum_3d6(self):
        """Test rolling and summing 3d6."""
        rolls, total = roll_and_sum(3, 6)
        self.assertEqual(len(rolls), 3)
        self.assertEqual(total, sum(rolls))
        self.assertGreaterEqual(total, 3)
        self.assertLessEqual(total, 18)

    def test_roll_and_sum_consistency(self):
        """Test that sum matches manual calculation."""
        rolls, total = roll_and_sum(5, 10)
        self.assertEqual(total, sum(rolls))


class TestRollWithDropLowest(unittest.TestCase):
    """Test rolling with dropping lowest dice."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_4d6_drop_1(self):
        """Test 4d6 drop lowest 1."""
        all_rolls, kept_rolls, total = roll_with_drop_lowest(4, 6, 1)

        self.assertEqual(len(all_rolls), 4)
        self.assertEqual(len(kept_rolls), 3)
        self.assertEqual(total, sum(kept_rolls))

        # Verify kept rolls are the 3 highest
        expected_kept = sorted(all_rolls, reverse=True)[:3]
        self.assertEqual(sorted(kept_rolls, reverse=True), expected_kept)

    def test_5d6_drop_2(self):
        """Test 5d6 drop lowest 2."""
        all_rolls, kept_rolls, total = roll_with_drop_lowest(5, 6, 2)

        self.assertEqual(len(all_rolls), 5)
        self.assertEqual(len(kept_rolls), 3)
        self.assertEqual(total, sum(kept_rolls))

    def test_drop_none(self):
        """Test rolling without dropping any dice."""
        all_rolls, kept_rolls, total = roll_with_drop_lowest(3, 6, 0)

        self.assertEqual(len(all_rolls), 3)
        self.assertEqual(len(kept_rolls), 3)
        self.assertEqual(all_rolls, kept_rolls)

    def test_invalid_drop_count(self):
        """Test that dropping >= num_dice raises ValueError."""
        with self.assertRaises(ValueError):
            roll_with_drop_lowest(3, 6, 3)
        with self.assertRaises(ValueError):
            roll_with_drop_lowest(3, 6, 4)
        with self.assertRaises(ValueError):
            roll_with_drop_lowest(3, 6, -1)

    def test_kept_rolls_are_highest(self):
        """Test that kept rolls are the highest values."""
        random.seed(100)  # Use different seed for variety
        all_rolls, kept_rolls, total = roll_with_drop_lowest(4, 6, 1)

        # Kept rolls should be the 3 highest
        expected_kept = sorted(all_rolls, reverse=True)[:3]
        self.assertEqual(sorted(kept_rolls, reverse=True), expected_kept)


class TestRollWithDropHighest(unittest.TestCase):
    """Test rolling with dropping highest dice."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_4d6_drop_1(self):
        """Test 4d6 drop highest 1."""
        all_rolls, kept_rolls, total = roll_with_drop_highest(4, 6, 1)

        self.assertEqual(len(all_rolls), 4)
        self.assertEqual(len(kept_rolls), 3)
        self.assertEqual(total, sum(kept_rolls))

    def test_kept_rolls_are_lowest(self):
        """Test that kept rolls are the lowest values."""
        random.seed(100)
        all_rolls, kept_rolls, total = roll_with_drop_highest(4, 6, 1)

        # Kept rolls should be the 3 lowest
        expected_kept = sorted(all_rolls)[:3]
        self.assertEqual(sorted(kept_rolls), expected_kept)


class TestRollPercentile(unittest.TestCase):
    """Test percentile dice rolling."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_roll_percentile(self):
        """Test rolling percentile dice."""
        result = roll_percentile()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 100)

    def test_percentile_distribution(self):
        """Test percentile distribution over many rolls."""
        rolls = [roll_percentile() for _ in range(1000)]

        # Should get values across the entire range
        self.assertGreater(len(set(rolls)), 50)  # At least 50 different values
        self.assertGreaterEqual(min(rolls), 1)
        self.assertLessEqual(max(rolls), 100)


class TestFormatDiceNotation(unittest.TestCase):
    """Test dice notation formatting."""

    def test_basic_notation(self):
        """Test basic dice notation without modifier."""
        self.assertEqual(format_dice_notation(3, 6), "3d6")
        self.assertEqual(format_dice_notation(1, 20), "1d20")
        self.assertEqual(format_dice_notation(2, 10), "2d10")

    def test_positive_modifier(self):
        """Test notation with positive modifier."""
        self.assertEqual(format_dice_notation(3, 6, 2), "3d6+2")
        self.assertEqual(format_dice_notation(1, 20, 5), "1d20+5")

    def test_negative_modifier(self):
        """Test notation with negative modifier."""
        self.assertEqual(format_dice_notation(3, 6, -2), "3d6-2")
        self.assertEqual(format_dice_notation(1, 20, -1), "1d20-1")

    def test_zero_modifier(self):
        """Test notation with zero modifier."""
        self.assertEqual(format_dice_notation(3, 6, 0), "3d6")


class TestRollDemonDie(unittest.TestCase):
    """Test demon die rolling."""

    def test_average_result(self):
        """Test that 2-5 returns intensity 0."""
        # Find a seed that gives an average result (2-5)
        for seed in range(100):
            random.seed(seed)
            rolls, intensity = roll_demon_die()
            if rolls[0] in [2, 3, 4, 5]:
                self.assertEqual(len(rolls), 1)
                self.assertEqual(intensity, 0)
                return
        self.fail("Could not find a seed that produces an average result")

    def test_single_one_pretty(self):
        """Test that a single 1 followed by non-1 gives intensity -1."""
        # We need to find a seed that gives [1, non-1]
        random.seed(3)  # Test with seed 3
        rolls, intensity = roll_demon_die()
        if rolls[0] == 1:
            self.assertLess(intensity, 0)
            self.assertEqual(abs(intensity), sum(1 for r in rolls if r == 1))

    def test_single_six_ugly(self):
        """Test that a single 6 followed by non-6 gives intensity 1."""
        random.seed(7)  # Test with seed 7
        rolls, intensity = roll_demon_die()
        if rolls[0] == 6:
            self.assertGreater(intensity, 0)
            self.assertEqual(intensity, sum(1 for r in rolls if r == 6))

    def test_intensity_matches_count(self):
        """Test that intensity magnitude equals count of 1s or 6s."""
        for seed in range(100):
            random.seed(seed)
            rolls, intensity = roll_demon_die()

            if intensity < 0:
                # Pretty: count of 1s
                ones = sum(1 for r in rolls if r == 1)
                self.assertEqual(abs(intensity), ones)
            elif intensity > 0:
                # Ugly: count of 6s
                sixes = sum(1 for r in rolls if r == 6)
                self.assertEqual(intensity, sixes)
            else:
                # Average: first roll was 2-5
                self.assertIn(rolls[0], [2, 3, 4, 5])

    def test_rolls_end_on_non_exploding_value(self):
        """Test that rolls stop when non-exploding value is hit."""
        for seed in range(100):
            random.seed(seed)
            rolls, intensity = roll_demon_die()

            if len(rolls) > 1:
                # Last roll should not be the exploding value
                if rolls[0] == 1:
                    self.assertNotEqual(rolls[-1], 1)
                elif rolls[0] == 6:
                    self.assertNotEqual(rolls[-1], 6)


class TestDiceStatistics(unittest.TestCase):
    """Test statistical properties of dice rolls."""

    def test_3d6_average(self):
        """Test that 3d6 average is close to expected value (10.5)."""
        random.seed(None)  # Use actual randomness
        rolls = [sum(roll_dice(3, 6)) for _ in range(10000)]
        average = sum(rolls) / len(rolls)

        # Expected average is 10.5, allow some variance
        self.assertAlmostEqual(average, 10.5, delta=0.2)

    def test_4d6_drop_lowest_average(self):
        """Test that 4d6 drop lowest has higher average than 3d6."""
        random.seed(None)
        rolls_3d6 = [sum(roll_dice(3, 6)) for _ in range(1000)]
        rolls_4d6 = [roll_with_drop_lowest(4, 6, 1)[2] for _ in range(1000)]

        avg_3d6 = sum(rolls_3d6) / len(rolls_3d6)
        avg_4d6 = sum(rolls_4d6) / len(rolls_4d6)

        # 4d6 drop lowest should have higher average
        self.assertGreater(avg_4d6, avg_3d6)

    def test_4d6_drop_lowest_minimum(self):
        """Test that 4d6 drop lowest minimum is 3."""
        random.seed(42)
        # Even with bad rolls, minimum should be 3 (three 1s)
        rolls = [roll_with_drop_lowest(4, 6, 1)[2] for _ in range(100)]
        self.assertGreaterEqual(min(rolls), 3)


if __name__ == '__main__':
    unittest.main()
