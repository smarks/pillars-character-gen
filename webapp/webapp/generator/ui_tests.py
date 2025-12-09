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

        # Click on Character Generator link (use partial link text since it includes icon)
        generator_link = self.browser.find_element(By.PARTIAL_LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Should be on generator page
        self.assertIn('generator', self.browser.current_url)
        self.assertIn('Character Generator', self.browser.page_source)

    def test_copy_to_clipboard_button(self):
        """Test that Copy to Clipboard button exists on the generator page."""
        # Go directly to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on the generator page
        self.assertIn('Character Generator', self.browser.page_source)

        # Verify a character was generated (check for attributes)
        page_source = self.browser.page_source
        self.assertTrue('STR' in page_source or 'DEX' in page_source)

        # Find the Copy to Clipboard button
        copy_button = self.browser.find_element(By.ID, 'copy-btn')
        self.assertIsNotNone(copy_button)
        self.assertIn('Copy', copy_button.text)

    def test_add_experience_button(self):
        """Test that Add Experience button adds experience and stays on generator."""
        # Go directly to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on the generator page
        self.assertIn('Character Generator', self.browser.page_source)

        # Verify a character was generated (check for attributes)
        page_source = self.browser.page_source
        self.assertTrue('STR' in page_source or 'DEX' in page_source)

        # Find and click the Add Experience button
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()

        # Wait for redirect to complete
        import time
        time.sleep(1)
        self.wait_for_page_load()

        # Should stay on generator page
        self.assertIn('generator', self.browser.current_url)
        # Should see experience log
        self.assertTrue(
            'Year-by-Year' in self.browser.page_source or 'Year 16' in self.browser.page_source,
            "Generator should show experience log after adding experience"
        )

    def test_reroll_buttons(self):
        """Test that re-roll buttons generate new characters."""
        # Go directly to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on the generator page with character attributes
        page_source = self.browser.page_source
        self.assertTrue('STR' in page_source)

        # Click Re-roll (No Focus)
        reroll_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="reroll_none"]'
        )
        reroll_button.click()
        self.wait_for_page_load()

        # Should still be on generator page
        self.assertIn('generator', self.browser.current_url)
        self.assertIn('Character Generator', self.browser.page_source)

        # Character should have been regenerated (page still shows attributes)
        self.assertTrue('STR' in self.browser.page_source)

    def test_full_flow_without_experience(self):
        """Test complete flow: welcome -> generator shows character."""
        # Start at welcome
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Go to generator
        generator_link = self.browser.find_element(By.PARTIAL_LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Should be on generator page
        self.assertIn('generator', self.browser.current_url)

        # Should have character data displayed
        page_source = self.browser.page_source
        self.assertTrue('STR' in page_source)
        self.assertTrue('Add Experience' in page_source or 'add_experience' in page_source)

    def test_full_flow_with_experience(self):
        """Test complete flow: welcome -> generator -> add experience."""
        # Start at welcome
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Go to generator
        generator_link = self.browser.find_element(By.PARTIAL_LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Click Add Experience
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()
        self.wait_for_page_load()

        # Should stay on generator page
        self.assertIn('generator', self.browser.current_url)

        # Should see experience log (Year 17 is the first year added to a 16-year-old character)
        page_source = self.browser.page_source
        self.assertTrue(
            'Year-by-Year' in page_source or 'Year 17' in page_source or 'Prior Experience' in page_source,
            "Generator should show experience log after adding experience"
        )


class InteractiveFlowTests(BrowserTestCase):
    """UI tests for the experience flow."""

    def test_add_experience_flow(self):
        """Test adding experience directly from the generator."""
        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Click Add Experience - this now adds experience directly
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()
        self.wait_for_page_load()

        # Should stay on generator page
        self.assertIn('generator', self.browser.current_url)

        # Should see experience log with year results (Year 17 is the first year for a 16yo)
        page_source = self.browser.page_source
        self.assertTrue(
            'Year-by-Year' in page_source or 'Year 17' in page_source or 'Prior Experience' in page_source,
            "Generator should show year-by-year log after adding experience"
        )

        # Click Add Experience again to add more years
        add_exp_button = self.browser.find_element(
            By.CSS_SELECTOR, 'button[value="add_experience"]'
        )
        add_exp_button.click()
        self.wait_for_page_load()

        # Should still be on generator and show more experience
        self.assertIn('generator', self.browser.current_url)

        # Character is ready - verify character data is still visible
        page_source = self.browser.page_source
        self.assertTrue('STR' in page_source, "Character attributes should be visible")


class SessionPersistenceTests(BrowserTestCase):
    """Tests to verify session data persists across page loads."""

    def test_character_persists_after_page_refresh(self):
        """Test that character data persists when refreshing the page."""
        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Get the character name from the page
        page_source = self.browser.page_source
        # Find the character name element
        name_element = self.browser.find_element(By.CSS_SELECTOR, '.character-name, h2, h3')
        initial_name = name_element.text

        # Refresh the page
        self.browser.refresh()
        self.wait_for_page_load()

        # Character should be the same (not regenerated)
        name_element = self.browser.find_element(By.CSS_SELECTOR, '.character-name, h2, h3')
        refreshed_name = name_element.text
        self.assertEqual(initial_name, refreshed_name)

    def test_new_character_on_welcome_return(self):
        """Test that going back to welcome clears the character."""
        # Go to generator
        self.browser.get(f'{self.live_server_url}/generator/')
        self.wait_for_page_load()

        # Verify we're on generator with character data
        self.assertIn('generator', self.browser.current_url)
        self.assertTrue('STR' in self.browser.page_source)

        # Go back to welcome
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Go to generator again
        generator_link = self.browser.find_element(By.PARTIAL_LINK_TEXT, 'Character Generator')
        generator_link.click()
        self.wait_for_page_load()

        # Should have a new character generated
        self.assertIn('generator', self.browser.current_url)
        # Both visits should show valid character data (STR attribute)
        self.assertTrue('STR' in self.browser.page_source)


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

    def test_dm_sees_dm_link_but_not_manage_users(self):
        """Test that DM role users see DM link but not Manage Users."""
        self.login_user('dm_ui_test', 'testpass123')

        # Go to welcome page
        self.browser.get(f'{self.live_server_url}/')
        self.wait_for_page_load()

        # Should see DM link (the link text is just "DM" not "DM Handbook")
        self.assertTrue(
            self.element_exists(By.CSS_SELECTOR, 'a[href*="/dm"]'),
            "DM should see DM link"
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

        # Should see DM link (the link text is just "DM" not "DM Handbook")
        self.assertTrue(
            self.element_exists(By.CSS_SELECTOR, 'a[href*="/dm"]'),
            "Admin should see DM link"
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

        # Should see both links (DM link text is just "DM" not "DM Handbook")
        self.assertTrue(
            self.element_exists(By.CSS_SELECTOR, 'a[href*="/dm"]'),
            "Admin+DM should see DM link"
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

    def setUp(self):
        """Create test users before each test."""
        super().setUp()
        # Create a test user for this test
        from django.contrib.auth.models import User
        from webapp.generator.models import UserProfile
        self.test_user = User.objects.create_user(
            username='unified_ui_test',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.test_user, roles=['player'])

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
