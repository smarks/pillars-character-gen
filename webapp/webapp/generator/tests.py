from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from pillars.attributes import TrackType, MagicSchool
from webapp.generator.models import UserProfile, SavedCharacter


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
        """Test that welcome page has link to lore/background."""
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, 'Background')
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
        self.assertContains(response, 'Background')

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
        self.assertContains(response, "Handbook")

    def test_handbook_has_content(self):
        """Test that handbook page has markdown content."""
        response = self.client.get(reverse('handbook'))
        # Should contain some heading from the handbook
        self.assertContains(response, 'Pillars')

    def test_handbook_has_back_link(self):
        """Test that handbook page has link back to home."""
        response = self.client.get(reverse('handbook'))
        self.assertContains(response, reverse('welcome'))


class CombatPageTests(TestCase):
    """Tests for the combat & movement page."""

    def setUp(self):
        self.client = Client()

    def test_combat_page_loads(self):
        """Test that combat page loads successfully."""
        response = self.client.get(reverse('combat'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Combat')

    def test_combat_has_movement_content(self):
        """Test that combat page has movement content."""
        response = self.client.get(reverse('combat'))
        self.assertContains(response, 'Movement')


class ReferenceImageTests(TestCase):
    """Tests for serving images from references/images directory."""

    def setUp(self):
        self.client = Client()

    def test_valid_image_serves(self):
        """Test that a valid image file is served."""
        response = self.client.get(reverse('reference_image', args=['megahex.png']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_invalid_image_404(self):
        """Test that non-existent image returns 404."""
        response = self.client.get(reverse('reference_image', args=['nonexistent.png']))
        self.assertEqual(response.status_code, 404)

    def test_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        # Django's URL routing blocks ../ in the pattern, so we test the view directly
        # The URL pattern [^/]+ prevents slashes, so traversal via URL is blocked
        # Test that a filename starting with / is blocked
        response = self.client.get('/images//etc/passwd')
        self.assertEqual(response.status_code, 404)

    def test_combat_page_renders_image(self):
        """Test that the combat page contains an img tag with correct absolute path."""
        response = self.client.get(reverse('combat'))
        self.assertEqual(response.status_code, 200)
        # The markdown ![Mega hex](/images/megahex.png) should render as an img tag
        # Note: must use absolute path /images/ to match the URL route
        self.assertContains(response, '<img')
        self.assertContains(response, '/images/megahex.png')


class IndexViewTests(TestCase):
    """Tests for the main index view (new auto-generate flow)."""

    def setUp(self):
        self.client = Client()

    def test_index_page_loads_with_character(self):
        """Test that the index page loads with auto-generated character."""
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Generator')
        # Character should be auto-generated and displayed
        self.assertContains(response, 'Pillars Character')

    def test_initial_character_has_no_skill_track_or_experience(self):
        """Test that initial character does NOT show skill track or prior experience."""
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)
        # Character should have basic info
        self.assertContains(response, 'Wealth:')
        # But NOT skill track or prior experience
        self.assertNotContains(response, 'PRIOR EXPERIENCE')
        self.assertNotContains(response, 'Track)')  # Would appear as "(Ranger Track)" etc.

    def test_index_has_control_buttons(self):
        """Test that index page has the control buttons."""
        response = self.client.get(reverse('generator'))
        self.assertContains(response, 'Add')  # Add Experience or Add More Experience
        self.assertContains(response, 'Re-roll')  # Re-roll buttons
        self.assertContains(response, 'years')  # Years selector

    def test_add_experience_stays_on_generator(self):
        """Test that add experience stays on generator and adds experience."""
        # First load to get character
        self.client.get(reverse('generator'))
        # Add experience
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'auto',
        })
        # Should redirect back to generator
        self.assertRedirects(response, reverse('generator'))
        # Session should have experience data
        self.assertGreater(self.client.session.get('interactive_years', 0), 0)

    def test_finish_shows_character_sheet(self):
        """Test that finish displays the character sheet."""
        # First load to get character
        self.client.get(reverse('generator'))
        # Finish
        response = self.client.post(reverse('generator'), {
            'action': 'finish',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Sheet')


class SelectTrackViewTests(TestCase):
    """Tests for the track selection view (legacy - not used in new UI)."""

    def test_select_track_redirects_without_pending_character(self):
        """Test that select track redirects to index if no pending character."""
        response = self.client.get(reverse('select_track'))
        self.assertRedirects(response, reverse('generator'))


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

    def test_add_experience_with_manual_track_works(self):
        """Test that adding experience with manual track selection works."""
        # First load generator to get character
        self.client.get(reverse('generator'))
        # Add experience with manual track selection
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'manual',
            'chosen_track': 'WORKER',
        })
        # Should redirect back to generator
        self.assertRedirects(response, reverse('generator'))
        # Check experience was added (at least 1 year - character may die before completing all 3)
        years_added = self.client.session.get('interactive_years')
        self.assertIsNotNone(years_added)
        self.assertGreaterEqual(years_added, 1)
        self.assertLessEqual(years_added, 3)
        # Track name should be set
        self.assertEqual(self.client.session.get('interactive_track_name'), 'Worker')


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
        # First create some session data by loading generator and adding experience
        self.client.get(reverse('generator'))
        self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'auto',
        })

        # Verify session has data
        self.assertIn('current_character', self.client.session)
        self.assertGreater(self.client.session.get('interactive_years', 0), 0)

        # Start over
        response = self.client.get(reverse('start_over'))
        self.assertRedirects(response, reverse('welcome'))

        # Session should be cleared of character data
        self.assertNotIn('interactive_years', self.client.session)


class UIFlowTests(TestCase):
    """End-to-end UI flow tests for the character generator (new flow)."""

    def setUp(self):
        self.client = Client()

    def test_full_generator_flow(self):
        """Test complete character generation flow with new UI."""
        # Step 1: Load index page - character auto-generated
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Generator')
        self.assertContains(response, 'Pillars Character')

        # Step 2: Finish the character
        response = self.client.post(reverse('generator'), {
            'action': 'finish',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Character Sheet')

    def test_full_experience_flow(self):
        """Test complete experience flow on generator page."""
        # Step 1: Load generator
        self.client.get(reverse('generator'))

        # Step 2: Add experience
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 5,
            'track_mode': 'auto',
        })
        # Should redirect back to generator
        self.assertRedirects(response, reverse('generator'))

        # Step 3: Generator should show experience info
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Year-by-Year Log')
        # Check session has experience (1-5 years - character may die before completing all)
        years_added = self.client.session.get('interactive_years')
        self.assertIsNotNone(years_added)
        self.assertGreaterEqual(years_added, 1)
        self.assertLessEqual(years_added, 5)

    def test_start_over_clears_experience(self):
        """Test start over button clears experience data."""
        # Load generator and add experience
        self.client.get(reverse('generator'))
        self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'auto',
        })

        # Verify we have session data
        self.assertIn('current_character', self.client.session)
        self.assertGreater(self.client.session.get('interactive_years', 0), 0)

        # Start over
        response = self.client.get(reverse('start_over'))
        self.assertRedirects(response, reverse('welcome'))

        # Session should be cleared
        self.assertNotIn('interactive_years', self.client.session)

    def test_finish_after_experience(self):
        """Test finishing a character after adding experience."""
        # Load generator and go through track selection
        self.client.get(reverse('generator'))
        self.client.post(reverse('generator'), {'action': 'add_experience'})
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

    def test_control_section_available(self):
        """Test that control section with years selector is available."""
        response = self.client.get(reverse('generator'))
        self.assertContains(response, 'years-select')


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


