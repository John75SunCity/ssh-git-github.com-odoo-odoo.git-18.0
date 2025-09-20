#!/usr/bin/env python3
"""
Detect and fix nested or duplicated <data> sections under <odoo> in XML files.

Strategy (safe, conservative):
- For each XML file, find <odoo> ... </odoo> region. If not present, skip.
- Count occurrences of <data ...> and </data> within <odoo>.
- If more than one <data> open/close or if nesting depth ever exceeds 1:
    - Remove ALL <data ...> and </data> tags inside <odoo>.
    - Wrap the inner content with a SINGLE <data> ... </data> right inside <odoo>.
    - Preserve ordering and whitespace as much as possible; do not alter records.

This avoids mismatched closing tags and ensures a single well-formed data section.

Usage:
  python3 development-tools/cleanup/fix_nested_data_sections.py records_management/views
"""
from __future__ import annotations

import sys
import pathlib
import re
from typing import Tuple


OD_START = re.compile(r"<odoo[^>]*>", re.IGNORECASE)
OD_END = re.compile(r"</odoo>", re.IGNORECASE)
DATA_OPEN = re.compile(r"<data[^>]*>", re.IGNORECASE)
DATA_CLOSE = re.compile(r"</data>", re.IGNORECASE)


def fix_file(fp: pathlib.Path) -> Tuple[bool, str]:
    text = fp.read_text(encoding='utf-8', errors='replace')

    # Locate <odoo> ... </odoo>
    m_start = OD_START.search(text)
    m_end = OD_END.search(text)
    if not m_start or not m_end or m_end.start() <= m_start.end():
        return False, "no-odoo"

    before = text[:m_start.end()]
    inside = text[m_start.end():m_end.start()]
    after = text[m_end.start():]

    # Assess data structure inside <odoo>
    opens = list(DATA_OPEN.finditer(inside))
    closes = list(DATA_CLOSE.finditer(inside))

    # Quick pass to detect nesting (depth > 1)
    depth = 0
    nested = False
    idx_open = 0
    idx_close = 0
    # Merge sorted events
    events = []
    for m in opens:
        events.append((m.start(), 1))  # open
    for m in closes:
        events.append((m.start(), -1))  # close
    events.sort(key=lambda t: t[0])
    for _, ev in events:
        if ev == 1:
            depth += 1
            if depth > 1:
                nested = True
        else:
            depth = max(0, depth - 1)

    multiple = len(opens) != 1 or len(closes) != 1
    needs_fix = nested or multiple

    if not needs_fix:
        return False, "ok"

    # Remove all <data ...> and </data> tags inside
    def strip_data_tags(s: str) -> str:
        s = DATA_OPEN.sub("", s)
        s = DATA_CLOSE.sub("", s)
        return s

    content = strip_data_tags(inside)
    # Normalize surrounding whitespace minimally
    content_stripped = content.strip('\n')

    # Rebuild with a single <data> wrapper
    new_inside = "\n    <data>\n" + content_stripped + "\n    </data>\n"

    new_text = before + new_inside + after
    if new_text != text:
        fp.write_text(new_text, encoding='utf-8')
        return True, "fixed"
    return False, "nochange"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: fix_nested_data_sections.py <path> [<path> ...]", file=sys.stderr)
        return 2

    targets = [pathlib.Path(p) for p in argv[1:]]
    files = []
    for t in targets:
        if t.is_file() and t.suffix.lower() == '.xml':
            files.append(t)
        elif t.is_dir():
            files.extend(sorted(t.rglob('*.xml')))

    scanned = 0
    fixed = 0
    skipped = 0
    for fp in files:
        scanned += 1
        try:
            ch, status = fix_file(fp)
        except Exception as e:
            print(f"ERROR {fp}: {e}")
            continue
        if ch:
            fixed += 1
            print(f"fixed: {fp}")
        elif status == 'no-odoo':
            skipped += 1
        # else ok

    print("\nSummary:")
    print(f"  Files scanned: {scanned}")
    print(f"  Files fixed:  {fixed}")
    print(f"  No <odoo>:    {skipped}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
