"""
Unit tests for character attribute generation.
"""

import unittest
import random
from pillars.attributes import (
    get_attribute_modifier,
    roll_single_attribute_3d6,
    roll_single_attribute_4d6_drop_lowest,
    generate_attributes_3d6,
    generate_attributes_4d6_drop_lowest,
    generate_attributes_point_buy,
    validate_point_buy,
    roll_appearance,
    get_appearance_description,
    roll_height,
    roll_weight,
    roll_provenance,
    roll_location,
    roll_literacy_check,
    roll_wealth,
    get_wealth_level,
    roll_skill_track,
    roll_craft_type,
    roll_survivability_random,
    roll_prior_experience,
    roll_yearly_skill,
    roll_survivability_check,
    check_army_acceptance,
    check_navy_acceptance,
    check_ranger_acceptance,
    check_officer_acceptance,
    check_merchant_acceptance,
    get_eligible_tracks,
    select_optimal_track,
    get_nobility_rank,
    get_merchant_type,
    get_commoner_type,
    get_craft_type,
    CORE_ATTRIBUTES,
    HEIGHT_TABLE,
    WEIGHT_TABLE,
    WEALTH_TABLE,
    SURVIVAL_SKILLS,
    TRACK_SURVIVABILITY,
    TRACK_INITIAL_SKILLS,
    TRACK_YEARLY_SKILLS,
    CharacterAttributes,
    AttributeRoll,
    Appearance,
    Height,
    Weight,
    Wealth,
    Provenance,
    Location,
    LiteracyCheck,
    TrackType,
    CraftType,
    AcceptanceCheck,
    SkillTrack,
    YearResult,
    PriorExperience
)


class TestAttributeModifier(unittest.TestCase):
    """Test attribute modifier calculations."""

    def test_low_modifiers(self):
        """Test modifiers for low attribute values."""
        self.assertEqual(get_attribute_modifier(3), -5)
        self.assertEqual(get_attribute_modifier(4), -4)
        self.assertEqual(get_attribute_modifier(5), -3)
        self.assertEqual(get_attribute_modifier(6), -2)
        self.assertEqual(get_attribute_modifier(7), -1)

    def test_average_modifiers(self):
        """Test modifiers for average attribute values."""
        for value in range(8, 14):
            self.assertEqual(get_attribute_modifier(value), 0)

    def test_high_modifiers(self):
        """Test modifiers for high attribute values."""
        self.assertEqual(get_attribute_modifier(14), 1)
        self.assertEqual(get_attribute_modifier(15), 2)
        self.assertEqual(get_attribute_modifier(16), 3)
        self.assertEqual(get_attribute_modifier(17), 4)
        self.assertEqual(get_attribute_modifier(18), 5)

    def test_exceptional_values(self):
        """Test modifiers for values outside normal range."""
        # Below minimum
        self.assertEqual(get_attribute_modifier(2), -5)
        self.assertEqual(get_attribute_modifier(1), -5)

        # Above maximum (should extend pattern)
        self.assertEqual(get_attribute_modifier(19), 6)
        self.assertEqual(get_attribute_modifier(20), 7)


class TestSingleAttributeRolls(unittest.TestCase):
    """Test single attribute rolling methods."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_roll_3d6(self):
        """Test rolling a single attribute with 3d6."""
        rolls, total = roll_single_attribute_3d6()

        self.assertEqual(len(rolls), 3)
        self.assertEqual(total, sum(rolls))
        self.assertGreaterEqual(total, 3)
        self.assertLessEqual(total, 18)

    def test_roll_4d6_drop_lowest(self):
        """Test rolling a single attribute with 4d6 drop lowest."""
        all_rolls, kept_rolls, total = roll_single_attribute_4d6_drop_lowest()

        self.assertEqual(len(all_rolls), 4)
        self.assertEqual(len(kept_rolls), 3)
        self.assertEqual(total, sum(kept_rolls))
        self.assertGreaterEqual(total, 3)
        self.assertLessEqual(total, 18)


class TestGenerate3d6(unittest.TestCase):
    """Test generating full attribute set with 3d6."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_generates_all_attributes(self):
        """Test that all six attributes are generated."""
        character = generate_attributes_3d6()

        for attr in CORE_ATTRIBUTES:
            self.assertTrue(hasattr(character, attr))
            value = getattr(character, attr)
            self.assertGreaterEqual(value, 3)
            self.assertLessEqual(value, 18)

    def test_generation_method_recorded(self):
        """Test that generation method is recorded."""
        character = generate_attributes_3d6()
        self.assertEqual(character.generation_method, "3d6")

    def test_roll_details_recorded(self):
        """Test that roll details are recorded."""
        character = generate_attributes_3d6()

        self.assertEqual(len(character.roll_details), 6)

        for roll_detail in character.roll_details:
            self.assertIsInstance(roll_detail, AttributeRoll)
            self.assertIn(roll_detail.attribute_name, CORE_ATTRIBUTES)
            self.assertEqual(len(roll_detail.all_rolls), 3)
            self.assertEqual(len(roll_detail.kept_rolls), 3)
            self.assertEqual(roll_detail.value, sum(roll_detail.kept_rolls))

    def test_specific_seed_results(self):
        """Test specific results with known seed."""
        random.seed(42)
        character = generate_attributes_3d6()

        # With seed 42, we know the sequence
        self.assertEqual(character.STR, 8)
        self.assertEqual(character.DEX, 11)
        self.assertEqual(character.INT, 10)
        self.assertEqual(character.generation_method, "3d6")


class TestGenerate4d6DropLowest(unittest.TestCase):
    """Test generating full attribute set with 4d6 drop lowest."""

    def setUp(self):
        """Set random seed for reproducible tests."""
        random.seed(42)

    def test_generates_all_attributes(self):
        """Test that all six attributes are generated."""
        character = generate_attributes_4d6_drop_lowest()

        for attr in CORE_ATTRIBUTES:
            self.assertTrue(hasattr(character, attr))
            value = getattr(character, attr)
            self.assertGreaterEqual(value, 3)
            self.assertLessEqual(value, 18)

    def test_generation_method_recorded(self):
        """Test that generation method is recorded."""
        character = generate_attributes_4d6_drop_lowest()
        self.assertEqual(character.generation_method, "4d6 drop lowest")

    def test_roll_details_recorded(self):
        """Test that roll details are recorded correctly."""
        character = generate_attributes_4d6_drop_lowest()

        self.assertEqual(len(character.roll_details), 6)

        for roll_detail in character.roll_details:
            self.assertIsInstance(roll_detail, AttributeRoll)
            self.assertIn(roll_detail.attribute_name, CORE_ATTRIBUTES)
            self.assertEqual(len(roll_detail.all_rolls), 4)
            self.assertEqual(len(roll_detail.kept_rolls), 3)
            self.assertEqual(roll_detail.value, sum(roll_detail.kept_rolls))

    def test_higher_average_than_3d6(self):
        """Test that 4d6 drop lowest produces higher averages."""
        random.seed(None)  # Use actual randomness

        # Generate many characters with each method
        chars_3d6 = [generate_attributes_3d6() for _ in range(100)]
        chars_4d6 = [generate_attributes_4d6_drop_lowest() for _ in range(100)]

        # Calculate average totals
        avg_3d6 = sum(
            sum(getattr(c, attr) for attr in CORE_ATTRIBUTES)
            for c in chars_3d6
        ) / len(chars_3d6)

        avg_4d6 = sum(
            sum(getattr(c, attr) for attr in CORE_ATTRIBUTES)
            for c in chars_4d6
        ) / len(chars_4d6)

        # 4d6 drop lowest should have higher average
        self.assertGreater(avg_4d6, avg_3d6)


