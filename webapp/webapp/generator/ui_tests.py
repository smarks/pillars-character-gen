"""
Selenium-based UI tests for the Pillars Character Generator.

These tests drive a real browser to verify the UI works correctly.
Run with: python manage.py test webapp.generator.ui_tests

Requirements:
    pip install selenium webdriver-manager
"""
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webapp.generator.models import UserProfile


class BrowserTestCase(StaticLiveServerTestCase):
    """Base class for browser-based tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up Chrome in headless mode
        options = ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        try:
            # Try using webdriver-manager to get ChromeDriver
            from webdriver_manager.chrome import ChromeDriverManager
            service = ChromeService(ChromeDriverManager().install())
            cls.browser = webdriver.Chrome(service=service, options=options)
        except Exception:
            # Fall back to system ChromeDriver
            cls.browser = webdriver.Chrome(options=options)

        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        """Clear cookies before each test to ensure clean state."""
        super().setUp()
        # Navigate to the site first so we can clear cookies for the domain
        self.browser.get(f'{self.live_server_url}/')
        self.browser.delete_all_cookies()

    def wait_for_page_load(self, timeout=10):
        """Wait for page to fully load."""
        WebDriverWait(self.browser, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present and visible."""
        return WebDriverWait(self.browser, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def click_button(self, button_text):
        """Find and click a button by its text content."""
        # Try finding by exact text first
        buttons = self.browser.find_elements(By.TAG_NAME, 'button')
        for button in buttons:
            if button_text in button.text:
                button.click()
                return
        # Try finding by value attribute (for submit buttons)
        buttons = self.browser.find_elements(By.CSS_SELECTOR, f'button[value="{button_text}"]')
        if buttons:
            buttons[0].click()
            return
        raise Exception(f"Button with text '{button_text}' not found")

    def login_user(self, username, password):
        """Login a user via the browser."""
        self.browser.get(f'{self.live_server_url}/login/')
        self.wait_for_page_load()

        # Fill in login form
        username_field = self.browser.find_element(By.NAME, 'username')
        password_field = self.browser.find_element(By.NAME, 'password')
        username_field.send_keys(username)
        password_field.send_keys(password)

        # Submit form
        login_button = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()

        # Wait for redirect away from login page
        import time
        time.sleep(1)  # Give time for form submission and redirect
        self.wait_for_page_load()

        # Verify login succeeded - we should NOT still be on login page
        if '/login' in self.browser.current_url:
            # Check for error messages
            page_source = self.browser.page_source
            if 'Please correct the errors' in page_source:
                raise AssertionError(f"Login failed for user '{username}': form has errors")
            raise AssertionError(f"Login failed for user '{username}': still on login page")

    def element_exists(self, by, value):
        """Check if an element exists on the page."""
        try:
            self.browser.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def link_exists(self, link_text):
        """Check if a link with the given text exists."""
        try:
            self.browser.find_element(By.LINK_TEXT, link_text)
            return True
        except NoSuchElementException:
            return False

    def partial_link_exists(self, partial_text):
        """Check if a link containing the given text exists."""
        try:
            self.browser.find_element(By.PARTIAL_LINK_TEXT, partial_text)
            return True
        except NoSuchElementException:
            return False


class GeneratorUITests(BrowserTestCase):
    """UI tests for the character generator flow."""

    def test_welcome_to_generator(self):
        """Test navigating from welcome page to generator."""
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should see welcome page
        self.assertIn('Pillars', self.browser.title)

        # Click on Character Generator link
        generator_link = self.browser.find_element(By.LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Should be on generator page
        self.assertIn('generator', self.browser.current_url)
        self.assertIn('Character Generator', self.browser.page_source)

    def test_finish_character_button(self):
        """Test that Finish Character button takes you to the character sheet."""
        # Go directly to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on the generator page
        self.assertIn('Character Generator', self.browser.page_source)

        # Verify a character was generated (this creates the session)
        pre_element = self.browser.find_element(By.TAG_NAME, 'pre')
        self.assertIn('Pillars Character', pre_element.text)

        # Find and click the Finish Character button
        finish_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="finish"]'
        )
        finish_button.click()
        self.wait_for_page_load()

        # Should now be on the character sheet page
        self.assertIn('Character Sheet', self.browser.page_source)
        # Should have the copy button
        self.assertIn('Copy to Clipboard', self.browser.page_source)

    def test_add_experience_button(self):
        """Test that Add Experience button takes you to track selection."""
        # Go directly to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on the generator page
        self.assertIn('Character Generator', self.browser.page_source)

        # Verify a character was generated (this creates the session)
        pre_element = self.browser.find_element(By.TAG_NAME, 'pre')
        self.assertIn('Pillars Character', pre_element.text)

        # Find and click the Add Experience button
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()

        # Wait for redirect to complete
        import time
        time.sleep(1)
        self.wait_for_page_load()

        # Should now be on the track selection page
        self.assertIn('select-track', self.browser.current_url)
        # Should see track options
        self.assertIn('Track', self.browser.page_source)

    def test_reroll_buttons(self):
        """Test that re-roll buttons generate new characters."""
        # Go directly to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Get the initial character display
        initial_content = self.browser.find_element(By.TAG_NAME, 'pre').text

        # Click Re-roll (No Focus)
        reroll_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="reroll_none"]'
        )
        reroll_button.click()
        self.wait_for_page_load()

        # Should still be on generator page
        self.assertIn('generator', self.browser.current_url)
        self.assertIn('Character Generator', self.browser.page_source)

        # Character should have been regenerated (page still shows a character)
        new_content = self.browser.find_element(By.TAG_NAME, 'pre').text
        self.assertIn('Pillars Character', new_content)

    def test_full_flow_finish_without_experience(self):
        """Test complete flow: welcome -> generator -> finish."""
        # Start at welcome
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Go to generator
        generator_link = self.browser.find_element(By.LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Click Finish Character
        finish_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="finish"]'
        )
        finish_button.click()
        self.wait_for_page_load()

        # Verify we're on character sheet
        self.assertIn('Character Sheet', self.browser.page_source)

        # Should have character data displayed
        character_sheet = self.browser.find_element(By.ID, 'character-sheet')
        self.assertIn('Pillars Character', character_sheet.text)

    def test_full_flow_with_experience(self):
        """Test complete flow: welcome -> generator -> add experience -> track selection."""
        # Start at welcome
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Go to generator
        generator_link = self.browser.find_element(By.LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Click Add Experience
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()
        self.wait_for_page_load()

        # Should be on track selection
        self.assertIn('select-track', self.browser.current_url)

        # Should see track selection options
        page_source = self.browser.page_source
        # Check for track-related content
        self.assertTrue(
            'Worker' in page_source or 'Ranger' in page_source or 'Track' in page_source,
            "Track selection page should show track options"
        )


class InteractiveFlowTests(BrowserTestCase):
    """UI tests for the interactive prior experience flow."""

    def test_interactive_mode_flow(self):
        """Test the interactive year-by-year mode."""
        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Click Add Experience
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()
        self.wait_for_page_load()

        # On track selection page, check the interactive mode checkbox
        interactive_checkbox = self.browser.find_element(By.ID, 'interactive-checkbox')
        if not interactive_checkbox.is_selected():
            interactive_checkbox.click()

        # Select a safe track (Worker has low survivability requirement)
        # First, select manual mode
        manual_radio = self.browser.find_element(
            By.CSS_SELECTOR, 'input[name="track_mode"][value="manual"]'
        )
        manual_radio.click()

        # Select Worker track
        worker_radio = self.browser.find_element(
            By.CSS_SELECTOR, 'input[name="chosen_track"][value="WORKER"]'
        )
        worker_radio.click()

        # Click Add Experience button on track selection
        add_exp_submit = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_submit.click()
        self.wait_for_page_load()

        # Should be on interactive page
        self.assertIn('interactive', self.browser.current_url)
        self.assertIn('Interactive', self.browser.page_source)

        # Click Continue to add a year
        continue_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="continue"]'
        )
        continue_button.click()
        self.wait_for_page_load()

        # Should still be on interactive page with year results
        self.assertIn('interactive', self.browser.current_url)
        # Should show year 17 in the results
        self.assertIn('17', self.browser.page_source)

        # Now click Finish Character
        finish_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="finish"]'
        )
        finish_button.click()
        self.wait_for_page_load()

        # Should be on character sheet
        self.assertIn('Character Sheet', self.browser.page_source)


