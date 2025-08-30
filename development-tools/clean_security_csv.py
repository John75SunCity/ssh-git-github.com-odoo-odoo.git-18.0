#!/usr/bin/env python3
"""
Clean Security CSV Generator
Creates a clean ir.model.access.csv file with only valid model references
"""

import os
import re

# Get valid model names from the codebase
def get_valid_models():
    """Extract valid model names from Python files"""
    valid_models = set()
    models_dir = "records_management/models"

    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find _name = 'model.name' patterns
                    matches = re.findall(r"_name\s*=\s*['\"]([a-zA-Z0-9._]+)['\"]", content)
                    for match in matches:
                        # Only include proper model names (with dots and alphanumeric)
                        if '.' in match and not any(c in match for c in [' ', '(', ')', '%', ':', '?', 'if', 'else']):
                            valid_models.add(match)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

    return sorted(valid_models)

def create_clean_csv():
    """Create a clean CSV file with only valid models"""
    valid_models = get_valid_models()

    print(f"Found {len(valid_models)} valid models:")
    for model in valid_models:
        print(f"  - {model}")

    # Generate CSV content
    csv_lines = ["id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"]

    for model in valid_models:
        # Convert model name to external ID format (replace dots with underscores)
        model_id = f"model_{model.replace('.', '_')}"
        access_id_user = f"access_{model.replace('.', '_')}_user"
        access_id_manager = f"access_{model.replace('.', '_')}_manager"

        # Add user access (read, write, create, no unlink)
        csv_lines.append(
            f"{access_id_user},{model},{model_id},records_management.group_records_user,1,1,1,0"
        )

        # Add manager access (full access)
        csv_lines.append(
            f"{access_id_manager},{model},{model_id},records_management.group_records_manager,1,1,1,1"
        )

    # Write the clean CSV
    output_path = "records_management/security/ir.model.access.csv"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(csv_lines) + '\n')

    print(f"\n✅ Created clean CSV with {len(csv_lines)-1} access rules")
    print(f"📄 File: {output_path}")

if __name__ == "__main__":
    create_clean_csv()
