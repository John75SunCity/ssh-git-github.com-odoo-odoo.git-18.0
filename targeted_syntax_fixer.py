#!/usr/bin/env python3
"""
Precise syntax error fixer for specific issues identified
"""

import re
from pathlib import Path

def fix_duplicate_message_posts(content, filename):
    """Fix duplicate message_post calls that were concatenated"""
    fixes_applied = 0
    
    # Pattern: Multiple message_post calls concatenated
    pattern = r'self\.message_post\(body=_\("Action completed"\)\)body=_\([^)]+\)\)'
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        old_text = match.group(0)
        # Extract the actual message from the second part
        message_match = re.search(r'body=_\("([^"]+)"\)\)$', old_text)
        if message_match:
            actual_message = message_match.group(1)
            new_text = f'self.message_post(body=_("{actual_message}"))'
            content = content.replace(old_text, new_text)
            fixes_applied += 1
            print(f"  Fixed duplicate message_post: {filename}")
    
    return content, fixes_applied

def fix_unclosed_parentheses_specific(content, filename):
    """Fix specific unclosed parentheses issues"""
    fixes_applied = 0
    
    # Pattern 1: display_name assignments missing closing parenthesis
    patterns = [
        (r'record\.display_name = _\("([^"]+)"\s*%\s*([^)]+)(?=\s*$)', r'record.display_name = _("\1", \2)'),
        (r'name = _\("([^"]+)"\s*%\s*([^)]+)(?=\s*$)', r'name = _("\1", \2)'),
        (r'record\.display_name = _\("([^"]*%s[^"]*)"(?=\s*$)', r'record.display_name = _("\1", "Unknown")'),
    ]
    
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            fixes_applied += count
            print(f"  Fixed {count} unclosed parentheses patterns: {filename}")
    
    return content, fixes_applied

def fix_incomplete_if_elif_else(content, filename):
    """Fix incomplete if/elif/else statements with proper indentation"""
    fixes_applied = 0
    
    # Find and fix incomplete statements
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for incomplete if/elif/else statements
        if re.match(r'^\s*(if|elif)\s+[^:]+:\s*$', line):
            # Check if next line is another control statement or end of block
            next_i = i + 1
            needs_pass = True
            
            if next_i < len(lines):
                next_line = lines[next_i].strip()
                # If next line has content and proper indentation, don't add pass
                if next_line and not re.match(r'^\s*(if|elif|else|def|class)', next_line):
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(lines[next_i]) - len(lines[next_i].lstrip())
                    if next_indent > current_indent:
                        needs_pass = False
            
            fixed_lines.append(line)
            if needs_pass:
                # Add pass with proper indentation
                indent = len(line) - len(line.lstrip()) + 4
                fixed_lines.append(' ' * indent + 'pass')
                fixes_applied += 1
            
        elif re.match(r'^\s*else:\s*$', line):
            # Check if next line exists and has proper content
            next_i = i + 1
            needs_pass = True
            
            if next_i < len(lines):
                next_line = lines[next_i].strip()
                if next_line and not re.match(r'^\s*(if|elif|else|def|class)', next_line):
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(lines[next_i]) - len(lines[next_i].lstrip())
                    if next_indent > current_indent:
                        needs_pass = False
            
            fixed_lines.append(line)
            if needs_pass:
                # Add pass with proper indentation  
                indent = len(line) - len(line.lstrip()) + 4
                fixed_lines.append(' ' * indent + 'pass')
                fixes_applied += 1
        else:
            fixed_lines.append(line)
        
        i += 1
    
    if fixes_applied > 0:
        content = '\n'.join(fixed_lines)
        print(f"  Fixed {fixes_applied} incomplete control statements: {filename}")
    
    return content, fixes_applied

def fix_unmatched_parentheses(content, filename):
    """Fix unmatched closing parentheses"""
    fixes_applied = 0
    
    # Pattern: Lines ending with unmatched )
    pattern = r'^(\s*[^)]*)\)(\s*)$'
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if re.match(pattern, line) and line.count('(') < line.count(')'):
            # Remove extra closing parenthesis
            fixed_line = re.sub(r'\)(\s*)$', r'\1', line)
            fixed_lines.append(fixed_line)
            fixes_applied += 1
        else:
            fixed_lines.append(line)
    
    if fixes_applied > 0:
        content = '\n'.join(fixed_lines)
        print(f"  Fixed {fixes_applied} unmatched closing parentheses: {filename}")
    
    return content, fixes_applied

def fix_method_definitions(content, filename):
    """Fix incomplete method definitions"""
    fixes_applied = 0
    
    # Pattern: def method(self, args): without body
    pattern = r'(def\s+\w+\([^)]+\):\s*)\n(\s*"""[^"]*"""\s*)?(?=\n\s*(def|class|\Z))'
    
    def replace_method(match):
        method_def = match.group(1)
        docstring = match.group(2) or ''
        indent = '        '  # Standard method body indent
        return method_def + '\n' + docstring + '\n' + indent + 'pass\n'
    
    new_content, count = re.subn(pattern, replace_method, content, flags=re.MULTILINE | re.DOTALL)
    if count > 0:
        content = new_content
        fixes_applied = count
        print(f"  Fixed {count} incomplete method definitions: {filename}")
    
    return content, fixes_applied

def process_file(file_path):
    """Process a single file with targeted fixes"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        total_fixes = 0
        
        print(f"\nProcessing {file_path.name}...")
        
        # Apply targeted fixes
        content, fixes = fix_duplicate_message_posts(content, file_path.name)
        total_fixes += fixes
        
        content, fixes = fix_unclosed_parentheses_specific(content, file_path.name)
        total_fixes += fixes
        
        content, fixes = fix_unmatched_parentheses(content, file_path.name)
        total_fixes += fixes
        
        content, fixes = fix_incomplete_if_elif_else(content, file_path.name)
        total_fixes += fixes
        
        content, fixes = fix_method_definitions(content, file_path.name)
        total_fixes += fixes
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Applied {total_fixes} targeted fixes to {file_path.name}")
        else:
            print(f"⚪ No additional fixes needed for {file_path.name}")
            
        return total_fixes
        
    except Exception as e:
        print(f"❌ Error processing {file_path.name}: {e}")
        return 0

def main():
    """Main execution for targeted fixes"""
    models_dir = Path("records_management/models")
    
    # Files that still have issues after first fix
    problem_files = [
        "barcode_product.py",
        "service_item.py", 
        "shredding_hard_drive.py",
        "shredding_certificate.py",
        "records_container_type_converter.py",
        "shredding_inventory_item.py",
        "bin_unlock_service.py",
        "approval_history.py",
        "portal_request.py",
        "shredding_service.py",
        "hr_employee_naid.py",
        "records_vehicle.py",
        "unlock_service_history.py",
        "records_billing_contact.py",
        "signed_document.py",
        "pickup_request.py",
        "pickup_route.py",
        "records_department.py",
        "transitory_field_config.py",
        "paper_load_shipment.py",
        "records_document.py"
    ]
    
    total_fixes = 0
    files_processed = 0
    
    print("🎯 Starting targeted syntax fixes for remaining issues...")
    
    for filename in problem_files:
        file_path = models_dir / filename
        if file_path.exists():
            fixes = process_file(file_path)
            total_fixes += fixes
            files_processed += 1
    
    print(f"\n📊 Targeted Fix Summary:")
    print(f"   Files processed: {files_processed}")
    print(f"   Total fixes applied: {total_fixes}")
    print(f"\n✅ Targeted syntax fixing complete!")

if __name__ == "__main__":
    main()
