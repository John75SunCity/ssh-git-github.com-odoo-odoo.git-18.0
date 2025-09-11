#!/usr/bin/env python3
"""
Find remaining models that need view files created - improved version
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

    print("🔍 Scanning model files...")
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find model definitions - more precise regex
        model_matches = re.findall(r'_name\s*=\s*["\']([a-zA-Z][a-zA-Z0-9._]+)["\']', content)
        for model in model_matches:
            # Only include models that look like valid Odoo model names
            if '.' in model and len(model.split('.')) >= 2:
                all_models.add(model)
                print(f"  Found model: {model} (in {py_file.name})")

    print(f"\n📊 Found {len(all_models)} valid models total")

    # Get all models that have view files
    models_with_views = set()

    print("\n🔍 Scanning view files...")
    for view_file in views_dir.glob("*.xml"):
        with open(view_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find model references in views - more precise
        model_refs = re.findall(r'<field name="model">([a-zA-Z][a-zA-Z0-9._]+)</field>', content)
        model_refs.extend(re.findall(r'<field name="res_model">([a-zA-Z][a-zA-Z0-9._]+)</field>', content))

        for model in model_refs:
            model = model.strip()
            if model in all_models:  # Only count if it's one of our models
                models_with_views.add(model)

    print(f"📊 Found {len(models_with_views)} models with views")

    # Find models without views
    models_without_views = all_models - models_with_views

    print(f"\n⚠️  Models WITHOUT view files ({len(models_without_views)}):")

    # Group by priority
    core_models = []
    config_models = []
    extension_models = []

    for model in sorted(models_without_views):
        if any(word in model for word in ['extension', 'inherit']):
            extension_models.append(model)
        elif any(word in model for word in ['config', 'setting', 'version']):
            config_models.append(model)
        else:
            core_models.append(model)

    if core_models:
        print(f"\n🎯 PRIORITY - Core Business Models ({len(core_models)}):")
        for model in core_models:
            print(f"  - {model}")

    if config_models:
        print(f"\n⚙️  Configuration Models ({len(config_models)}):")
        for model in config_models:
            print(f"  - {model}")

    if extension_models:
        print(f"\n🔧 Extension Models ({len(extension_models)}) - May not need views:")
        for model in extension_models:
            print(f"  - {model}")

    return core_models, config_models, extension_models

if __name__ == "__main__":
    os.chdir("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    find_models_without_views()
