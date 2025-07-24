#!/bin/bash

# Script to add remaining missing @api.depends() decorators

echo "🔧 Adding remaining @api.depends() decorators..."

# Files to process
FILES=(
    "records_management/models/naid_audit.py"
    "records_management/models/portal_feedback.py"
    "records_management/models/records_document.py"
    "records_management/models/load.py"
    "records_management/models/visitor_pos_wizard.py"
    "records_management/models/records_tag.py"
    "records_management/models/pickup_request.py"
    "records_management/models/records_document_type.py"
    "records_management/models/customer_inventory_report.py"
)

# Add @api.depends() decorator before compute methods
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  🔧 Processing $file"
        
        # Find all _compute_ methods and add @api.depends() if missing
        python3 -c "
import re

with open('$file', 'r') as f:
    content = f.read()

# Find all compute methods without @api.depends
lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if this is a compute method definition
    if re.match(r'\s*def _compute_\w+\(', line):
        # Check if previous lines have @api.depends
        has_depends = False
        for j in range(max(0, i-5), i):
            if '@api.depends(' in lines[j]:
                has_depends = True
                break
        
        if not has_depends:
            # Add @api.depends() decorator
            indent = len(line) - len(line.lstrip())
            decorator = ' ' * indent + '@api.depends()'
            new_lines.append(decorator)
        
        new_lines.append(line)
    else:
        new_lines.append(line)
    
    i += 1

# Write back to file
with open('$file', 'w') as f:
    f.write('\n'.join(new_lines))
"
        
        echo "  ✅ Processed $file"
    else
        echo "  ❌ File not found: $file"
    fi
done

echo "🎉 Completed processing remaining files!"
