#!/usr/bin/env python3
"""Custom Field Normalization Audit

Goal: Identify custom fields that duplicate or overlap standard Odoo core concepts
so we can potentially remove or refactor them to reduce maintenance overhead.

Heuristics Applied:
- Detect models inheriting/res.inheriting core models (res.partner, res.company, product.template, etc.)
- Gather custom field names that look like duplicates of standard metadata (email, phone, mobile, company_id, user_id)
- Suggest replacement when a custom field resembles a standard one already present in the inheritance chain.
- Flag boolean or selection status fields that mirror existing 'state', 'active', 'company_id' or misnamed partners.

Limitations: Heuristic string checks only; does NOT introspect actual registry.

Output Sections:
 1. potential_duplicates: field appears similar to a standard field probably already provided
 2. redundant_state_like: multiple status fields where one standard 'state' already exists
 3. company_tracking_overlaps: fields duplicating company/user ownership
 4. contact_info_overlaps: duplicate email/phone/mobile fields
 5. low_value_text_blobs: large text fields that might be mergeable

Usage:
  python3 development-tools/analysis-reports/custom_field_normalization_audit.py --module-path records_management
"""
from __future__ import annotations
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Set

STANDARD_CONTACT_FIELDS = {"email","phone","mobile","website","fax"}
STANDARD_OWNERSHIP_FIELDS = {"company_id","user_id","owner_id","partner_id"}
STATE_FIELD_NAMES = {"state","status","stage","lifecycle_state"}
LOW_VALUE_TEXT_HINTS = {"notes","description","internal_notes","comments"}

CORE_MODEL_KEYWORDS = {
    'res.partner','res.company','product.template','product.product','mail.thread','mail.activity.mixin'
}

class FieldDef:
    def __init__(self, name: str, field_type: str, compute: bool, string_label: str|None):
        self.name = name
        self.field_type = field_type
        self.compute = compute
        self.string_label = string_label or ''

class ModelDef:
    def __init__(self):
        self.name: str|None = None
        self.inherits: List[str] = []  # _inherit(s)
        self.fields: Dict[str, FieldDef] = {}


def parse_models(module_path: Path) -> Dict[str, ModelDef]:
    models: Dict[str, ModelDef] = {}
    for py_file in (module_path / 'models').glob('*.py'):
        try:
            tree = ast.parse(py_file.read_text(encoding='utf-8'))
        except Exception:
            continue
        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.current: ModelDef|None = None
            def visit_ClassDef(self, node: ast.ClassDef):
                local = ModelDef()
                model_key = None
                inherits: List[str] = []
                # first pass assignments
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and len(stmt.targets)==1 and isinstance(stmt.targets[0], ast.Name):
                        tname = stmt.targets[0].id
                        if tname == '_name':
                            val = stmt.value
                            if isinstance(val, ast.Constant) and isinstance(val.value,str):
                                model_key = val.value
                        elif tname == '_inherit':
                            val = stmt.value
                            if isinstance(val, ast.Constant) and isinstance(val.value,str):
                                inherits.append(val.value)
                            elif isinstance(val, (ast.List, ast.Tuple)):
                                for elt in val.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value,str):
                                        inherits.append(elt.value)
                if not model_key and not inherits:
                    return
                if not model_key and inherits:
                    # pure extension - synthesize key from first inherit
                    model_key = inherits[0]
                local.name = model_key
                local.inherits = inherits
                # second pass: field definitions
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and len(stmt.targets)==1 and isinstance(stmt.targets[0], ast.Name):
                        fname = stmt.targets[0].id
                        if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute):
                            if isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == 'fields':
                                ftype = stmt.value.func.attr
                                compute = False
                                label = None
                                for kw in stmt.value.keywords:
                                    if kw.arg == 'compute':
                                        compute = True
                                    elif kw.arg == 'string':
                                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value,str):
                                            label = kw.value.value
                                local.fields[fname] = FieldDef(fname, ftype, compute, label)
                if local.name:
                    models.setdefault(local.name, local)
        Visitor().visit(tree)
    return models


def analyze(models: Dict[str, ModelDef]):
    potential_duplicates: List[str] = []
    redundant_state_like: List[str] = []
    company_tracking_overlaps: List[str] = []
    contact_info_overlaps: List[str] = []
    low_value_text_blobs: List[str] = []

    for mname, mdef in models.items():
        # Determine if model extends core entity
        inherits_core = any(base in CORE_MODEL_KEYWORDS for base in mdef.inherits)
        field_names = set(mdef.fields.keys())

        # Contact info duplicates
        for std in STANDARD_CONTACT_FIELDS:
            alt_candidates = {f for f in field_names if f.replace('primary_','').replace('main_','') == std or f.endswith('_'+std)}
            if (alt_candidates and (std not in field_names or len(alt_candidates) > 1)):
                for c in sorted(alt_candidates):
                    contact_info_overlaps.append(f"{mname}: {c} -> consider using standard '{std}'")

        # Ownership duplicates
        for std in STANDARD_OWNERSHIP_FIELDS:
            dupe_variants = {f for f in field_names if f.endswith('_'+std.replace('_id','')) and f not in STANDARD_OWNERSHIP_FIELDS}
            for dv in dupe_variants:
                company_tracking_overlaps.append(f"{mname}: {dv} ~ '{std}'")

        # Multiple state-like fields
        state_like = [f for f in field_names if f in STATE_FIELD_NAMES or f.endswith('_state') or f.endswith('_status')]
        if state_like and len(state_like) > 1:
            redundant_state_like.append(f"{mname}: {', '.join(sorted(state_like))}")

        # Potential duplicates: generic naming patterns
        for f, fd in mdef.fields.items():
            base = f.rstrip('_id')
            if f in STANDARD_CONTACT_FIELDS | STANDARD_OWNERSHIP_FIELDS:
                continue
            if f.endswith('_name') and 'name' in mdef.fields:
                potential_duplicates.append(f"{mname}: {f} duplicates core 'name'")
            if f.startswith('primary_') and f[8:] in field_names:
                potential_duplicates.append(f"{mname}: {f} vs {f[8:]}")
            if inherits_core and f in {'email_alt','email_secondary','phone_alt','mobile_alt'}:
                potential_duplicates.append(f"{mname}: {f} consider merging with standard contact fields")
            # Low value text
            if fd.field_type in {'Text','Html'} and (fd.name in LOW_VALUE_TEXT_HINTS or fd.string_label.lower() in LOW_VALUE_TEXT_HINTS):
                if not fd.compute:
                    low_value_text_blobs.append(f"{mname}: {fd.name} ({fd.field_type}) may be mergeable")

    return {
        'potential_duplicates': potential_duplicates,
        'redundant_state_like': redundant_state_like,
        'company_tracking_overlaps': company_tracking_overlaps,
        'contact_info_overlaps': contact_info_overlaps,
        'low_value_text_blobs': low_value_text_blobs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--module-path', default='records_management')
    args = ap.parse_args()
    module_path = Path(args.module_path)
    models = parse_models(module_path)
    report = analyze(models)
    print("CUSTOM FIELD NORMALIZATION AUDIT")
    for section, rows in report.items():
        print(f"\n== {section} ({len(rows)}) ==")
        for line in rows[:200]:
            print(line)
        if rows[200:]:
            print(f"... (+{len(rows)-200} more)")
    # exit non-zero if lots of potential duplicates
    if report['potential_duplicates'] or report['contact_info_overlaps']:
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
