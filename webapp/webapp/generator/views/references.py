"""
Reference page views for the Pillars Character Generator.

This module handles serving handbook and reference content:
- handbook_section: Generic handbook section from markdown
- reference_html: Render markdown/HTML reference files
- serve_reference_html: Serve standalone HTML files
- serve_reference_image: Serve images from references
- serve_reference_file: Serve raw reference files
- dm_handbook: DM Handbook with chapter navigation
"""

import os
import re
import markdown
import bleach
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404, HttpResponse, FileResponse
from django.urls import reverse


# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "code",
    "pre",
    "blockquote",
    "hr",
    "a",
    "img",
    "div",
    "span",
]
ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
}


def handbook_section(request, section: str):
    """Generic view for handbook sections loaded from markdown files."""
    # Map section names to file paths and display titles
    # All game content is in references/
    SECTION_CONFIG = {
        "about": {
            "path": os.path.join(settings.BASE_DIR, "..", "references", "about.md"),
            "title": "About",
        },
        "lore": {
            "path": os.path.join(settings.BASE_DIR, "..", "references", "lore.md"),
            "title": "Background",
        },
        "players_handbook": {
            "path": os.path.join(
                settings.BASE_DIR, "..", "references", "A Pillars Handbook.md"
            ),
            "title": "Player's Handbook",
        },
        "combat": {
            "path": os.path.join(
                settings.BASE_DIR, "..", "references", "Combat_and_Movement.md"
            ),
            "title": "Combat & Movement",
        },
        "dm_handbook": {
            "path": os.path.join(
                settings.BASE_DIR, "..", "references", "dm-handbook.md"
            ),
            "title": "DM Handbook",
        },
        "public_rulebook": {
            "path": os.path.join(
                settings.BASE_DIR, "..", "references", "public-rulebook.md"
            ),
            "title": "Rulebook",
        },
    }

    config = SECTION_CONFIG.get(section)
    if config:
        section_path = config["path"]
        title = config["title"]
    else:
        # Fallback for unknown sections - look in references
        section_path = os.path.join(
            settings.BASE_DIR, "..", "references", f"{section}.md"
        )
        title = section.replace("_", " ").title()

    try:
        with open(section_path, "r", encoding="utf-8") as f:
            content = f.read()

        html_content = markdown.markdown(
            content, extensions=["tables", "fenced_code", "toc"]
        )

        # Rewrite relative image paths to Django URL paths for the web app
        # This allows markdown files to work both standalone and in the browser
        # e.g., src="images/foo.png" becomes src="/images/foo.png"
        # Use a function to generate proper Django URLs
        def replace_image_path(match):
            filename = match.group(1)
            # Generate the Django URL for the image
            image_url = reverse("reference_image", args=[filename])
            return f'src="{image_url}"'

        html_content = re.sub(r'src="images/([^"]+)"', replace_image_path, html_content)
    except FileNotFoundError:
        html_content = f"<p>Section '{section}' not found.</p>"

    return render(
        request,
        "generator/handbook_section.html",
        {
            "content": html_content,
            "title": title,
        },
    )


def serve_reference_html(request, filename):
    """Serve standalone HTML files from the references directory.

    This is used for legacy URLs (like pillars-turn-sequence.html).
    Content-only HTML files are served wrapped in the base template.
    """
    # Security: prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        raise Http404("Invalid filename")

    references_dir = os.path.realpath(
        os.path.join(settings.BASE_DIR, "..", "references")
    )
    html_path = os.path.realpath(os.path.join(references_dir, filename))

    # Ensure resolved path is still within references directory
    if not html_path.startswith(references_dir + os.sep):
        raise Http404("Invalid filename")

    if not os.path.exists(html_path):
        raise Http404("File not found")

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title from content-only HTML (<!-- title: Title Here -->)
    title_match = re.search(r"<!-- title: (.+?) -->", content)
    if title_match:
        title = title_match.group(1)
        # Remove the title comment from content
        content = re.sub(r"<!-- title: .+? -->\n?", "", content)
    else:
        # Fallback: extract from filename
        title = (
            filename.replace(".html", "").replace("-", " ").replace("_", " ").title()
        )

    # Check if this is a content-only HTML file (no <html> tag)
    if "<html" not in content.lower():
        # Content-only HTML - render through template
        return render(
            request,
            "generator/handbook_section.html",
            {
                "content": content,
                "title": title,
            },
        )
    else:
        # Legacy full HTML file - serve as-is with injected nav
        # This handles files like pillars-turn-sequence.html
        return HttpResponse(content, content_type="text/html")