class TestCharacterAttributes(unittest.TestCase):
    """Test CharacterAttributes class methods."""

    def setUp(self):
        """Create a test character."""
        self.character = CharacterAttributes(
            STR=15,
            DEX=12,
            INT=10,
            WIS=8,
            CON=14,
            CHR=16,
            generation_method="test"
        )

    def test_get_modifier(self):
        """Test getting individual attribute modifiers."""
        self.assertEqual(self.character.get_modifier("STR"), 2)
        self.assertEqual(self.character.get_modifier("DEX"), 0)
        self.assertEqual(self.character.get_modifier("INT"), 0)
        self.assertEqual(self.character.get_modifier("WIS"), 0)
        self.assertEqual(self.character.get_modifier("CON"), 1)
        self.assertEqual(self.character.get_modifier("CHR"), 3)

    def test_get_modifier_invalid_attribute(self):
        """Test that invalid attribute raises ValueError."""
        with self.assertRaises(ValueError):
            self.character.get_modifier("INVALID")

    def test_get_all_modifiers(self):
        """Test getting all modifiers at once."""
        modifiers = self.character.get_all_modifiers()

        self.assertEqual(len(modifiers), 6)
        self.assertEqual(modifiers["STR"], 2)
        self.assertEqual(modifiers["DEX"], 0)
        self.assertEqual(modifiers["INT"], 0)
        self.assertEqual(modifiers["WIS"], 0)
        self.assertEqual(modifiers["CON"], 1)
        self.assertEqual(modifiers["CHR"], 3)

    def test_str_representation(self):
        """Test string representation of character."""
        result = str(self.character)

        # Should contain all attributes
        for attr in CORE_ATTRIBUTES:
            self.assertIn(attr, result)

        # Should contain generation method
        self.assertIn("test", result)


class TestAttributeRoll(unittest.TestCase):
    """Test AttributeRoll dataclass."""

    def test_creation(self):
        """Test creating an AttributeRoll."""
        roll = AttributeRoll(
            attribute_name="STR",
            all_rolls=[3, 5, 2, 6],
            kept_rolls=[3, 5, 6],
            value=14,
            modifier=1
        )

        self.assertEqual(roll.attribute_name, "STR")
        self.assertEqual(roll.all_rolls, [3, 5, 2, 6])
        self.assertEqual(roll.kept_rolls, [3, 5, 6])
        self.assertEqual(roll.value, 14)
        self.assertEqual(roll.modifier, 1)

    def test_str_representation(self):
        """Test string representation of roll."""
        roll = AttributeRoll(
            attribute_name="STR",
            all_rolls=[3, 5, 2, 6],
            kept_rolls=[3, 5, 6],
            value=14,
            modifier=1
        )

        result = str(roll)
        self.assertIn("STR", result)
        self.assertIn("14", result)
        self.assertIn("+1", result)


class TestPointBuy(unittest.TestCase):
    """Test point buy system."""

    def test_generate_point_buy_template(self):
        """Test generating point buy template."""
        character = generate_attributes_point_buy(65)

        # Should have all attributes
        for attr in CORE_ATTRIBUTES:
            self.assertTrue(hasattr(character, attr))

        # Should record generation method
        self.assertIn("Point Buy", character.generation_method)

    def test_validate_point_buy_valid(self):
        """Test validating a legal point buy."""
        attributes = {
            "STR": 10,
            "DEX": 12,
            "INT": 14,
            "WIS": 11,
            "CON": 9,
            "CHR": 9
        }

        is_valid, message = validate_point_buy(attributes)
        self.assertTrue(is_valid)
        self.assertEqual(message, "")

    def test_validate_point_buy_too_many_points(self):
        """Test validating point buy with too many points."""
        attributes = {
            "STR": 18,
            "DEX": 18,
            "INT": 18,
            "WIS": 18,
            "CON": 18,
            "CHR": 18
        }

        is_valid, message = validate_point_buy(attributes)
        self.assertFalse(is_valid)
        self.assertIn("Total points", message)

    def test_validate_point_buy_too_few_points(self):
        """Test validating point buy with too few points."""
        attributes = {
            "STR": 8,
            "DEX": 8,
            "INT": 8,
            "WIS": 8,
            "CON": 8,
            "CHR": 8
        }

        is_valid, message = validate_point_buy(attributes)
        self.assertFalse(is_valid)
        self.assertIn("Total points", message)

    def test_validate_point_buy_missing_attribute(self):
        """Test validating point buy with missing attribute."""
        attributes = {
            "STR": 10,
            "DEX": 12,
            "INT": 14,
            "WIS": 11,
            "CON": 9
            # Missing CHR
        }

        is_valid, message = validate_point_buy(attributes)
        self.assertFalse(is_valid)
        self.assertIn("Missing attribute", message)

    def test_validate_point_buy_value_too_low(self):
        """Test validating point buy with value below minimum."""
        attributes = {
            "STR": 2,  # Below minimum
            "DEX": 12,
            "INT": 14,
            "WIS": 11,
            "CON": 13,
            "CHR": 13
        }

        is_valid, message = validate_point_buy(attributes)
        self.assertFalse(is_valid)
        self.assertIn("below minimum", message)

    def test_validate_point_buy_value_too_high(self):
        """Test validating point buy with value above maximum."""
        attributes = {
            "STR": 19,  # Above maximum
            "DEX": 12,
            "INT": 12,
            "WIS": 11,
            "CON": 11,
            "CHR": 0
        }

        is_valid, message = validate_point_buy(attributes)
        self.assertFalse(is_valid)


class TestAttributeStatistics(unittest.TestCase):
    """Test statistical properties of attribute generation."""

    def test_3d6_produces_valid_range(self):
        """Test that 3d6 produces values in expected range."""
        random.seed(None)
        characters = [generate_attributes_3d6() for _ in range(100)]

        for character in characters:
            for attr in CORE_ATTRIBUTES:
                value = getattr(character, attr)
                self.assertGreaterEqual(value, 3)
                self.assertLessEqual(value, 18)

    def test_4d6_produces_valid_range(self):
        """Test that 4d6 drop lowest produces values in expected range."""
        random.seed(None)
        characters = [generate_attributes_4d6_drop_lowest() for _ in range(100)]

        for character in characters:
            for attr in CORE_ATTRIBUTES:
                value = getattr(character, attr)
                self.assertGreaterEqual(value, 3)
                self.assertLessEqual(value, 18)


class TestAppearance(unittest.TestCase):
    """Test appearance generation."""

    def test_appearance_description_average(self):
        """Test average appearance description."""
        self.assertEqual(get_appearance_description(0), "Average")

    def test_appearance_description_pretty(self):
        """Test pretty appearance descriptions."""
        self.assertEqual(get_appearance_description(-1), "Pretty")
        self.assertEqual(get_appearance_description(-2), "Very Pretty")
        self.assertEqual(get_appearance_description(-3), "Extremely Pretty")

    def test_appearance_description_ugly(self):
        """Test ugly appearance descriptions."""
        self.assertEqual(get_appearance_description(1), "Ugly")
        self.assertEqual(get_appearance_description(2), "Very Ugly")
        self.assertEqual(get_appearance_description(3), "Extremely Ugly")

    def test_roll_appearance_returns_appearance(self):
        """Test that roll_appearance returns an Appearance object."""
        random.seed(42)
        appearance = roll_appearance()
        self.assertIsInstance(appearance, Appearance)
        self.assertIsInstance(appearance.rolls, list)
        self.assertIsInstance(appearance.intensity, int)
        self.assertIsInstance(appearance.description, str)

    def test_appearance_str_representation(self):
        """Test string representation of appearance."""
        appearance = Appearance(rolls=[6, 6, 2], intensity=2, description="Very Ugly")
        result = str(appearance)
        self.assertIn("Very Ugly", result)
        self.assertIn("6, 6, 2", result)

    def test_appearance_intensity_matches_description(self):
        """Test that intensity matches the description."""
        for seed in range(50):
            random.seed(seed)
            appearance = roll_appearance()

            if appearance.intensity == 0:
                self.assertEqual(appearance.description, "Average")
            elif appearance.intensity < 0:
                self.assertIn("Pretty", appearance.description)
            else:
                self.assertIn("Ugly", appearance.description)