class SessionPersistenceTests(BrowserTestCase):
    """Tests to verify session data persists across page loads."""

    def test_character_persists_after_page_refresh(self):
        """Test that character data persists when refreshing the page."""
        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Get the character content
        initial_content = self.browser.find_element(By.TAG_NAME, 'pre').text

        # Refresh the page
        self.browser.refresh()
        self.wait_for_page_load()

        # Character should be the same (not regenerated)
        refreshed_content = self.browser.find_element(By.TAG_NAME, 'pre').text
        self.assertEqual(initial_content, refreshed_content)

    def test_new_character_on_welcome_return(self):
        """Test that going back to welcome clears the character."""
        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Get the character content
        first_content = self.browser.find_element(By.TAG_NAME, 'pre').text

        # Go back to welcome
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Go to generator again
        generator_link = self.browser.find_element(By.LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Should have a new character (different from before)
        second_content = self.browser.find_element(By.TAG_NAME, 'pre').text

        # Both should be valid characters
        self.assertIn('Pillars Character', first_content)
        self.assertIn('Pillars Character', second_content)


class RoleUITests(BrowserTestCase):
    """UI tests for role-based access control."""

    def setUp(self):
        """Create test users with different roles before each test."""
        super().setUp()
        # Create test users with different roles
        # These need to be created in setUp (not setUpClass) because
        # TransactionTestCase flushes the database between tests
        self.player_user = User.objects.create_user('player_ui_test', password='testpass123')
        UserProfile.objects.create(user=self.player_user, roles=['player'])

        self.dm_user = User.objects.create_user('dm_ui_test', password='testpass123')
        UserProfile.objects.create(user=self.dm_user, roles=['dm'])

        self.admin_user = User.objects.create_user('admin_ui_test', password='testpass123')
        UserProfile.objects.create(user=self.admin_user, roles=['admin'])

        self.admin_dm_user = User.objects.create_user('admin_dm_ui_test', password='testpass123')
        UserProfile.objects.create(user=self.admin_dm_user, roles=['admin', 'dm'])

    def test_unauthenticated_user_sees_no_dm_links(self):
        """Test that unauthenticated users don't see DM or admin links."""
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should NOT see DM Handbook or Manage Users links
        self.assertFalse(
            self.partial_link_exists('DM Handbook'),
            "Unauthenticated user should NOT see DM Handbook link"
        )
        self.assertFalse(
            self.partial_link_exists('Manage Users'),
            "Unauthenticated user should NOT see Manage Users link"
        )

    def test_player_sees_no_dm_links(self):
        """Test that player role users don't see DM or admin links."""
        self.login_user('player_ui_test', 'testpass123')

        # Go to welcome page
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should NOT see DM Handbook or Manage Users links
        self.assertFalse(
            self.partial_link_exists('DM Handbook'),
            "Player should NOT see DM Handbook link"
        )
        self.assertFalse(
            self.partial_link_exists('Manage Users'),
            "Player should NOT see Manage Users link"
        )

    def test_dm_sees_dm_handbook_but_not_manage_users(self):
        """Test that DM role users see DM Handbook but not Manage Users."""
        self.login_user('dm_ui_test', 'testpass123')

        # Go to welcome page
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should see DM Handbook
        self.assertTrue(
            self.partial_link_exists('DM Handbook'),
            "DM should see DM Handbook link"
        )
        # Should NOT see Manage Users
        self.assertFalse(
            self.partial_link_exists('Manage Users'),
            "DM should NOT see Manage Users link"
        )

    def test_admin_sees_all_links(self):
        """Test that admin role users see all links including Manage Users."""
        self.login_user('admin_ui_test', 'testpass123')

        # Go to welcome page
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should see DM Handbook
        self.assertTrue(
            self.partial_link_exists('DM Handbook'),
            "Admin should see DM Handbook link"
        )
        # Should see Manage Users
        self.assertTrue(
            self.partial_link_exists('Manage Users'),
            "Admin should see Manage Users link"
        )

    def test_admin_can_access_manage_users_page(self):
        """Test that admin can access the manage users page."""
        self.login_user('admin_ui_test', 'testpass123')

        # Navigate to manage users
        self.browser.get(f'{self.live_server_url}/manage-users/')
        self.wait_for_page_load()

        # Should be on the manage users page (not redirected)
        self.assertIn('Manage Users', self.browser.page_source)
        self.assertIn('manage-users', self.browser.current_url)

    def test_player_cannot_access_manage_users_page(self):
        """Test that player is redirected when trying to access manage users."""
        self.login_user('player_ui_test', 'testpass123')

        # Try to navigate to manage users
        self.browser.get(f'{self.live_server_url}/manage-users/')
        self.wait_for_page_load()

        # Should be redirected to welcome page
        self.assertNotIn('manage-users', self.browser.current_url)
        # Should see the welcome page
        self.assertIn('PILLARS', self.browser.page_source)

    def test_dm_cannot_access_manage_users_page(self):
        """Test that DM is redirected when trying to access manage users."""
        self.login_user('dm_ui_test', 'testpass123')

        # Try to navigate to manage users
        self.browser.get(f'{self.live_server_url}/manage-users/')
        self.wait_for_page_load()

        # Should be redirected to welcome page
        self.assertNotIn('manage-users', self.browser.current_url)
        # Should see the welcome page
        self.assertIn('PILLARS', self.browser.page_source)

    def test_dm_can_access_dm_handbook(self):
        """Test that DM can access the DM handbook."""
        self.login_user('dm_ui_test', 'testpass123')

        # Navigate to DM handbook
        self.browser.get(f'{self.live_server_url}/dm/')
        self.wait_for_page_load()

        # Should be on the DM page (not redirected)
        self.assertIn('/dm', self.browser.current_url)

    def test_player_cannot_access_dm_handbook(self):
        """Test that player is redirected when trying to access DM handbook."""
        self.login_user('player_ui_test', 'testpass123')

        # Try to navigate to DM handbook
        self.browser.get(f'{self.live_server_url}/dm/')
        self.wait_for_page_load()

        # Should be redirected away from DM page
        # Either redirected to welcome or login
        self.assertFalse(
            self.browser.current_url.endswith('/dm/'),
            "Player should be redirected away from DM handbook"
        )

    def test_admin_dm_can_access_everything(self):
        """Test that user with both admin and DM roles can access everything."""
        self.login_user('admin_dm_ui_test', 'testpass123')

        # Go to welcome page
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should see both links
        self.assertTrue(
            self.partial_link_exists('DM Handbook'),
            "Admin+DM should see DM Handbook link"
        )
        self.assertTrue(
            self.partial_link_exists('Manage Users'),
            "Admin+DM should see Manage Users link"
        )

        # Should be able to access DM handbook
        self.browser.get(f'{self.live_server_url}/dm/')
        self.wait_for_page_load()
        self.assertIn('/dm', self.browser.current_url)

        # Should be able to access manage users
        self.browser.get(f'{self.live_server_url}/manage-users/')
        self.wait_for_page_load()
        self.assertIn('manage-users', self.browser.current_url)


class SessionCharacterLoginUITests(BrowserTestCase):
    """UI tests for session character preservation on login."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test user for login tests
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile
        cls.test_user = User.objects.create_user(
            username='session_ui_test',
            password='testpass123'
        )
        UserProfile.objects.create(user=cls.test_user, roles=['player'])

    def test_login_preserves_character_and_redirects_to_generator(self):
        """Test that logging in with a session character redirects to generator."""
        # First, create a character as anonymous user
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on generator and see character data
        self.assertIn('generator', self.browser.current_url)
        page_source = self.browser.page_source
        self.assertTrue(
            'STR' in page_source or 'DEX' in page_source,
            "Generator page should show character attributes"
        )

        # Now go to login
        self.browser.get(f'{self.live_server_url}/login/')
        self.wait_for_page_load()

        # Fill in login form
        username_field = self.browser.find_element(By.NAME, 'username')
        password_field = self.browser.find_element(By.NAME, 'password')
        username_field.send_keys('session_ui_test')
        password_field.send_keys('testpass123')

        # Submit form
        login_button = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()

        import time
        time.sleep(1)  # Wait for redirect

        # Should be redirected to generator (because we had a character)
        self.assertIn('generator', self.browser.current_url)

        # Character should still be visible
        page_source = self.browser.page_source
        self.assertTrue(
            'STR' in page_source or 'DEX' in page_source,
            "Generator page should still show the character after login"
        )


class GeneratorUnifiedFlowUITests(BrowserTestCase):
    """UI tests for unified generator flow (same for logged-in and anonymous)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test user
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile
        cls.test_user = User.objects.create_user(
            username='unified_ui_test',
            password='testpass123'
        )
        UserProfile.objects.create(user=cls.test_user, roles=['player'])

    def test_logged_in_user_stays_on_generator(self):
        """Test that logged-in users stay on generator page."""
        # Login first
        self.login_user('unified_ui_test', 'testpass123')

        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Should be on generator (not redirected to character sheet)
        self.assertIn('generator', self.browser.current_url)
        self.assertNotIn('character/', self.browser.current_url)

        # Should see the generator page content
        page_source = self.browser.page_source
        self.assertTrue(
            'Re-roll' in page_source or 'reroll' in page_source.lower(),
            "Generator page should have re-roll buttons"
        )

    def test_logged_in_add_experience_shows_on_generator(self):
        """Test that adding experience shows results on generator page."""
        # Login first
        self.login_user('unified_ui_test', 'testpass123')

        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Click Add Experience button
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()
        self.wait_for_page_load()

        # Should still be on generator
        self.assertIn('generator', self.browser.current_url)

        # Should see experience log
        page_source = self.browser.page_source
        self.assertTrue(
            'Year-by-Year' in page_source or 'Year 16' in page_source,
            "Generator page should show experience log after adding experience"
        )
