#!/usr/bin/env python3
"""
Normalize XML indentation to 4-space steps for all *.xml files under a given path.

Rules:
- Replace leading tabs with 4 spaces (tabstop = 4) – though current code has none, keep safe.
- If a line starts with spaces only, reduce leading spaces to the nearest lower multiple of 4.
  (e.g., 2 -> 0, 6 -> 4, 10 -> 8). This preserves structure without inflating lines.
- Leave lines that are blank or do not start with whitespace unchanged.

This script is conservative: it only normalizes leading whitespace and does not alter any
characters after the first non-whitespace character on a line.

Usage:
  python3 development-tools/cleanup/normalize_xml_indentation.py records_management/views

Exit codes:
  0 on success; prints a small summary of changes.
"""
from __future__ import annotations

import sys
import pathlib
from typing import Tuple


def normalize_line(line: str) -> Tuple[str, bool]:
    """Return normalized line and whether it changed.

    - Convert leading tabs to four spaces each.
    - Compute count of leading spaces; if not a multiple of 4, floor to nearest multiple of 4.
    """
    original = line
    # Early exit for empty or no leading whitespace
    if not line:
        return line, False

    i = 0
    # Count leading whitespace sequence (spaces/tabs)
    while i < len(line) and line[i] in (" ", "\t"):
        i += 1
    if i == 0:
        return line, False

    leading = line[:i]
    rest = line[i:]

    # Replace tabs with 4 spaces
    leading = leading.replace("\t", "    ")

    # Count spaces; now leading contains only spaces
    spaces = len(leading)
    # Floor to nearest multiple of 4
    if spaces:
        normalized_spaces = spaces - (spaces % 4)
    else:
        normalized_spaces = 0

    if normalized_spaces == spaces:
        # No change
        new_line = leading + rest
        return new_line, new_line != original

    new_line = (" " * normalized_spaces) + rest
    return new_line, True


def normalize_file(fp: pathlib.Path) -> Tuple[int, int, bool]:
    """Normalize a single file. Returns (total_lines, changed_lines, changed_flag)."""
    text = fp.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=False)

    changed_lines = 0
    new_lines = []
    for ln in lines:
        new_ln, changed = normalize_line(ln)
        if changed:
            changed_lines += 1
        new_lines.append(new_ln)

    if changed_lines:
        # Preserve final newline if original had one
        trailing_newline = text.endswith("\n")
        out = ("\n".join(new_lines)) + ("\n" if trailing_newline else "")
        fp.write_text(out, encoding="utf-8")
        return len(lines), changed_lines, True
    return len(lines), 0, False


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: normalize_xml_indentation.py <path> [<path> ...]", file=sys.stderr)
        return 2

    targets = [pathlib.Path(p) for p in argv[1:]]
    xml_files = []
    for t in targets:
        if t.is_file() and t.suffix.lower() == ".xml":
            xml_files.append(t)
        elif t.is_dir():
            xml_files.extend(sorted(t.rglob("*.xml")))

    total = 0
    changed_files = 0
    changed_lines_total = 0

    for fp in xml_files:
        try:
            tl, cl, ch = normalize_file(fp)
        except Exception as e:
            print(f"ERROR processing {fp}: {e}")
            continue
        total += 1
        if ch:
            changed_files += 1
            changed_lines_total += cl
            print(f"normalized: {fp} (changed lines: {cl})")

    print("\nSummary:")
    print(f"  XML files scanned: {total}")
    print(f"  Files changed:    {changed_files}")
    print(f"  Lines changed:    {changed_lines_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
