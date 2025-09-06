"""Utility: Remove deprecated <field name="type"> entries from view XML files.

Odoo 18 determines the view mode (tree/list, form, kanban, search, graph, pivot,
calendar) from the root element of the arch ( <list>, <form>, <kanban>, etc.).
Leaving legacy values like <field name="type">tree</field> causes load errors
(`Wrong value for ir.ui.view.type`). Only 'qweb' remains a valid explicit type
for template-based views.

This script scans records_management/views/*.xml and removes any line that:
    - Matches <field name="type">VALUE</field>
    - Where VALUE is NOT 'qweb'

Safety: Pure line-level removal; no other transformations.
Run once, then validate module.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "records_management" / "views"
PATTERN = re.compile(r"<field\s+name=\"type\">(.*?)</field>")

def should_remove(line: str) -> bool:
    m = PATTERN.search(line)
    if not m:
        return False
    value = m.group(1).strip().lower()
    # keep only 'qweb'; everything else removed
    return value != "qweb"

def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8").splitlines(True)
    changed = False
    output_lines = []
    for line in original:
        if should_remove(line):
            changed = True
            continue
        output_lines.append(line)
    if changed:
        path.write_text("".join(output_lines), encoding="utf-8")
    return changed

def main():
    if not ROOT.exists():
        print(f"Views directory not found: {ROOT}")
        return
    xml_files = sorted(ROOT.rglob("*.xml"))
    total_changed = 0
    for f in xml_files:
        try:
            if process_file(f):
                total_changed += 1
                print(f"CLEANED: {f.relative_to(ROOT.parent)}")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"ERROR processing {f}: {exc}")
    print(f"Completed. Files modified: {total_changed}")

if __name__ == "__main__":  # pragma: no cover
    main()
