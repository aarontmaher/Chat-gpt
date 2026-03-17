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
import re
import sys
from collections import Counter

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
        if title in ('TEMPLATES', 'Main topic'):
            continue
        color = COLORS[len(sections) % len(COLORS)]
        nodes = []
        for child in section_el:
            if (child.tag == 'outline'
                    and child.get('text', '').strip()
                    and child.get('type') != 'video'):
                nodes.append(convert_node(child))
        sections.append({'title': title, 'color': color, 'nodes': nodes})

    return sections


# ---------------------------------------------------------------------------
# Perspective / schema layer names (must match SCHEMA_NAMES in index.html)
# ---------------------------------------------------------------------------

SCHEMA_NAMES = frozenset([
    'Setups / Entries', 'Control', 'Offence', 'Defence / Escapes',
    'Submissions', 'Offensive transitions', 'Defence',
    'Instructional video', 'Live video',
    'Attacker', 'Defender', 'Passer', 'Guard player',
    'You', 'Opponent', 'Initiative', 'Defensive',
    'Entries', 'Passes', 'Notes', 'Subtopic', 'Main topic',
])


# ---------------------------------------------------------------------------
# NET_NODES / NET_EDGES generation
# ---------------------------------------------------------------------------

def _make_key(section_title, text):
    """Python equivalent of makeKey() in index.html."""
    return re.sub(r'\s+', '_', (section_title + '|' + text).lower())


PERSPECTIVE_NAMES = frozenset([
    'Attacker', 'Defender', 'Passer', 'Guard player',
    'Initiative', 'Defensive', 'You', 'Opponent',
])


def _normalize_segment(s):
    """Python equivalent of normalizeSegment() in index.html."""
    s = s.strip().lower()
    s = re.sub(r'\s+', '_', s)
    s = re.sub(r'[^a-z0-9_\-]', '', s)
    s = re.sub(r'_+', '_', s)
    return s


