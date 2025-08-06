#!/usr/bin/env python3
"""
🚀 ULTIMATE BATCH FIELD & ACTION FIXER
=====================================
Combines XML-Python cross-reference validation with intelligent batch processing
to fix ALL missing fields and action methods in 2-3 deployment cycles instead of 50+

This script:
1. Cross-references ALL XML view field references against Python model definitions
2. Cross-references ALL XML action method calls against Python model methods
3. Generates missing fields with intelligent type detection
4. Generates missing action methods with smart implementation patterns
5. Processes in strategic batches to minimize deployment cycles
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
import ast
from pathlib import Path
import json


class UltimateBatchFixer:
    def __init__(self, base_dir="records_management"):
        self.base_dir = Path(base_dir)
        self.models_dir = self.base_dir / "models"
        self.views_dir = self.base_dir / "views"

        # Data structures for analysis
        self.model_fields = {}  # model_name -> set(fields)
        self.model_methods = {}  # model_name -> set(methods)
        self.xml_field_refs = defaultdict(set)  # model_name -> set(field_refs)
        self.xml_action_refs = defaultdict(set)  # model_name -> set(action_refs)
        self.missing_fields = defaultdict(set)
        self.missing_actions = defaultdict(set)

        print("🚀 ULTIMATE BATCH FIELD & ACTION FIXER INITIALIZED")
        print("=" * 60)

    def scan_python_models(self):
        """Extract model definitions and existing fields/methods from Python files"""
        print("📄 Step 1: Scanning Python model files...")

        for model_file in self.models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            try:
                with open(model_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse with AST for accuracy
                tree = ast.parse(content)
                model_name = None
                fields = set()
                methods = set()

                for node in ast.walk(tree):
                    # Find model name
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "_name":
                                if isinstance(node.value, ast.Constant):
                                    model_name = node.value.value
                                elif isinstance(node.value, ast.Str):  # Python < 3.8
                                    model_name = node.value.s

                    # Find field assignments
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                field_name = target.id
                                if isinstance(node.value, ast.Call):
                                    # Check if it's a fields.* call
                                    if isinstance(node.value.func, ast.Attribute):
                                        if (
                                            isinstance(node.value.func.value, ast.Name)
                                            and node.value.func.value.id == "fields"
                                        ):
                                            fields.add(field_name)

                    # Find method definitions
                    if isinstance(node, ast.FunctionDef):
                        methods.add(node.name)

                if model_name:
                    self.model_fields[model_name] = fields
                    self.model_methods[model_name] = methods
                    print(
                        f"   📝 {model_name}: {len(fields)} fields, {len(methods)} methods"
                    )

            except Exception as e:
                print(f"   ❌ Error parsing {model_file}: {e}")

        print(f"✅ Scanned {len(self.model_fields)} models")

    def scan_xml_views(self):
        """Extract field and action references from XML view files"""
        print("\\n🎯 Step 2: Scanning XML view files...")

        for view_file in self.views_dir.glob("*.xml"):
            try:
                tree = ET.parse(view_file)
                root = tree.getroot()

                # Find all view records
                for record in root.findall(".//record[@model='ir.ui.view']"):
                    # Get the model this view is for
                    model_field = record.find(".//field[@name='model']")
                    if model_field is None:
                        continue

                    view_model = model_field.text
                    if not view_model:
                        continue

                    # Find arch field containing the view definition
                    arch_field = record.find(".//field[@name='arch']")
                    if arch_field is None:
                        continue

                    # Convert arch to string for pattern matching
                    arch_content = ET.tostring(arch_field, encoding="unicode")

                    # Extract field references
                    field_patterns = [
                        r'<field\\s+name="([^"]+)"',  # <field name="fieldname"
                        r"domain=.*?\'([^\']*?)\'",  # domain references
                        r'context=.*?"([^"]*?)"',  # context references
                    ]

                    for pattern in field_patterns:
                        matches = re.findall(pattern, arch_content)
                        for match in matches:
                            # Filter out obvious non-field references
                            if not any(
                                skip in match
                                for skip in ["group_by", "search_default", "default_"]
                            ):
                                if (
                                    "." not in match and len(match) < 50
                                ):  # Basic field name
                                    self.xml_field_refs[view_model].add(match)

                    # Extract action method references
                    action_patterns = [
                        r'name="(action_[^"]+)"',  # Button actions
                        r'action="(action_[^"]+)"',  # Action attributes
                    ]

                    for pattern in action_patterns:
                        matches = re.findall(pattern, arch_content)
                        for match in matches:
                            self.xml_action_refs[view_model].add(match)

                print(
                    f"   🎯 {view_file.name}: {sum(len(refs) for refs in self.xml_field_refs.values())} field refs"
                )

            except Exception as e:
                print(f"   ❌ Error parsing {view_file}: {e}")

        print(f"✅ Scanned {len(list(self.views_dir.glob('*.xml')))} XML files")

    def analyze_gaps(self):
        """Compare XML references against Python definitions to find gaps"""
        print("\\n🔍 Step 3: Analyzing gaps...")

        # Find missing fields
        for model, xml_fields in self.xml_field_refs.items():
            if model in self.model_fields:
                python_fields = self.model_fields[model]
                missing = xml_fields - python_fields
                if missing:
                    self.missing_fields[model] = missing
                    print(f"   🔥 {model}: {len(missing)} missing fields")
            else:
                print(f"   ❓ Unknown model: {model}")

        # Find missing action methods
        for model, xml_actions in self.xml_action_refs.items():
            if model in self.model_methods:
                python_methods = self.model_methods[model]
                missing = xml_actions - python_methods
                if missing:
                    self.missing_actions[model] = missing
                    print(f"   🚨 {model}: {len(missing)} missing actions")

        total_missing_fields = sum(
            len(fields) for fields in self.missing_fields.values()
        )
        total_missing_actions = sum(
            len(actions) for actions in self.missing_actions.values()
        )

        print(f"\\n📊 ANALYSIS COMPLETE:")
        print(
            f"   🔥 {total_missing_fields} missing fields across {len(self.missing_fields)} models"
        )
        print(
            f"   🚨 {total_missing_actions} missing actions across {len(self.missing_actions)} models"
        )

        return total_missing_fields, total_missing_actions

    def generate_smart_field_definition(self, field_name, model_name):
        """Generate intelligent field definitions based on field name patterns"""
        field_lower = field_name.lower()

        # Date fields
        if any(
            keyword in field_lower for keyword in ["date", "time", "created", "updated"]
        ):
            if "datetime" in field_lower or "time" in field_lower:
                return f"    {field_name} = fields.Datetime(string='{field_name.replace('_', ' ').title()}', tracking=True)"
            else:
                return f"    {field_name} = fields.Date(string='{field_name.replace('_', ' ').title()}', tracking=True)"

        # Boolean fields
        if any(
            keyword in field_lower
            for keyword in ["is_", "has_", "can_", "active", "enabled", "required"]
        ):
            default_val = "True" if field_name == "active" else "False"
            return f"    {field_name} = fields.Boolean(string='{field_name.replace('_', ' ').title()}', default={default_val})"

        # Many2one relationships
        if field_name.endswith("_id"):
            related_model = field_name[:-3].replace("_", ".")
            if "partner" in field_lower or "customer" in field_lower:
                related_model = "res.partner"
            elif "user" in field_lower:
                related_model = "res.users"
            elif "company" in field_lower:
                related_model = "res.company"

            return f"    {field_name} = fields.Many2one('{related_model}', string='{field_name[:-3].replace('_', ' ').title()}', tracking=True)"

        # One2many relationships
        if field_name.endswith("_ids"):
            related_model = field_name[:-4].replace("_", ".")
            inverse_field = f"{model_name.split('.')[-1]}_id"
            return f"    {field_name} = fields.One2many('{related_model}', '{inverse_field}', string='{field_name[:-4].replace('_', ' ').title()}')"

        # Monetary fields
        if any(
            keyword in field_lower
            for keyword in ["amount", "price", "cost", "rate", "total", "fee"]
        ):
            return f"    {field_name} = fields.Monetary(string='{field_name.replace('_', ' ').title()}', currency_field='currency_id', tracking=True)"

        # Integer fields
        if any(
            keyword in field_lower
            for keyword in ["count", "number", "qty", "quantity", "sequence"]
        ):
            default_val = "10" if "sequence" in field_lower else "0"
            return f"    {field_name} = fields.Integer(string='{field_name.replace('_', ' ').title()}', default={default_val})"

        # Selection fields
        if any(
            keyword in field_lower
            for keyword in ["state", "status", "type", "level", "priority"]
        ):
            return f"    {field_name} = fields.Selection([('draft', 'Draft')], string='{field_name.replace('_', ' ').title()}', default='draft', tracking=True)"

        # Float fields
        if any(keyword in field_lower for keyword in ["weight", "percentage", "ratio"]):
            return f"    {field_name} = fields.Float(string='{field_name.replace('_', ' ').title()}', digits='Stock Weight')"

        # Text fields
        if any(
            keyword in field_lower
            for keyword in ["notes", "description", "comment", "instruction"]
        ):
            return f"    {field_name} = fields.Text(string='{field_name.replace('_', ' ').title()}')"

        # Default: Char field
        return f"    {field_name} = fields.Char(string='{field_name.replace('_', ' ').title()}', tracking=True)"

    def generate_smart_action_method(self, method_name, model_name):
        """Generate intelligent action method implementations"""
        method_display = method_name.replace("_", " ").replace("action ", "").title()

        # View actions
        if "view" in method_name:
            related_model = model_name  # Default to same model
            if "documents" in method_name:
                related_model = "records.document"
            elif "containers" in method_name:
                related_model = "records.container"
            elif "invoices" in method_name:
                related_model = "account.move"

            return f'''    def {method_name}(self):
        """{method_display} - View related records"""
        self.ensure_one()
        return {{
            "type": "ir.actions.act_window",
            "name": _("{method_display}"),
            "res_model": "{related_model}",
            "view_mode": "tree,form",
            "domain": [("{model_name.split('.')[-1]}_id", "=", self.id)],
            "context": {{"default_{model_name.split('.')[-1]}_id": self.id}},
        }}'''

        # Report actions
        if any(
            word in method_name
            for word in ["report", "generate", "print", "certificate"]
        ):
            return f'''    def {method_name}(self):
        """{method_display} - Generate report"""
        self.ensure_one()
        return {{
            "type": "ir.actions.report",
            "report_name": "records_management.{method_name}_template",
            "report_type": "qweb-pdf",
            "data": {{"ids": [self.id]}},
            "context": self.env.context,
        }}'''

        # State change actions
        if any(
            word in method_name
            for word in ["confirm", "approve", "complete", "start", "cancel"]
        ):
            new_state = (
                "confirmed" if "confirm" in method_name else method_name.split("_")[-1]
            )
            return f'''    def {method_name}(self):
        """{method_display} - Change state"""
        self.ensure_one()
        self.write({{"state": "{new_state}"}})
        self.message_post(body=_("{method_display} completed"))
        return True'''

        # Mark/toggle actions
        if method_name.startswith("action_mark_") or method_name.startswith(
            "action_toggle_"
        ):
            field_to_set = method_name.replace("action_mark_", "").replace(
                "action_toggle_", ""
            )
            return f'''    def {method_name}(self):
        """{method_display} - Update field"""
        self.ensure_one()
        self.write({{"{field_to_set}": True}})
        self.message_post(body=_("{method_display}"))
        return True'''

        # Generic action
        return f'''    def {method_name}(self):
        """{method_display} - Action method"""
        self.ensure_one()
        return {{
            "type": "ir.actions.act_window",
            "name": _("{method_display}"),
            "res_model": "{model_name}",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }}'''

    def create_batch_fixes(self, batch_size=5):
        """Create strategic batches of fixes to minimize deployment cycles"""
        print("\\n🔧 Step 4: Creating strategic fix batches...")

        # Prioritize models by impact (most referenced models first)
        model_priority = Counter()
        for model, fields in self.missing_fields.items():
            model_priority[model] += len(fields) * 2  # Fields are critical
        for model, actions in self.missing_actions.items():
            model_priority[model] += len(actions) * 1  # Actions are important

        # Create batches
        batches = []
        models_to_process = list(model_priority.keys())

        for i in range(0, len(models_to_process), batch_size):
            batch_models = models_to_process[i : i + batch_size]
            batches.append(batch_models)

        print(f"📦 Created {len(batches)} strategic batches:")
        for i, batch in enumerate(batches, 1):
            total_fixes = sum(
                len(self.missing_fields.get(m, []))
                + len(self.missing_actions.get(m, []))
                for m in batch
            )
            print(f"   Batch {i}: {batch} ({total_fixes} total fixes)")

        return batches

    def apply_batch_fixes(self, batch_models, batch_num):
        """Apply fixes for a batch of models"""
        print(f"\\n🛠️  Applying Batch {batch_num} fixes...")

        for model_name in batch_models:
            model_file = None

            # Find the model file
            for py_file in self.models_dir.glob("*.py"):
                try:
                    with open(py_file, "r") as f:
                        content = f.read()
                        if (
                            f"_name = '{model_name}'" in content
                            or f'_name = "{model_name}"' in content
                        ):
                            model_file = py_file
                            break
                except:
                    continue

            if not model_file:
                print(f"   ❌ Could not find model file for {model_name}")
                continue

            # Read current file content
            with open(model_file, "r") as f:
                content = f.read()

            additions = []

            # Add missing fields
            if model_name in self.missing_fields:
                fields_to_add = self.missing_fields[model_name]
                additions.append(
                    "\\n    # ============================================================================"
                )
                additions.append(f"    # AUTO-GENERATED FIELDS (Batch {batch_num})")
                additions.append(
                    "    # ============================================================================"
                )

                for field_name in sorted(fields_to_add):
                    field_def = self.generate_smart_field_definition(
                        field_name, model_name
                    )
                    additions.append(field_def)

                print(f"   ✅ {model_name}: Added {len(fields_to_add)} fields")

            # Add missing action methods
            if model_name in self.missing_actions:
                actions_to_add = self.missing_actions[model_name]
                additions.append(
                    "\\n    # ============================================================================"
                )
                additions.append(
                    f"    # AUTO-GENERATED ACTION METHODS (Batch {batch_num})"
                )
                additions.append(
                    "    # ============================================================================"
                )

                for method_name in sorted(actions_to_add):
                    method_def = self.generate_smart_action_method(
                        method_name, model_name
                    )
                    additions.append(method_def)

                print(f"   ✅ {model_name}: Added {len(actions_to_add)} action methods")

            # Insert additions before the last class closing or at end
            if additions:
                insertion_point = content.rfind("\\n")  # End of file
                if insertion_point == -1:
                    insertion_point = len(content)

                new_content = (
                    content[:insertion_point]
                    + "\\n".join(additions)
                    + content[insertion_point:]
                )

                # Write back to file
                with open(model_file, "w") as f:
                    f.write(new_content)

    def run_comprehensive_fix(self):
        """Execute the complete batch fixing process"""
        try:
            # Step 1: Scan existing code
            self.scan_python_models()

            # Step 2: Scan XML references
            self.scan_xml_views()

            # Step 3: Analyze gaps
            total_fields, total_actions = self.analyze_gaps()

            if total_fields == 0 and total_actions == 0:
                print(
                    "\\n🎉 NO GAPS FOUND! All XML references have corresponding Python definitions."
                )
                return True

            # Step 4: Create strategic batches
            batches = self.create_batch_fixes()

            # Step 5: Apply first batch (most critical)
            if batches:
                self.apply_batch_fixes(batches[0], 1)

                print(f"\\n🚀 BATCH 1 COMPLETE!")
                print(f"✅ Fixed critical issues in {len(batches[0])} models")
                print(
                    f"📦 {len(batches)-1} more batches ready for subsequent deployments"
                )
                print("\\n🎯 NEXT STEPS:")
                print("1. Commit and push these changes")
                print("2. Wait for Odoo.sh deployment (10-15 min)")
                print("3. Check for errors, then run next batch")

                return False  # More batches needed

            return True  # All complete

        except Exception as e:
            print(f"❌ Error during comprehensive fix: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Main execution function"""
    print("🚀 ULTIMATE BATCH FIELD & ACTION FIXER")
    print("=" * 60)
    print("🎯 Goal: Fix ALL missing fields and actions in 2-3 deployment cycles")
    print("⏰ Save: 40+ hours of 10-15 minute rebuild cycles")
    print("=" * 60)

    # Change to correct directory
    if os.path.exists("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"):
        os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")

    fixer = UltimateBatchFixer()
    success = fixer.run_comprehensive_fix()

    if success:
        print("\\n🎉 ALL FIXES COMPLETE!")
    else:
        print("\\n📦 BATCH 1 APPLIED - Ready for deployment!")

    return success


if __name__ == "__main__":
    main()
