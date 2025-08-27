#!/usr/bin/env python3
"""
Find remaining models that need view files created
"""

import os
import re
from pathlib import Path

def find_models_without_views():
    """Find all models that don't have corresponding view files"""

    models_dir = Path("records_management/models")
    views_dir = Path("records_management/views")

    # Get all model names from Python files
    all_models = set()

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find model definitions
        model_matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        for model in model_matches:
            # Skip extension models (they inherit from other models)
            if not any(skip in py_file.name for skip in ['extension', 'inherit']):
                all_models.add(model)

    print(f"📊 Found {len(all_models)} models total")

    # Get all models that have view files
    models_with_views = set()

    for view_file in views_dir.glob("*.xml"):
        with open(view_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find model references in views
        model_refs = re.findall(r'<field name="model">([^<]+)</field>', content)
        model_refs.extend(re.findall(r'<field name="res_model">([^<]+)</field>', content))

        for model in model_refs:
            models_with_views.add(model.strip())

    print(f"📊 Found {len(models_with_views)} models with views")

    # Find models without views
    models_without_views = all_models - models_with_views

    print(f"\n⚠️  Models WITHOUT view files ({len(models_without_views)}):")
    for model in sorted(models_without_views):
        print(f"  - {model}")

    return models_without_views

if __name__ == "__main__":
    os.chdir("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    find_models_without_views()
