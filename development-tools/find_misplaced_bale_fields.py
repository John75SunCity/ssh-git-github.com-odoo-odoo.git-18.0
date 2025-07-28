#!/usr/bin/env python3
"""
Find specific view files that reference the misplaced bale fields
"""

import os
import re

def search_views_for_fields():
    views_dir = "records_management/views"
    target_fields = ['bale_date', 'gross_weight', 'service_type', 'state']
    
    for filename in os.listdir(views_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(views_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if this view references records.container
            if 'records.container' in content:
                print(f"\n=== {filename} ===")
                print("Contains records.container model reference")
                
                # Check for the problematic fields
                for field in target_fields:
                    if f'name="{field}"' in content:
                        print(f"  ❌ References field: {field}")
                        
                        # Find the line numbers
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if f'name="{field}"' in line:
                                print(f"    Line {i}: {line.strip()}")

if __name__ == "__main__":
    search_views_for_fields()
