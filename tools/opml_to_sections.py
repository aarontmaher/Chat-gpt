#!/usr/bin/env python3
"""
tools/opml_to_sections.py
Converts grappling.opml -> updates const SECTIONS in index.html

Usage:
    python3 tools/opml_to_sections.py [--dry-run]
"""

import xml.etree.ElementTree as ET
import json
import os
import sys

COLORS = ['#e8ff47', '#ff6b35', '#a78bfa', '#47c8ff', '#34d399']

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPML_PATH = os.path.join(REPO_ROOT, 'grappling.opml')
INDEX_PATH = os.path.join(REPO_ROOT, 'index.html')

# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------

# Mindomo exports OPML with <?xml ... encoding="ISO-8859-1"?> in the
# XML declaration, but the file bytes are actually UTF-8.  Python's
# ElementTree respects the declared encoding, so it tries to decode UTF-8
# multi-byte sequences (e.g. the 3 bytes E2 86 92 that encode →) as
# ISO-8859-1.  That either raises a ParseError (byte 0x86 is a forbidden
# C1 control in XML 1.0) or silently produces three Latin-1 replacement
# characters instead of the single arrow →.
#
# Fix: read the file as raw bytes, patch the encoding declaration to UTF-8
# *before* handing bytes to the parser, then decode as UTF-8.

_CORRUPT_ARROW = '\u00e2\u0086\u0092'   # → misread as ISO-8859-1 (E2 86 92)
_REAL_ARROW    = '\u2192'                 # → (U+2192 RIGHTWARDS ARROW)


def _normalize_text(text: str) -> str:
    """Fix any residual encoding corruption and double-arrow typos in a label.

    Replaces:
      - corrupted 3-char sequence (UTF-8 bytes for → decoded as Latin-1) -> →
      - → → (doubled transition arrow) -> →  (single)
    """
    text = text.replace(_CORRUPT_ARROW, _REAL_ARROW)
    text = text.replace(_REAL_ARROW + ' ' + _REAL_ARROW, _REAL_ARROW)
    return text


def _read_opml_bytes(opml_path: str) -> bytes:
    """Read OPML file and patch encoding declaration to UTF-8.

    Mindomo declares ISO-8859-1 but writes UTF-8.  We fix the declaration so
    ElementTree parses the bytes with the correct encoding.
    """
    with open(opml_path, 'rb') as f:
        raw = f.read()

    # Patch both quote styles (double and single) just in case
    raw = raw.replace(b'encoding="ISO-8859-1"', b'encoding="UTF-8"')
    raw = raw.replace(b"encoding='ISO-8859-1'", b"encoding='UTF-8'")
    return raw


# ---------------------------------------------------------------------------
# Node conversion
# ---------------------------------------------------------------------------

def convert_node(outline):
    """Recursively convert an OPML <outline> element to a SECTIONS node dict."""
    text = _normalize_text(outline.get('text', '').strip())
    node = {'t': text}

    # Note field (Mindomo exports as 'note' attribute)
    note = outline.get('note', '') or outline.get('_note', '')
    if note:
        node['n'] = _normalize_text(note)

    children = list(outline)

    # Detect video children: empty text + url, or type="video"
    video_children = [
        c for c in children
        if c.get('type') == 'video'
        or (c.get('text', '').strip() == '' and c.get('url', ''))
    ]
    other_children = [
        c for c in children
        if c not in video_children and c.get('text', '').strip()
    ]

    # Attach first video URL to this node
    if video_children and video_children[0].get('url'):
        node['v'] = video_children[0].get('url')

    # Recurse into real children
    if other_children:
        node['c'] = [convert_node(c) for c in other_children]

    return node


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def opml_to_sections(opml_path):
    """Parse OPML file and return the SECTIONS list."""
    # Read and patch encoding declaration so ElementTree uses UTF-8
    raw = _read_opml_bytes(opml_path)

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise ValueError(f'Failed to parse OPML (after encoding patch): {e}')

    body = root.find('body')
    if body is None:
        raise ValueError('No <body> element found in OPML')

    root_outline = body.find('outline')
    if root_outline is None:
        raise ValueError('No root <outline> found in OPML body')

    sections = []
    for idx, section_el in enumerate(root_outline):
        if section_el.tag != 'outline':
            continue
        title = _normalize_text(section_el.get('text', '').strip())
        if not title:
            continue
        if title == 'TEMPLATES':
            continue
        color = COLORS[idx % len(COLORS)]
        nodes = []
        for child in section_el:
            if (child.tag == 'outline'
                    and child.get('text', '').strip()
                    and child.get('type') != 'video'):
                nodes.append(convert_node(child))
        sections.append({'title': title, 'color': color, 'nodes': nodes})

    return sections


def update_index_html(sections, dry_run=False):
    """Replace const SECTIONS = [...] in index.html with new data."""
    # Explicit UTF-8 encoding required: index.html uses non-ASCII characters
    # (e.g. → U+2192) that must round-trip correctly through read and write.
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    marker_start = 'const SECTIONS = '
    marker_end   = '\nconst COLORS'

    start = content.find(marker_start)
    if start == -1:
        raise ValueError('"const SECTIONS = " not found in index.html')
    end = content.find(marker_end, start)
    if end == -1:
        raise ValueError('"const COLORS" not found after SECTIONS block')

    # ensure_ascii=False preserves → and other non-ASCII as literal Unicode;
    # the file is written as UTF-8, so no information is lost.
    sections_json = json.dumps(sections, ensure_ascii=False)
    new_line = marker_start + sections_json
    new_content = content[:start] + new_line + content[end:]

    if dry_run:
        print(f'[DRY RUN] Would write {len(sections_json)} chars of SECTIONS data')
        return len(sections_json)

    # Explicit UTF-8 + Unix line endings
    with open(INDEX_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_content)

    return len(sections_json)


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    try:
        print(f'Reading: {OPML_PATH}')
        if not os.path.exists(OPML_PATH):
            raise FileNotFoundError(f'OPML file not found: {OPML_PATH}')

        sections = opml_to_sections(OPML_PATH)
        section_names = [s['title'] for s in sections]
        print(f'Parsed {len(sections)} sections: {section_names}')

        chars = update_index_html(sections, dry_run=dry_run)
        if not dry_run:
            print(f'Updated index.html ({chars} chars of SECTIONS data)')
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
