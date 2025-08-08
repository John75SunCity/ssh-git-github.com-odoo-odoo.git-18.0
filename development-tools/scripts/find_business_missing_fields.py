#!/usr/bin/env python3
"""
BUSINESS-FOCUSED FIELD ANALYSIS SCRIPT
Finds missing BUSINESS-SPECIFIC fields, filtering out standard Odoo framework fields
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

# Standard Odoo framework fields that come automatically with inheritance
STANDARD_FRAMEWORK_FIELDS = {
    # From models.Model base class
    'id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update',
    
    # From mail.thread mixin
    'message_ids', 'message_follower_ids', 'message_partner_ids', 'message_channel_ids',
    'message_is_follower', 'message_needaction', 'message_needaction_counter',
    'message_has_error', 'message_has_error_counter', 'message_attachment_count',
    'message_main_attachment_id', 'website_message_ids',
    
    # From mail.activity.mixin
    'activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id',
    'activity_date_deadline', 'activity_summary', 'activity_exception_decoration',
    'activity_exception_icon',
    
    # From portal.mixin
    'access_url', 'access_token', 'access_warning',
    
    # From rating.mixin  
    'rating_ids', 'rating_last_value', 'rating_last_feedback', 'rating_last_image',
    'rating_count', 'rating_avg',
    
    # Common computed fields in base modules
    'display_name', 'name_get',
}

# View-only fields that should NOT be in models
VIEW_ONLY_FIELDS = {
    'arch', 'context', 'domain', 'help', 'model', 'res_model', 'view_mode', 
    'search_view_id', 'view_id', 'target', 'type', 'action', 'string',
    'invisible', 'readonly', 'required', 'widget', 'options', 'attrs',
    'decoration-bf', 'decoration-danger', 'decoration-info', 'decoration-muted',
    'decoration-primary', 'decoration-success', 'decoration-warning'
}

# Fields that are commonly used in tree/form views but should be contextual
CONTEXTUAL_FIELDS = {
    'state', 'name', 'active', 'company_id', 'currency_id', 'partner_id',
    'user_id', 'date', 'amount', 'quantity', 'description', 'notes',
    'sequence', 'color'
}

def extract_fields_from_python_file(file_path):
    """Extract all field definitions from a Python model file"""
    fields = set()
    model_inherits = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Match field definitions: field_name = fields.FieldType(...)
        field_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.[A-Za-z_][A-Za-z0-9_]*\('
        for line in content.split('\n'):
            match = re.match(field_pattern, line)
            if match:
                field_name = match.group(1)
                # Skip private fields and methods
                if not field_name.startswith('_') and field_name not in ['fields']:
                    fields.add(field_name)
                    
        # Extract inherited models
        inherit_patterns = [
            r"_inherit\s*=\s*['\"]([^'\"]+)['\"]",  # Single inheritance
            r"_inherit\s*=\s*\[(.*?)\]"  # Multiple inheritance
        ]
        
        for pattern in inherit_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if '[' in pattern:  # Multiple inheritance
                    # Parse the list
                    inherit_list = re.findall(r"['\"]([^'\"]+)['\"]", match)
                    model_inherits.extend(inherit_list)
                else:  # Single inheritance
                    model_inherits.append(match)
                    
        return fields, model_inherits
        
    except Exception as e:
        print(f"Error reading Python file {file_path}: {e}")
        return set(), []

def extract_model_name_from_python_file(file_path):
    """Extract the model name from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for _name definition
        name_pattern = r"_name\s*=\s*['\"]([^'\"]+)['\"]"
        name_match = re.search(name_pattern, content)
        if name_match:
            return name_match.group(1)
            
        # Look for class name and convert to model name
        class_pattern = r'class\s+([A-Za-z][A-Za-z0-9_]*)\(models\.Model\)'
        class_match = re.search(class_pattern, content)
        if class_match:
            class_name = class_match.group(1)
            # Convert CamelCase to dot.notation
            model_name = re.sub(r'([a-z0-9])([A-Z])', r'\1.\2', class_name).lower()
            return model_name
            
    except Exception as e:
        print(f"Error reading Python file {file_path}: {e}")
        
    return None

