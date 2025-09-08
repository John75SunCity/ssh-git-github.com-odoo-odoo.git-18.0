#!/usr/bin/env python3
"""Generate a deterministically ordered data file list for the module manifest.

Goals:
  - Provide stable, dependency-aware grouping (security → core → config → pricing → indexes → mail → cron → custom config → early action views → menus → wizard views → standard views → reports → templates).
  - Preserve lines 1-16 of the original manifest (caller is responsible when applying changes).
  - Allow dry-run printing or writing back in-place.

Limitations:
  - This is heuristic: it does not parse XML dependencies. You can extend CATEGORY_RULES with
    smarter predicates (e.g., parse actions referenced by menus) if needed.

Usage:
  python3 development-tools/generate_manifest_data_order.py --manifest records_management/__manifest__.py --print
  python3 development-tools/generate_manifest_data_order.py --manifest records_management/__manifest__.py --write

Exit status 0 on success; non‑zero on failure.
"""
from __future__ import annotations
import argparse
import ast
import pathlib
import sys
from typing import Callable, Dict, List, Tuple

Category = str

# Ordered list of category names (display + output order)
CATEGORY_ORDER: List[Category] = [
    "security",
    "sequences",
    "core",
    "base_config",
    "pricing_rates",
    "naid",
    "feedback_survey",
    "indexes_tags",
    "mail_templates_activity",
    "scheduled_actions_cron",
    "custom_config",
    "early_action_views",
    "root_menus",
    "wizard_views",
    "model_views",
    "reports",
    "templates",
]

# Predicates: each returns True if file belongs to that category.
# First matching category wins; unclassified views/data fall back to model_views or base_config heuristics.
CATEGORY_RULES: List[Tuple[Category, Callable[[str], bool]]] = [
    ("security", lambda f: f.startswith("security/")),
    ("sequences", lambda f: "sequence" in f),
    ("core", lambda f: f in {"data/core_records_data.xml", "data/load_data.xml"}),
    ("base_config", lambda f: any(k in f for k in [
        "container_types_base_rates", "paper_shred_configurator", "paper_products_data"])),
    ("pricing_rates", lambda f: any(k in f for k in ["retrieval_rate", "retrieval_rates", "rates_data", "storage_fee", "products_data", "document_retrieval_rates_data", "storage_fee_data"])),
    ("naid", lambda f: "naid_" in f and "certificate" not in f),
    ("feedback_survey", lambda f: "feedback_survey" in f),
    ("indexes_tags", lambda f: "intelligent_search_indexes" in f or f.endswith("tag_data.xml")),
    ("mail_templates_activity", lambda f: "mail_activity" in f or "mail_templates" in f),
    ("scheduled_actions_cron", lambda f: "cron" in f or "scheduled_actions" in f),
    ("custom_config", lambda f: any(k in f for k in ["temp_inventory_configurator", "field_label_customization"])),
    ("early_action_views", lambda f: f in {
        "views/records_digital_scan_views.xml",
        "views/field_label_helper_wizard_views.xml",
        "views/report_window_actions_views.xml",
    }),
    ("root_menus", lambda f: f.endswith("_menus.xml")),
    ("wizard_views", lambda f: f.startswith("views/") and ("_wizard_" in f or f.endswith("_wizard_views.xml"))),
    ("reports", lambda f: f.startswith("report/")),
    ("templates", lambda f: f.startswith("templates/")),
    # model_views fallback below
]

HEADER_COMMENTS: Dict[Category, str] = {
    "security": "Security & access control must load first.",
    "sequences": "Sequences before any records referencing them.",
    "core": "Core baseline data & mandatory load scaffolding.",
    "base_config": "Base configuration & framework data (container types, configurators).",
    "pricing_rates": "Pricing & rate configuration (products, fees, retrieval rates).",
    "naid": "NAID framework data prior to dependent artifacts.",
    "feedback_survey": "Feedback & survey seed data.",
    "indexes_tags": "Search indexes & tag taxonomy.",
    "mail_templates_activity": "Mail activity types & templates.",
    "scheduled_actions_cron": "Scheduled actions / cron definitions.",
    "custom_config": "Custom configurator & field label customization batches.",
    "early_action_views": "Early action views defining ir.actions.* required by subsequent menus.",
    "root_menus": "Root menu definitions before child wizard/model views.",
    "wizard_views": "Wizard views (transient models).",
    "model_views": "Standard model views (forms, lists, kanbans).",
    "reports": "Report definitions loaded after all views.",
    "templates": "QWeb / portal templates last.",
}

