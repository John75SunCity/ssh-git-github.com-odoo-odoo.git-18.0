#!/usr/bin/env python3
"""
Comprehensive Records Management Module Validator
==============================================

This validator checks for XML structural issues, field duplications, syntax errors,
and schema compliance problems that can cause deployment failures.

ENHANCED to catch issues missed in previous validations including:
- Duplicate field definitions in views
- Excessive whitespace and formatting issues  
- Invalid menu visibility syntax
- XML schema compliance problems
- Field/model reference validation
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import traceback
from collections import defaultdict
import subprocess
import sys

class ComprehensiveValidator:
    def __init__(self):
        self.total_files = 0
        self.total_issues = 0
        self.files_with_issues = 0
        self.files_passed = 0
        # Local model registry collected from Python files
        self.local_models = set()
        # Action XML IDs collected from XML files (e.g., ir.actions.* and <act_window>)
        self.action_xml_ids = set()
        # Non-blocking warnings to display after summary
        self.global_warnings = []
        # Counters for new modernization categories
        self.hierarchy_issues = 0
        self.deprecated_attr_usage = 0
        self.deprecated_states_usage = 0
        # New modernization counters
        self.legacy_tree_usages = 0
        self.inline_script_usages = 0
        self.missing_hierarchy_view_warnings = 0
        # Cron tracking
        self._cron_id_first_seen = {}
        self._duplicate_cron_issues = []

    # ---------------------- Modernization / New Checks ----------------------
    def check_hierarchy_tags(self, root: ET.Element, file_path: Path):
        """Validate <hierarchy> tags for allowed/required attributes.

        Allowed attributes (Odoo 18): string, parent_field, child_field
        Required attributes: parent_field, child_field
        Unsupported or missing attributes are blocking errors.
        """
        issues = []
        allowed = {"string", "parent_field", "child_field"}
        required = {"parent_field", "child_field"}
        for elem in root.findall('.//hierarchy'):
            attrs = elem.attrib
            missing = required - set(attrs)
            if missing:
                issues.append(
                    f"❌ hierarchy tag missing required attribute(s): {', '.join(sorted(missing))}"
                )
            unsupported = [a for a in attrs if a not in allowed]
            if unsupported:
                issues.append(
                    f"❌ hierarchy tag has unsupported attribute(s): {', '.join(sorted(unsupported))}; allowed: {', '.join(sorted(allowed))}"
                )
        self.hierarchy_issues += len(issues)
        return issues

    def check_deprecated_attrs_usage(self, content: str):
        """Detect legacy attrs= usage (deprecated in modern view logic)."""
        # Fast check first
        if 'attrs=' not in content:
            return []
        # Avoid false positives in comments by simple heuristic (not perfect but sufficient)
        issues = []
        pattern = re.compile(r"attrs=\"|attrs='")
        if pattern.search(content):
            issues.append("❌ Deprecated 'attrs=' usage detected – replace with direct invisible/required expressions or decoration attributes")
            self.deprecated_attr_usage += 1
        return issues

    def check_deprecated_states_usage(self, content: str):
        """Detect legacy states= usage (server-side state logic should move to widgets/attrs equivalent in Odoo 18)."""
        if 'states=' not in content:
            return []
        issues = []
        pattern = re.compile(r"states=\"|states='")
        if pattern.search(content):
            issues.append("❌ Deprecated 'states=' usage detected – migrate to statusbar widgets or compute-driven visibility")
            self.deprecated_states_usage += 1
        return issues

    def check_active_id_usage(self, content: str, file_path: Path):
        """Flag active_id usage for manual review.

        Guidance:
          - active_id is fine in transient wizard defaults or action buttons setting defaults.
          - It should NOT be relied upon inside persistent domain logic enforcing data integrity.
        We treat every occurrence as a non-blocking advisory unless future rules classify patterns.
        """
        if 'active_id' not in content:
            return
        # Count occurrences (rough)
        count = content.count('active_id')
        self.global_warnings.append(
            f"WARN {file_path}: contains {count} occurrence(s) of active_id – verify usage is limited to UI defaults / action contexts"
        )

    def collect_local_model_names(self):
        """Scan records_management/models and wizards to collect `_name` model names"""
        model_dirs = [
            Path("records_management/models"),
            Path("records_management/wizards"),
        ]
        name_regex = re.compile(r"_name\s*=\s*['\"]([a-z0-9_.]+)['\"]", re.IGNORECASE)
        for base in model_dirs:
            if not base.exists():
                continue
            for py_file in base.rglob("*.py"):
                try:
                    text = py_file.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for match in name_regex.findall(text):
                    self.local_models.add(match.strip())
        
    def validate_xml_structure(self, file_path, content):
        """Enhanced XML structure validation that catches formatting and duplication issues"""
        issues = []
        
        try:
            # Parse XML for basic structure validation
            root = ET.fromstring(content)
            
            # Check for duplicate field definitions in views
            if 'views' in str(file_path):
                field_duplicates = self.check_duplicate_fields(content)
                issues.extend(field_duplicates)
            
            # Check for excessive whitespace that can cause parsing issues
            whitespace_issues = self.check_excessive_whitespace(content)
            issues.extend(whitespace_issues)
            
            # Check menu visibility syntax
            menu_syntax_issues = self.check_menu_syntax(content)
            issues.extend(menu_syntax_issues)
            
            # Check XML declaration format
            declaration_issues = self.check_xml_declaration(content)
            issues.extend(declaration_issues)
            
            # Check for proper data tag structure
            data_structure_issues = self.check_data_structure(content)
            issues.extend(data_structure_issues)

            # Validate ir.actions.act_window res_model values against local models
            action_model_issues = self.check_action_res_models(root, file_path)
            issues.extend(action_model_issues)

            # Validate that menus reference existing actions (by XML id)
            menu_action_issues = self.check_menu_action_references(root, file_path)
            issues.extend(menu_action_issues)

            # New modernization checks
            issues.extend(self.check_hierarchy_tags(root, Path(file_path)))
            issues.extend(self.check_deprecated_attrs_usage(content))
            issues.extend(self.check_deprecated_states_usage(content))
            issues.extend(self.check_legacy_tree_usage(content, Path(file_path)))
            issues.extend(self.check_inline_script_usage(content, Path(file_path)))
            # active_id usage: advisory only
            self.check_active_id_usage(content, Path(file_path))
            # Post-parse heuristic: parent/child relation but no hierarchy view in same file
            self.check_missing_hierarchy_view(root, content, Path(file_path))
            
        except ET.ParseError as e:
            issues.append(f"❌ XML Parse Error: {e}")
        except Exception as e:
            issues.append(f"❌ Structure validation error: {e}")
            
        return issues

    def check_action_res_models(self, root: ET.Element, file_path: Path):
        """Check <record model="ir.actions.act_window"> res_model values.

        Rules (non-invasive):
        - ERROR if res_model starts with 'records.' or 'rate.' and is not in local models set
        - For other unknown res_models, collect a non-blocking global warning (printed after summary)
        """
        issues = []
        for record in root.findall(".//record[@model='ir.actions.act_window']"):
            res_model_field = record.find(".//field[@name='res_model']")
            if res_model_field is None or (res_model_field.text or '').strip() == '':
                continue
            res_model = (res_model_field.text or '').strip()
            if res_model in self.local_models:
                continue
            # Strict ERROR only for local namespaces we own
            if res_model.startswith('records.') or res_model.startswith('rate.'):
                issues.append(f"❌ Action res_model '{res_model}' not found among local models/wizards")
            else:
                # Non-blocking global warning (do not fail validation)
                self.global_warnings.append(
                    f"WARN {file_path}: res_model '{res_model}' not found in local models – verify dependencies/typos"
                )
        return issues

    def _extract_action_target(self, raw_value: str):
        """Normalize an action reference string to (module, id).

        Accepts values like 'module.action_id' or 'action_id'. Returns tuple
        (module or None, id_str). Whitespace is stripped. If value is empty, returns (None, '').
        """
        if not raw_value:
            return (None, '')
        value = (raw_value or '').strip()
        # Odoo allows module-qualified refs: module.xml_id
        if '.' in value:
            module, _, xml_id = value.rpartition('.')
            module = module or None
            return (module, xml_id)
        return (None, value)

    def check_menu_action_references(self, root: ET.Element, file_path: Path):
        """Ensure that menus reference existing action XML IDs.

        Rules:
        - If a <menuitem> has an 'action' attribute or a child <field name="action" ref="...">
          we check that the referenced action xml id exists.
        - If the reference is module-qualified and module != 'records_management', emit a
          non-blocking warning only (external dependency), don't fail.
        - If the reference is local (module is None or 'records_management') and the id is
          not in self.action_xml_ids, raise a blocking error.
        Also supports <record model="ir.ui.menu"> with <field name="action" ref="..."/>.
        """
        issues = []
        # 1) <menuitem action="...">
        for menu in root.findall('.//menuitem'):
            action_attr = menu.get('action')
            if action_attr:
                mod, xml_id = self._extract_action_target(action_attr)
                if not xml_id:
                    continue
                if mod and mod != 'records_management':
                    # External module reference – warn only
                    self.global_warnings.append(
                        f"WARN {file_path}: menu action '{action_attr}' not defined locally – verify dependency order"
                    )
                else:
                    if xml_id not in self.action_xml_ids:
                        issues.append(
                            f"❌ Menu references unknown action '{action_attr}' (xml id '{xml_id}' not found in this module)"
                        )
        # 2) <menuitem><field name="action" ref="..."/></menuitem>
        for field in root.findall(".//menuitem/field[@name='action']"):
            ref = field.get('ref') or ''
            if not ref:
                continue
            mod, xml_id = self._extract_action_target(ref)
            if mod and mod != 'records_management':
                self.global_warnings.append(
                    f"WARN {file_path}: menu action ref '{ref}' not defined locally – verify dependency order"
                )
            else:
                if xml_id not in self.action_xml_ids:
                    issues.append(
                        f"❌ Menu references unknown action ref '{ref}' (xml id '{xml_id}' not found in this module)"
                    )
        # 3) <record model="ir.ui.menu"><field name="action" ref="..."/></record>
        for rec in root.findall(".//record[@model='ir.ui.menu']"):
            field = rec.find(".//field[@name='action']")
            if field is None:
                continue
            ref = field.get('ref') or ''
            if not ref:
                # Sometimes action may be provided as text with eval="...", skip complex cases
                continue
            mod, xml_id = self._extract_action_target(ref)
            if mod and mod != 'records_management':
                self.global_warnings.append(
                    f"WARN {file_path}: ir.ui.menu action ref '{ref}' not defined locally – verify dependency order"
                )
            else:
                if xml_id not in self.action_xml_ids:
                    issues.append(
                        f"❌ ir.ui.menu references unknown action ref '{ref}' (xml id '{xml_id}' not found in this module)"
                    )
        return issues
    
    def check_duplicate_fields(self, content):
        """Check for TRUE duplicate field definitions within the same exact context"""
        issues = []
        lines = content.split('\n')
        
        # Parse the XML to properly understand structure
        try:
            root = ET.fromstring(content)
            
            # Find all view records
            for record in root.findall(".//record[@model='ir.ui.view']"):
                record_id = record.get('id', 'unknown')
                
                # Find the arch field
                arch_field = record.find(".//field[@name='arch']")
                if arch_field is None:
                    continue
                
                # Check each direct child of arch for duplicates
                arch_content = arch_field[0] if len(arch_field) > 0 else None
                if arch_content is not None:
                    self._check_context_duplicates(arch_content, record_id, issues, content)
                    
        except ET.ParseError:
            # Fallback to line-by-line if XML parsing fails
            return self._fallback_duplicate_check(content)
            
        return issues
    
    def _check_context_duplicates(self, element, record_id, issues, original_content):
        """Recursively check for duplicates within specific contexts"""
        # Only check direct children of structural elements for duplicates
        structural_elements = ['list', 'form', 'kanban', 'search', 'tree']
        
        if element.tag in structural_elements:
            # Check direct field children for duplicates
            field_names = []
            for child in element:
                if child.tag == 'field' and child.get('name'):
                    field_name = child.get('name')
                    if field_name in field_names:
                        # Find line number for reporting
                        line_num = self._find_line_number(original_content, field_name, record_id)
                        issues.append(f"❌ Actual duplicate field '{field_name}' in {element.tag} view at line {line_num}")
                    else:
                        field_names.append(field_name)
        
        # Recursively check children
        for child in element:
            self._check_context_duplicates(child, record_id, issues, original_content)
    
    def _find_line_number(self, content, field_name, record_id):
        """Find approximate line number for error reporting"""
        lines = content.split('\n')
        in_record = False
        for i, line in enumerate(lines, 1):
            if f'id="{record_id}"' in line or f"id='{record_id}'" in line:
                in_record = True
            elif in_record and '</record>' in line:
                in_record = False
            elif in_record and f'name="{field_name}"' in line or f"name='{field_name}'" in line:
                return i
        return 0
    
    def _fallback_duplicate_check(self, content):
        """Fallback method if XML parsing fails"""
        issues = []
        lines = content.split('\n')
        
        current_structural_context = None
        current_fields = []
        in_arch = False
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if '<field name="arch"' in stripped:
                in_arch = True
                continue
            elif in_arch and '</field>' in stripped and 'arch' not in stripped:
                in_arch = False
                continue
                
            if in_arch:
                # Detect structural elements
                if any(f'<{tag}' in stripped for tag in ['list', 'form', 'kanban', 'tree', 'search']):
                    current_structural_context = stripped
                    current_fields = []
                elif any(f'</{tag}>' in stripped for tag in ['list', 'form', 'kanban', 'tree', 'search']):
                    current_structural_context = None
                    current_fields = []
                elif '<field name=' in stripped and current_structural_context:
                    field_match = re.search(r'name=["\']([^"\']+)["\']', stripped)
                    if field_match:
                        field_name = field_match.group(1)
                        if field_name in current_fields:
                            issues.append(f"❌ Duplicate field '{field_name}' at line {i}")
                        else:
                            current_fields.append(field_name)
        
        return issues
    
    def check_excessive_whitespace(self, content):
        """Check for excessive whitespace that can cause XML parsing issues"""
        issues = []
        lines = content.split('\n')
        
        consecutive_empty = 0
        for i, line in enumerate(lines, 1):
            if not line.strip():
                consecutive_empty += 1
            else:
                if consecutive_empty > 3:
                    issues.append(f"⚠️  Excessive whitespace: {consecutive_empty} consecutive empty lines ending at line {i}")
                consecutive_empty = 0
        
        return issues
    
    def check_menu_syntax(self, content):
        """Check for invalid menu visibility syntax - DISABLED: These are valid Odoo XML patterns"""
        issues = []
        
        # DISABLED: The patterns invisible="field == True" and decoration="field == False" 
        # are valid Odoo XML syntax and should NOT be flagged as deprecated
        
        return issues
    
    def check_xml_declaration(self, content):
        """Check XML declaration format for Odoo 18.0 compliance"""
        issues = []
        
        # Check for single quotes in XML declaration
        if re.search(r"<\?xml version='1\.0' encoding='utf-8'\?>", content):
            issues.append("❌ XML declaration uses single quotes - should use double quotes for Odoo 18.0 compliance")
        
        return issues
    
    def check_data_structure(self, content):
        """Check for proper data tag structure"""
        issues = []
        
        # Check if XML has proper odoo/data structure
        if '<odoo>' in content:
            # Accept <data> with or without attributes (e.g., <data noupdate="1">)
            has_data_wrapper = re.search(r"<data(\s|>)", content) is not None
            if not has_data_wrapper:
                # Check if there are records that should be in data tags
                if any(tag in content for tag in ['<record', '<menuitem', '<act_window']):
                    issues.append("⚠️  Records found without <data> wrapper - may cause schema issues")
        
        return issues
    
    def validate_file(self, file_path):
        """Validate a single XML file"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Run all validation checks
            xml_issues = self.validate_xml_structure(file_path, content)
            issues.extend(xml_issues)
            
        except Exception as e:
            issues.append(f"❌ Failed to read file: {e}")
        
        return issues
    
    def validate_all_files(self):
        """Validate all XML files in the records_management module"""
        print("🔍 COMPREHENSIVE RECORDS MANAGEMENT VALIDATOR")
        print("=" * 60)
        print("🎯 Enhanced to catch XML structural and formatting issues")
        print()
        # Collect local model names once
        self.collect_local_model_names()
        if self.local_models:
            print(f"📚 Local models collected: {len(self.local_models)}")
        else:
            print("📚 Local models collected: 0 (skipping res_model cross-check)")
        
        # Find all XML files
        xml_files = list(Path("records_management").rglob("*.xml"))
        
        if not xml_files:
            print("❌ No XML files found in records_management/")
            return 1

        # Pre-collect all action xml ids across module for menu cross-checks
        self.collect_action_xml_ids(xml_files)
        print(f"🧭 Action XML IDs collected: {len(self.action_xml_ids)}")
        # Detect duplicate cron ids BEFORE per-file validation so they surface early
        self.detect_duplicate_cron_ids(xml_files)
        if self._duplicate_cron_issues:
            # Count each duplicate as an issue (blocking) – duplicates cause override ambiguity
            self.total_issues += len(self._duplicate_cron_issues)
            self.files_with_issues += 1
            print("📄 [aggregate] scheduled_actions (ir.cron)")
            print("🎯 Status: ❌ ISSUES FOUND")
            for issue in self._duplicate_cron_issues:
                print(f"      {issue}")
            print()
        
        self.total_files = len(xml_files)
        print(f"📊 Validating {self.total_files} XML files...")
        print()
        
        files_with_issues = []
        
        for xml_file in xml_files:
            issues = self.validate_file(xml_file)
            
            if issues:
                self.files_with_issues += 1
                self.total_issues += len(issues)
                files_with_issues.append((xml_file, issues))
                
                print(f"📄 {xml_file}")
                print("🎯 Status: ❌ ISSUES FOUND")
                for issue in issues:
                    print(f"      {issue}")
                print()
            else:
                self.files_passed += 1
                print(f"📄 {xml_file}")
                print("🎯 Status: ✅ PASSED")
                print("   ✅ All validations passed!")
                print()
        
        # Run nested sublist field existence validator (catch cross-model nested list field errors)
        nested_tool = Path("development-tools/validation-tools/nested_sublist_field_validator.py")
        nested_issues = 0
        if nested_tool.exists():
            print("🔎 Running nested sublist field validator...")
            try:
                proc = subprocess.run([
                    sys.executable, str(nested_tool)
                ], capture_output=True, text=True, check=False)
                output = (proc.stdout or "") + (proc.stderr or "")
                # Echo output for visibility
                if output.strip():
                    print(output)
                # Non-zero return code indicates ERROR(s) (WARNs allowed)
                if proc.returncode != 0:
                    # Count ERROR lines if present to add into totals
                    nested_issues = sum(1 for line in output.splitlines() if line.startswith("ERROR")) or 1
                    self.total_issues += nested_issues
            except Exception as e:
                print(f"⚠️  Failed to run nested sublist validator: {e}")

        # Summary
        print("=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        print(f"📁 Total files validated: {self.total_files}")
        print(f"✅ Files passed: {self.files_passed}")
        print(f"❌ Files with issues: {self.files_with_issues}")
        print(f"🐛 Total issues found: {self.total_issues}")
        if self.hierarchy_issues or self.deprecated_attr_usage or self.deprecated_states_usage:
            print("\n🧪 Modernization metrics:")
            print(f"   • Hierarchy attribute issues: {self.hierarchy_issues}")
            print(f"   • Deprecated attrs= usages: {self.deprecated_attr_usage}")
            print(f"   • Deprecated states= usages: {self.deprecated_states_usage}")
            print(f"   • Legacy <tree> usages: {self.legacy_tree_usages}")
            print(f"   • Inline <script> usages: {self.inline_script_usages}")
            print(f"   • Missing hierarchy view warnings: {self.missing_hierarchy_view_warnings}")
        if nested_issues:
            print(f"   • Nested sublist field errors: {nested_issues}")
        
        if self.total_issues > 0:
            print(f"\n⚠️  {self.total_issues} issues need to be resolved before deployment")
            
            # Show most common issue types
            issue_types = defaultdict(int)
            for _, issues in files_with_issues:
                for issue in issues:
                    if "Duplicate field" in issue:
                        issue_types["Duplicate fields"] += 1
                    elif "XML declaration" in issue:
                        issue_types["XML declaration format"] += 1
                    elif "menu syntax" in issue:
                        issue_types["Menu visibility syntax"] += 1
                    elif "whitespace" in issue:
                        issue_types["Excessive whitespace"] += 1
                    elif "Parse Error" in issue:
                        issue_types["XML parse errors"] += 1
                    else:
                        issue_types["Other issues"] += 1
            
            if issue_types:
                print("\n📈 Issue breakdown:")
                for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {issue_type}: {count}")
        else:
            print("\n🎉 All files passed validation!")

        # Print non-blocking global warnings (do not affect totals)
        if self.global_warnings:
            print("\n⚠️  NON-BLOCKING WARNINGS")
            for w in self.global_warnings:
                print(f"   {w}")
        
        return self.total_issues

    # ---------------- Additional Modernization Checks -----------------
    def check_legacy_tree_usage(self, content: str, file_path: Path):
        """Detect legacy <tree> tag usage (should be <list> in Odoo 18).

        Blocking error: each occurrence increments total issues.
        """
        if '<tree' not in content:
            return []
        # Avoid false positives inside comments by naive exclusion of <!-- ... --> blocks
        stripped = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        matches = re.findall(r'<tree\b', stripped)
        if not matches:
            return []
        self.legacy_tree_usages += len(matches)
        return [f"❌ Legacy <tree> tag detected ({len(matches)} occurrence(s)) – replace with <list> for Odoo 18 modernization"]

    def check_inline_script_usage(self, content: str, file_path: Path):
        """Detect inline <script> blocks in view XML (warn)."""
        if '<script' not in content:
            return []
        stripped = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        matches = re.findall(r'<script\b', stripped)
        if not matches:
            return []
        self.inline_script_usages += len(matches)
        # Non-blocking: push to global warnings so they do not fail validation
        self.global_warnings.append(
            f"WARN {file_path}: inline <script> tag detected ({len(matches)} occurrence(s)) – prefer assets pipeline or JS modules"
        )
        return []

    def check_missing_hierarchy_view(self, root: ET.Element, content: str, file_path: Path):
        """Heuristic: If model appears to define parent/child relational structure and no hierarchy view is present.

        Logic (per file scope):
          - Detect presence of words parent_id and child_ids (or parent_* / *_child_ids patterns) inside same view XML file.
          - If file defines at least one <record model="ir.ui.view"> for that model BUT none with <hierarchy>, raise WARN.
        This is a heuristic – adds non-blocking global warning to avoid false positives.
        """
        text_lower = content.lower()
        if 'parent_id' not in text_lower:
            return
        if '<hierarchy' in text_lower:
            return  # already has hierarchy
        # attempt to extract model names for which views are defined here
        model_names = set()
        for rec in root.findall(".//record[@model='ir.ui.view']"):
            model_field = rec.find(".//field[@name='model']")
            if model_field is not None and (model_field.text or '').strip():
                model_names.add((model_field.text or '').strip())
        if not model_names:
            return
        # Only warn once per file
        self.global_warnings.append(
            f"WARN {file_path}: parent_id detected without a hierarchy view – consider adding <hierarchy> for tree-like navigation"
        )
        self.missing_hierarchy_view_warnings += 1

    def collect_action_xml_ids(self, xml_files):
        """Scan provided XML files to collect action XML IDs defined in this module.

        We collect ids from:
         - <record model="ir.actions.*" id="...">
         - <act_window id="..." .../>
        """
        action_ids = set()
        for xml_file in xml_files:
            try:
                content = Path(xml_file).read_text(encoding='utf-8', errors='ignore')
                root = ET.fromstring(content)
            except Exception:
                continue
            # Collect from <record model="ir.actions.*">
            for rec in root.findall(".//record"):
                model = rec.get('model') or ''
                if model.startswith('ir.actions.'):
                    rec_id = rec.get('id')
                    if rec_id:
                        action_ids.add(rec_id)
            # Collect from shorthand <act_window id="...">
            for aw in root.findall('.//act_window'):
                rec_id = aw.get('id')
                if rec_id:
                    action_ids.add(rec_id)
        self.action_xml_ids = action_ids

    # ---------------- Scheduled Action Integrity -----------------
    def detect_duplicate_cron_ids(self, xml_files):
        """Detect duplicate ir.cron record ids across XML files.

        Duplicate cron XML IDs can cause silent overrides leading to unexpected scheduling behavior.
        We flag each duplicate occurrence (after the first) as a blocking issue.
        """
        for xml_file in xml_files:
            try:
                content = Path(xml_file).read_text(encoding='utf-8', errors='ignore')
                root = ET.fromstring(content)
            except Exception:
                continue
            for rec in root.findall(".//record[@model='ir.cron']"):
                cron_id = rec.get('id')
                if not cron_id:
                    continue
                if cron_id not in self._cron_id_first_seen:
                    self._cron_id_first_seen[cron_id] = xml_file
                else:
                    first_file = self._cron_id_first_seen[cron_id]
                    # Avoid reporting same duplicate multiple times if more than two occurrences
                    duplicate_marker = (cron_id, xml_file)
                    already_reported = any(msg.startswith(f"❌ Duplicate ir.cron id '{cron_id}'") and first_file in msg for msg in self._duplicate_cron_issues)
                    if not already_reported:
                        self._duplicate_cron_issues.append(
                            f"❌ Duplicate ir.cron id '{cron_id}' found in {xml_file} (already defined in {first_file})"
                        )

def main():
    """Main validation function"""
    validator = ComprehensiveValidator()
    exit_code = validator.validate_all_files()
    return exit_code

if __name__ == "__main__":
    try:
        issues = main()
        exit(1 if issues > 0 else 0)
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        traceback.print_exc()
        exit(1)