class RoleTests(TestCase):
    """Tests for user roles and permissions."""

    def setUp(self):
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile

        self.client = Client()

        # Create test users with different roles
        self.player_user = User.objects.create_user('player_test', password='testpass')
        UserProfile.objects.create(user=self.player_user, roles=['player'])

        self.dm_user = User.objects.create_user('dm_test', password='testpass')
        UserProfile.objects.create(user=self.dm_user, roles=['dm'])

        self.admin_user = User.objects.create_user('admin_test', password='testpass')
        UserProfile.objects.create(user=self.admin_user, roles=['admin'])

        self.admin_dm_user = User.objects.create_user('admin_dm_test', password='testpass')
        UserProfile.objects.create(user=self.admin_dm_user, roles=['admin', 'dm'])

    def test_player_role_properties(self):
        """Test player role property methods."""
        profile = self.player_user.profile
        self.assertTrue(profile.is_player)
        self.assertFalse(profile.is_dm)
        self.assertFalse(profile.is_admin)

    def test_dm_role_properties(self):
        """Test DM role property methods."""
        profile = self.dm_user.profile
        self.assertFalse(profile.is_player)
        self.assertTrue(profile.is_dm)
        self.assertFalse(profile.is_admin)

    def test_admin_role_properties(self):
        """Test admin role property methods."""
        profile = self.admin_user.profile
        self.assertFalse(profile.is_player)
        self.assertFalse(profile.is_dm)
        self.assertTrue(profile.is_admin)

    def test_multi_role_properties(self):
        """Test user with multiple roles."""
        profile = self.admin_dm_user.profile
        self.assertFalse(profile.is_player)
        self.assertTrue(profile.is_dm)
        self.assertTrue(profile.is_admin)

    def test_player_cannot_see_dm_links(self):
        """Test that player cannot see DM links on welcome page."""
        self.client.login(username='player_test', password='testpass')
        response = self.client.get(reverse('welcome'))
        self.assertNotContains(response, 'DM Handbook')
        self.assertNotContains(response, 'Manage Users')

    def test_dm_can_see_dm_handbook_link(self):
        """Test that DM can see DM link on welcome page."""
        self.client.login(username='dm_test', password='testpass')
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, reverse('dm'))
        self.assertNotContains(response, 'Manage Users')

    def test_admin_can_see_all_links(self):
        """Test that admin can see all links on welcome page."""
        self.client.login(username='admin_test', password='testpass')
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, reverse('dm'))
        self.assertContains(response, 'Manage Users')

    def test_admin_dm_can_see_all_links(self):
        """Test that admin+dm user can see all links on welcome page."""
        self.client.login(username='admin_dm_test', password='testpass')
        response = self.client.get(reverse('welcome'))
        self.assertContains(response, reverse('dm'))
        self.assertContains(response, 'Manage Users')

    def test_player_cannot_access_manage_users(self):
        """Test that player cannot access manage users page."""
        self.client.login(username='player_test', password='testpass')
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('welcome'))

    def test_dm_cannot_access_manage_users(self):
        """Test that DM cannot access manage users page."""
        self.client.login(username='dm_test', password='testpass')
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('welcome'))

    def test_admin_can_access_manage_users(self):
        """Test that admin can access manage users page."""
        self.client.login(username='admin_test', password='testpass')
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Users')

    def test_unauthenticated_cannot_see_dm_links(self):
        """Test that unauthenticated user cannot see DM links."""
        response = self.client.get(reverse('welcome'))
        self.assertNotContains(response, 'DM Handbook')
        self.assertNotContains(response, 'Manage Users')

    def test_unauthenticated_cannot_access_manage_users(self):
        """Test that unauthenticated user cannot access manage users."""
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('login'))


class DMHandbookContentTests(TestCase):
    """Tests for DM Handbook content integrity."""

    def setUp(self):
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile

        self.client = Client()

        # Create a DM user to access the handbook
        self.dm_user = User.objects.create_user('dm_content_test', password='testpass')
        UserProfile.objects.create(user=self.dm_user, roles=['dm'])

    def test_dm_handbook_loads(self):
        """Test that DM handbook page loads successfully for DM users."""
        self.client.login(username='dm_content_test', password='testpass')
        response = self.client.get(reverse('dm'))
        self.assertEqual(response.status_code, 200)

    def test_dm_handbook_has_correct_structure(self):
        """Test that DM handbook starts with proper header, not corrupted content."""
        self.client.login(username='dm_content_test', password='testpass')
        response = self.client.get(reverse('dm'))

        # The handbook should contain the proper Game Master Reference header
        self.assertContains(response, 'Game Master Reference')
        self.assertContains(response, 'Quick Reference Tables')

    def test_dm_handbook_has_no_corrupted_content(self):
        """Test that DM handbook does not have corrupted content at the start."""
        self.client.login(username='dm_content_test', password='testpass')
        response = self.client.get(reverse('dm'))

        # These are markers of the corrupted content that was incorrectly prepended
        self.assertNotContains(response, 'Wild magic')
        self.assertNotContains(response, 'Controlled magic')
        self.assertNotContains(response, 'Determine Prior Experience')

    def test_dm_handbook_has_scenario_seeds(self):
        """Test that DM handbook contains the scenario seeds section."""
        self.client.login(username='dm_content_test', password='testpass')
        response = self.client.get(reverse('dm'))

        # Verify key sections from the handbook are present
        self.assertContains(response, 'Scenario Seeds')
        self.assertContains(response, 'The Weregild Appraiser')


class ReturnToGeneratorTests(TestCase):
    """Tests for experience display on generator page."""

    def setUp(self):
        self.client = Client()

    def test_add_experience_returns_to_generator(self):
        """Test that adding experience returns to generator page."""
        # Load generator
        self.client.get(reverse('generator'))

        # Add experience
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'auto',
        })

        # Should redirect back to generator
        self.assertRedirects(response, reverse('generator'))

        # Session should have experience data
        self.assertEqual(self.client.session.get('interactive_years'), 3)

    def test_generator_shows_experience_after_adding(self):
        """Test that generator shows prior experience after adding."""
        # Load generator
        self.client.get(reverse('generator'))

        # Add experience
        self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 2,
            'track_mode': 'auto',
        })

        # Load generator page again
        response = self.client.get(reverse('generator'))

        # Should show experience section
        self.assertContains(response, 'Year-by-Year Log')
        self.assertContains(response, 'Year 16')  # First year is age 16


class CharacterSheetTests(TestCase):
    """Tests for the editable character sheet."""

    def setUp(self):
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile, SavedCharacter

        self.client = Client()

        # Create test user
        self.user = User.objects.create_user('sheet_test', password='testpass')
        UserProfile.objects.create(user=self.user, roles=['player'])

        # Create a saved character
        self.char_data = {
            'attributes': {
                'STR': 12, 'DEX': 14, 'INT': 10, 'WIS': 11, 'CON': 13, 'CHR': 9,
                'generation_method': '4d6 drop lowest',
                'fatigue_points': 40, 'body_points': 30,
                'fatigue_roll': 3, 'body_roll': 4
            },
            'appearance': 'Average',
            'height': '5\'10"',
            'weight': '160 lbs',
            'provenance': 'Commoner - Laborer',
            'provenance_social_class': 'Commoner',
            'provenance_sub_class': 'Laborer',
            'location': 'Village',
            'location_skills': ['Survival'],
            'literacy': 'Literate',
            'wealth': 'Moderate (100 coin)',
            'wealth_level': 'Moderate',
            'str_repr': 'Test character',
            'skill_track': None,
            'interactive_years': 0,
            'interactive_skills': [],
            'interactive_yearly_results': [],
            'interactive_aging': {},
            'interactive_died': False,
        }
        self.saved_char = SavedCharacter.objects.create(
            user=self.user,
            name='Test Character',
            character_data=self.char_data
        )

    def test_character_sheet_requires_login(self):
        """Test that character sheet requires authentication."""
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertRedirects(response, f'/login/?next=/character/{self.saved_char.id}/')

    def test_character_sheet_loads_for_owner(self):
        """Test that character sheet loads for the owner."""
        self.client.login(username='sheet_test', password='testpass')
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Character')

    def test_character_sheet_shows_attributes(self):
        """Test that character sheet displays all attributes."""
        self.client.login(username='sheet_test', password='testpass')
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertContains(response, 'STR')
        self.assertContains(response, 'DEX')
        self.assertContains(response, 'INT')
        self.assertContains(response, 'WIS')
        self.assertContains(response, 'CON')
        self.assertContains(response, 'CHR')

    def test_character_sheet_shows_skills(self):
        """Test that character sheet displays skills."""
        self.client.login(username='sheet_test', password='testpass')
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertContains(response, 'Survival')  # From location_skills

    def test_character_sheet_404_for_nonexistent(self):
        """Test that nonexistent character returns redirect to my_characters."""
        self.client.login(username='sheet_test', password='testpass')
        response = self.client.get(reverse('character_sheet', args=[99999]))
        self.assertRedirects(response, reverse('my_characters'))

    def test_character_sheet_403_for_other_user(self):
        """Test that other user's character returns redirect."""
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile

        other_user = User.objects.create_user('other_test', password='testpass')
        UserProfile.objects.create(user=other_user, roles=['player'])

        self.client.login(username='other_test', password='testpass')
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertRedirects(response, reverse('my_characters'))

    def test_character_sheet_shows_yearly_results(self):
        """Test that character sheet displays year-by-year experience log."""
        self.client.login(username='sheet_test', password='testpass')

        # Add yearly results to the character
        self.saved_char.character_data['interactive_years'] = 3
        self.saved_char.character_data['interactive_yearly_results'] = [
            {'year': 16, 'skill': 'Sword', 'surv_roll': 10, 'surv_mod': 2, 'surv_total': 12, 'surv_target': 5, 'survived': True},
            {'year': 17, 'skill': 'Shield', 'surv_roll': 8, 'surv_mod': 2, 'surv_total': 10, 'surv_target': 5, 'survived': True},
            {'year': 18, 'skill': 'Tactics', 'surv_roll': 6, 'surv_mod': 2, 'surv_total': 8, 'surv_target': 5, 'survived': True},
        ]
        self.saved_char.save()

        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        # Check yearly_results is in context
        self.assertIn('yearly_results', response.context)
        self.assertEqual(len(response.context['yearly_results']), 3)
        # Check that the year-by-year log section appears
        self.assertContains(response, 'Year-by-Year Log')
        # Check that specific year entries appear
        self.assertContains(response, 'Year 16')
        self.assertContains(response, 'Sword')
        self.assertContains(response, 'Year 17')
        self.assertContains(response, 'Shield')

    def test_character_sheet_shows_aging_warning_elements(self):
        """Test that character sheet has aging warning UI elements."""
        self.client.login(username='sheet_test', password='testpass')
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        # Check for aging warning HTML elements
        self.assertContains(response, 'id="aging-warning"')
        self.assertContains(response, 'Aging Warning!')
        self.assertContains(response, 'id="aging-years"')
        self.assertContains(response, 'aging penalties')
        # Check for the JavaScript that handles the warning
        self.assertContains(response, 'updateAgingWarning')
        self.assertContains(response, 'CURRENT_AGE')


