#!/usr/bin/env python3
"""View Field *_id Audit (Enhanced)

Scans the records_management module:
 1. Builds a mapping of model -> declared field names from Python model files (direct + inherited via simple _inherit chain merge).
 2. Parses XML view files to extract every <field name="..."> reference.
 3. Flags candidate *_id (or containing `_id`) references that do NOT exist in any referenced model for that view file.
 4. Applies a WHITELIST and PATTERN_WHITELIST for pervasive framework / chatter / common relation fields to reduce noise.
 5. Outputs:
            A. Full suspicious list (post-whitelist) with location & context.
            B. Frequency summary.
            C. High-confidence subset (low-frequency & not in soft-ignore patterns).

Heuristics / Simplifications:
 - Inheritance: only single-string `_inherit = 'model.name'` merged (no list, no multiple inheritance resolution).
 - Does not parse delegated inheritance or _inherits mapping.
 - Does not introspect real Odoo registry; purely static AST scan.

Usage:
    python3 development-tools/view_field_id_audit.py > view_field_id_audit_report.txt
"""
from __future__ import annotations
import os
import re
import ast
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / 'records_management'
MODELS_DIR = MODULE / 'models'
VIEWS_DIR = MODULE / 'views'

FIELD_DEF_REGEX = re.compile(r"fields\.([A-Za-z0-9_]+)\(")
FIELD_NAME_ARG_REGEX = re.compile(r"fields\.[A-Za-z0-9_]+\(.*?['\"]([A-Za-z0-9_]+)['\"][,)]")
FIELD_TAG_REGEX = re.compile(r"<field[^>]*name=['\"]([A-Za-z0-9_.]+)['\"]")
MODEL_NAME_REGEX = re.compile(r"_name\s*=\s*['\"]([a-z0-9_.]+)['\"]")
INHERIT_NAME_REGEX = re.compile(r"_inherit\s*=\s*['\"]([a-z0-9_.]+)['\"]")  # legacy single-string pattern (kept for reference)
CLASS_REGEX = re.compile(r"class\s+([A-Za-z0-9_]+)\(")

# Whitelist for common framework / chatter / meta fields or clearly valid generic names that
# may not be declared directly in the module file due to inheritance from mail.thread etc.
WHITELIST = {
    'message_ids', 'message_follower_ids', 'activity_ids', 'activity_id', 'company_id', 'user_id',
    'partner_id', 'partner_ids', 'currency_id', 'employee_id', 'department_id', 'product_id',
    'product_uom_id', 'category_id', 'categ_id', 'parent_id', 'child_ids', 'view_id', 'search_view_id',
    'country_id', 'country_ids', 'state_id', 'state_ids', 'journal_id', 'invoice_id', 'sequence_id',
    'pos_session_id', 'pos_config_id', 'payment_method_id', 'payment_method_ids', 'uom_id', 'uom_po_id',
    'model_id', 'res_id', 'move_id', 'picking_id', 'picking_type_id', 'location_id', 'location_dest_id',
    'quant_ids', 'stock_move_ids', 'invoice_journal_id', 'template_id', 'rule_ids', 'stage_id', 'task_id',
    'task_ids', 'project_id', 'fsm_task_id', 'fsm_order_ids', 'pricing_rule_ids', 'product_variant_ids',
    # View architecture meta fields frequently present in <record model="ir.ui.view">
    'inherit_id'
}

# Pattern whitelist (regex) for frequent conventional One2many names etc. Keep short / targeted.
PATTERN_WHITELIST = [
    re.compile(r'^line_ids$'),
    re.compile(r'^.*_line_ids$'),
    re.compile(r'^.*_history_ids$'),
    re.compile(r'^.*_log_ids$'),
    re.compile(r'^.*_item_ids$'),
    re.compile(r'^.*_work_order_ids$'),
]

# Soft ignore fields (still counted but excluded from high-confidence list); noise reducers.
SOFT_IGNORE = {
    'partner_id', 'company_id', 'user_id', 'message_ids', 'message_follower_ids', 'activity_ids',
    'currency_id', 'department_id', 'product_id', 'category_id', 'categ_id', 'uom_id'
}

# Lightweight parser: collect declared fields per Python file.

def extract_model_fields(py_path: Path):
    text = py_path.read_text(encoding='utf-8', errors='ignore')
    # Quick skip if not a model file
    if '_name' not in text and '_inherit' not in text:
        return []
    try:
        tree = ast.parse(text, filename=str(py_path))
    except SyntaxError:
        return []
    models = []
    current_model = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            # Detect if inherits models.Model / models.TransientModel by name presence in bases text
            base_names = [getattr(b, 'id', None) or getattr(getattr(b, 'attr', None), 'id', None) for b in node.bases]
            base_join = ' '.join([b for b in base_names if b])
            if 'Model' not in base_join:
                continue
            # Find assignments inside class for _name / _inherit and fields
            model_name = None
            inherit_name = None
            fields_in_class = set()
            inherit_names = []
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    # _name / _inherit
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            if target.id in ('_name', '_inherit') and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                if target.id == '_name':
                                    model_name = stmt.value.value
                                else:  # single string _inherit
                                    inherit_name = stmt.value.value
                            elif target.id == '_inherit' and isinstance(stmt.value, (ast.List, ast.Tuple)):
                                # list/tuple _inherit forms
                                for elt in getattr(stmt.value, 'elts', []):
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        inherit_names.append(elt.value)
                if isinstance(stmt, ast.Assign):
                    # Field definitions: name = fields.*(...)
                    if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute):
                        if getattr(stmt.value.func.value, 'id', None) == 'fields':
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    fields_in_class.add(target.id)
            if model_name or inherit_name or inherit_names:
                # record primary first
                models.append({
                    'model': model_name or inherit_name or (inherit_names[0] if inherit_names else None),
                    'own_name': model_name,
                    'inherit_name': inherit_name,
                    'inherit_list': inherit_names,
                    'declared_fields': fields_in_class,
                    'file': py_path
                })
    return models


