#!/usr/bin/env python3
"""Analyze models that declare BOTH _name and _inherit.

Goal: Support consolidation toward extending core models instead of cloning
when duplication provides little additional logic. Produces a concise report:

For each dual-definition class:
  - file
  - class name
  - _name value
  - _inherit value(s)
  - added field count (simple heuristic)
  - added method count (heuristic: def declarations minus super-only wrappers)
  - flags (has_state_field, has_sequence_usage, mixin_only)
  - recommendation (keep_new / convert_to_extension / review)

Heuristics:
  - If inherit list contains ONLY framework mixins (mail.thread, mail.activity.mixin, rating.mixin, portal.mixin, sequence.mixin, image.mixin): treat as standalone new model => keep_new
  - Else if new fields <=3 and no state / sequence / business methods: convert_to_extension
  - If many new fields (>15) or state field present: keep_new (likely separate entity)
  - Else: review

No side effects—read-only analysis.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

MODULE_ROOT = Path(__file__).parent.parent / "records_management" / "models"

# Known mixin models that do NOT constitute a functional parent
KNOWN_MIXINS: Set[str] = {
    'mail.thread',
    'mail.activity.mixin',
    'rating.mixin',
    'portal.mixin',
    'sequence.mixin',
    'image.mixin',
}


@dataclass
class DualModelInfo:
    file: Path
    class_name: str
    model_name: str
    inherit_raw: str
    field_count: int
    method_count: int
    has_state: bool
    uses_sequence: bool
    mixin_only: bool
    recommendation: str


def extract_info(py_file: Path) -> List[DualModelInfo]:
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    infos: List[DualModelInfo] = []
    for node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        # Quick check for models.Model base
        if not any(
            isinstance(b, ast.Attribute) and getattr(b.value, "id", None) == "models" and b.attr == "Model"
            for b in node.bases
        ):
            continue

        model_name = None
        inherit_vals: List[str] = []
        field_count = 0
        method_count = 0
        has_state = False
        uses_sequence = False

        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                tgt = stmt.targets[0].id
                if tgt == "_name":
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        model_name = stmt.value.value
                elif tgt == "_inherit":
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        inherit_vals = [stmt.value.value]
                    elif isinstance(stmt.value, (ast.Tuple, ast.List)):
                        tmp = []
                        for elt in stmt.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                tmp.append(elt.value)
                        inherit_vals = tmp
                else:
                    # Field heuristic: call to fields.*
                    if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute):
                        if isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == "fields":
                            field_count += 1
                            if tgt == "state":
                                has_state = True
                            # Sequence usage heuristic (default next_by_code)
                            for kw in stmt.value.keywords:
                                if kw.arg == "default" and isinstance(kw.value, ast.Call):
                                    if isinstance(kw.value.func, ast.Attribute) and kw.value.func.attr.startswith("next_by_code"):
                                        uses_sequence = True
            elif isinstance(stmt, ast.FunctionDef):
                body = stmt.body
                meaningful = [n for n in body if not (isinstance(n, ast.Pass) or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)))]
                if len(meaningful) == 1 and isinstance(meaningful[0], ast.Return):
                    ret = meaningful[0].value
                    if isinstance(ret, ast.Call) and isinstance(ret.func, ast.Attribute) and ret.func.attr == "super":
                        continue
                method_count += 1

        if model_name and inherit_vals:
            mixin_only = all(val in KNOWN_MIXINS for val in inherit_vals)
            # Recommendation logic
            if mixin_only:
                rec = "keep_new"
            elif field_count <= 3 and not has_state and method_count <= 1:
                rec = "convert_to_extension"
            elif field_count > 15 or has_state:
                rec = "keep_new"
            else:
                rec = "review"

            infos.append(
                DualModelInfo(
                    file=py_file,
                    class_name=node.name,
                    model_name=model_name,
                    inherit_raw=",".join(inherit_vals),
                    field_count=field_count,
                    method_count=method_count,
                    has_state=has_state,
                    uses_sequence=uses_sequence,
                    mixin_only=mixin_only,
                    recommendation=rec,
                )
            )
    return infos


def main() -> int:
    if not MODULE_ROOT.exists():
        print("Module models directory not found")
        return 1

    all_infos: List[DualModelInfo] = []
    for py_file in MODULE_ROOT.glob("*.py"):
        all_infos.extend(extract_info(py_file))

    if not all_infos:
        print("No dual _name + _inherit patterns detected.")
        return 0

    # Summarize
    print("Detected models declaring BOTH _name and _inherit (potential clones or new entities):")
    print("-" * 130)
    header = f"{'Model':40} {'Inherit':35} Flds Meth State Seq MixOnly Recommendation File"
    print(header)
    print("-" * len(header))
    for info in sorted(all_infos, key=lambda x: (x.recommendation, x.model_name)):
        print(
            f"{info.model_name:40} {info.inherit_raw[:35]:35} {info.field_count:4} {info.method_count:4}  "
            f"{'Y' if info.has_state else 'N':5} {'Y' if info.uses_sequence else 'N':3} {'Y' if info.mixin_only else 'N':7} {info.recommendation:18} {info.file.name}"
        )

    counts: dict[str, int] = {}
    for i in all_infos:
        counts[i.recommendation] = counts.get(i.recommendation, 0) + 1
    print("\nSummary:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    print("\nLegend: Flds=added field count; Meth=added methods; State=has state field; Seq=sequence default; MixOnly=inherit list only mixins")
    print("convert_to_extension => drop _name only if real functional parent present (NOT just mixins)")
    print("keep_new => standalone entity or mixin-only new model")
    print("review => borderline: manual assessment needed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
