#!/usr/bin/env python3
import os
import re

def extract_model_names():
    """Extract all model names from the records_management module"""
    models_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    model_names = set()

    for root, dirs, files in os.walk(models_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Find all _name assignments
                    name_pattern = r"_name\s*=\s*['\"]([^'\"]+)['\"]"
                    matches = re.findall(name_pattern, content)
                    for match in matches:
                        model_names.add(match.strip())

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return sorted(list(model_names))

if __name__ == "__main__":
    models = extract_model_names()
    print(f"Found {len(models)} models:")
    for model in models:
        print(f"  {model}")
