#!/usr/bin/env python3
"""
Comprehensive Relationship Auditor + File Optimizer for Odoo Records Management
Finds and fixes all One2many/Many2one relationship issues while simultaneously optimizing files
"""
import os
import re
import glob
import json
from collections import defaultdict


class RelationshipAuditorOptimizer:
    def __init__(self, base_path):
        self.base_path = base_path
        self.models_path = os.path.join(base_path, "records_management", "models")
        self.views_path = os.path.join(base_path, "records_management", "views")
        self.all_models = {}
        self.all_fields = {}
        self.xml_field_references = {}
        self.xml_model_references = {}
        self.missing_xml_fields = []
        self.unused_model_fields = []
        self.relationship_issues = []
        self.fixes_applied = []
        self.optimization_stats = {}
        self.files_to_optimize = set()
        self.xml_files_to_optimize = set()

    def scan_all_models(self):
        """Scan all Python model files to build complete field inventory"""
        print("🔍 Scanning all model files...")

        py_files = glob.glob(os.path.join(self.models_path, "*.py"))

        for py_file in py_files:
            if py_file.endswith("__init__.py"):
                continue

            # Track files for potential optimization
            file_size = os.path.getsize(py_file)
            line_count = self.count_lines(py_file)

            if line_count > 400:  # Files over 400 lines are optimization candidates
                self.files_to_optimize.add(py_file)

            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract model names
            model_matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)

            for model_name in model_matches:
                self.all_models[model_name] = {
                    "file": py_file,
                    "fields": {},
                    "line_count": line_count,
                    "file_size": file_size,
                }

                # Extract all fields for this model
                field_matches = re.findall(
                    r"(\w+)\s*=\s*fields\.(Many2one|One2many|Many2many)\s*\([^)]+\)",
                    content,
                )

                for field_name, field_type in field_matches:
                    self.all_models[model_name]["fields"][field_name] = field_type

                # Also extract regular fields that might be inverse targets
                regular_fields = re.findall(r"(\w+)\s*=\s*fields\.\w+", content)
                for field_name in regular_fields:
                    if field_name not in self.all_models[model_name]["fields"]:
                        self.all_models[model_name]["fields"][field_name] = "regular"

        print(f"✅ Found {len(self.all_models)} models")
        print(f"📊 {len(self.files_to_optimize)} files are candidates for optimization")
        return self.all_models

    def scan_all_xml_views(self):
        """Scan all XML view files to find field and model references"""
        print("🔍 Scanning XML view files...")

        xml_files = glob.glob(os.path.join(self.views_path, "*.xml"))

        for xml_file in xml_files:
            # Track XML files for potential optimization
            file_size = os.path.getsize(xml_file)
            line_count = self.count_lines(xml_file)

            if line_count > 300:  # XML files over 300 lines are optimization candidates
                self.xml_files_to_optimize.add(xml_file)

            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.read()

            xml_filename = os.path.basename(xml_file)
            self.xml_field_references[xml_filename] = {
                "fields": set(),
                "models": set(),
                "line_count": line_count,
                "file_size": file_size,
            }

            # Find field references in XML
            field_patterns = [
                r'name=["\']([^"\']+)["\']',  # Basic field references
                r'field="([^"\']+)"',  # Explicit field attributes
                r'<field[^>]+name=["\']([^"\']+)["\']',  # Field elements
                r'domain=.*?\(["\']([^"\']+)["\']',  # Domain field references
                r'context=.*?["\']([^"\']+)["\']',  # Context field references
            ]

            for pattern in field_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Filter out obvious non-field names
                    if (
                        not match.startswith("ir.")
                        and not match.startswith("base.")
                        and not match.startswith("view_")
                        and not match.endswith("_view")
                        and "_" in match
                        or match.islower()
                    ):
                        self.xml_field_references[xml_filename]["fields"].add(match)

            # Find model references in XML
            model_patterns = [
                r'model=["\']([^"\']+)["\']',
                r'res_model=["\']([^"\']+)["\']',
                r'<record[^>]+model=["\']([^"\']+)["\']',
            ]

            for pattern in model_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith(("records.", "customer.", "portal.", "naid.")):
                        self.xml_field_references[xml_filename]["models"].add(match)

        total_xml_fields = sum(
            len(data["fields"]) for data in self.xml_field_references.values()
        )
        total_xml_models = sum(
            len(data["models"]) for data in self.xml_field_references.values()
        )

        print(f"✅ Scanned {len(xml_files)} XML files")
        print(
            f"📊 Found {total_xml_fields} field references, {total_xml_models} model references"
        )
        print(
            f"🔧 {len(self.xml_files_to_optimize)} XML files are candidates for optimization"
        )

        return self.xml_field_references

    def cross_reference_xml_model_fields(self):
        """Cross-reference XML field usage with model definitions"""
        print("🔍 Cross-referencing XML fields with model definitions...")

        # Find fields referenced in XML but missing from models
        for xml_file, xml_data in self.xml_field_references.items():
            for model_name in xml_data["models"]:
                if model_name in self.all_models:
                    model_fields = set(self.all_models[model_name]["fields"].keys())
                    xml_fields = xml_data["fields"]

                    # Find fields in XML but not in model
                    missing_fields = xml_fields - model_fields
                    for field in missing_fields:
                        # Filter out common non-field references
                        if (
                            field
                            not in ["id", "create_date", "write_date", "__last_update"]
                            and not field.startswith("action_")
                            and not field.endswith("_view")
                        ):
                            self.missing_xml_fields.append(
                                {
                                    "xml_file": xml_file,
                                    "model": model_name,
                                    "field": field,
                                    "type": "field_in_xml_missing_in_model",
                                }
                            )

        # Find fields in models but never used in XML
        all_xml_fields = set()
        for xml_data in self.xml_field_references.values():
            all_xml_fields.update(xml_data["fields"])

        for model_name, model_data in self.all_models.items():
            for field_name, field_type in model_data["fields"].items():
                if (
                    field_name not in all_xml_fields
                    and field_name
                    not in [
                        "id",
                        "create_date",
                        "write_date",
                        "display_name",
                        "activity_ids",
                        "message_ids",
                        "message_follower_ids",
                    ]
                    and not field_name.startswith("_")
                ):
                    self.unused_model_fields.append(
                        {
                            "model": model_name,
                            "field": field_name,
                            "field_type": field_type,
                            "file": model_data["file"],
                            "type": "field_in_model_unused_in_xml",
                        }
                    )

        print(
            f"⚠️  Found {len(self.missing_xml_fields)} fields referenced in XML but missing from models"
        )
        print(
            f"📊 Found {len(self.unused_model_fields)} model fields not used in any XML views"
        )

        return self.missing_xml_fields, self.unused_model_fields

    def optimize_xml_file(self, file_path, content):
        """Optimize XML file structure"""
        lines = content.split("\n")
        original_line_count = len(lines)

        optimized_lines = []
        indent_level = 0
        prev_was_empty = False

        for line in lines:
            stripped = line.strip()

            # Skip excessive empty lines
            if not stripped:
                if not prev_was_empty:
                    optimized_lines.append("")
                prev_was_empty = True
                continue
            prev_was_empty = False

            # Normalize indentation
            if stripped.startswith("</"):
                indent_level = max(0, indent_level - 1)
                optimized_lines.append("    " * indent_level + stripped)
            elif (
                stripped.startswith("<")
                and not stripped.endswith("/>")
                and not stripped.endswith(">")
            ):
                # Opening tag
                optimized_lines.append("    " * indent_level + stripped)
                if not stripped.endswith("/>"):
                    indent_level += 1
            elif stripped.startswith("<") and stripped.endswith("/>"):
                # Self-closing tag
                optimized_lines.append("    " * indent_level + stripped)
            else:
                # Content or attributes
                optimized_lines.append("    " * indent_level + stripped)

        # Remove trailing empty lines
        while optimized_lines and not optimized_lines[-1].strip():
            optimized_lines.pop()

        optimized_content = "\n".join(optimized_lines)
        final_line_count = len(optimized_lines)

        reduction_percent = (
            ((original_line_count - final_line_count) / original_line_count) * 100
            if original_line_count > 0
            else 0
        )

        return optimized_content, {
            "original_lines": original_line_count,
            "optimized_lines": final_line_count,
            "reduction_percent": reduction_percent,
            "lines_saved": original_line_count - final_line_count,
        }

    def count_lines(self, file_path):
        """Count lines in a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except:
            return 0

    def optimize_file_structure(self, file_path, content):
        """Optimize a file's structure while maintaining functionality"""
        lines = content.split("\n")
        original_line_count = len(lines)

        optimized_lines = []
        current_section = None
        field_buffer = []

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Detect and organize sections
            if (
                "# ============================================================================"
                in line
            ):
                # Process any buffered fields first
                if field_buffer:
                    optimized_lines.extend(self.optimize_field_group(field_buffer))
                    field_buffer = []

                # Add section header
                if i + 1 < len(lines):
                    section_name = lines[i + 1].strip("# ")
                    current_section = section_name
                    optimized_lines.append(line)
                    optimized_lines.append(lines[i + 1])
                    i += 2
                    continue

            # Collect field definitions for optimization
            elif re.match(r"\s+\w+\s*=\s*fields\.", line):
                field_buffer.append(line)
                # Look ahead for multi-line field definitions
                j = i + 1
                while j < len(lines) and (
                    lines[j].strip().startswith(")")
                    or lines[j].strip().startswith(",")
                    or lines[j].strip().startswith('"')
                    or lines[j].strip().startswith("'")
                    or lines[j].strip() == ""
                ):
                    field_buffer.append(lines[j].rstrip())
                    j += 1
                i = j - 1

            # Process accumulated fields at section boundaries
            elif line.strip() == "" and field_buffer:
                optimized_lines.extend(self.optimize_field_group(field_buffer))
                field_buffer = []
                if line.strip():  # Only add non-empty lines
                    optimized_lines.append(line)

            # Regular lines
            else:
                # Process any remaining field buffer
                if field_buffer:
                    optimized_lines.extend(self.optimize_field_group(field_buffer))
                    field_buffer = []

                if line.strip():  # Skip multiple consecutive empty lines
                    optimized_lines.append(line)
                elif not optimized_lines or optimized_lines[-1].strip():
                    optimized_lines.append("")  # Keep single empty lines

            i += 1

        # Process any remaining field buffer
        if field_buffer:
            optimized_lines.extend(self.optimize_field_group(field_buffer))

        # Clean up excessive empty lines
        final_lines = []
        prev_empty = False
        for line in optimized_lines:
            if line.strip() == "":
                if not prev_empty:
                    final_lines.append(line)
                prev_empty = True
            else:
                final_lines.append(line)
                prev_empty = False

        optimized_content = "\n".join(final_lines)
        final_line_count = len(final_lines)

        # Track optimization stats
        reduction_percent = (
            (original_line_count - final_line_count) / original_line_count
        ) * 100

        return optimized_content, {
            "original_lines": original_line_count,
            "optimized_lines": final_line_count,
            "reduction_percent": reduction_percent,
            "lines_saved": original_line_count - final_line_count,
        }

    def optimize_field_group(self, field_lines):
        """Optimize a group of field definitions"""
        if not field_lines:
            return []

        optimized = []
        current_field = []

        for line in field_lines:
            if re.match(r"\s+\w+\s*=\s*fields\.", line) and current_field:
                # Process the previous field
                optimized.extend(self.optimize_single_field(current_field))
                current_field = [line]
            else:
                current_field.append(line)

        # Process the last field
        if current_field:
            optimized.extend(self.optimize_single_field(current_field))

        return optimized

    def optimize_single_field(self, field_lines):
        """Optimize a single field definition"""
        if not field_lines:
            return []

        # Join multi-line field definition
        field_content = " ".join(line.strip() for line in field_lines if line.strip())

        # Extract field info
        field_match = re.match(r"(\w+)\s*=\s*fields\.(\w+)\s*\((.+)\)", field_content)
        if not field_match:
            return field_lines  # Return original if can't parse

        field_name = field_match.group(1)
        field_type = field_match.group(2)
        field_params = field_match.group(3)

        # Clean up parameters
        if len(field_content) > 100:  # Multi-line format for long definitions
            return [
                f"    {field_name} = fields.{field_type}(",
                f"        {field_params}",
                "    )",
            ]
        else:  # Single line for short definitions
            return [f"    {field_name} = fields.{field_type}({field_params})"]

    def find_relationship_issues(self):
        """Find all One2many relationships and check if inverse fields exist"""
        print("\n🔍 Analyzing One2many relationships...")

        for py_file in glob.glob(os.path.join(self.models_path, "*.py")):
            if py_file.endswith("__init__.py"):
                continue

            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find One2many field definitions with detailed parsing
            one2many_pattern = r'(\w+)\s*=\s*fields\.One2many\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*(?:,\s*[^)]+)?\s*\)'

            for match in re.finditer(one2many_pattern, content):
                field_name = match.group(1)
                comodel = match.group(2)
                inverse_name = match.group(3)

                # Check if comodel exists
                if comodel not in self.all_models:
                    self.relationship_issues.append(
                        {
                            "type": "missing_comodel",
                            "file": py_file,
                            "field_name": field_name,
                            "comodel": comodel,
                            "inverse_name": inverse_name,
                            "line": match.start(),
                        }
                    )
                    continue

                # Check if inverse field exists in comodel
                comodel_fields = self.all_models[comodel]["fields"]
                if inverse_name not in comodel_fields:
                    self.relationship_issues.append(
                        {
                            "type": "missing_inverse_field",
                            "file": py_file,
                            "field_name": field_name,
                            "comodel": comodel,
                            "inverse_name": inverse_name,
                            "comodel_file": self.all_models[comodel]["file"],
                            "line": match.start(),
                            "full_match": match.group(0),
                        }
                    )

        # Also check Many2one fields for consistency
        self.find_many2one_issues()

        print(f"⚠️  Found {len(self.relationship_issues)} relationship issues")
        return self.relationship_issues

    def find_many2one_issues(self):
        """Find Many2one fields that might have naming issues"""
        print("🔍 Checking Many2one field consistency...")

        for py_file in glob.glob(os.path.join(self.models_path, "*.py")):
            if py_file.endswith("__init__.py"):
                continue

            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find Many2one fields
            many2one_pattern = r'(\w+)\s*=\s*fields\.Many2one\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*[^)]+)?\s*\)'

            for match in re.finditer(many2one_pattern, content):
                field_name = match.group(1)
                comodel = match.group(2)

                # Check if comodel exists
                if comodel not in self.all_models:
                    # Try to find similar model names
                    similar_models = self.find_similar_model_names(comodel)
                    if similar_models:
                        self.relationship_issues.append(
                            {
                                "type": "possible_renamed_comodel",
                                "file": py_file,
                                "field_name": field_name,
                                "comodel": comodel,
                                "suggestions": similar_models,
                                "line": match.start(),
                                "full_match": match.group(0),
                            }
                        )

    def find_similar_model_names(self, target_model):
        """Find similar model names for potential renames"""
        suggestions = []
        target_parts = target_model.split(".")

        for model_name in self.all_models.keys():
            model_parts = model_name.split(".")

            # Check for partial matches
            if len(target_parts) == len(model_parts):
                matches = sum(1 for a, b in zip(target_parts, model_parts) if a == b)
                if matches >= len(target_parts) - 1:  # Allow 1 difference
                    suggestions.append(model_name)

            # Check for substring matches
            if any(part in model_name for part in target_parts[-2:]):
                suggestions.append(model_name)

        return suggestions[:5]  # Return top 5 suggestions

    def generate_fixes(self):
        """Generate fixes for all relationship issues"""
        print("\n🔧 Generating fixes...")

        fixes = []

        for issue in self.relationship_issues:
            if issue["type"] == "missing_inverse_field":
                fix = self.generate_inverse_field_fix(issue)
                if fix:
                    fixes.append(fix)

            elif issue["type"] == "missing_comodel":
                fix = self.generate_comodel_fix(issue)
                if fix:
                    fixes.append(fix)

            elif issue["type"] == "possible_renamed_comodel":
                fix = self.generate_rename_fix(issue)
                if fix:
                    fixes.append(fix)

        return fixes

    def generate_inverse_field_fix(self, issue):
        """Generate fix for missing inverse field"""
        comodel_file = issue["comodel_file"]
        inverse_name = issue["inverse_name"]

        # Determine the current model name from the file with the One2many
        current_model = self.get_model_name_from_file(issue["file"])
        if not current_model:
            return None

        # Generate appropriate Many2one field
        field_def = f'    {inverse_name} = fields.Many2one("{current_model}", string="{inverse_name.replace("_", " ").title()}")'

        return {
            "type": "add_inverse_field",
            "file": comodel_file,
            "field_definition": field_def,
            "field_name": inverse_name,
            "description": f"Add missing inverse field {inverse_name} to {issue['comodel']}",
        }

    def generate_comodel_fix(self, issue):
        """Generate fix for missing comodel - suggest alternatives"""
        suggestions = self.find_similar_model_names(issue["comodel"])

        if suggestions:
            return {
                "type": "suggest_comodel_rename",
                "file": issue["file"],
                "original_comodel": issue["comodel"],
                "suggestions": suggestions,
                "field_name": issue["field_name"],
                "description": f"Missing comodel {issue['comodel']}, suggested alternatives: {', '.join(suggestions)}",
            }
        return None

    def generate_rename_fix(self, issue):
        """Generate fix for potentially renamed comodel"""
        if issue["suggestions"]:
            best_suggestion = issue["suggestions"][0]
            return {
                "type": "rename_comodel_reference",
                "file": issue["file"],
                "field_name": issue["field_name"],
                "old_comodel": issue["comodel"],
                "new_comodel": best_suggestion,
                "full_match": issue["full_match"],
                "description": f"Update {issue['field_name']} comodel from {issue['comodel']} to {best_suggestion}",
            }
        return None

    def get_model_name_from_file(self, file_path):
        """Extract model name from file"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None

    def apply_fixes(self, fixes, dry_run=True):
        """Apply the generated fixes"""
        print(f"\n{'🔍 DRY RUN' if dry_run else '🔧 APPLYING'} fixes...")

        for fix in fixes:
            print(f"\n📝 {fix['description']}")

            if fix["type"] == "add_inverse_field":
                self.apply_inverse_field_fix(fix, dry_run)
            elif fix["type"] == "rename_comodel_reference":
                self.apply_comodel_rename_fix(fix, dry_run)
            elif fix["type"] == "suggest_comodel_rename":
                print(f"   💡 Manual review needed: {fix['description']}")
            elif fix["type"] == "add_missing_xml_field":
                self.apply_missing_xml_field_fix(fix, dry_run)

    def apply_missing_xml_field_fix(self, fix, dry_run=True):
        """Apply fix for fields referenced in XML but missing from models"""
        model_name = fix["model"]
        field_name = fix["field_name"]
        field_type = fix["suggested_field_type"]
        file_path = fix["file"]

        if not file_path or not os.path.exists(file_path):
            print(f"   ❌ Model file not found for {model_name}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Generate appropriate field definition
        if field_type == "fields.Many2one":
            # Try to guess the comodel from field name
            if field_name.endswith("_id"):
                base_name = field_name[:-3]
                # Common comodel patterns
                if base_name == "partner":
                    comodel = "res.partner"
                elif base_name == "company":
                    comodel = "res.company"
                elif base_name == "user":
                    comodel = "res.users"
                else:
                    comodel = f"records.{base_name}"
                field_def = f'    {field_name} = fields.Many2one("{comodel}", string="{field_name.replace("_", " ").title()}")'
            else:
                field_def = f'    {field_name} = fields.Many2one("res.partner", string="{field_name.replace("_", " ").title()}")'
        elif field_type == "fields.Selection":
            field_def = f'    {field_name} = fields.Selection([], string="{field_name.replace("_", " ").title()}")'
        elif field_type == "fields.Boolean":
            field_def = f'    {field_name} = fields.Boolean(string="{field_name.replace("_", " ").title()}", default=False)'
        elif field_type == "fields.Date":
            field_def = f'    {field_name} = fields.Date(string="{field_name.replace("_", " ").title()}")'
        elif field_type == "fields.Datetime":
            field_def = f'    {field_name} = fields.Datetime(string="{field_name.replace("_", " ").title()}")'
        elif field_type == "fields.Float":
            field_def = f'    {field_name} = fields.Float(string="{field_name.replace("_", " ").title()}", digits="Product Price")'
        elif field_type == "fields.Integer":
            field_def = f'    {field_name} = fields.Integer(string="{field_name.replace("_", " ").title()}", default=0)'
        elif field_type == "fields.Text":
            field_def = f'    {field_name} = fields.Text(string="{field_name.replace("_", " ").title()}")'
        else:  # Default to Char
            field_def = f'    {field_name} = fields.Char(string="{field_name.replace("_", " ").title()}")'

        # Find insertion point (same logic as inverse field fix)
        lines = content.split("\n")
        insert_pos = -1

        # Look for the last field of similar type or core fields section
        for i, line in enumerate(lines):
            if (
                field_type.split(".")[-1] in line
                or "user_id =" in line
                or "company_id =" in line
                or "partner_id =" in line
            ):
                insert_pos = i + 1

        if insert_pos == -1:
            # Find class definition and add after it
            for i, line in enumerate(lines):
                if line.strip().startswith("class ") and "models.Model" in line:
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() == "" or lines[j].strip().startswith("_"):
                            continue
                        insert_pos = j
                        break
                    break

        if insert_pos != -1:
            lines.insert(insert_pos, field_def)
            new_content = "\n".join(lines)

            # Check if this file should be optimized
            if file_path in self.files_to_optimize:
                print(f"   🔧 Optimizing {os.path.basename(file_path)} while fixing...")
                optimized_content, stats = self.optimize_file_structure(
                    file_path, new_content
                )
                self.optimization_stats[file_path] = stats
                new_content = optimized_content
                print(
                    f"   📊 Optimized: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                )

            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(
                    f"   ✅ Added XML-referenced field to {os.path.basename(file_path)}"
                )
            else:
                print(
                    f"   📝 Would add to {os.path.basename(file_path)}: {field_def.strip()}"
                )
        else:
            print(
                f"   ⚠️  Could not find insertion point in {os.path.basename(file_path)}"
            )

    def apply_inverse_field_fix(self, fix, dry_run=True):
        """Apply inverse field addition with simultaneous optimization"""
        file_path = fix["file"]
        field_def = fix["field_definition"]

        if not os.path.exists(file_path):
            print(f"   ❌ File not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add the missing field
        lines = content.split("\n")
        insert_pos = -1

        # Look for the last Many2one field or core fields section
        for i, line in enumerate(lines):
            if (
                "fields.Many2one" in line
                or "user_id =" in line
                or "company_id =" in line
                or "partner_id =" in line
            ):
                insert_pos = i + 1

        if insert_pos == -1:
            # Find class definition and add after it
            for i, line in enumerate(lines):
                if line.strip().startswith("class ") and "models.Model" in line:
                    # Find next empty line or field definition
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() == "" or lines[j].strip().startswith("_"):
                            continue
                        insert_pos = j
                        break
                    break

        if insert_pos != -1:
            lines.insert(insert_pos, field_def)
            new_content = "\n".join(lines)

            # Check if this file should be optimized
            if file_path in self.files_to_optimize:
                print(f"   🔧 Optimizing {os.path.basename(file_path)} while fixing...")
                optimized_content, stats = self.optimize_file_structure(
                    file_path, new_content
                )
                self.optimization_stats[file_path] = stats
                new_content = optimized_content
                print(
                    f"   📊 Optimized: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                )

            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"   ✅ Added field and optimized {os.path.basename(file_path)}")
            else:
                print(
                    f"   📝 Would add to {os.path.basename(file_path)}: {field_def.strip()}"
                )
        else:
            print(
                f"   ⚠️  Could not find insertion point in {os.path.basename(file_path)}"
            )

    def apply_comodel_rename_fix(self, fix, dry_run=True):
        """Apply comodel reference rename with simultaneous optimization"""
        file_path = fix["file"]
        old_comodel = fix["old_comodel"]
        new_comodel = fix["new_comodel"]

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace the comodel reference
        new_content = content.replace(f'"{old_comodel}"', f'"{new_comodel}"')
        new_content = new_content.replace(f"'{old_comodel}'", f"'{new_comodel}'")

        if new_content != content:
            # Check if this file should be optimized
            if file_path in self.files_to_optimize:
                print(f"   🔧 Optimizing {os.path.basename(file_path)} while fixing...")
                optimized_content, stats = self.optimize_file_structure(
                    file_path, new_content
                )
                self.optimization_stats[file_path] = stats
                new_content = optimized_content
                print(
                    f"   📊 Optimized: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                )

            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(
                    f"   ✅ Updated comodel reference and optimized {os.path.basename(file_path)}"
                )
            else:
                print(
                    f"   📝 Would update {os.path.basename(file_path)}: {old_comodel} → {new_comodel}"
                )
        else:
            print(f"   ⚠️  No changes needed in {os.path.basename(file_path)}")

    def optimize_remaining_files(self, dry_run=True):
        """Optimize files that weren't touched during relationship fixes"""
        print(f"\n🔧 Optimizing remaining files...")

        optimized_files = set(self.optimization_stats.keys())
        remaining_files = self.files_to_optimize - optimized_files

        for file_path in remaining_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            optimized_content, stats = self.optimize_file_structure(file_path, content)

            if stats["lines_saved"] > 10:  # Only optimize if significant savings
                self.optimization_stats[file_path] = stats

                if not dry_run:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(optimized_content)
                    print(
                        f"   ✅ Optimized {os.path.basename(file_path)}: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                    )
                else:
                    print(
                        f"   📝 Would optimize {os.path.basename(file_path)}: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                    )

        return len(remaining_files)

    def generate_report(self):
        """Generate comprehensive relationship report"""
        report = {
            "timestamp": "2025-08-05",
            "total_models": len(self.all_models),
            "total_issues": len(self.relationship_issues),
            "issues_by_type": defaultdict(int),
            "detailed_issues": self.relationship_issues,
            "models_inventory": self.all_models,
        }

        for issue in self.relationship_issues:
            report["issues_by_type"][issue["type"]] += 1

        return report

    def run_full_audit(self, apply_fixes=False):
        """Run complete relationship audit with XML cross-referencing"""
        print("🚀 Starting Comprehensive Relationship Audit + XML Analysis")
        print("=" * 70)

        # Step 1: Scan all models
        self.scan_all_models()

        # Step 2: Scan all XML views
        self.scan_all_xml_views()

        # Step 3: Cross-reference XML and model fields
        self.cross_reference_xml_model_fields()

        # Step 4: Find relationship issues
        self.find_relationship_issues()

        # Step 5: Generate fixes
        fixes = self.generate_fixes()

        # Step 6: Generate XML-based fixes
        xml_fixes = self.generate_xml_based_fixes()
        all_fixes = fixes + xml_fixes

        # Step 7: Show summary
        print(f"\n📊 AUDIT SUMMARY:")
        print(f"   Total Models: {len(self.all_models)}")
        print(f"   Total XML Files: {len(self.xml_field_references)}")
        print(f"   Relationship Issues: {len(self.relationship_issues)}")
        print(f"   XML-Model Mismatches: {len(self.missing_xml_fields)}")
        print(f"   Unused Model Fields: {len(self.unused_model_fields)}")
        print(f"   Generated Fixes: {len(all_fixes)}")

        issue_types = defaultdict(int)
        for issue in self.relationship_issues:
            issue_types[issue["type"]] += 1

        for issue_type, count in issue_types.items():
            print(f"   - {issue_type}: {count}")

        # Step 8: Apply fixes
        if all_fixes:
            self.apply_fixes(all_fixes, dry_run=not apply_fixes)

        # Step 9: Optimize remaining files (both Python and XML)
        if apply_fixes:
            self.optimize_remaining_files(dry_run=False)
            self.optimize_remaining_xml_files(dry_run=False)

        # Step 10: Generate comprehensive report
        report = self.generate_comprehensive_report()

        report_file = os.path.join(
            self.base_path, "development-tools", "analysis-reports", "comprehensive_audit_report.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Comprehensive report saved to: {report_file}")

        return report, all_fixes

    def generate_xml_based_fixes(self):
        """Generate fixes based on XML-model cross-referencing"""
        fixes = []

        # Generate fixes for missing fields referenced in XML
        for missing_field in self.missing_xml_fields:
            fix = {
                "type": "add_missing_xml_field",
                "model": missing_field["model"],
                "field_name": missing_field["field"],
                "xml_file": missing_field["xml_file"],
                "description": f"Add missing field {missing_field['field']} to model {missing_field['model']} (used in {missing_field['xml_file']})",
            }

            # Try to determine field type from XML usage
            field_type = self.guess_field_type_from_xml_usage(
                missing_field["xml_file"], missing_field["field"]
            )
            fix["suggested_field_type"] = field_type
            fix["file"] = self.all_models.get(missing_field["model"], {}).get("file")

            if fix["file"]:
                fixes.append(fix)

        return fixes

    def guess_field_type_from_xml_usage(self, xml_file, field_name):
        """Analyze XML usage to guess appropriate field type"""
        xml_path = os.path.join(self.views_path, xml_file)
        if not os.path.exists(xml_path):
            return "fields.Char"

        with open(xml_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for patterns that suggest field type
        if f'widget="many2one"' in content and field_name in content:
            return "fields.Many2one"
        elif f'widget="selection"' in content and field_name in content:
            return "fields.Selection"
        elif f'widget="boolean"' in content and field_name in content:
            return "fields.Boolean"
        elif f'widget="date"' in content and field_name in content:
            return "fields.Date"
        elif f'widget="datetime"' in content and field_name in content:
            return "fields.Datetime"
        elif f'widget="float"' in content and field_name in content:
            return "fields.Float"
        elif f'widget="integer"' in content and field_name in content:
            return "fields.Integer"
        elif f'widget="text"' in content and field_name in content:
            return "fields.Text"
        elif field_name.endswith("_id"):
            return "fields.Many2one"
        elif field_name.endswith("_ids"):
            return "fields.One2many"
        elif field_name.endswith("_date"):
            return "fields.Date"
        elif field_name.endswith("_count"):
            return "fields.Integer"
        else:
            return "fields.Char"

    def optimize_remaining_xml_files(self, dry_run=True):
        """Optimize XML files that weren't touched during relationship fixes"""
        print(f"\n🔧 Optimizing XML files...")

        xml_optimized = 0

        for xml_file in self.xml_files_to_optimize:
            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.read()

            optimized_content, stats = self.optimize_xml_file(xml_file, content)

            if stats["lines_saved"] > 5:  # Only optimize if there are savings
                xml_optimized += 1

                if not dry_run:
                    with open(xml_file, "w", encoding="utf-8") as f:
                        f.write(optimized_content)
                    print(
                        f"   ✅ Optimized {os.path.basename(xml_file)}: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                    )
                else:
                    print(
                        f"   📝 Would optimize {os.path.basename(xml_file)}: {stats['original_lines']} → {stats['optimized_lines']} lines ({stats['reduction_percent']:.1f}% reduction)"
                    )

        return xml_optimized

    def generate_comprehensive_report(self):
        """Generate comprehensive audit report including XML analysis"""
        report = {
            "timestamp": "2025-08-05",
            "audit_type": "comprehensive_with_xml",
            "summary": {
                "total_models": len(self.all_models),
                "total_xml_files": len(self.xml_field_references),
                "total_relationship_issues": len(self.relationship_issues),
                "missing_xml_fields": len(self.missing_xml_fields),
                "unused_model_fields": len(self.unused_model_fields),
                "files_optimized": len(self.optimization_stats),
            },
            "relationship_issues": {
                "issues_by_type": defaultdict(int),
                "detailed_issues": self.relationship_issues,
            },
            "xml_model_mismatches": {
                "missing_fields": self.missing_xml_fields,
                "unused_fields": self.unused_model_fields,
            },
            "optimization_results": {
                "python_files": self.optimization_stats,
                "optimization_candidates": {
                    "python": list(self.files_to_optimize),
                    "xml": list(self.xml_files_to_optimize),
                },
            },
            "models_inventory": self.all_models,
            "xml_references": self.xml_field_references,
        }

        for issue in self.relationship_issues:
            report["relationship_issues"]["issues_by_type"][issue["type"]] += 1

        return report


def main():
    # Get the actual current working directory or use relative path
    import os
    # Since we're in development-tools/scripts/, go up two levels to get to workspace root
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    auditor = RelationshipAuditorOptimizer(base_path)

    # Run audit in dry-run mode first
    print("🔍 CRITICAL: Focusing on KeyError: 'task_id' issue...")
    print("Running comprehensive relationship audit...")
    report, fixes = auditor.run_full_audit(apply_fixes=False)

    # Focus on task_id specific issues
    task_id_fixes = [fix for fix in fixes if 'task_id' in fix.get('field_name', '') or 'task_id' in fix.get('inverse_name', '')]

    if task_id_fixes:
        print(f"\n🚨 FOUND {len(task_id_fixes)} task_id related fixes:")
        for fix in task_id_fixes:
            print(f"   ⚡ {fix['description']}")

        print("\n❓ Apply task_id fixes immediately? They resolve the critical KeyError.")
        # Automatically apply task_id fixes since they're critical
        print("🔧 APPLYING TASK_ID FIXES AUTOMATICALLY...")
        auditor.apply_fixes(task_id_fixes, dry_run=False)
        print("✅ Task_id fixes applied!")

    if fixes:
        print(f"\n📊 FULL AUDIT SUMMARY: Found {len(fixes)} total fixable issues.")

        # Show breakdown by type
        fix_types = {}
        for fix in fixes:
            fix_type = fix.get('type', 'unknown')
            fix_types[fix_type] = fix_types.get(fix_type, 0) + 1

        print("\n📋 Fix types breakdown:")
        for fix_type, count in fix_types.items():
            print(f"   - {fix_type}: {count}")

        # Show priority fixes (excluding already applied task_id ones)
        priority_fixes = [fix for fix in fixes if fix not in task_id_fixes and fix.get('type') == 'missing_inverse_field']
        if priority_fixes:
            print(f"\n� {len(priority_fixes)} HIGH PRIORITY relationship fixes:")
            for i, fix in enumerate(priority_fixes[:10]):
                print(f"   {i+1}. {fix['description']}")

            if priority_fixes and len(priority_fixes) > 10:
                print(f"   ... and {len(priority_fixes) - 10} more")


if __name__ == "__main__":
    main()
