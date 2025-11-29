from django.test import TestCase, Client
from django.urls import reverse
from pillars.attributes import TrackType, MagicSchool


class WelcomePageTests(TestCase):
    """Tests for the welcome/landing page."""

    def setUp(self):
        self.client = Client()

    def test_welcome_page_loads(self):
        """Test that welcome page loads successfully."""
        response = self.client.get(reverse('welcome'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS')

    def test_welcome_has_generator_link(self):
        """Test that welcome page has link to character generator."""
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, 'Character Generator')
        self.assertContains(response, reverse('generator'))

    def test_welcome_has_lore_link(self):
        """Test that welcome page has link to lore."""
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, 'Lore')
        self.assertContains(response, reverse('lore'))

    def test_welcome_has_handbook_link(self):
        """Test that welcome page has link to handbook."""
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, "Player's Handbook")
        self.assertContains(response, reverse('handbook'))


class LorePageTests(TestCase):
    """Tests for the lore page."""

    def setUp(self):
        self.client = Client()

    def test_lore_page_loads(self):
        """Test that lore page loads successfully."""
        response = self.client.get(reverse('lore'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lore')

    def test_lore_has_back_link(self):
        """Test that lore page has link back to home."""
        response = self.client.get(reverse('lore'))
        self.assertContains(response, reverse('welcome'))


class HandbookPageTests(TestCase):
    """Tests for the handbook page."""

    def setUp(self):
        self.client = Client()

    def test_handbook_page_loads(self):
        """Test that handbook page loads successfully."""
        response = self.client.get(reverse('handbook'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Player's Handbook")

    def test_handbook_has_content(self):
        """Test that handbook page has markdown content."""
        response = self.client.get(reverse('handbook'))
        # Should contain some heading from the handbook
        self.assertContains(response, 'Pillars')

    def test_handbook_has_back_link(self):
        """Test that handbook page has link back to home."""
        response = self.client.get(reverse('handbook'))
        self.assertContains(response, reverse('welcome'))


class IndexViewTests(TestCase):
    """Tests for the main index view (new auto-generate flow)."""

    def setUp(self):
        self.client = Client()

    def test_index_page_loads_with_character(self):
        """Test that the index page loads with auto-generated character."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Generator')
        # Character should be auto-generated and displayed
        self.assertContains(response, 'PILLARS CHARACTER')

    def test_initial_character_has_no_skill_track_or_experience(self):
        """Test that initial character does NOT show skill track or prior experience."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # Character should have basic info
        self.assertContains(response, 'Wealth:')
        # But NOT skill track or prior experience
        self.assertNotContains(response, 'PRIOR EXPERIENCE')
        self.assertNotContains(response, 'Track)')  # Would appear as "(Ranger Track)" etc.

    def test_index_has_control_buttons(self):
        """Test that index page has the control buttons."""
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Finish Character')
        self.assertContains(response, 'Re-roll')
        self.assertContains(response, 'Add Prior Experience')

    def test_reroll_no_focus(self):
        """Test re-rolling a character with no focus."""
        # First load to get initial character
        self.client.get(reverse('index'))
        # Re-roll with no focus
        response = self.client.post(reverse('index'), {
            'action': 'reroll_none',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')

    def test_reroll_physical_focus(self):
        """Test re-rolling a character with physical focus."""
        response = self.client.post(reverse('index'), {
            'action': 'reroll_physical',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')

    def test_reroll_mental_focus(self):
        """Test re-rolling a character with mental focus."""
        response = self.client.post(reverse('index'), {
            'action': 'reroll_mental',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')

    def test_add_experience_redirects_to_track_selection(self):
        """Test that add experience redirects to track selection."""
        # First load to get character
        self.client.get(reverse('index'))
        # Add experience
        response = self.client.post(reverse('index'), {
            'action': 'add_experience',
        })
        # Should redirect to track selection first
        self.assertRedirects(response, reverse('select_track'))
        # Session should have pending character
        self.assertIn('pending_character', self.client.session)
        self.assertTrue(self.client.session.get('pending_return_to_generator', False))

    def test_finish_shows_character_sheet(self):
        """Test that finish displays the character sheet."""
        # First load to get character
        self.client.get(reverse('index'))
        # Finish
        response = self.client.post(reverse('index'), {
            'action': 'finish',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Sheet')


class SelectTrackViewTests(TestCase):
    """Tests for the track selection view (legacy - not used in new UI)."""

    def test_select_track_redirects_without_pending_character(self):
        """Test that select track redirects to index if no pending character."""
        response = self.client.get(reverse('select_track'))
        self.assertRedirects(response, reverse('index'))


class MagicTrackTests(TestCase):
    """Tests specifically for Magic track functionality."""

    def setUp(self):
        self.client = Client()

    def test_magic_track_in_availability(self):
        """Test that Magic track appears in track availability."""
        from pillars.attributes import get_track_availability

        # Character with INT bonus
        avail = get_track_availability(
            str_mod=0, dex_mod=0, int_mod=2, wis_mod=0,
            social_class='Commoner', wealth_level='Moderate'
        )

        self.assertIn(TrackType.MAGIC, avail)
        self.assertTrue(avail[TrackType.MAGIC]['available'])
        self.assertFalse(avail[TrackType.MAGIC]['impossible'])

    def test_magic_track_requires_mental_bonus(self):
        """Test that Magic track requires INT or WIS bonus."""
        from pillars.attributes import get_track_availability

        # Character without INT/WIS bonus
        avail = get_track_availability(
            str_mod=2, dex_mod=2, int_mod=0, wis_mod=0,
            social_class='Commoner', wealth_level='Moderate'
        )

        self.assertTrue(avail[TrackType.MAGIC]['impossible'])

    def test_magic_track_survivability_is_highest(self):
        """Test that Magic track has survivability 7 (highest danger)."""
        from pillars.attributes import TRACK_SURVIVABILITY

        self.assertEqual(TRACK_SURVIVABILITY[TrackType.MAGIC], 7)

    def test_magic_track_creation_has_school(self):
        """Test that creating Magic track assigns a school."""
        from pillars.attributes import create_skill_track_for_choice

        track = create_skill_track_for_choice(
            TrackType.MAGIC,
            str_mod=0, dex_mod=0, int_mod=2, wis_mod=0,
            social_class='Commoner', sub_class='Laborer',
            wealth_level='Moderate'
        )

        self.assertEqual(track.track, TrackType.MAGIC)
        self.assertIsNotNone(track.magic_school)
        self.assertIsInstance(track.magic_school, MagicSchool)
        self.assertEqual(track.survivability, 7)

    def test_magic_track_initial_skills_include_spell(self):
        """Test that Magic track initial skills include first spell."""
        from pillars.attributes import create_skill_track_for_choice

        track = create_skill_track_for_choice(
            TrackType.MAGIC,
            str_mod=0, dex_mod=0, int_mod=2, wis_mod=0,
            social_class='Commoner', sub_class='Laborer',
            wealth_level='Moderate'
        )

        # Should have at least one spell and the school
        spell_skills = [s for s in track.initial_skills if s.startswith('Spell:')]
        school_skills = [s for s in track.initial_skills if s.startswith('School:')]

        self.assertGreaterEqual(len(spell_skills), 1)
        self.assertEqual(len(school_skills), 1)

    def test_magic_yearly_skills_are_spells(self):
        """Test that Magic track yearly skills progress through spells."""
        from pillars.attributes import (
            create_skill_track_for_choice, roll_yearly_skill,
            MAGIC_SPELL_PROGRESSION
        )

        track = create_skill_track_for_choice(
            TrackType.MAGIC,
            str_mod=0, dex_mod=0, int_mod=2, wis_mod=0,
            social_class='Commoner', sub_class='Laborer',
            wealth_level='Moderate'
        )

        # Get spell for year 0
        skill, _ = roll_yearly_skill(TrackType.MAGIC, 0, track.magic_school)
        self.assertIn('Spell:', skill)

    def test_magic_school_rolls_recorded(self):
        """Test that magic school determination rolls are recorded."""
        from pillars.attributes import roll_magic_school

        school, rolls = roll_magic_school()

        self.assertIsInstance(school, MagicSchool)
        self.assertIn('percentile', rolls)
        self.assertIn('school', rolls)


class InteractiveModeMagicTests(TestCase):
    """Tests for interactive mode with tracks."""

    def setUp(self):
        self.client = Client()

    def test_interactive_mode_works(self):
        """Test that interactive mode works after track selection."""
        # First load generator to get character
        self.client.get(reverse('index'))
        # Add experience goes to track selection first
        self.client.post(reverse('index'), {'action': 'add_experience'})
        # Select a track with interactive mode
        response = self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })
        # Should redirect to interactive
        self.assertRedirects(response, reverse('interactive'))
        # Check we're set up for interactive
        self.assertIn('interactive_character', self.client.session)


class SessionSerializationTests(TestCase):
    """Tests for character serialization with Magic track."""

    def test_serialize_magic_track_character(self):
        """Test that Magic track characters serialize correctly."""
        from webapp.generator.views import serialize_character, deserialize_character
        from pillars import generate_character
        from pillars.attributes import create_skill_track_for_choice, TrackType

        # Create a character with Magic track
        char = generate_character(years=0)

        # Manually set magic track if character is eligible
        int_mod = char.attributes.get_modifier('INT')
        wis_mod = char.attributes.get_modifier('WIS')

        if int_mod > 0 or wis_mod > 0:
            char.skill_track = create_skill_track_for_choice(
                TrackType.MAGIC,
                str_mod=char.attributes.get_modifier('STR'),
                dex_mod=char.attributes.get_modifier('DEX'),
                int_mod=int_mod,
                wis_mod=wis_mod,
                social_class=char.provenance.social_class,
                sub_class=char.provenance.sub_class,
                wealth_level=char.wealth.wealth_level
            )

            # Serialize and deserialize
            data = serialize_character(char)
            restored = deserialize_character(data)

            self.assertEqual(restored.skill_track.track, TrackType.MAGIC)
            self.assertIsNotNone(restored.skill_track.magic_school)


class StartOverTests(TestCase):
    """Tests for the start over functionality."""

    def setUp(self):
        self.client = Client()

    def test_start_over_clears_session(self):
        """Test that start over clears all session data."""
        # First create some session data by loading generator and going through flow
        self.client.get(reverse('index'))
        # Add experience goes to track selection now
        self.client.post(reverse('index'), {'action': 'add_experience'})
        # Select a track to get to interactive mode
        self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })

        # Verify session has data
        self.assertIn('interactive_character', self.client.session)

        # Start over
        response = self.client.get(reverse('start_over'))
        self.assertRedirects(response, reverse('welcome'))

        # Session should be cleared
        self.assertNotIn('interactive_character', self.client.session)


class UIFlowTests(TestCase):
    """End-to-end UI flow tests for the character generator (new flow)."""

    def setUp(self):
        self.client = Client()

    def test_full_generator_flow(self):
        """Test complete character generation flow with new UI."""
        # Step 1: Load index page - character auto-generated
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Generator')
        self.assertContains(response, 'PILLARS CHARACTER')

        # Step 2: Finish the character
        response = self.client.post(reverse('index'), {
            'action': 'finish',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Sheet')

    def test_full_interactive_mode_flow(self):
        """Test complete interactive mode flow with year-by-year progression."""
        # Step 1: Load generator and add experience
        self.client.get(reverse('index'))
        response = self.client.post(reverse('index'), {
            'action': 'add_experience',
        })
        # Should go to track selection first
        self.assertRedirects(response, reverse('select_track'))

        # Step 2: Select a track with interactive mode
        response = self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })
        # Should redirect to interactive mode
        self.assertRedirects(response, reverse('interactive'))

        # Step 3: Continue for first year
        response = self.client.post(reverse('interactive'), {
            'action': 'continue',
        })
        self.assertEqual(response.status_code, 200)
        # Should show year 1 results
        self.assertContains(response, 'Years of Experience')

        # Step 4: Stop and return to generator
        response = self.client.post(reverse('interactive'), {
            'action': 'stop',
        })
        # Should redirect back to generator
        self.assertRedirects(response, reverse('generator'))

        # Step 5: Generator should show experience info
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prior Experience')

    def test_reroll_flow(self):
        """Test re-rolling characters with different focuses."""
        # Load initial character
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'PILLARS CHARACTER')

        # Re-roll with physical focus
        response = self.client.post(reverse('index'), {
            'action': 'reroll_physical',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')

        # Re-roll with mental focus
        response = self.client.post(reverse('index'), {
            'action': 'reroll_mental',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')

    def test_start_over_from_interactive(self):
        """Test start over button from interactive mode."""
        # Load generator and go through track selection to interactive mode
        self.client.get(reverse('index'))
        self.client.post(reverse('index'), {'action': 'add_experience'})
        self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })

        # Continue a few years
        self.client.post(reverse('interactive'), {'action': 'continue'})
        self.client.post(reverse('interactive'), {'action': 'continue'})

        # Verify we have session data
        self.assertIn('interactive_character', self.client.session)
        self.assertGreater(self.client.session.get('interactive_years', 0), 0)

        # Start over
        response = self.client.get(reverse('start_over'))
        self.assertRedirects(response, reverse('welcome'))

        # Session should be cleared
        self.assertNotIn('interactive_character', self.client.session)

    def test_finish_after_experience(self):
        """Test finishing a character after adding experience."""
        # Load generator and go through track selection
        self.client.get(reverse('index'))
        self.client.post(reverse('index'), {'action': 'add_experience'})
        self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })

        # Add one year
        self.client.post(reverse('interactive'), {'action': 'continue'})

        # Return to generator
        self.client.post(reverse('interactive'), {'action': 'stop'})

        # Finish the character
        response = self.client.post(reverse('generator'), {
            'action': 'finish',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Sheet')


class AttributeFocusTests(TestCase):
    """Tests for the attribute focus feature."""

    def setUp(self):
        self.client = Client()

    def test_physical_focus_generates_str_or_dex_bonus(self):
        """Test that physical focus ensures STR or DEX +1."""
        from pillars.generator import generate_character

        # Generate 10 characters with physical focus
        for _ in range(10):
            char = generate_character(years=0, attribute_focus='physical')
            str_mod = char.attributes.get_modifier("STR")
            dex_mod = char.attributes.get_modifier("DEX")
            self.assertTrue(
                str_mod >= 1 or dex_mod >= 1,
                f"Physical focus should have STR({str_mod}) or DEX({dex_mod}) >= 1"
            )

    def test_mental_focus_generates_int_or_wis_bonus(self):
        """Test that mental focus ensures INT or WIS +1."""
        from pillars.generator import generate_character

        # Generate 10 characters with mental focus
        for _ in range(10):
            char = generate_character(years=0, attribute_focus='mental')
            int_mod = char.attributes.get_modifier("INT")
            wis_mod = char.attributes.get_modifier("WIS")
            self.assertTrue(
                int_mod >= 1 or wis_mod >= 1,
                f"Mental focus should have INT({int_mod}) or WIS({wis_mod}) >= 1"
            )

    def test_no_focus_generates_any_character(self):
        """Test that no focus doesn't restrict attributes."""
        from pillars.generator import generate_character

        # Just make sure it generates without error
        char = generate_character(years=0, attribute_focus=None)
        self.assertIsNotNone(char.attributes)

    def test_reroll_buttons_available(self):
        """Test that re-roll buttons with different focuses are available."""
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'reroll_none')
        self.assertContains(response, 'reroll_physical')
        self.assertContains(response, 'reroll_mental')

    def test_physical_focus_web_generation(self):
        """Test generating a character with physical focus via web."""
        response = self.client.post(reverse('index'), {
            'action': 'reroll_physical',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')

    def test_mental_focus_web_generation(self):
        """Test generating a character with mental focus via web."""
        response = self.client.post(reverse('index'), {
            'action': 'reroll_mental',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PILLARS CHARACTER')


class MagicTrackUITests(TestCase):
    """Tests for Magic track functionality."""

    def setUp(self):
        self.client = Client()

    def test_magic_track_shows_school_info(self):
        """Test that Magic track includes school information."""
        from pillars.attributes import create_skill_track_for_choice, TrackType

        # Create a Magic track to verify it includes school info
        track = create_skill_track_for_choice(
            TrackType.MAGIC,
            str_mod=0, dex_mod=0, int_mod=2, wis_mod=0,
            social_class='Commoner', sub_class='Laborer',
            wealth_level='Moderate'
        )

        # Verify school is assigned
        self.assertIsNotNone(track.magic_school)
        # Verify initial skills include spell and school
        skill_str = ', '.join(track.initial_skills)
        self.assertIn('Spell:', skill_str)
        self.assertIn('School:', skill_str)


class ReturnToGeneratorTests(TestCase):
    """Tests for returning to generator after interactive mode."""

    def setUp(self):
        self.client = Client()

    def test_return_to_generator_after_experience(self):
        """Test that stopping interactive mode returns to generator."""
        # Load generator
        self.client.get(reverse('index'))

        # Add experience - goes to track selection
        self.client.post(reverse('index'), {'action': 'add_experience'})

        # Verify pending flag is set
        self.assertTrue(self.client.session.get('pending_return_to_generator', False))

        # Select a track to get to interactive mode
        self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })

        # Verify interactive return flag is now set
        self.assertTrue(self.client.session.get('interactive_return_to_generator', False))

        # Continue one year
        self.client.post(reverse('interactive'), {'action': 'continue'})

        # Stop - should redirect to generator
        response = self.client.post(reverse('interactive'), {'action': 'stop'})
        self.assertRedirects(response, reverse('generator'))

        # Flag should be cleared
        self.assertNotIn('interactive_return_to_generator', self.client.session)

    def test_generator_shows_experience_after_return(self):
        """Test that generator shows prior experience after returning."""
        # Load generator
        self.client.get(reverse('index'))

        # Add experience - go through track selection
        self.client.post(reverse('index'), {'action': 'add_experience'})
        self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'track_mode': 'manual',
            'interactive_mode': 'on',
            'action': 'add_experience',
        })

        # Continue one year
        self.client.post(reverse('interactive'), {'action': 'continue'})
        self.client.post(reverse('interactive'), {'action': 'stop'})

        # Load generator page
        response = self.client.get(reverse('generator'))

        # Should show prior experience section
        self.assertContains(response, 'Prior Experience')
        self.assertContains(response, 'Year')
