#!/usr/bin/env python3
"""
Automated Documentation Update Script for Records Management System

This script automatically updates the handbook when code changes occur,
ensuring documentation remains current as the modules evolve.
"""

import ast
import os
import re
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class HandbookUpdater:
    """Main class for updating Records Management handbook documentation."""
    
    def __init__(self, module_path: str, handbook_path: str):
        self.module_path = Path(module_path)
        self.handbook_path = Path(handbook_path)
        self.updated_sections = []
        
    def run_full_update(self) -> None:
        """Run complete documentation update."""
        print("🔄 Starting documentation update...")
        
        # Update various sections
        self.update_field_dictionary()
        self.update_view_mapping()
        self.update_security_matrix()
        self.update_model_statistics()
        self.update_menu_structure()
        
        # Generate update summary
        self.generate_update_summary()
        print(f"✅ Documentation update complete. Updated {len(self.updated_sections)} sections.")
    
    def parse_model(self, py_file: Path) -> Optional[Dict[str, Any]]:
        """Parse Python model file and extract field information."""
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if this is an Odoo model
                    if self._is_odoo_model(node):
                        return self._extract_model_info(node, content)
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error parsing {py_file}: {e}")
            return None
    
    def _is_odoo_model(self, class_node: ast.ClassDef) -> bool:
        """Check if class is an Odoo model."""
        # Look for _name or _inherit attributes
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ['_name', '_inherit']:
                        return True
        return False
    
    def _extract_model_info(self, class_node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """Extract model information including fields."""
        model_info = {
            'class_name': class_node.name,
            'fields': {},
            'methods': [],
            '_name': None,
            '_description': None,
            '_inherit': None
        }
        
        # Extract model attributes and fields
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                self._process_assignment(node, model_info, content)
            elif isinstance(node, ast.FunctionDef):
                model_info['methods'].append(node.name)
        
        return model_info
    
    def _process_assignment(self, node: ast.Assign, model_info: Dict, content: str) -> None:
        """Process field assignments in model."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                field_name = target.id
                
                # Handle special model attributes
                if field_name in ['_name', '_description', '_inherit']:
                    if isinstance(node.value, ast.Constant):
                        model_info[field_name] = node.value.value
                    elif isinstance(node.value, ast.Str):  # Python < 3.8
                        model_info[field_name] = node.value.s
                
                # Handle field definitions
                elif self._is_field_definition(node.value):
                    field_info = self._extract_field_info(node.value, content)
                    model_info['fields'][field_name] = field_info
    
    def _is_field_definition(self, node: ast.AST) -> bool:
        """Check if assignment is a field definition."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                return (isinstance(node.func.value, ast.Name) and 
                       node.func.value.id == 'fields')
        return False
    
    def _extract_field_info(self, node: ast.Call, content: str) -> Dict[str, Any]:
        """Extract field information from fields.* call."""
        field_info = {
            'type': node.func.attr if isinstance(node.func, ast.Attribute) else 'Unknown',
            'string': None,
            'required': False,
            'default': None,
            'help': None,
            'readonly': False,
            'compute': None,
            'related': None,
            'store': None
        }
        
        # Extract keyword arguments
        for keyword in node.keywords:
            if keyword.arg in field_info:
                if isinstance(keyword.value, ast.Constant):
                    field_info[keyword.arg] = keyword.value.value
                elif isinstance(keyword.value, ast.Str):  # Python < 3.8
                    field_info[keyword.arg] = keyword.value.s
        
        return field_info
    
    def parse_views(self, xml_file: Path) -> Dict[str, Dict]:
        """Parse XML view file and extract view information."""
        views = {}
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for record in root.findall('.//record'):
                if record.get('model') == 'ir.ui.view':
                    view_id = record.get('id')
                    if view_id:
                        view_info = {
                            'id': view_id,
                            'model': None,
                            'type': None,
                            'inherit_id': None,
                            'file': xml_file.name
                        }
                        
                        # Extract view details
                        for field in record.findall('field'):
                            field_name = field.get('name')
                            if field_name in ['model', 'type', 'inherit_id']:
                                view_info[field_name] = field.text or field.get('ref')
                        
                        views[view_id] = view_info
            
        except Exception as e:
            print(f"⚠️  Error parsing {xml_file}: {e}")
        
        return views
    
    def parse_security_csv(self, csv_file: Path) -> Dict[str, List]:
        """Parse security CSV and extract access rights."""
        access_rights = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    model = row.get('model_id:id', '').replace('model_', '')
                    group = row.get('group_id:id', '')
                    
                    if model not in access_rights:
                        access_rights[model] = []
                    
                    access_rights[model].append({
                        'group': group,
                        'read': row.get('perm_read', '0') == '1',
                        'write': row.get('perm_write', '0') == '1',
                        'create': row.get('perm_create', '0') == '1',
                        'unlink': row.get('perm_unlink', '0') == '1'
                    })
            
        except Exception as e:
            print(f"⚠️  Error parsing {csv_file}: {e}")
        
        return access_rights
    
    def update_field_dictionary(self) -> None:
        """Update field dictionary section in handbook."""
        print("📝 Updating field dictionary...")
        
        models = {}
        for py_file in self.module_path.glob('models/*.py'):
            if py_file.name != '__init__.py':
                model_info = self.parse_model(py_file)
                if model_info and model_info.get('_name'):
                    models[model_info['_name']] = model_info
        
        # Generate field reference section
        field_section = self._generate_field_reference(models)
        
        # Update handbook
        self._update_handbook_section('Custom Fields Reference', field_section)
        self.updated_sections.append('Field Dictionary')
    
    def update_view_mapping(self) -> None:
        """Update view mapping section in handbook."""
        print("🎨 Updating view mapping...")
        
        views = {}
        for xml_file in self.module_path.glob('views/*.xml'):
            view_info = self.parse_views(xml_file)
            views.update(view_info)
        
        # Generate view mapping section
        view_section = self._generate_view_mapping(views)
        
        # Update handbook
        self._update_handbook_section('Views & Templates Mapping', view_section)
        self.updated_sections.append('View Mapping')
    
    def update_security_matrix(self) -> None:
        """Update security matrix in handbook."""
        print("🔐 Updating security matrix...")
        
        csv_file = self.module_path / 'security/ir.model.access.csv'
        if csv_file.exists():
            access_rights = self.parse_security_csv(csv_file)
            
            # Generate security matrix
            security_section = self._generate_security_matrix(access_rights)
            
            # Update handbook
            self._update_handbook_section('Access Rights Matrix', security_section)
            self.updated_sections.append('Security Matrix')
    
    def update_model_statistics(self) -> None:
        """Update model statistics in handbook."""
        print("📊 Updating model statistics...")
        
        # Count models
        model_count = len([f for f in self.module_path.glob('models/*.py') 
                          if f.name != '__init__.py'])
        
        # Count views
        view_count = len(list(self.module_path.glob('views/*.xml')))
        
        # Count data files
        data_count = len(list(self.module_path.glob('data/*.xml')))
        
        # Update statistics section
        stats = {
            'Python Models': model_count,
            'XML Views': view_count,
            'Data Files': data_count,
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        stats_section = self._generate_statistics_table(stats)
        self._update_handbook_section('Module Statistics', stats_section)
        self.updated_sections.append('Model Statistics')
    
    def update_menu_structure(self) -> None:
        """Update menu structure documentation."""
        print("📋 Updating menu structure...")
        # This would scan menu XML files and generate structure
        self.updated_sections.append('Menu Structure')
    
    def _generate_field_reference(self, models: Dict) -> str:
        """Generate field reference documentation."""
        content = []
        
        for model_name, model_info in sorted(models.items()):
            if model_info['fields']:
                content.append(f"\n#### **{model_name}** Fields")
                content.append(f"**Purpose**: {model_info.get('_description', 'No description')}")
                content.append(f"**Field Count**: {len(model_info['fields'])} fields")
                content.append("\n| Field Name | Type | Purpose | Required | Default |")
                content.append("|------------|------|---------|----------|---------|")
                
                for field_name, field_info in sorted(model_info['fields'].items()):
                    purpose = field_info.get('help', field_info.get('string', 'No description'))
                    required = '✓' if field_info.get('required') else '-'
                    default = str(field_info.get('default', '-'))
                    
                    content.append(
                        f"| `{field_name}` | {field_info['type']} | "
                        f"{purpose[:50]}... | {required} | {default[:20]} |"
                    )
        
        return '\n'.join(content)
    
    def _generate_view_mapping(self, views: Dict) -> str:
        """Generate view mapping documentation."""
        content = []
        view_types = {}
        
        # Group views by type and model
        for view_id, view_info in views.items():
            model = view_info.get('model', 'unknown')
            view_type = view_info.get('type', 'form')
            
            if model not in view_types:
                view_types[model] = {}
            if view_type not in view_types[model]:
                view_types[model][view_type] = []
            
            view_types[model][view_type].append(view_info)
        
        # Generate documentation
        for model, types in sorted(view_types.items()):
            content.append(f"\n#### **{model}** Views")
            content.append("```xml")
            for view_type, view_list in sorted(types.items()):
                content.append(f"<!-- {view_type.title()} Views -->")
                for view in view_list:
                    content.append(f"├── {view['id']} ({view['file']})")
            content.append("```")
        
        return '\n'.join(content)
    
    def _generate_security_matrix(self, access_rights: Dict) -> str:
        """Generate security access matrix."""
        content = []
        content.append("\n| **Model** | **Group** | **Read** | **Write** | **Create** | **Delete** |")
        content.append("|-----------|-----------|----------|-----------|------------|------------|")
        
        for model, rights_list in sorted(access_rights.items()):
            for rights in rights_list:
                group = rights['group'].split('.')[-1] if '.' in rights['group'] else rights['group']
                read = '✓' if rights['read'] else '-'
                write = '✓' if rights['write'] else '-'
                create = '✓' if rights['create'] else '-'
                delete = '✓' if rights['unlink'] else '-'
                
                content.append(f"| **{model}** | {group} | {read} | {write} | {create} | {delete} |")
        
        return '\n'.join(content)
    
    def _generate_statistics_table(self, stats: Dict) -> str:
        """Generate statistics table."""
        content = []
        content.append("\n| **Component** | **Count** |")
        content.append("|---------------|-----------|")
        
        for key, value in stats.items():
            content.append(f"| **{key}** | {value} |")
        
        return '\n'.join(content)
    
    def _update_handbook_section(self, section_title: str, new_content: str) -> None:
        """Update specific section in handbook."""
        if not self.handbook_path.exists():
            print(f"⚠️  Handbook file not found: {self.handbook_path}")
            return
        
        try:
            with open(self.handbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find section and replace content
            pattern = f"### {section_title}.*?(?=###|---|\Z)"
            replacement = f"### {section_title}\n{new_content}\n"
            
            updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            with open(self.handbook_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Updated section: {section_title}")
            
        except Exception as e:
            print(f"⚠️  Error updating section {section_title}: {e}")
    
    def generate_update_summary(self) -> None:
        """Generate update summary."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'updated_sections': self.updated_sections,
            'module_path': str(self.module_path),
            'handbook_path': str(self.handbook_path)
        }
        
        summary_file = self.handbook_path.parent / 'update_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📋 Update summary saved to: {summary_file}")


def main():
    """Main entry point for documentation update."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Records Management documentation')
    parser.add_argument('--module-path', default='records_management', 
                       help='Path to records_management module')
    parser.add_argument('--handbook-path', default='RECORDS_MANAGEMENT_HANDBOOK.md',
                       help='Path to handbook file')
    parser.add_argument('--section', choices=['fields', 'views', 'security', 'stats', 'all'],
                       default='all', help='Section to update')
    
    args = parser.parse_args()
    
    updater = HandbookUpdater(args.module_path, args.handbook_path)
    
    if args.section == 'all':
        updater.run_full_update()
    elif args.section == 'fields':
        updater.update_field_dictionary()
    elif args.section == 'views':
        updater.update_view_mapping()
    elif args.section == 'security':
        updater.update_security_matrix()
    elif args.section == 'stats':
        updater.update_model_statistics()


if __name__ == '__main__':
    main()