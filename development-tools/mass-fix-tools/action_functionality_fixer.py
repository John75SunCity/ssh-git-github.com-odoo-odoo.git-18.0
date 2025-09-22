#!/usr/bin/env python3
"""
Action Functionality Fixer for Odoo 18
Fixes common action functionality issues and applies Odoo best practices
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

class ActionFixer:
    def __init__(self):
        self.fixes_applied = []
        
    def fix_non_wizard_new_target(self, directory):
        """Fix actions using target='new' for non-wizard models"""
        print("🔧 Fixing non-wizard target='new' actions...")
        
        records_path = Path(directory) / 'records_management' / 'views'
        fixes = []
        
        for xml_file in records_path.glob('*.xml'):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                changed = False
                
                for record in root.findall(".//record[@model='ir.actions.act_window']"):
                    action_id = record.get('id', '')
                    res_model = None
                    target_field = None
                    
                    # Get model and target info
                    for field in record.findall('field'):
                        if field.get('name') == 'res_model':
                            res_model = field.text
                        elif field.get('name') == 'target':
                            target_field = field
                    
                    # Check if target=new but not a wizard
                    if (target_field is not None and 
                        target_field.text == 'new' and 
                        res_model and 
                        'wizard' not in res_model.lower() and
                        not res_model.endswith('.wizard')):
                        
                        # Check if it's really a dialog pattern
                        view_mode = None
                        for field in record.findall('field'):
                            if field.get('name') == 'view_mode':
                                view_mode = field.text
                                break
                        
                        # If it's just form view, it might be a legitimate dialog
                        if view_mode == 'form':
                            # Add comment explaining the pattern
                            comment = ET.Comment(f' Action {action_id} uses target="new" for dialog form - verify this is intentional ')
                            record.insert(0, comment)
                        else:
                            # Change to current window
                            target_field.text = 'current'
                            changed = True
                            
                            fixes.append({
                                'file': xml_file.name,
                                'action': action_id,
                                'model': res_model,
                                'change': 'Changed target from "new" to "current"'
                            })
                
                if changed:
                    self._format_xml(root)
                    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
                    
            except Exception as e:
                print(f"❌ Error processing {xml_file}: {e}")
                
        print(f"✅ Applied {len(fixes)} target fixes")
        return fixes
    
    def add_missing_menu_sequences(self, directory):
        """Add sequence to menus that are missing them"""
        print("🔧 Adding missing menu sequences...")
        
        records_path = Path(directory) / 'records_management' / 'views'
        fixes = []
        
        for xml_file in records_path.glob('*.xml'):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                changed = False
                
                for menuitem in root.findall(".//menuitem"):
                    if not menuitem.get('sequence'):
                        menu_id = menuitem.get('id', 'unknown')
                        parent = menuitem.get('parent')
                        
                        # Assign a reasonable default sequence
                        if parent:
                            # Sub-menu, use higher sequence
                            menuitem.set('sequence', '50')
                        else:
                            # Top-level menu, use lower sequence
                            menuitem.set('sequence', '10')
                            
                        changed = True
                        fixes.append({
                            'file': xml_file.name,
                            'menu': menu_id,
                            'sequence': menuitem.get('sequence')
                        })
                
                if changed:
                    self._format_xml(root)
                    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
                    
            except Exception as e:
                continue
                
        print(f"✅ Added sequences to {len(fixes)} menus")
        return fixes
    
    def optimize_actions_with_model_capabilities(self, directory):
        """Add comments suggesting built-in alternatives for actions"""
        print("🔧 Adding optimization suggestions to actions...")
        
        # First scan models for capabilities
        models_path = Path(directory) / 'records_management' / 'models'
        model_capabilities = {}
        
        if models_path.exists():
            for py_file in models_path.glob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    model_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    
                    for model_name in model_matches:
                        capabilities = []
                        
                        if 'sequence' in content and re.search(r'sequence\s*=\s*fields\.', content):
                            capabilities.append('has_sequence_field')
                        
                        if re.search(r'_order\s*=.*sequence', content):
                            capabilities.append('has_default_order')
                            
                        if re.search(r'state\s*=\s*fields\.Selection', content):
                            capabilities.append('has_state_field')
                            
                        if capabilities:
                            model_capabilities[model_name] = capabilities
                            
                except Exception:
                    continue
        
        # Now add suggestions to actions
        records_path = Path(directory) / 'records_management' / 'views'
        suggestions = []
        
        for xml_file in records_path.glob('*.xml'):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                changed = False
                
                for record in root.findall(".//record[@model='ir.actions.act_window']"):
                    action_id = record.get('id', '')
                    res_model = None
                    
                    for field in record.findall('field'):
                        if field.get('name') == 'res_model':
                            res_model = field.text
                            break
                    
                    if res_model and res_model in model_capabilities:
                        capabilities = model_capabilities[res_model]
                        
                        # Check if we should add optimization comments
                        needs_comment = False
                        
                        if 'has_sequence_field' in capabilities and 'has_default_order' not in capabilities:
                            comment = ET.Comment(f' OPTIMIZATION: Model {res_model} has sequence field - consider adding _order="sequence" to model ')
                            record.insert(0, comment)
                            needs_comment = True
                            
                        if 'has_state_field' in capabilities:
                            comment = ET.Comment(f' OPTIMIZATION: Model {res_model} has state field - consider using default search filters ')
                            record.insert(0, comment)
                            needs_comment = True
                            
                        if needs_comment:
                            changed = True
                            suggestions.append({
                                'file': xml_file.name,
                                'action': action_id,
                                'model': res_model,
                                'capabilities': capabilities
                            })
                
                if changed:
                    self._format_xml(root)
                    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
                    
            except Exception as e:
                continue
                
        print(f"✅ Added optimization suggestions to {len(suggestions)} actions")
        return suggestions
    
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
    
    def fix_all_issues(self, directory):
        """Apply all fixes"""
        print("🚀 Applying comprehensive action fixes...")
        
        # Apply fixes
        target_fixes = self.fix_non_wizard_new_target(directory)
        menu_fixes = self.add_missing_menu_sequences(directory)
        optimization_suggestions = self.optimize_actions_with_model_capabilities(directory)
        
        # Summary
        print("\n" + "="*60)
        print("🎯 ACTION FIXES APPLIED SUMMARY")
        print("="*60)
        print(f"🔧 Target fixes: {len(target_fixes)}")
        print(f"📋 Menu sequence fixes: {len(menu_fixes)}")
        print(f"💡 Optimization suggestions: {len(optimization_suggestions)}")
        
        if target_fixes:
            print("\n🔧 Target Fixes Applied:")
            for fix in target_fixes[:5]:
                print(f"   📄 {fix['file']} -> {fix['action']} ({fix['model']})")
        
        if menu_fixes:
            print("\n📋 Menu Sequences Added:")
            for fix in menu_fixes[:5]:
                print(f"   📄 {fix['file']} -> {fix['menu']} (sequence={fix['sequence']})")
        
        print("\n✅ All fixes applied successfully!")

def main():
    import os
    fixer = ActionFixer()
    fixer.fix_all_issues(os.getcwd())

if __name__ == "__main__":
    main()
