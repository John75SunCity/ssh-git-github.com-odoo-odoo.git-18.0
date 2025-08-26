#!/usr/bin/env python3
"""
Verify comodels and inverse fields across Odoo models in this module.

Checks performed:
- Collects all local model names declared via _name.
- Scans One2many/Many2one/Many2many definitions for comodel_name/positional comodel.
- Flags One2many missing its inverse Many2one on the comodel (when comodel is local).
- Flags comodels that don't exist locally and aren't in a known core allowlist (probable typo).
- Suggests probable inverse name fixes using _id naming heuristics when a close candidate exists.

Exit codes:
- 0: No blocking errors. Warnings may still be printed.
- 1: Potential problems found (unknown comodels or missing inverses).
"""
from __future__ import annotations

import ast
import warnings
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

MODULE_MODELS_DIR = os.path.join('records_management', 'models')

# Silence deprecation warnings from ast.Str on older files to keep wrapper output clean
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Common Odoo models that are valid but not defined in this module
CORE_MODEL_ALLOWLIST: Set[str] = {
    'res.partner', 'res.users', 'res.company', 'ir.attachment', 'ir.model', 'ir.sequence',
    'mail.message', 'mail.activity', 'mail.followers',
    'product.product', 'product.template', 'uom.uom',
    'account.move', 'account.move.line', 'account.journal',
    'stock.move', 'stock.picking', 'stock.location', 'stock.quant', 'stock.lot',
    'project.task', 'project.project',
    'maintenance.equipment', 'maintenance.request',
    'portal.request', 'portal.feedback',
    'hr.employee', 'hr.department',
    'sign.request', 'sms.template', 'mail.template',
    'res.country', 'res.country.state',
    'fleet.vehicle',
    'ir.ui.view', 'ir.model.fields',
    'account.payment',
    'res.groups',
    # Common core/business models often referenced
    'res.currency', 'product.category', 'crm.team', 'sale.order',
}


@dataclass
class FieldDef:
    name: str
    field_type: str  # One2many | Many2one | Many2many | other
    comodel: Optional[str] = None
    inverse_name: Optional[str] = None
    file_path: Optional[str] = None


class ModelScanner(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.current_model: Optional[str] = None
        self.models: Dict[str, List[FieldDef]] = {}
        self.model_fields: Dict[str, Set[str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Determine if this class is an Odoo model (inherits models.Model/TransientModel/AbstractModel)
        def _is_models_base(base: ast.AST, attr: str) -> bool:
            return (
                isinstance(base, ast.Attribute)
                and isinstance(base.value, ast.Name)
                and base.value.id == 'models'
                and base.attr == attr
            ) or (isinstance(base, ast.Name) and base.id == attr)

        is_odoo_model = any(
            _is_models_base(base, 'Model')
            or _is_models_base(base, 'TransientModel')
            or _is_models_base(base, 'AbstractModel')
            for base in node.bases
        )
        if not is_odoo_model:
            return

        # Find _name
        local_model_name = None
        for stmt in node.body:
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == '_name'
            ):
                if isinstance(stmt.value, ast.Str):  # Py <3.8
                    local_model_name = stmt.value.s
                    break
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):  # Py 3.8+
                    local_model_name = stmt.value.value
                    break

        if not local_model_name:
            return

        self.current_model = local_model_name
        self.models.setdefault(local_model_name, [])
        self.model_fields.setdefault(local_model_name, set())

        # Walk attributes
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                field_name = stmt.targets[0].id
                self.model_fields[local_model_name].add(field_name)
                if isinstance(stmt.value, ast.Call) and hasattr(stmt.value.func, 'attr'):
                    ftype = stmt.value.func.attr
                    if ftype in {'One2many', 'Many2one', 'Many2many'}:
                        comodel = None
                        inverse_name = None
                        # positional args
                        if stmt.value.args:
                            if isinstance(stmt.value.args[0], ast.Str):
                                comodel = stmt.value.args[0].s
                            elif isinstance(stmt.value.args[0], ast.Constant) and isinstance(stmt.value.args[0].value, str):
                                comodel = stmt.value.args[0].value
                            if ftype == 'One2many' and len(stmt.value.args) > 1:
                                if isinstance(stmt.value.args[1], ast.Str):
                                    inverse_name = stmt.value.args[1].s
                                elif isinstance(stmt.value.args[1], ast.Constant) and isinstance(stmt.value.args[1].value, str):
                                    inverse_name = stmt.value.args[1].value
                        # keyword args
                        for kw in stmt.value.keywords:
                            if kw.arg == 'comodel_name':
                                if isinstance(kw.value, ast.Str):
                                    comodel = kw.value.s
                                elif isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                    comodel = kw.value.value
                            if kw.arg == 'inverse_name':
                                if isinstance(kw.value, ast.Str):
                                    inverse_name = kw.value.s
                                elif isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                    inverse_name = kw.value.value

                        self.models[local_model_name].append(FieldDef(
                            name=field_name,
                            field_type=ftype,
                            comodel=comodel,
                            inverse_name=inverse_name,
                            file_path=self.file_path,
                        ))


def collect_local_models(base_dir: str) -> Tuple[Dict[str, List[FieldDef]], Dict[str, Set[str]]]:
    aggregated_models: Dict[str, List[FieldDef]] = {}
    aggregated_fields: Dict[str, Set[str]] = {}

    for root, _, files in os.walk(base_dir):
        for fn in files:
            if not fn.endswith('.py') or fn == '__init__.py':
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=path)
                scanner = ModelScanner(path)
                scanner.visit(tree)
                for m, fields in scanner.models.items():
                    aggregated_models.setdefault(m, []).extend(fields)
                for m, names in scanner.model_fields.items():
                    aggregated_fields.setdefault(m, set()).update(names)
            except SyntaxError as e:
                print(f"WARN: Could not parse {path}: {e}", file=sys.stderr)

    return aggregated_models, aggregated_fields