def build_model_field_map():
    """Build field map with simple single-chain _inherit merge.

    If a class declares _inherit = 'x' (without its own _name), we treat it as extending
    'x' and merging fields. If it declares _name AND _inherit the strategy is ambiguous; we only
    use _name as authoritative new model (merge parent's fields if known).
    """
    raw = []
    for py_file in MODELS_DIR.glob('*.py'):
        raw.extend(extract_model_fields(py_file))
    by_model = {}
    inherit_graph = {}
    for rec in raw:
        model = rec['model']
        by_model.setdefault(model, set()).update(rec['declared_fields'])
        # Single-string augmentation (_inherit only)
        if rec.get('own_name') is None and rec.get('inherit_name'):
            inherit_graph.setdefault(rec['inherit_name'], set()).add(model)
        # New model that also inherits (both _name and _inherit)
        if rec.get('own_name') and rec.get('inherit_name'):
            inherit_graph.setdefault(rec['inherit_name'], set()).add(rec['own_name'])
        # List / tuple inheritance variants
        for parent in rec.get('inherit_list', []):
            if rec.get('own_name') and parent:
                inherit_graph.setdefault(parent, set()).add(rec['own_name'])
            elif not rec.get('own_name') and parent and model != parent:
                inherit_graph.setdefault(parent, set()).add(model)
    # Propagate parent fields down one level repeatedly (simple BFS, avoid cycles)
    changed = True
    while changed:
        changed = False
        for parent, children in list(inherit_graph.items()):
            parent_fields = by_model.get(parent, set())
            for child in children:
                before = len(by_model.get(child, set()))
                by_model.setdefault(child, set()).update(parent_fields)
                after = len(by_model.get(child, set()))
                if after > before:
                    changed = True
    return by_model


def infer_model_from_view_path(xml_path: Path):
    # Heuristic: search for model="..." in same file for tree/form views
    text = xml_path.read_text(encoding='utf-8', errors='ignore')
    model_refs = set(re.findall(r"model=\"([a-z0-9_.]+)\"", text))
    # Also capture <field name="model">model.name</field> patterns inside ir.ui.view records
    for m in re.findall(r"<field\s+name=\"model\">\s*([a-z0-9_.]+)\s*</field>", text):
        model_refs.add(m)
    return model_refs


def audit_views(model_field_map):
    issues = []
    for xml_path in sorted(VIEWS_DIR.glob('*.xml')):
        text = xml_path.read_text(encoding='utf-8', errors='ignore')
        # Collect view-scoped models to map fields contextually
        models_in_file = infer_model_from_view_path(xml_path)
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            for match in FIELD_TAG_REGEX.finditer(line):
                field_full = match.group(1)
                # Skip expressions with dot path (related paths in search filter domain)
                if '.' in field_full:
                    continue
                # Candidate only if endswith _id or contains _id inside
                if '_id' not in field_full:
                    continue
                # Skip whitelisted or pattern-whitelisted fields immediately
                if field_full in WHITELIST:
                    continue
                if any(pat.match(field_full) for pat in PATTERN_WHITELIST):
                    continue
                # Attempt to validate against each model in file; if any model has it we accept
                valid_any = False
                for model_name in models_in_file:
                    declared = model_field_map.get(model_name, set())
                    if field_full in declared:
                        valid_any = True
                        break
                if not valid_any:
                    issues.append({
                        'field': field_full,
                        'xml': xml_path.relative_to(ROOT),
                        'line': idx,
                        'models': list(models_in_file) or ['<unknown>'],
                        'context': line.strip()[:200]
                    })
    return issues


def main():
    model_field_map = build_model_field_map()
    issues = audit_views(model_field_map)
    if not issues:
        print('No suspicious *_id field references found in view XML files (post-whitelist).')
        return
    print('# Suspicious *_id fields in view XML (post-whitelist, missing in static model map)')
    for issue in issues:
        print(f"- Field: {issue['field']} | Models: {','.join(issue['models'])} | File: {issue['xml']} | Line: {issue['line']} | Context: {issue['context']}")

    counter = Counter([i['field'] for i in issues])
    print('\n# Frequency by field (descending)')
    for field, count in counter.most_common():
        print(f"{field}: {count}")

    # High-confidence subset: frequency <= 2, not soft ignored, not pattern white-listed again
    high_conf = []
    for issue in issues:
        f = issue['field']
        if f in SOFT_IGNORE:
            continue
        if counter[f] > 2:
            continue
        if any(pat.match(f) for pat in PATTERN_WHITELIST):
            continue
        # Skip plural relation style names ending with _ids (likely One2many/Many2many);
        # these are normally less risky and often flagged only due to static limitations.
        if f.endswith('_ids'):
            continue
        high_conf.append(issue)
    if high_conf:
        print('\n# High-Confidence Suspicious Fields (frequency <=2, not soft-ignore)')
        for issue in high_conf:
            print(f"* {issue['field']} | File: {issue['xml']} | Line: {issue['line']} | Models: {','.join(issue['models'])}")
    else:
        print('\n# High-Confidence Suspicious Fields: None identified with current heuristics.')

if __name__ == '__main__':
    main()
