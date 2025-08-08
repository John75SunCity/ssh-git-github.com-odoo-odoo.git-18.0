#!/usr/bin/env python3
"""
Advanced Selection Field Fixer
Fixes malformed Selection field definitions properly
"""

import re
from pathlib import Path

def fix_selection_field_syntax(file_path):
    """Fix malformed Selection field definitions"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Pattern: Fix malformed Selection fields like:
        # fields.Selection([('placeholder', 'Placeholder')]
        #     ('option1', 'Label1'),)
        #     ('option2', 'Label2'),
        
        # Find Selection field patterns
        selection_pattern = r"(fields\.Selection\(\[)\('placeholder', 'Placeholder'\)\]\s*\n\s*(\([^)]+\),\s*\)\s*\n.*?)(\], [^)]*\))"
        
        def fix_selection_match(match):
            start = match.group(1)  # "fields.Selection(["
            options_part = match.group(2)  # The malformed options
            end = match.group(3)  # "], string=...)"
            
            # Clean up the options part
            # Remove extra parentheses and fix formatting
            options_clean = re.sub(r'\),\s*\)\s*\n\s*', '),\n        ', options_part)
            options_clean = re.sub(r'^\s*', '        ', options_clean, flags=re.MULTILINE)
            
            return f"{start}\n{options_clean}\n    {end}"
        
        if re.search(selection_pattern, content, re.DOTALL):
            content = re.sub(selection_pattern, fix_selection_match, content, flags=re.DOTALL)
            fixes_applied.append("Fixed malformed Selection field syntax")
        
        # Alternative approach - manually fix the specific pattern we saw
        # Look for the exact broken pattern and fix it
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for the specific broken pattern
            if "fields.Selection([('placeholder', 'Placeholder')]" in line:
                # This is the start of a broken Selection field
                field_lines = [line.replace("[('placeholder', 'Placeholder')]", "[")]
                i += 1
                
                # Collect the actual selection options
                while i < len(lines) and not lines[i].strip().startswith('], '):
                    option_line = lines[i].strip()
                    if option_line.endswith(',)'):
                        # Fix the broken syntax
                        option_line = option_line[:-2] + ','
                    elif option_line.endswith(','):
                        pass  # Already correct
                    
                    if option_line.startswith('(') and option_line.endswith(','):
                        field_lines.append(f"        {option_line}")
                    i += 1
                
                # Add the closing part
                if i < len(lines):
                    closing_line = lines[i]
                    field_lines.append(f"    {closing_line}")
                    i += 1
                
                fixed_lines.extend(field_lines)
                fixes_applied.append("Fixed Selection field bracket syntax")
            else:
                fixed_lines.append(line)
                i += 1
        
        if fixes_applied:
            content = '\n'.join(fixed_lines)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixes_applied
        
        return False, []
        
    except Exception as e:
        return False, [f"Error: {str(e)}"]

def main():
    """Fix Selection field syntax issues"""
    models_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    print("=== Advanced Selection Field Fixer ===")
    
    # Test on the specific file first
    file_path = models_dir / 'advanced_billing.py'
    
    print(f"Fixing: {file_path.name}")
    success, fixes = fix_selection_field_syntax(file_path)
    
    if success:
        print(f"✓ Applied fixes: {', '.join(fixes)}")
    else:
        print("✗ No fixes applied")
    
    return success

if __name__ == "__main__":
    main()