def suggest_inverse_candidate(inverse_name: str, comodel_fields: Set[str]) -> Optional[str]:
    # If inverse_name is 'x_id' but only 'x' exists, or vice versa, suggest it.
    if inverse_name.endswith('_id') and inverse_name[:-3] in comodel_fields:
        return inverse_name[:-3]
    if (inverse_name + '_id') in comodel_fields:
        return inverse_name + '_id'
    return None


def main() -> int:
    if not os.path.isdir(MODULE_MODELS_DIR):
        print(f"Error: Directory not found at '{MODULE_MODELS_DIR}'. Run from repo root.", file=sys.stderr)
        return 2

    models_map, fields_map = collect_local_models(MODULE_MODELS_DIR)

    unknown_comodels: List[Tuple[str, str, str, str]] = []  # (model, field, comodel, file)
    missing_inverses: List[Tuple[str, str, str, str, str]] = []  # (o2m_model, o2m_field, comodel, inverse_name, file)
    suggestions: List[Tuple[str, str, str, str, str]] = []  # (o2m_model, o2m_field, comodel, suggested, file)

    for model, fields in models_map.items():
        for fd in fields:
            if fd.field_type in {'One2many', 'Many2one', 'Many2many'}:
                comodel = fd.comodel
                if not comodel:
                    continue
                if comodel not in fields_map and comodel not in CORE_MODEL_ALLOWLIST:
                    unknown_comodels.append((model, fd.name, comodel, fd.file_path or '?'))
                if fd.field_type == 'One2many' and fd.inverse_name and comodel in fields_map:
                    if fd.inverse_name not in fields_map[comodel]:
                        # Missing exact inverse
                        missing_inverses.append((model, fd.name, comodel, fd.inverse_name, fd.file_path or '?'))
                        # Try suggestion
                        sugg = suggest_inverse_candidate(fd.inverse_name, fields_map[comodel])
                        if sugg:
                            suggestions.append((model, fd.name, comodel, sugg, fd.file_path or '?'))

    exit_code = 0
    if unknown_comodels or missing_inverses:
        exit_code = 1

    print("\n=== Comodels & Inverses Audit ===")
    print(f"Scanned models dir: {MODULE_MODELS_DIR}")

    if unknown_comodels:
        print("\nPotential unknown comodels (typos or external models not in allowlist):")
        for m, f, cm, fp in unknown_comodels:
            print(f"  - {m}.{f}: comodel='{cm}' (file: {fp})")
    else:
        print("\nNo unknown comodels detected.")

    if missing_inverses:
        print("\nOne2many fields missing inverse Many2one on comodel:")
        for m, f, cm, inv, fp in missing_inverses:
            print(f"  - {m}.{f} → {cm}.{inv} (missing) (file: {fp})")
    else:
        print("\nNo missing inverses detected for local comodels.")

    if suggestions:
        print("\nSuggested inverse name candidates:")
        for m, f, cm, s, fp in suggestions:
            print(f"  - {m}.{f}: consider inverse_name='{s}' on {cm} (file: {fp})")

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