def reference_html(request, name):
    """Serve markdown content rendered to HTML, wrapped in the base template.

    This provides consistent navigation across all reference pages.
    Markdown is converted to HTML on-the-fly using the markdown library.
    """
    # Security: prevent directory traversal
    if ".." in name or "/" in name:
        raise Http404("Invalid name")

    # Special handling for dm-handbook - serve the intro chapter
    # This maintains backward compatibility with /html/dm-handbook/ URLs
    if name == "dm-handbook":
        # Check DM access first
        profile = getattr(request.user, "profile", None)
        is_dm_or_admin = (
            profile and (profile.is_dm or profile.is_admin) if profile else False
        )
        if not is_dm_or_admin:
            # Redirect to login if not authenticated, or show access denied
            if not request.user.is_authenticated:
                return redirect("login")
            else:
                from django.http import HttpResponseForbidden

                return HttpResponseForbidden("DM access required")

        # Serve the intro chapter file
        filename = "dm-handbook-00-intro.md"
        references_dir = os.path.realpath(
            os.path.join(settings.BASE_DIR, "..", "references")
        )
        md_path = os.path.realpath(os.path.join(references_dir, filename))

        if not md_path.startswith(references_dir + os.sep) or not os.path.exists(
            md_path
        ):
            raise Http404("File not found")

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Extract title
        title = "DM Handbook"
        for line in md_content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Convert markdown to HTML
        content = markdown.markdown(
            md_content, extensions=["tables", "fenced_code", "toc"]
        )

        # Rewrite chapter links to use the new chapter system
        # Handle chapter name with optional trailing slash and optional anchor fragment
        content = re.sub(
            r'href="/dm/chapter/([^"/#]+)/?(#[^"]*)?"',
            lambda m: f'href="{reverse("dm_chapter", args=[m.group(1)])}{m.group(2) or ""}"',
            content,
        )

        # Sanitize HTML to prevent XSS attacks
        content = bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

        return render(
            request,
            "generator/handbook_section.html",
            {
                "content": content,
                "title": title,
            },
        )

    # Read the markdown file
    filename = f"{name}.md"
    references_dir = os.path.realpath(
        os.path.join(settings.BASE_DIR, "..", "references")
    )
    md_path = os.path.realpath(os.path.join(references_dir, filename))

    # Ensure resolved path is still within references directory
    if not md_path.startswith(references_dir + os.sep):
        raise Http404("Invalid name")

    if not os.path.exists(md_path):
        raise Http404("File not found")

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Extract title from first # heading and remove it from content to avoid duplication
    title = name.replace("-", " ").replace("_", " ").title()
    lines = md_content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            # Remove the H1 line to prevent duplicate title
            lines[i] = ""
            break
    md_content = "\n".join(lines)

    # Convert markdown to HTML with extensions for tables and fenced code
    content = markdown.markdown(md_content, extensions=["tables", "fenced_code", "toc"])

    # Sanitize HTML to prevent XSS attacks
    content = bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    return render(
        request,
        "generator/handbook_section.html",
        {
            "content": content,
            "title": title,
        },
    )


def serve_reference_image(request, filename):
    """Serve images from the references/images directory."""
    import mimetypes

    # Security: prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        raise Http404("Invalid filename")

    images_dir = os.path.realpath(settings.REFERENCES_IMAGES_DIR)
    image_path = os.path.realpath(os.path.join(images_dir, filename))

    # Ensure resolved path is still within images directory
    if not image_path.startswith(images_dir + os.sep):
        raise Http404("Invalid filename")

    if not os.path.exists(image_path):
        raise Http404("Image not found")

    content_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(open(image_path, "rb"), content_type=content_type)


def serve_reference_file(request, filename):
    """Serve raw reference files (md/html) from the references directory."""
    import mimetypes

    # Security: prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        raise Http404("Invalid filename")

    # Only allow specific file extensions
    allowed_extensions = [".md", ".html"]
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise Http404("Invalid file type")

    references_dir = os.path.realpath(
        os.path.join(settings.BASE_DIR, "..", "references")
    )
    file_path = os.path.realpath(os.path.join(references_dir, filename))

    # Ensure resolved path is still within references directory
    if not file_path.startswith(references_dir + os.sep):
        raise Http404("Invalid filename")

    if not os.path.exists(file_path):
        raise Http404("File not found")

    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "text/plain"

    return FileResponse(open(file_path, "rb"), content_type=content_type)


