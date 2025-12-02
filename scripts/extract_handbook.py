#!/usr/bin/env python3
"""
Extract tagged sections from A Pillars Handbook.md into separate files.

This script parses the handbook for tags like:
    -- tag_name --
    content here
    -- /tag_name --

And extracts each section to:
    webapp/webapp/generator/docs/<tag_name>.md

It also updates:
    - welcome.html with navigation links for all discovered tags
    - urls.py with routes for new tags
    - Creates a sections.json manifest file

Usage:
    python scripts/extract_handbook.py

Can be run as a pre-commit hook or during deployment.
"""

import json
import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Section:
    """A tagged section from the handbook."""
    tag: str
    content: str
    display_name: str
    url_path: str
    icon: str


# Tag configuration - display names, URL paths, and icons
# New tags will be auto-configured with defaults
TAG_CONFIG = {
    'meta': {
        'display_name': 'Meta',
        'url_path': 'meta',
        'icon': '&#9432;',  # info circle
    },
    'lore': {
        'display_name': 'Background',
        'url_path': 'lore',
        'icon': '&#128220;',  # scroll
    },
    'players_handbook': {
        'display_name': "Player's Handbook",
        'url_path': 'handbook',
        'icon': '&#128214;',  # open book
    },
    'DM_handbook': {
        'display_name': 'DM',
        'url_path': 'dm',
        'icon': '&#128218;',  # books
    },
}

# Default icon for new/unknown tags
DEFAULT_ICON = '&#128196;'  # page facing up


def find_project_root() -> Path:
    """Find the project root directory."""
    # Start from script location and go up
    script_dir = Path(__file__).resolve().parent
    # Go up from scripts/ to project root
    return script_dir.parent


def parse_handbook(handbook_path: Path) -> dict[str, str]:
    """
    Parse the handbook and extract all tagged sections.

    Returns:
        Dict mapping tag names to their content.
    """
    if not handbook_path.exists():
        print(f"ERROR: Handbook not found at {handbook_path}")
        sys.exit(1)

    content = handbook_path.read_text(encoding='utf-8')

    # Find all tags using regex
    # Matches: -- tag_name -- (with optional whitespace variations)
    tag_pattern = r'--\s*(\w+)\s*--'

    # Find all opening tags and their positions
    sections = {}
    tag_positions = []

    for match in re.finditer(tag_pattern, content):
        tag_name = match.group(1)
        pos = match.end()
        tag_positions.append((tag_name, pos, match.start()))

    # For each opening tag, find its closing tag
    for i, (tag_name, start_pos, tag_start) in enumerate(tag_positions):
        # Look for closing tag pattern: -- /tag_name -- or --/ tag_name --
        close_pattern = rf'--\s*/\s*{re.escape(tag_name)}\s*--'
        close_match = re.search(close_pattern, content[start_pos:], re.IGNORECASE)

        if close_match:
            end_pos = start_pos + close_match.start()
            section_content = content[start_pos:end_pos].strip()
            sections[tag_name] = section_content
            print(f"  Found section: {tag_name} ({len(section_content)} chars)")
        else:
            # No closing tag - look for next opening tag or end of file
            if i + 1 < len(tag_positions):
                end_pos = tag_positions[i + 1][2]  # Start of next tag
            else:
                end_pos = len(content)
            section_content = content[start_pos:end_pos].strip()
            sections[tag_name] = section_content
            print(f"  Found section (no close tag): {tag_name} ({len(section_content)} chars)")

    return sections


def get_section_config(tag: str) -> dict:
    """Get configuration for a tag, with defaults for unknown tags."""
    if tag in TAG_CONFIG:
        return TAG_CONFIG[tag]

    # Generate defaults for unknown tags
    display_name = tag.replace('_', ' ').title()
    url_path = tag.lower().replace('_', '-')

    return {
        'display_name': display_name,
        'url_path': url_path,
        'icon': DEFAULT_ICON,
    }


def write_section_files(sections: dict[str, str], docs_dir: Path) -> list[Section]:
    """
    Write extracted sections to markdown files.

    Returns:
        List of Section objects for all extracted sections.
    """
    docs_dir.mkdir(parents=True, exist_ok=True)
    extracted = []

    for tag, content in sections.items():
        config = get_section_config(tag)
        output_path = docs_dir / f"{tag}.md"
        output_path.write_text(content, encoding='utf-8')
        print(f"  Wrote: {output_path}")

        extracted.append(Section(
            tag=tag,
            content=content,
            display_name=config['display_name'],
            url_path=config['url_path'],
            icon=config['icon'],
        ))

    return extracted


