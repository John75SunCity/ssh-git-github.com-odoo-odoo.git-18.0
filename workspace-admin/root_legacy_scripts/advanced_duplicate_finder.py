#!/usr/bin/env python3
"""
Advanced script to find duplicate access rules that cause PostgreSQL constraint violations
Relocated from repository root to workspace-admin/root_legacy_scripts on 2025-09-17.
"""

import csv
from collections import defaultdict, Counter

def find_security_duplicates():
	file_path = "records_management/security/ir.model.access.csv"
    
	print("🔍 Analyzing ir.model.access.csv for PostgreSQL constraint violations...")
    
	with open(file_path, 'r', encoding='utf-8') as file:
		reader = csv.DictReader(file)
		rows = list(reader)
    
	print(f"📊 Total access rules: {len(rows)}")
    
	# Check for duplicate IDs (PRIMARY KEY constraint)
	ids = [row['id'] for row in rows]
	id_counts = Counter(ids)
	duplicates_by_id = {k: v for k, v in id_counts.items() if v > 1}
    
	# Check for duplicate names (UNIQUE constraint on name)
	names = [row['name'] for row in rows]
	name_counts = Counter(names)
	duplicates_by_name = {k: v for k, v in name_counts.items() if v > 1}
    
	# Check for complete duplicates (module, name combination)
	module_name_pairs = []
	for row in rows:
		module = 'records_management'
		name = row['id']  # The 'id' field becomes 'name' in ir_model_data
		module_name_pairs.append((module, name))
    
	module_name_counts = Counter(module_name_pairs)
	duplicates_by_module_name = {k: v for k, v in module_name_counts.items() if v > 1}
    
	# Display results
	total_issues = 0
    
	if duplicates_by_id:
		print(f"\n❌ DUPLICATE IDs found ({len(duplicates_by_id)}):")
		for rule_id, count in sorted(duplicates_by_id.items()):
			print(f"  - {rule_id}: appears {count} times")
			total_issues += count - 1
    
	if duplicates_by_name:
		print(f"\n⚠️  DUPLICATE names found ({len(duplicates_by_name)}):")
		for name, count in sorted(duplicates_by_name.items()):
			print(f"  - {name}: appears {count} times")
			total_issues += count - 1
    
	if duplicates_by_module_name:
		print(f"\n🔥 CRITICAL: DUPLICATE (module, name) pairs found ({len(duplicates_by_module_name)}):")
		for (module, name), count in sorted(duplicates_by_module_name.items()):
			print(f"  - ({module}, {name}): appears {count} times")
			total_issues += count - 1
    
	# Look for potentially problematic entries
	print(f"\n🔍 Scanning for specific PostgreSQL constraint patterns...")
    
	ir_model_data_entries = []
	for row in rows:
		entry = {
			'module': 'records_management',
			'name': row['id'],
			'model': 'ir.model.access',
		}
		ir_model_data_entries.append((entry['module'], entry['name']))
    
	ir_data_counts = Counter(ir_model_data_entries)
	ir_data_duplicates = {k: v for k, v in ir_data_counts.items() if v > 1}
    
	if ir_data_duplicates:
		print(f"\n💥 IR_MODEL_DATA CONSTRAINT VIOLATIONS found ({len(ir_data_duplicates)}):")
		for (module, name), count in sorted(ir_data_duplicates.items()):
			print(f"  - module='{module}', name='{name}': {count} occurrences")
			print(f"    This will cause: UNIQUE constraint (module, name) violation")
    
	if total_issues == 0 and not ir_data_duplicates:
		print("✅ No obvious duplicates found in CSV structure!")
		print("\n🤔 The PostgreSQL error suggests a different issue...")
		print("   Checking for trailing entries or encoding issues...")
        
		for i, row in enumerate(rows[-10:], len(rows)-9):
			if any(not value.strip() for value in row.values()):
				print(f"   Line {i}: Contains empty values: {row}")
    
	return {
		'duplicates_by_id': duplicates_by_id,
		'duplicates_by_name': duplicates_by_name, 
		'ir_data_duplicates': ir_data_duplicates,
		'total_rows': len(rows)
	}

if __name__ == "__main__":
	result = find_security_duplicates()
	if result['ir_data_duplicates']:
		print(f"\n🚨 SOLUTION NEEDED: Remove {len(result['ir_data_duplicates'])} duplicate entries")
		print("   Run deduplication script to fix PostgreSQL constraint violation")