def spells_tabbed(request):
    """Serve the spells compendium with tabs for each school.

    Requires DM or Admin role. Parses spells.md and splits into sections by school.
    """
    # Late import to avoid circular dependency
    from .admin import dm_required_check

    # Check DM access
    redirect_response = dm_required_check(request)
    if redirect_response:
        return redirect_response

    # Read the spells.md file
    spells_path = os.path.join(settings.BASE_DIR, "..", "references", "spells.md")

    try:
        with open(spells_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise Http404("Spells file not found")

    # Split content by H1 headers (# School Name)
    # The file structure is:
    # - Overview/mechanics at the top
    # - # Elemental School
    # - # Passage School
    # - # Protection School
    # - # Mending School
    # - # Weather School
    # - # Control School
    # - Appendices at the end

    sections = re.split(
        r"^(# (?:Elemental|Passage|Protection|Mending|Weather|Control) School)$",
        content,
        flags=re.MULTILINE,
    )

    # First section is overview (before any school header)
    overview_md = sections[0]

    # Build a dict of school -> content
    schools = {}
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            header = sections[i]
            school_content = sections[i + 1]
            # Extract school name from header
            school_name = header.replace("# ", "").replace(" School", "").lower()
            schools[school_name] = header + school_content

    # Find and extract appendices (everything after Control school that starts with # Appendix)
    appendix_content = ""
    if "control" in schools:
        control_parts = re.split(
            r"^(# Appendix)", schools["control"], maxsplit=1, flags=re.MULTILINE
        )
        if len(control_parts) > 1:
            schools["control"] = control_parts[0]
            appendix_content = (
                "# Appendix" + control_parts[2] if len(control_parts) > 2 else ""
            )

    # Add appendices to overview
    overview_md += "\n\n" + appendix_content

    # Convert each section to HTML
    def md_to_html(md_content):
        html = markdown.markdown(
            md_content, extensions=["tables", "fenced_code", "toc"]
        )
        return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    context = {
        "overview_content": md_to_html(overview_md),
        "elemental_content": md_to_html(schools.get("elemental", "")),
        "passage_content": md_to_html(schools.get("passage", "")),
        "protection_content": md_to_html(schools.get("protection", "")),
        "mending_content": md_to_html(schools.get("mending", "")),
        "weather_content": md_to_html(schools.get("weather", "")),
        "control_content": md_to_html(schools.get("control", "")),
    }

    return render(request, "generator/spells_tabbed.html", context)


def dm_handbook(request, chapter=None):
    """DM Handbook - requires DM or Admin role. Supports chapter navigation.

    Note: Access control is handled by the dm_required decorator
    applied in the __init__.py or urls.py, or checked inline.
    """
    # Late import to avoid circular dependency
    from .admin import dm_required_check

    # Check DM access
    redirect_response = dm_required_check(request)
    if redirect_response:
        return redirect_response
    # Chapter mapping: key -> (filename, sidebar_title, page_title)
    CHAPTERS = {
        None: ("dm-handbook-00-intro.md", "Table of Contents", "DM Handbook"),
        "00-intro": ("dm-handbook-00-intro.md", "Table of Contents", "DM Handbook"),
        "01-magic-mechanics": (
            "dm-handbook-01-magic-mechanics.md",
            "Mechanics",
            "Magic Mechanics",
        ),
        "02-spells": ("dm-handbook-02-spells.md", "Spells", "Spell Compendium"),
        "03-gm-tools": ("dm-handbook-03-gm-tools.md", "GM Tools", "GM Tools"),
        "04-using-tables": (
            "dm-handbook-05-using-tables.md",
            "Using These Tables",
            "Using These Tables",
        ),
        "05-the-world": ("dm-handbook-02-the-world.md", "The World", "The World"),
        "06-scenario-seeds": (
            "dm-handbook-04-scenario-seeds.md",
            "Scenario Seeds",
            "Scenario Seeds",
        ),
        "07-nobility-titles": (
            "dm-handbook-06-nobility-titles.md",
            "Nobility Titles",
            "Nobility Titles",
        ),
        "08-names": ("dm-handbook-09-names.md", "Names", "Names"),
    }

    # Hierarchical menu structure for sidebar
    MENU_STRUCTURE = [
        {"type": "link", "key": None, "title": "Table of Contents"},
        {
            "type": "section",
            "title": "Magic",
            "items": [
                {"key": "01-magic-mechanics", "title": "Mechanics"},
                {"key": "02-spells", "title": "Spells"},
            ],
        },
        {
            "type": "section",
            "title": "GM Tools",
            "items": [
                {"key": "04-using-tables", "title": "Using These Tables"},
                {"key": "05-the-world", "title": "The World"},
                {"key": "06-scenario-seeds", "title": "Scenario Seeds"},
                {"key": "07-nobility-titles", "title": "Nobility Titles"},
                {"key": "08-names", "title": "Names"},
            ],
        },
    ]

    # Get chapter info
    chapter_key = chapter if chapter else None
    chapter_info = CHAPTERS.get(chapter_key)

    if not chapter_info:
        raise Http404("Chapter not found")

    filename, section_title, page_title = chapter_info

    # Build file path
    section_path = os.path.join(settings.BASE_DIR, "..", "references", filename)

    try:
        with open(section_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove H1 title from content to avoid duplication with section_title
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# "):
                lines[i] = ""
                break
        content = "\n".join(lines)

        html_content = markdown.markdown(
            content, extensions=["tables", "fenced_code", "toc"]
        )

        # Rewrite relative image paths to Django URL paths
        def replace_image_path(match):
            img_filename = match.group(1)
            image_url = reverse("reference_image", args=[img_filename])
            return f'src="{image_url}"'

        html_content = re.sub(r'src="images/([^"]+)"', replace_image_path, html_content)
    except FileNotFoundError:
        html_content = f"<p>Chapter '{chapter}' not found.</p>"

    return render(
        request,
        "generator/dm_handbook.html",
        {
            "content": html_content,
            "title": page_title,
            "section_title": section_title,
            "menu_structure": MENU_STRUCTURE,
            "current_chapter": chapter_key,
        },
    )