class TestHeight(unittest.TestCase):
    """Test height generation."""

    def test_height_table_values(self):
        """Test that height table has correct values."""
        self.assertEqual(HEIGHT_TABLE[1], (14, 56))  # 4'8"
        self.assertEqual(HEIGHT_TABLE[2], (15, 60))  # 5'0"
        self.assertEqual(HEIGHT_TABLE[3], (16, 64))  # 5'4"
        self.assertEqual(HEIGHT_TABLE[4], (17, 68))  # 5'8"
        self.assertEqual(HEIGHT_TABLE[5], (18, 72))  # 6'0"
        self.assertEqual(HEIGHT_TABLE[6], (19, 76))  # 6'4"

    def test_roll_height_returns_height(self):
        """Test that roll_height returns a Height object."""
        random.seed(42)
        height = roll_height()
        self.assertIsInstance(height, Height)
        self.assertIsInstance(height.rolls, list)
        self.assertIsInstance(height.hands, int)
        self.assertIsInstance(height.inches, int)

    def test_height_imperial_format(self):
        """Test imperial format conversion."""
        height = Height(rolls=[4], hands=17, inches=68)
        self.assertEqual(height.feet, 5)
        self.assertEqual(height.remaining_inches, 8)
        self.assertEqual(height.imperial, "5'8\"")

    def test_height_str_representation(self):
        """Test string representation of height."""
        height = Height(rolls=[4], hands=17, inches=68)
        result = str(height)
        self.assertIn("17 hands", result)
        self.assertIn("5'8\"", result)

    def test_standard_rolls_use_table(self):
        """Test that rolls 2-5 use the table directly."""
        for seed in range(100):
            random.seed(seed)
            height = roll_height()
            if height.rolls[0] in [2, 3, 4, 5]:
                expected_hands, expected_inches = HEIGHT_TABLE[height.rolls[0]]
                self.assertEqual(height.hands, expected_hands)
                self.assertEqual(height.inches, expected_inches)

    def test_exploding_ones_subtract_height(self):
        """Test that multiple 1s reduce height."""
        for seed in range(200):
            random.seed(seed)
            height = roll_height()
            if height.rolls[0] == 1 and len(height.rolls) > 1:
                ones_count = sum(1 for r in height.rolls if r == 1)
                # Each additional 1 subtracts 4 inches from base 56
                expected_inches = 56 - (4 * (ones_count - 1))
                self.assertEqual(height.inches, expected_inches)
                break

    def test_exploding_sixes_add_height(self):
        """Test that multiple 6s increase height."""
        for seed in range(200):
            random.seed(seed)
            height = roll_height()
            if height.rolls[0] == 6 and len(height.rolls) > 1:
                sixes_count = sum(1 for r in height.rolls if r == 6)
                # Each additional 6 adds 4 inches to base 76
                expected_inches = 76 + (4 * (sixes_count - 1))
                self.assertEqual(height.inches, expected_inches)
                break


class TestWeight(unittest.TestCase):
    """Test weight generation."""

    def test_weight_table_values(self):
        """Test that weight table has correct values."""
        self.assertEqual(WEIGHT_TABLE[1], 8)
        self.assertEqual(WEIGHT_TABLE[2], 9)
        self.assertEqual(WEIGHT_TABLE[3], 10)
        self.assertEqual(WEIGHT_TABLE[4], 11)
        self.assertEqual(WEIGHT_TABLE[5], 12)
        self.assertEqual(WEIGHT_TABLE[6], 13)

    def test_roll_weight_returns_weight(self):
        """Test that roll_weight returns a Weight object."""
        random.seed(42)
        weight = roll_weight(10)
        self.assertIsInstance(weight, Weight)
        self.assertIsInstance(weight.rolls, list)
        self.assertIsInstance(weight.base_stones, int)
        self.assertIsInstance(weight.str_bonus_stones, float)
        self.assertIsInstance(weight.total_stones, float)

    def test_weight_str_bonus_calculation(self):
        """Test STR bonus is correctly calculated."""
        random.seed(1)  # Get a predictable roll
        weight = roll_weight(14)
        self.assertEqual(weight.str_bonus_stones, 7.0)  # 14 / 2

    def test_weight_total_calculation(self):
        """Test total weight calculation."""
        weight = Weight(rolls=[3], base_stones=10, str_bonus_stones=5.0, total_stones=15.0)
        self.assertEqual(weight.total_stones, 15.0)
        self.assertEqual(weight.total_pounds, 210)  # 15 * 14

    def test_weight_str_representation(self):
        """Test string representation of weight."""
        weight = Weight(rolls=[3], base_stones=10, str_bonus_stones=5.0, total_stones=15.0)
        result = str(weight)
        self.assertIn("15.0 stones", result)
        self.assertIn("210 lbs", result)

    def test_standard_rolls_use_table(self):
        """Test that rolls 2-5 use the table directly."""
        for seed in range(100):
            random.seed(seed)
            weight = roll_weight(10)
            if weight.rolls[0] in [2, 3, 4, 5]:
                expected_base = WEIGHT_TABLE[weight.rolls[0]]
                self.assertEqual(weight.base_stones, expected_base)

    def test_exploding_ones_subtract_weight(self):
        """Test that multiple 1s reduce base weight."""
        for seed in range(200):
            random.seed(seed)
            weight = roll_weight(10)
            if weight.rolls[0] == 1 and len(weight.rolls) > 1:
                ones_count = sum(1 for r in weight.rolls if r == 1)
                # Each additional 1 subtracts 1 stone from base 8
                expected_base = 8 - (ones_count - 1)
                self.assertEqual(weight.base_stones, expected_base)
                break

    def test_exploding_sixes_add_weight(self):
        """Test that multiple 6s increase base weight."""
        for seed in range(200):
            random.seed(seed)
            weight = roll_weight(10)
            if weight.rolls[0] == 6 and len(weight.rolls) > 1:
                sixes_count = sum(1 for r in weight.rolls if r == 6)
                # Each additional 6 adds 1 stone to base 13
                expected_base = 13 + (sixes_count - 1)
                self.assertEqual(weight.base_stones, expected_base)
                break


