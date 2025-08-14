#!/usr/bin/env python3
"""
Fix All Bracket Mismatches in Files - Odoo-Aware Version
Systematically fixes mismatched brackets in Odoo method calls with context awareness.
"""

import os
import re
import py_compile


def fix_write_create_mismatches(content):
    """
    Fixes bracket mismatches for write() and create() methods.
    These methods expect dictionaries with curly braces {}.
    """
    # Pattern 1: Fix write((key: value)) -> write({key: value})
    # Pattern for dictionary-like content inside double parentheses
    pattern_double_parens = (
        r"(\.(?:write|create)\s*\()\s*\(([\s\S]*?:[\s\S]*?)\)\s*(\))"
    )
    content = re.sub(pattern_double_parens, r"\1{\2}\3", content)

    # Pattern 2: Fix incomplete write({ ... ) -> write({ ... })
    lines = content.split('\n')
    fixed_lines = []
    in_dict_block = False
    brace_count = 0
    paren_count = 0
    method_start_line = -1

    for i, line in enumerate(lines):
        # Detect start of write/create with opening brace
        if re.search(r"\.(?:write|create)\s*\(\s*\{", line):
            in_dict_block = True
            method_start_line = i
            brace_count = line.count('{') - line.count('}')
            paren_count = line.count("(") - line.count(")")

        elif in_dict_block:
            brace_count += line.count("{") - line.count("}")
            paren_count += line.count("(") - line.count(")")

            # Fix mismatched closing: ) instead of })
            if (
                brace_count > 0
                and paren_count > 0
                and (line.strip() == ")" or line.strip() == "))")
            ):
                if line.strip() == ")":
                    fixed_lines.append(line.replace(")", "})"))
                else:  # '))'
                    fixed_lines.append(line.replace("))", "})"))
                in_dict_block = False
                continue

        fixed_lines.append(line)

        # Reset if we've balanced everything
        if in_dict_block and brace_count <= 0 and paren_count <= 1:
            in_dict_block = False

    return '\n'.join(fixed_lines)


def fix_selection_field_brackets(content):
    """
    Fix fields.Selection and similar field definitions that should use square brackets [].
    """
    # Pattern: fields.Selection((...)) -> fields.Selection([...])
    # Look for field definitions with tuples of tuples (selection options)
    pattern = r"(fields\.Selection\s*\()\s*\(\s*(\([^)]*\)[^)]*)\s*\)\s*(\))"

    def replace_selection(match):
        prefix = match.group(1)  # "fields.Selection("
        content = match.group(2)  # The selection options
        suffix = match.group(3)  # ")"
        return f"{prefix}[{content}]{suffix}"

    content = re.sub(
        pattern, replace_selection, content, flags=re.MULTILINE | re.DOTALL
    )

    # Also fix single-line selection patterns
    pattern_simple = r"(fields\.Selection\s*\()\s*\(([^)]*)\)\s*(\))"
    content = re.sub(pattern_simple, r"\1[\2]\3", content)

    return content


def fix_method_parameter_brackets(content):
    """
    Fix method parameter bracket mismatches while preserving context.
    """
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Fix common parameter bracket issues
        # Example: method_call{args} -> method_call(args)
        if re.search(r"\w+\s*\{[^}]*\}(?!\s*[,\)])", line):
            # This looks like method_call{args} which should be method_call(args)
            line = re.sub(r"(\w+)\s*\{([^}]*)\}", r"\1(\2)", line)

        # Fix trailing bracket issues in method calls
        line = re.sub(r"(\w+\([^)]*),\s*\)\s*\}", r"\1)}", line)

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_odoo_specific_patterns(content):
    """
    Fix Odoo-specific bracket patterns with context awareness.
    """
    # 1. Fix write/create methods (expect dictionaries)
    content = fix_write_create_mismatches(content)

    # 2. Fix selection fields (expect lists)
    content = fix_selection_field_brackets(content)

    # 3. Fix general parameter brackets
    content = fix_method_parameter_brackets(content)

    # 4. Fix domain brackets - domains should use lists []
    # Pattern: domain=((field, operator, value)) -> domain=[(field, operator, value)]
    domain_pattern = r"(domain\s*=\s*)\(\s*\((.*?)\)\s*\)"
    content = re.sub(
        domain_pattern, r"\1[(\2)]", content, flags=re.MULTILINE | re.DOTALL
    )

    return content


def validate_python_syntax(filepath):
    """Validate Python syntax after fixing"""
    try:
        py_compile.compile(filepath, doraise=True)
        return True, "Syntax valid"
    except py_compile.PyCompileError as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def fix_file_bracket_mismatches(filepath):
    """Fix bracket mismatches in a single file with Odoo awareness"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Apply Odoo-aware bracket fixes
        content = fix_odoo_specific_patterns(content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            # Validate syntax after fixing
            syntax_valid, syntax_msg = validate_python_syntax(filepath)
            return True, f"Fixed bracket mismatches - {syntax_msg}"

        return False, "No bracket mismatches found"

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Main function to fix all files with bracket mismatch errors"""
    # Files with known bracket mismatch errors
    error_files = [
        'document_retrieval_item.py',
        'portal_feedback_analytic.py',
        'naid_compliance_action_plan.py', 
        'naid_compliance_support_models.py',
        'barcode_product.py',
        'naid_risk_assessment.py',
        'base_rate.py',
        'records_location.py',
        'product_container_type.py',
        'records_customer_billing_profile.py',
        'approval_history.py',
        'naid_compliance_alert.py',
        'records_access_log.py',
        'portal_feedback.py',
        'records_billing_contact.py',
        'file_retrieval_work_order_item.py',
        'records_billing_profile.py'
    ]

    print("🔧 Fixing bracket mismatches with Odoo-aware patterns...\n")

    fixed_count = 0
    valid_count = 0

    for filename in error_files:
        filepath = f'records_management/models/{filename}'
        if os.path.exists(filepath):
            print(f"🔧 Processing {filename}...")
            success, message = fix_file_bracket_mismatches(filepath)

            if success:
                print(f"   ✅ {message}")
                fixed_count += 1
                if "Syntax valid" in message:
                    valid_count += 1
            else:
                print(f"   ⏭️  {message}")
        else:
            print(f"   ❌ File not found: {filename}")

    print(f"\n📊 Summary:")
    print(f"   • Files processed: {len(error_files)}")
    print(f"   • Files modified: {fixed_count}")
    print(f"   • Files with valid syntax: {valid_count}")

    if fixed_count > 0:
        print(f"\n🎯 Odoo-aware fixes applied:")
        print(
            f"   • write/create methods: Use curly braces {{}} for dictionaries"
        )
        print(
            f"   • fields.Selection: Use square brackets [] for option lists"
        )
        print(f"   • Domain filters: Use square brackets [] for domain lists")
        print(f"   • Method parameters: Use parentheses () for arguments")

if __name__ == '__main__':
    main()
