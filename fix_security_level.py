#!/usr/bin/env python3
"""Fix security_level values in demo data from numeric to Selection values."""

import re
import sys

file_path = 'records_management/demo/customer_inventory_demo.xml'

try:
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count occurrences before replacement
    count_1 = len(re.findall(r'<field name="security_level">1</field>', content))
    count_2 = len(re.findall(r'<field name="security_level">2</field>', content))
    count_3 = len(re.findall(r'<field name="security_level">3</field>', content))

    print(f"Found {count_1 + count_2 + count_3} numeric security_level values:")
    print(f"  - {count_1} instances of '1' (will convert to 'internal')")
    print(f"  - {count_2} instances of '2' (will convert to 'confidential')")
    print(f"  - {count_3} instances of '3' (will convert to 'restricted')")

    # Replace numeric security_level values with valid Selection values
    # Mapping based on stock_location.py Selection field definition:
    # - public, internal, confidential, restricted
    content = re.sub(
        r'<field name="security_level">1</field>',
        '<field name="security_level">internal</field>',
        content
    )

    content = re.sub(
        r'<field name="security_level">2</field>',
        '<field name="security_level">confidential</field>',
        content
    )

    content = re.sub(
        r'<field name="security_level">3</field>',
        '<field name="security_level">restricted</field>',
        content
    )

    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ Successfully fixed security_level values in {file_path}")
    print("   - Replaced '1' with 'internal'")
    print("   - Replaced '2' with 'confidential'")
    print("   - Replaced '3' with 'restricted'")
    
except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