class TestProvenance(unittest.TestCase):
    """Test provenance (social class) generation."""

    def test_nobility_ranks(self):
        """Test nobility rank lookup."""
        self.assertEqual(get_nobility_rank(1), "Monarch")
        self.assertEqual(get_nobility_rank(3), "Royal Family")
        self.assertEqual(get_nobility_rank(10), "Duke")
        self.assertEqual(get_nobility_rank(25), "March/Border Lord")
        self.assertEqual(get_nobility_rank(35), "Count/Earl")
        self.assertEqual(get_nobility_rank(45), "Viscount")
        self.assertEqual(get_nobility_rank(55), "Baron")
        self.assertEqual(get_nobility_rank(75), "Baronet")
        self.assertEqual(get_nobility_rank(90), "Knight/Warrior Nobility")

    def test_merchant_types(self):
        """Test merchant type lookup."""
        self.assertEqual(get_merchant_type(50), "Retail")
        self.assertEqual(get_merchant_type(80), "Wholesale")
        self.assertEqual(get_merchant_type(98), "Specialty")

    def test_commoner_types(self):
        """Test commoner type lookup."""
        self.assertEqual(get_commoner_type(50), "Laborer")
        self.assertEqual(get_commoner_type(85), "Crafts")

    def test_craft_types(self):
        """Test craft type lookup."""
        self.assertEqual(get_craft_type(30), "Smith/Builder/Wainwright")
        self.assertEqual(get_craft_type(70), "Medical/Herb Lore/Maker")
        self.assertEqual(get_craft_type(95), "Magic")

    def test_roll_provenance_returns_provenance(self):
        """Test that roll_provenance returns a Provenance object."""
        random.seed(42)
        provenance = roll_provenance()
        self.assertIsInstance(provenance, Provenance)
        self.assertIsInstance(provenance.main_roll, int)
        self.assertIn(provenance.social_class, ["Nobility", "Merchant", "Commoner"])

    def test_provenance_str_representation(self):
        """Test string representation of provenance."""
        provenance = Provenance(
            main_roll=5,
            sub_roll=50,
            craft_roll=None,
            social_class="Nobility",
            sub_class="Baron",
            craft_type=None
        )
        result = str(provenance)
        self.assertIn("Nobility", result)
        self.assertIn("Baron", result)

    def test_provenance_crafts_has_craft_type(self):
        """Test that Crafts commoners have a craft type."""
        for seed in range(200):
            random.seed(seed)
            provenance = roll_provenance()
            if provenance.social_class == "Commoner" and provenance.sub_class == "Crafts":
                self.assertIsNotNone(provenance.craft_type)
                self.assertIn(provenance.craft_type, [
                    "Smith/Builder/Wainwright",
                    "Medical/Herb Lore/Maker",
                    "Magic"
                ])
                break

    def test_provenance_main_roll_determines_class(self):
        """Test that main roll correctly determines social class."""
        for seed in range(100):
            random.seed(seed)
            provenance = roll_provenance()

            if provenance.main_roll <= 10:
                self.assertEqual(provenance.social_class, "Nobility")
            elif provenance.main_roll <= 30:
                self.assertEqual(provenance.social_class, "Merchant")
            else:
                self.assertEqual(provenance.social_class, "Commoner")

    def test_provenance_nobility_has_sub_roll(self):
        """Test that nobility always has a sub_roll."""
        for seed in range(200):
            random.seed(seed)
            provenance = roll_provenance()
            if provenance.social_class == "Nobility":
                self.assertIsNotNone(provenance.sub_roll)
                break


class TestLocation(unittest.TestCase):
    """Test location generation."""

    def test_roll_location_returns_location(self):
        """Test that roll_location returns a Location object."""
        random.seed(42)
        location = roll_location()
        self.assertIsInstance(location, Location)
        self.assertIsInstance(location.roll, int)
        self.assertIsInstance(location.location_type, str)
        self.assertIsInstance(location.skills, list)
        self.assertIsInstance(location.attribute_modifiers, dict)

    def test_city_location(self):
        """Test city location properties."""
        for seed in range(100):
            random.seed(seed)
            location = roll_location()
            if location.roll <= 20:
                self.assertEqual(location.location_type, "City")
                self.assertEqual(location.skills, ["Street Smarts"])
                self.assertEqual(location.attribute_modifiers, {"CON": -1, "INT": 1})
                self.assertEqual(location.literacy_check_modifier, 0)
                break

    def test_village_location(self):
        """Test village location properties."""
        for seed in range(100):
            random.seed(seed)
            location = roll_location()
            if 21 <= location.roll <= 70:
                self.assertEqual(location.location_type, "Village")
                self.assertEqual(len(location.skills), 1)
                self.assertIn(location.skills[0], ["Street Smarts", "Survival"])
                self.assertEqual(len(location.attribute_modifiers), 1)
                bonus_attr = list(location.attribute_modifiers.keys())[0]
                self.assertIn(bonus_attr, ["INT", "WIS", "STR", "DEX"])
                self.assertEqual(location.attribute_modifiers[bonus_attr], 1)
                self.assertEqual(location.literacy_check_modifier, 2)
                break

    def test_rural_location(self):
        """Test rural location properties."""
        for seed in range(100):
            random.seed(seed)
            location = roll_location()
            if 71 <= location.roll <= 99:
                self.assertEqual(location.location_type, "Rural")
                self.assertEqual(len(location.skills), 2)
                for skill in location.skills:
                    self.assertIn(skill, SURVIVAL_SKILLS)
                self.assertEqual(location.attribute_modifiers, {"STR": 1, "DEX": 1})
                self.assertEqual(location.literacy_check_modifier, 4)
                break

    def test_special_location(self):
        """Test special (off-lander) location."""
        # Create a location manually with roll 100
        location = Location(
            roll=100,
            location_type="Special (Off-lander)",
            skills=[],
            skill_roll=None,
            attribute_modifiers={},
            attribute_roll=None,
            skill_rolls=None,
            literacy_check_modifier=0
        )
        self.assertEqual(location.location_type, "Special (Off-lander)")
        self.assertEqual(location.skills, [])

    def test_location_str_representation(self):
        """Test string representation of location."""
        location = Location(
            roll=15,
            location_type="City",
            skills=["Street Smarts"],
            skill_roll=None,
            attribute_modifiers={"CON": -1, "INT": 1},
            attribute_roll=None,
            skill_rolls=None,
            literacy_check_modifier=0
        )
        result = str(location)
        self.assertIn("City", result)
        self.assertIn("Street Smarts", result)
        self.assertIn("-1 CON", result)
        self.assertIn("+1 INT", result)

    def test_village_has_skill_and_attribute_rolls(self):
        """Test that Village location has skill and attribute rolls."""
        for seed in range(100):
            random.seed(seed)
            location = roll_location()
            if location.location_type == "Village":
                self.assertIsNotNone(location.skill_roll)
                self.assertIn(location.skill_roll, range(1, 7))
                self.assertIsNotNone(location.attribute_roll)
                self.assertIn(location.attribute_roll, range(1, 5))
                break

    def test_rural_has_skill_rolls(self):
        """Test that Rural location has skill rolls."""
        for seed in range(100):
            random.seed(seed)
            location = roll_location()
            if location.location_type == "Rural":
                self.assertIsNotNone(location.skill_rolls)
                self.assertEqual(len(location.skill_rolls), 2)
                for roll in location.skill_rolls:
                    self.assertIn(roll, range(1, 6))  # d5 (1-5)
                break

    def test_location_roll_determines_type(self):
        """Test that roll correctly determines location type."""
        for seed in range(100):
            random.seed(seed)
            location = roll_location()

            if location.roll <= 20:
                self.assertEqual(location.location_type, "City")
            elif location.roll <= 70:
                self.assertEqual(location.location_type, "Village")
            elif location.roll <= 99:
                self.assertEqual(location.location_type, "Rural")
            else:
                self.assertEqual(location.location_type, "Special (Off-lander)")


