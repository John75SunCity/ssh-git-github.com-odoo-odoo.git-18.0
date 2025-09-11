import os
import re
import ast
import xml.etree.ElementTree as ET

# --- Configuration ---
MODULE_PATH = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
MODELS_DIR = os.path.join(MODULE_PATH, 'models')
VIEWS_DIR = os.path.join(MODULE_PATH, 'views')
REPORT_DIR = os.path.join(MODULE_PATH, 'report')
SECURITY_DIR = os.path.join(MODULE_PATH, 'security')

# --- Odoo / External Dependencies ---
# Expanded list of known models and standard fields to reduce false positives.
KNOWN_EXTERNAL_MODELS = {
    'product.product', 'product.template', 'product.category', 'uom.uom',
    'account.move', 'account.move.line', 'account.payment.term', 'account.fiscal.position', 'account.payment', 'account.journal',
    'stock.picking', 'stock.lot', 'stock.move', 'stock.location',
    'project.task', 'project.project',
    'fsm.order', 'fsm.task', 'fsm.pickup.request',
    'hr.employee', 'hr.department',
    'survey.survey',
    'mail.thread', 'mail.activity.mixin', 'mail.template',
    'maintenance.equipment', 'maintenance.team', 'maintenance.request',
    'point_of_sale', 'pos.config',
    'quality.point', 'quality.check',
    'res.partner', 'res.users', 'res.company', 'res.config.settings', 'res.currency',
    'crm.team',
    'fleet.vehicle',
    'ir.actions.report', 'ir.ui.view', 'ir.model.data', 'ir.model.fields', 'ir.model',
    # Models that seem to be part of this module but might be missed by initial scan
    'naid.custody', 'billing.period', 'document.retrieval.work.order', 'records.service.type',
    'records.approval.request', 'records.tag.category', 'naid.compliance', 'container.access.report',
    'records.destruction.certificate', 'assigned.user', 'revenue.analytic.config', 'records.bin.key',
    'document.type', 'records.bin', 'work.order', 'billing.service', 'customer.inventory.report',
    'records.inventory', 'destruction.request', 'records.work.order', 'report.template',
}

STANDARD_ODOO_FIELDS = {
    'id', 'name', 'display_name', 'create_date', 'create_uid', 'write_date', 'write_uid',
    'activity_ids', 'message_follower_ids', 'message_ids', '__last_update', 'active',
    'message_partner_ids', 'message_channel_ids', 'message_main_attachment_id',
    # Add more as needed
}

# --- Data Structures ---
models_data = {}  # { 'model.name': {'fields': {'field_name': {'related': '...', 'comodel': '...'}}, 'file': 'path/to/file.py'} }
potential_errors = []

# --- Utility Functions ---

def get_files_by_extension(directory, extension):
    """Get all files with a given extension in a directory."""
    found_files = []
    if not os.path.isdir(directory):
        return []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                found_files.append(os.path.join(root, file))
    return found_files

# New: Function to check full related chain validity
def validate_related_chain(model_name, related_chain, source_file):
    current_model = model_name
    for part in related_chain[:-1]:
        if current_model not in models_data or part not in models_data[current_model]['fields']:
            return False
        field_info = models_data[current_model]['fields'][part]
        current_model = field_info.get('comodel')
        if not current_model or (current_model not in models_data and current_model not in KNOWN_EXTERNAL_MODELS):
            return False
    target_field = related_chain[-1]
    if current_model in models_data:
        return target_field in models_data[current_model]['fields'] or target_field in STANDARD_ODOO_FIELDS
    return current_model in KNOWN_EXTERNAL_MODELS

# --- Analysis Core ---

