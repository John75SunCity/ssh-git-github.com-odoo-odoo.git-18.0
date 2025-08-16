#!/usr/bin/env python3
"""
Fix indentation issues caused by ensure_one() insertion
"""

import os
import re

def fix_indentation_issues():
    """Fix common indentation issues in the affected files"""

    files_with_issues = [
        'records_chain_of_custody.py',
        'records_deletion_request.py',
        'barcode_models.py',
        'shredding_hard_drive.py',
        'records_billing_line.py',
        'processing_log.py',
        'approval_history.py',
        'paper_bale_source_document.py',
        'records_tag.py',
        'file_retrieval_work_order_item.py',
        'records_billing_profile.py',
        'customer_inventory_report.py',
        'work_order_coordinator.py'
    ]

    base_path = "records_management/models"

    for filename in files_with_issues:
        filepath = os.path.join(base_path, filename)
        if not os.path.exists(filepath):
            print(f"⚠️ File {filename} not found, skipping...")
            continue

        print(f"🔧 Fixing {filename}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        fixed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for ensure_one() followed by incorrect indentation
            if 'self.ensure_one()' in line and i + 1 < len(lines):
                # Current line (ensure_one)
                fixed_lines.append(line)

                # Check next lines for indentation issues
                base_indent = len(line) - len(line.lstrip())
                expected_next_indent = base_indent

                # Look ahead to find proper indentation level
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]

                    if not next_line.strip():  # Empty line
                        fixed_lines.append(next_line)
                        j += 1
                        continue

                    # Check if this line has wrong indentation
                    current_indent = len(next_line) - len(next_line.lstrip())

                    # If line starts with extra indentation, fix it
                    if (current_indent > expected_next_indent and
                        not next_line.strip().startswith(('"""', "'''", '#'))):

                        # Remove extra indentation
                        correct_line = ' ' * expected_next_indent + next_line.lstrip()
                        fixed_lines.append(correct_line)
                    else:
                        fixed_lines.append(next_line)

                    j += 1

                    # Stop at next method or significant dedent
                    if (next_line.strip() and
                        current_indent <= base_indent and
                        (next_line.strip().startswith('def ') or
                         next_line.strip().startswith('class ') or
                         next_line.strip().startswith('@'))):
                        break

                i = j
                continue

            fixed_lines.append(line)
            i += 1

        fixed_content = '\n'.join(fixed_lines)

        # Additional cleanup patterns
        # Fix double ensure_one
        fixed_content = re.sub(r'(self\.ensure_one\(\)\s*\n\s*self\.ensure_one\(\))', 'self.ensure_one()', fixed_content)

        # Fix ensure_one in wrong place (after other code)
        fixed_content = re.sub(r'(\n\s+)([^#\n]+\n\s+)(self\.ensure_one\(\))', r'\1self.ensure_one()\n\1\2', fixed_content)

        if fixed_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  ✅ Fixed indentation in {filename}")
        else:
            print(f"  ℹ️ No changes needed for {filename}")

if __name__ == "__main__":
    print("🔧 FIXING INDENTATION ISSUES")
    print("=" * 40)
    fix_indentation_issues()
    print("=" * 40)
    print("✅ Indentation fix complete")