class TestLiteracyCheck(unittest.TestCase):
    """Test literacy check generation using 3d6 roll-under."""

    def test_roll_literacy_check_returns_literacy_check(self):
        """Test that roll_literacy_check returns a LiteracyCheck object."""
        random.seed(42)
        literacy = roll_literacy_check(10)
        self.assertIsInstance(literacy, LiteracyCheck)
        self.assertIsInstance(literacy.roll, int)
        self.assertIsInstance(literacy.int_value, int)
        self.assertIsInstance(literacy.is_literate, bool)

    def test_literacy_check_roll_range(self):
        """Test that roll is in 3d6 range (3-18)."""
        for seed in range(50):
            random.seed(seed)
            literacy = roll_literacy_check(10)
            self.assertGreaterEqual(literacy.roll, 3)
            self.assertLessEqual(literacy.roll, 18)

    def test_literacy_check_target_calculation(self):
        """Test that target is INT - difficulty_modifier."""
        random.seed(42)
        # INT 10, no modifier: target = 10
        literacy = roll_literacy_check(10, difficulty_modifier=0)
        self.assertEqual(literacy.target, 10)

        # INT 10, +4 modifier (Rural): target = 6
        random.seed(42)
        literacy = roll_literacy_check(10, difficulty_modifier=4)
        self.assertEqual(literacy.target, 6)

        # INT 14, +2 modifier (Village): target = 12
        random.seed(42)
        literacy = roll_literacy_check(14, difficulty_modifier=2)
        self.assertEqual(literacy.target, 12)

    def test_literacy_check_pass_fail(self):
        """Test that pass/fail is correctly determined (roll < target = pass)."""
        # Roll must be LESS THAN target to pass
        # High INT, no difficulty = easy to pass
        for seed in range(100):
            random.seed(seed)
            literacy = roll_literacy_check(18, difficulty_modifier=0)
            # Target is 18, roll 3-17 passes, roll 18 fails
            if literacy.roll < 18:
                self.assertTrue(literacy.is_literate)
            else:
                self.assertFalse(literacy.is_literate)

        # Low INT + high difficulty = hard to pass
        for seed in range(100):
            random.seed(seed)
            literacy = roll_literacy_check(6, difficulty_modifier=4)
            # Target is 2, impossible to pass (min roll is 3)
            self.assertFalse(literacy.is_literate)

    def test_literacy_check_str_representation(self):
        """Test string representation of literacy check."""
        literacy = LiteracyCheck(
            roll=5,
            int_value=10,
            difficulty_modifier=4,
            target=6,
            is_literate=False
        )
        result = str(literacy)
        self.assertIn("Illiterate", result)
        self.assertIn("5", result)  # roll
        self.assertIn("10", result)  # INT value
        self.assertIn("6", result)  # target

    def test_literacy_str_representation_literate(self):
        """Test string representation when literate."""
        literacy = LiteracyCheck(
            roll=5,
            int_value=12,
            difficulty_modifier=0,
            target=12,
            is_literate=True
        )
        result = str(literacy)
        self.assertIn("Literate", result)


