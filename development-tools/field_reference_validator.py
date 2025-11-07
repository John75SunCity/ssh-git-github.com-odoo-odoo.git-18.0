#!/usr/bin/env python3
"""
Field Reference Validator for Odoo Views
==========================================

Validates that fields referenced in views actually exist in their models.
Parses Python model definitions to build a field registry.
"""

import re
import ast
from pathlib import Path
from typing import Dict, Set, List, Tuple
import xml.etree.ElementTree as ET


class FieldReferenceValidator:
    """Validates field references in views against model definitions"""
    
    def __init__(self):
        self.model_fields: Dict[str, Set[str]] = {}  # model_name -> set of field names
        self.issues: List[str] = []
        self._build_field_registry()
    
    def _build_field_registry(self):
        """Parse all Python model files and build field registry"""
        models_dir = Path("records_management/models")
        
        if not models_dir.exists():
            print("⚠️  Models directory not found")
            return
        
        for py_file in sorted(models_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                
                # Extract model name and fields
                self._parse_model_file(py_file, content)
            except Exception as e:
                print(f"⚠️  Could not parse {py_file}: {e}")
    
    def _parse_model_file(self, file_path: Path, content: str):
        """Parse a single model file and extract fields"""
        # Extract model name from _name = '...'
        name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if not name_match:
            return
        
        model_name = name_match.group(1)
        fields = set()
        
        # Find all field definitions: field_name = fields.Type(...)
        # This is a simple regex-based approach
        field_patterns = [
            r'(\w+)\s*=\s*fields\.Char\(',
            r'(\w+)\s*=\s*fields\.Integer\(',
            r'(\w+)\s*=\s*fields\.Float\(',
            r'(\w+)\s*=\s*fields\.Boolean\(',
            r'(\w+)\s*=\s*fields\.Date\(',
            r'(\w+)\s*=\s*fields\.DateTime\(',
            r'(\w+)\s*=\s*fields\.Text\(',
            r'(\w+)\s*=\s*fields\.Selection\(',
            r'(\w+)\s*=\s*fields\.Many2one\(',
            r'(\w+)\s*=\s*fields\.One2many\(',
            r'(\w+)\s*=\s*fields\.Many2many\(',
            r'(\w+)\s*=\s*fields\.Monetary\(',
            r'(\w+)\s*=\s*fields\.Json\(',
            r'(\w+)\s*=\s*fields\.Html\(',
            r'(\w+)\s*=\s*fields\.Image\(',
            r'(\w+)\s*=\s*fields\.Binary\(',
        ]
        
        for pattern in field_patterns:
            for match in re.finditer(pattern, content):
                field_name = match.group(1)
                fields.add(field_name)
        
        # Also add common inherited fields
        fields.update(['id', 'create_date', 'create_uid', 'write_date', 'write_uid', 'active', '__last_update'])
        
        if fields:
            self.model_fields[model_name] = fields
    
    def validate_view_fields(self, view_id: str, model_name: str, arch_content: str) -> List[str]:
        """Validate all field references in a view's arch"""
        errors = []
        
        # Get fields for this model
        if model_name not in self.model_fields:
            # Model not found in registry (might be from another module)
            return []
        
        model_fields = self.model_fields[model_name]
        
        # Extract all field name references from arch
        # Pattern: <field name="field_name"
        field_pattern = re.compile(r'<field\s+[^>]*name=["\']([^"\']+)["\']')
        
        for match in field_pattern.finditer(arch_content):
            field_name = match.group(1)
            
            # Skip relational field path references (e.g., partner_id.name)
            if '.' in field_name:
                continue
            
            # Check if field exists in model
            if field_name not in model_fields:
                line_num = arch_content[:match.start()].count('\n') + 1
                errors.append(
                    f"❌ Field Reference Error (Line {line_num}): Field '{field_name}' does not exist in model '{model_name}'"
                )
        
        return errors
    
    def validate_xml_file(self, xml_file_path: Path) -> Dict[str, List[str]]:
        """Validate all views in an XML file"""
        file_errors = {}
        
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            for record in root.findall('.//record'):
                if record.get('model') != 'ir.ui.view':
                    continue
                
                view_id = record.get('id', 'unknown')
                model_name = record.find("field[@name='model']")
                arch_field = record.find("field[@name='arch']")
                
                if model_name is None or arch_field is None:
                    continue
                
                model_text = model_name.text or ''
                arch_text = arch_field.text or ''
                
                if not arch_text.strip():
                    continue
                
                # Validate field references
                errors = self.validate_view_fields(view_id, model_text, arch_text)
                if errors:
                    file_errors[view_id] = errors
        
        except Exception as e:
            file_errors['ERROR'] = [f"Could not parse {xml_file_path}: {e}"]
        
        return file_errors
    
    def validate_all_views(self) -> Dict[Path, Dict[str, List[str]]]:
        """Validate all view XML files"""
        all_errors = {}
        views_dir = Path("records_management/views")
        
        if not views_dir.exists():
            print("⚠️  Views directory not found")
            return all_errors
        
        for xml_file in sorted(views_dir.glob("*.xml")):
            errors = self.validate_xml_file(xml_file)
            if errors:
                all_errors[xml_file] = errors
        
        return all_errors


if __name__ == '__main__':
    validator = FieldReferenceValidator()
    
    print("\n📚 Field Registry Built:")
    print(f"   Models found: {len(validator.model_fields)}")
    for model_name in sorted(validator.model_fields.keys())[:5]:
        field_count = len(validator.model_fields[model_name])
        print(f"   • {model_name}: {field_count} fields")
    if len(validator.model_fields) > 5:
        print(f"   ... and {len(validator.model_fields) - 5} more models")
    
    print("\n🔍 Validating Field References in Views...\n")
    
    all_errors = validator.validate_all_views()
    
    if not all_errors:
        print("✅ All field references are valid!")
    else:
        total_errors = sum(len(errors) for file_errors in all_errors.values() for errors in file_errors.values())
        print(f"❌ Found {total_errors} field reference errors:\n")
        
        for xml_file, file_errors in sorted(all_errors.items()):
            print(f"📄 {xml_file}")
            for view_id, errors in file_errors.items():
                if view_id == 'ERROR':
                    print(f"   {errors[0]}")
                else:
                    print(f"   View: {view_id}")
                    for error in errors:
                        print(f"      {error}")
            print()
