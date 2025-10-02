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
import html
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class HandbookUpdater:
    """Main class for updating Records Management handbook documentation.

    Enhancements (2025-10-02):
    - Multi-module support: --module-path accepts comma-separated module roots
    - Menu structure extraction: builds hierarchy of ir.ui.menu + linked act_window
    - Printable mode: generates a consolidated user-friendly markdown for Word
    """

    def __init__(self, module_path: str, handbook_path: str, split: bool = False,
                 split_dir: str = 'handbook', printable: bool = False, printable_dir: str = 'handbook/printable'):
        # Support comma-separated module paths
        raw_paths = [p.strip() for p in module_path.split(',') if p.strip()]
        if not raw_paths:
            raise ValueError("No valid module paths provided")
        self.module_paths: List[Path] = [Path(p) for p in raw_paths]
        self.handbook_path = Path(handbook_path)
        self.updated_sections: List[str] = []
        self.split = split
        self.split_dir = Path(split_dir)
        self.printable = printable
        self.printable_dir = Path(printable_dir)
        if self.split:
            self.split_dir.mkdir(parents=True, exist_ok=True)
        if self.printable:
            self.printable_dir.mkdir(parents=True, exist_ok=True)

    def run_full_update(self) -> None:
        """Run complete documentation update."""
        print("🔄 Starting documentation update...")
        self._ensure_handbook_skeleton()
        # Update various sections (order matters for printable readability)
        self.update_field_dictionary()
        self.update_view_mapping()
        self.update_security_matrix()
        self.update_model_statistics()
        self.update_menu_structure()

        # Generate update summary
        self.generate_update_summary()
        # Generate printable variant if requested
        if self.printable:
            self.generate_printable_version()
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

        models: Dict[str, Dict[str, Any]] = {}
        for module_path in self.module_paths:
            for py_file in module_path.glob('models/*.py'):
                if py_file.name != '__init__.py':
                    model_info = self.parse_model(py_file)
                    if model_info and model_info.get('_name'):
                        # Merge fields if model defined across modules (inheritance/ext)
                        existing = models.get(model_info['_name'])
                        if existing:
                            existing['fields'].update(model_info['fields'])
                        else:
                            models[model_info['_name']] = model_info

        # Generate field reference section
        field_section = self._generate_field_reference(models)

        # Update handbook
        self._update_handbook_section('Custom Fields Reference', field_section)
        self.updated_sections.append('Field Dictionary')

    def update_view_mapping(self) -> None:
        """Update view mapping section in handbook."""
        print("🎨 Updating view mapping...")

        views: Dict[str, Dict[str, Any]] = {}
        for module_path in self.module_paths:
            for xml_file in module_path.glob('views/*.xml'):
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

        aggregated_access: Dict[str, List] = {}
        for module_path in self.module_paths:
            csv_file = module_path / 'security/ir.model.access.csv'
            if csv_file.exists():
                access_rights = self.parse_security_csv(csv_file)
                for model, rights in access_rights.items():
                    aggregated_access.setdefault(model, []).extend(rights)
        if aggregated_access:
            security_section = self._generate_security_matrix(aggregated_access)
            self._update_handbook_section('Access Rights Matrix', security_section)
            self.updated_sections.append('Security Matrix')

    def update_model_statistics(self) -> None:
        """Update model statistics in handbook."""
        print("📊 Updating model statistics...")

        # Per-module stats then total
        combined = {
            'Python Models': 0,
            'XML Views': 0,
            'Data Files': 0,
        }
        stats_lines = ["\n### Per-Module Breakdown"]
        stats_lines.append("\n| **Module** | **Models** | **Views** | **Data Files** |")
        stats_lines.append("|-----------|-----------|----------|-------------|")
        for module_path in self.module_paths:
            model_count = len([f for f in module_path.glob('models/*.py') if f.name != '__init__.py'])
            view_count = len(list(module_path.glob('views/*.xml')))
            data_count = len(list(module_path.glob('data/*.xml')))
            combined['Python Models'] += model_count
            combined['XML Views'] += view_count
            combined['Data Files'] += data_count
            stats_lines.append(f"| {module_path.name} | {model_count} | {view_count} | {data_count} |")
        stats = {
            'Python Models (Total)': combined['Python Models'],
            'XML Views (Total)': combined['XML Views'],
            'Data Files (Total)': combined['Data Files'],
            'Modules Included': ', '.join([p.name for p in self.module_paths]),
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        stats_section = self._generate_statistics_table(stats)
        stats_full = stats_section + '\n' + '\n'.join(stats_lines)
        self._update_handbook_section('Module Statistics', stats_full)
        self.updated_sections.append('Model Statistics')

    def update_menu_structure(self) -> None:
        """Update menu structure documentation."""
        print("📋 Updating menu structure...")
        menus: Dict[str, Dict[str, Any]] = {}
        actions: Dict[str, Dict[str, Any]] = {}
        # Parse all view XMLs for menus & actions
        for module_path in self.module_paths:
            for xml_file in module_path.glob('views/*.xml'):
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    # 1. <record model="ir.ui.menu"> style (classic)
                    for record in root.findall('.//record'):
                        model_attr = record.get('model')
                        rec_id = record.get('id')
                        if not rec_id or not model_attr:
                            continue
                        if model_attr == 'ir.ui.menu':
                            menu_data = {'id': rec_id, 'name': None, 'parent_id': None, 'action': None, 'file': xml_file.name}
                            for field in record.findall('field'):
                                fname = field.get('name')
                                if fname == 'name':
                                    menu_data['name'] = (field.text or '').strip()
                                elif fname == 'parent_id':
                                    # parent via ref attr or text
                                    parent_ref = field.get('ref') or (field.text or '').strip()
                                    menu_data['parent_id'] = parent_ref
                                elif fname == 'action':
                                    action_ref = field.get('ref') or (field.text or '').strip()
                                    menu_data['action'] = action_ref
                            menus[rec_id] = menu_data
                        elif model_attr == 'ir.actions.act_window':
                            action_data = {'id': rec_id, 'name': None, 'res_model': None, 'view_mode': None, 'file': xml_file.name}
                            for field in record.findall('field'):
                                fname = field.get('name')
                                if fname == 'name':
                                    action_data['name'] = (field.text or '').strip()
                                elif fname == 'res_model':
                                    action_data['res_model'] = (field.text or '').strip()
                                elif fname == 'view_mode':
                                    action_data['view_mode'] = (field.text or '').strip()
                            actions[rec_id] = action_data

                    # 2. <menuitem .../> shorthand style (common in Odoo menus)
                    for mi in root.findall('.//menuitem'):
                        rec_id = mi.get('id')
                        if not rec_id:
                            continue
                        name_raw = mi.get('name') or ''
                        # Unescape HTML entities then strip <i ...> icon tags
                        name_unescaped = html.unescape(name_raw)
                        name_clean = re.sub(r'<i[^>]*></i>|<i[^>]*/?>', '', name_unescaped, flags=re.IGNORECASE).strip()
                        parent_ref = mi.get('parent')
                        action_ref = mi.get('action')
                        # Only create / update if not already defined via <record>
                        if rec_id not in menus:
                            menus[rec_id] = {
                                'id': rec_id,
                                'name': name_clean or name_unescaped or '(No Name)',
                                'parent_id': parent_ref,
                                'action': action_ref,
                                'file': xml_file.name
                            }
                        else:
                            # Augment missing data if needed
                            if not menus[rec_id].get('name'):
                                menus[rec_id]['name'] = name_clean or name_unescaped
                            if not menus[rec_id].get('parent_id') and parent_ref:
                                menus[rec_id]['parent_id'] = parent_ref
                            if not menus[rec_id].get('action') and action_ref:
                                menus[rec_id]['action'] = action_ref
                except Exception as e:
                    print(f"⚠️  Error parsing for menus/actions in {xml_file}: {e}")

        if not menus:
            self._update_handbook_section('Menu Structure', '_No menus detected in provided modules._')
            self.updated_sections.append('Menu Structure')
            return

        menu_section = self._generate_menu_structure(menus, actions)
        self._update_handbook_section('Menu Structure', menu_section)
        self.updated_sections.append('Menu Structure')

    def _generate_menu_structure(self, menus: Dict[str, Dict[str, Any]], actions: Dict[str, Dict[str, Any]]) -> str:
        """Build hierarchical menu markdown."""
        # Build node graph
        nodes = {}
        for mid, m in menus.items():
            nodes[mid] = {**m, 'children': []}
        # Attach children
        for mid, m in nodes.items():
            parent = m.get('parent_id')
            if parent and parent in nodes:
                nodes[parent]['children'].append(m)

        # Identify roots
        roots = [n for n in nodes.values() if not n.get('parent_id') or n.get('parent_id') not in nodes]
        # Sort recursively
        def sort_children(node):
            node['children'].sort(key=lambda c: (c.get('name') or '').lower())
            for ch in node['children']:
                sort_children(ch)
        for r in roots:
            sort_children(r)

        lines = ["_Menu hierarchy generated from ir.ui.menu and ir.actions.act_window records._", ""]

        def render(node, depth=0):
            indent = '  ' * depth
            name = node.get('name') or '(No Name)'
            line = f"{indent}- {name}  (`{node['id']}`)"
            action_id = node.get('action')
            if action_id and action_id in actions:
                act = actions[action_id]
                ameta = f" → {act.get('name','(no title)')} [{act.get('res_model') or '?'}]"
                if act.get('view_mode'):
                    ameta += f" modes={act['view_mode']}"
                line += ameta
            lines.append(line)
            for ch in node['children']:
                render(ch, depth+1)

        for root in sorted(roots, key=lambda r: (r.get('name') or '').lower()):
            render(root)
        return '\n'.join(lines)

    def generate_printable_version(self) -> None:
        """Generate a consolidated printable markdown suitable for Word import."""
        try:
            if not self.handbook_path.exists():
                return
            with open(self.handbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Collect section anchors
            headings = re.findall(r'^### (.+)$', content, flags=re.MULTILINE)
            toc_lines = ["# Records Management Handbook (Printable Edition)", "", "## Table of Contents"]
            for h in headings:
                anchor = re.sub(r'[^a-z0-9]+', '-', h.lower()).strip('-')
                toc_lines.append(f"- [{h}](#{anchor})")
            # Attempt to include Quick Start Guide if present
            quick_start_path = self.split_dir / 'quick-start-guide.md'
            quick_start_content = ''
            if quick_start_path.exists():
                try:
                    with open(quick_start_path, 'r', encoding='utf-8') as qf:
                        quick_start_raw = qf.read().strip()
                    quick_start_content = f"\n\n---\n\n{quick_start_raw}\n\n---\n"
                    # Add link at top of TOC
                    toc_lines.insert(3, '- [Quick Start Guide](#quick-start-guide---records-management-system)')
                except Exception as qe:
                    print(f"⚠️  Failed to embed Quick Start Guide: {qe}")
            # Add page breaks before each major section (replace '### ' with page break + heading)
            printable = re.sub(r'^### ', '\n\n---\n\n### ', content, flags=re.MULTILINE)
            output = '\n'.join(toc_lines) + quick_start_content + '\n' + printable
            target = self.printable_dir / 'records_management_handbook_printable.md'
            with open(target, 'w', encoding='utf-8') as pf:
                pf.write(output)
            print(f"🖨  Generated printable handbook: {target}")
        except Exception as e:
            print(f"⚠️  Failed generating printable version: {e}")

    def _generate_field_reference(self, models: Dict) -> str:
        """Generate field reference documentation."""
        content = []

        def _truncate(val: str, limit: int) -> str:
            if val is None:
                return ''
            val = str(val)
            return val if len(val) <= limit else val[:limit] + '…'

        for model_name, model_info in sorted(models.items()):
            if model_info['fields']:
                content.append(f"\n#### **{model_name}** Fields")
                content.append(f"**Purpose**: {model_info.get('_description', 'No description')}")
                content.append(f"**Field Count**: {len(model_info['fields'])} fields")
                content.append("\n| Field Name | Type | Purpose | Required | Default |")
                content.append("|------------|------|---------|----------|---------|")

                for field_name, field_info in sorted(model_info['fields'].items()):
                    purpose = field_info.get('help') or field_info.get('string') or 'No description'
                    required = '✓' if field_info.get('required') else '-'
                    default_val = field_info.get('default', '-')
                    content.append(
                        f"| `{field_name}` | {field_info['type']} | "
                        f"{_truncate(purpose,50)} | {required} | {_truncate(default_val,20)} |"
                    )

        return '\n'.join(content)

    def _generate_view_mapping(self, views: Dict) -> str:
        """Generate view mapping documentation."""
        content = []
        view_types = {}

        # Group views by type and model
        for view_id, view_info in views.items():
            model = view_info.get('model') or 'unknown'
            view_type = view_info.get('type') or 'form'

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
                safe_label = view_type.title() if isinstance(view_type, str) else 'View'
                content.append(f"<!-- {safe_label} Views -->")
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
            print(f"⚠️  Handbook file not found (creating skeleton): {self.handbook_path}")
            self._ensure_handbook_skeleton()

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

            # If split mode, also write individual section file
            if self.split:
                filename = section_title.lower().replace('&', 'and').replace(' ', '-').replace('/', '-')
                target = self.split_dir / f"{filename}.md"
                with open(target, 'w', encoding='utf-8') as sf:
                    sf.write(f"# {section_title}\n\n{new_content}\n")
                print(f"🗂  Wrote split section file: {target}")

        except Exception as e:
            print(f"⚠️  Error updating section {section_title}: {e}")

    def generate_update_summary(self) -> None:
        """Generate update summary."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'updated_sections': self.updated_sections,
            'module_paths': [str(p) for p in self.module_paths],
            'handbook_path': str(self.handbook_path),
            'printable': self.printable
        }

        summary_file = self.handbook_path.parent / 'update_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"📋 Update summary saved to: {summary_file}")

    def _ensure_handbook_skeleton(self) -> None:
        """Create a base handbook file with placeholder section headers if missing."""
        if self.handbook_path.exists():
            return
        skeleton_sections = [
            'Custom Fields Reference',
            'Views & Templates Mapping',
            'Access Rights Matrix',
            'Module Statistics',
            'Menu Structure'
        ]
        lines = ["# Records Management Handbook (Auto-Generated)\n",
                 "Generated file – sections are updated automatically. Do not edit section bodies manually; add custom notes outside section markers.\n"]
        for s in skeleton_sections:
            lines.append(f"\n### {s}\n\n_Placeholder – will be populated on update._\n")
        with open(self.handbook_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"🆕 Created handbook skeleton at {self.handbook_path}")


def main():
    """Main entry point for documentation update."""
    import argparse

    parser = argparse.ArgumentParser(description='Update Records Management documentation')
    parser.add_argument('--module-path', default='records_management',
                       help='Path(s) to module(s). Comma-separated for multiple (e.g. records_management,records_management_fsm)')
    parser.add_argument('--handbook-path', default='RECORDS_MANAGEMENT_HANDBOOK.md',
                       help='Path to handbook file')
    parser.add_argument('--section', choices=['fields', 'views', 'security', 'stats', 'all'],
                       default='all', help='Section to update')
    parser.add_argument('--split', action='store_true', help='Also write each section to handbook/ directory')
    parser.add_argument('--printable', action='store_true', help='Generate printable consolidated handbook version')

    args = parser.parse_args()

    updater = HandbookUpdater(args.module_path, args.handbook_path, split=args.split, printable=args.printable)

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
    # In non-all mode, still allow printable generation if flag passed
    if args.section != 'all' and args.printable:
        updater.generate_printable_version()


if __name__ == '__main__':
    main()
