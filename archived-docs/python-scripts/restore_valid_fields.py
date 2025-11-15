#!/usr/bin/env python3
"""
Restore weight, storage_start_date, and last_access_date fields that were incorrectly removed.
These fields DO exist in the records.container model.
"""

import re
import random
from datetime import datetime, timedelta

# Read the demo file
with open('records_management/demo/customer_inventory_demo.xml', 'r') as f:
    content = f.read()

def add_restored_fields(match):
    """Add weight, storage_start_date, and last_access_date to container"""
    container_block = match.group(0)
    
    # Check if fields already exist
    if 'name="weight"' in container_block:
        return container_block
    
    # Find the content_date_to line (insert after it)
    date_match = re.search(r'(<field name="content_date_to">.*?</field>)', container_block)
    if not date_match:
        return container_block
    
    date_line = date_match.group(1)
    
    # Extract dates for reference
    date_from_match = re.search(r'<field name="content_date_from">(.*?)</field>', container_block)
    date_to_match = re.search(r'<field name="content_date_to">(.*?)</field>', container_block)
    
    if date_from_match and date_to_match:
        date_from_str = date_from_match.group(1)
        date_to_str = date_to_match.group(1)
        
        # Storage start = 30-60 days before content_date_from
        content_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        storage_start = content_from - timedelta(days=random.randint(30, 60))
        
        # Last access = somewhere between storage start and now
        # For older containers, access might be years ago
        days_since_storage = (datetime.now() - storage_start).days
        last_access = storage_start + timedelta(days=random.randint(0, min(days_since_storage, 365*2)))
        
        # Random weight between 15-50 lbs
        weight = round(random.uniform(15.0, 50.0), 1)
        
        # Create new fields
        new_fields = f'''{date_line}
            <field name="weight">{weight}</field>
            <field name="storage_start_date">{storage_start.strftime('%Y-%m-%d')}</field>
            <field name="last_access_date">{last_access.strftime('%Y-%m-%d')}</field>'''
        
        # Replace the date_to line with date_to + new fields
        updated_block = container_block.replace(date_line, new_fields)
        
        return updated_block
    
    return container_block

# Find all container records and add fields
pattern = r'<record id="container_\d+" model="records\.container">.*?</record>'
updated_content = re.sub(pattern, add_restored_fields, content, flags=re.DOTALL)

# Write back
with open('records_management/demo/customer_inventory_demo.xml', 'w') as f:
    f.write(updated_content)

print("✅ Restored weight, storage_start_date, and last_access_date to all containers")
print("   - weight: Random values 15-50 lbs")
print("   - storage_start_date: 30-60 days before content_date_from")
print("   - last_access_date: Random date after storage start")
