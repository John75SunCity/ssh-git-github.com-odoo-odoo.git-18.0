import os
import re
import csv
from xml.etree import ElementTree as ET

# Configuration
MODULE_DIR = 'records_management'
MODELS_DIR = os.path.join(MODULE_DIR, 'models')
VIEWS_DIR = os.path.join(MODULE_DIR, 'views')
REPORT_DIR = os.path.join(MODULE_DIR, 'report')  # Note: singular 'report' as per architecture
SECURITY_FILE = os.path.join(MODULE_DIR, 'security', 'ir.model.access.csv')
INIT_FILE = os.path.join(MODELS_DIR, '__init__.py')

# Helper functions
def get_model_names_from_files():
    models = []
    if not os.path.isdir(MODELS_DIR):
        print(f"Error: Models directory not found at {MODELS_DIR}")
        return models
    for filename in os.listdir(MODELS_DIR):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(MODELS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # This regex handles single and double quotes, and different spacing
                matches = re.findall(r"_name\s*=\s*['\"]([\w\.]+)['\"]", content)
                if matches:
                    models.extend(matches)
    return list(set(models)) # Return unique model names

def get_imported_models():
    imported = []
    if not os.path.exists(INIT_FILE):
        print(f"Error: __init__.py not found at {INIT_FILE}")
        return imported
    with open(INIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        # This regex finds all modules imported from the current package
        imports = re.findall(r"from \. import (\w+)", content)
        imported.extend(imports)
    return imported

def get_security_entries():
    entries = {}
    if not os.path.exists(SECURITY_FILE):
        print(f"Error: ir.model.access.csv not found at {SECURITY_FILE}")
        return entries
    with open(SECURITY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header row
        for row in reader:
            if row and len(row) > 2 and row[0].startswith('access_'):
                # model name is usually in the format model_my_model_name
                model_name_formatted = row[2].replace('model_', '').replace('_', '.')
                entries[model_name_formatted] = row
    return entries

def get_views_for_models():
    views = {}
    if not os.path.isdir(VIEWS_DIR):
        print(f"Error: Views directory not found at {VIEWS_DIR}")
        return views
    for filename in os.listdir(VIEWS_DIR):
        if filename.endswith('.xml'):
            filepath = os.path.join(VIEWS_DIR, filename)
            try:
                tree = ET.parse(filepath)
                root = tree.getroot()
                # Find all record tags that define a view
                for record in root.findall(".//record[@model='ir.ui.view']"):
                    model_field = record.find("./field[@name='model']")
                    if model_field is not None and model_field.text:
                        model_name = model_field.text
                        if model_name not in views:
                            views[model_name] = []
                        views[model_name].append(filename)
            except ET.ParseError:
                print(f"Warning: Could not parse XML in {filename}")
    return views

def get_reports():
    reports = []
    if not os.path.isdir(REPORT_DIR):
        # This is not an error, as a module may not have reports
        return reports
    for filename in os.listdir(REPORT_DIR):
        if filename.endswith(('.py', '.xml')) and not filename.startswith('__'):
            reports.append(filename)
    return reports

# --- Main Analysis ---
print("Starting Records Management Module Integrity Check...")
print("="*50)

all_models = get_model_names_from_files()
imported_modules = get_imported_models()
security_models = get_security_entries()
view_models = get_views_for_models()
report_files = get_reports()

# --- Analysis Logic ---
# Convert imported module names to a set for faster lookup
imported_set = set(imported_modules)
# Extract the last part of the model name to match against module file names
model_module_names = {m.split('.')[-1] for m in all_models}

missing_imports = model_module_names - imported_set
missing_security = [m for m in all_models if m not in security_models]
missing_views = [m for m in all_models if m not in view_models]

# --- Reporting ---
print(f"Found {len(all_models)} models in '{MODELS_DIR}'.")
print(f"Found {len(imported_modules)} imported modules in '{INIT_FILE}'.")
print(f"Found {len(security_models)} security entries in '{SECURITY_FILE}'.")
print(f"Found views for {len(view_models)} models in '{VIEWS_DIR}'.")
print(f"Found {len(report_files)} report files in '{REPORT_DIR}'.")
print("="*50)

if missing_imports:
    print("\n🔥 Missing Model Imports in models/__init__.py:")
    for module_name in sorted(list(missing_imports)):
        print(f"  - from . import {module_name}")
else:
    print("\n✅ All models appear to be correctly imported in models/__init__.py.")

if missing_security:
    print("\n🔥 Models Missing ir.model.access.csv Entries:")
    for model_name in sorted(missing_security):
        print(f"  - {model_name}")
else:
    print("\n✅ All models have corresponding security entries.")

if missing_views:
    print("\n🔥 Models Missing View Definitions:")
    for model_name in sorted(missing_views):
        print(f"  - {model_name}")
else:
    print("\n✅ All models appear to have corresponding view files.")

if report_files:
    print("\n📊 Reports Found:")
    for report_file in sorted(report_files):
        print(f"  - {report_file}")
else:
    print("\nℹ️ No reports found in the 'report/' directory.")

print("\nIntegrity check complete.")