def _build_transition_edges(sections, node_id_by_label):
    """Scan SECTIONS for OT (Offensive transitions) leaves and return weighted
    transition edges + categorized warnings.

    Canonical position = any node whose direct children include at least one
    PERSPECTIVE_NAMES entry (isCanonical).

    Walk algorithm uses a canonical_stack (push on enter, pop on leave) so
    nested canonical positions are tracked correctly.

    Edge key = (srcPositionLabel, contextLabel, destLabel) — 3-part key.
    Same context→dest from different source positions = separate edges.
    Same dest with different contextLabels = separate edges.

    Returns:
        edges          – list of {source, target, label, type, weight, ...}
        warnings       – list of human-readable warning strings
        canonical_set  – set of canonical position label strings
    """
    ARROW = _REAL_ARROW  # → (U+2192)

    # 1. Identify canonical positions: nodes with a direct perspective child
    def _is_canonical(node):
        child_labels = {c['t'] for c in node.get('c', [])}
        return bool(child_labels & PERSPECTIVE_NAMES)

    canonical_set = set()
    canonical_by_section = {}  # label -> [section_title, ...]

    def _scan_canonical(node, section_title):
        if _is_canonical(node):
            canonical_set.add(node['t'])
            canonical_by_section.setdefault(node['t'], []).append(section_title)
        for c in node.get('c', []):
            _scan_canonical(c, section_title)

    for sec in sections:
        for node in sec['nodes']:
            _scan_canonical(node, sec['title'])

    # Build normalized lookup: norm -> [{label, section}]
    norm_to_positions = {}
    for label in canonical_set:
        norm = _normalize_segment(label)
        norm_to_positions.setdefault(norm, []).append({
            'label': label,
            'sections': canonical_by_section.get(label, []),
        })

    # 2. Walk tree with canonical_stack — collect OT leaves only
    #    edge_counter key = (srcPositionLabel, contextLabel, destLabel) — 3-part key
    #    same context→dest from different source positions = separate edges
    edge_counter = Counter()          # (src, context, dest_label) -> count
    warnings = []
    canonical_stack = []              # push/pop as we enter/leave canonical nodes

    def _is_ot_heading(text):
        return text == 'Offensive transitions'

    def _walk_tree(node, section_title):
        """Recursive walk with canonical_stack push/pop."""
        t = node.get('t', '')
        children = node.get('c', [])
        pushed = False

        # On entering node: if isCanonical → push onto stack
        if _is_canonical(node):
            canonical_stack.append(t)
            pushed = True

        if _is_ot_heading(t):
            # Flatten double-wrapper: OT > OT → descend into inner
            inner_children = children
            if (len(children) == 1
                    and _is_ot_heading(children[0].get('t', ''))):
                inner_children = children[0].get('c', [])
            # Collect OT leaves
            _walk_ot_children(inner_children, section_title)
        else:
            # Not an OT heading — recurse looking for OT headings deeper
            for c in children:
                _walk_tree(c, section_title)

        # On leaving node: if we pushed → pop
        if pushed:
            canonical_stack.pop()

    def _walk_ot_children(nodes, section_title):
        """Walk children of an OT heading, collecting arrow leaves."""
        for node in nodes:
            t = node.get('t', '')
            children = node.get('c', [])
            # Filter out media children
            real_children = [c for c in children
                             if c.get('t', '') not in
                             ('Instructional video', 'Live video')]

            # Leaf with arrow = transition
            if ARROW in t and len(real_children) == 0:
                # Split at FIRST arrow only
                idx = t.index(ARROW)
                context_label = t[:idx].strip()
                dest_raw = t[idx + len(ARROW):].strip()

                current_canonical = (canonical_stack[-1]
                                     if canonical_stack else None)

                if not context_label or not dest_raw:
                    warnings.append(
                        f'MALFORMED: "{t}" (section "{section_title}")')
                elif current_canonical is None:
                    warnings.append(
                        f'NO_SRC: "{t}" — no canonical ancestor '
                        f'(section "{section_title}")')
                else:
                    dest_norm = _normalize_segment(dest_raw)
                    matches = norm_to_positions.get(dest_norm, [])

                    if len(matches) > 1:
                        candidates = ', '.join(
                            f'{m["label"]} ({"/".join(m["sections"])})'
                            for m in matches)
                        warnings.append(
                            f'AMBIG_DEST: "→ {dest_raw}" matches '
                            f'[{candidates}] '
                            f'(src: "{current_canonical}", '
                            f'section "{section_title}")')
                    elif len(matches) == 0:
                        warnings.append(
                            f'NO_DEST: "→ {dest_raw}" — no matching '
                            f'position '
                            f'(src: "{current_canonical}", '
                            f'section "{section_title}")')
                    else:
                        # Exactly 1 match — valid edge
                        resolved_dest = matches[0]['label']
                        key = (current_canonical, context_label, resolved_dest)
                        edge_counter[key] += 1
            else:
                # Recurse into non-leaf OT children
                _walk_ot_children(children, section_title)

    for sec in sections:
        for node in sec['nodes']:
            _walk_tree(node, sec['title'])

    # 3. Build edges list — one edge per unique (src, context, dest) triple
    edges = []
    for (src_label, context_label, tgt_label), weight in edge_counter.items():
        src_id = node_id_by_label.get(src_label)
        tgt_id = node_id_by_label.get(tgt_label)
        if src_id is None or tgt_id is None:
            warnings.append(
                f'UNRESOLVED: "{src_label}" → "{tgt_label}" '
                f'(context: "{context_label}") — '
                f'could not resolve node IDs')
            continue
        edges.append({
            'source': src_id,
            'target': tgt_id,
            'source_label': src_label,
            'target_label': tgt_label,
            'label': context_label,
            'type': 'transition',
            'weight': weight,
        })

    return edges, warnings, canonical_set


def sections_to_network(sections):
    """Flatten SECTIONS into NET_NODES and transition-based NET_EDGES."""
    nodes = []
    node_id = 0

    # Mapping: position label -> node ID (populated after canonical detection)
    node_id_by_label = {}

    def walk(node, section_title, section_idx, depth, parent_id):
        nonlocal node_id
        my_id = node_id
        node_id += 1
        children = node.get('c', [])
        entry = {
            'id': my_id,
            'label': node['t'],
            'section': section_title,
            'section_idx': section_idx,
            'depth': depth,
            'parent_id': parent_id,
            'children_ids': [],
            'has_video': 'v' in node,
            'video_url': node.get('v', ''),
            'key': _make_key(section_title, node['t']),
            'in_network': False,  # set after edge resolution
        }
        nodes.append(entry)
        # Recurse into children — collect actual IDs
        for c in children:
            child_id = node_id  # next ID that walk() will assign
            entry['children_ids'].append(child_id)
            walk(c, section_title, section_idx, depth + 1, my_id)

    for si, s in enumerate(sections):
        for top_node in s['nodes']:
            walk(top_node, s['title'], si, 1, None)

    # Build transition-based edges (replaces structural parent-child edges)
    # First, get canonical_set so we know which labels to register for ID lookup
    edges, warnings, canonical_set = _build_transition_edges(
        sections, {})  # empty dict — we'll re-resolve after

    # Populate node_id_by_label for all canonical positions (any depth)
    # Prefer shallowest node when labels collide
    for n in nodes:
        if n['label'] in canonical_set and n['label'] not in node_id_by_label:
            node_id_by_label[n['label']] = n['id']

    # Re-run edge building with populated label→ID map
    edges, warnings, canonical_set = _build_transition_edges(
        sections, node_id_by_label)

    # Update in_network: node participates as source or target in a transition edge,
    # OR is a shallow (depth <= 2) child of an edge participant
    trans_node_ids = set()
    for e in edges:
        trans_node_ids.add(e['source'])
        trans_node_ids.add(e['target'])

    for n in nodes:
        if n['id'] in trans_node_ids:
            # Direct edge participant (any depth)
            n['in_network'] = True
        elif n['depth'] <= 2 and n['parent_id'] in trans_node_ids:
            # Child of an edge participant (sub-positions visible with parent)
            n['in_network'] = True
        else:
            n['in_network'] = False

    return nodes, edges, warnings, canonical_set


