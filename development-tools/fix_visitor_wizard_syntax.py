#!/usr/bin/env python3
"""
Fix syntax errors in visitor_pos_wizard.py by adding missing closing brackets
and parentheses to Selection field definitions.
"""

import re

def fix_selection_fields(file_path):
    """Fix all Selection fields missing closing brackets and parentheses."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split into lines for processing
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a Selection field definition
        if re.match(r'\s*\w+\s*=\s*fields\.Selection\(\[', line):
            # Find the field name
            field_match = re.match(r'\s*(\w+)\s*=\s*fields\.Selection\(\[', line)
            if field_match:
                field_name = field_match.group(1)
                
                # Start collecting the selection items
                selection_lines = [line]
                i += 1
                
                # Look for selection tuples
                while i < len(lines):
                    current_line = lines[i]
                    selection_lines.append(current_line)
                    
                    # Check if this is the end of selection items (next field or method)
                    if (re.match(r'\s*\w+\s*=\s*fields\.', current_line) or 
                        re.match(r'\s*def\s+', current_line) or
                        re.match(r'\s*@api\.', current_line) or
                        re.match(r'\s*#', current_line) or
                        current_line.strip() == ''):
                        
                        # Remove the last line (it's the next field/method)
                        selection_lines.pop()
                        
                        # Add closing bracket and parameters
                        display_name = ' '.join(word.capitalize() for word in field_name.split('_'))
                        closing_line = f'    ], string="{display_name}", default="")'
                        selection_lines.append(closing_line)
                        
                        # Add all selection lines to fixed_lines
                        fixed_lines.extend(selection_lines)
                        
                        # Don't increment i, process the current line again
                        i -= 1
                        break
                    i += 1
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        
        i += 1
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    return len([line for line in fixed_lines if 'fields.Selection' in line and '], string=' in line])

if __name__ == '__main__':
    file_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/visitor_pos_wizard.py'
    fixed_count = fix_selection_fields(file_path)
    print(f"Fixed {fixed_count} Selection field definitions in visitor_pos_wizard.py")