def classify(path: str) -> Category:
    for cat, pred in CATEGORY_RULES:
        if pred(path):
            return cat
    if path.startswith("views/"):
        return "model_views"
    # Fallback: treat remaining data files as base_config unless already covered
    if path.startswith("data/"):
        return "base_config"
    return "model_views"


def load_manifest(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        data = ast.literal_eval(text)
    except Exception as e:  # pragma: no cover
        print(f"ERROR: Unable to parse manifest {path}: {e}", file=sys.stderr)
        sys.exit(2)
    return data


def build_order(data_files: List[str]) -> List[str]:
    buckets: Dict[Category, List[str]] = {c: [] for c in CATEGORY_ORDER}
    unknown: List[str] = []
    for f in data_files:
        cat = classify(f)
        if cat in buckets:
            buckets[cat].append(f)
        else:
            unknown.append(f)
    # Sort each bucket alphabetically for determinism EXCEPT early_action_views where original relative order matters.
    for cat, files in buckets.items():
        if cat == "early_action_views":
            # Preserve insertion order
            continue
        files.sort()
    if unknown:
        buckets.setdefault("model_views", []).extend(sorted(unknown))
    # Flatten with comments
    ordered: List[str] = []
    for cat in CATEGORY_ORDER:
        bucket = buckets.get(cat) or []
        if not bucket:
            continue
        ordered.append(f"# --- {cat}: {HEADER_COMMENTS.get(cat, cat)}")
        ordered.extend(bucket)
    return ordered


def render_data_block(ordered: List[str]) -> str:
    lines = []
    for item in ordered:
        if item.startswith('#'):
            lines.append(f"        {item}")
        else:
            lines.append(f"        \"{item}\",")
    # Remove trailing comma from last real file for cleanliness
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('"'):  # pragma: no branch
            lines[i] = lines[i].rstrip(',')
            break
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default='records_management/__manifest__.py')
    ap.add_argument('--print', dest='do_print', action='store_true', help='Print reordered list to stdout')
    ap.add_argument('--write', action='store_true', help='Write reordered data list back into manifest file')
    args = ap.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest = load_manifest(manifest_path)
    data_files = manifest.get('data', [])
    if not isinstance(data_files, list):
        print('ERROR: manifest["data"] is not a list', file=sys.stderr)
        sys.exit(3)

    ordered = build_order([f for f in data_files if isinstance(f, str)])
    block = render_data_block(ordered)

    if args.do_print:
        print(block)

    if args.write:
        original_lines = manifest_path.read_text(encoding='utf-8').splitlines()
        # Identify start & end of existing data list for replacement (simple heuristic)
        start_idx = None
        end_idx = None
        for i, line in enumerate(original_lines):
            if start_idx is None and line.strip().startswith('"data"') and line.rstrip().endswith('['):
                start_idx = i + 1
                continue
            if start_idx is not None:
                # End when we find closing bracket followed by optional comma
                if line.strip() == '],' or line.strip() == ']':
                    end_idx = i
                    break
        if start_idx is None or end_idx is None:
            print('ERROR: Unable to locate data list boundaries in manifest.', file=sys.stderr)
            sys.exit(4)
        # Preserve everything outside the data block
        new_lines = original_lines[:start_idx] + [block] + original_lines[end_idx:]
        manifest_path.write_text("\n".join(new_lines) + "\n", encoding='utf-8')
        print(f"Updated manifest data ordering with {len(ordered)} entries across categories.")

if __name__ == '__main__':  # pragma: no cover
    main()