def update_index_html(sections, net_nodes, net_edges, dry_run=False):
    """Replace const SECTIONS, NET_NODES, NET_EDGES in index.html."""
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- Replace SECTIONS ---
    marker_start = 'const SECTIONS = '
    marker_end   = '\nconst COLORS'
    start = content.find(marker_start)
    if start == -1:
        raise ValueError('"const SECTIONS = " not found in index.html')
    end = content.find(marker_end, start)
    if end == -1:
        raise ValueError('"const COLORS" not found after SECTIONS block')
    sections_json = json.dumps(sections, ensure_ascii=False)
    content = content[:start] + marker_start + sections_json + content[end:]

    # --- Replace NET_NODES ---
    nn_start_marker = '  const NET_NODES = '
    nn_start = content.find(nn_start_marker)
    if nn_start == -1:
        raise ValueError('"const NET_NODES = " not found in index.html')
    nn_end = content.find(';\n', nn_start)
    if nn_end == -1:
        raise ValueError('Could not find end of NET_NODES line')
    nn_json = json.dumps(net_nodes, ensure_ascii=False)
    content = content[:nn_start] + nn_start_marker + nn_json + content[nn_end:]

    # --- Replace NET_EDGES ---
    ne_start_marker = '  const NET_EDGES = '
    ne_start = content.find(ne_start_marker)
    if ne_start == -1:
        raise ValueError('"const NET_EDGES = " not found in index.html')
    ne_end = content.find(';\n', ne_start)
    if ne_end == -1:
        raise ValueError('Could not find end of NET_EDGES line')
    ne_json = json.dumps(net_edges, ensure_ascii=False)
    content = content[:ne_start] + ne_start_marker + ne_json + content[ne_end:]

    if dry_run:
        print(f'[DRY RUN] SECTIONS: {len(sections_json)} chars, '
              f'NET_NODES: {len(nn_json)} chars ({len(net_nodes)} nodes), '
              f'NET_EDGES: {len(ne_json)} chars ({len(net_edges)} edges)')
        return len(sections_json)

    with open(INDEX_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

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

        net_nodes, net_edges, warnings, canonical_set = sections_to_network(sections)
        in_net = sum(1 for n in net_nodes if n['in_network'])

        # Transition edge stats
        matched = len(net_edges)
        total_weight = sum(e['weight'] for e in net_edges)
        max_weight = max((e['weight'] for e in net_edges), default=0)
        print(f'Canonical positions: {len(canonical_set)}')
        print(f'Transition edges: {matched} unique | '
              f'total weight: {total_weight} | max weight: {max_weight}')

        # Categorize warnings
        no_dest = [w for w in warnings if w.startswith('NO_DEST:')]
        ambig_dest = [w for w in warnings if w.startswith('AMBIG_DEST:')]
        no_src = [w for w in warnings if w.startswith('NO_SRC:')]
        malformed = [w for w in warnings if w.startswith('MALFORMED:')]
        unresolved = [w for w in warnings if w.startswith('UNRESOLVED:')]
        other = [w for w in warnings if not any(
            w.startswith(p) for p in ('NO_DEST:', 'AMBIG_DEST:', 'NO_SRC:', 'MALFORMED:', 'UNRESOLVED:'))]

        print(f'Warnings: {len(warnings)} total '
              f'(NO_DEST: {len(no_dest)}, AMBIG_DEST: {len(ambig_dest)}, '
              f'NO_SRC: {len(no_src)}, MALFORMED: {len(malformed)}, '
              f'UNRESOLVED: {len(unresolved)})')
        for w in warnings:
            print(f'  WARN: {w}')

        print(f'Network: {len(net_nodes)} total nodes, {in_net} in_network, '
              f'{len(net_edges)} transition edges')

        chars = update_index_html(sections, net_nodes, net_edges, dry_run=dry_run)
        if not dry_run:
            print(f'Updated index.html ({chars} chars of SECTIONS data)')
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
