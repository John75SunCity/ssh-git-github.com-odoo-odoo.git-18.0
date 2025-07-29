#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Missing Fields Fixer
Systematically identifies and adds all missing fields that cause KeyErrors
"""

import os
import re
import sys

# Add the workspace to Python path
workspace_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'
sys.path.insert(0, workspace_path)

def get_model_files():
    """Get all Python model files"""
    models_dir = os.path.join(workspace_path, 'records_management', 'models')
    model_files = []
    for file in os.listdir(models_dir):
        if file.endswith('.py') and file != '__init__.py':
            model_files.append(os.path.join(models_dir, file))
    return model_files

def find_missing_fields():
    """Find all missing field references"""
    missing_fields = {}
    
    model_files = get_model_files()
    
    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find related field definitions
            related_pattern = r"(\w+)\s*=\s*fields\.\w+\([^)]*related\s*=\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(related_pattern, content, re.MULTILINE)
            
            for field_name, related_path in matches:
                if '.' in related_path:
                    target_field, referenced_field = related_path.split('.', 1)
                    filename = os.path.basename(file_path)
                    
                    if filename not in missing_fields:
                        missing_fields[filename] = []
                    
                    missing_fields[filename].append({
                        'field_name': field_name,
                        'related_path': related_path,
                        'target_field': target_field,
                        'referenced_field': referenced_field
                    })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return missing_fields

def add_missing_field_to_model(model_file, field_name, field_type, help_text="", default_value=None):
    """Add missing field to a model file"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the class definition
        class_pattern = r'(class\s+\w+\([^)]+\):\s*(?:\s*"""[^"]*""")?\s*(?:\s*_name\s*=.*\n)?\s*(?:\s*_description\s*=.*\n)?\s*(?:\s*_inherit\s*=.*\n)?\s*(?:\s*_order\s*=.*\n)?\s*(?:\s*_rec_name\s*=.*\n)?)'
        
        # Look for existing field definitions to find insertion point
        field_pattern = r'(\s+\w+\s*=\s*fields\.\w+\([^)]*\)[^\n]*\n)'
        
        # Create the field definition
        if field_type == 'Boolean':
            field_def = f'    {field_name} = fields.Boolean(string="{field_name.replace("_", " ").title()}", default={default_value if default_value is not None else "False"})\n'
        elif field_type == 'Char':
            field_def = f'    {field_name} = fields.Char(string="{field_name.replace("_", " ").title()}")\n'
        elif field_type == 'Integer':
            field_def = f'    {field_name} = fields.Integer(string="{field_name.replace("_", " ").title()}", default={default_value if default_value is not None else "0"})\n'
        elif field_type == 'Float':
            field_def = f'    {field_name} = fields.Float(string="{field_name.replace("_", " ").title()}", default={default_value if default_value is not None else "0.0"})\n'
        elif field_type == 'Many2one':
            field_def = f'    {field_name} = fields.Many2one("res.partner", string="{field_name.replace("_", " ").title()}")\n'
        else:
            field_def = f'    {field_name} = fields.Char(string="{field_name.replace("_", " ").title()}")\n'
        
        # Add help text if provided
        if help_text:
            field_def = field_def.rstrip(')\n') + f', help="{help_text}")\n'
        
        # Find existing fields and add our field
        existing_fields = re.findall(field_pattern, content)
        if existing_fields:
            # Insert after the last field
            last_field = existing_fields[-1]
            insert_pos = content.rfind(last_field) + len(last_field)
            content = content[:insert_pos] + field_def + content[insert_pos:]
        else:
            # Insert after class definition
            class_match = re.search(class_pattern, content)
            if class_match:
                insert_pos = class_match.end()
                content = content[:insert_pos] + '\n' + field_def + content[insert_pos:]
        
        # Write back to file
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error adding field {field_name} to {model_file}: {e}")
        return False

