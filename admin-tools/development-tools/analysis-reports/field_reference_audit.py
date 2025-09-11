#!/usr/bin/env python3
"""Field Reference Audit

Scans Odoo models in the target module and builds:
- Declared fields per model (map: model_name -> set(field_names))
- Computed fields (have compute= or @api.depends decorated methods)
- View field references (XML <field name="..."> for model)
- Python code field attribute references (simple heuristic: record.field_name or self.field_name inside model class)

Reports:
 1. View references to unknown fields (likely already covered elsewhere, but we cross-check again)
 2. Python references to unknown fields (attribute usage not declared as field)
 3. Declared computed fields missing @api.depends (have compute='...' but no decorator) (heuristic)
 4. Declared fields never referenced (potential dead / removable) – excluding standard metadata & technical fields

Usage:
  python3 development-tools/analysis-reports/field_reference_audit.py --module-path records_management

Limitations: heuristic only; doesn't execute Odoo environment; false positives possible.
"""
from __future__ import annotations
import ast
import re
import argparse
from pathlib import Path
from typing import Dict, Set, List, Tuple, DefaultDict
from collections import defaultdict

STD_SKIP_FIELDS = {
    "id","display_name","create_date","write_date","create_uid","write_uid","__last_update",
    # mail.thread / mail.activity common technical fields
    'message_ids','message_follower_ids','message_partner_ids','message_needaction','message_needaction_counter',
    'message_has_error','message_has_error_counter','message_attachment_count','activity_ids','activity_state',
    'activity_user_id','activity_type_id','activity_date_deadline','activity_exception_decoration',
    'activity_exception_icon','activity_summary'
}

FIELD_CALL_PREFIX = "fields."
FIELD_TYPES = {
    'Char','Text','Boolean','Integer','Float','Monetary','Many2one','One2many','Many2many','Selection','Date','Datetime','Binary','Html'
}

class ModelInfo:
    def __init__(self):
        self.fields: Set[str] = set()
        self.computed_fields: Set[str] = set()  # field names declared with compute kw
        self.compute_methods: Set[str] = set()  # method names decorated with @api.depends
        self.method_names: Set[str] = set()     # all method names (for _compute_<field> detection)
        self.depends_map: Dict[str, List[str]] = {}
        self.python_refs: Set[str] = set()
        self.view_refs: Set[str] = set()


def parse_models(module_path: Path) -> Dict[str, ModelInfo]:
    models: Dict[str, ModelInfo] = {}
    for py_file in (module_path / 'models').glob('*.py'):
        try:
            tree = ast.parse(py_file.read_text(encoding='utf-8'))
        except Exception:
            continue
        class ModelVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_model = None
                self.in_class_body = False
            def visit_ClassDef(self, node: ast.ClassDef):
                # Detect Odoo model if _name inside body
                model_name = None
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        if len(item.targets)==1 and isinstance(item.targets[0], ast.Name) and item.targets[0].id == '_name':
                            val = item.value
                            if isinstance(val, ast.Str):
                                model_name = val.s
                            elif isinstance(val, ast.Constant) and isinstance(val.value,str):
                                model_name = val.value
                prev = self.current_model
                if model_name:
                    self.current_model = model_name
                    models.setdefault(model_name, ModelInfo())
                self.generic_visit(node)
                self.current_model = prev
            def visit_Assign(self, node: ast.Assign):
                if not self.current_model:
                    return
                # field = fields.X(...)
                if len(node.targets)==1 and isinstance(node.targets[0], ast.Name):
                    tname = node.targets[0].id
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                        if isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == 'fields':
                            field_type = node.value.func.attr
                            if field_type in FIELD_TYPES:
                                models[self.current_model].fields.add(tname)
                                # detect compute kw
                                for kw in node.value.keywords:
                                    if kw.arg == 'compute':
                                        models[self.current_model].computed_fields.add(tname)
                self.generic_visit(node)
            def visit_FunctionDef(self, node: ast.FunctionDef):
                if not self.current_model:
                    return
                models[self.current_model].method_names.add(node.name)
                # collect depends decorators & note compute methods
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and hasattr(dec.func,'attr') and dec.func.attr == 'depends':
                        # args are field names
                        deps = []
                        for arg in dec.args:
                            if isinstance(arg, ast.Str):
                                deps.append(arg.s)
                            elif isinstance(arg, ast.Constant) and isinstance(arg.value,str):
                                deps.append(arg.value)
                        models[self.current_model].depends_map[node.name] = deps
                        models[self.current_model].compute_methods.add(node.name)
                # simple attribute usage scan
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Attribute) and isinstance(inner.value, ast.Name) and inner.value.id in {'self','record','rec'}:
                        models[self.current_model].python_refs.add(inner.attr)
                self.generic_visit(node)
        ModelVisitor().visit(tree)
    return models


