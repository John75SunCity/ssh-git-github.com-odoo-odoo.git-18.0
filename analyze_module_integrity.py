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
# A list of known models from other modules (stock, account, etc.) to prevent false positives.
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

# --- Analysis Core ---

def analyze_py_models():
    """
    Scan all python files in models directory to extract model names and their fields using AST.
    This now captures more detail about fields, like comodel_name for relational fields.
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
                        # First, find the _name attribute to identify the model
                        for class_node in node.body:
                            if isinstance(class_node, ast.Assign) and len(class_node.targets) == 1 and isinstance(class_node.targets[0], ast.Name) and class_node.targets[0].id == '_name':
                                if isinstance(class_node.value, ast.Str):
                                    model_name = class_node.value.s
                                    break

                        if model_name:
                            if model_name not in models_data:
                                models_data[model_name] = {'fields': {}, 'file': file_path}

                            # Now, iterate again to get field definitions
                            for class_node in node.body:
                                if isinstance(class_node, ast.Assign) and len(class_node.targets) == 1 and isinstance(class_node.targets[0], ast.Name):
                                    field_name = class_node.targets[0].id
                                    # Ensure it's a field definition
                                    if isinstance(class_node.value, ast.Call) and hasattr(class_node.value, 'func') and isinstance(class_node.value.func, ast.Attribute) and hasattr(class_node.value.func.value, 'id') and class_node.value.func.value.id == 'fields':
                                        field_info = {'related': None, 'comodel': None}

                                        # Extract 'related' and 'comodel_name' from keywords
                                        for kw in class_node.value.keywords:
                                            if kw.arg == 'related' and isinstance(kw.value, ast.Str):
                                                field_info['related'] = kw.value.s
                                            if kw.arg == 'comodel_name' and isinstance(kw.value, ast.Str):
                                                field_info['comodel'] = kw.value.s

                                        models_data[model_name]['fields'][field_name] = field_info
        except Exception as e:
            potential_errors.append(f"Could not parse Python file: {file_path} - {e}")
    print(f"   Found {len(models_data)} models.")


def analyze_xml_files():
    """
    Scan all XML files to find field usages and check them against the Python models.
    This version is more robust and understands the structure of Odoo XML.
    """
    print("2. Analyzing XML views and reports...")
    xml_files = get_files_by_extension(VIEWS_DIR, '.xml') + get_files_by_extension(REPORT_DIR, '.xml')

    for file_path in xml_files:
        try:
            tree = ET.parse(file_path)
            for record in tree.findall(".//record"):
                record_model = record.get('model')

                # We only care about views for field validation
                if record_model == 'ir.ui.view':
                    model_field = record.find("./field[@name='model']")
                    if model_field is None or not model_field.text:
                        continue

                    target_model_name = model_field.text
                    if target_model_name not in models_data:
                        # This could be a view for a model in another module, which is valid.
                        continue

                    # Get all fields defined for the model, including standard Odoo fields
                    defined_fields = set(models_data[target_model_name]['fields'].keys())
                    defined_fields.update(['id', 'name', 'display_name', 'create_date', 'create_uid', 'write_date', 'write_uid', 'activity_ids', 'message_follower_ids', 'message_ids', '__last_update'])

                    arch_field = record.find("./field[@name='arch']")
                    if arch_field is not None and arch_field.text:
                        try:
                            # The arch is XML content itself
                            arch_tree = ET.fromstring(arch_field.text)
                            for field_node in arch_tree.findall(".//*[@name]"):
                                field_name = field_node.get('name')
                                # Odoo views can have dot notation for related fields (e.g., 'partner_id.name')
                                # We only check the base field.
                                base_field_name = field_name.split('.')[0]

                                if base_field_name not in defined_fields:
                                    # Filter out elements that use 'name' for non-field purposes
                                    if field_node.tag in ['field', 'filter', 'group', 'page', 'button', 'label']:
                                        potential_errors.append(
                                            f"KeyError risk in View: Field '{field_name}' used in '{os.path.basename(file_path)}' "
                                            f"but base field '{base_field_name}' not found in model '{target_model_name}'. Record ID: {record.get('id')}"
                                        )
                        except ET.ParseError:
                            # The 'arch' field can sometimes contain template logic (t-name, etc.) which isn't valid XML.
                            # We can ignore these parsing errors as they are not relevant to field definitions.
                            pass
        except ET.ParseError as e:
            potential_errors.append(f"Could not parse XML file: {file_path} - {e}")
        except Exception as e:
            potential_errors.append(f"Error processing XML file: {file_path} - {e}")

def analyze_relational_fields():
    """
    Scan python models for Many2one fields and check if the comodel exists.
    Also analyzes server-side related fields for potential KeyErrors.
    """
    print("3. Analyzing relational and related fields...")

    for model_name, data in models_data.items():
        for field_name, field_info in data['fields'].items():
            # Check Many2one comodel existence
            if field_info.get('comodel'):
                comodel_name = field_info['comodel']
                if comodel_name not in models_data and comodel_name not in KNOWN_EXTERNAL_MODELS:
                    potential_errors.append(
                        f"KeyError risk in Model: Field '{field_name}' in model '{model_name}' "
                        f"has a Many2one relation to an unrecognized model '{comodel_name}'. "
                        f"File: {os.path.basename(data['file'])}"
                    )

            # Check related fields
            if field_info.get('related'):
                related_chain = field_info['related'].split('.')
                if not related_chain or len(related_chain) < 2:
                    continue

                # Find the comodel of the base field
                current_model_name = model_name
                for i, chain_part in enumerate(related_chain[:-1]):
                    if current_model_name not in models_data or chain_part not in models_data[current_model_name]['fields']:
                        potential_errors.append(
                            f"Broken Related Chain: In model '{model_name}', field '{field_name}' has a related chain '{field_info['related']}' "
                            f"where intermediate field '{chain_part}' could not be found in model '{current_model_name}'. "
                            f"File: {os.path.basename(data['file'])}"
                        )
                        current_model_name = None
                        break

                    base_field_info = models_data[current_model_name]['fields'][chain_part]
                    current_model_name = base_field_info.get('comodel')

                    if not current_model_name:
                        # If comodel is not explicit, the base field must be a Many2one to another model.
                        # This static analysis can't easily determine that, so we stop here for this chain.
                        # A more advanced version could parse the field type (e.g., fields.Many2one(...))
                        potential_errors.append(
                            f"Info: Could not determine comodel for '{chain_part}' in related chain '{field_info['related']}' "
                            f"in model '{model_name}'. Manual check required. File: {os.path.basename(data['file'])}"
                        )
                        current_model_name = None # Stop processing this chain
                        break

                if current_model_name:
                    # Now check the final part of the chain
                    target_field_name = related_chain[-1]
                    if current_model_name in models_data:
                        if target_field_name not in models_data[current_model_name]['fields']:
                            potential_errors.append(
                                f"HIGH RISK KeyError: Field '{field_name}' in model '{model_name}' is related to '{field_info['related']}', "
                                f"but the target field '{target_field_name}' was NOT found in the related model '{current_model_name}'. "
                                f"File: {os.path.basename(data['file'])}"
                            )
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
