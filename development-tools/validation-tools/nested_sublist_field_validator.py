#!/usr/bin/env python3
"""
Nested Sublist Field Validator for Odoo Views
=============================================

Purpose:
- Parse Odoo XML view files to find nested sublist definitions (One2many fields with mode="list").
- Identify the comodel of each One2many using model files.
- Validate that the inner <list> fields exist on the comodel.

Scope:
- Scans `records_management/models/**/*.py` for model definitions and fields.
- Scans `records_management/views/**/*.xml` for <record model="ir.ui.view"> with nested <list> under <field name="...">.
- Reports any inner field names that don't exist on the comodel.

Limitations:
- Static analysis only; does not import Odoo.
- Field detection is regex-based and may miss dynamic constructs.

Usage:
  python3 development-tools/validation-tools/nested_sublist_field_validator.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


MODEL_FILE_GLOB = "records_management/models/**/*.py"
VIEW_FILE_GLOB = "records_management/views/**/*.xml"


@dataclass
class ModelInfo:
    name: str
    fields: Dict[str, str] = field(default_factory=dict)  # field_name -> type


def parse_models() -> Dict[str, ModelInfo]:
    """Build a map of model technical names to their fields.

    Detects:
    - _name = 'model.name'
    - fields.<Type>(... string or not), captures field name
    """
    models: Dict[str, ModelInfo] = {}
    for py in Path("records_management/models").rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue

        # Find model name(s)
        # Anchor to start-of-line to avoid matching res_name/comodel_name
        for m in re.finditer(r"^\s*_name\s*=\s*['\"]([\w\.]+)['\"]", text, re.M):
            model_name = m.group(1)
            models.setdefault(model_name, ModelInfo(name=model_name))

        # Collect simple field defs:  field_name = fields.Type(
        # NOTE: Field type names in Odoo can contain digits (e.g., Many2one, One2many, Many2many),
        # so allow 0-9 in the type token.
        for f in re.finditer(r"^(\s*)([a-zA-Z_][\w]*)\s*=\s*fields\.([A-Za-z0-9_]+)\(", text, re.M):
            field_name = f.group(2)
            field_type = f.group(3)
            # Heuristic: attribute belongs to the last declared model in file; acceptable for our codebase
            # Enhance by segmenting classes if needed
            # Try to locate nearest preceding _name definition
            before = text[: f.start()]
            nearest = list(re.finditer(r"^\s*_name\s*=\s*['\"]([\w\.]+)['\"]", before, re.M))
            if not nearest:
                continue
            model_name = nearest[-1].group(1)
            models.setdefault(model_name, ModelInfo(name=model_name))
            models[model_name].fields[field_name] = field_type

    return models


def get_one2many_map(models: Dict[str, ModelInfo]) -> Dict[Tuple[str, str], str]:
    """Map (model, o2m_field) -> comodel name using comodel_name='...'."""
    mapping: Dict[Tuple[str, str], str] = {}
    for py in Path("records_management/models").rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        # Pattern: <field> = fields.One2many(comodel_name='model.name', inverse_name=...)
        for m in re.finditer(
            r"^(\s*)([a-zA-Z_][\w]*)\s*=\s*fields\.One2many\([^\)]*comodel_name\s*=\s*['\"]([\w\.]+)['\"]",
            text,
            re.M,
        ):
            field_name = m.group(2)
            comodel = m.group(3)
            # Find owning model via nearest preceding _name
            before = text[: m.start()]
            nearest = list(re.finditer(r"^\s*_name\s*=\s*['\"]([\w\.]+)['\"]", before, re.M))
            if not nearest:
                continue
            owner_model = nearest[-1].group(1)
            mapping[(owner_model, field_name)] = comodel
    return mapping


def validate_nested_lists(models: Dict[str, ModelInfo]):
    """Scan views and validate nested list fields against comodel fields."""
    issues: List[str] = []

    one2many_map = get_one2many_map(models)

    for xml_path in Path("records_management/views").rglob("*.xml"):
        try:
            text = xml_path.read_text(encoding="utf-8")
            root = ET.fromstring(text)
        except Exception as e:
            # Skip non-parseable files; other validators catch these
            continue

        for rec in root.findall(".//record[@model='ir.ui.view']"):
            model_el = rec.find(".//field[@name='model']")
            arch_el = rec.find(".//field[@name='arch']")
            if model_el is None or arch_el is None or len(arch_el) == 0:
                continue

            parent_model = (model_el.text or "").strip()
            if not parent_model:
                continue

            # Find any <field name="o2m_field" mode="list"> ... <list> ...
            for o2m_field in arch_el.findall(".//field[@mode='list']"):
                o2m_name = o2m_field.get("name")
                if not o2m_name:
                    continue

                comodel = one2many_map.get((parent_model, o2m_name))
                if not comodel:
                    # Could not resolve comodel; warn but continue
                    issues.append(
                        f"WARN {xml_path.name}: unable to resolve comodel for {parent_model}.{o2m_name}"
                    )
                    continue

                # Collect inner list fields
                inner_list = o2m_field.find(".//list")
                if inner_list is None:
                    continue
                wanted_fields = [fld.get("name") for fld in inner_list.findall("field") if fld.get("name")]

                # Resolve comodel fields
                comodel_info = models.get(comodel)
                comodel_fields = set(comodel_info.fields.keys()) if comodel_info else set()

                # Missing fields on comodel
                missing = [w for w in wanted_fields if w not in comodel_fields]
                if missing:
                    issues.append(
                        f"ERROR {xml_path.name}: {parent_model}.{o2m_name} -> {comodel} missing fields: {', '.join(missing)}"
                    )

    return issues


def main():
    models = parse_models()
    issues = validate_nested_lists(models)
    if issues:
        print("\nNested Sublist Field Validator Report")
        print("=" * 40)
        for line in issues:
            print(line)
        print(f"\nTotal issues: {sum(1 for i in issues if i.startswith('ERROR'))}")
        # Non-zero exit only on ERROR lines; WARN are advisory
        has_errors = any(i.startswith("ERROR") for i in issues)
        return 1 if has_errors else 0
    else:
        print("Nested Sublist Field Validator: No issues found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
