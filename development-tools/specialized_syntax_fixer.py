#!/usr/bin/env python3
"""
Specialized Syntax Error Fixer
Fixes the specific syntax patterns causing the remaining 18 syntax errors
"""

import os
import re
from pathlib import Path


def fix_field_definition_patterns(content):
    """Fix the specific malformed field definition patterns"""
    fixes_applied = 0
    original_content = content

    # Pattern 1: Fix hanging help parameters after field definitions
    # Look for cases like: field_name,) \n        help="text"
    lines = content.split("\n")
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for field definitions ending with ",)" 
        if re.match(r'\s+[^=]+=\s*fields\.[^(]+\([^)]*,\)\s*$', line):
            fixed_lines.append(line.rstrip(",)") + ",")
            
            # Look ahead for orphaned help parameter
            if (i + 1 < len(lines) and 
                re.match(r'\s+help="[^"]*"', lines[i + 1])):
                
                # Get the base indentation from the field line
                base_indent = len(line) - len(line.lstrip())
                help_line = lines[i + 1].strip()
                fixed_lines.append(" " * base_indent + f"    {help_line}")
                
                # Add closing parenthesis
                if not help_line.endswith(","):
                    fixed_lines[-1] += ","
                fixed_lines.append(" " * base_indent + ")")
                
                # Skip the orphaned help line and any closing parenthesis
                i += 1
                if (i + 1 < len(lines) and 
                    lines[i + 1].strip() in [")", "),", "),"]):
                    i += 1
                
                fixes_applied += 1
            else:
                # No orphaned help, just fix the closing
                fixed_lines.append(" " * (len(line) - len(line.lstrip())) + ")")
                
        # Check for hanging help parameters with wrong indentation
        elif re.match(r'\s{8,}help="[^"]*"', line):
            # This might be an orphaned help - check if previous line needs fixing
            if (len(fixed_lines) > 0 and 
                not fixed_lines[-1].strip().endswith(")")):
                # Get proper indentation from previous context
                prev_indent = 0
                for prev_line in reversed(fixed_lines[-3:]):
                    if "fields." in prev_line:
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                        break
                
                if prev_indent > 0:
                    help_content = re.search(r'help="([^"]*)"', line)
                    if help_content:
                        fixed_line = " " * prev_indent + f'    help="{help_content.group(1)}"'
                        if not line.strip().endswith(","):
                            fixed_line += ","
                        fixed_lines.append(fixed_line)
                        fixes_applied += 1
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        
        i += 1

    if fixes_applied > 0:
        content = "\n".join(fixed_lines)

    # Pattern 2: Fix specific currency_field syntax errors
    pattern = r'(\s+currency_field="[^"]*",)\)\s*\n\s+help="([^"]*)",?\s*\n\s+\),'
    def fix_currency_field(match):
        base_indent = len(match.group(1)) - len(match.group(1).lstrip())
        return (match.group(1) + "\n" + 
                " " * base_indent + f'    help="{match.group(2)}",\n' +
                " " * base_indent + ")")
    
    new_content = re.sub(pattern, fix_currency_field, content, flags=re.MULTILINE)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    # Pattern 3: Fix double closing parentheses
    content = re.sub(r'(\s+)\)\s*\n\s+\)\s*,?\s*$', r'\1)', content, flags=re.MULTILINE)

    return content, fixes_applied if content != original_content else 0


def fix_indentation_issues(content):
    """Fix general indentation issues"""
    fixes_applied = 0
    
    # Fix lines that have incorrect indentation levels
    lines = content.split("\n")
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # Check for common indentation issues
        stripped = line.lstrip()
        
        # If line starts with help= and has wrong indentation
        if stripped.startswith('help=') and len(line) - len(stripped) > 8:
            # Find proper indentation from context
            proper_indent = 4
            for j in range(i-1, max(0, i-5), -1):
                if "fields." in lines[j]:
                    proper_indent = len(lines[j]) - len(lines[j].lstrip()) + 4
                    break
            fixed_lines.append(" " * proper_indent + stripped)
            fixes_applied += 1
        else:
            fixed_lines.append(line)
    
    if fixes_applied > 0:
        content = "\n".join(fixed_lines)
    
    return content, fixes_applied


