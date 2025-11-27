#!/usr/bin/env python3
"""
Odoo Model & Field Catalog for Records Management
==================================================
Dynamically scans Python models to build a comprehensive registry of:
- All models with their _name, _inherit, _description
- All field definitions with types and attributes
- Relational fields (Many2one, One2many, Many2many) with comodels
- Computed fields with dependencies
- Related fields with paths
- Selection field options
- View definitions from XML files

This catalog integrates with comprehensive_validator.py to eliminate
false positives by validating against real model/field data.

Usage:
    from model_field_catalog import ModelFieldCatalog
    catalog = ModelFieldCatalog()
    catalog.build()
    catalog.get_model_fields('records.container')
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import xml.etree.ElementTree as ET


@dataclass
class FieldInfo:
    """Represents a field definition with all its attributes."""
    name: str
    field_type: str
    string: Optional[str] = None
    comodel_name: Optional[str] = None  # For relational fields
    inverse_name: Optional[str] = None  # For One2many
    relation: Optional[str] = None  # For Many2many (relation table)
    related: Optional[str] = None  # For related fields
    compute: Optional[str] = None  # Compute method name
    depends: List[str] = field(default_factory=list)  # @api.depends
    selection: List[Tuple[str, str]] = field(default_factory=list)
    required: bool = False
    readonly: bool = False
    store: bool = True
    index: bool = False
    default: Optional[str] = None
    help_text: Optional[str] = None
    groups: Optional[str] = None
    tracking: bool = False
    copy: bool = True
    file_path: Optional[str] = None  # Source file
    line_number: int = 0


@dataclass
class ModelInfo:
    """Represents an Odoo model definition."""
    name: str
    inherit: List[str] = field(default_factory=list)
    inherits: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    order: Optional[str] = None
    rec_name: Optional[str] = None
    fields: Dict[str, FieldInfo] = field(default_factory=dict)
    file_path: Optional[str] = None

    # Relational field summaries for quick lookup
    many2one_fields: List[str] = field(default_factory=list)
    one2many_fields: List[str] = field(default_factory=list)
    many2many_fields: List[str] = field(default_factory=list)
    computed_fields: List[str] = field(default_factory=list)
    related_fields: List[str] = field(default_factory=list)
    selection_fields: List[str] = field(default_factory=list)


@dataclass
class ViewInfo:
    """Represents an Odoo view definition."""
    xml_id: str
    name: str
    model: str
    view_type: str  # form, list, kanban, search, etc.
    inherit_id: Optional[str] = None
    priority: int = 16
    fields_used: Set[str] = field(default_factory=set)
    file_path: Optional[str] = None


class ModelFieldCatalog:
    """
    Dynamic catalog of all models, fields, and views in records_management.
    
    Provides:
    - Complete field registry for validation
    - Relational field mapping for comodel validation
    - Computed field dependency tracking
    - View field usage tracking
    """

    # Common inherited fields from mail.thread, mail.activity.mixin, etc.
    COMMON_INHERITED_FIELDS = {
        # Base model fields
        'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
        'display_name', '__last_update',

        # mail.thread fields
        'message_ids', 'message_follower_ids', 'message_partner_ids',
        'message_channel_ids', 'message_is_follower', 'message_needaction',
        'message_needaction_counter', 'message_has_error',
        'message_has_error_counter', 'message_attachment_count',
        'message_main_attachment_id', 'website_message_ids',

        # mail.activity.mixin fields
        'activity_ids', 'activity_state', 'activity_user_id',
        'activity_type_id', 'activity_type_icon', 'activity_date_deadline',
        'activity_summary', 'activity_exception_decoration',
        'activity_exception_icon', 'my_activity_date_deadline',

        # portal.mixin fields
        'access_url', 'access_token', 'access_warning',

        # image.mixin fields
        'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128',

        # Active field (common)
        'active',

        # Company-dependent fields
        'company_id',
    }

    # Field type patterns for regex parsing
    FIELD_TYPE_PATTERNS = {
        'Char': r'fields\.Char\s*\(',
        'Text': r'fields\.Text\s*\(',
        'Html': r'fields\.Html\s*\(',
        'Integer': r'fields\.Integer\s*\(',
        'Float': r'fields\.Float\s*\(',
        'Monetary': r'fields\.Monetary\s*\(',
        'Boolean': r'fields\.Boolean\s*\(',
        'Date': r'fields\.Date\s*\(',
        'Datetime': r'fields\.Datetime\s*\(',
        'Binary': r'fields\.Binary\s*\(',
        'Image': r'fields\.Image\s*\(',
        'Selection': r'fields\.Selection\s*\(',
        'Many2one': r'fields\.Many2one\s*\(',
        'One2many': r'fields\.One2many\s*\(',
        'Many2many': r'fields\.Many2many\s*\(',
        'Reference': r'fields\.Reference\s*\(',
        'Json': r'fields\.Json\s*\(',
        'Properties': r'fields\.Properties\s*\(',
        'PropertiesDefinition': r'fields\.PropertiesDefinition\s*\(',
    }

    def __init__(self, module_path: str = "records_management"):
        self.module_path = Path(module_path)
        self.models: Dict[str, ModelInfo] = {}
        self.views: Dict[str, ViewInfo] = {}
        self.comodel_references: Dict[str, Set[str]] = defaultdict(set)  # comodel -> set of referencing fields
        self.field_to_model: Dict[str, str] = {}  # field_name -> model_name (for ambiguous lookups)
        self._built = False

    def build(self) -> 'ModelFieldCatalog':
        """Build the complete catalog from source files."""
        if self._built:
            return self

        print("📚 Building Model & Field Catalog...")

        # Scan Python models
        self._scan_models()

        # Scan XML views
        self._scan_views()

        # Build cross-references
        self._build_cross_references()

        self._built = True
        self._print_summary()

        return self

    def _scan_models(self) -> None:
        """Scan all Python files for model definitions."""
        model_dirs = [
            self.module_path / "models",
            self.module_path / "wizards",
        ]

        for model_dir in model_dirs:
            if not model_dir.exists():
                continue

            for py_file in sorted(model_dir.rglob("*.py")):
                if py_file.name.startswith("__"):
                    continue

                try:
                    self._parse_model_file(py_file)
                except Exception as e:
                    print(f"  ⚠️  Error parsing {py_file.name}: {e}")

    def _parse_model_file(self, file_path: Path) -> None:
        """Parse a Python file for model and field definitions."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        # Find all class definitions that are Odoo models
        class_pattern = re.compile(
            r'class\s+(\w+)\s*\([^)]*(?:models\.Model|models\.TransientModel|models\.AbstractModel)[^)]*\)\s*:'
        )

        for class_match in class_pattern.finditer(content):
            class_name = class_match.group(1)
            class_start = class_match.start()

            # Find the class body
            class_body = self._extract_class_body(content, class_start)
            if not class_body:
                continue
            
            # Parse model attributes
            model_info = self._parse_model_attributes(class_body, file_path)
            if model_info and model_info.name:
                # Add common inherited fields
                for field_name in self.COMMON_INHERITED_FIELDS:
                    if field_name not in model_info.fields:
                        model_info.fields[field_name] = FieldInfo(
                            name=field_name,
                            field_type='inherited',
                            file_path=str(file_path)
                        )
                
                # MERGE fields if model already exists (inheritance extension)
                if model_info.name in self.models:
                    existing = self.models[model_info.name]
                    # Merge fields from inheritance extension
                    for field_name, field_info in model_info.fields.items():
                        if field_name not in existing.fields:
                            existing.fields[field_name] = field_info
                    # Merge field category lists
                    for attr in ['many2one_fields', 'one2many_fields', 'many2many_fields',
                                 'selection_fields', 'computed_fields', 'related_fields']:
                        existing_list = getattr(existing, attr)
                        new_list = getattr(model_info, attr)
                        for item in new_list:
                            if item not in existing_list:
                                existing_list.append(item)
                else:
                    self.models[model_info.name] = model_info
    
    def _extract_class_body(self, content: str, class_start: int) -> Optional[str]:
        """Extract the body of a class definition."""
        # Simple approach: find content until next class or end of file
        lines = content[class_start:].split('\n')
        body_lines = []
        indent_level = None
        
        for i, line in enumerate(lines):
            if i == 0:
                body_lines.append(line)
                continue
            
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                body_lines.append(line)
                continue
            
            current_indent = len(line) - len(stripped)
            
            if indent_level is None and stripped:
                indent_level = current_indent
            
            # Check if we've exited the class (new class at same or lower indent)
            if indent_level and current_indent <= 0 and stripped.startswith('class '):
                break
            
            body_lines.append(line)
        
        return '\n'.join(body_lines)
    
    def _parse_model_attributes(self, class_body: str, file_path: Path) -> Optional[ModelInfo]:
        """Parse model _name, _inherit, _description and fields."""
        model_info = ModelInfo(name='', file_path=str(file_path))
        
        # Extract _name
        name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", class_body)
        if name_match:
            model_info.name = name_match.group(1)
        
        # Extract _inherit (can be string or list)
        inherit_match = re.search(r"_inherit\s*=\s*\[([^\]]+)\]", class_body)
        if inherit_match:
            inherits = re.findall(r"['\"]([^'\"]+)['\"]", inherit_match.group(1))
            model_info.inherit = inherits
        else:
            inherit_match = re.search(r"_inherit\s*=\s*['\"]([^'\"]+)['\"]", class_body)
            if inherit_match:
                model_info.inherit = [inherit_match.group(1)]
                # If only _inherit without _name, use inherited model name
                if not model_info.name:
                    model_info.name = inherit_match.group(1)
        
        # Extract _description
        desc_match = re.search(r"_description\s*=\s*['\"]([^'\"]+)['\"]", class_body)
        if desc_match:
            model_info.description = desc_match.group(1)
        
        # Extract _order
        order_match = re.search(r"_order\s*=\s*['\"]([^'\"]+)['\"]", class_body)
        if order_match:
            model_info.order = order_match.group(1)
        
        # Extract _rec_name
        rec_name_match = re.search(r"_rec_name\s*=\s*['\"]([^'\"]+)['\"]", class_body)
        if rec_name_match:
            model_info.rec_name = rec_name_match.group(1)
        
        # Parse fields
        self._parse_fields(class_body, model_info, file_path)
        
        return model_info if model_info.name else None
    
    def _parse_fields(self, class_body: str, model_info: ModelInfo, file_path: Path) -> None:
        """Parse all field definitions from a class body."""
        lines = class_body.split('\n')
        
        # Pattern to match field assignments
        field_pattern = re.compile(
            r'^\s*(\w+)\s*=\s*fields\.(\w+)\s*\('
        )
        
        for line_num, line in enumerate(lines, 1):
            match = field_pattern.match(line)
            if not match:
                continue
            
            field_name = match.group(1)
            field_type = match.group(2)
            
            # Extract field arguments (may span multiple lines)
            field_def = self._extract_field_definition(lines, line_num - 1)
            field_info = self._parse_field_info(field_name, field_type, field_def, file_path, line_num)
            
            model_info.fields[field_name] = field_info
            
            # Categorize relational and special fields
            if field_type == 'Many2one':
                model_info.many2one_fields.append(field_name)
            elif field_type == 'One2many':
                model_info.one2many_fields.append(field_name)
            elif field_type == 'Many2many':
                model_info.many2many_fields.append(field_name)
            elif field_type == 'Selection':
                model_info.selection_fields.append(field_name)
            
            if field_info.compute:
                model_info.computed_fields.append(field_name)
            if field_info.related:
                model_info.related_fields.append(field_name)
    
    def _extract_field_definition(self, lines: List[str], start_line: int) -> str:
        """Extract complete field definition that may span multiple lines."""
        # Simple approach: collect lines until parentheses are balanced
        definition = []
        paren_count = 0
        started = False
        
        for i in range(start_line, min(start_line + 50, len(lines))):
            line = lines[i]
            definition.append(line)
            
            for char in line:
                if char == '(':
                    paren_count += 1
                    started = True
                elif char == ')':
                    paren_count -= 1
            
            if started and paren_count == 0:
                break
        
        return '\n'.join(definition)
    
    def _parse_field_info(self, name: str, field_type: str, definition: str, 
                          file_path: Path, line_num: int) -> FieldInfo:
        """Parse field attributes from its definition."""
        field_info = FieldInfo(
            name=name,
            field_type=field_type,
            file_path=str(file_path),
            line_number=line_num
        )
        
        # Extract string/label
        string_match = re.search(r"string\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if string_match:
            field_info.string = string_match.group(1)
        
        # Extract comodel_name for relational fields
        comodel_match = re.search(r"comodel_name\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if comodel_match:
            field_info.comodel_name = comodel_match.group(1)
        else:
            # First positional argument for relational fields
            if field_type in ('Many2one', 'One2many', 'Many2many'):
                first_arg = re.search(r"fields\.\w+\s*\(\s*['\"]([^'\"]+)['\"]", definition)
                if first_arg:
                    field_info.comodel_name = first_arg.group(1)
        
        # Extract inverse_name for One2many
        inverse_match = re.search(r"inverse_name\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if inverse_match:
            field_info.inverse_name = inverse_match.group(1)
        
        # Extract relation table for Many2many
        relation_match = re.search(r"relation\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if relation_match:
            field_info.relation = relation_match.group(1)
        
        # Extract related path
        related_match = re.search(r"related\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if related_match:
            field_info.related = related_match.group(1)
        
        # Extract compute method
        compute_match = re.search(r"compute\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if compute_match:
            field_info.compute = compute_match.group(1)
        
        # Extract required
        if 'required=True' in definition or 'required = True' in definition:
            field_info.required = True
        
        # Extract readonly
        if 'readonly=True' in definition or 'readonly = True' in definition:
            field_info.readonly = True
        
        # Extract store
        if 'store=False' in definition or 'store = False' in definition:
            field_info.store = False
        
        # Extract index
        if 'index=True' in definition or 'index = True' in definition:
            field_info.index = True
        
        # Extract tracking
        if 'tracking=True' in definition or 'tracking = True' in definition:
            field_info.tracking = True
        
        # Extract selection options
        if field_type == 'Selection':
            selection_match = re.search(r'\[\s*(\([^)]+\)\s*,?\s*)+\]', definition)
            if selection_match:
                options = re.findall(r"\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", 
                                    selection_match.group(0))
                field_info.selection = options
        
        # Extract help text
        help_match = re.search(r"help\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if help_match:
            field_info.help_text = help_match.group(1)
        
        # Extract groups
        groups_match = re.search(r"groups\s*=\s*['\"]([^'\"]+)['\"]", definition)
        if groups_match:
            field_info.groups = groups_match.group(1)
        
        return field_info
    
    def _scan_views(self) -> None:
        """Scan all XML files for view definitions."""
        views_dir = self.module_path / "views"
        templates_dir = self.module_path / "templates"
        
        for xml_dir in [views_dir, templates_dir]:
            if not xml_dir.exists():
                continue
            
            for xml_file in sorted(xml_dir.rglob("*.xml")):
                try:
                    self._parse_view_file(xml_file)
                except Exception as e:
                    pass  # Silently skip problematic files
    
    def _parse_view_file(self, file_path: Path) -> None:
        """Parse an XML file for view definitions."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError:
            return
        
        for record in root.findall('.//record'):
            if record.get('model') != 'ir.ui.view':
                continue
            
            xml_id = record.get('id', '')
            if not xml_id:
                continue
            
            # Extract view attributes
            name_elem = record.find("field[@name='name']")
            model_elem = record.find("field[@name='model']")
            arch_elem = record.find("field[@name='arch']")
            inherit_elem = record.find("field[@name='inherit_id']")
            priority_elem = record.find("field[@name='priority']")
            
            view_info = ViewInfo(
                xml_id=xml_id,
                name=name_elem.text if name_elem is not None and name_elem.text else '',
                model=model_elem.text if model_elem is not None and model_elem.text else '',
                view_type=self._detect_view_type(arch_elem),
                inherit_id=inherit_elem.get('ref') if inherit_elem is not None else None,
                priority=int(priority_elem.text) if priority_elem is not None and priority_elem.text else 16,
                file_path=str(file_path)
            )
            
            # Extract fields used in view
            if arch_elem is not None:
                arch_str = ET.tostring(arch_elem, encoding='unicode')
                field_pattern = re.compile(r'name=["\']([^"\']+)["\']')
                view_info.fields_used = set(field_pattern.findall(arch_str))
            
            self.views[xml_id] = view_info
    
    def _detect_view_type(self, arch_elem) -> str:
        """Detect the type of view from its arch content."""
        if arch_elem is None:
            return 'unknown'
        
        arch_str = ET.tostring(arch_elem, encoding='unicode').lower()
        
        view_types = ['form', 'list', 'tree', 'kanban', 'search', 'calendar', 
                      'graph', 'pivot', 'cohort', 'gantt', 'hierarchy', 'activity']
        
        for vtype in view_types:
            if f'<{vtype}' in arch_str:
                return vtype
        
        return 'unknown'
    
    def _build_cross_references(self) -> None:
        """Build cross-reference maps for validation."""
        for model_name, model_info in self.models.items():
            for field_name, field_info in model_info.fields.items():
                # Track comodel references
                if field_info.comodel_name:
                    self.comodel_references[field_info.comodel_name].add(
                        f"{model_name}.{field_name}"
                    )
                
                # Track field to model mapping
                self.field_to_model[field_name] = model_name
    
    def _print_summary(self) -> None:
        """Print a summary of the catalog."""
        total_fields = sum(len(m.fields) for m in self.models.values())
        total_m2o = sum(len(m.many2one_fields) for m in self.models.values())
        total_o2m = sum(len(m.one2many_fields) for m in self.models.values())
        total_m2m = sum(len(m.many2many_fields) for m in self.models.values())
        total_computed = sum(len(m.computed_fields) for m in self.models.values())
        total_related = sum(len(m.related_fields) for m in self.models.values())
        total_selection = sum(len(m.selection_fields) for m in self.models.values())
        
        print(f"\n📊 Catalog Summary:")
        print(f"   Models: {len(self.models)}")
        print(f"   Total Fields: {total_fields}")
        print(f"   ├── Many2one: {total_m2o}")
        print(f"   ├── One2many: {total_o2m}")
        print(f"   ├── Many2many: {total_m2m}")
        print(f"   ├── Computed: {total_computed}")
        print(f"   ├── Related: {total_related}")
        print(f"   └── Selection: {total_selection}")
        print(f"   Views: {len(self.views)}")
    
    # ==================== Public API ====================
    
    def get_model(self, model_name: str) -> Optional[ModelInfo]:
        """Get a model by name."""
        return self.models.get(model_name)
    
    def get_model_fields(self, model_name: str) -> Set[str]:
        """Get all field names for a model."""
        model = self.models.get(model_name)
        if model:
            return set(model.fields.keys())
        return set()
    
    def get_field_info(self, model_name: str, field_name: str) -> Optional[FieldInfo]:
        """Get detailed field info."""
        model = self.models.get(model_name)
        if model:
            return model.fields.get(field_name)
        return None
    
    def field_exists(self, model_name: str, field_name: str) -> bool:
        """Check if a field exists on a model."""
        model = self.models.get(model_name)
        if model:
            return field_name in model.fields
        return False
    
    def model_exists(self, model_name: str) -> bool:
        """Check if a model exists in the catalog."""
        return model_name in self.models
    
    def get_comodel(self, model_name: str, field_name: str) -> Optional[str]:
        """Get the comodel for a relational field."""
        field_info = self.get_field_info(model_name, field_name)
        if field_info:
            return field_info.comodel_name
        return None
    
    def validate_field_reference(self, model_name: str, field_path: str) -> Tuple[bool, str]:
        """
        Validate a field reference path (e.g., 'partner_id.name').
        Returns (is_valid, error_message).
        """
        if not field_path:
            return True, ""
        
        parts = field_path.split('.')
        current_model = model_name
        
        for i, part in enumerate(parts):
            if not self.model_exists(current_model):
                # Model might be from external module - allow it
                return True, ""
            
            if not self.field_exists(current_model, part):
                return False, f"Field '{part}' does not exist on model '{current_model}'"
            
            # For next iteration, get the comodel if this is a relational field
            if i < len(parts) - 1:
                comodel = self.get_comodel(current_model, part)
                if comodel:
                    current_model = comodel
                else:
                    # Non-relational field can't have dot notation
                    return False, f"Field '{part}' on '{current_model}' is not a relational field"
        
        return True, ""
    
    def get_selection_values(self, model_name: str, field_name: str) -> List[str]:
        """Get valid selection values for a field."""
        field_info = self.get_field_info(model_name, field_name)
        if field_info and field_info.selection:
            return [opt[0] for opt in field_info.selection]
        return []
    
    def export_to_json(self, output_path: str = None) -> str:
        """Export the catalog to JSON for debugging or caching."""
        if output_path is None:
            output_path = str(self.module_path / ".catalog_cache.json")
        
        # Convert to serializable format
        data = {
            'models': {},
            'views': {},
            'comodel_references': dict(self.comodel_references)
        }
        
        for name, model in self.models.items():
            model_dict = {
                'name': model.name,
                'inherit': model.inherit,
                'description': model.description,
                'order': model.order,
                'rec_name': model.rec_name,
                'file_path': model.file_path,
                'fields': {},
                'many2one_fields': model.many2one_fields,
                'one2many_fields': model.one2many_fields,
                'many2many_fields': model.many2many_fields,
                'computed_fields': model.computed_fields,
                'related_fields': model.related_fields,
                'selection_fields': model.selection_fields,
            }
            
            for fname, finfo in model.fields.items():
                model_dict['fields'][fname] = {
                    'name': finfo.name,
                    'field_type': finfo.field_type,
                    'string': finfo.string,
                    'comodel_name': finfo.comodel_name,
                    'inverse_name': finfo.inverse_name,
                    'related': finfo.related,
                    'compute': finfo.compute,
                    'selection': finfo.selection,
                    'required': finfo.required,
                    'readonly': finfo.readonly,
                    'store': finfo.store,
                }
            
            data['models'][name] = model_dict
        
        for name, view in self.views.items():
            data['views'][name] = {
                'xml_id': view.xml_id,
                'name': view.name,
                'model': view.model,
                'view_type': view.view_type,
                'inherit_id': view.inherit_id,
                'fields_used': list(view.fields_used),
                'file_path': view.file_path,
            }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=list)
        
        return output_path


# Singleton instance for use by other modules
_catalog_instance: Optional[ModelFieldCatalog] = None


def get_catalog() -> ModelFieldCatalog:
    """Get or create the singleton catalog instance."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = ModelFieldCatalog()
        _catalog_instance.build()
    return _catalog_instance


if __name__ == '__main__':
    print("=" * 70)
    print("ODOO MODEL & FIELD CATALOG")
    print("Records Management Module")
    print("=" * 70)
    
    catalog = ModelFieldCatalog()
    catalog.build()
    
    # Show sample model details
    print("\n📋 Sample Model Details:")
    sample_models = ['records.container', 'records.file', 'portal.request']
    
    for model_name in sample_models:
        model = catalog.get_model(model_name)
        if model:
            print(f"\n   📦 {model_name}")
            print(f"      Description: {model.description or 'N/A'}")
            print(f"      Fields: {len(model.fields)}")
            print(f"      Many2one: {len(model.many2one_fields)}")
            print(f"      One2many: {len(model.one2many_fields)}")
            print(f"      Many2many: {len(model.many2many_fields)}")
            
            if model.many2one_fields[:3]:
                print(f"      Sample M2O: {', '.join(model.many2one_fields[:3])}")
            if model.one2many_fields[:3]:
                print(f"      Sample O2M: {', '.join(model.one2many_fields[:3])}")
    
    # Export catalog
    cache_path = catalog.export_to_json()
    print(f"\n💾 Catalog exported to: {cache_path}")
    
    print("\n✅ Catalog build complete!")