def write_manifest(sections: list[Section], manifest_path: Path):
    """Write a JSON manifest of all sections."""
    manifest = {
        'sections': [asdict(s) for s in sections],
        'tag_config': TAG_CONFIG,
    }
    # Don't include content in manifest (too large)
    for s in manifest['sections']:
        del s['content']

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f"  Wrote manifest: {manifest_path}")


def update_welcome_html(sections: list[Section], template_path: Path):
    """Update welcome.html with navigation links for all sections."""
    if not template_path.exists():
        print(f"WARNING: Template not found: {template_path}")
        return

    content = template_path.read_text(encoding='utf-8')

    # Build the nav-links section
    nav_links = ['    <div class="nav-links">']

    # Always include Character Generator first
    nav_links.append('''        <a href="{% url 'generator' %}" class="nav-link">
            <span class="icon">&#9876;</span>
            Character Generator
        </a>''')

    # Add all extracted sections in a consistent order
    # Use TAG_CONFIG order for known tags, then alphabetical for new ones
    known_tags = list(TAG_CONFIG.keys())
    section_by_tag = {s.tag: s for s in sections}

    # First add known tags in order
    for tag in known_tags:
        if tag in section_by_tag:
            s = section_by_tag[tag]
            nav_links.append(f'''        <a href="{{% url '{s.url_path}' %}}" class="nav-link">
            <span class="icon">{s.icon}</span>
            {s.display_name}
        </a>''')

    # Then add any new tags alphabetically
    new_tags = sorted(set(section_by_tag.keys()) - set(known_tags))
    for tag in new_tags:
        s = section_by_tag[tag]
        nav_links.append(f'''        <a href="{{% url '{s.url_path}' %}}" class="nav-link">
            <span class="icon">{s.icon}</span>
            {s.display_name}
        </a>''')

    nav_links.append('    </div>')
    nav_html = '\n'.join(nav_links)

    # Replace the nav-links section
    pattern = r'<div class="nav-links">.*?</div>'
    new_content = re.sub(pattern, nav_html, content, flags=re.DOTALL)

    if new_content != content:
        template_path.write_text(new_content, encoding='utf-8')
        print(f"  Updated: {template_path}")
    else:
        print(f"  No changes needed: {template_path}")


def update_urls_py(sections: list[Section], urls_path: Path):
    """Update urls.py with routes for all sections."""
    if not urls_path.exists():
        print(f"WARNING: urls.py not found: {urls_path}")
        return

    content = urls_path.read_text(encoding='utf-8')

    # Check which routes already exist by URL name
    existing_routes = set(re.findall(r"name='(\w+)'", content))

    # Build list of needed routes (only for new sections not already in urls.py)
    new_routes = []
    for s in sections:
        # Check both the url_path name and tag name to avoid duplicates
        if s.url_path not in existing_routes and s.tag not in existing_routes:
            new_routes.append(
                f"    path('{s.url_path}/', views.handbook_section, "
                f"{{'section': '{s.tag}'}}, name='{s.url_path}'),"
            )
            print(f"  New route needed: {s.url_path}")

    if new_routes:
        # Find the closing bracket of urlpatterns
        # Look for the pattern ]\n or ] at end
        insert_match = re.search(r'\n\s*\]', content)
        if insert_match:
            insert_point = insert_match.start()
            new_content = (
                content[:insert_point] +
                '\n    # Auto-generated handbook sections\n' +
                '\n'.join(new_routes) +
                content[insert_point:]
            )
            urls_path.write_text(new_content, encoding='utf-8')
            print(f"  Updated: {urls_path}")
        else:
            print(f"  WARNING: Could not find insertion point in {urls_path}")
    else:
        print(f"  No new routes needed in {urls_path}")


