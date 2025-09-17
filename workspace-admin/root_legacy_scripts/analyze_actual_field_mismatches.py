#!/usr/bin/env python3
"""
Analyze ACTUAL field mismatches between models and views in Records Management.

Relocated from repository root to workspace-admin/root_legacy_scripts on 2025-09-17.
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

def analyze_xml_file(xml_path):
	try:
		tree = ET.parse(xml_path)
		root = tree.getroot()
		view_fields = set()
		action_configs = set()
		for record in root.findall('.//record'):
			model = record.get('model', '')
			if model == 'ir.ui.view':
				arch_field = record.find('.//field[@name="arch"]')
				if arch_field is not None:
					arch_content = ET.tostring(arch_field, encoding='unicode')
					field_matches = re.findall(r'<field\s+name="([^"]+)"', arch_content)
					view_fields.update(field_matches)
			elif model in ['ir.actions.act_window', 'ir.actions.server', 'ir.actions.client']:
				for field in record.findall('.//field'):
					field_name = field.get('name', '')
					if field_name:
						action_configs.add(field_name)
		return view_fields, action_configs
	except Exception as e:
		print(f"Error parsing {xml_path}: {e}")
		return set(), set()

def get_model_fields(model_path):
	try:
		with open(model_path, 'r', encoding='utf-8') as f:
			content = f.read()
		field_pattern = r'(\w+)\s*=\s*fields\.\w+'
		matches = re.findall(field_pattern, content)
		return set(matches)
	except Exception as e:
		print(f"Error reading {model_path}: {e}")
		return set()

def main():
	model_path = "records_management/models/shredding_service_bin.py"
	view_path = "records_management/views/shredding_service_bin_views.xml"
	if not os.path.exists(model_path):
		print(f"Model file not found: {model_path}")
		return
	if not os.path.exists(view_path):
		print(f"View file not found: {view_path}")
		return
	print("🔍 PROPER FIELD MISMATCH ANALYSIS")
	print("=" * 60)
	model_fields = get_model_fields(model_path)
	print(f"\n📝 Model Fields Found: {len(model_fields)}")
	print(f"Sample: {list(sorted(model_fields))[:5]}...")
	view_fields, action_configs = analyze_xml_file(view_path)
	print(f"\n👀 View Field References: {len(view_fields)}")
	print(f"Sample: {list(sorted(view_fields))[:5]}...")
	print(f"\n⚙️ Action Configurations: {len(action_configs)}")
	print(f"Sample: {list(sorted(action_configs))[:5]}...")
	missing_fields = view_fields - model_fields
	print(f"\n❌ ACTUAL Missing Fields: {len(missing_fields)}")
	if missing_fields:
		print("Fields referenced in views but not defined in model:")
		for field in sorted(missing_fields):
			print(f"  - {field}")
	else:
		print("✅ All view fields are properly defined in the model!")
	print(f"\n🚨 What Old Audit Tool Incorrectly Counted:")
	print(f"  - Action configs as missing fields: {len(action_configs)}")
	print(f"  - These are NOT model fields: {list(sorted(action_configs))[:10]}...")
	print(f"\n✅ CONCLUSION:")
	print(f"  - Real missing fields: {len(missing_fields)}")
	print(f"  - False positives from old tool: {len(action_configs)}")
	print(f"  - This explains the 'hundreds of missing fields' confusion!")

if __name__ == "__main__":
	main()