class UpdateCharacterAPITests(TestCase):
    """Tests for the character update API endpoint."""

    def setUp(self):
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile, SavedCharacter

        self.client = Client()

        # Create test user
        self.user = User.objects.create_user('api_test', password='testpass')
        UserProfile.objects.create(user=self.user, roles=['player'])

        # Create a saved character
        self.char_data = {
            'attributes': {
                'STR': 12, 'DEX': 14, 'INT': 10, 'WIS': 11, 'CON': 13, 'CHR': 9,
                'generation_method': '4d6 drop lowest',
                'fatigue_points': 40, 'body_points': 30,
                'fatigue_roll': 3, 'body_roll': 4
            },
            'appearance': 'Average',
            'height': '5\'10"',
            'weight': '160 lbs',
            'provenance': 'Commoner',
            'location': 'Village',
            'location_skills': ['Survival'],
            'literacy': 'Literate',
            'wealth': 'Moderate',
            'str_repr': 'Test character',
            'manual_skills': [],
        }
        self.saved_char = SavedCharacter.objects.create(
            user=self.user,
            name='Test Character',
            character_data=self.char_data
        )

    def test_update_requires_login(self):
        """Test that update API requires authentication."""
        import json
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'name', 'value': 'New Name'}),
            content_type='application/json'
        )
        self.assertRedirects(response, f'/login/?next=/character/{self.saved_char.id}/update/')

    def test_update_name(self):
        """Test updating character name."""
        import json
        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'name', 'value': 'New Name'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.name, 'New Name')

    def test_update_attribute(self):
        """Test updating an attribute."""
        import json
        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'attributes.STR', 'value': 15}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # Should return computed values
        self.assertIn('computed', data)
        self.assertIn('fatigue_points', data['computed'])
        self.assertIn('body_points', data['computed'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['attributes']['STR'], 15)

    def test_update_biographical_field(self):
        """Test updating a biographical field."""
        import json
        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'appearance', 'value': 'Handsome'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['appearance'], 'Handsome')

    def test_add_skill(self):
        """Test adding a skill."""
        import json
        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'skills', 'action': 'add', 'value': 'Sword +1'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertIn('Sword +1', self.saved_char.character_data['manual_skills'])

    def test_remove_skill(self):
        """Test removing a skill."""
        import json
        # First add a skill
        self.saved_char.character_data['manual_skills'] = ['Sword +1', 'Shield']
        self.saved_char.save()

        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'skills', 'action': 'remove', 'index': 0}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['manual_skills'], ['Shield'])

    def test_edit_skill(self):
        """Test editing a skill."""
        import json
        # First add a skill
        self.saved_char.character_data['manual_skills'] = ['Sword +1']
        self.saved_char.save()

        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'skills', 'action': 'edit', 'index': 0, 'value': 'Sword +3'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['manual_skills'], ['Sword +3'])

    def test_update_notes(self):
        """Test updating notes field."""
        import json
        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'notes', 'value': 'Born in the mountains...'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify in database
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['notes'], 'Born in the mountains...')

    def test_update_invalid_field(self):
        """Test updating an invalid field returns error."""
        import json
        self.client.login(username='api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'invalid_field', 'value': 'test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_update_other_users_character(self):
        """Test that updating another user's character fails."""
        import json
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile

        other_user = User.objects.create_user('other_api_test', password='testpass')
        UserProfile.objects.create(user=other_user, roles=['player'])

        self.client.login(username='other_api_test', password='testpass')
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            data=json.dumps({'field': 'name', 'value': 'Hacked Name'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)


class RecalculateDerivedTests(TestCase):
    """Tests for the recalculate_derived function."""

    def test_recalculate_fatigue_and_body(self):
        """Test that fatigue and body points are correctly recalculated."""
        from webapp.generator.views import recalculate_derived

        char_data = {
            'attributes': {
                'STR': 14,  # +1 mod
                'DEX': 12,  # 0 mod
                'INT': 10,  # 0 mod
                'WIS': 16,  # +3 mod
                'CON': 13,  # 0 mod
                'CHR': 9,   # 0 mod
                'fatigue_roll': 4,
                'body_roll': 3,
            }
        }

        result = recalculate_derived(char_data)

        # Fatigue = CON + WIS + max(DEX, STR) + fatigue_roll + int_mod + wis_mod
        # = 13 + 16 + 14 + 4 + 0 + 3 = 50
        self.assertEqual(result['fatigue_points'], 50)

        # Body = CON + max(DEX, STR) + body_roll + int_mod + wis_mod
        # = 13 + 14 + 3 + 0 + 3 = 33
        self.assertEqual(result['body_points'], 33)

    def test_recalculate_with_negative_modifiers(self):
        """Test recalculation with negative attribute modifiers."""
        from webapp.generator.views import recalculate_derived

        char_data = {
            'attributes': {
                'STR': 6,   # -2 mod
                'DEX': 8,   # 0 mod
                'INT': 5,   # -3 mod
                'WIS': 7,   # -1 mod
                'CON': 10,  # 0 mod
                'CHR': 9,   # 0 mod
                'fatigue_roll': 3,
                'body_roll': 3,
            }
        }

        result = recalculate_derived(char_data)

        # Fatigue = CON + WIS + max(DEX, STR) + fatigue_roll + int_mod + wis_mod
        # = 10 + 7 + 8 + 3 + (-3) + (-1) = 24
        self.assertEqual(result['fatigue_points'], 24)

        # Body = CON + max(DEX, STR) + body_roll + int_mod + wis_mod
        # = 10 + 8 + 3 + (-3) + (-1) = 17
        self.assertEqual(result['body_points'], 17)


class AttributeFormatTests(TestCase):
    """Tests for the extended attribute format (beyond 18)."""

    def test_get_attribute_modifier_standard_values(self):
        """Test modifier calculation for standard 1-18 values."""
        from webapp.generator.views import get_attribute_modifier

        # Standard values from ATTRIBUTE_MODIFIERS
        # {3: -5, 4: -4, 5: -3, 6: -2, 7: -1, 8-13: 0, 14: 1, 15: 2, 16: 3, 17: 4, 18: 5}
        self.assertEqual(get_attribute_modifier(3), -5)
        self.assertEqual(get_attribute_modifier(6), -2)
        self.assertEqual(get_attribute_modifier(10), 0)
        self.assertEqual(get_attribute_modifier(14), 1)
        self.assertEqual(get_attribute_modifier(18), 5)

    def test_get_attribute_modifier_decimal_notation(self):
        """Test modifier calculation for decimal notation (18.XX, 19.XX, etc)."""
        from webapp.generator.views import get_attribute_modifier

        # 18.XX should have +5 modifier (same as 18)
        self.assertEqual(get_attribute_modifier("18.10"), 5)
        self.assertEqual(get_attribute_modifier("18.50"), 5)
        self.assertEqual(get_attribute_modifier("18.100"), 5)

        # 19.XX should have +6 modifier
        self.assertEqual(get_attribute_modifier("19.10"), 6)
        self.assertEqual(get_attribute_modifier("19.100"), 6)

        # 20.XX should have +7 modifier
        self.assertEqual(get_attribute_modifier("20.50"), 7)

        # Higher values
        self.assertEqual(get_attribute_modifier("24.10"), 11)

    def test_get_attribute_base_value(self):
        """Test extracting base value from attribute."""
        from webapp.generator.views import get_attribute_base_value

        # Integer values
        self.assertEqual(get_attribute_base_value(12), 12)
        self.assertEqual(get_attribute_base_value(18), 18)

        # Decimal notation
        self.assertEqual(get_attribute_base_value("18.20"), 18)
        self.assertEqual(get_attribute_base_value("19.50"), 19)
        self.assertEqual(get_attribute_base_value("24.100"), 24)

        # String integers
        self.assertEqual(get_attribute_base_value("15"), 15)

    def test_format_attribute_display(self):
        """Test formatting attributes for display."""
        from webapp.generator.views import format_attribute_display

        self.assertEqual(format_attribute_display(12), "12")
        self.assertEqual(format_attribute_display("18.20"), "18.20")
        self.assertEqual(format_attribute_display("19.100"), "19.100")

    def test_recalculate_with_exceptional_attributes(self):
        """Test derived stat calculation with exceptional attributes."""
        from webapp.generator.views import recalculate_derived

        char_data = {
            'attributes': {
                'STR': "19.50",  # Base 19, mod +6
                'DEX': 14,       # Mod +1
                'INT': 10,       # Mod 0
                'WIS': 16,       # Mod +3
                'CON': 15,       # Mod +2
                'CHR': 12,       # Mod 0
                'fatigue_roll': 4,
                'body_roll': 3,
            }
        }

        result = recalculate_derived(char_data)

        # Fatigue = CON + WIS + max(DEX, STR) + fatigue_roll + int_mod + wis_mod
        # = 15 + 16 + 19 + 4 + 0 + 3 = 57
        self.assertEqual(result['fatigue_points'], 57)

        # Body = CON + max(DEX, STR) + body_roll + int_mod + wis_mod
        # = 15 + 19 + 3 + 0 + 3 = 40
        self.assertEqual(result['body_points'], 40)


class ConsolidateSkillsTests(TestCase):
    """Tests for skill consolidation."""

    def test_consolidate_simple_duplicates(self):
        """Test consolidating simple duplicate skills."""
        from webapp.generator.views import consolidate_skills

        skills = ['Tracking', 'Tracking', 'Tracking']
        result = consolidate_skills(skills)
        self.assertEqual(result, ['Tracking 3'])

    def test_consolidate_mixed_skills(self):
        """Test consolidating mixed skills with some duplicates."""
        from webapp.generator.views import consolidate_skills

        skills = ['Tracking', 'Survival', 'Tracking', 'Swimming']
        result = consolidate_skills(skills)
        # Should be sorted alphabetically
        self.assertIn('Tracking 2', result)
        self.assertIn('Survival', result)
        self.assertIn('Swimming', result)
        self.assertEqual(len(result), 3)

    def test_consolidate_skills_with_numbers(self):
        """Test consolidating skills that already have numbers."""
        from webapp.generator.views import consolidate_skills

        skills = ['Sword +1', 'Sword +1', 'Shield']
        result = consolidate_skills(skills)
        # Skills with numbers use (xN) format
        self.assertIn('Sword +1 (x2)', result)
        self.assertIn('Shield', result)

    def test_consolidate_no_duplicates(self):
        """Test consolidating with no duplicates."""
        from webapp.generator.views import consolidate_skills

        skills = ['Tracking', 'Survival', 'Swimming']
        result = consolidate_skills(skills)
        self.assertEqual(len(result), 3)
        # All skills should appear without counts
        self.assertIn('Tracking', result)
        self.assertIn('Survival', result)
        self.assertIn('Swimming', result)

    def test_consolidate_empty_list(self):
        """Test consolidating empty skill list."""
        from webapp.generator.views import consolidate_skills

        result = consolidate_skills([])
        self.assertEqual(result, [])

    def test_consolidate_sorted_alphabetically(self):
        """Test that consolidated skills are sorted alphabetically."""
        from webapp.generator.views import consolidate_skills

        skills = ['Zebra', 'Apple', 'Mango']
        result = consolidate_skills(skills)
        self.assertEqual(result, ['Apple', 'Mango', 'Zebra'])

    def test_consolidate_case_insensitive(self):
        """Test that skill consolidation is case-insensitive."""
        from webapp.generator.views import consolidate_skills

        skills = ['Weather Sense', 'weather sense', 'WEATHER SENSE']
        result = consolidate_skills(skills)
        self.assertEqual(len(result), 1)
        self.assertIn('Weather Sense 3', result)

    def test_consolidate_mixed_case_preserves_first(self):
        """Test that the first occurrence's case is preserved."""
        from webapp.generator.views import consolidate_skills

        skills = ['Tracking', 'TRACKING']
        result = consolidate_skills(skills)
        self.assertEqual(result, ['Tracking 2'])

    def test_consolidate_handles_empty_strings(self):
        """Test that empty strings are filtered out."""
        from webapp.generator.views import consolidate_skills

        skills = ['Tracking', '', 'Survival', None, 'Tracking']
        result = consolidate_skills(skills)
        self.assertIn('Tracking 2', result)
        self.assertIn('Survival', result)
        self.assertEqual(len(result), 2)


class NormalizeSkillTests(TestCase):
    """Tests for skill name normalization."""

    def test_normalize_simple_skill(self):
        """Test normalization of simple skill names."""
        from webapp.generator.views import normalize_skill_name

        self.assertEqual(normalize_skill_name('tracking'), 'Tracking')
        self.assertEqual(normalize_skill_name('WEATHER SENSE'), 'Weather Sense')
        self.assertEqual(normalize_skill_name('weather sense'), 'Weather Sense')

    def test_normalize_skill_with_modifier(self):
        """Test that modifiers like +1 are preserved."""
        from webapp.generator.views import normalize_skill_name

        self.assertEqual(normalize_skill_name('sword +1 to hit'), 'Sword +1 to hit')
        self.assertEqual(normalize_skill_name('SWORD +2'), 'Sword +2')

    def test_normalize_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        from webapp.generator.views import normalize_skill_name

        self.assertEqual(normalize_skill_name('  Tracking  '), 'Tracking')
        self.assertEqual(normalize_skill_name('\tSurvival\n'), 'Survival')

    def test_normalize_empty_string(self):
        """Test that empty strings are handled."""
        from webapp.generator.views import normalize_skill_name

        self.assertEqual(normalize_skill_name(''), '')
        self.assertIsNone(normalize_skill_name(None))


class TrackInfoTests(TestCase):
    """Tests for track info display on character sheet."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='trackinfo_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

        self.saved_char = SavedCharacter.objects.create(
            user=self.user,
            name='Track Info Test',
            character_data={
                'attributes': {
                    'STR': 14, 'DEX': 12, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10,
                    'fatigue_points': 30, 'body_points': 25,
                },
                'provenance_social_class': 'Commoner',
                'wealth_level': 'Moderate',
            }
        )

    def test_character_sheet_shows_track_info_when_no_track(self):
        """Test that character sheet shows track availability when no track selected."""
        self.client.login(username='trackinfo_test', password='test123')

        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        # Should have track info in context
        self.assertIn('track_info', response.context)
        self.assertIsNotNone(response.context['track_info'])
        # Should show the track list
        self.assertContains(response, 'Available Tracks')
        self.assertContains(response, 'track-item')

    def test_character_sheet_hides_track_info_when_has_track(self):
        """Test that track info is hidden when character already has a track."""
        self.client.login(username='trackinfo_test', password='test123')

        # Add a skill track and some experience so the Prior Experience section shows
        self.saved_char.character_data['skill_track'] = {
            'track': 'Army',
            'survivability': 5,
            'initial_skills': ['Sword'],
        }
        self.saved_char.character_data['interactive_years'] = 3
        self.saved_char.save()

        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        # Should not have track_info since character has a track
        self.assertIsNone(response.context['track_info'])
        # Should show track in Prior Experience section
        self.assertContains(response, 'Prior Experience')
        self.assertContains(response, 'Army')


class AdminViewAllCharactersTests(TestCase):
    """Tests for admin ability to view all characters in manage_users."""

    def setUp(self):
        self.client = Client()
        # Create a regular player
        self.player = User.objects.create_user(username='player1', password='test123')
        UserProfile.objects.create(user=self.player, roles=['player'])

        # Create a DM
        self.dm = User.objects.create_user(username='dm1', password='test123')
        UserProfile.objects.create(user=self.dm, roles=['dm'])

        # Create an admin
        self.admin = User.objects.create_user(username='admin1', password='test123')
        UserProfile.objects.create(user=self.admin, roles=['admin'])

        # Create a character owned by the player
        self.player_char = SavedCharacter.objects.create(
            user=self.player,
            name='Player Character',
            character_data={
                'attributes': {
                    'STR': 14, 'DEX': 12, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10,
                    'fatigue_points': 30, 'body_points': 25, 'fatigue_roll': 3, 'body_roll': 3,
                    'generation_method': 'test',
                },
                'appearance': 'Average',
                'height': '5\'10"',
                'weight': '170 lbs',
                'provenance': 'Commoner',
                'location': 'Test Town',
                'location_skills': [],
                'literacy': 'Illiterate',
                'wealth': 'Moderate',
                'wealth_level': 'Moderate',
                'str_repr': "player1's character",
            }
        )

    def test_player_sees_only_own_characters_in_my_characters(self):
        """Test that my_characters only shows user's own characters."""
        self.client.login(username='player1', password='test123')
        response = self.client.get(reverse('my_characters'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Saved Characters')
        # Should not have show_owner in context
        self.assertNotIn('show_owner', response.context)

    def test_admin_sees_all_characters_in_manage_users(self):
        """Test that admin sees all characters grouped by user in manage_users page."""
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('manage_users'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Characters')
        self.assertContains(response, 'player1')  # Username as section header
        self.assertContains(response, 'Player Character')  # Character name
        # Should have characters_by_user in context
        self.assertIn('characters_by_user', response.context)
        self.assertIn('player1', response.context['characters_by_user'])

    def test_dm_cannot_access_manage_users(self):
        """Test that DM (non-admin) cannot access manage_users page."""
        self.client.login(username='dm1', password='test123')
        response = self.client.get(reverse('manage_users'))

        # Should redirect away since DM is not admin
        self.assertRedirects(response, reverse('welcome'))

    def test_admin_can_view_other_player_character(self):
        """Test that admin can view another player's character sheet."""
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('character_sheet', args=[self.player_char.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_owner'])
        self.assertContains(response, 'Player Character')
        self.assertContains(response, "player1's character")

    def test_player_cannot_view_other_character(self):
        """Test that regular player cannot view another player's character."""
        other_player = User.objects.create_user(username='player2', password='test123')
        UserProfile.objects.create(user=other_player, roles=['player'])

        self.client.login(username='player2', password='test123')
        response = self.client.get(reverse('character_sheet', args=[self.player_char.id]))

        # Should redirect to my_characters with error
        self.assertRedirects(response, reverse('my_characters'))

    def test_admin_cannot_edit_other_player_character(self):
        """Test that admin can view but not edit another player's character."""
        import json
        self.client.login(username='admin1', password='test123')

        response = self.client.post(
            reverse('update_character', args=[self.player_char.id]),
            json.dumps({'field': 'name', 'value': 'Hacked Name'}),
            content_type='application/json'
        )

        # Should get 404 since update only allows owner
        self.assertEqual(response.status_code, 404)

        # Character name should be unchanged
        self.player_char.refresh_from_db()
        self.assertEqual(self.player_char.name, 'Player Character')


class AutoSaveTests(TestCase):
    """Tests for auto-save functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='autosave_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

    def test_logged_in_user_auto_saves_on_generate(self):
        """Test that logged-in users get characters auto-saved to database."""
        self.client.login(username='autosave_test', password='test123')

        # Visit generator - should create and auto-save a character (stays on generator)
        response = self.client.get(reverse('generator'))

        # Should stay on generator page
        self.assertEqual(response.status_code, 200)

        # Character should be saved in database
        saved_chars = SavedCharacter.objects.filter(user=self.user)
        self.assertEqual(saved_chars.count(), 1)

    def test_anonymous_user_stores_in_session(self):
        """Test that anonymous users get characters stored in session only."""
        # Visit generator without login
        response = self.client.get(reverse('generator'))

        # Should stay on the generator page (200)
        self.assertEqual(response.status_code, 200)

        # No characters should be in database
        self.assertEqual(SavedCharacter.objects.count(), 0)

        # Session should have character data
        self.assertIn('current_character', self.client.session)


class AddExperienceTests(TestCase):
    """Tests for adding experience to saved characters."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='exp_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

        # Create a saved character
        self.saved_char = SavedCharacter.objects.create(
            user=self.user,
            name='Test Character',
            character_data={
                'attributes': {
                    'STR': 14, 'DEX': 12, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10,
                    'fatigue_points': 30, 'body_points': 25, 'fatigue_roll': 3, 'body_roll': 3,
                    'generation_method': 'test',
                },
                'appearance': 'Average',
                'height': '5\'10"',
                'weight': '170 lbs',
                'provenance': 'Commoner',
                'provenance_social_class': 'Commoner',
                'provenance_sub_class': 'Laborer',
                'location': 'Test Town',
                'location_skills': ['Farming'],
                'literacy': 'Illiterate',
                'wealth': 'Moderate',
                'wealth_level': 'Moderate',
                'str_repr': 'Test character',
            }
        )

    def test_add_experience_creates_skill_track(self):
        """Test that adding experience creates a skill track if none exists."""
        self.client.login(username='exp_test', password='test123')

        response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 3, 'track': 'ARMY'}
        )

        # Should redirect to character sheet
        self.assertRedirects(response, reverse('character_sheet', args=[self.saved_char.id]))

        # Reload character
        self.saved_char.refresh_from_db()
        char_data = self.saved_char.character_data

        # Should have skill track
        self.assertIn('skill_track', char_data)
        self.assertEqual(char_data['skill_track']['track'], 'Army')

        # Should have years of experience
        self.assertEqual(char_data['interactive_years'], 3)

        # Should have skills from experience
        self.assertIn('interactive_skills', char_data)
        self.assertGreater(len(char_data['interactive_skills']), 0)

    def test_add_experience_accumulates(self):
        """Test that adding more experience accumulates with existing."""
        self.client.login(username='exp_test', password='test123')

        # Add first batch
        self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 2, 'track': 'WORKER'}
        )

        self.saved_char.refresh_from_db()
        first_years = self.saved_char.character_data['interactive_years']
        first_skills = len(self.saved_char.character_data['interactive_skills'])

        # Add second batch
        self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 2}
        )

        self.saved_char.refresh_from_db()
        second_years = self.saved_char.character_data['interactive_years']
        second_skills = len(self.saved_char.character_data['interactive_skills'])

        # Years should accumulate
        self.assertGreater(second_years, first_years)

        # Skills should accumulate
        self.assertGreater(second_skills, first_skills)

    def test_add_experience_updates_ui_correctly(self):
        """Test that adding experience updates the character sheet UI with new data."""
        self.client.login(username='exp_test', password='test123')

        # First, verify the character sheet shows no experience
        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertEqual(response.status_code, 200)
        # Should show years_served as 0
        self.assertEqual(response.context['years_served'], 0)
        self.assertEqual(response.context['current_age'], 16)
        # Should have empty yearly_results
        self.assertEqual(len(response.context['yearly_results']), 0)
        # Year-by-Year Log should NOT appear (no results)
        self.assertNotContains(response, 'Year-by-Year Log')

        # Add 3 years of experience
        add_response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 3, 'track': 'WORKER'},
            follow=True  # Follow the redirect
        )

        # Should end up at character sheet
        self.assertEqual(add_response.status_code, 200)

        # Verify the UI shows updated experience data
        # Check context variables
        self.assertEqual(add_response.context['years_served'], 3)
        self.assertEqual(add_response.context['current_age'], 19)  # 16 + 3
        self.assertEqual(len(add_response.context['yearly_results']), 3)

        # Check the HTML content shows the experience
        self.assertContains(add_response, 'Year-by-Year Log')
        self.assertContains(add_response, 'Year 16')  # First year of experience
        self.assertContains(add_response, 'Year 17')
        self.assertContains(add_response, 'Year 18')

        # Prior Experience sidebar section should show updated values
        self.assertContains(add_response, 'Prior Experience')
        self.assertContains(add_response, 'Years Served')

        # Should show the track that was selected
        self.assertContains(add_response, 'Worker')

    def test_add_more_experience_updates_ui(self):
        """Test that adding more experience to existing updates UI correctly."""
        self.client.login(username='exp_test', password='test123')

        # Add initial experience
        self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 2, 'track': 'WORKER'}
        )

        # Verify initial state
        response1 = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))
        self.assertEqual(response1.context['years_served'], 2)
        self.assertEqual(response1.context['current_age'], 18)
        self.assertEqual(len(response1.context['yearly_results']), 2)

        # Add more experience
        add_response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 3},
            follow=True
        )

        # Verify accumulated experience in UI
        self.assertEqual(add_response.context['years_served'], 5)
        self.assertEqual(add_response.context['current_age'], 21)  # 16 + 5
        self.assertEqual(len(add_response.context['yearly_results']), 5)

        # Should show all 5 years in the log
        self.assertContains(add_response, 'Year 16')
        self.assertContains(add_response, 'Year 17')
        self.assertContains(add_response, 'Year 18')
        self.assertContains(add_response, 'Year 19')
        self.assertContains(add_response, 'Year 20')

    def test_add_experience_requires_login(self):
        """Test that adding experience requires authentication."""
        response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 3}
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_add_experience_handles_failed_track_creation(self):
        """Test that add experience handles when track creation fails gracefully."""
        self.client.login(username='exp_test', password='test123')

        # Create a character with stats that won't qualify for any track with auto-select
        # (all zero modifiers, no special qualifications)
        char_with_bad_stats = SavedCharacter.objects.create(
            user=self.user,
            name='Bad Stats Character',
            character_data={
                'attributes': {
                    'STR': 10, 'DEX': 10, 'INT': 10, 'WIS': 10, 'CON': 10, 'CHR': 10,
                    'fatigue_points': 30, 'body_points': 25, 'fatigue_roll': 3, 'body_roll': 3,
                },
                'provenance_social_class': 'Commoner',
                'provenance_sub_class': 'Laborer',
                'wealth_level': 'Moderate',
            }
        )

        # Try with auto-select - should handle gracefully even if track creation fails
        response = self.client.post(
            reverse('add_experience_to_character', args=[char_with_bad_stats.id]),
            {'years': 3, 'track': 'auto'}
        )

        # Should redirect back to character sheet (not crash with AttributeError)
        self.assertEqual(response.status_code, 302)
        self.assertIn('character', response.url)

    def test_add_experience_with_none_track_does_not_crash(self):
        """Test that add experience doesn't crash when skill_track.track is None."""
        from unittest.mock import patch, MagicMock
        from pillars.attributes import SkillTrack

        self.client.login(username='exp_test', password='test123')

        # Mock create_skill_track_for_choice to return a SkillTrack with track=None
        mock_skill_track = MagicMock(spec=SkillTrack)
        mock_skill_track.track = None  # This is the edge case that was crashing

        with patch('webapp.generator.views.create_skill_track_for_choice', return_value=mock_skill_track):
            response = self.client.post(
                reverse('add_experience_to_character', args=[self.saved_char.id]),
                {'years': 3, 'track': 'auto'}
            )

        # Should redirect with error message, not crash
        self.assertEqual(response.status_code, 302)
        self.assertIn('character', response.url)


    def test_add_experience_other_users_character(self):
        """Test that users cannot add experience to another user's character."""
        other_user = User.objects.create_user(username='other_exp', password='test123')
        UserProfile.objects.create(user=other_user, roles=['player'])

        self.client.login(username='other_exp', password='test123')

        response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 3, 'track': 'ARMY'}
        )

        # Should redirect to my_characters (not found for this user)
        self.assertRedirects(response, reverse('my_characters'))

    def test_add_experience_nonexistent_character(self):
        """Test that adding experience to nonexistent character redirects gracefully."""
        self.client.login(username='exp_test', password='test123')

        response = self.client.post(
            reverse('add_experience_to_character', args=[99999]),
            {'years': 3, 'track': 'ARMY'}
        )

        # Should redirect to my_characters
        self.assertRedirects(response, reverse('my_characters'))

    def test_add_experience_already_dead_character(self):
        """Test that adding experience to a dead character doesn't add more years."""
        self.client.login(username='exp_test', password='test123')

        # Mark character as dead
        self.saved_char.character_data['interactive_died'] = True
        self.saved_char.character_data['interactive_years'] = 5
        self.saved_char.character_data['skill_track'] = {
            'track': 'Army',
            'survivability': 5,
            'initial_skills': ['Sword'],
        }
        self.saved_char.save()

        response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 3}
        )

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Years should not have increased (character was already dead)
        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['interactive_years'], 5)

    def test_add_experience_with_specific_track(self):
        """Test that specifying a track uses that track."""
        self.client.login(username='exp_test', password='test123')

        response = self.client.post(
            reverse('add_experience_to_character', args=[self.saved_char.id]),
            {'years': 2, 'track': 'NAVY'}
        )

        self.assertEqual(response.status_code, 302)

        self.saved_char.refresh_from_db()
        self.assertEqual(self.saved_char.character_data['skill_track']['track'], 'Navy')


