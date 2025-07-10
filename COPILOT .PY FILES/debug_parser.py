#!/usr/bin/env python3
"""
Debug Invoice Parser - Let's see what's in the data
"""

import re

def debug_parser():
    """Debug the parser to see what's happening"""
    input_file = '/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/rawText.txt'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    lines = text_content.strip().split('\n')
    
    print(f"Total lines: {len(lines)}")
    print("\n=== First 20 lines ===")
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:3d}: '{line.strip()}'")
    
    # Look for invoice numbers
    invoice_count = 0
    wo_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for invoice number patterns
        if re.match(r'^(\d{7})', line):
            invoice_count += 1
            if invoice_count <= 5:
                print(f"\nFound invoice: '{line}' at line {i+1}")
        
        # Check for WO patterns
        if 'WO #' in line:
            wo_count += 1
            if wo_count <= 5:
                print(f"\nFound WO line: '{line}' at line {i+1}")
                # Try our regex
                wo_pattern = r'WO #(\d+)\s+([^-]+)\s*-\s*([^,]+?)(?:,|\s+)(\d+\.\d{4})\s+(\d+\.\d{2})\s+(\d+\.\d{2})'
                match = re.search(wo_pattern, line)
                if match:
                    print(f"  ✓ Regex matched: {match.groups()}")
                else:
                    print(f"  ✗ Regex didn't match")
    
    print(f"\n=== Summary ===")
    print(f"Total invoice lines found: {invoice_count}")
    print(f"Total WO lines found: {wo_count}")

if __name__ == "__main__":
    debug_parser()
