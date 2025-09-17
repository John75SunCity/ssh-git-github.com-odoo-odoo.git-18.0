#!/usr/bin/env python3
"""
Comprehensive Action & Field Validator for Odoo 18
- Validates invalid action fields
- Checks if actions follow Odoo best practices
- Suggests built-in Odoo solutions where applicable
- Validates action-model relationships
"""

import os
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from collections import defaultdict

class ComprehensiveActionValidator:
    def __init__(self):
        # Valid fields for ir.actions.act_window in Odoo 18
        self.valid_act_window_fields = {
            'name', 'res_model', 'view_mode', 'views', 'domain', 'context',
            'target', 'res_id', 'search_view_id', 'limit', 'help', 'type',
            'view_id', 'view_ids', 'auto_search', 'filter', 'binding_model_id',
            'binding_type', 'binding_view_types'
        }
        
        # Fields that should be in related models instead
        self.deprecated_fields = {
            'sequence': {
                'reason': 'Use menuitem sequence="X" instead of action sequence - sequence belongs in ir.ui.menu',
                'alternative': 'Move to <menuitem sequence="X" action="action_id"/>',
                'related_model': 'ir.ui.menu'
            },
            'priority': {
                'reason': 'No longer supported in Odoo 18 - use menu sequence for ordering',
                'alternative': 'Use menu sequence or model priority field if needed',
                'related_model': 'ir.ui.menu or target model'
            },
            'groups_id': {
                'reason': 'Use menuitem groups instead of action groups',
                'alternative': 'Move to <menuitem groups="group1,group2" action="action_id"/>',
                'related_model': 'ir.ui.menu'
            }
        }
        
        # Built-in Odoo action patterns to check for
        self.builtin_alternatives = {
            'tree_view_only': {
                'pattern': r'view_mode.*tree.*(?!form)',
                'suggestion': 'Consider if this needs custom action or can use standard list action'
            },
            'simple_form': {
                'pattern': r'target.*new.*view_mode.*form',
                'suggestion': 'Check if ir.actions.act_window_close or wizard pattern is more appropriate'
            }
        }
        
        # Odoo core fields that should be ignored during validation
        # These come from standard Odoo mixins and models
        self.odoo_core_fields = {
            # Base model fields
            'id', 'create_date', 'create_uid', 'write_date', 'write_uid', 
            'display_name', '__last_update',
            
            # mail.thread mixin fields
            'message_ids', 'message_follower_ids', 'message_partner_ids',
            'message_channel_ids', 'message_unread', 'message_unread_counter',
            'message_needaction', 'message_needaction_counter', 'message_has_error',
            'message_has_error_counter', 'message_attachment_count',
            
            # mail.activity.mixin fields
            'activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id',
            'activity_date_deadline', 'activity_summary', 'my_activity_date_deadline',
            
            # Common state fields that might exist
            'state', 'active', 'name', 'sequence', 'company_id', 'currency_id',
            
            # Portal mixin fields
            'access_url', 'access_token', 'access_warning',
            
            # Website mixin fields
            'website_id', 'is_published', 'website_url',
            
            # UTM mixin fields
            'utm_campaign_id', 'utm_source_id', 'utm_medium_id'
        }
        
        # Track relationships
        self.action_model_map = {}
        self.model_capabilities = defaultdict(set)
        self.issues_found = []
        self.suggestions = []
        
    def analyze_model_capabilities(self, directory):
        """Analyze what capabilities models have vs what actions expect"""
        models_path = Path(directory) / 'records_management' / 'models'
        
        if not models_path.exists():
            return
            
        print("🔍 Analyzing model capabilities...")
        
        for py_file in models_path.glob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find model names
                model_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                
                for model_name in model_matches:
                    # Check for sequence field
                    if 'sequence' in content:
                        self.model_capabilities[model_name].add('has_sequence_field')
                    
                    # Check for priority field
                    if re.search(r'priority\s*=\s*fields\.', content):
                        self.model_capabilities[model_name].add('has_priority_field')
                    
                    # Check for state field
                    if re.search(r'state\s*=\s*fields\.Selection', content):
                        self.model_capabilities[model_name].add('has_state_field')
                        
                    # Check if inherits from mail.thread
                    if 'mail.thread' in content:
                        self.model_capabilities[model_name].add('has_chatter')
                        
            except Exception as e:
                continue
                
        print(f"✅ Analyzed {len(self.model_capabilities)} models")

    def validate_action_functionality(self, action_record, action_id, filepath):
        """Validate if action fields actually work and suggest alternatives"""
        issues = []
        
        # Get action details
        res_model = None
        view_mode = None
        target = None
        domain = None
        context = None
        
        for field in action_record.findall('field'):
            field_name = field.get('name')
            field_value = field.get('eval') or field.text or ''
            
            if field_name == 'res_model':
                res_model = field_value
            elif field_name == 'view_mode':
                view_mode = field_value
            elif field_name == 'target':
                target = field_value
            elif field_name == 'domain':
                domain = field_value
            elif field_name == 'context':
                context = field_value
        
        if res_model:
            self.action_model_map[action_id] = res_model
            
            # Check if model has capabilities that could replace action features
            model_caps = self.model_capabilities.get(res_model, set())
            
            # Validate view_mode makes sense
            if view_mode:
                if 'tree' in view_mode and 'form' not in view_mode:
                    if 'kanban' not in view_mode and 'pivot' not in view_mode:
                        issues.append({
                            'type': 'functionality_suggestion',
                            'field': 'view_mode',
                            'message': f'Action {action_id} only shows tree view - consider if form view needed for usability',
                            'suggestion': 'Add form view: view_mode="tree,form"'
                        })
                
                # Check for wizard patterns
                if target == 'new' and view_mode == 'form':
                    if res_model.endswith('.wizard') or 'wizard' in res_model:
                        issues.append({
                            'type': 'best_practice',
                            'field': 'target',
                            'message': f'Wizard action {action_id} follows correct pattern',
                            'suggestion': 'Good: Using target="new" for wizard'
                        })
                    else:
                        issues.append({
                            'type': 'functionality_warning',
                            'field': 'target',
                            'message': f'Action {action_id} uses target="new" but model is not a wizard',
                            'suggestion': 'Consider if this should be a wizard model or use target="current"'
                        })
            
            # Check for unnecessary custom actions
            if view_mode == 'tree,form' and not domain and not context:
                issues.append({
                    'type': 'optimization',
                    'field': 'action',
                    'message': f'Action {action_id} might be redundant - simple tree,form action',
                    'suggestion': 'Check if standard menu action would suffice'
                })
        
        return issues

    def validate_view_fields(self, view_element, model_name, filepath, line_num=None):
        """Validate that fields referenced in views actually exist in the model"""
        issues = []
        
        # Find all field references in this view
        field_elements = view_element.findall('.//field[@name]')
        
        for field_elem in field_elements:
            field_name = field_elem.get('name')
            
            # Skip Odoo core fields - they're handled by the framework
            if field_name in self.odoo_core_fields:
                continue
                
            # Skip computed field patterns that are always valid
            if '.' in field_name:  # Related fields like partner_id.name
                continue
                
            # Check if field exists in our custom models
            model_fields = self._get_model_fields(model_name)
            
            if field_name not in model_fields and field_name not in self.odoo_core_fields:
                issues.append({
                    'type': 'field_error',
                    'file': filepath,
                    'line': line_num,
                    'field': field_name,
                    'model': model_name,
                    'message': f'Field "{field_name}" does not exist in model "{model_name}"',
                    'reason': f'View references non-existent field "{field_name}"',
                    'alternative': 'Check if field should be added to model or removed from view'
                })
        
        return issues

    def _get_model_fields(self, model_name):
        """Get fields for a model by scanning Python model files"""
        model_fields = set()
        
        # Add standard Odoo fields that are always available
        model_fields.update(self.odoo_core_fields)
        
        # Find the model file
        model_file_patterns = [
            f"records_management/models/{model_name.replace('.', '_')}.py",
            f"models/{model_name.replace('.', '_')}.py"
        ]
        
        for pattern in model_file_patterns:
            model_path = Path(pattern)
            if model_path.exists():
                try:
                    with open(model_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract field definitions
                    field_patterns = [
                        r'(\w+)\s*=\s*fields\.\w+\(',  # Standard field definitions
                        r'@api\.depends\([\'"]([^\'"]+)[\'"]\)',  # Dependencies might reveal fields
                    ]
                    
                    for pattern in field_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple):
                                # Handle depends patterns
                                for dep in match[0].split(','):
                                    field_name = dep.strip().strip('\'"').split('.')[0]
                                    model_fields.add(field_name)
                            else:
                                model_fields.add(match.strip())
                                
                except Exception:
                    pass
                break
        
        return model_fields

    def validate_field_context_issues(self, filepath):
        """Detect fields referenced in wrong model context (e.g., main model fields in embedded views)"""
        context_issues = []
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Look for One2many/Many2many fields with embedded views
            for record in root.findall(".//record[@model='ir.ui.view']"):
                model_field = record.find("field[@name='model']")
                if model_field is None:
                    continue
                    
                main_model = model_field.text or model_field.get('eval', '').strip('\'"')
                
                # Find embedded tree/form views within field definitions
                arch_field = record.find("field[@name='arch']")
                if arch_field is not None:
                    # Look for field elements with One2many/Many2many that have embedded views
                    for field_elem in arch_field.findall('.//field[@name]'):
                        field_name = field_elem.get('name')
                        
                        # Check if this field has embedded list/form views
                        embedded_lists = field_elem.findall('.//list')
                        embedded_forms = field_elem.findall('.//form')
                        
                        if embedded_lists or embedded_forms:
                            # This is likely a relational field with embedded views
                            # Check if the embedded views reference fields that don't exist in the related model
                            related_model = self._get_related_model_name(main_model, field_name)
                            
                            if related_model:
                                # Check fields in embedded views
                                for embedded_view in embedded_lists + embedded_forms:
                                    embedded_issues = self.validate_view_fields(embedded_view, related_model, filepath)
                                    for issue in embedded_issues:
                                        issue['context'] = f'Embedded view for field {field_name} (model: {related_model})'
                                        issue['suggestion'] = f'Field exists in {main_model} but not in {related_model}. Consider adding alias field or changing reference.'
                                    context_issues.extend(embedded_issues)
        
        except Exception as e:
            pass
            
        return context_issues

    def _get_related_model_name(self, main_model, field_name):
        """Get the related model name for a relational field"""
        # Map common field patterns to their likely related models
        field_to_model_map = {
            'line_ids': f'{main_model}.line',
            'item_ids': f'{main_model}.item', 
            'detail_ids': f'{main_model}.detail',
        }
        
        if field_name in field_to_model_map:
            return field_to_model_map[field_name]
            
        # Try to find the model by examining the Python model file
        model_file_patterns = [
            f"records_management/models/{main_model.replace('.', '_')}.py",
            f"models/{main_model.replace('.', '_')}.py"
        ]
        
        for pattern in model_file_patterns:
            model_path = Path(pattern)
            if model_path.exists():
                try:
                    with open(model_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for field definition with comodel_name
                    field_pattern = rf'{field_name}\s*=\s*fields\.(One2many|Many2many)\([^)]*comodel_name=[\'"]([^\'"]+)[\'"]'
                    match = re.search(field_pattern, content)
                    if match:
                        return match.group(2)
                except Exception:
                    pass
                break
                
        return None

    def validate_xml_file(self, filepath):
        """Validate a single XML file for action issues"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            file_issues = []
            changes_made = False
            
            # Find all ir.actions.act_window records
            for record in root.findall(".//record[@model='ir.actions.act_window']"):
                action_id = record.get('id', 'unknown')
                
                # Check for deprecated fields
                for field in record.findall('field'):
                    field_name = field.get('name')
                    
                    if field_name and field_name not in self.valid_act_window_fields:
                        if field_name in self.deprecated_fields:
                            field_value = field.get('eval', field.text or '')
                            dep_info = self.deprecated_fields[field_name]
                            
                            issue = {
                                'file': filepath,
                                'record_id': action_id,
                                'field': field_name,
                                'value': field_value,
                                'reason': dep_info['reason'],
                                'alternative': dep_info['alternative'],
                                'related_model': dep_info['related_model'],
                                'action': 'remove'
                            }
                            file_issues.append(issue)
                            
                            # Add helpful comment
                            if field_name == 'sequence':
                                comment = ET.Comment(f' Sequence {field_value} should be moved to menuitem - belongs in {dep_info["related_model"]} ')
                                record.insert(0, comment)
                            
                            # Remove deprecated field
                            record.remove(field)
                            changes_made = True
                            
                        else:
                            issue = {
                                'file': filepath,
                                'record_id': action_id,
                                'field': field_name,
                                'reason': 'Unknown field for ir.actions.act_window',
                                'action': 'manual_review'
                            }
                            file_issues.append(issue)
                
                # Validate action functionality
                functionality_issues = self.validate_action_functionality(record, action_id, filepath)
                file_issues.extend(functionality_issues)
            
            # Find and validate ir.ui.view records
            for record in root.findall(".//record[@model='ir.ui.view']"):
                view_id = record.get('id', 'unknown')
                
                # Get the model this view is for
                model_field = record.find("field[@name='model']")
                if model_field is not None:
                    model_name = model_field.text or model_field.get('eval', '').strip('\'"')
                    
                    # Get the arch content
                    arch_field = record.find("field[@name='arch']")
                    if arch_field is not None:
                        # Parse the arch XML content
                        try:
                            # Handle arch content that might be in different formats
                            arch_content = arch_field.text or ''
                            if not arch_content:
                                # Look for XML children in arch field
                                for child in arch_field:
                                    arch_content = ET.tostring(child, encoding='unicode')
                                    break
                            
                            if arch_content:
                                # Parse arch content as XML
                                arch_root = ET.fromstring(f"<root>{arch_content}</root>")
                                
                                # Validate fields in this view
                                view_issues = self.validate_view_fields(arch_root, model_name, filepath)
                                file_issues.extend(view_issues)
                                
                        except ET.ParseError:
                            # If arch content can't be parsed, try to validate direct children
                            view_issues = self.validate_view_fields(arch_field, model_name, filepath)
                            file_issues.extend(view_issues)
            
            # Additional validation for field context issues (embedded view field mismatches)
            context_issues = self.validate_field_context_issues(filepath)
            file_issues.extend(context_issues)
            
            # Save changes if any were made
            if changes_made:
                self._format_xml(root)
                tree.write(filepath, encoding='utf-8', xml_declaration=True)
                print(f"✅ Fixed issues in {filepath}")
            
            if file_issues:
                self.issues_found.extend(file_issues)
                
            return file_issues
            
        except ET.ParseError as e:
            print(f"❌ XML Parse Error in {filepath}: {e}")
            return []
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            return []

    def _format_xml(self, root):
        """Format XML with proper indentation"""
        def indent(elem, level=0):
            i = "\n" + level * "    "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "    "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    indent(elem, level + 1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i
        
        indent(root)

    def check_builtin_alternatives(self, directory):
        """Check if custom actions could be replaced with Odoo built-ins"""
        print("\n🔍 Checking for built-in Odoo alternatives...")
        
        alternatives_found = []
        
        for action_id, model in self.action_model_map.items():
            # Check if this is a simple CRUD action that could use defaults
            model_caps = self.model_capabilities.get(model, set())
            
            if 'has_sequence_field' in model_caps:
                alternatives_found.append({
                    'action': action_id,
                    'model': model,
                    'suggestion': f'Model {model} has sequence field - consider using built-in list sorting',
                    'alternative': 'Use default_order in model or orderBy in view'
                })
                
            if 'has_state_field' in model_caps:
                alternatives_found.append({
                    'action': action_id,
                    'model': model,
                    'suggestion': f'Model {model} has state field - consider using built-in state filters',
                    'alternative': 'Use default search filters or kanban states'
                })
        
        self.suggestions.extend(alternatives_found)
        return alternatives_found

    def validate_directory(self, directory):
        """Validate all XML files in a directory"""
        print(f"🚀 Starting Comprehensive Action Validation in: {directory}")
        
        # First analyze model capabilities
        self.analyze_model_capabilities(directory)
        
        # Then validate actions
        records_mgmt_path = Path(directory) / 'records_management' / 'views'
        
        if not records_mgmt_path.exists():
            print(f"❌ Directory not found: {records_mgmt_path}")
            return
        
        xml_files = list(records_mgmt_path.glob('*.xml'))
        print(f"🔍 Scanning {len(xml_files)} XML files for action issues...")
        
        total_issues = 0
        for xml_file in xml_files:
            issues = self.validate_xml_file(xml_file)
            total_issues += len(issues)
        
        # Check for built-in alternatives
        self.check_builtin_alternatives(directory)
        
        # Validate menu relationships
        self.validate_menu_action_relationships(directory)
            
        self._print_comprehensive_summary(total_issues)

    def validate_menu_action_relationships(self, directory):
        """Validate that menus have proper sequence when actions don't"""
        records_path = Path(directory) / 'records_management' / 'views'
        
        if not records_path.exists():
            return
            
        print("\n🔍 Validating Menu-Action Relationships:")
        
        action_to_menu = {}
        missing_sequences = []
        
        for xml_file in records_path.glob('*.xml'):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                for menuitem in root.findall(".//menuitem"):
                    action = menuitem.get('action')
                    sequence = menuitem.get('sequence')
                    menu_id = menuitem.get('id', 'unknown')
                    
                    if action:
                        action_to_menu[action] = {
                            'menu_id': menu_id,
                            'sequence': sequence,
                            'file': xml_file.name
                        }
                        
                        if not sequence:
                            missing_sequences.append({
                                'file': xml_file.name,
                                'menu_id': menu_id,
                                'action': action
                            })
                            
            except Exception as e:
                continue
        
        if missing_sequences:
            print(f"⚠️  Found {len(missing_sequences)} menus without sequence:")
            for item in missing_sequences[:5]:
                print(f"   📄 {item['file']} -> {item['menu_id']} (action: {item['action']})")
                
        print(f"✅ Found {len(action_to_menu)} menu-action relationships")
        return action_to_menu

    def _print_comprehensive_summary(self, total_issues):
        """Print comprehensive validation summary"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE ACTION VALIDATION SUMMARY")
        print("="*80)
        
        print(f"📁 Files processed: {len(self.action_model_map)}")
        print(f"🎬 Actions analyzed: {len(self.action_model_map)}")
        print(f"📊 Models found: {len(self.model_capabilities)}")
        print(f"🐛 Issues found: {total_issues}")
        print(f"💡 Suggestions: {len(self.suggestions)}")
        
        if self.issues_found:
            print("\n📋 ISSUES BY TYPE:")
            
            by_type = defaultdict(list)
            for issue in self.issues_found:
                issue_type = issue.get('type', 'field_error')
                by_type[issue_type].append(issue)
            
            for issue_type, issues in by_type.items():
                print(f"\n❌ {issue_type.replace('_', ' ').title()}: {len(issues)}")
                for issue in issues[:3]:
                    if 'file' in issue:
                        print(f"   📄 {Path(issue['file']).name} -> {issue.get('record_id', 'unknown')}")
                    print(f"   💡 {issue.get('reason', issue.get('message', 'No details'))}")
                    if 'alternative' in issue:
                        print(f"   🔧 Fix: {issue['alternative']}")
                if len(issues) > 3:
                    print(f"   ... and {len(issues) - 3} more")
        
        if self.suggestions:
            print("\n💡 OPTIMIZATION SUGGESTIONS:")
            for suggestion in self.suggestions[:5]:
                print(f"   🎯 {suggestion['action']} ({suggestion['model']})")
                print(f"   💭 {suggestion['suggestion']}")
                print(f"   🔧 {suggestion['alternative']}")
        
        print("\n✅ Comprehensive validation complete!")

def main():
    """Main execution function"""
    validator = ComprehensiveActionValidator()
    current_dir = os.getcwd()
    validator.validate_directory(current_dir)

if __name__ == "__main__":
    main()
