#!/usr/bin/env python3
"""
Script to find duplicate access rules in ir.model.access.csv
"""

import csv
from collections import defaultdict

def find_duplicates():
    file_path = "records_management/security/ir.model.access.csv"
    
    # Track duplicates by different criteria
    id_counts = defaultdict(int)
    name_counts = defaultdict(int)
    combined_counts = defaultdict(int)
    
    duplicates = {
        'ids': [],
        'names': [], 
        'combined': []
    }
    
    print("🔍 Analyzing security access rules for duplicates...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        for row in reader:
            # Count by ID
            rule_id = row['id']
            id_counts[rule_id] += 1
            
            # Count by name  
            name = row['name']
            name_counts[name] += 1
            
            # Count by combined key (id + model + group)
            combined_key = (rule_id, row['model_id'], row['group_id:id'])
            combined_counts[combined_key] += 1
    
    # Find duplicates
    for rule_id, count in id_counts.items():
        if count > 1:
            duplicates['ids'].append((rule_id, count))
    
    for name, count in name_counts.items():
        if count > 1:
            duplicates['names'].append((name, count))
            
    for combined_key, count in combined_counts.items():
        if count > 1:
            duplicates['combined'].append((combined_key, count))
    
    # Report findings
    print(f"\n📊 Analysis Results:")
    print(f"Total access rules: {len(rows)}")
    print(f"Unique IDs: {len(id_counts)}")
    print(f"Unique names: {len(name_counts)}")
    
    if duplicates['ids']:
        print(f"\n❌ DUPLICATE IDs found ({len(duplicates['ids'])}):")
        for rule_id, count in sorted(duplicates['ids']):
            print(f"  - {rule_id}: {count} occurrences")
    
    if duplicates['names']:
        print(f"\n⚠️  DUPLICATE names found ({len(duplicates['names'])}):")
        for name, count in sorted(duplicates['names']):
            print(f"  - {name}: {count} occurrences")
    
    if duplicates['combined']:
        print(f"\n🔥 CRITICAL: COMPLETE DUPLICATES found ({len(duplicates['combined'])}):")
        for combined_key, count in sorted(duplicates['combined']):
            rule_id, model_id, group_id = combined_key
            print(f"  - {rule_id} ({model_id}, {group_id}): {count} occurrences")
    
    if not any(duplicates.values()):
        print("✅ No duplicates found!")
    
    return duplicates

if __name__ == "__main__":
    find_duplicates()