def analyze_py_models():
    """
    Scan all python files in models directory to extract model names and their fields using AST.
    This now captures more detail about fields, like comodel_name for relational fields.
    Enhanced to scan compute methods for field accesses.
    """
    print("1. Analyzing Python models...")
    py_files = get_files_by_extension(MODELS_DIR, '.py')

    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        model_name = None
                        for class_node in node.body:
                            if isinstance(class_node, ast.Assign) and len(class_node.targets) == 1 and isinstance(class_node.targets[0], ast.Name) and class_node.targets[0].id == '_name':
                                if isinstance(class_node.value, ast.Str):
                                    model_name = class_node.value.s
                                    break

                        if model_name:
                            if model_name not in models_data:
                                models_data[model_name] = {'fields': {}, 'file': file_path}

                            for class_node in node.body:
                                if isinstance(class_node, ast.Assign) and len(class_node.targets) == 1 and isinstance(class_node.targets[0], ast.Name):
                                    field_name = class_node.targets[0].id
                                    if isinstance(class_node.value, ast.Call) and hasattr(class_node.value, 'func') and isinstance(class_node.value.func, ast.Attribute) and hasattr(class_node.value.func.value, 'id') and class_node.value.func.value.id == 'fields':
                                        field_info = {'related': None, 'comodel': None, 'type': class_node.value.func.attr}
                                        for kw in class_node.value.keywords:
                                            if kw.arg == 'related' and isinstance(kw.value, ast.Str):
                                                field_info['related'] = kw.value.s
                                            if kw.arg == 'comodel_name' and isinstance(kw.value, ast.Str):
                                                field_info['comodel'] = kw.value.s
                                        models_data[model_name]['fields'][field_name] = field_info

                            # New: Scan methods for potential field accesses
                            for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                                for stmt in ast.walk(method):
                                    if isinstance(stmt, ast.Attribute) and isinstance(stmt.value, ast.Name) and stmt.value.id == 'self' and isinstance(stmt.attr, str):
                                        field_name = stmt.attr
                                        if field_name not in models_data[model_name]['fields'] and field_name not in STANDARD_ODOO_FIELDS:
                                            potential_errors.append(
                                                f"Potential KeyError in method '{method.name}' of model '{model_name}': Access to undefined field '{field_name}'. File: {os.path.basename(file_path)}"
                                            )
        except Exception as e:
            potential_errors.append(f"Could not parse Python file: {file_path} - {e}")
    print(f"   Found {len(models_data)} models.")


def analyze_xml_files():
    """
    Scan all XML files to find field usages and check them against the Python models.
    Enhanced to handle full related chains, better false positive exclusion, and additional XML types (security, actions).
    """
    print("2. Analyzing XML views, reports, security, and actions...")
    xml_files = get_files_by_extension(VIEWS_DIR, '.xml') + get_files_by_extension(REPORT_DIR, '.xml') + get_files_by_extension(SECURITY_DIR, '.xml') + get_files_by_extension(MODULE_PATH, '.xml')  # Broaden to all XML

    non_field_name_patterns = re.compile(r'(t-name|name\s*=\s*["\'](?:template|action|menu|report|group|inherit_id|model|arch|field|filter|button|label|page|group|expr|position|attribute|value|domain|context|eval|invisible|readonly|required|options|class|style|attrs|groups|states|kanban_default|decoration-\w+)|^\d|computed_|t-.*)')

    for file_path in xml_files:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Create a parent map to allow finding parent elements, which is not standard in ElementTree
            parent_map = {c: p for p in root.iter() for c in p}

            for elem in tree.iter():
                if 'name' in elem.attrib:
                    field_name = elem.attrib['name']
                    if non_field_name_patterns.search(field_name) or elem.tag not in ['field', 'filter', 'groupby']:  # Stricter tag filter
                        continue  # Exclude false positives

                    base_field_name = field_name.split('.')[0]
                    related_chain = field_name.split('.')

                    # Find associated model (improved detection using parent_map)
                    model = None
                    parent = parent_map.get(elem)
                    if elem.tag == 'record' and elem.get('model'):
                        model = elem.get('model')
                    elif parent is not None and parent.get('model'):
                        model = parent.get('model')
                    else:
                        # Fallback for views where model is defined in a field
                        view_model_elem = tree.find(".//field[@name='model']")
                        if view_model_elem is not None and view_model_elem.text:
                            model = view_model_elem.text

                    if not model or model not in models_data:
                        continue

                    defined_fields = set(models_data[model]['fields'].keys()) | STANDARD_ODOO_FIELDS

                    if base_field_name not in defined_fields:
                        potential_errors.append(
                            f"KeyError risk: Field '{field_name}' (base '{base_field_name}') not defined in model '{model}'. File: {os.path.basename(file_path)}, Tag: {elem.tag}"
                        )
                    elif related_chain and not validate_related_chain(model, related_chain, file_path):
                        potential_errors.append(
                            f"KeyError risk in related chain '{field_name}' for model '{model}'. File: {os.path.basename(file_path)}"
                        )
        except ET.ParseError as e:
            potential_errors.append(f"Could not parse XML file: {file_path} - {e}")
        except Exception as e:
            potential_errors.append(f"Error processing XML file: {file_path} - {e}")

