"""
Content negotiation middleware for the Pillars Character Generator.

Supports returning content in different formats:
- Add .md to any URL or send Accept: text/markdown → returns Markdown
- Add .txt to any URL → returns plain text
"""

import html2text
import re
from django.http import HttpResponse
from django.urls import resolve, Resolver404


class ContentNegotiationMiddleware:
    """
    Middleware that handles content negotiation via URL suffix or Accept header.

    Usage:
    - GET /handbook.md → returns markdown version
    - GET /handbook.txt → returns plain text version
    - GET /handbook with Accept: text/markdown → returns markdown version
    """

    # Paths that should never have suffix processing (serve files directly)
    EXCLUDED_PATH_PREFIXES = [
        "/ref/",  # Raw reference files (already .md or .html)
        "/static/",  # Static files
        "/media/",  # Media files
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Configure html2text for clean markdown output
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Don't wrap lines
        self.h2t.unicode_snob = True
        self.h2t.skip_internal_links = True

    def _should_skip_path(self, path):
        """Check if path should be excluded from content negotiation."""
        for prefix in self.EXCLUDED_PATH_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _path_resolves(self, path):
        """Check if a path resolves to a valid URL."""
        try:
            resolve(path)
            return True
        except Resolver404:
            # Try with trailing slash (Django APPEND_SLASH behavior)
            if not path.endswith("/"):
                try:
                    resolve(path + "/")
                    return True
                except Resolver404:
                    pass
            return False

    def _get_resolved_path(self, path):
        """Get the resolved path, handling trailing slash normalization.

        Returns the path that resolves, or None if neither variant resolves.
        """
        if not path:
            return None
        try:
            resolve(path)
            return path
        except Resolver404:
            # Try with trailing slash (Django APPEND_SLASH behavior)
            if not path.endswith("/"):
                try:
                    path_with_slash = path + "/"
                    resolve(path_with_slash)
                    return path_with_slash
                except Resolver404:
                    pass
            return None

    def __call__(self, request):
        # Check for format suffix in URL
        path = request.path_info
        requested_format = None
        original_path = path
        original_request_path = request.path

        # Skip excluded paths
        if self._should_skip_path(path):
            return self.get_response(request)

        if path.endswith(".md"):
            # Check if the stripped path resolves - if not, this might be a real .md file
            stripped_path = path[:-3]
            resolved_path = self._get_resolved_path(stripped_path)
            if resolved_path:
                requested_format = "markdown"
                request.path_info = resolved_path
                request.path = resolved_path
        elif path.endswith(".txt"):
            stripped_path = path[:-4]
            resolved_path = self._get_resolved_path(stripped_path)
            if resolved_path:
                requested_format = "text"
                request.path_info = resolved_path
                request.path = resolved_path

        # Check Accept header if no suffix
        if not requested_format:
            accept = request.META.get("HTTP_ACCEPT", "")
            if "text/markdown" in accept:
                requested_format = "markdown"
            elif "text/plain" in accept and "text/html" not in accept:
                # Only use text/plain if text/html is not also requested
                requested_format = "text"

        # Store format request for potential use by views
        request.requested_format = requested_format

        # Get the response
        response = self.get_response(request)

        # If we got a 404 after stripping suffix, restore original path and retry
        if (
            response.status_code == 404
            and requested_format
            and path != request.path_info
        ):
            request.path_info = original_path
            request.path = original_request_path
            request.requested_format = None
            return self.get_response(request)

        # Only convert HTML responses
        if requested_format and response.get("Content-Type", "").startswith(
            "text/html"
        ):
            if response.status_code == 200:
                return self._convert_response(response, requested_format)

        return response

    def _convert_response(self, response, format_type):
        """Convert HTML response to requested format."""
        try:
            # Get HTML content
            if hasattr(response, "content"):
                html_content = response.content.decode("utf-8")
            else:
                return response

            # Extract main content (try to find article or main content area)
            content = self._extract_main_content(html_content)

            if format_type == "markdown":
                converted = self._html_to_markdown(content)
                return HttpResponse(
                    converted,
                    content_type="text/markdown; charset=utf-8",
                )
            elif format_type == "text":
                converted = self._html_to_text(content)
                return HttpResponse(
                    converted,
                    content_type="text/plain; charset=utf-8",
                )
        except Exception:
            # If conversion fails, return original response
            return response

        return response

    def _extract_main_content(self, html):
        """Extract main content area from HTML, removing navigation etc."""
        # Try to find main content area
        patterns = [
            r"<main[^>]*>(.*?)</main>",
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r"<article[^>]*>(.*?)</article>",
            r"<body[^>]*>(.*?)</body>",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)

        # Fall back to full HTML
        return html

    def _html_to_markdown(self, html):
        """Convert HTML to Markdown."""
        # Clean up common elements that don't convert well
        html = self._clean_html_for_conversion(html)

        # Convert to markdown
        markdown = self.h2t.handle(html)

        # Clean up the markdown
        markdown = self._clean_markdown(markdown)

        return markdown

    def _html_to_text(self, html):
        """Convert HTML to plain text."""
        # Use html2text with more aggressive settings for plain text
        h2t_text = html2text.HTML2Text()
        h2t_text.ignore_links = True
        h2t_text.ignore_images = True
        h2t_text.ignore_emphasis = True
        h2t_text.body_width = 80
        h2t_text.unicode_snob = True

        html = self._clean_html_for_conversion(html)
        text = h2t_text.handle(html)

        # Additional cleanup for plain text
        text = self._clean_plain_text(text)

        return text

    def _clean_html_for_conversion(self, html):
        """Clean up HTML before conversion."""
        # Remove script and style tags
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove navigation elements
        html = re.sub(r"<nav[^>]*>.*?</nav>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Remove form elements (buttons, inputs for UI)
        html = re.sub(
            r"<button[^>]*>.*?</button>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove hidden elements
        html = re.sub(
            r'<[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>.*?</[^>]+>',
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove SVG icons
        html = re.sub(r"<svg[^>]*>.*?</svg>", "", html, flags=re.DOTALL | re.IGNORECASE)

        return html

    def _clean_markdown(self, markdown):
        """Clean up converted markdown."""
        # Remove excessive blank lines
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        # Clean up list formatting
        markdown = re.sub(r"^\s*\*\s*$", "", markdown, flags=re.MULTILINE)

        # Remove lines that are just whitespace
        lines = markdown.split("\n")
        lines = [line.rstrip() for line in lines]
        markdown = "\n".join(lines)

        # Remove leading/trailing whitespace
        markdown = markdown.strip()

        return markdown

    def _clean_plain_text(self, text):
        """Clean up plain text output."""
        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove markdown-like artifacts
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)

        # Clean up list markers
        text = re.sub(r"^\s*[\*\-]\s*$", "", text, flags=re.MULTILINE)

        # Remove lines that are just whitespace
        lines = text.split("\n")
        lines = [line.rstrip() for line in lines]
        text = "\n".join(lines)

        text = text.strip()

        return text
