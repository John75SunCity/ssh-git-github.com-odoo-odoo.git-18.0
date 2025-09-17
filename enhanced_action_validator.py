#!/usr/bin/env python3
"""
Enhanced Action Validator for Odoo 18
Validates and fixes invalid fields in ir.actions.act_window definitions
"""

import os
import xml.etree.ElementTree as ET
import re
from pathlib import Path

class ActionValidator:
    def __init__(self):
        # Valid fields for ir.actions.act_window in Odoo 18
        self.valid_act_window_fields = {
            'name', 'res_model', 'view_mode', 'views', 'domain', 'context',
            'target', 'res_id', 'search_view_id', 'limit', 'help', 'type',
            'view_id', 'view_ids', 'auto_search', 'filter', 'binding_model_id',
            'binding_type', 'binding_view_types'
        }
        
        # Fields that were valid in older versions but not in Odoo 18
        self.deprecated_fields = {
            'sequence': 'Use menuitem sequence="X" instead of action sequence - sequence belongs in ir.ui.menu',
            'priority': 'No longer supported in Odoo 18 - use menu sequence instead',
            'groups_id': 'Use menuitem groups="group1,group2" instead of action groups',
            'auto_refresh': 'No longer supported in Odoo 18',
            'usage': 'Deprecated field - not used in Odoo 18'
        }
        
        # Alternative patterns for common fixes
        self.fix_suggestions = {
            'sequence': {
                'pattern': r'<field name="sequence" eval="(\d+)"/>',
                'replacement': '<!-- Move sequence to menuitem: sequence="{value}" -->',
                'explanation': 'Sequence should be defined in the menuitem that references this action'
            }
        }
        
        self.issues_found = []
        self.files_processed = []

    def validate_xml_file(self, filepath):
        """Validate a single XML file for action issues"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            file_issues = []
            changes_made = False
            
            # Find all ir.actions.act_window records
            for record in root.findall(".//record[@model='ir.actions.act_window']"):
                record_id = record.get('id', 'unknown')
                
                # Check each field in the record
                for field in record.findall('field'):
                    field_name = field.get('name')
                    
                    if field_name and field_name not in self.valid_act_window_fields:
                        if field_name in self.deprecated_fields:
                            field_value = field.get('eval', field.text or '')
                            
                            issue = {
                                'file': filepath,
                                'record_id': record_id,
                                'field': field_name,
                                'value': field_value,
                                'reason': self.deprecated_fields[field_name],
                                'action': 'remove'
                            }
                            file_issues.append(issue)
                            
                            # Add a helpful comment before removing
                            if field_name == 'sequence':
                                comment = ET.Comment(f' Sequence {field_value} moved to menuitem - sequence belongs in ir.ui.menu, not ir.actions.act_window ')
                                record.insert(0, comment)
                            
                            # Remove the deprecated field
                            record.remove(field)
                            changes_made = True
                            
                        else:
                            issue = {
                                'file': filepath,
                                'record_id': record_id,
                                'field': field_name,
                                'reason': 'Unknown field for ir.actions.act_window',
                                'action': 'manual_review'
                            }
                            file_issues.append(issue)
            
            # Save changes if any were made
            if changes_made:
                # Format the XML nicely
                self._format_xml(root)
                tree.write(filepath, encoding='utf-8', xml_declaration=True)
                print(f"✅ Fixed issues in {filepath}")
            
            if file_issues:
                self.issues_found.extend(file_issues)
                
            self.files_processed.append(filepath)
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
                
                # Find all menuitem elements
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

    def validate_directory(self, directory):
        """Validate all XML files in a directory"""
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
            
        # Also validate menu relationships
        self.validate_menu_action_relationships(directory)
            
        self._print_summary(total_issues)

    def _print_summary(self, total_issues):
        """Print validation summary"""
        print("\n" + "="*80)
        print("🎯 ENHANCED ACTION VALIDATION SUMMARY")
        print("="*80)
        
        print(f"📁 Files processed: {len(self.files_processed)}")
        print(f"🐛 Total issues found: {total_issues}")
        
        if self.issues_found:
            print("\n📋 DETAILED ISSUES:")
            
            # Group by issue type
            by_field = {}
            for issue in self.issues_found:
                field = issue['field']
                if field not in by_field:
                    by_field[field] = []
                by_field[field].append(issue)
            
            for field, issues in by_field.items():
                print(f"\n❌ Field '{field}' issues: {len(issues)}")
                for issue in issues[:3]:  # Show first 3 examples
                    print(f"   📄 {Path(issue['file']).name} -> {issue['record_id']}")
                    print(f"   💡 {issue['reason']}")
                    if 'value' in issue and issue['value']:
                        print(f"   🔧 Value was: {issue['value']}")
                if len(issues) > 3:
                    print(f"   ... and {len(issues) - 3} more files")
        
        print("\n✅ Validation complete!")

def main():
    """Main execution function"""
    validator = ActionValidator()
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"🚀 Starting Enhanced Action Validation in: {current_dir}")
    
    validator.validate_directory(current_dir)
    
    # Also check for other common action issues
    print("\n🔍 Additional Action Validation Checks:")
    
    # Check for sequence fields in other action types
    records_path = Path(current_dir) / 'records_management' / 'views'
    if records_path.exists():
        sequence_pattern = re.compile(r'<field\s+name="sequence".*?model="ir\.actions\.')
        for xml_file in records_path.glob('*.xml'):
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if sequence_pattern.search(content):
                        print(f"⚠️  Found sequence field in action: {xml_file.name}")
            except Exception as e:
                print(f"❌ Error reading {xml_file}: {e}")

if __name__ == "__main__":
    main()