class CharacterSheetLayoutTests(TestCase):
    """Tests for character sheet display and layout."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='layout_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

        self.saved_char = SavedCharacter.objects.create(
            user=self.user,
            name='Layout Test Character',
            character_data={
                'attributes': {
                    'STR': 14, 'DEX': 12, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10,
                    'fatigue_points': 30, 'body_points': 25, 'fatigue_roll': 3, 'body_roll': 3,
                    'generation_method': 'test',
                },
                'appearance': 'Average',
                'height': '5\'10"',
                'weight': '170 lbs',
                'provenance': 'Commoner',
                'location': 'Test Town',
                'location_skills': ['Farming', 'Farming', 'Tracking'],
                'literacy': 'Illiterate',
                'wealth': 'Moderate',
                'str_repr': 'Test character',
            }
        )

    def test_character_sheet_has_add_experience_form(self):
        """Test that character sheet has add experience form on left side."""
        self.client.login(username='layout_test', password='test123')

        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Experience')
        self.assertContains(response, 'character-sidebar')

    def test_character_sheet_has_export_button(self):
        """Test that character sheet has markdown export button."""
        self.client.login(username='layout_test', password='test123')

        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Copy as Markdown')
        self.assertContains(response, 'exportMarkdown')

    def test_character_sheet_consolidates_skills(self):
        """Test that character sheet shows consolidated skills."""
        self.client.login(username='layout_test', password='test123')

        response = self.client.get(reverse('character_sheet', args=[self.saved_char.id]))

        self.assertEqual(response.status_code, 200)
        # "Farming" appears twice, should be consolidated
        content = response.content.decode()
        self.assertIn('Farming 2', content)
        self.assertIn('Tracking', content)


class SkillAdditionConsolidationTests(TestCase):
    """Tests for skill addition with consolidation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='skill_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

        self.saved_char = SavedCharacter.objects.create(
            user=self.user,
            name='Skill Test Character',
            character_data={
                'attributes': {
                    'STR': 14, 'DEX': 12, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10,
                    'fatigue_points': 30, 'body_points': 25, 'fatigue_roll': 3, 'body_roll': 3,
                    'generation_method': 'test',
                },
                'location_skills': ['Tracking'],
                'manual_skills': [],
                'str_repr': 'Test character',
            }
        )

    def test_adding_skill_returns_consolidated_list(self):
        """Test that adding a skill returns the consolidated skill list."""
        import json
        self.client.login(username='skill_test', password='test123')

        # Add the same skill that already exists
        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            json.dumps({'field': 'skills', 'action': 'add', 'value': 'Tracking'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Should have consolidated skills in response
        self.assertIn('computed', data)
        self.assertIn('skills', data['computed'])
        # Should show "Tracking 2" since we now have 2 Tracking skills
        self.assertIn('Tracking 2', data['computed']['skills'])

    def test_update_with_invalid_json(self):
        """Test that update endpoint handles invalid JSON gracefully."""
        self.client.login(username='skill_test', password='test123')

        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            'this is not valid json{{{',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON', data['error'])

    def test_update_with_missing_field(self):
        """Test that update endpoint requires a field."""
        import json
        self.client.login(username='skill_test', password='test123')

        response = self.client.post(
            reverse('update_character', args=[self.saved_char.id]),
            json.dumps({'value': 'test'}),  # No field specified
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('No field', data['error'])


class AutoSaveRerollTests(TestCase):
    """Tests for auto-save on re-roll functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reroll_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

    def test_reroll_physical_creates_new_character(self):
        """Test that re-rolling with physical focus creates and saves a new character."""
        self.client.login(username='reroll_test', password='test123')

        # First create a character (stays on generator page now)
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)

        initial_count = SavedCharacter.objects.filter(user=self.user).count()
        self.assertEqual(initial_count, 1)

        # Re-roll with physical focus (stays on generator page)
        response = self.client.post(reverse('generator'), {'action': 'reroll_physical'})
        self.assertEqual(response.status_code, 200)

        # Should have 2 characters now
        new_count = SavedCharacter.objects.filter(user=self.user).count()
        self.assertEqual(new_count, 2)

    def test_reroll_mental_creates_new_character(self):
        """Test that re-rolling with mental focus creates and saves a new character."""
        self.client.login(username='reroll_test', password='test123')

        # First create a character
        self.client.get(reverse('generator'))

        # Re-roll with mental focus (stays on generator page)
        response = self.client.post(reverse('generator'), {'action': 'reroll_mental'})
        self.assertEqual(response.status_code, 200)

        # Should have 2 characters
        self.assertEqual(SavedCharacter.objects.filter(user=self.user).count(), 2)

    def test_reroll_none_creates_new_character(self):
        """Test that re-rolling with no focus creates and saves a new character."""
        self.client.login(username='reroll_test', password='test123')

        # First create a character
        self.client.get(reverse('generator'))

        # Re-roll with no focus (stays on generator page)
        response = self.client.post(reverse('generator'), {'action': 'reroll_none'})
        self.assertEqual(response.status_code, 200)

        # Should have 2 characters
        self.assertEqual(SavedCharacter.objects.filter(user=self.user).count(), 2)


class SessionCharacterOnLoginTests(TestCase):
    """Tests for saving session character when user logs in or registers."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='login_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

    def test_login_saves_session_character(self):
        """Test that logging in saves any character from the session."""
        # First, create a character as anonymous user
        response = self.client.get(reverse('generator'))
        self.assertEqual(response.status_code, 200)

        # Verify session has character data
        self.assertIn('current_character', self.client.session)

        # Now login
        response = self.client.post(reverse('login'), {
            'username': 'login_test',
            'password': 'test123'
        })

        # Should redirect to generator (since we had a character)
        self.assertRedirects(response, reverse('generator'))

        # Character should now be saved in database
        self.assertEqual(SavedCharacter.objects.filter(user=self.user).count(), 1)

        # Session should have saved character ID
        self.assertIn('current_saved_character_id', self.client.session)

    def test_login_without_character_redirects_to_welcome(self):
        """Test that logging in without a session character goes to welcome."""
        # Login directly without visiting generator first
        response = self.client.post(reverse('login'), {
            'username': 'login_test',
            'password': 'test123'
        })

        # Should redirect to welcome
        self.assertRedirects(response, reverse('welcome'))

        # No characters should be created
        self.assertEqual(SavedCharacter.objects.filter(user=self.user).count(), 0)

    def test_login_preserves_experience_data(self):
        """Test that logging in preserves experience data from session."""
        # Create a character and add experience as anonymous user
        self.client.get(reverse('generator'))
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'auto'
        })

        # Verify session has experience data
        self.assertGreater(self.client.session.get('interactive_years', 0), 0)

        # Now login
        self.client.post(reverse('login'), {
            'username': 'login_test',
            'password': 'test123'
        })

        # Character should be saved with experience
        saved_char = SavedCharacter.objects.get(user=self.user)
        self.assertGreater(saved_char.character_data.get('interactive_years', 0), 0)
        self.assertGreater(len(saved_char.character_data.get('interactive_yearly_results', [])), 0)

    def test_register_saves_session_character(self):
        """Test that registering saves any character from the session."""
        # First, create a character as anonymous user
        self.client.get(reverse('generator'))

        # Verify session has character data
        self.assertIn('current_character', self.client.session)

        # Now register a new user (include all required fields)
        response = self.client.post(reverse('register'), {
            'username': 'newusertest',
            'email': 'newtest@example.com',
            'password1': 'Str0ngP@ssw0rd!',
            'password2': 'Str0ngP@ssw0rd!',
            'role': 'player',
        })

        # Should redirect to generator (since we had a character)
        self.assertRedirects(response, reverse('generator'))

        # Character should now be saved in database for new user
        new_user = User.objects.get(username='newusertest')
        self.assertEqual(SavedCharacter.objects.filter(user=new_user).count(), 1)


class GeneratorUnifiedFlowTests(TestCase):
    """Tests for unified generator flow (same behavior for logged-in and anonymous)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='flow_test', password='test123')
        UserProfile.objects.create(user=self.user, roles=['player'])

    def test_logged_in_user_stays_on_generator(self):
        """Test that logged-in users stay on generator page, not redirected."""
        self.client.login(username='flow_test', password='test123')

        # Visit generator
        response = self.client.get(reverse('generator'))

        # Should stay on generator (200), not redirect (302)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'generator/index.html')

    def test_logged_in_reroll_stays_on_generator(self):
        """Test that re-rolling as logged-in user stays on generator."""
        self.client.login(username='flow_test', password='test123')

        # Re-roll
        response = self.client.post(reverse('generator'), {'action': 'reroll_none'}, follow=True)

        # Should end up on generator
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'generator/index.html')

    def test_logged_in_add_experience_stays_on_generator(self):
        """Test that adding experience as logged-in user stays on generator."""
        self.client.login(username='flow_test', password='test123')

        # First visit to create character
        self.client.get(reverse('generator'))

        # Add experience
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 3,
            'track_mode': 'auto'
        }, follow=True)

        # Should end up on generator
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'generator/index.html')

        # Experience should be visible
        self.assertContains(response, 'Year-by-Year Log')

    def test_anonymous_and_logged_in_see_same_ui_elements(self):
        """Test that both anonymous and logged-in users see the same UI elements."""
        # Anonymous user
        anon_response = self.client.get(reverse('generator'))
        # Check for key UI elements that come from the shared component
        self.assertContains(anon_response, 'STR')  # Attributes section
        self.assertContains(anon_response, 'Add Experience')  # Experience button

        # Logged-in user
        self.client.login(username='flow_test', password='test123')
        auth_response = self.client.get(reverse('generator'))
        # Should see the same UI elements
        self.assertContains(auth_response, 'STR')
        self.assertContains(auth_response, 'Add Experience')

    def test_experience_synced_to_database_for_logged_in(self):
        """Test that experience is synced to database for logged-in users."""
        self.client.login(username='flow_test', password='test123')

        # Visit generator (creates saved character)
        self.client.get(reverse('generator'))

        # Add experience
        self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 5,
            'track_mode': 'auto'
        })

        # Verify database has experience
        saved_char = SavedCharacter.objects.filter(user=self.user).first()
        self.assertIsNotNone(saved_char)
        self.assertGreater(saved_char.character_data.get('interactive_years', 0), 0)


class AdminUserManagementTests(TestCase):
    """Tests for admin user management views."""

    def setUp(self):
        """Create test users with different roles."""
        # Admin user
        self.admin = User.objects.create_user(username='admin_test', password='admin123')
        UserProfile.objects.create(user=self.admin, roles=['admin'])

        # Regular player user
        self.player = User.objects.create_user(username='player_test', password='player123', email='player@test.com')
        UserProfile.objects.create(user=self.player, roles=['player'], phone='555-1234', discord_handle='player#1234')

        # DM user
        self.dm = User.objects.create_user(username='dm_test', password='dm123')
        UserProfile.objects.create(user=self.dm, roles=['dm'])

        # Create a character for the player
        self.player_char = SavedCharacter.objects.create(
            user=self.player,
            name='Test Character',
            character_data={
                'name': 'Test Character',
                'attributes': {'STR': 12, 'DEX': 14, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10},
                'provenance_social_class': 'Commoner',
                'provenance_sub_class': 'Laborer',
                'wealth_level': 'Moderate',
            }
        )

        self.client = Client()

    def test_manage_users_requires_admin(self):
        """Test that manage users page requires admin role."""
        # Anonymous user
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('login'))

        # Player can't access
        self.client.login(username='player_test', password='player123')
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('welcome'))

        # DM can't access
        self.client.login(username='dm_test', password='dm123')
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('welcome'))

        # Admin can access
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)

    def test_manage_users_shows_all_users(self):
        """Test that manage users page shows all users."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('manage_users'))
        self.assertContains(response, 'admin_test')
        self.assertContains(response, 'player_test')
        self.assertContains(response, 'dm_test')

    def test_manage_users_shows_characters_by_user(self):
        """Test that manage users page shows characters grouped by user."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('manage_users'))
        self.assertContains(response, 'Test Character')
        self.assertContains(response, 'player_test')

    def test_edit_user_requires_admin(self):
        """Test that edit user page requires admin role."""
        # Player can't access
        self.client.login(username='player_test', password='player123')
        response = self.client.get(reverse('edit_user', args=[self.dm.id]))
        self.assertRedirects(response, reverse('welcome'))

        # Admin can access
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('edit_user', args=[self.player.id]))
        self.assertEqual(response.status_code, 200)

    def test_edit_user_shows_user_data(self):
        """Test that edit user page shows correct user data."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('edit_user', args=[self.player.id]))
        self.assertContains(response, 'player_test')
        self.assertContains(response, 'player@test.com')
        self.assertContains(response, '555-1234')
        self.assertContains(response, 'player#1234')

    def test_edit_user_updates_username(self):
        """Test that admin can update a user's username."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('edit_user', args=[self.player.id]), {
            'username': 'new_player_name',
            'email': 'player@test.com',
            'roles': ['player'],
            'phone': '',
            'discord_handle': '',
            'preferred_contact': 'email',
        })
        self.assertRedirects(response, reverse('manage_users'))
        self.player.refresh_from_db()
        self.assertEqual(self.player.username, 'new_player_name')

    def test_edit_user_updates_roles(self):
        """Test that admin can update a user's roles."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('edit_user', args=[self.player.id]), {
            'username': 'player_test',
            'email': 'player@test.com',
            'roles': ['player', 'dm'],
            'phone': '',
            'discord_handle': '',
            'preferred_contact': 'email',
        })
        self.assertRedirects(response, reverse('manage_users'))
        self.player.profile.refresh_from_db()
        self.assertIn('player', self.player.profile.roles)
        self.assertIn('dm', self.player.profile.roles)

    def test_edit_user_updates_password(self):
        """Test that admin can update a user's password."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('edit_user', args=[self.player.id]), {
            'username': 'player_test',
            'email': 'player@test.com',
            'new_password': 'newpassword456',
            'roles': ['player'],
            'phone': '',
            'discord_handle': '',
            'preferred_contact': 'email',
        })
        self.assertRedirects(response, reverse('manage_users'))
        # Verify new password works
        self.client.logout()
        self.assertTrue(self.client.login(username='player_test', password='newpassword456'))

    def test_edit_user_prevents_duplicate_username(self):
        """Test that editing to a duplicate username is prevented."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('edit_user', args=[self.player.id]), {
            'username': 'dm_test',  # Already taken
            'email': 'player@test.com',
            'roles': ['player'],
            'phone': '',
            'discord_handle': '',
            'preferred_contact': 'email',
        })
        # Should redirect back to edit page with error
        self.assertRedirects(response, reverse('edit_user', args=[self.player.id]))
        self.player.refresh_from_db()
        self.assertEqual(self.player.username, 'player_test')  # Unchanged

    def test_edit_user_not_found(self):
        """Test edit user with non-existent user ID."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('edit_user', args=[99999]))
        self.assertRedirects(response, reverse('manage_users'))

    def test_delete_user_requires_admin(self):
        """Test that delete user requires admin role."""
        self.client.login(username='player_test', password='player123')
        response = self.client.post(reverse('delete_user', args=[self.dm.id]))
        self.assertRedirects(response, reverse('welcome'))

        # Verify user not deleted
        self.assertTrue(User.objects.filter(id=self.dm.id).exists())

    def test_delete_user_success(self):
        """Test that admin can delete a user."""
        self.client.login(username='admin_test', password='admin123')
        player_id = self.player.id
        response = self.client.post(reverse('delete_user', args=[player_id]))
        self.assertRedirects(response, reverse('manage_users'))
        # Verify user deleted
        self.assertFalse(User.objects.filter(id=player_id).exists())

    def test_delete_user_cascades_to_characters(self):
        """Test that deleting a user also deletes their characters."""
        self.client.login(username='admin_test', password='admin123')
        char_id = self.player_char.id
        player_id = self.player.id
        response = self.client.post(reverse('delete_user', args=[player_id]))
        self.assertRedirects(response, reverse('manage_users'))
        # Verify character also deleted
        self.assertFalse(SavedCharacter.objects.filter(id=char_id).exists())

    def test_delete_user_cannot_delete_self(self):
        """Test that admin cannot delete their own account."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('delete_user', args=[self.admin.id]))
        self.assertRedirects(response, reverse('manage_users'))
        # Verify admin still exists
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

    def test_delete_user_not_found(self):
        """Test delete user with non-existent user ID."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('delete_user', args=[99999]))
        self.assertRedirects(response, reverse('manage_users'))


class AdminDeleteCharacterTests(TestCase):
    """Tests for admin character deletion."""

    def setUp(self):
        """Create test users and characters."""
        self.admin = User.objects.create_user(username='admin_test', password='admin123')
        UserProfile.objects.create(user=self.admin, roles=['admin'])

        self.player = User.objects.create_user(username='player_test', password='player123')
        UserProfile.objects.create(user=self.player, roles=['player'])

        self.player_char = SavedCharacter.objects.create(
            user=self.player,
            name='Player Character',
            character_data={
                'name': 'Player Character',
                'attributes': {'STR': 12, 'DEX': 14, 'INT': 10, 'WIS': 10, 'CON': 12, 'CHR': 10},
            }
        )

        self.client = Client()

    def test_admin_delete_character_requires_admin(self):
        """Test that admin delete character requires admin role."""
        self.client.login(username='player_test', password='player123')
        response = self.client.post(reverse('admin_delete_character', args=[self.player_char.id]))
        self.assertRedirects(response, reverse('welcome'))
        # Verify character not deleted
        self.assertTrue(SavedCharacter.objects.filter(id=self.player_char.id).exists())

    def test_admin_delete_character_success(self):
        """Test that admin can delete any character."""
        self.client.login(username='admin_test', password='admin123')
        char_id = self.player_char.id
        response = self.client.post(reverse('admin_delete_character', args=[char_id]))
        self.assertRedirects(response, reverse('manage_users'))
        # Verify character deleted
        self.assertFalse(SavedCharacter.objects.filter(id=char_id).exists())

    def test_admin_delete_character_not_found(self):
        """Test admin delete character with non-existent character ID."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('admin_delete_character', args=[99999]))
        self.assertRedirects(response, reverse('manage_users'))


