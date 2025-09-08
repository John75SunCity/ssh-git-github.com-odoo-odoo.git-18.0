#!/usr/bin/env python3
"""Generate dependency-aware models/__init__.py import ordering.

Scans records_management/models/*.py extracting:
  - _name = 'model.name'
  - _inherit = 'model.name' or list/tuple including names
Builds a directed graph: base model file -> inheriting file(s).
Emits import lines ensuring each file defining a model is imported
before any file that inherits/extends it (topological order) while
preserving deterministic alphabetical fallback for unrelated groups.

Usage:
  python3 development-tools/generate_models_init.py --write   # overwrite models/__init__.py
  python3 development-tools/generate_models_init.py --print   # print proposed content

This does NOT modify files outside models/. Non-Python artifacts ignored.
Safeguards:
  - Ignores files that already imported (dedupe)
  - Falls back to simple alpha order if cycle detected, logging a warning
  - Keeps explicitly pinned priority list (CRITICAL_FIRST) at the top

Extend CRITICAL_FIRST if you discover additional early-load bases.
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

MODULE_ROOT = Path(__file__).resolve().parent.parent / 'records_management'
MODELS_DIR = MODULE_ROOT / 'models'
INIT_FILE = MODELS_DIR / '__init__.py'

MODEL_NAME_RE = re.compile(r"^\s*_name\s*=\s*['\"]([a-zA-Z0-9_.]+)['\"]", re.MULTILINE)
INHERIT_SINGLE_RE = re.compile(r"^\s*_inherit\s*=\s*['\"]([a-zA-Z0-9_.]+)['\"]", re.MULTILINE)
INHERIT_COLLECTION_RE = re.compile(r"^\s*_inherit\s*=\s*([\[]|\()[^\n]+", re.MULTILINE)
STRING_LITERAL_RE = re.compile(r"['\"]([a-zA-Z0-9_.]+)['\"]")

# Generic model reference patterns (Python + XML) – conservative to avoid noise
PY_MODEL_REF_RE = re.compile(r"['\"]([a-zA-Z0-9_.]+)['\"]")
XML_MODEL_REF_RE = re.compile(r"model=[\"']([a-zA-Z0-9_.]+)[\"']")

# Files that must appear early regardless of graph (base definitions with many extensions)
CRITICAL_FIRST = [
    'records_billing_config.py',  # prevents missing model inheritance
]

EXCLUDE_FILES = {"__init__.py", "__pycache__"}


def discover_files():
    for f in MODELS_DIR.glob('*.py'):
        if f.name in EXCLUDE_FILES:
            continue
        yield f


def parse_model_metadata(path: Path) -> Tuple[List[str], List[str]]:
    text = path.read_text(encoding='utf-8', errors='ignore')
    names = MODEL_NAME_RE.findall(text)
    inherits: List[str] = []
    single = INHERIT_SINGLE_RE.findall(text)
    if single:
        inherits.extend(single)
    else:
        coll = INHERIT_COLLECTION_RE.findall(text)
        if coll:
            inherits.extend(STRING_LITERAL_RE.findall(coll[0]))
    return names, inherits


def scan_first_external_references(model_to_file: Dict[str, str]) -> Dict[str, int]:
    """Return mapping of target file name -> earliest external reference line number.

    We scan:
      - Other Python model files
      - XML files under records_management/views + data + report + templates

    Heuristic: If a model name appears in a different file BEFORE its own file defines it,
    we record the earliest occurrence line number as a priority hint. Lower line numbers
    mean earlier import preference (so definitions precede references).
    """
    search_roots = [
        MODULE_ROOT / 'models',
        MODULE_ROOT / 'views',
        MODULE_ROOT / 'data',
        MODULE_ROOT / 'report',
        MODULE_ROOT / 'templates',
    ]
    file_priority: Dict[str, int] = {}
    # Pre-build reverse index: file -> set(models it defines)
    for model, fname in model_to_file.items():
        file_priority.setdefault(fname, sys.maxsize)

    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if not path.is_file():
                continue
            # Only scan limited extensions
            if path.suffix not in {'.py', '.xml'}:
                continue
            try:
                text = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            lines = text.splitlines()
            for idx, line in enumerate(lines, start=1):
                # Quick skip if no dot pattern
                if '.' not in line:
                    continue
                # Gather candidate model tokens
                candidates: Set[str] = set()
                if path.suffix == '.py':
                    for m in PY_MODEL_REF_RE.findall(line):
                        candidates.add(m)
                else:
                    for m in XML_MODEL_REF_RE.findall(line):
                        candidates.add(m)
                for token in candidates:
                    target_file = model_to_file.get(token)
                    if not target_file:
                        continue
                    # Ignore references inside same defining file
                    if path.name == target_file:
                        continue
                    # Update earliest reference
                    if idx < file_priority[target_file]:
                        file_priority[target_file] = idx
    # Normalize maxsize -> large number meaning no external references
    for f, val in list(file_priority.items()):
        if val == sys.maxsize:
            file_priority[f] = 10_000_000  # sentinel large
    return file_priority


def build_graph():
    file_by_model: Dict[str, str] = {}
    inherits_by_file: Dict[str, List[str]] = {}

    for f in discover_files():
        model_names, inherit_models = parse_model_metadata(f)
        for mn in model_names:
            file_by_model[mn] = f.name
        inherits_by_file[f.name] = inherit_models

    graph: Dict[str, Set[str]] = defaultdict(set)
    indegree: Dict[str, int] = defaultdict(int)

    for f in inherits_by_file:
        indegree[f] = 0

    for file_name, inherit_models in inherits_by_file.items():
        for parent_model in inherit_models:
            parent_file = file_by_model.get(parent_model)
            if parent_file and parent_file != file_name:
                if file_name not in graph[parent_file]:
                    graph[parent_file].add(file_name)
                    indegree[file_name] += 1

    # External reference heuristic priorities
    first_ref_priority = scan_first_external_references(file_by_model)
    return graph, indegree, set(inherits_by_file.keys()), first_ref_priority


def topo_sort():
    graph, indegree, all_files, first_ref_priority = build_graph()

    # Priority queue emulation using list + sort each pop (N small enough).
    ready: List[str] = []
    for f in all_files:
        if indegree[f] == 0:
            ready.append(f)

    def sort_ready():
        # Lower first_ref_priority first; tie-break alphabetical
        ready.sort(key=lambda x: (first_ref_priority.get(x, 10_000_000), x))

    sort_ready()
    ordered: List[str] = []

    while ready:
        cur = ready.pop(0)
        ordered.append(cur)
        for nxt in graph.get(cur, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
        sort_ready()

    if len(ordered) != len(all_files):
        cycle_files = all_files - set(ordered)
        sys.stderr.write(
            f"[WARN] Cycle detected among: {', '.join(sorted(cycle_files))} — appending in alpha order\n"
        )
        ordered.extend(sorted(cycle_files))

    # Move critical-first files to front preserving their relative order
    critical = [f for f in CRITICAL_FIRST if f in ordered]
    remaining = [f for f in ordered if f not in critical]
    # De-dup safety
    seen: Set[str] = set()
    final: List[str] = []
    for f in critical + remaining:
        if f not in seen:
            seen.add(f)
            final.append(f)
    return final


def generate_init_lines():
    ordered_files = topo_sort()
    lines = [
        "# Auto-generated by development-tools/generate_models_init.py",
        "# Ordering logic:",
        "#  1. Critical base files (CRITICAL_FIRST).",
        "#  2. Topological order of inheritance graph (_inherit dependencies).",
        "#  3. Tie-break / prioritization by earliest external reference (Python/XML).",
        "#  4. Deterministic alphabetical fallback.",
        "# Do NOT hand-edit ordering; rerun the generator if needed.",
        "",
    ]
    for fname in ordered_files:
        module_name = fname[:-3]  # strip .py
        lines.append(f"from . import {module_name}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true', help='Overwrite models/__init__.py')
    parser.add_argument('--print', action='store_true', help='Print proposed content')
    args = parser.parse_args()

    content = generate_init_lines()
    if args.print or not args.write:
        print(content)
    if args.write:
        INIT_FILE.write_text(content, encoding='utf-8')
        print(f"[OK] Wrote dependency-aware init to {INIT_FILE}")

if __name__ == '__main__':
    main()