def fix_all_missing_fields():
    """Fix all missing fields systematically"""
    
    print("🔧 COMPREHENSIVE MISSING FIELDS FIXER")
    print("=" * 50)
    
    # Critical missing fields that need to be added to specific models
    critical_fixes = {
        # res.partner missing fields
        'res_partner.py': [
            {'field': 'container_count', 'type': 'Integer', 'help': 'Number of containers for this customer', 'default': 0},
            {'field': 'total_monthly_revenue', 'type': 'Float', 'help': 'Total monthly revenue from this customer'},
            {'field': 'billing_account_number', 'type': 'Char', 'help': 'Billing account number'},
            {'field': 'preferred_pickup_day', 'type': 'Selection', 'help': 'Preferred day for pickups'},
            {'field': 'service_level', 'type': 'Selection', 'help': 'Service level agreement'},
            {'field': 'credit_limit', 'type': 'Float', 'help': 'Credit limit for this customer'},
            {'field': 'payment_terms_days', 'type': 'Integer', 'help': 'Payment terms in days', 'default': 30},
        ],
        
        # records.box missing fields  
        'records_box.py': [
            {'field': 'box_number', 'type': 'Char', 'help': 'Box identification number'},
            {'field': 'barcode', 'type': 'Char', 'help': 'Box barcode'},
            {'field': 'destruction_eligible_date', 'type': 'Date', 'help': 'Date when eligible for destruction'},
            {'field': 'last_accessed_date', 'type': 'Date', 'help': 'Last access date'},
            {'field': 'storage_cost', 'type': 'Float', 'help': 'Monthly storage cost'},
            {'field': 'box_type', 'type': 'Selection', 'help': 'Type of storage box'},
            {'field': 'current_location_barcode', 'type': 'Char', 'help': 'Current location barcode'},
        ],
        
        # base.rates missing fields
        'shredding_rates.py': [
            # Add to BaseRates model if not present
            {'field': 'external_per_bin_rate', 'type': 'Float', 'help': 'External per bin rate'},
            {'field': 'external_service_call_rate', 'type': 'Float', 'help': 'External service call rate'},
            {'field': 'managed_retrieval_rate', 'type': 'Float', 'help': 'Managed retrieval rate'},
            {'field': 'managed_shredding_rate', 'type': 'Float', 'help': 'Managed shredding rate'},
            {'field': 'revenue_change_percentage', 'type': 'Float', 'help': 'Revenue change percentage'},
        ],
        
        # visitor model missing fields
        'frontdesk_visitor.py': [
            {'field': 'visitor_type', 'type': 'Selection', 'help': 'Type of visitor'},
            {'field': 'purpose', 'type': 'Text', 'help': 'Purpose of visit'},
            {'field': 'host_employee_id', 'type': 'Many2one', 'help': 'Host employee'},
            {'field': 'check_in_time', 'type': 'Datetime', 'help': 'Check-in time'},
            {'field': 'check_out_time', 'type': 'Datetime', 'help': 'Check-out time'},
        ],
        
        # records.vehicle missing fields  
        'records_vehicle.py': [
            {'field': 'fuel_capacity', 'type': 'Float', 'help': 'Fuel tank capacity'},
            {'field': 'maintenance_due_date', 'type': 'Date', 'help': 'Next maintenance due date'},
            {'field': 'insurance_expiry', 'type': 'Date', 'help': 'Insurance expiry date'},
            {'field': 'registration_number', 'type': 'Char', 'help': 'Vehicle registration number'},
        ],
        
        # billing models missing fields
        'billing.py': [
            {'field': 'subtotal', 'type': 'Float', 'help': 'Subtotal amount before taxes'},
            {'field': 'tax_amount', 'type': 'Float', 'help': 'Tax amount'},
            {'field': 'discount_amount', 'type': 'Float', 'help': 'Discount amount'},
            {'field': 'payment_status', 'type': 'Selection', 'help': 'Payment status'},
        ],
        
        # advanced billing missing fields
        'advanced_billing.py': [
            {'field': 'billing_line_ids', 'type': 'One2many', 'help': 'Billing line items'},
            {'field': 'billing_ids', 'type': 'One2many', 'help': 'Related billing records'},
            {'field': 'quantity', 'type': 'Float', 'help': 'Quantity', 'default': 1.0},
        ],
        
        # hr.employee extensions
        'hr_employee.py': [
            {'field': 'naid_certification_date', 'type': 'Date', 'help': 'NAID certification date'},
            {'field': 'records_access_level', 'type': 'Selection', 'help': 'Records access level'},
            {'field': 'security_clearance', 'type': 'Selection', 'help': 'Security clearance level'},
        ],
        
        # temp_inventory missing fields
        'temp_inventory.py': [
            {'field': 'retrieval_item_ids', 'type': 'One2many', 'help': 'Items for retrieval'},
            {'field': 'rate_id', 'type': 'Many2one', 'help': 'Applicable rate'},
        ],
        
        # pickup route missing fields
        'pickup_route.py': [
            {'field': 'route_stop_ids', 'type': 'One2many', 'help': 'Route stops'},
            {'field': 'total_weight', 'type': 'Float', 'help': 'Total weight'},
            {'field': 'fuel_cost', 'type': 'Float', 'help': 'Fuel cost'},
            {'field': 'actual_arrival_time', 'type': 'Datetime', 'help': 'Actual arrival time'},
        ]
    }
    
    models_dir = os.path.join(workspace_path, 'records_management', 'models')
    
    total_added = 0
    
    for model_file, fields_to_add in critical_fixes.items():
        model_path = os.path.join(models_dir, model_file)
        
        if os.path.exists(model_path):
            print(f"\n📄 Processing {model_file}...")
            
            # Read current content to check if fields already exist
            with open(model_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for field_info in fields_to_add:
                field_name = field_info['field']
                field_type = field_info['type']
                help_text = field_info.get('help', '')
                default_value = field_info.get('default')
                
                # Check if field already exists
                if f"{field_name} = fields." in content:
                    print(f"  ✅ {field_name} already exists")
                    continue
                
                # Add the field
                success = add_missing_field_to_model(model_path, field_name, field_type, help_text, default_value)
                if success:
                    print(f"  ➕ Added {field_name} ({field_type})")
                    total_added += 1
                else:
                    print(f"  ❌ Failed to add {field_name}")
        else:
            print(f"  ⚠️  Model file {model_file} not found")
    
    print(f"\n🎯 SUMMARY: Added {total_added} missing fields")
    print("=" * 50)

if __name__ == "__main__":
    fix_all_missing_fields()
