"""Advanced Missing View Fields Detector

Purpose:
	Scan the `records_management` addon for XML view field references and
	compare them with model field declarations, reporting:
		1. Fields referenced in views but absent in model definitions.
		2. Special case: `<field name="name"/>` when the target model lacks
		   a real `name` field (even if `_rec_name` points elsewhere) so that
		   form title placeholders don't break during load (ParseError).

Usage:
	python3 development-tools/advanced_missing_view_fields_detector.py

Output:
	Prints a summary and writes a JSON report `missing_view_fields_enhanced.json`.

Notes:
	- Ignores inherited fields by collecting fields from `_inherit` chains only
	  when explicitly re-declared here (keeps audit actionable & minimal).
	- Treats transient/wizard models the same way; if a view references `name`
	  we still ensure a Char field exists.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Dict, Set, List

ADDON = Path(__file__).resolve().parent.parent / 'records_management'
XML_DIRS = ['views', 'templates', 'report']
REPORT_PATH = Path(__file__).resolve().parent / 'missing_view_fields_enhanced.json'

MODEL_FIELD_REGEX = re.compile(r"^\s*(?P<fname>[a-zA-Z0-9_]+)\s*=\s*fields\.")
MODEL_NAME_REGEX = re.compile(r"_name\s*=\s*['\"]([a-z0-9_.]+)['\"]")
MODEL_INHERIT_REGEX = re.compile(r"_inherit\s*=\s*['\"]([a-z0-9_.]+)['\"]")

FIELD_TAG_REGEX = re.compile(r"<field[^>]*name=['\"]([a-zA-Z0-9_\.]+)['\"]")
TREE_FORM_REGEX = re.compile(r"<form|<tree|<kanban|<search")


def extract_models() -> Dict[str, Set[str]]:
	models: Dict[str, Set[str]] = {}
	for py_file in (ADDON / 'models').glob('*.py'):
		text = py_file.read_text(encoding='utf-8', errors='ignore')
		# quick skip for empty / placeholder files
		if '_name' not in text:
			continue
		# naive multi-model support (rare, but present in repo)
		current_model: str | None = None
		fields_for_model: Set[str] = set()
		for line in text.splitlines():
			name_match = MODEL_NAME_REGEX.search(line)
			if name_match:
				if current_model and fields_for_model:
					models.setdefault(current_model, set()).update(fields_for_model)
				current_model = name_match.group(1)
				fields_for_model = set()
				continue
			# collect field assignments
			fmatch = MODEL_FIELD_REGEX.match(line)
			if fmatch and current_model:
				fields_for_model.add(fmatch.group('fname'))
		if current_model and fields_for_model:
			models.setdefault(current_model, set()).update(fields_for_model)
	return models


def extract_view_field_usage() -> Dict[str, Set[str]]:
	usage: Dict[str, Set[str]] = {}
	for directory in XML_DIRS:
		view_dir = ADDON / directory
		if not view_dir.exists():
			continue
		for xml_file in view_dir.rglob('*.xml'):
			text = xml_file.read_text(encoding='utf-8', errors='ignore')
			if not TREE_FORM_REGEX.search(text):
				continue
			# Try to infer model context: look for model= attribute first
			# Keep simple: accumulate fields for any model mentioned in file
			model_ids = set(re.findall(r"model=['\"]([a-z0-9_.]+)['\"]", text))
			if not model_ids:
				continue
			field_refs = FIELD_TAG_REGEX.findall(text)
			if not field_refs:
				continue
			for m in model_ids:
				bucket = usage.setdefault(m, set())
				# only collect simple field names (ignore dotted paths partner_id.name)
				for ref in field_refs:
					if '.' in ref:
						continue
					bucket.add(ref)
	return usage


def main():
	models = extract_models()
	usage = extract_view_field_usage()
	missing = {}
	special_name_issues = {}

	for model, fields_used in usage.items():
		declared = models.get(model, set())
		for field in sorted(fields_used):
			if field not in declared:
				missing.setdefault(model, set()).add(field)
		# Special rule: if 'name' used in view but not declared, flag separately
		if 'name' in fields_used and 'name' not in declared:
			special_name_issues[model] = True

	# Convert sets to sorted lists
	missing_serializable = {m: sorted(v) for m, v in sorted(missing.items())}

	report = {
		'models_with_missing_fields': len(missing_serializable),
		'total_missing_field_refs': sum(len(v) for v in missing_serializable.values()),
		'special_name_issues': sorted(special_name_issues.keys()),
		'missing_fields': missing_serializable,
	}
	REPORT_PATH.write_text(json.dumps(report, indent=2), encoding='utf-8')
	print("=== Missing View Field Audit (Enhanced) ===")
	print(f"Models with missing fields: {report['models_with_missing_fields']}")
	print(f"Total missing field refs: {report['total_missing_field_refs']}")
	if report['special_name_issues']:
		print("\nModels missing explicit 'name' field but used in views:")
		for m in report['special_name_issues']:
			print(f"  - {m}")
	print("\nSample (first 10 models):")
	for idx, (m, fields) in enumerate(report['missing_fields'].items()):
		if idx >= 10:
			break
		more = '...' if fields[8:] else ''
		print(f"  {m}: {', '.join(fields[:8])}{more}")
	print(f"\nReport written to {REPORT_PATH}")


if __name__ == '__main__':
	main()
