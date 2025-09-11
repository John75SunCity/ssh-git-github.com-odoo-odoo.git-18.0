#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Missing Compute Methods Fixer - Phase 3
Add missing compute methods for computed fields to prevent AttributeError
"""

import os
import re
import sys

workspace_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'
sys.path.insert(0, workspace_path)

def add_compute_method_to_model(model_file, method_definition):
    """Add compute method to model file"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the end of the class to insert the method
        # Look for the last method or field definition
        method_pattern = r'(\s+def\s+\w+\([^)]*\):\s*(?:"""[^"]*""")?\s*[^}]+?)(?=\s+def\s|\s+@|\s*class\s|\Z)'
        method_matches = list(re.finditer(method_pattern, content, re.MULTILINE | re.DOTALL))
        
        if method_matches:
            # Insert after the last method
            last_match = method_matches[-1]
            insert_pos = last_match.end()
        else:
            # Find the last field definition
            field_pattern = r'(\s+\w+\s*=\s*fields\.\w+\([^)]*(?:\([^)]*\))*[^)]*\)(?:\s*#[^\n]*)?)\n'
            field_matches = list(re.finditer(field_pattern, content))
            if field_matches:
                last_match = field_matches[-1]
                insert_pos = last_match.end()
            else:
                # Find class definition
                class_pattern = r'(class\s+\w+\([^)]+\):\s*(?:\s*"""[^"]*""")?\s*(?:\s*_name\s*=.*\n)*)'
                class_match = re.search(class_pattern, content)
                if class_match:
                    insert_pos = class_match.end()
                else:
                    return False
        
        content = content[:insert_pos] + "\n" + method_definition + "\n" + content[insert_pos:]
        
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error adding compute method to {model_file}: {e}")
        return False

