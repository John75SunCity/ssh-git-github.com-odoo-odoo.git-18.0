#!/usr/bin/env python3
"""
Targeted Field Definition Fixer
Fixes the specific field definition syntax errors identified by Black
"""

import re
from pathlib import Path

def fix_field_definitions(file_path):
    """Fix broken field definitions that cause syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Pattern 1: Fix fields.Type()...parameters on next line
        # fields.Many2one()
        #     "model.name",
        #     parameter=value
        # )
        
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for field definition with empty parentheses
            field_match = re.match(r'(\s*)(\w+)\s*=\s*fields\.(\w+)\(\)', line)
            if field_match:
                indent = field_match.group(1)
                field_name = field_match.group(2)
                field_type = field_match.group(3)
                
                # Look ahead for parameters
                parameters = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        i += 1
                        continue
                    if next_line == ')':
                        break
                    if (next_line.startswith('"') or 
                        next_line.startswith("'") or 
                        next_line.startswith('string=') or
                        next_line.startswith('help=') or
                        next_line.startswith('required=') or
                        next_line.startswith('default=') or
                        next_line.startswith('ondelete=') or
                        next_line.startswith('domain=') or
                        next_line.startswith('tracking=') or
                        next_line.startswith('index=') or
                        next_line.startswith('compute=') or
                        next_line.startswith('store=')):
                        parameters.append(next_line.rstrip(','))
                    elif next_line.startswith('[') or next_line.startswith('('):
                        # This is likely a Selection field or similar
                        parameters.append(next_line.rstrip(','))
                    else:
                        break
                    i += 1
                
                # Reconstruct the field definition
                if parameters:
                    if field_type == 'Selection' and parameters[0].startswith('['):
                        # Special handling for Selection fields
                        fixed_lines.append(f'{indent}{field_name} = fields.{field_type}({parameters[0]},')
                        for param in parameters[1:]:
                            fixed_lines.append(f'{indent}    {param}')
                        fixed_lines.append(f'{indent})')
                    else:
                        # Regular field with parameters
                        fixed_lines.append(f'{indent}{field_name} = fields.{field_type}(')
                        for param in parameters:
                            fixed_lines.append(f'{indent}    {param},')
                        fixed_lines.append(f'{indent})')
                    
                    fixes_applied.append(f"Fixed {field_type} field: {field_name}")
                else:
                    # No parameters found, just close the field
                    fixed_lines.append(f'{indent}{field_name} = fields.{field_type}()')
                
                continue
            
            fixed_lines.append(line)
            i += 1
        
        if fixes_applied:
            content = '\n'.join(fixed_lines)
        
        # Pattern 2: Fix trailing commas in string parameters
        content = re.sub(r'string="([^"]*)",\s*$', r'string="\1"', content, flags=re.MULTILINE)
        content = re.sub(r"string='([^']*)',\s*$", r"string='\1'", content, flags=re.MULTILINE)
        
        # Pattern 3: Fix broken method calls
        content = re.sub(r'\.write\(\)\s*\n\s*\{', r'.write({', content)
        content = re.sub(r'\.create\(\)\s*\n\s*\{', r'.create({', content)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixes_applied
        
        return False, []
        
    except Exception as e:
        return False, [f"Error: {str(e)}"]

def main():
    """Fix field definition issues in Python files"""
    models_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    print("=== Targeted Field Definition Fixer ===")
    
    # Priority files that had field definition issues
    priority_files = [
        'advanced_billing.py',
        'hr_employee.py', 
        'records_box.py',
        'partner_bin_key.py',
        'records_chain_of_custody.py',
        'survey_user_input.py',
        'naid_compliance.py',
        'records_location.py',
        'visitor.py',
        'portal_request.py'
    ]
    
    fixed_count = 0
    
    for filename in priority_files:
        file_path = models_dir / filename
        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue
            
        print(f"\nFixing: {filename}")
        
        success, fixes = fix_field_definitions(file_path)
        if success:
            print(f"✓ Applied: {', '.join(fixes)}")
            fixed_count += 1
        else:
            print(f"- No changes needed")
    
    print(f"\n=== Summary ===")
    print(f"Files processed: {len(priority_files)}")
    print(f"Files fixed: {fixed_count}")
    
    return fixed_count > 0

if __name__ == "__main__":
    main()
