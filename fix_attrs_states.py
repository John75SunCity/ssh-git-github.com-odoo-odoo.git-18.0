#!/usr/bin/env python3
"""
Script to convert deprecated attrs and states attributes to Odoo 18.0 syntax
"""

import os
import re

def fix_attrs_and_states(file_path):
    """Fix attrs and states attributes in a view file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix states attributes
        # states="draft" -> invisible="state != 'draft'"
        content = re.sub(r'states="([^"]*)"', lambda m: convert_states(m.group(1)), content)
        
        # Fix simple attrs attributes
        # attrs="{'invisible': [('field', '=', 'value')]}" -> invisible="field == 'value'"
        # attrs="{'readonly': [('field', '!=', 'value')]}" -> readonly="field != 'value'"
        # attrs="{'required': [('field', 'in', ['value1','value2'])]}" -> required="field in ('value1','value2')"
        
        attrs_patterns = [
            (r"attrs=\"\{'invisible': \[\('([^']+)', '=', False\)\]\}\"", r'invisible="not \1"'),
            (r"attrs=\"\{'invisible': \[\('([^']+)', '!=', False\)\]\}\"", r'invisible="\1"'),
            (r"attrs=\"\{'invisible': \[\('([^']+)', '=', '([^']+)'\)\]\}\"", r'invisible="\1 == \'\2\'"'),
            (r"attrs=\"\{'invisible': \[\('([^']+)', '!=', '([^']+)'\)\]\}\"", r'invisible="\1 != \'\2\'"'),
            (r"attrs=\"\{'invisible': \[\('([^']+)', '=', 0\)\]\}\"", r'invisible="\1 == 0"'),
            (r"attrs=\"\{'readonly': \[\('([^']+)', '!=', '([^']+)'\)\]\}\"", r'readonly="\1 != \'\2\'"'),
            (r"attrs=\"\{'readonly': \[\('([^']+)', '=', '([^']+)'\)\]\}\"", r'readonly="\1 == \'\2\'"'),
            (r"attrs=\"\{'required': \[\('([^']+)', 'in', \[([^\]]+)\]\)\]\}\"", r'required="\1 in (\2)"'),
        ]
        
        for pattern, replacement in attrs_patterns:
            content = re.sub(pattern, replacement, content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Fixed {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def convert_states(states_value):
    """Convert states value to invisible attribute"""
    states = [s.strip() for s in states_value.split(',')]
    if len(states) == 1:
        return f'invisible="state != \'{states[0]}\'"'
    else:
        states_str = "', '".join(states)
        return f'invisible="state not in (\'{states_str}\')"'

# Process all view files
views_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/records_management/views"
for filename in os.listdir(views_dir):
    if filename.endswith('.xml'):
        file_path = os.path.join(views_dir, filename)
        fix_attrs_and_states(file_path)

print("Done!")
