#!/usr/bin/env python3
"""Scan all ir.ui.view XML files for field references that do not exist in their models.

Lightweight, no Odoo import required. AST-parse Python model files to build a map:
    model_name -> set(fields)
Then parse XML (<record model="ir.ui.view"> or generic XML containing <field name="...")
extract model attributes from <field name="model"> inside <record> or from embedded model="..." attrs.

Outputs plain text summary plus JSON (optional) to stdout.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, Set, List

ROOT = Path(__file__).resolve().parents[2]  # repository root
MODULE = ROOT / "records_management"


def collect_model_fields(module_path: Path) -> Dict[str, Set[str]]:
    model_fields: Dict[str, Set[str]] = {}
    for py_file in module_path.rglob("*.py"):
        try:
            code = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(code)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                model_name = None
                fields: Set[str] = set()
                for item in node.body:
                    if isinstance(item, ast.Assign) and len(item.targets) == 1:
                        target = item.targets[0]
                        if isinstance(target, ast.Name):
                            # _name detection
                            if target.id == "_name":
                                val = getattr(item, "value", None)
                                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                                    model_name = val.value
                                elif isinstance(val, ast.Str):  # py<3.8 compatibility
                                    model_name = val.s
                            # fields.X detection
                            elif isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Attribute):
                                if isinstance(item.value.func.value, ast.Name) and item.value.func.value.id == "fields":
                                    fields.add(target.id)
                if model_name:
                    model_fields.setdefault(model_name, set()).update(fields)
    return model_fields


MODEL_ATTR_RE = re.compile(r'model\s*=\s*"([^"]+)"')
FIELD_TAG_RE = re.compile(r'<field\s+name="([^"]+)"')


def extract_view_models(xml_content: str) -> List[str]:
    models: List[str] = []
    for match in MODEL_ATTR_RE.finditer(xml_content):
        models.append(match.group(1))
    return models


def scan_views(module_path: Path, model_fields: Dict[str, Set[str]]):
    missing: Dict[str, Dict[str, Set[str]]] = {}
    for xml_file in module_path.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "ir.ui.view" not in content and "<form" not in content and "<tree" not in content and "<kanban" not in content:
            continue
        models = extract_view_models(content)
        if not models:
            continue
        field_refs = set(FIELD_TAG_RE.findall(content))
        # skip meta / system fields
        skip = {"id", "model", "priority", "create_uid", "create_date", "write_uid", "write_date"}
        field_refs = {f for f in field_refs if f not in skip}
        for model in models:
            available = model_fields.get(model, set())
            missing_fields = {f for f in field_refs if f not in available and not f.startswith("x_")}
            if missing_fields:
                missing.setdefault(str(xml_file.relative_to(module_path)), {}).setdefault(model, set()).update(missing_fields)
    return missing


def main():
    model_fields = collect_model_fields(MODULE / "models")
    missing = scan_views(MODULE, model_fields)
    if not missing:
        print("✅ No missing view fields detected")
        return 0
    total = 0
    print("❌ Missing view fields detected:")
    for view_path, models in missing.items():
        for model, fields in models.items():
            total += len(fields)
            field_list = ", ".join(sorted(fields))
            print(f"  - {view_path} :: model={model} -> {field_list}")
    summary = {"total_missing": total, "details": {k: {m: sorted(v) for m, v in d.items()} for k, d in missing.items()}}
    print("--- JSON SUMMARY ---")
    print(json.dumps(summary, indent=2))
    return 1 if total else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
