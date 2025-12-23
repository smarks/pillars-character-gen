#!/usr/bin/env python3
"""
Build script to convert all .md files to content-only .html fragments.
These fragments are served by Django views wrapped in the base template,
ensuring consistent navigation everywhere.
"""

import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')


def convert_inline_markdown(text: str) -> str:
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def convert_markdown_to_html(content: str) -> tuple:
    lines = content.split('\n')
    html_parts = []
    title, subtitle, credits = "", "", ""

    i = 0
    if i < len(lines) and lines[i].startswith('# '):
        title = lines[i][2:].strip()
        i += 1

    while i < len(lines) and not lines[i].strip():
        i += 1

    if i < len(lines) and lines[i].startswith('*') and lines[i].endswith('*') and not lines[i].startswith('**'):
        subtitle = lines[i][1:-1].strip()
        i += 1

    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith('by '):
        credits = lines[i].strip()
        i += 1

    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith('---')):
        i += 1

    in_table, in_list, list_type = False, False, None
    table_rows, list_items, current_paragraph = [], [], []

    def flush_paragraph():
        nonlocal current_paragraph
        if current_paragraph:
            html_parts.append(f'<p>{convert_inline_markdown(" ".join(current_paragraph))}</p>')
            current_paragraph = []

    def flush_list():
        nonlocal in_list, list_items, list_type
        if list_items:
            tag = 'ol' if list_type == 'ordered' else 'ul'
            html_parts.append(f'<{tag}>{"".join(f"<li>{convert_inline_markdown(item)}</li>" for item in list_items)}</{tag}>')
            list_items, in_list, list_type = [], False, None

    def flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            h = ''.join(f'<th>{convert_inline_markdown(c)}</th>' for c in table_rows[0])
            b = ''.join('<tr>' + ''.join(f'<td>{convert_inline_markdown(c)}</td>' for c in r) + '</tr>' for r in table_rows[2:])
            html_parts.append(f'<div class="table-wrapper"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')
            table_rows, in_table = [], False

    while i < len(lines):
        line, stripped = lines[i], lines[i].strip()

        if stripped.startswith('---') and all(c == '-' for c in stripped):
            flush_paragraph(); flush_list(); flush_table()
            html_parts.append('<hr>')
            i += 1; continue

        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            flush_paragraph(); flush_list(); flush_table()
            lvl, txt = len(heading_match.group(1)), heading_match.group(2).strip()
            html_parts.append(f'<h{lvl} id="{slugify(txt)}">{convert_inline_markdown(txt)}</h{lvl}>')
            i += 1; continue

        if '|' in stripped and stripped.startswith('|'):
            flush_paragraph(); flush_list()
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            table_rows.append(cells)
            if not in_table: in_table = True
            i += 1; continue
        elif in_table:
            flush_table()

        ol_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if ol_match:
            flush_paragraph(); flush_table()
            if list_type == 'unordered': flush_list()
            in_list, list_type = True, 'ordered'
            list_items.append(ol_match.group(2))
            i += 1; continue

        ul_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if ul_match:
            flush_paragraph(); flush_table()
            if list_type == 'ordered': flush_list()
            in_list, list_type = True, 'unordered'
            list_items.append(ul_match.group(1))
            i += 1; continue

        if not stripped:
            flush_paragraph(); flush_list(); flush_table()
            i += 1; continue

        if in_list: flush_list()
        current_paragraph.append(stripped)
        i += 1

    flush_paragraph(); flush_list(); flush_table()
    return title, subtitle, credits, '\n'.join(html_parts)


def generate_content_html(title: str, body_html: str) -> str:
    """Generate content-only HTML (no page wrapper, no menu).

    This content will be loaded by Django and wrapped in base.html template.
    """
    return f'''<!-- title: {title} -->
{body_html}
'''


def get_doc_title(md_path: Path) -> str:
    content = md_path.read_text(encoding='utf-8')
    for line in content.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    return md_path.stem.replace('-', ' ').replace('_', ' ').title()


def convert_file(md_path: Path) -> None:
    print(f"Converting {md_path.name}...")
    md_content = md_path.read_text(encoding='utf-8')
    title, subtitle, credits, body_html = convert_markdown_to_html(md_content)
    if not title:
        title = md_path.stem.replace('-', ' ').replace('_', ' ').title()
    html_path = md_path.with_suffix('.html')
    final_html = generate_content_html(title, body_html)
    html_path.write_text(final_html, encoding='utf-8')
    print(f"  -> {html_path.name}")


def main():
    script_dir = Path(__file__).parent
    md_files = sorted(script_dir.glob('*.md'))

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target.endswith('.md'):
            md_path = script_dir / target
            if md_path.exists():
                convert_file(md_path)
            else:
                print(f"File not found: {target}"); sys.exit(1)
        else:
            print(f"Expected .md file, got: {target}"); sys.exit(1)
    else:
        if not md_files:
            print("No .md files found."); sys.exit(0)
        print(f"Found {len(md_files)} markdown file(s):\n")
        for md_file in md_files:
            convert_file(md_file)
        print(f"\nDone! Converted {len(md_files)} file(s).")


if __name__ == '__main__':
    main()