class ChangeUserRoleTests(TestCase):
    """Tests for change user role functionality."""

    def setUp(self):
        """Create test users."""
        self.admin = User.objects.create_user(username='admin_test', password='admin123')
        UserProfile.objects.create(user=self.admin, roles=['admin'])

        self.player = User.objects.create_user(username='player_test', password='player123')
        UserProfile.objects.create(user=self.player, roles=['player'])

        self.client = Client()

    def test_change_role_requires_admin(self):
        """Test that changing roles requires admin."""
        self.client.login(username='player_test', password='player123')
        response = self.client.post(reverse('change_user_role', args=[self.player.id]), {
            'roles': ['admin'],
        })
        self.assertRedirects(response, reverse('welcome'))
        # Verify role not changed
        self.player.profile.refresh_from_db()
        self.assertNotIn('admin', self.player.profile.roles)

    def test_change_role_success(self):
        """Test that admin can change user roles."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('change_user_role', args=[self.player.id]), {
            'roles': ['player', 'dm'],
        })
        self.assertRedirects(response, reverse('manage_users'))
        self.player.profile.refresh_from_db()
        self.assertIn('player', self.player.profile.roles)
        self.assertIn('dm', self.player.profile.roles)

    def test_change_role_removes_roles(self):
        """Test that admin can remove all roles."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('change_user_role', args=[self.player.id]), {
            # No roles selected
        })
        self.assertRedirects(response, reverse('manage_users'))
        self.player.profile.refresh_from_db()
        self.assertEqual(self.player.profile.roles, [])

    def test_change_role_invalid_user(self):
        """Test change role with invalid user ID."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('change_user_role', args=[99999]), {
            'roles': ['player'],
        })
        self.assertRedirects(response, reverse('manage_users'))

    def test_change_role_ignores_invalid_roles(self):
        """Test that invalid role values are filtered out."""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(reverse('change_user_role', args=[self.player.id]), {
            'roles': ['player', 'superuser', 'root'],  # Invalid roles
        })
        self.assertRedirects(response, reverse('manage_users'))
        self.player.profile.refresh_from_db()
        self.assertEqual(self.player.profile.roles, ['player'])


class InputValidationTests(TestCase):
    """Tests for input validation."""

    def setUp(self):
        self.client = Client()

    def test_experience_years_validation_negative(self):
        """Test that negative years are clamped to minimum."""
        self.client.get(reverse('generator'))
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': -5,
            'track_mode': 'auto',
        })
        # Should not crash and should add at least 1 year
        self.assertRedirects(response, reverse('generator'))
        years = self.client.session.get('interactive_years', 0)
        self.assertGreaterEqual(years, 1)

    def test_experience_years_validation_too_large(self):
        """Test that extremely large years are clamped to maximum."""
        self.client.get(reverse('generator'))
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 1000,
            'track_mode': 'auto',
        })
        # Should not crash
        self.assertRedirects(response, reverse('generator'))
        # Years should be clamped to max (50)
        years = self.client.session.get('interactive_years', 0)
        self.assertLessEqual(years, 50)

    def test_experience_years_validation_non_numeric(self):
        """Test that non-numeric years use default value."""
        self.client.get(reverse('generator'))
        response = self.client.post(reverse('generator'), {
            'action': 'add_experience',
            'years': 'abc',
            'track_mode': 'auto',
        })
        # Should not crash and use default
        self.assertRedirects(response, reverse('generator'))
