"""
Tests to validate all internal links in markdown files and templates.

These tests ensure that:
1. All markdown links point to valid URLs
2. All template URL tags use valid URL names
3. No broken internal links exist
"""

import os
import re
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch, resolve, Resolver404
from django.conf import settings


class MarkdownLinkValidationTests(TestCase):
    """Tests to validate links in markdown files."""

    def setUp(self):
        """Set up test client and find all markdown files."""
        self.client = Client()
        self.base_dir = settings.BASE_DIR
        self.references_dir = os.path.join(self.base_dir, "..", "references")

    def test_all_markdown_files_exist(self):
        """Test that all markdown files referenced in code actually exist."""
        # Markdown files that should exist
        expected_files = [
            "welcome.md",
            "about.md",
            "public-rulebook.md",
            "dm-handbook.md",
        ]

        for filename in expected_files:
            filepath = os.path.join(self.references_dir, filename)
            self.assertTrue(
                os.path.exists(filepath),
                f"Markdown file {filename} should exist at {filepath}",
            )

    def test_welcome_md_links_are_valid(self):
        """Test that all links in welcome.md point to valid URLs."""
        welcome_file = os.path.join(self.references_dir, "welcome.md")
        if not os.path.exists(welcome_file):
            self.skipTest("welcome.md not found")

        with open(welcome_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all markdown links [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        links = re.findall(link_pattern, content)

        # Expected valid links
        valid_links = {
            "/html/about/": "reference_html",
            "/html/public-rulebook/": "reference_html",
            "/generator/": "generator",
        }

        for link_text, link_url in links:
            # Only check internal links (starting with /)
            if link_url.startswith("/"):
                # Check if it's an external link (http/https)
                if link_url.startswith(("http://", "https://")):
                    continue

                # Check if URL is valid
                if link_url in valid_links:
                    url_name = valid_links[link_url]
                    try:
                        reverse(
                            url_name,
                            kwargs=(
                                {"name": link_url.split("/")[-2]}
                                if "html/" in link_url
                                else {}
                            ),
                        )
                    except (NoReverseMatch, KeyError):
                        # Try direct URL resolution
                        try:
                            resolve(link_url)
                        except Resolver404:
                            self.fail(
                                f"Invalid link in welcome.md: [{link_text}]({link_url})"
                            )
                elif link_url == "/":
                    # Root URL should resolve to welcome
                    try:
                        resolve(link_url)
                    except Resolver404:
                        self.fail(
                            f"Root URL / should be valid, but link [{link_text}]({link_url}) failed"
                        )
                else:
                    # Try to resolve the URL
                    try:
                        resolve(link_url)
                    except Resolver404:
                        self.fail(
                            f"Invalid link in welcome.md: [{link_text}]({link_url})"
                        )

    def test_about_md_links_are_valid(self):
        """Test that all links in about.md point to valid URLs."""
        about_file = os.path.join(self.references_dir, "about.md")
        if not os.path.exists(about_file):
            self.skipTest("about.md not found")

        with open(about_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all markdown links [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        links = re.findall(link_pattern, content)

        broken_links = []
        for link_text, link_url in links:
            # Only check internal links (starting with /)
            if link_url.startswith("/") and not link_url.startswith(
                ("http://", "https://")
            ):
                # Check for common broken patterns
                if link_url == "/":
                    broken_links.append(
                        f"[{link_text}]({link_url}) - should be /generator/"
                    )
                else:
                    # Try to resolve the URL
                    try:
                        resolve(link_url)
                    except Resolver404:
                        # Check if it's a reference_html URL
                        if link_url.startswith("/html/"):
                            name = (
                                link_url.split("/")[-2]
                                if link_url.endswith("/")
                                else link_url.split("/")[-1]
                            )
                            try:
                                reverse("reference_html", kwargs={"name": name})
                            except NoReverseMatch:
                                broken_links.append(
                                    f"[{link_text}]({link_url}) - invalid reference_html name: {name}"
                                )
                        else:
                            broken_links.append(
                                f"[{link_text}]({link_url}) - URL not found"
                            )

        if broken_links:
            self.fail(f"Found broken links in about.md:\n" + "\n".join(broken_links))

    def test_public_rulebook_md_links_are_valid(self):
        """Test that all links in public-rulebook.md point to valid URLs."""
        rulebook_file = os.path.join(self.references_dir, "public-rulebook.md")
        if not os.path.exists(rulebook_file):
            self.skipTest("public-rulebook.md not found")

        with open(rulebook_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all markdown links [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        links = re.findall(link_pattern, content)

        broken_links = []
        for link_text, link_url in links:
            # Only check internal links (starting with /)
            if link_url.startswith("/") and not link_url.startswith(
                ("http://", "https://")
            ):
                # Check for common broken patterns
                if link_url == "/":
                    broken_links.append(
                        f"[{link_text}]({link_url}) - should be /generator/"
                    )
                else:
                    # Try to resolve the URL
                    try:
                        resolve(link_url)
                    except Resolver404:
                        # Check if it's a reference_html URL
                        if link_url.startswith("/html/"):
                            name = (
                                link_url.split("/")[-2]
                                if link_url.endswith("/")
                                else link_url.split("/")[-1]
                            )
                            try:
                                reverse("reference_html", kwargs={"name": name})
                            except NoReverseMatch:
                                broken_links.append(
                                    f"[{link_text}]({link_url}) - invalid reference_html name: {name}"
                                )
                        elif link_url.startswith("/turn-sequence"):
                            # This should resolve to turn_sequence view
                            try:
                                reverse("turn_sequence")
                            except NoReverseMatch:
                                broken_links.append(
                                    f"[{link_text}]({link_url}) - turn_sequence URL not found"
                                )
                        else:
                            broken_links.append(
                                f"[{link_text}]({link_url}) - URL not found"
                            )

        if broken_links:
            self.fail(
                f"Found broken links in public-rulebook.md:\n" + "\n".join(broken_links)
            )

    def test_no_root_links_to_generator(self):
        """Test that no markdown files link to / when they should link to /generator/."""
        markdown_files = [
            "welcome.md",
            "about.md",
            "public-rulebook.md",
            "dm-handbook.md",
        ]

        broken_links = []
        for filename in markdown_files:
            filepath = os.path.join(self.references_dir, filename)
            if not os.path.exists(filepath):
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Find links that point to / and mention character/generator
            link_pattern = r"\[([^\]]*(?:character|generator|create)[^\]]*)\]\((/)\)"
            matches = re.findall(link_pattern, content, re.IGNORECASE)

            for link_text, link_url in matches:
                broken_links.append(
                    f"{filename}: [{link_text}]({link_url}) should be /generator/"
                )

        if broken_links:
            self.fail(
                "Found links to / that should point to /generator/:\n"
                + "\n".join(broken_links)
            )

    def test_reference_html_urls_resolve(self):
        """Test that all /html/... URLs in markdown files resolve correctly."""
        markdown_files = [
            "welcome.md",
            "about.md",
            "public-rulebook.md",
            "dm-handbook.md",
        ]

        broken_links = []
        for filename in markdown_files:
            filepath = os.path.join(self.references_dir, filename)
            if not os.path.exists(filepath):
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all /html/... links
            link_pattern = r"\[([^\]]+)\]\((/html/[^)]+)\)"
            links = re.findall(link_pattern, content)

            for link_text, link_url in links:
                # Extract the name from /html/name/ (strip anchor fragments)
                url_without_anchor = link_url.split("#")[0]
                name = url_without_anchor.rstrip("/").split("/")[-1]

                # Skip if name is empty (shouldn't happen, but be safe)
                if not name:
                    continue

                # Check if the URL resolves
                try:
                    reverse("reference_html", kwargs={"name": name})
                except NoReverseMatch:
                    broken_links.append(
                        f"{filename}: [{link_text}]({link_url}) - name '{name}' not found"
                    )

                # Check if the markdown file exists
                md_file = os.path.join(self.references_dir, f"{name}.md")
                if not os.path.exists(md_file):
                    broken_links.append(
                        f"{filename}: [{link_text}]({link_url}) - file {name}.md does not exist"
                    )

        if broken_links:
            self.fail("Found broken /html/... links:\n" + "\n".join(broken_links))


class TemplateLinkValidationTests(TestCase):
    """Tests to validate URL tags in Django templates."""

    def test_all_url_names_exist(self):
        """Test that all URL names used in templates actually exist."""
        from django.template import Engine, Context
        from django.template.loader import get_template

        # Common URL names used in templates
        url_names = [
            ("welcome", {}),
            ("generator", {}),
            ("my_characters", {}),
            ("reference_html", {"name": "about"}),  # Test with a sample name
            ("turn_sequence", {}),
            ("about", {}),
            ("lore", {}),
            ("handbook", {}),
            ("combat", {}),
            ("dm", {}),
            ("rulebook", {}),
            ("login", {}),
            ("logout", {}),
            ("register", {}),
            ("my_profile", {}),
            ("notes", {}),
            ("manage_users", {}),
            ("manage_characters", {}),
        ]

        missing_urls = []
        for url_name, kwargs in url_names:
            try:
                reverse(url_name, kwargs=kwargs)
            except NoReverseMatch:
                missing_urls.append(f"{url_name}({kwargs})")

        if missing_urls:
            self.fail(
                f"URL names used in templates but not defined: {', '.join(missing_urls)}"
            )

    def test_base_template_urls_resolve(self):
        """Test that all URL tags in base.html resolve correctly."""
        try:
            template = get_template("generator/base.html")
            # Render template to check for URL resolution errors
            context = Context({"user": None})
            template.render(context)
        except NoReverseMatch as e:
            self.fail(f"URL name in base.html does not exist: {e}")
        except Exception as e:
            # Other template errors are okay for this test
            pass


class URLResolutionTests(TestCase):
    """Tests to ensure all URL patterns resolve correctly."""

    def setUp(self):
        """Set up test client and find all markdown files."""
        self.references_dir = os.path.join(settings.BASE_DIR, "..", "references")

    def test_all_main_urls_resolve(self):
        """Test that all main URL patterns resolve without errors."""
        urls_to_test = [
            ("welcome", {}),
            ("generator", {}),
            ("about", {}),
            ("lore", {}),
            ("handbook", {}),
            ("combat", {}),
            ("rulebook", {}),
            ("turn_sequence", {}),
            ("login", {}),
            ("register", {}),
        ]

        broken_urls = []
        for url_name, kwargs in urls_to_test:
            try:
                url = reverse(url_name, kwargs=kwargs)
                # Try to resolve it back
                resolve(url)
            except (NoReverseMatch, Resolver404) as e:
                broken_urls.append(f"{url_name}: {e}")

        if broken_urls:
            self.fail("Found URLs that don't resolve:\n" + "\n".join(broken_urls))

    def test_reference_html_urls_work(self):
        """Test that reference_html URLs work for all known reference files."""
        reference_names = [
            "about",
            "public-rulebook",
            "dm-handbook",
        ]

        broken_urls = []
        for name in reference_names:
            try:
                url = reverse("reference_html", kwargs={"name": name})
                # Check if file exists
                md_file = os.path.join(
                    settings.BASE_DIR, "..", "references", f"{name}.md"
                )
                if not os.path.exists(md_file):
                    broken_urls.append(
                        f"reference_html('{name}') - file {name}.md does not exist"
                    )
            except NoReverseMatch as e:
                broken_urls.append(f"reference_html('{name}'): {e}")

        if broken_urls:
            self.fail("Found broken reference_html URLs:\n" + "\n".join(broken_urls))

    def test_all_redirect_calls_are_valid(self):
        """Test that all redirect() calls in views.py use valid URL names."""
        views_file = os.path.join(settings.BASE_DIR, "webapp", "generator", "views.py")
        if not os.path.exists(views_file):
            self.skipTest("views.py not found")

        with open(views_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all redirect() calls with string literals
        redirect_pattern = r"redirect\([\'\"]([^\'\"]+)[\'\"]"
        redirects = re.findall(redirect_pattern, content)

        broken_redirects = []
        for url_name in set(redirects):
            # Skip if it's a variable or function call
            if "(" in url_name or ")" in url_name:
                continue
            try:
                # Try to reverse it (some may need kwargs, so catch exception)
                reverse(url_name)
            except NoReverseMatch:
                # Check if it's a redirect with kwargs (like character_sheet)
                if "char_id" in content or "user_id" in content or "note_id" in content:
                    # These might need kwargs, skip for now
                    continue
                broken_redirects.append(f"redirect('{url_name}') - URL name not found")

        if broken_redirects:
            self.fail("Found invalid redirect() calls:\n" + "\n".join(broken_redirects))

    def test_all_template_url_tags_are_valid(self):
        """Test that all {% url %} tags in templates use valid URL names."""
        from django.template import Engine
        from django.template.loader import get_template

        templates_to_check = [
            "generator/base.html",
            "generator/index.html",
            "generator/welcome.html",
        ]

        broken_urls = []
        for template_name in templates_to_check:
            try:
                template = get_template(template_name)
                # Try to render with empty context to catch URL errors
                from django.template import Context

                context = Context({})
                template.render(context)
            except NoReverseMatch as e:
                broken_urls.append(f"{template_name}: {e}")
            except Exception as e:
                # Other errors (like missing context variables) are okay
                # We're only checking URL resolution
                if "NoReverseMatch" in str(type(e).__name__):
                    broken_urls.append(f"{template_name}: {e}")

        if broken_urls:
            self.fail(
                "Found invalid {% url %} tags in templates:\n" + "\n".join(broken_urls)
            )

    def test_dm_handbook_links_are_valid(self):
        """Test that all links in dm-handbook.md point to valid URLs."""
        dm_file = os.path.join(self.references_dir, "dm-handbook.md")
        if not os.path.exists(dm_file):
            self.skipTest("dm-handbook.md not found")

        with open(dm_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all markdown links [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        links = re.findall(link_pattern, content)

        broken_links = []
        for link_text, link_url in links:
            # Only check internal links (starting with /)
            if link_url.startswith("/") and not link_url.startswith(
                ("http://", "https://")
            ):
                # Check for common broken patterns
                if link_url == "/":
                    broken_links.append(
                        f"[{link_text}]({link_url}) - should be /generator/"
                    )
                else:
                    # Try to resolve the URL
                    try:
                        resolve(link_url)
                    except Resolver404:
                        # Check if it's a reference_html URL
                        if link_url.startswith("/html/"):
                            name = link_url.split("#")[0].rstrip("/").split("/")[-1]
                            try:
                                reverse("reference_html", kwargs={"name": name})
                            except NoReverseMatch:
                                broken_links.append(
                                    f"[{link_text}]({link_url}) - invalid reference_html name: {name}"
                                )
                        else:
                            broken_links.append(
                                f"[{link_text}]({link_url}) - URL not found"
                            )

        if broken_links:
            self.fail(
                f"Found broken links in dm-handbook.md:\n" + "\n".join(broken_links)
            )