class TestSkillTrack(unittest.TestCase):
    """Test skill track selection and acceptance checks."""

    def test_track_type_enum(self):
        """Test TrackType enum values."""
        self.assertEqual(TrackType.ARMY.value, "Army")
        self.assertEqual(TrackType.NAVY.value, "Navy")
        self.assertEqual(TrackType.RANGER.value, "Ranger")
        self.assertEqual(TrackType.OFFICER.value, "Officer")
        self.assertEqual(TrackType.RANDOM.value, "Random")
        self.assertEqual(TrackType.WORKER.value, "Worker")
        self.assertEqual(TrackType.CRAFTS.value, "Crafts")
        self.assertEqual(TrackType.MERCHANT.value, "Merchant")
        self.assertEqual(TrackType.MAGIC.value, "Magic")

    def test_craft_type_enum(self):
        """Test CraftType enum values."""
        self.assertEqual(CraftType.SMITH.value, "Smith")
        self.assertEqual(CraftType.AGRICULTURE.value, "Agriculture")
        self.assertEqual(CraftType.MEDICAL.value, "Medical")
        self.assertEqual(CraftType.MAGIC.value, "Magic")

    def test_track_survivability_values(self):
        """Test survivability values are correct."""
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.ARMY], 5)
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.NAVY], 5)
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.RANGER], 6)
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.OFFICER], 5)
        self.assertIsNone(TRACK_SURVIVABILITY[TrackType.RANDOM])  # Rolled
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.WORKER], 4)
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.CRAFTS], 3)
        self.assertEqual(TRACK_SURVIVABILITY[TrackType.MERCHANT], 3)

    def test_track_initial_skills(self):
        """Test initial skills are defined for each track."""
        self.assertIn("Sword +1 to hit", TRACK_INITIAL_SKILLS[TrackType.ARMY])
        self.assertIn("Swimming", TRACK_INITIAL_SKILLS[TrackType.NAVY])
        self.assertIn("Tracking", TRACK_INITIAL_SKILLS[TrackType.RANGER])
        self.assertIn("Morale", TRACK_INITIAL_SKILLS[TrackType.OFFICER])
        self.assertIn("Laborer", TRACK_INITIAL_SKILLS[TrackType.WORKER])
        self.assertIn("Literacy", TRACK_INITIAL_SKILLS[TrackType.CRAFTS])
        self.assertIn("Coins", TRACK_INITIAL_SKILLS[TrackType.MERCHANT])

    def test_army_acceptance_with_bonuses(self):
        """Test Army acceptance with good modifiers."""
        random.seed(42)
        # With +2 STR and +2 DEX, should pass most of the time
        check = check_army_acceptance(str_mod=2, dex_mod=2)
        self.assertIsInstance(check, AcceptanceCheck)
        self.assertEqual(check.track, TrackType.ARMY)
        self.assertEqual(check.target, 8)
        self.assertIsNotNone(check.roll)

    def test_army_acceptance_with_penalties(self):
        """Test Army acceptance with negative modifiers."""
        # With -5 STR and -5 DEX, very unlikely to pass
        failed_count = 0
        for seed in range(50):
            random.seed(seed)
            check = check_army_acceptance(str_mod=-5, dex_mod=-5)
            if not check.accepted:
                failed_count += 1
        # Most should fail
        self.assertGreater(failed_count, 40)

    def test_navy_acceptance(self):
        """Test Navy acceptance check."""
        random.seed(42)
        check = check_navy_acceptance(str_mod=1, dex_mod=1, int_mod=1)
        self.assertEqual(check.track, TrackType.NAVY)
        self.assertEqual(check.target, 8)
        self.assertIn("INT", check.modifiers)

    def test_ranger_acceptance_requires_both_bonuses(self):
        """Test Ranger requires both physical and mental bonuses."""
        # Has both - should pass
        check = check_ranger_acceptance(str_mod=1, dex_mod=0, int_mod=0, wis_mod=1)
        self.assertTrue(check.accepted)

        # Only physical - should fail
        check = check_ranger_acceptance(str_mod=1, dex_mod=1, int_mod=0, wis_mod=0)
        self.assertFalse(check.accepted)

        # Only mental - should fail
        check = check_ranger_acceptance(str_mod=0, dex_mod=0, int_mod=1, wis_mod=1)
        self.assertFalse(check.accepted)

        # Neither - should fail
        check = check_ranger_acceptance(str_mod=0, dex_mod=0, int_mod=0, wis_mod=0)
        self.assertFalse(check.accepted)

    def test_officer_acceptance_rich(self):
        """Test Officer acceptance for Rich characters."""
        check = check_officer_acceptance(is_rich=True, is_promoted=False)
        self.assertTrue(check.accepted)
        self.assertIn("Rich", check.reason)

    def test_officer_acceptance_promoted(self):
        """Test Officer acceptance for promoted characters."""
        check = check_officer_acceptance(is_rich=False, is_promoted=True)
        self.assertTrue(check.accepted)
        self.assertIn("Promoted", check.reason)

    def test_officer_acceptance_neither(self):
        """Test Officer rejection when neither Rich nor promoted."""
        check = check_officer_acceptance(is_rich=False, is_promoted=False)
        self.assertFalse(check.accepted)

    def test_merchant_acceptance_poor(self):
        """Test Merchant acceptance for poor (Subsistence) characters."""
        random.seed(42)
        check = check_merchant_acceptance(social_class="Commoner", wealth_level="Subsistence")
        self.assertEqual(check.target, 10)
        self.assertIn("poor", check.reason)

    def test_merchant_acceptance_working_class(self):
        """Test Merchant acceptance for working class characters."""
        random.seed(42)
        check = check_merchant_acceptance(social_class="Commoner", wealth_level="Moderate")
        self.assertEqual(check.target, 8)
        self.assertIn("working class", check.reason)

    def test_merchant_acceptance_above_working_class(self):
        """Test Merchant acceptance for above working class."""
        random.seed(42)
        check = check_merchant_acceptance(social_class="Nobility", wealth_level="Merchant")
        self.assertEqual(check.target, 6)
        self.assertIn("above working class", check.reason)

    def test_get_eligible_tracks_always_includes_basics(self):
        """Test that Random, Worker, and Crafts are always eligible."""
        eligible = get_eligible_tracks(
            str_mod=0, dex_mod=0, int_mod=0, wis_mod=0,
            social_class="Commoner", wealth_level="Moderate"
        )
        eligible_types = {t for t, _ in eligible}
        self.assertIn(TrackType.RANDOM, eligible_types)
        self.assertIn(TrackType.WORKER, eligible_types)
        self.assertIn(TrackType.CRAFTS, eligible_types)

    def test_select_optimal_track_prioritizes_officer_for_rich(self):
        """Test that Officer is selected for Rich characters."""
        track, check = select_optimal_track(
            str_mod=2, dex_mod=2, int_mod=2, wis_mod=2,
            social_class="Nobility", wealth_level="Rich", sub_class="Baron"
        )
        self.assertEqual(track, TrackType.OFFICER)

    def test_select_optimal_track_prioritizes_ranger(self):
        """Test that Ranger is prioritized when eligible (and not Officer)."""
        track, check = select_optimal_track(
            str_mod=2, dex_mod=0, int_mod=2, wis_mod=0,
            social_class="Commoner", wealth_level="Moderate", sub_class="Laborer"
        )
        self.assertEqual(track, TrackType.RANGER)

    def test_roll_survivability_random_never_returns_5(self):
        """Test that Random track survivability never returns 5."""
        for seed in range(100):
            random.seed(seed)
            survivability, roll = roll_survivability_random()
            self.assertNotEqual(survivability, 5)
            self.assertIn(survivability, [1, 2, 3, 4, 6, 7, 8])

    def test_roll_craft_type_returns_valid_craft(self):
        """Test that roll_craft_type returns a valid CraftType."""
        for seed in range(50):
            random.seed(seed)
            craft, rolls = roll_craft_type()
            self.assertIsInstance(craft, CraftType)
            self.assertIsInstance(rolls, list)
            self.assertGreaterEqual(len(rolls), 1)

    def test_roll_craft_type_main_rolls(self):
        """Test craft type main roll mappings."""
        # Test each main roll value
        crafts_found = set()
        for seed in range(200):
            random.seed(seed)
            craft, rolls = roll_craft_type()
            crafts_found.add(craft)

        # Should find at least the basic crafts
        self.assertIn(CraftType.SMITH, crafts_found)
        self.assertIn(CraftType.AGRICULTURE, crafts_found)
        self.assertIn(CraftType.TAILOR, crafts_found)
        self.assertIn(CraftType.MEDICAL, crafts_found)
        self.assertIn(CraftType.MAGIC, crafts_found)

    def test_roll_skill_track_returns_skill_track(self):
        """Test that roll_skill_track returns a SkillTrack object."""
        random.seed(42)
        track = roll_skill_track(
            str_mod=0, dex_mod=0, int_mod=0, wis_mod=0,
            social_class="Commoner", sub_class="Laborer",
            wealth_level="Moderate"
        )
        self.assertIsInstance(track, SkillTrack)
        self.assertIsInstance(track.track, TrackType)
        self.assertIsInstance(track.survivability, int)
        self.assertIsInstance(track.initial_skills, list)

    def test_roll_skill_track_crafts_has_craft_type(self):
        """Test that Crafts track includes craft type."""
        for seed in range(100):
            random.seed(seed)
            track = roll_skill_track(
                str_mod=-5, dex_mod=-5, int_mod=-5, wis_mod=-5,
                social_class="Commoner", sub_class="Crafts",
                wealth_level="Subsistence",
                optimize=False  # Random selection
            )
            if track.track == TrackType.CRAFTS:
                self.assertIsNotNone(track.craft_type)
                self.assertIsNotNone(track.craft_rolls)
                break

    def test_roll_skill_track_worker_bonus_for_poor(self):
        """Test Worker track gives bonus Laborer for poor characters."""
        for seed in range(100):
            random.seed(seed)
            track = roll_skill_track(
                str_mod=-5, dex_mod=-5, int_mod=-5, wis_mod=-5,
                social_class="Commoner", sub_class="Laborer",
                wealth_level="Subsistence",
                optimize=False
            )
            if track.track == TrackType.WORKER:
                self.assertIn("Laborer (bonus)", track.initial_skills)
                break

    def test_skill_track_str_representation(self):
        """Test string representation of SkillTrack."""
        track = SkillTrack(
            track=TrackType.ARMY,
            acceptance_check=AcceptanceCheck(
                track=TrackType.ARMY, accepted=True, roll=9,
                target=8, modifiers={"STR": 1, "DEX": 1},
                reason="Total 11 ≥ 8"
            ),
            survivability=5,
            survivability_roll=None,
            initial_skills=["Sword +1 to hit", "Sword +1 parry"],
            craft_type=None,
            craft_rolls=None
        )
        result = str(track)
        self.assertIn("Army", result)
        self.assertIn("Survivability: 5", result)
        self.assertIn("Sword", result)

    def test_acceptance_check_str_with_roll(self):
        """Test AcceptanceCheck string with roll."""
        check = AcceptanceCheck(
            track=TrackType.ARMY, accepted=True, roll=9,
            target=8, modifiers={"STR": 2, "DEX": 1},
            reason="Total 12 ≥ 8"
        )
        result = str(check)
        self.assertIn("Army", result)
        self.assertIn("Accepted", result)
        self.assertIn("9", result)

    def test_acceptance_check_str_without_roll(self):
        """Test AcceptanceCheck string without roll."""
        check = AcceptanceCheck(
            track=TrackType.OFFICER, accepted=True, roll=None,
            target=None, modifiers={},
            reason="Rich wealth level"
        )
        result = str(check)
        self.assertIn("Officer", result)
        self.assertIn("Rich", result)


