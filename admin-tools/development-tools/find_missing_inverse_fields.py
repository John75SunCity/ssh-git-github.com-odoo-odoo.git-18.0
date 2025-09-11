import os
import ast
import sys

# Directory to scan
MODELS_DIR = 'records_management/models'

class ModelVisitor(ast.NodeVisitor):
    def __init__(self):
        self.models = {}
        self.current_model = None
        self.one2many_fields = []
        self.all_fields = {}

    def visit_ClassDef(self, node):
        # In Odoo, models can inherit from 'models.Model'
        is_odoo_model = False
        for base in node.bases:
            if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) and base.value.id == 'models' and base.attr == 'Model':
                is_odoo_model = True
                break
            if isinstance(base, ast.Name) and base.id == 'Model': # Simpler inheritance
                is_odoo_model = True
                break

        if is_odoo_model:
            self.current_model = None
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name) and target.id == '_name':
                        if isinstance(stmt.value, ast.Str):
                            self.current_model = stmt.value.s
                            if self.current_model not in self.models:
                                self.models[self.current_model] = []
                                self.all_fields[self.current_model] = set()
            if self.current_model:
                self.generic_visit(node)

    def visit_Assign(self, node):
        if self.current_model:
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                field_name = node.targets[0].id
                # Add all assigned names as fields
                self.all_fields[self.current_model].add(field_name)

                if isinstance(node.value, ast.Call) and hasattr(node.value.func, 'attr') and node.value.func.attr == 'One2many':
                    comodel = None
                    inverse_name = None

                    # Arguments can be positional or keyword
                    if len(node.value.args) > 0 and isinstance(node.value.args[0], ast.Str):
                        comodel = node.value.args[0].s
                    if len(node.value.args) > 1 and isinstance(node.value.args[1], ast.Str):
                        inverse_name = node.value.args[1].s

                    for kw in node.value.keywords:
                        if kw.arg == 'comodel_name' and isinstance(kw.value, ast.Str):
                            comodel = kw.value.s
                        elif kw.arg == 'inverse_name' and isinstance(kw.value, ast.Str):
                            inverse_name = kw.value.s

                    if comodel and inverse_name:
                        self.one2many_fields.append({
                            'source_model': self.current_model,
                            'field_name': field_name,
                            'comodel': comodel,
                            'inverse_name': inverse_name,
                            'file_path': self.current_file
                        })

            self.generic_visit(node)

def scan_models(directory):
    visitor = ModelVisitor()
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(root, filename)
                visitor.current_file = filepath
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=filepath)
                        visitor.visit(tree)
                    except SyntaxError as e:
                        print(f"Could not parse {filepath}: {e}", file=sys.stderr)
    return visitor.one2many_fields, visitor.all_fields

def find_missing_inverses(one2many_fields, all_fields):
    missing = []
    for o2m in one2many_fields:
        comodel = o2m['comodel']
        inverse_name = o2m['inverse_name']
        if comodel in all_fields:
            if inverse_name not in all_fields[comodel]:
                missing.append({
                    'one2many_model': o2m['source_model'],
                    'one2many_field': o2m['field_name'],
                    'missing_in_model': comodel,
                    'missing_field': inverse_name,
                    'file_path': o2m['file_path']
                })
        else:
            # This case handles when the target model is not in the scanned files
            # (e.g., it's a built-in Odoo model or in another module)
            # We can't confirm or deny the field exists, so we could flag it as a warning.
            pass
    return missing

def generate_report(missing):
    if not missing:
        print("✅ No missing inverse fields found within the scanned module.")
        return

    print("="*80)
    print("🔥 MISSING INVERSE FIELDS REPORT 🔥")
    print("="*80)
    print("The following One2many fields are missing their corresponding Many2one inverse field.")
    print("This will cause a 'KeyError' during module installation.\n")

    for item in missing:
        print(f"🔴 ERROR in Model: '{item['one2many_model']}' (File: {item['file_path']})")
        print(f"  - Field:          '{item['one2many_field']}'")
        print(f"  - Problem:        Requires a Many2one field named '{item['missing_field']}' to exist on the '{item['missing_in_model']}' model, but it was not found.")
        print(f"  - To Fix:         Add the field `'{item['missing_field']}' = fields.Many2one('{item['one2many_model']}')` to the model definition for '{item['missing_in_model']}'.")
        print("-"*80)

if __name__ == "__main__":
    if not os.path.isdir(MODELS_DIR):
        print(f"Error: Directory not found at '{MODELS_DIR}'. Please run this script from the Odoo root directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning for models in: {os.path.abspath(MODELS_DIR)}...\n")
    one2many_fields, all_fields = scan_models(MODELS_DIR)
    missing = find_missing_inverses(one2many_fields, all_fields)
    generate_report(missing)