def extract_fields_from_xml_file(file_path):
    """Extract all field references from an XML view file"""
    field_references = defaultdict(set)
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Find all field elements
        for field_elem in root.findall('.//field'):
            field_name = field_elem.get('name')
            if field_name and field_name not in VIEW_ONLY_FIELDS:
                # Try to determine the model context
                model_context = None
                
                # Look for model in parent elements
                parent = field_elem
                while parent is not None:
                    if parent.tag == 'record' and parent.get('model'):
                        if 'view' in parent.get('model', ''):
                            # This is a view definition, look for the model it refers to
                            for child in parent:
                                if child.tag == 'field' and child.get('name') == 'model':
                                    model_context = child.text
                                    break
                        break
                    elif parent.tag in ['tree', 'form', 'kanban', 'search', 'calendar', 'graph', 'pivot']:
                        # Look for model in arch context or record
                        record_parent = parent
                        while record_parent is not None:
                            if record_parent.tag == 'record':
                                for child in record_parent:
                                    if child.tag == 'field' and child.get('name') == 'model':
                                        model_context = child.text
                                        break
                                break
                            record_parent = record_parent.getparent() if hasattr(record_parent, 'getparent') else None
                        break
                    parent = parent.getparent() if hasattr(parent, 'getparent') else None
                
                # Also extract model from file context by examining other records
                if not model_context:
                    for record in root.findall('.//record'):
                        for field in record.findall('.//field[@name="model"]'):
                            if field.text and '.' in field.text:
                                model_context = field.text
                                break
                        if model_context:
                            break
                
                if model_context:
                    field_references[model_context].add(field_name)
                else:
                    # Add to unknown context for manual review
                    field_references['__unknown__'].add(field_name)
                    
    except ET.ParseError as e:
        print(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        print(f"Error reading XML file {file_path}: {e}")
        
    return field_references

def get_inherited_fields(model_inherits):
    """Get fields that should be available from inherited models"""
    inherited_fields = set()
    
    # Add framework fields based on inheritance
    for inherit in model_inherits:
        if inherit == 'mail.thread':
            inherited_fields.update([
                'message_ids', 'message_follower_ids', 'message_partner_ids',
                'message_channel_ids', 'message_is_follower', 'message_needaction',
                'message_needaction_counter', 'message_has_error', 'message_has_error_counter',
                'message_attachment_count', 'message_main_attachment_id', 'website_message_ids'
            ])
        elif inherit == 'mail.activity.mixin':
            inherited_fields.update([
                'activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id',
                'activity_date_deadline', 'activity_summary', 'activity_exception_decoration',
                'activity_exception_icon'
            ])
        elif inherit == 'portal.mixin':
            inherited_fields.update(['access_url', 'access_token', 'access_warning'])
        elif inherit == 'rating.mixin':
            inherited_fields.update([
                'rating_ids', 'rating_last_value', 'rating_last_feedback',
                'rating_last_image', 'rating_count', 'rating_avg'
            ])
            
    return inherited_fields

def analyze_fields():
    """Main analysis function focusing on business-specific missing fields"""
    
    print("🔍 BUSINESS-FOCUSED FIELD ANALYSIS STARTING...")
    print("=" * 60)
    print("🎯 Filtering out standard Odoo framework fields")
    print("🎯 Focusing on business-specific missing fields")
    print("=" * 60)
    
    base_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    models_path = os.path.join(base_path, 'models')
    views_path = os.path.join(base_path, 'views')
    
    # Step 1: Extract model fields
    print("\n📄 STEP 1: Analyzing Python Model Files...")
    model_fields = {}
    model_inheritance = {}
    
    for filename in os.listdir(models_path):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_path, filename)
            model_name = extract_model_name_from_python_file(file_path)
            
            if model_name:
                fields, inherits = extract_fields_from_python_file(file_path)
                model_fields[model_name] = fields
                model_inheritance[model_name] = inherits
                print(f"  ✓ {model_name}: {len(fields)} fields")
            else:
                fields, inherits = extract_fields_from_python_file(file_path)
                print(f"  ? {filename}: {len(fields)} fields (unknown model name)")
    
    # Step 2: Extract view field references
    print("\n📋 STEP 2: Analyzing XML View Files...")
    view_field_references = defaultdict(set)
    
    for filename in os.listdir(views_path):
        if filename.endswith('.xml'):
            file_path = os.path.join(views_path, filename)
            file_references = extract_fields_from_xml_file(file_path)
            
            for model, fields in file_references.items():
                view_field_references[model].update(fields)
                if model != '__unknown__':
                    print(f"  ✓ {filename}: {len(fields)} field references for {model}")
    
    # Step 3: Find BUSINESS-SPECIFIC missing fields
    print("\n🔎 STEP 3: Finding Business-Specific Missing Fields...")
    
    total_missing = 0
    business_missing = 0
    models_with_missing = 0
    
    for model, referenced_fields in view_field_references.items():
        if model == '__unknown__' or model not in model_fields:
            continue
            
        # Get actual model fields
        actual_fields = model_fields[model]
        
        # Get inherited fields that should be available
        inherits = model_inheritance.get(model, [])
        inherited_fields = get_inherited_fields(inherits)
        
        # Combine actual and inherited fields
        available_fields = actual_fields | inherited_fields | STANDARD_FRAMEWORK_FIELDS
        
        # Find missing fields
        missing_fields = referenced_fields - available_fields
        
        # Filter out view-only and contextual fields for business analysis
        business_missing_fields = missing_fields - VIEW_ONLY_FIELDS
        
        # Further filter contextual fields that might be acceptable misses
        critical_missing = set()
        contextual_missing = set()
        
        for field in business_missing_fields:
            if field in CONTEXTUAL_FIELDS:
                contextual_missing.add(field)
            else:
                critical_missing.add(field)
        
        total_missing += len(missing_fields)
        business_missing += len(critical_missing)
        
        if critical_missing:
            models_with_missing += 1
            print(f"\n🚨 Model: {model}")
            print(f"   📊 Total referenced: {len(referenced_fields)}")
            print(f"   ✅ Available: {len(available_fields & referenced_fields)}")
            print(f"   ❌ CRITICAL missing: {len(critical_missing)}")
            print(f"   ⚠️  Contextual missing: {len(contextual_missing)}")
            
            if critical_missing:
                print(f"   🎯 CRITICAL BUSINESS FIELDS TO ADD:")
                for field in sorted(critical_missing):
                    print(f"      - {field}")
            
            if contextual_missing:
                print(f"   💡 CONTEXTUAL (review needed):")
                for field in sorted(contextual_missing):
                    print(f"      - {field}")
    
    # Step 4: Summary
    print(f"\n📊 STEP 4: BUSINESS-FOCUSED SUMMARY")
    print("=" * 60)
    print(f"🎯 CRITICAL BUSINESS MISSING FIELDS: {business_missing}")
    print(f"📈 Total missing (including framework): {total_missing}")
    print(f"🏢 Models needing attention: {models_with_missing}")
    print(f"📋 Total models analyzed: {len(model_fields)}")
    
    success_rate = ((total_missing - business_missing) / total_missing * 100) if total_missing > 0 else 100
    print(f"✅ Framework filtering success: {success_rate:.1f}%")
    
    print(f"\n🎯 PRIORITY: Focus on the {business_missing} critical business fields above!")
    print("💡 These are the fields that need custom implementation for business logic.")

if __name__ == "__main__":
    analyze_fields()