class TestPriorExperience(unittest.TestCase):
    """Test prior experience generation."""

    def test_track_yearly_skills_defined(self):
        """Test that yearly skills are defined for all tracks."""
        for track in TrackType:
            self.assertIn(track, TRACK_YEARLY_SKILLS)
            self.assertGreater(len(TRACK_YEARLY_SKILLS[track]), 0)

    def test_roll_yearly_skill_returns_skill(self):
        """Test that roll_yearly_skill returns a valid skill."""
        random.seed(42)
        skill, roll = roll_yearly_skill(TrackType.ARMY, 0)
        self.assertIsInstance(skill, str)
        self.assertIn(skill, TRACK_YEARLY_SKILLS[TrackType.ARMY])
        self.assertGreaterEqual(roll, 1)
        self.assertLessEqual(roll, 12)

    def test_roll_survivability_check_range(self):
        """Test survivability check roll range (3d6 = 3-18)."""
        for seed in range(50):
            random.seed(seed)
            roll, total, survived = roll_survivability_check(5)
            self.assertGreaterEqual(roll, 3)
            self.assertLessEqual(roll, 18)
            # With no modifier, total should equal roll
            self.assertEqual(roll, total)

    def test_roll_survivability_check_with_modifier(self):
        """Test survivability check with attribute modifiers."""
        random.seed(42)
        # Positive modifier
        roll, total, survived = roll_survivability_check(10, total_modifier=5)
        self.assertEqual(total, roll + 5)

        # Negative modifier
        random.seed(42)
        roll2, total2, survived2 = roll_survivability_check(10, total_modifier=-3)
        self.assertEqual(total2, roll2 - 3)

    def test_roll_survivability_check_pass_fail(self):
        """Test survivability check pass/fail logic."""
        # With target 3, should always pass (3d6 >= 3)
        passed_count = 0
        for seed in range(100):
            random.seed(seed)
            roll, total, survived = roll_survivability_check(3)
            if survived:
                passed_count += 1
        self.assertEqual(passed_count, 100)  # All should pass

        # With target 18, should rarely pass (need exactly 18)
        passed_count = 0
        for seed in range(100):
            random.seed(seed)
            roll, total, survived = roll_survivability_check(18)
            if survived:
                passed_count += 1
        self.assertLess(passed_count, 10)  # Very few should pass

    def test_roll_prior_experience_returns_prior_experience(self):
        """Test that roll_prior_experience returns a PriorExperience object."""
        random.seed(42)
        skill_track = SkillTrack(
            track=TrackType.ARMY,
            acceptance_check=None,
            survivability=5,
            survivability_roll=None,
            initial_skills=["Sword +1 to hit", "Sword +1 parry"],
            craft_type=None,
            craft_rolls=None
        )
        experience = roll_prior_experience(skill_track, years=5)
        self.assertIsInstance(experience, PriorExperience)
        self.assertEqual(experience.starting_age, 16)
        self.assertEqual(experience.track, TrackType.ARMY)

    def test_prior_experience_skill_points_match_years(self):
        """Test that skill points equal years served (if survived)."""
        random.seed(42)
        skill_track = SkillTrack(
            track=TrackType.CRAFTS,  # Low survivability = 3, easy to survive
            acceptance_check=None,
            survivability=3,
            survivability_roll=None,
            initial_skills=["Laborer"],
            craft_type=None,
            craft_rolls=None
        )
        experience = roll_prior_experience(skill_track, years=5)
        if not experience.died:
            self.assertEqual(experience.total_skill_points, experience.years_served)

    def test_prior_experience_includes_initial_skills(self):
        """Test that initial skills from track are included."""
        random.seed(42)
        initial_skills = ["Sword +1 to hit", "Sword +1 parry"]
        skill_track = SkillTrack(
            track=TrackType.ARMY,
            acceptance_check=None,
            survivability=3,
            survivability_roll=None,
            initial_skills=initial_skills,
            craft_type=None,
            craft_rolls=None
        )
        experience = roll_prior_experience(skill_track, years=1)
        for skill in initial_skills:
            self.assertIn(skill, experience.all_skills)

    def test_prior_experience_death_stops_progression(self):
        """Test that death stops further year progression."""
        # Use high survivability to increase death chance
        for seed in range(200):
            random.seed(seed)
            skill_track = SkillTrack(
                track=TrackType.RANGER,  # Survivability 6
                acceptance_check=None,
                survivability=6,
                survivability_roll=None,
                initial_skills=[],
                craft_type=None,
                craft_rolls=None
            )
            experience = roll_prior_experience(skill_track, years=18)
            if experience.died:
                # Years served should be less than max
                self.assertLess(experience.years_served, 18)
                self.assertIsNotNone(experience.death_year)
                # Last year result should show death
                self.assertFalse(experience.yearly_results[-1].survived)
                break

    def test_prior_experience_zero_years(self):
        """Test prior experience with zero years."""
        random.seed(42)
        skill_track = SkillTrack(
            track=TrackType.MERCHANT,
            acceptance_check=None,
            survivability=3,
            survivability_roll=None,
            initial_skills=["Coins", "Literacy"],
            craft_type=None,
            craft_rolls=None
        )
        experience = roll_prior_experience(skill_track, years=0)
        self.assertEqual(experience.years_served, 0)
        self.assertEqual(experience.total_skill_points, 0)
        self.assertEqual(len(experience.yearly_results), 0)
        # Should still have initial skills
        self.assertEqual(experience.all_skills, ["Coins", "Literacy"])

    def test_prior_experience_age_calculation(self):
        """Test that final age is calculated correctly."""
        random.seed(42)
        skill_track = SkillTrack(
            track=TrackType.CRAFTS,
            acceptance_check=None,
            survivability=3,
            survivability_roll=None,
            initial_skills=[],
            craft_type=None,
            craft_rolls=None
        )
        experience = roll_prior_experience(skill_track, years=10)
        if not experience.died:
            self.assertEqual(experience.final_age, 16 + 10)  # 26

    def test_prior_experience_random_years(self):
        """Test that years=-1 gives random years (0-18)."""
        skill_track = SkillTrack(
            track=TrackType.CRAFTS,
            acceptance_check=None,
            survivability=3,
            survivability_roll=None,
            initial_skills=[],
            craft_type=None,
            craft_rolls=None
        )
        years_seen = set()
        for seed in range(200):
            random.seed(seed)
            experience = roll_prior_experience(skill_track, years=-1)
            if not experience.died:
                years_seen.add(experience.years_served)
        # Should see variety of years
        self.assertGreater(len(years_seen), 5)

    def test_prior_experience_clamps_years(self):
        """Test that years are clamped to 0-18 range."""
        skill_track = SkillTrack(
            track=TrackType.CRAFTS,
            acceptance_check=None,
            survivability=3,
            survivability_roll=None,
            initial_skills=[],
            craft_type=None,
            craft_rolls=None
        )
        # Test negative (not -1) gets clamped to 0
        random.seed(42)
        experience = roll_prior_experience(skill_track, years=-5)
        self.assertEqual(experience.years_served, 0)

        # Test over 18 gets clamped to 18
        random.seed(42)
        experience = roll_prior_experience(skill_track, years=25)
        # May die before 18, but target was 18
        self.assertLessEqual(experience.years_served, 18)

    def test_year_result_str_representation(self):
        """Test YearResult string representation."""
        result = YearResult(
            year=20,
            track=TrackType.ARMY,
            skill_gained="Tactics",
            skill_roll=4,
            skill_points=1,
            survivability_target=5,
            survivability_roll=8,
            survivability_modifier=2,
            survivability_total=10,
            survived=True
        )
        result_str = str(result)
        self.assertIn("Year 20", result_str)
        self.assertIn("Tactics", result_str)
        self.assertIn("Survived", result_str)
        self.assertIn("+2", result_str)  # Modifier should be shown
        self.assertIn("=10", result_str)  # Total should be shown

    def test_year_result_str_death(self):
        """Test YearResult string representation on death."""
        result = YearResult(
            year=22,
            track=TrackType.RANGER,
            skill_gained="Tracking",
            skill_roll=3,
            skill_points=1,
            survivability_target=6,
            survivability_roll=4,
            survivability_modifier=-2,
            survivability_total=2,
            survived=False
        )
        result_str = str(result)
        self.assertIn("DIED", result_str)
        self.assertIn("-2", result_str)  # Negative modifier

    def test_prior_experience_str_representation(self):
        """Test PriorExperience string representation."""
        experience = PriorExperience(
            starting_age=16,
            final_age=20,
            years_served=4,
            track=TrackType.NAVY,
            survivability_target=6,
            yearly_results=[],
            total_skill_points=4,
            all_skills=["Swimming", "Sailing", "Navigation", "Rope Use"],
            died=False,
            death_year=None,
            attribute_scores={"STR": 12, "DEX": 14, "INT": 10, "WIS": 11, "CON": 13, "CHR": 9},
            attribute_modifiers={"STR": 0, "DEX": 1, "INT": 0, "WIS": 0, "CON": 0, "CHR": 0}
        )
        result_str = str(experience)
        self.assertIn("Navy", result_str)
        self.assertIn("TOTAL SKILL POINTS: 4", result_str)
        self.assertIn("Swimming", result_str)
        self.assertIn("Survivability Target: 6+", result_str)
        self.assertIn("STR:12", result_str)
        self.assertIn("DEX:14(+1)", result_str)

    def test_prior_experience_str_on_death(self):
        """Test PriorExperience string shows death."""
        experience = PriorExperience(
            starting_age=16,
            final_age=19,
            years_served=3,
            track=TrackType.ARMY,
            survivability_target=5,
            yearly_results=[],
            total_skill_points=3,
            all_skills=["Sword +1 to hit"],
            died=True,
            death_year=19
        )
        result_str = str(experience)
        self.assertIn("DIED", result_str)
        self.assertIn("age 19", result_str)

    def test_prior_experience_skill_counting(self):
        """Test that duplicate skills are counted correctly in output."""
        experience = PriorExperience(
            starting_age=16,
            final_age=20,
            years_served=4,
            track=TrackType.ARMY,
            survivability_target=5,
            yearly_results=[],
            total_skill_points=4,
            all_skills=["Sword +1 to hit", "Sword +1 to hit", "Shield", "Tactics"],
            died=False,
            death_year=None
        )
        result_str = str(experience)
        self.assertIn("Sword +1 to hit x2", result_str)