def fix_unclosed_parentheses(content):
    """Fix unclosed parentheses issues"""
    fixes_applied = 0
    
    # Simple fix for common patterns
    # Look for method definitions or field definitions missing closing parens
    lines = content.split("\n")
    paren_stack = []
    fixed_lines = []
    
    for line in lines:
        # Count parentheses
        open_parens = line.count("(")
        close_parens = line.count(")")
        
        # Track parentheses balance
        for _ in range(open_parens):
            paren_stack.append("(")
        for _ in range(close_parens):
            if paren_stack:
                paren_stack.pop()
        
        fixed_lines.append(line)
        
        # If we're at end of a field definition and missing closing paren
        if (line.strip().endswith(",") and 
            len(paren_stack) > 0 and 
            re.match(r'\s+(help=|string=|default=)', line)):
            # Check if next line doesn't close the paren
            next_line_idx = len(fixed_lines)
            needs_closing = True
            
            # Look ahead a few lines to see if there's already a closing paren
            for look_ahead in range(1, min(4, len(lines) - next_line_idx + 1)):
                if next_line_idx + look_ahead - 1 < len(lines):
                    next_line = lines[next_line_idx + look_ahead - 1].strip()
                    if next_line.startswith(")"):
                        needs_closing = False
                        break
                        
            if needs_closing and len(paren_stack) > 0:
                indent = len(line) - len(line.lstrip()) - 4
                fixed_lines.append(" " * max(0, indent) + ")")
                paren_stack.pop()
                fixes_applied += 1
    
    if fixes_applied > 0:
        content = "\n".join(fixed_lines)
    
    return content, fixes_applied


def fix_action_method_indentation(content):
    """Fix any remaining action method indentation issues"""
    fixes_applied = 0

    # Fix ensure_one calls with wrong indentation
    pattern = r'(\n\s{4}def action_\w+\([^)]*\):\s*\n\s*"""[^"]*"""\s*\n)\s{12,}(self\.ensure_one\(\))'
    replacement = r"\1        \2"
    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def analyze_specific_error(file_path, line_num):
    """Analyze the specific error at a given line"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_num <= len(lines):
            error_line = lines[line_num - 1]
            context_start = max(0, line_num - 3)
            context_end = min(len(lines), line_num + 2)

            print(f"   📍 Line {line_num}: {error_line.strip()}")
            print(f"   📝 Context:")
            for i in range(context_start, context_end):
                prefix = ">>>" if i == line_num - 1 else "   "
                print(f"      {prefix} {i+1:3d}: {lines[i].rstrip()}")

    except Exception as e:
        print(f"   ❌ Could not analyze: {e}")


def process_file(file_path):
    """Process a single file to fix syntax errors"""
    print(f"🔍 Processing: {file_path.name}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        total_fixes = 0

        # Apply field definition fixes
        content, fixes = fix_field_definition_patterns(content)
        total_fixes += fixes

        # Apply indentation fixes
        content, fixes = fix_indentation_issues(content)
        total_fixes += fixes

        # Apply action method fixes
        content, fixes = fix_action_method_indentation(content)
        total_fixes += fixes

        # Apply parentheses fixes
        content, fixes = fix_unclosed_parentheses(content)
        total_fixes += fixes

        # Write back if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✅ Applied {total_fixes} fixes")
            return total_fixes
        else:
            print(f"   ℹ️  No changes needed")
            return 0

    except Exception as e:
        print(f"   ❌ Error processing: {e}")
        return 0


def main():
    """Main function"""
    models_dir = Path("records_management/models")

    # Error files with their specific line numbers (from latest validation)
    error_files = {
        "barcode_product.py": 206,
        "service_item.py": 192,
        "shredding_hard_drive.py": 123,
        "portal_feedback_support_models.py": 73,
        "processing_log.py": 162,
        "paper_bale.py": 43,
        "records_location.py": 95,
        "shredding_team.py": 128,
        "paper_bale_recycling.py": 227,
        "shredding_inventory_item.py": 281,
        "records_vehicle.py": 54,
        "unlock_service_history.py": 60,
        "records_access_log.py": 234,
        "temp_inventory.py": 53,
        "signed_document.py": 42,
        "pickup_route.py": 53,
        "records_document_type.py": 65,
        "records_container_movement.py": 440,
    }

    print("🔧 SPECIALIZED SYNTAX ERROR FIXER")
    print("=" * 60)
    print(f"🎯 Targeting {len(error_files)} files with specific syntax errors")
    print("=" * 60)

    total_files_fixed = 0
    total_fixes_applied = 0

    for file_name, error_line in error_files.items():
        file_path = models_dir / file_name

        if not file_path.exists():
            print(f"⚠️  {file_name}: File not found")
            continue

        print(f"\n📁 {file_name} (error at line {error_line})")

        # Show the specific error context
        analyze_specific_error(file_path, error_line)

        # Apply fixes
        fixes = process_file(file_path)

        if fixes > 0:
            total_files_fixed += 1
            total_fixes_applied += fixes

    print("\n" + "=" * 60)
    print("📊 SPECIALIZED FIXER SUMMARY")
    print("=" * 60)
    print(f"🎯 Files processed: {len(error_files)}")
    print(f"✅ Files successfully fixed: {total_files_fixed}")
    print(f"🔧 Total fixes applied: {total_fixes_applied}")

    if total_fixes_applied > 0:
        print(f"\n🧪 NEXT STEPS:")
        print(
            f"   1. Run syntax validation: python development-tools/find_syntax_errors.py"
        )
        print(f"   2. Check remaining issues (if any)")
        print(f"   3. Test module loading in Odoo")
    else:
        print(f"\n⚠️  No automatic fixes were applied.")
        print(
            f"   These files may need manual inspection for complex syntax issues."
        )


if __name__ == "__main__":
    main()