def check_method_exists(model_file, method_name):
    """Check if method already exists in model"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"def {method_name}(" in content
    except:
        return False

def fix_missing_compute_methods():
    """Add missing compute methods"""
    
    print("🔧 MISSING COMPUTE METHODS FIXER - PHASE 3")
    print("=" * 60)
    
    models_dir = os.path.join(workspace_path, 'records_management', 'models')
    
    # Critical compute methods needed
    compute_methods = {
        'records_box.py': [
            '''    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute number of documents in container"""
        for record in self:
            record.document_count = len(record.document_ids)''',
            
            '''    @api.depends('actual_weight', 'estimated_weight')
    def _compute_weight(self):
        """Compute effective weight"""
        for record in self:
            record.weight = record.actual_weight or record.estimated_weight or 0.0''',
            
            '''    @api.depends('container_type')
    def _compute_container_type_display(self):
        """Compute container type display"""
        for record in self:
            if record.container_type:
                record.container_type_display = dict(record._fields['container_type'].selection).get(record.container_type, record.container_type)
            else:
                record.container_type_display = ''\''''
        ],
        
        'records_location.py': [
            '''    @api.depends('box_ids')
    def _compute_box_count(self):
        """Calculate total number of boxes in this location"""
        for record in self:
            record.box_count = len(record.box_ids)''',
            
            '''    @api.depends('box_count', 'max_capacity')
    def _compute_utilization(self):
        """Calculate current utilization percentage"""
        for record in self:
            if record.max_capacity and record.max_capacity > 0:
                record.current_utilization = (record.box_count / record.max_capacity) * 100
            else:
                record.current_utilization = 0.0''',
            
            '''    @api.depends('box_count', 'max_capacity')
    def _compute_available_space(self):
        """Calculate available space"""
        for record in self:
            record.available_space = max(0, (record.max_capacity or 0) - record.box_count)'''
        ],
        
        'shredding_service.py': [
            '''    @api.depends('actual_start_time', 'actual_completion_time')
    def _compute_actual_duration(self):
        """Calculate actual service duration"""
        for record in self:
            if record.actual_start_time and record.actual_completion_time:
                delta = record.actual_completion_time - record.actual_start_time
                record.actual_duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                record.actual_duration = 0.0''',
            
            '''    @api.depends('destruction_item_ids', 'destruction_item_ids.weight')
    def _compute_total_weight(self):
        """Calculate total weight from items"""
        for record in self:
            record.total_weight = sum(record.destruction_item_ids.mapped('weight'))''',
            
            '''    @api.depends('hourly_rate', 'actual_duration')
    def _compute_total_cost(self):
        """Calculate total service cost"""
        for record in self:
            if record.hourly_rate and record.actual_duration:
                record.total_cost = record.hourly_rate * record.actual_duration
            else:
                record.total_cost = 0.0'''
        ],
        
        'billing.py': [
            '''    @api.depends('subtotal', 'tax_amount', 'discount_amount')
    def _compute_total_amount(self):
        """Calculate total amount"""
        for record in self:
            record.total_amount = (record.subtotal or 0.0) + (record.tax_amount or 0.0) - (record.discount_amount or 0.0)'''
        ],
        
        'paper_bale_recycling.py': [
            '''    @api.depends('gross_weight', 'tare_weight')
    def _compute_net_weight(self):
        """Calculate net weight"""
        for record in self:
            record.net_weight = (record.gross_weight or 0.0) - (record.tare_weight or 0.0)''',
            
            '''    @api.depends('net_weight', 'price_per_ton')
    def _compute_total_revenue(self):
        """Calculate total revenue from bale"""
        for record in self:
            if record.net_weight and record.price_per_ton:
                # Convert weight to tons (assuming weight is in lbs)
                weight_tons = record.net_weight / 2000.0
                record.total_revenue = weight_tons * record.price_per_ton
            else:
                record.total_revenue = 0.0'''
        ],
        
        'records_document.py': [
            '''    @api.depends('received_date', 'document_type_id')
    def _compute_destruction_eligible_date(self):
        """Calculate destruction eligible date based on retention policy"""
        for record in self:
            if record.received_date and record.document_type_id and record.document_type_id.retention_years:
                from dateutil.relativedelta import relativedelta
                record.destruction_eligible_date = record.received_date + relativedelta(years=record.document_type_id.retention_years)
            else:
                record.destruction_eligible_date = False'''
        ],
        
        'bin_unlock_service.py': [
            '''    @api.depends('service_start_time', 'service_end_time')
    def _compute_service_duration(self):
        """Calculate service duration"""
        for record in self:
            if record.service_start_time and record.service_end_time:
                delta = record.service_end_time - record.service_start_time
                record.service_duration = delta.total_seconds() / 3600.0  # Hours
            else:
                record.service_duration = 0.0''',
            
            '''    @api.depends('service_rate', 'service_duration')
    def _compute_total_cost(self):
        """Calculate total service cost"""
        for record in self:
            record.total_cost = (record.service_rate or 0.0) * (record.service_duration or 0.0)'''
        ],
        
        'advanced_billing.py': [
            '''    @api.depends('billing_line_ids', 'billing_line_ids.subtotal')
    def _compute_subtotal(self):
        """Calculate billing subtotal"""
        for record in self:
            record.subtotal = sum(record.billing_line_ids.mapped('subtotal'))''',
            
            '''    @api.depends('billing_ids', 'billing_ids.total_amount')
    def _compute_total(self):
        """Calculate total from billing lines"""
        for record in self:
            record.total_amount = sum(record.billing_ids.mapped('total_amount'))''',
            
            '''    @api.depends('quantity', 'unit_price')
    def _compute_line_total(self):
        """Calculate line total"""
        for record in self:
            record.line_total = (record.quantity or 0.0) * (record.unit_price or 0.0)'''
        ],
        
        'hr_employee.py': [
            '''    @api.depends('naid_certification_date')
    def _compute_certification_status(self):
        """Compute NAID certification status"""
        for record in self:
            if record.naid_certification_date:
                from datetime import date
                days_since = (date.today() - record.naid_certification_date).days
                if days_since > 365:
                    record.certification_status = 'expired'
                elif days_since > 330:
                    record.certification_status = 'expiring'
                else:
                    record.certification_status = 'valid'
            else:
                record.certification_status = 'none\''''
            
            '''    @api.depends('records_access_level')
    def _compute_access_description(self):
        """Compute access level description"""
        for record in self:
            access_levels = {
                'basic': 'Basic access to public records',
                'standard': 'Standard access to most records',
                'elevated': 'Elevated access including confidential records',
                'admin': 'Full administrative access to all records'
            }
            record.access_description = access_levels.get(record.records_access_level, 'No access defined')'''
        ],
        
        'records_vehicle.py': [
            '''    @api.depends('vehicle_capacity_weight')
    def _compute_capacity_status(self):
        """Compute vehicle capacity status"""
        for record in self:
            if record.vehicle_capacity_weight:
                if record.vehicle_capacity_weight >= 10000:
                    record.capacity_status = 'heavy_duty'
                elif record.vehicle_capacity_weight >= 5000:
                    record.capacity_status = 'medium_duty'
                else:
                    record.capacity_status = 'light_duty'
            else:
                record.capacity_status = 'unknown\''''
        ],
        
        'container.py': [
            '''    @api.depends('length', 'width', 'height')
    def _compute_volume(self):
        """Calculate container volume"""
        for record in self:
            record.volume = (record.length or 0.0) * (record.width or 0.0) * (record.height or 0.0)''',
            
            '''    @api.depends('box_ids')
    def _compute_box_count(self):
        """Count boxes in container"""
        for record in self:
            record.box_count = len(record.box_ids)'''
        ]
    }
    
    total_added = 0
    
    for model_file, methods_to_add in compute_methods.items():
        model_path = os.path.join(models_dir, model_file)
        
        if os.path.exists(model_path):
            print(f"\n📄 Processing {model_file}...")
            
            for method_definition in methods_to_add:
                # Extract method name from definition
                method_match = re.search(r'def\s+(\w+)\(', method_definition)
                if method_match:
                    method_name = method_match.group(1)
                    
                    # Check if method already exists
                    if check_method_exists(model_path, method_name):
                        print(f"  ✅ {method_name} already exists")
                        continue
                    
                    # Add the method
                    success = add_compute_method_to_model(model_path, method_definition)
                    if success:
                        print(f"  ➕ Added {method_name}")
                        total_added += 1
                    else:
                        print(f"  ❌ Failed to add {method_name}")
        else:
            print(f"  ⚠️  Model file {model_file} not found, skipping...")
    
    print(f"\n🎯 PHASE 3 SUMMARY: Added {total_added} compute methods")
    print("=" * 60)

if __name__ == "__main__":
    fix_missing_compute_methods()
