#!/usr/bin/env python3
"""Missing View Fields Scanner (precision version)

Accurately maps field references inside each ir.ui.view record's arch to the view's target model.

Why rewrite? Previous simplistic regex approach massively over-reported because it:
  * Associated ALL <field name="..."> occurrences in a file with ALL model="..." attributes in that file.
  * Reported "missing" fields for core models (ir.ui.view, ir.actions.act_window, etc.).

Strategy now:
  1. AST-parse Python model files to build model -> declared field set.
  2. XML-parse each view file; for each <record model="ir.ui.view"> capture the view model from
     <field name="model"> or arch root's model attribute.
  3. Parse the embedded arch XML; collect <field name="..."> entries only within that arch (not whole file).
  4. Compare to declared fields, ignoring meta/system/chatter & core ir.* models.

Limitations:
  * Does not resolve inherited view (inherit_id) field removals / additions from other modules.
  * Does not execute python, relies on static AST.
  * Skips models starting with 'ir.' and 'res.config.' to avoid core/admin noise.

Exit code 0 always (informational) to keep pipelines non-blocking unless --strict passed.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "records_management"
MODELS_DIR = MODULE / "models"
VIEWS_DIR = MODULE / "views"

META_FIELDS = {
    "id", "create_uid", "write_uid", "create_date", "write_date", "display_name", "__last_update",
    # typical technical / arch fields
    "arch", "model", "inherit_id", "name", "priority", "view_mode", "view_id", "type", "sequence"
}

CORE_MODEL_PREFIXES = ("ir.", "res.config.")


class ModelFieldCollector(ast.NodeVisitor):
    def __init__(self):
        self.current_model: str | None = None
        self.model_fields: Dict[str, Set[str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        model_name = None
        # first pass: find _name
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == '_name':
                        val = getattr(stmt, 'value', None)
                        if isinstance(val, ast.Constant) and isinstance(val.value, str):
                            model_name = val.value
                        elif hasattr(ast, 'Str') and isinstance(val, ast.Str):  # py<3.8
                            model_name = val.s
        if model_name:
            fields: Set[str] = set()
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            val = stmt.value
                            if (
                                isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute)
                                and isinstance(val.func.value, ast.Name) and val.func.value.id == 'fields'
                            ):
                                fields.add(target.id)
            existing = self.model_fields.setdefault(model_name, set())
            existing.update(fields)
        # continue walking (nested classes rarely define models but safe)
        self.generic_visit(node)


def collect_python_model_fields() -> Dict[str, Set[str]]:
    collector = ModelFieldCollector()
    for py_file in MODELS_DIR.rglob('*.py'):
        try:
            code = py_file.read_text(encoding='utf-8')
            tree = ast.parse(code, filename=str(py_file))
            collector.visit(tree)
        except Exception:
            continue
    return collector.model_fields


def extract_view_arch_records(view_xml: Path) -> List[Tuple[str, ET.Element]]:
    """Return list of (model_name, arch_root_element) for each ir.ui.view record."""
    try:
        tree = ET.parse(view_xml)
    except ET.ParseError:
        return []
    root = tree.getroot()
    result: List[Tuple[str, ET.Element]] = []
    for rec in root.findall('record'):
        if rec.get('model') != 'ir.ui.view':
            continue
        # get model from field name="model"
        model_name = None
        for f in rec.findall('field'):
            if f.get('name') == 'model' and f.text:
                model_name = f.text.strip()
                break
        arch_field = rec.find("field[@name='arch']")
        if not arch_field or arch_field.text is None:
            continue
        try:
            arch_root = ET.fromstring(arch_field.text)
        except ET.ParseError:
            continue
        if not model_name:
            # fallback to arch root 'model' attribute
            model_name = arch_root.get('model')
        if not model_name:
            continue
        result.append((model_name, arch_root))
    return result


def collect_view_field_references() -> Dict[str, Set[str]]:
    model_fields_needed: Dict[str, Set[str]] = {}
    for xml in VIEWS_DIR.glob('*.xml'):
        for model_name, arch_root in extract_view_arch_records(xml):
            if model_name.startswith(CORE_MODEL_PREFIXES):
                continue
            needed = model_fields_needed.setdefault(model_name, set())
            for field_el in arch_root.findall('.//field'):
                fname = field_el.get('name')
                if not fname:
                    continue
                # ignore meta/system
                if fname in META_FIELDS:
                    continue
                needed.add(fname)
    return model_fields_needed


def diff_missing_fields(declared: Dict[str, Set[str]], referenced: Dict[str, Set[str]]):
    missing: Dict[str, List[str]] = {}
    for model, refs in referenced.items():
        model_declared = declared.get(model, set())
        diff = [f for f in sorted(refs) if f not in model_declared and not f.startswith('x_')]
        if diff:
            missing[model] = diff
    return missing


def main(argv: List[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Scan for view-referenced fields missing in model definitions")
    parser.add_argument('--json', dest='json_out', help='Write JSON report to file path')
    parser.add_argument('--strict', action='store_true', help='Exit 1 if any missing fields found')
    args = parser.parse_args(argv)

    declared = collect_python_model_fields()
    referenced = collect_view_field_references()
    missing = diff_missing_fields(declared, referenced)

    if not missing:
        print("✅ All view-referenced fields are declared (within scanner limits).")
    else:
        print("❌ Missing view fields (custom models):")
        total = 0
        for model, fields in sorted(missing.items()):
            total += len(fields)
            preview = ', '.join(fields[:12]) + ('...' if fields[12:] else '')
            print(f"  - {model}: {len(fields)} missing -> {preview}")
        print(f"\nTotal missing fields: {total} across {len(missing)} models")

    report = {
        'summary': {
            'models_with_missing': len(missing),
            'total_missing_fields': sum(len(v) for v in missing.values()),
        },
        'missing': missing,
    }
    if args.json_out:
        try:
            Path(args.json_out).write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(f"Report written to {args.json_out}")
        except Exception as e:
            print(f"Failed to write JSON report: {e}")

    return 1 if (args.strict and missing) else 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
