"""Menu/Action Integrity Audit Tool for records_management module.

Scans XML files for:
 1. ir.ui.menu records referencing missing actions
 2. ir.actions.act_window definitions without a referencing menu (potential orphan)
 3. Duplicate XML IDs across menus/actions
 4. Menus referencing actions defined later in the same file (load-order risk heuristic)

Output: Structured textual report to stdout.
"""
from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict

MODULE_NAME = "records_management"
BASE = Path(__file__).resolve().parent.parent / MODULE_NAME / "views"

MENU_PATTERN = re.compile(r"<record[^>]*id=\"([^\"]+)\"[^>]*model=\"ir.ui.menu\"[\s\S]*?</record>")
ACTION_PATTERN = re.compile(r"<record[^>]*id=\"([^\"]+)\"[^>]*model=\"ir.actions.act_window\"[\s\S]*?</record>")
ACTION_REF_PATTERN = re.compile(r"<field[^>]*name=\"action\">([^<]+)</field>")

def extract_records(xml: str, pattern: re.Pattern) -> dict[str, str]:
    return {m.group(1): m.group(0) for m in pattern.finditer(xml)}

def _collect_window_refs(xml: str) -> list[str]:
    refs = []
    for m in ACTION_REF_PATTERN.finditer(xml):
        raw = m.group(1).strip()
        if raw.startswith("ir.actions"):  # legacy style not expected
            continue
        # Accept both module.action and action id
        if "." in raw:
            _, action_id = raw.split(".", 1)
        else:
            action_id = raw
        refs.append(action_id)
    return refs

def scan():
    xml_files = sorted(BASE.glob("*.xml"))
    all_actions: dict[str, tuple[str, str]] = {}
    all_menus: dict[str, tuple[str, str]] = {}
    action_refs: list[tuple[str, str]] = []  # (file, action_id)
    duplicates = defaultdict(list)

    for f in xml_files:
        content = f.read_text(encoding="utf-8")
        actions = extract_records(content, ACTION_PATTERN)
        menus = extract_records(content, MENU_PATTERN)
        refs = _collect_window_refs(content)

        for aid, block in actions.items():
            if aid in all_actions:
                duplicates[aid].append(str(f))
            all_actions[aid] = (str(f), block)
        for mid, block in menus.items():
            if mid in all_menus:
                duplicates[mid].append(str(f))
            all_menus[mid] = (str(f), block)
        for r in refs:
            action_refs.append((str(f), r))

    referenced = {r for _, r in action_refs}
    orphan_actions = [a for a in all_actions if a not in referenced]
    missing_actions = [r for r in referenced if r not in all_actions]

    # Heuristic: menu referencing action defined later in same file when order index higher
    load_order_risks = []
    for file_path in {f for f, _ in action_refs}:
        content = Path(file_path).read_text(encoding="utf-8")
        # collect positions
        positions = {}
        for aid, (af, _) in all_actions.items():
            if af == file_path:
                idx = content.find(f'id="{aid}"')
                if idx >= 0:
                    positions[aid] = idx
        for fpath, aid in [ar for ar in action_refs if ar[0] == file_path]:
            if aid in positions:
                # find menu reference location
                ref_idx = content.find(f">{aid}<")
                if ref_idx >= 0 and ref_idx < positions[aid] - 10:  # referenced before definition
                    load_order_risks.append((aid, file_path))

    print("=== MENU/ACTION INTEGRITY REPORT ===")
    print(f"Scanned XML files in: {BASE}")
    print("")
    print("-- Missing Actions (referenced by menus) --")
    if missing_actions:
        for a in sorted(set(missing_actions)):
            locs = [f for f, r in action_refs if r == a]
            print(f"  * {a} (referenced in: {', '.join(sorted(set(locs)))})")
    else:
        print("  None ✅")
    print("")
    print("-- Orphan Actions (no menu references) --")
    if orphan_actions:
        for a in sorted(orphan_actions):
            print(f"  * {a} (defined in {all_actions[a][0]})")
    else:
        print("  None ✅")
    print("")
    print("-- Duplicate XML IDs --")
    if duplicates:
        for did, files in duplicates.items():
            print(f"  * {did}: {', '.join(files)}")
    else:
        print("  None ✅")
    print("")
    print("-- Load-Order Risk (reference before definition in same file) --")
    if load_order_risks:
        for aid, f in load_order_risks:
            print(f"  * {aid} in {f}")
    else:
        print("  None ✅")
    print("")
    print("Summary:")
    print(f"  Actions: {len(all_actions)} | Menus: {len(all_menus)} | Referenced Actions: {len(referenced)}")
    print("  Status: COMPLETE")

if __name__ == "__main__":  # pragma: no cover
    scan()