class TestWealth(unittest.TestCase):
    """Test wealth generation."""

    def test_wealth_level_lookup(self):
        """Test wealth level lookup from percentile roll."""
        # Subsistence: 0-15
        self.assertEqual(get_wealth_level(1), "Subsistence")
        self.assertEqual(get_wealth_level(15), "Subsistence")

        # Moderate: 16-70
        self.assertEqual(get_wealth_level(16), "Moderate")
        self.assertEqual(get_wealth_level(50), "Moderate")
        self.assertEqual(get_wealth_level(70), "Moderate")

        # Merchant: 71-95
        self.assertEqual(get_wealth_level(71), "Merchant")
        self.assertEqual(get_wealth_level(85), "Merchant")
        self.assertEqual(get_wealth_level(95), "Merchant")

        # Rich: 96-100
        self.assertEqual(get_wealth_level(96), "Rich")
        self.assertEqual(get_wealth_level(100), "Rich")

    def test_roll_wealth_returns_wealth(self):
        """Test that roll_wealth returns a Wealth object."""
        random.seed(42)
        wealth = roll_wealth()
        self.assertIsInstance(wealth, Wealth)
        self.assertIsInstance(wealth.roll, int)
        self.assertIsInstance(wealth.wealth_level, str)
        self.assertIsInstance(wealth.starting_coin, int)

    def test_wealth_roll_range(self):
        """Test that roll is in percentile range (1-100)."""
        for seed in range(50):
            random.seed(seed)
            wealth = roll_wealth()
            self.assertGreaterEqual(wealth.roll, 1)
            self.assertLessEqual(wealth.roll, 100)

    def test_subsistence_coin(self):
        """Test Subsistence wealth gives 10 coin."""
        for seed in range(200):
            random.seed(seed)
            wealth = roll_wealth()
            if wealth.wealth_level == "Subsistence":
                self.assertEqual(wealth.starting_coin, 10)
                self.assertIsNone(wealth.bonus_roll)
                break

    def test_moderate_coin(self):
        """Test Moderate wealth gives 100 coin."""
        for seed in range(200):
            random.seed(seed)
            wealth = roll_wealth()
            if wealth.wealth_level == "Moderate":
                self.assertEqual(wealth.starting_coin, 100)
                self.assertIsNone(wealth.bonus_roll)
                break

    def test_merchant_coin(self):
        """Test Merchant wealth gives 100 + percentile coin."""
        for seed in range(200):
            random.seed(seed)
            wealth = roll_wealth()
            if wealth.wealth_level == "Merchant":
                self.assertIsNotNone(wealth.bonus_roll)
                self.assertEqual(wealth.starting_coin, 100 + wealth.bonus_roll)
                self.assertGreaterEqual(wealth.starting_coin, 101)
                self.assertLessEqual(wealth.starting_coin, 200)
                break

    def test_rich_coin(self):
        """Test Rich wealth has 0 coin (consult DM)."""
        for seed in range(200):
            random.seed(seed)
            wealth = roll_wealth()
            if wealth.wealth_level == "Rich":
                self.assertEqual(wealth.starting_coin, 0)
                self.assertIsNone(wealth.bonus_roll)
                break

    def test_wealth_roll_determines_level(self):
        """Test that roll correctly determines wealth level."""
        for seed in range(100):
            random.seed(seed)
            wealth = roll_wealth()

            if wealth.roll <= 15:
                self.assertEqual(wealth.wealth_level, "Subsistence")
            elif wealth.roll <= 70:
                self.assertEqual(wealth.wealth_level, "Moderate")
            elif wealth.roll <= 95:
                self.assertEqual(wealth.wealth_level, "Merchant")
            else:
                self.assertEqual(wealth.wealth_level, "Rich")

    def test_wealth_str_representation(self):
        """Test string representation of wealth."""
        wealth = Wealth(roll=50, wealth_level="Moderate", starting_coin=100, bonus_roll=None)
        result = str(wealth)
        self.assertIn("Moderate", result)
        self.assertIn("100 coin", result)
        self.assertIn("50", result)

    def test_wealth_str_with_bonus(self):
        """Test string representation with bonus roll."""
        wealth = Wealth(roll=80, wealth_level="Merchant", starting_coin=145, bonus_roll=45)
        result = str(wealth)
        self.assertIn("Merchant", result)
        self.assertIn("145 coin", result)
        self.assertIn("bonus: 45", result)

    def test_allow_rich_false_rerolls(self):
        """Test that allow_rich=False avoids Rich result."""
        for seed in range(100):
            random.seed(seed)
            wealth = roll_wealth(allow_rich=False)
            self.assertNotEqual(wealth.wealth_level, "Rich")
            self.assertLessEqual(wealth.roll, 95)

    def test_wealth_table_has_all_ranges(self):
        """Test that WEALTH_TABLE covers all cases."""
        self.assertIn((0, 15), WEALTH_TABLE)
        self.assertIn((16, 70), WEALTH_TABLE)
        self.assertIn((71, 95), WEALTH_TABLE)
        self.assertIn((96, 100), WEALTH_TABLE)


if __name__ == '__main__':
    unittest.main()
