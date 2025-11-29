from django.test import TestCase, Client
from django.urls import reverse
from pillars.attributes import TrackType, MagicSchool


class IndexViewTests(TestCase):
    """Tests for the main index view."""

    def setUp(self):
        self.client = Client()

    def test_index_page_loads(self):
        """Test that the index page loads successfully."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pillars Character Generator')

    def test_index_has_track_selection_option(self):
        """Test that index page has track selection options."""
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'track_selection')
        self.assertContains(response, 'Choose Track')

    def test_generate_standard_character(self):
        """Test generating a character in standard mode."""
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '3',
            'track_selection': 'auto',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')

    def test_generate_interactive_mode_redirects(self):
        """Test that interactive mode sets up session correctly."""
        response = self.client.post(reverse('index'), {
            'mode': 'interactive',
            'years': '0',
            'track_selection': 'auto',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Interactive Prior Experience')
        # Check session was set up
        self.assertIn('interactive_character', self.client.session)

    def test_choose_track_redirects_to_select_track(self):
        """Test that choosing track option redirects to track selection page."""
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '3',
            'track_selection': 'choose',
            'action': 'generate',
        })
        self.assertRedirects(response, reverse('select_track'))


class SelectTrackViewTests(TestCase):
    """Tests for the track selection view."""

    def setUp(self):
        self.client = Client()
        # First generate a character to get to track selection
        self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '3',
            'track_selection': 'choose',
            'action': 'generate',
        })

    def test_select_track_page_loads(self):
        """Test that select track page loads after setup."""
        response = self.client.get(reverse('select_track'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select Skill Track')

    def test_select_track_shows_basic_tracks(self):
        """Test that basic track types are shown (always available)."""
        response = self.client.get(reverse('select_track'))
        # Check for track names that are always available
        self.assertContains(response, 'Random')
        self.assertContains(response, 'Worker')
        self.assertContains(response, 'Crafts')
        # These require rolls but should still show
        self.assertContains(response, 'Army')
        self.assertContains(response, 'Navy')
        self.assertContains(response, 'Merchant')
        # Magic may or may not show depending on character's INT/WIS

    def test_select_track_shows_magic_requirement(self):
        """Test that Magic track shows its requirement."""
        response = self.client.get(reverse('select_track'))
        self.assertContains(response, 'INT or WIS bonus')

    def test_select_worker_track(self):
        """Test selecting Worker track (always available)."""
        response = self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',  # Use enum name, not display name
            'action': 'select_track',
        })
        # Should render index with generated character (not redirect)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')


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
    """Tests for Magic track in interactive mode."""

    def setUp(self):
        self.client = Client()

    def test_interactive_mode_with_magic_track(self):
        """Test that interactive mode works with Magic track."""
        # First get to track selection with a character that can use Magic
        response = self.client.post(reverse('index'), {
            'mode': 'interactive',
            'years': '0',
            'track_selection': 'choose',
            'action': 'generate',
        })

        # Should redirect to track selection
        self.assertRedirects(response, reverse('select_track'))


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

    def test_start_over_clears_session(self):
        """Test that start over clears all session data."""
        # First create some session data
        self.client.post(reverse('index'), {
            'mode': 'interactive',
            'years': '0',
            'track_selection': 'auto',
            'action': 'generate',
        })

        # Verify session has data
        self.assertIn('interactive_character', self.client.session)

        # Start over
        response = self.client.get(reverse('start_over'))
        self.assertRedirects(response, reverse('index'))

        # Session should be cleared
        self.assertNotIn('interactive_character', self.client.session)


class UIFlowTests(TestCase):
    """End-to-end UI flow tests for the character generator."""

    def setUp(self):
        self.client = Client()

    def test_full_standard_generation_flow(self):
        """Test complete standard mode character generation flow."""
        # Step 1: Load index page
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate Character')

        # Step 2: Generate character with 5 years experience
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '5',
            'track_selection': 'auto',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')
        # Should show prior experience section
        self.assertContains(response, 'PRIOR EXPERIENCE')

    def test_full_interactive_mode_flow(self):
        """Test complete interactive mode flow with year-by-year progression."""
        # Step 1: Start interactive mode
        response = self.client.post(reverse('index'), {
            'mode': 'interactive',
            'years': '0',
            'track_selection': 'auto',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Interactive Prior Experience')
        self.assertContains(response, 'Continue Another Year')

        # Step 2: Continue for first year
        response = self.client.post(reverse('interactive'), {
            'action': 'continue',
        })
        self.assertEqual(response.status_code, 200)
        # Should show year 1 results
        self.assertContains(response, 'Years of Experience')

        # Step 3: Stop and finish
        response = self.client.post(reverse('interactive'), {
            'action': 'stop',
        })
        self.assertEqual(response.status_code, 200)
        # Should show final character
        self.assertContains(response, 'Generated Character')

    def test_track_selection_flow(self):
        """Test the track selection UI flow."""
        # Step 1: Request track selection
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '3',
            'track_selection': 'choose',
            'action': 'generate',
        })
        self.assertRedirects(response, reverse('select_track'))

        # Step 2: View track selection page
        response = self.client.get(reverse('select_track'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select Skill Track')
        self.assertContains(response, 'Available Skill Tracks')
        # Should show track cards
        self.assertContains(response, 'track-card')

        # Step 3: Select a track
        response = self.client.post(reverse('select_track'), {
            'chosen_track': 'CRAFTS',
            'action': 'select_track',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')
        self.assertContains(response, 'Crafts')

    def test_track_selection_shows_magic_track(self):
        """Test that Magic track appears in track selection when eligible."""
        # Start track selection
        self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '0',
            'track_selection': 'choose',
            'action': 'generate',
        })

        response = self.client.get(reverse('select_track'))
        self.assertEqual(response.status_code, 200)

        # Magic track should always be shown (even if impossible for this char)
        self.assertContains(response, 'Magic')
        self.assertContains(response, 'INT or WIS bonus')
        self.assertContains(response, 'Survivability:</strong> 7')

    def test_interactive_mode_with_chosen_track(self):
        """Test interactive mode after choosing a track."""
        # Step 1: Go to track selection with interactive mode
        response = self.client.post(reverse('index'), {
            'mode': 'interactive',
            'years': '0',
            'track_selection': 'choose',
            'action': 'generate',
        })
        self.assertRedirects(response, reverse('select_track'))

        # Step 2: Select Worker track
        response = self.client.post(reverse('select_track'), {
            'chosen_track': 'WORKER',
            'action': 'select_track',
        })
        self.assertEqual(response.status_code, 200)
        # Should be in interactive mode
        self.assertContains(response, 'Interactive Prior Experience')
        self.assertContains(response, 'Worker')

    def test_cancel_track_selection(self):
        """Test canceling track selection returns to index."""
        # Go to track selection
        self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '3',
            'track_selection': 'choose',
            'action': 'generate',
        })

        # Cancel
        response = self.client.post(reverse('select_track'), {
            'action': 'cancel',
        })
        self.assertRedirects(response, reverse('index'))

    def test_start_over_from_interactive(self):
        """Test start over button from interactive mode."""
        # Start interactive mode
        self.client.post(reverse('index'), {
            'mode': 'interactive',
            'years': '0',
            'track_selection': 'auto',
            'action': 'generate',
        })

        # Continue a few years
        self.client.post(reverse('interactive'), {'action': 'continue'})
        self.client.post(reverse('interactive'), {'action': 'continue'})

        # Verify we have session data
        self.assertIn('interactive_character', self.client.session)
        self.assertGreater(self.client.session.get('interactive_years', 0), 0)

        # Start over
        response = self.client.get(reverse('start_over'))
        self.assertRedirects(response, reverse('index'))

        # Session should be cleared
        self.assertNotIn('interactive_character', self.client.session)

    def test_continue_after_standard_generation(self):
        """Test continuing in interactive mode after standard generation."""
        # Generate character with 3 years
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '3',
            'track_selection': 'auto',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)

        # Should show continue option if character survived
        if 'can_continue' in response.context and response.context['can_continue']:
            self.assertContains(response, 'Continue in Interactive Mode')

            # Continue in interactive mode - this redirects to interactive page
            response = self.client.post(reverse('index'), {
                'action': 'continue_interactive',
            }, follow=True)  # Follow the redirect
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Interactive Prior Experience')

    def test_character_death_flow(self):
        """Test flow when character dies during prior experience."""
        # Generate with many years (high chance of death with high survivability)
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '18',
            'track_selection': 'auto',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')
        # Character may or may not have died, but page should load


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

    def test_index_shows_attribute_focus_option(self):
        """Test that the index page has attribute focus options."""
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Attribute Focus')
        self.assertContains(response, 'attribute_focus')
        self.assertContains(response, 'Physical (STR or DEX +1)')
        self.assertContains(response, 'Mental (INT or WIS +1)')

    def test_physical_focus_web_generation(self):
        """Test generating a character with physical focus via web."""
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '0',
            'track_selection': 'auto',
            'attribute_focus': 'physical',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')

    def test_mental_focus_web_generation(self):
        """Test generating a character with mental focus via web."""
        response = self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '0',
            'track_selection': 'auto',
            'attribute_focus': 'mental',
            'action': 'generate',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generated Character')


class MagicTrackUITests(TestCase):
    """UI tests specifically for Magic track functionality."""

    def setUp(self):
        self.client = Client()

    def test_magic_track_shows_school_info(self):
        """Test that selecting Magic track shows school information."""
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

    def test_magic_track_in_track_order(self):
        """Test that Magic track is included in the track selection order."""
        # Go to track selection
        self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '0',
            'track_selection': 'choose',
            'action': 'generate',
        })

        response = self.client.get(reverse('select_track'))

        # Magic should appear in the page
        self.assertContains(response, 'Magic')
        # Should show as a track card
        content = response.content.decode()
        self.assertIn('Magic', content)

    def test_magic_track_survivability_displayed(self):
        """Test that Magic track shows survivability 7 (most dangerous)."""
        self.client.post(reverse('index'), {
            'mode': 'standard',
            'years': '0',
            'track_selection': 'choose',
            'action': 'generate',
        })

        response = self.client.get(reverse('select_track'))
        # Should show survivability 7 for Magic
        self.assertContains(response, 'Survivability:</strong> 7')