def analyze_relational_fields():
    """
    Scan python models for Many2one fields and check if the comodel exists.
    Also analyzes server-side related fields for potential KeyErrors, paying special
    attention to load-order dependencies. Enhanced to handle abstract models.
    """
    print("3. Analyzing relational and related fields (with load order checks)...")

    for model_name, data in models_data.items():
        for field_name, field_info in data['fields'].items():
            # Check Many2one comodel existence (enhanced for abstract)
            if field_info.get('comodel'):
                comodel_name = field_info['comodel']
                if comodel_name not in models_data and comodel_name not in KNOWN_EXTERNAL_MODELS and not re.match(r'abstract\.', comodel_name):
                    potential_errors.append(
                        f"KeyError risk in Model: Field '{field_name}' in model '{model_name}' "
                        f"has a Many2one relation to an unrecognized model '{comodel_name}'. "
                        f"File: {os.path.basename(data['file'])}"
                    )

            # Check related fields for load-order issues (use validate_related_chain)
            if field_info.get('related'):
                related_chain = field_info['related'].split('.')
                if not related_chain or len(related_chain) < 2:
                    continue
                if not validate_related_chain(model_name, related_chain, data['file']):
                    target_field_name = related_chain[-1]
                    current_model_name = field_info.get('comodel')  # Simplified; full logic in validate
                    if current_model_name and current_model_name in models_data:
                        source_file = os.path.basename(data['file'])
                        target_file = os.path.basename(models_data[current_model_name]['file'])
                        error_msg = (
                            f"HIGH RISK KeyError (Load Order Dependent): Field '{field_name}' in model '{model_name}' (file: {source_file}) "
                            f"is related to '{field_info['related']}', but the target field '{target_field_name}' was NOT found in the related model '{current_model_name}' (file: {target_file}).\n"
                            f"  ▶ LIKELY CAUSE: Odoo is loading '{source_file}' before it has fully loaded '{target_file}'.\n"
                            f"  ▶ SOLUTION: 1. Ensure '{target_field_name}' is defined in the '{current_model_name}' class in '{target_file}'.\n"
                            f"              2. Move the definition of '{target_field_name}' to the top of its class.\n"
                            f"              3. Check `models/__init__.py` to ensure '{target_file}' is imported before '{source_file}'."
                        )
                        potential_errors.append(error_msg)
                    elif current_model_name not in KNOWN_EXTERNAL_MODELS:
                        potential_errors.append(
                            f"Unknown Related Model: Field '{field_name}' in model '{model_name}' relates to model '{current_model_name}', "
                            f"which is not defined in this module or in KNOWN_EXTERNAL_MODELS. "
                            f"File: {os.path.basename(data['file'])}"
                        )

# --- Main Execution ---

if __name__ == "__main__":
    print("Starting Records Management Module Integrity Analysis...")
    print("="*50)

    analyze_py_models()
    analyze_xml_files()
    analyze_relational_fields()

    print("\n" + "="*50)
    print("Analysis Complete. Potential Issues Found:")
    print("="*50)

    if potential_errors:
        # Sort errors to show high-risk ones first
        potential_errors.sort(key=lambda x: "HIGH RISK" not in x)
        for i, error in enumerate(potential_errors, 1):
            print(f"{i}. {error}\n")
    else:
        print("🎉 No obvious causes of KeyError found in models, views, or relational fields.")

    print(f"\nScan Summary:")
    print(f"- Models Analyzed: {len(models_data)}")
    print(f"- Potential Issues Detected: {len(potential_errors)}")
    print("="*50)
    print("Note: This is a static analysis and may not catch all runtime KeyErrors, but it now checks related fields.")