def parse_view_fields(module_path: Path, models: Dict[str, ModelInfo]):
    """Parse ir.ui.view records and attribute fields to their model only to reduce false positives."""
    xml_files = list(module_path.glob('**/*.xml'))
    record_re = re.compile(r'<record[^>]*model="ir.ui.view"[^>]*>(.*?)</record>', re.DOTALL)
    model_field_re = re.compile(r'<field\s+name="model">([^<]+)</field>')
    arch_re = re.compile(r'<field\s+name="arch"[^>]*>(.*?)</field>', re.DOTALL)
    field_tag_re = re.compile(r'<field\s+name="([^"]+)"')
    for xml in xml_files:
        try:
            text = xml.read_text(encoding='utf-8')
        except Exception:
            continue
        for rec_match in record_re.finditer(text):
            rec_block = rec_match.group(1)
            model_match = model_field_re.search(rec_block)
            if not model_match:
                continue
            model_name = model_match.group(1).strip()
            if model_name not in models:
                continue
            arch_match = arch_re.search(rec_block)
            if not arch_match:
                continue
            arch_content = arch_match.group(1)
            for fmatch in field_tag_re.finditer(arch_content):
                fname = fmatch.group(1)
                models[model_name].view_refs.add(fname)


def build_report(models: Dict[str, ModelInfo]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {
        'unknown_view_fields': [],
        'unknown_python_refs': [],
        'computed_without_depends': [],
        'unused_declared_fields': [],
    }
    for model_name, info in sorted(models.items()):
        # 1 view unknown
        for vf in sorted(info.view_refs):
            if vf in STD_SKIP_FIELDS:
                continue
            if vf not in info.fields:
                # Heuristic: ignore x_ custom placeholders often added later
                if vf.startswith('x_'):
                    continue
                issues['unknown_view_fields'].append(f"{model_name}: {vf}")
        # 2 python unknown
        for rf in sorted(info.python_refs):
            if rf not in info.fields and rf not in STD_SKIP_FIELDS:
                issues['unknown_python_refs'].append(f"{model_name}: {rf}")
        # 3 computed w/out depends (compute kw but no declared method decorated)
        for cf in sorted(info.computed_fields):
            method_name = f"_compute_{cf}"  # common convention
            if (
                method_name not in info.depends_map
                and method_name not in info.compute_methods
                and method_name not in info.method_names
            ):
                issues['computed_without_depends'].append(f"{model_name}: {cf}")
        # 4 unused declared fields
        for fld in sorted(info.fields):
            if (
                fld not in info.view_refs
                and fld not in info.python_refs
                and fld not in info.computed_fields
                and fld not in STD_SKIP_FIELDS
            ):
                issues['unused_declared_fields'].append(f"{model_name}: {fld}")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module-path', default='records_management')
    args = parser.parse_args()
    module_path = Path(args.module_path).resolve()
    models = parse_models(module_path)
    parse_view_fields(module_path, models)
    report = build_report(models)
    print("FIELD REFERENCE AUDIT REPORT")
    try:
        for section, rows in report.items():
            print(f"\n== {section} ({len(rows)}) ==")
            for row in rows[:200]:
                print(row)
            if rows[200:]:
                print(f"... (+{len(rows)-200} more)")
    except BrokenPipeError:  # pragma: no cover
        pass
    # Simple exit code: 1 if unknown refs (critical), else 0
    if report['unknown_view_fields'] or report['unknown_python_refs']:
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
