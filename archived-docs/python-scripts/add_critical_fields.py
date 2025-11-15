#!/usr/bin/env python3
"""
Add critical missing fields to customer_inventory_demo.xml containers:
- location_id (stock location tracking)
- content_date_from (earliest content date)
- content_date_to (latest content date)
"""

import re
from datetime import datetime, timedelta
import random

# Read the demo file
with open('records_management/demo/customer_inventory_demo.xml', 'r') as f:
    content = f.read()

# Location references to distribute containers across
locations = [
    'location_main_warehouse_a',
    'location_main_warehouse_b',
    'location_secure_vault'
]

# Date ranges for realistic content dates (varied by year)
date_ranges = [
    ('2018-01-01', '2018-12-31'),  # Old records (eligible for destruction)
    ('2019-01-01', '2019-12-31'),
    ('2020-01-01', '2020-12-31'),
    ('2021-01-01', '2021-12-31'),
    ('2022-01-01', '2022-12-31'),
    ('2023-01-01', '2023-12-31'),
    ('2024-01-01', '2024-12-31'),  # Recent records
    ('2023-01-01', '2023-03-31'),  # Q1
    ('2023-04-01', '2023-06-30'),  # Q2
    ('2023-07-01', '2023-09-30'),  # Q3
    ('2023-10-01', '2023-12-31'),  # Q4
]

def add_fields_to_container(match):
    """Add location_id and content dates to a container record"""
    container_block = match.group(0)

    # Check if fields already exist
    if 'name="location_id"' in container_block:
        return container_block

    # Find the state field line (insert after it)
    state_match = re.search(r'(<field name="state">.*?</field>)', container_block)
    if not state_match:
        return container_block

    state_line = state_match.group(1)

    # Choose random location and date range
    location = random.choice(locations)
    date_from, date_to = random.choice(date_ranges)

    # Create new fields
    new_fields = f'''{state_line}
            <field name="location_id" ref="{location}"/>
            <field name="content_date_from">{date_from}</field>
            <field name="content_date_to">{date_to}</field>'''

    # Replace the state line with state + new fields
    updated_block = container_block.replace(state_line, new_fields)

    return updated_block

# Find all container records and add fields
pattern = r'<record id="container_\d+" model="records\.container">.*?</record>'
updated_content = re.sub(pattern, add_fields_to_container, content, flags=re.DOTALL)

# Write back
with open('records_management/demo/customer_inventory_demo.xml', 'w') as f:
    f.write(updated_content)

print("✅ Added location_id, content_date_from, and content_date_to to all containers")
print(f"   - Locations: {', '.join(locations)}")
print(f"   - Date ranges: {len(date_ranges)} different ranges")
