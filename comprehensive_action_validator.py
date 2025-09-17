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
