import os
import re
import csv
from xml.etree import ElementTree as ET
from collections import defaultdict

# Configuration
MODULE_DIR = 'records_management'
MODELS_DIR = os.path.join(MODULE_DIR, 'models')
VIEWS_DIR = os.path.join(MODULE_DIR, 'views')
REPORT_DIR = os.path.join(MODULE_DIR, 'report')
SECURITY_FILE = os.path.join(MODULE_DIR, 'security', 'ir.model.access.csv')
INIT_FILE = os.path.join(MODELS_DIR, '__init__.py')

# Helper functions
def get_model_name_to_file_map():
    model_map = {}
    if not os.path.isdir(MODELS_DIR):
        print(f"Error: Models directory not found at {MODELS_DIR}")
        return model_map, []

    all_model_names = []
    for filename in os.listdir(MODELS_DIR):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(MODELS_DIR, filename)
            module_name = filename[:-3]  # remove .py
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r"_name\s*=\s*['\"]([\w\.]+)['\"]", content)
                if matches:
                    for model_name_str in matches:
                        model_map[model_name_str] = module_name
                        all_model_names.append(model_name_str)
    return model_map, list(set(all_model_names))

def get_imported_models():
    imported = []
    if not os.path.exists(INIT_FILE):
        print(f"Error: __init__.py not found at {INIT_FILE}")
        return imported
    with open(INIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        imports = re.findall(r"from \. import (\w+)", content)
        imported.extend(imports)
    return list(set(imported))

def get_security_entries():
    entries = defaultdict(list)
    if not os.path.exists(SECURITY_FILE):
        print(f"Error: ir.model.access.csv not found at {SECURITY_FILE}")
        return entries
    with open(SECURITY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader, None)
            if header is None: return entries
            # Find the column for model_id:id, which is more reliable than a fixed index
            model_col_index = -1
            for i, col in enumerate(header):
                if 'model_id' in col:
                    model_col_index = i
                    break
            if model_col_index == -1:
                 # Fallback for safety
                model_col_index = 2
                f.seek(0)
                next(reader, None) # Skip header again

        except (StopIteration, ValueError):
            # If header is missing or corrupt, fallback to default index
            model_col_index = 2
            # Rewind file to read from the start
            f.seek(0)

        for row in reader:
            if row and len(row) > model_col_index and row[0].startswith('access_'):
                model_id_str = row[model_col_index]
                # Handle both formats: model_res_partner and res.partner
                if model_id_str.startswith('model_'):
                    model_name = model_id_str[len('model_'):].replace('_', '.')
                else:
                    # This case might not be needed if CSV is standardized, but good for robustness
                    model_name = model_id_str
                entries[model_name].append(row)
    return entries

def get_views_for_models():
    views = defaultdict(list)
    if not os.path.isdir(VIEWS_DIR):
        print(f"Error: Views directory not found at {VIEWS_DIR}")
        return views
    for filename in os.listdir(VIEWS_DIR):
        if filename.endswith('.xml'):
            filepath = os.path.join(VIEWS_DIR, filename)
            try:
                tree = ET.parse(filepath)
                root = tree.getroot()
                for record in root.findall(".//record"):
                    model_field = record.find("./field[@name='model']")
                    res_model_field = record.find("./field[@name='res_model']")
                    model_name = None
                    if model_field is not None and model_field.text:
                        model_name = model_field.text
                    elif res_model_field is not None and res_model_field.text:
                        model_name = res_model_field.text
                    if model_name:
                        if filename not in views[model_name]:
                            views[model_name].append(filename)
            except ET.ParseError:
                print(f"Warning: Could not parse XML in {filename}")
    return views

def get_reports():
    reports = []
    if not os.path.isdir(REPORT_DIR):
        return reports
    for filename in os.listdir(REPORT_DIR):
        if filename.endswith(('.py', '.xml')) and not filename.startswith('__'):
            reports.append(filename)
    return reports

# --- Main Analysis ---
print("Starting Records Management Module Integrity Check...")
print("="*50)

all_model_map, all_models = get_model_name_to_file_map()
imported_modules = get_imported_models()
security_models = get_security_entries()
view_models = get_views_for_models()
report_files = get_reports()

# --- Analysis Logic ---
imported_set = set(imported_modules)
model_module_files = set(all_model_map.values())
missing_imports = model_module_files - imported_set

# --- Reporting ---
print(f"Found {len(all_models)} models in {len(model_module_files)} Python files in '{MODELS_DIR}'.")
print(f"Found {len(imported_modules)} imported modules in '{INIT_FILE}'.")
print(f"Found {sum(len(v) for v in security_models.values())} security entries for {len(security_models)} models in '{SECURITY_FILE}'.")
print(f"Found views for {len(view_models)} models in '{VIEWS_DIR}'.")
print(f"Found {len(report_files)} report files in '{REPORT_DIR}'.")
print("="*50)

# --- Import Analysis ---
if missing_imports:
    print("\n🔥 Missing Model Imports in models/__init__.py:")
    for module_name in sorted(list(missing_imports)):
        print(f"  - from . import {module_name}")
else:
    print("\n✅ All models appear to be correctly imported in models/__init__.py.")

# --- Security Analysis ---
print("\n🔐 Security Rule Status (ir.model.access.csv):")
if not all_models:
    print("  - No models found to check.")
else:
    for model_name in sorted(all_models):
        # Check for direct model name and the model_ prefixed version
        direct_name_entries = security_models.get(model_name, [])
        model_prefixed_name = f"model_{model_name.replace('.', '_')}"

        # This logic is simplified; a real-world scenario might need to merge these lists
        # For this script, we'll just check if either exists.
        num_entries = len(direct_name_entries)

        if num_entries == 0:
            status = "[❌ MISSING]"
            print(f"  {status} {model_name}")
        elif num_entries > 1:
            status = f"[⚠️ DUPLICATE] ({num_entries} entries)"
            print(f"  {status} {model_name}")
        else:
            status = "[✅ OK]"
            # To reduce noise, comment the line below if you only want to see problems
            # print(f"  {status}      {model_name}")

# --- View Analysis ---
print("\n🖼️ View Definition Status:")
if not all_models:
    print("  - No models found to check.")
else:
    for model_name in sorted(all_models):
        num_files = len(view_models.get(model_name, []))
        if num_files == 0:
            status = "[❌ MISSING]"
            print(f"  {status} {model_name}")
        elif num_files > 1:
            status = f"[⚠️ DUPLICATE]"
            print(f"  {status} {model_name} (found in {', '.join(view_models[model_name])})")
        else:
            status = "[✅ OK]"
            # To reduce noise, comment the line below if you only want to see problems
            # print(f"  {status}      {model_name}")

if report_files:
    print("\n📊 Reports Found:")
    for report_file in sorted(report_files):
        print(f"  - {report_file}")
else:
    print("\nℹ️ No reports found in the 'report/' directory.")

print("\nIntegrity check complete.")
