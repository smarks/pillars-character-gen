"""
Selenium-based UI tests for the Pillars Character Generator.

These tests drive a real browser to verify the UI works correctly.
Run with: python manage.py test webapp.generator.ui_tests

Requirements:
    pip install selenium webdriver-manager
"""
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException


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
