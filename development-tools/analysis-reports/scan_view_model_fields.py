#!/usr/bin/env python3
"""Deep View→Model Field Usage Scanner (Records Management)

Purpose:
    Identify fields referenced inside view XML architectures for module-owned
    models that are not yet defined in their Python model classes.

Why a new scanner?
    The earlier generic detector produced large noisy sets (including core
    ir.* models) and false negatives for already‑defined fields. This tool
    focuses ONLY on module (addon) owned namespaces and performs a structured
    extraction of the actual <field name="…"> tags inside the <field name="arch">'s
    embedded view architecture.

Heuristics / Scope:
    - Targets models whose technical name starts with any of these prefixes:
        ('records.', 'naid.', 'portal.', 'shredding.', 'paper.', 'chain.', 'customer.')
      (Add more prefixes if your addon defines additional namespaces.)
    - Parses each <record model="ir.ui.view">, extracts its declared target model
      from the <field name="model"> element (standard Odoo pattern).
    - Extracts the raw view architecture from <field name="arch" type="xml"> … </field>
      and regexes all <field name="XYZ" .../> usages inside.
    - Collects ALL defined Python fields via a lightweight AST + regex hybrid:
        field_name = fields.<Type>( ... )
      across addon model files.
    - Excludes meta / framework fields (id, create_date, write_uid, etc.).

Output:
    JSON report to development-tools/scan_view_model_fields_report.json plus
    a concise stdout summary. This report maps each model to:
        { 'missing': [...], 'defined': count_defined, 'referenced': count_referenced }

Limitations:
    - Does not follow inherited field additions from other addons outside this
      repository; assumes local model file visibility for custom fields.
    - Does not attempt type inference (that happens during actual implementation).

Next Step Workflow:
    1. Run this script.
    2. For each model with non-empty 'missing', implement fields in the model
       (_name file if local, else create an _inherit shim file).
    3. Re-run to confirm zero missing.

Author: Automated generation (GitHub Copilot)
"""

from __future__ import annotations

import re
import json
import sys
from pathlib import Path
from typing import Dict, Set, List, TypedDict

ADDON_ROOT_MARKER = 'records_management'
PREFIXES = (
    'records.', 'naid.', 'portal.', 'shredding.', 'paper.', 'chain.', 'customer.'
)

META_FIELDS = {
    'id', 'create_uid', 'create_date', 'write_uid', 'write_date',
    '__last_update', 'display_name', 'message_follower_ids', 'activity_ids',
    'activity_state', 'activity_exception_icon', 'activity_type_id',
    'activity_user_id', 'message_attachment_count', 'message_partner_ids',
    'message_ids', 'website_message_ids'
}

REPORT_PATH = Path('development-tools/scan_view_model_fields_report.json')

class SummaryEntry(TypedDict):
    referenced: int
    defined: int
    missing_count: int
    missing: List[str]


def collect_view_field_references(module_path: Path) -> Dict[str, Set[str]]:
    model_fields: Dict[str, Set[str]] = {}
    xml_files = list(module_path.glob('**/*.xml'))
    # Regex patterns
    field_usage_re = re.compile(r'<field\s+name="([a-zA-Z0-9_]+)"')
    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding='utf-8')
        except Exception:
            continue

        # Fast skip if file doesn't define any ir.ui.view records
        if 'model="ir.ui.view"' not in content:
            continue

        # Iterate through each <record model="ir.ui.view">
        for rec_match in re.finditer(r'<record[^>]*model="ir.ui.view"[^>]*>([\s\S]*?)</record>', content):
            rec_block = rec_match.group(1)
            # Extract target model
            model_match = re.search(r'<field\s+name="model"[^>]*>([^<]+)</field>', rec_block)
            if not model_match:
                continue
            target_model = model_match.group(1).strip()
            if not target_model.startswith(PREFIXES):
                continue  # skip external/core models

            # Extract arch block (raw) – may contain nested <field name="…">
            arch_match = re.search(r'<field\s+name="arch"[\s\S]*?>([\s\S]*?)</field>', rec_block)
            if not arch_match:
                continue
            arch_block = arch_match.group(1)
            refs = set(field_usage_re.findall(arch_block))
            if not refs:
                continue
            model_fields.setdefault(target_model, set()).update(refs)
    return model_fields


def collect_python_model_fields(module_path: Path) -> Dict[str, Set[str]]:
    defined: Dict[str, Set[str]] = {}
    model_files = list(module_path.glob('models/*.py'))
    # Patterns
    name_re = re.compile(r'^\s*_name\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
    inherit_re = re.compile(r'^\s*_inherit\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
    field_re = re.compile(r'^(?:\s{0,12})([a-zA-Z0-9_]+)\s*=\s*fields\.([A-Za-z0-9_]+)\(', re.MULTILINE)

    for mf in model_files:
        try:
            text = mf.read_text(encoding='utf-8')
        except Exception:
            continue
        # Determine the model(s) affected
        model_names: List[str] = []
        # Direct _name definitions
        model_names.extend(name_re.findall(text))
        # Pure inheritance additions also count for field definitions
        inherits = inherit_re.findall(text)
        model_names.extend([m for m in inherits if m.startswith(PREFIXES)])
        if not model_names:
            continue

        # Collect field names
        for field_name, _f_type in field_re.findall(text):
            if field_name.startswith('_'):
                continue
            for model_name in model_names:
                defined.setdefault(model_name, set()).add(field_name)
    return defined


def main() -> int:
    repo_root = Path.cwd()
    module_path = repo_root / 'records_management'
    if not module_path.exists():
        print('ERROR: Expected records_management addon root not found.')
        return 1

    view_refs = collect_view_field_references(module_path)
    defined = collect_python_model_fields(module_path)

    summary: Dict[str, SummaryEntry] = {}
    for model, refs in sorted(view_refs.items()):
        defined_fields = defined.get(model, set()) | META_FIELDS
        missing = sorted(refs - defined_fields)
        summary[model] = {
            'referenced': len(refs),
            'defined': len(defined.get(model, set())),
            'missing_count': len(missing),
            'missing': missing[:200],
        }

    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('=== View → Model Field Scan Summary (Custom Namespaces) ===')
    if not summary:
        print('No custom model view references found.')
    else:
        for model, info in summary.items():
            print(f"{model}: referenced={info['referenced']} defined={info['defined']} missing={info['missing_count']}")
            if info['missing_count']:
                # type-safe slice after TypedDict annotation
                print('  Missing sample:', ', '.join(info['missing'][:20]))
    print(f"Report written: {REPORT_PATH}")
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