def update_views_py(sections: list[Section], views_path: Path, docs_dir: Path):
    """Ensure views.py has the generic handbook_section view."""
    if not views_path.exists():
        print(f"WARNING: views.py not found: {views_path}")
        return

    content = views_path.read_text(encoding='utf-8')

    # Check if handbook_section view already exists
    if 'def handbook_section(' in content:
        print(f"  handbook_section view already exists in {views_path}")
        return

    # Add the generic view
    generic_view = '''

def handbook_section(request, section: str):
    """Generic view for handbook sections loaded from markdown files."""
    import os
    from django.conf import settings

    # Path to the docs directory
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    section_path = os.path.join(docs_dir, f'{section}.md')

    try:
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        html_content = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'toc']
        )
    except FileNotFoundError:
        html_content = f"<p>Section '{section}' not found.</p>"

    # Load section manifest for title
    manifest_path = os.path.join(docs_dir, 'sections.json')
    title = section.replace('_', ' ').title()
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            for s in manifest.get('sections', []):
                if s.get('tag') == section:
                    title = s.get('display_name', title)
                    break
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return render(request, 'generator/handbook_section.html', {
        'content': html_content,
        'title': title,
    })
'''

    # Insert after existing imports or at end of file
    new_content = content.rstrip() + generic_view
    views_path.write_text(new_content, encoding='utf-8')
    print(f"  Added handbook_section view to {views_path}")


def create_generic_template(templates_dir: Path):
    """Create a generic handbook section template if it doesn't exist."""
    template_path = templates_dir / 'handbook_section.html'

    if template_path.exists():
        print(f"  Template already exists: {template_path}")
        return

    template_content = '''{% extends "generator/base.html" %}

{% block title %}{{ title }} - Pillars{% endblock %}

{% block extra_css %}
.handbook-content {
    line-height: 1.7;
}
.handbook-content h2 {
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
    margin-top: 40px;
}
.handbook-content h3 {
    margin-top: 30px;
    color: #333;
}
.handbook-content h4 {
    margin-top: 25px;
    color: #555;
}
.handbook-content p {
    margin: 15px 0;
}
.handbook-content a {
    color: #36c;
}
.handbook-content hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 30px 0;
}
.handbook-content ul, .handbook-content ol {
    padding-left: 25px;
}
.handbook-content li {
    margin: 8px 0;
}
.handbook-content code {
    background: #f4f4f4;
    padding: 2px 6px;
    border: 1px solid #ddd;
}
.handbook-content pre {
    background: #f4f4f4;
    padding: 15px;
    border: 1px solid #ddd;
    overflow-x: auto;
}
.handbook-content blockquote {
    border-left: 4px solid #333;
    margin: 20px 0;
    padding-left: 20px;
    color: #666;
    font-style: italic;
}
.handbook-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}
.handbook-content th, .handbook-content td {
    border: 1px solid #ccc;
    padding: 10px;
    text-align: left;
}
.handbook-content th {
    background: #f4f4f4;
}
{% endblock %}

{% block content %}
<div class="top-bar">
    <h1>{{ title }}</h1>
    <a href="{% url 'welcome' %}" class="btn">&larr; Home</a>
</div>

<div class="handbook-content">
    {{ content|safe }}
</div>
{% endblock %}
'''

    template_path.write_text(template_content, encoding='utf-8')
    print(f"  Created template: {template_path}")


def main():
    """Main entry point."""
    print("Extracting handbook sections...")

    # Find paths
    project_root = find_project_root()
    handbook_path = project_root / 'A Pillars Handbook.md'
    webapp_dir = project_root / 'webapp' / 'webapp' / 'generator'
    docs_dir = project_root / 'references'
    templates_dir = webapp_dir / 'templates' / 'generator'

    print(f"\nProject root: {project_root}")
    print(f"Handbook: {handbook_path}")
    print(f"Output dir: {docs_dir}")

    # Parse handbook
    print("\nParsing handbook...")
    sections_dict = parse_handbook(handbook_path)

    if not sections_dict:
        print("No sections found!")
        sys.exit(1)

    print(f"\nFound {len(sections_dict)} sections")

    # Write section files
    print("\nWriting section files...")
    sections = write_section_files(sections_dict, docs_dir)

    # Write manifest
    print("\nWriting manifest...")
    write_manifest(sections, docs_dir / 'sections.json')

    # Update welcome.html
    print("\nUpdating welcome.html...")
    update_welcome_html(sections, templates_dir / 'welcome.html')

    # Create generic template
    print("\nChecking generic template...")
    create_generic_template(templates_dir)

    # Update views.py (add generic view if needed)
    print("\nChecking views.py...")
    update_views_py(sections, webapp_dir / 'views.py', docs_dir)

    # Update urls.py (for any new sections)
    print("\nChecking urls.py...")
    update_urls_py(sections, webapp_dir / 'urls.py')

    print("\nDone! Extracted sections:")
    for s in sections:
        print(f"  - {s.tag} -> /{s.url_path}/ ({s.display_name})")

    return 0


if __name__ == '__main__':
    sys.exit(main())
