#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional Missing Fields Fixer - Phase 2
Fix remaining critical missing fields identified from view analysis
"""

import os
import re
import sys

workspace_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'
sys.path.insert(0, workspace_path)

def add_field_to_model(model_file, field_name, field_definition):
    """Add field to model file with proper formatting"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the last field definition in the file to insert after it
        field_pattern = r'(\s+\w+\s*=\s*fields\.\w+\([^)]*(?:\([^)]*\))*[^)]*\)(?:\s*#[^\n]*)?)\n'
        field_matches = list(re.finditer(field_pattern, content))
        
        if field_matches:
            # Insert after the last field
            last_match = field_matches[-1]
            insert_pos = last_match.end()
            content = content[:insert_pos] + f"    {field_definition}\n" + content[insert_pos:]
        else:
            # Find class definition and insert after it
            class_pattern = r'(class\s+\w+\([^)]+\):\s*(?:\s*"""[^"]*""")?\s*(?:\s*_name\s*=.*\n)?\s*(?:\s*_description\s*=.*\n)?\s*(?:\s*_inherit\s*=.*\n)?\s*(?:\s*_order\s*=.*\n)?\s*(?:\s*_rec_name\s*=.*\n)?)'
            class_match = re.search(class_pattern, content)
            if class_match:
                insert_pos = class_match.end()
                content = content[:insert_pos] + f"\n    {field_definition}\n" + content[insert_pos:]
        
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error adding {field_name} to {model_file}: {e}")
        return False

def check_field_exists(model_file, field_name):
    """Check if field already exists in model"""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"{field_name} = fields." in content
    except:
        return False

def fix_additional_missing_fields():
    """Fix additional missing fields from analysis"""
    
    print("🔧 ADDITIONAL MISSING FIELDS FIXER - PHASE 2")
    print("=" * 60)
    
    models_dir = os.path.join(workspace_path, 'records_management', 'models')
    
    # Additional critical fields identified from comprehensive analysis
    additional_fixes = {
        # Records Box Model - Critical fields from analysis
        'records_box.py': [
            "document_ids = fields.One2many('records.document', 'container_id', string='Documents')",
            "actual_weight = fields.Float(string='Actual Weight (lbs)', tracking=True)",
            "container_type = fields.Selection([('01', 'Standard'), ('03', 'Map'), ('04', 'Pallet'), ('05', 'Pathology'), ('06', 'Specialty')], string='Container Type', default='01')",
            "box_ids = fields.One2many('records.box', 'parent_container_id', string='Child Boxes')",
        ],
        
        # Records Location Model - Missing computed fields
        'records_location.py': [
            "box_ids = fields.One2many('records.container', 'location_id', string='Stored Boxes')",
            "box_count = fields.Integer(string='Box Count', compute='_compute_box_count', store=True)",
            "current_utilization = fields.Float(string='Current Utilization (%)', compute='_compute_utilization')",
            "available_space = fields.Integer(string='Available Space', compute='_compute_available_space')",
            "max_capacity = fields.Integer(string='Maximum Capacity', default=1000)",
        ],
        
        # Shredding Service Model - Critical workflow fields
        'shredding_service.py': [
            "destruction_item_ids = fields.One2many('destruction.item', 'shredding_service_id', string='Items for Destruction')",
            "witness_ids = fields.Many2many('res.users', string='Witnesses')",
            "hourly_rate = fields.Float(string='Hourly Rate', default=75.0)",
            "actual_start_time = fields.Datetime(string='Actual Start Time')",
        ],
        
        # NAID Destruction Record - Critical compliance fields
        'naid_destruction_record.py': [
            "witness_ids = fields.Many2many('res.users', string='Witnesses')",
            "destruction_item_ids = fields.One2many('destruction.item', 'destruction_record_id', string='Destroyed Items')",
        ],
        
        # Paper Bale Recycling - Weight tracking
        'paper_bale_recycling.py': [
            "gross_weight = fields.Float(string='Gross Weight (lbs)', required=True)",
            "net_weight = fields.Float(string='Net Weight (lbs)', compute='_compute_net_weight', store=True)",
        ],
        
        # Field Label Customization - Customer specific fields
        'field_label_customization.py': [
            "label_box_number = fields.Char(string='Box Number Label', default='Box Number')",
            "customer_id = fields.Many2one('res.partner', string='Customer', domain=[('is_company', '=', True)])",
        ],
        
        # Container Model - Document tracking
        'container.py': [
            "length = fields.Float(string='Length (ft)')",
            "box_ids = fields.One2many('records.box', 'parent_container_id', string='Boxes')",
        ],
        
        # Document Retrieval Work Order - Workflow tracking
        'document_retrieval_work_order.py': [
            "item_count = fields.Integer(string='Item Count', default=1)",
        ],
        
        # Billing Models - Financial tracking
        'billing.py': [
            "total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)",
        ],
        
        # Records Document Model - Document lifecycle
        'records_document.py': [
            "received_date = fields.Date(string='Received Date', default=fields.Date.today)",
            "destruction_eligible_date = fields.Date(string='Destruction Eligible Date', compute='_compute_destruction_eligible_date')",
        ],
        
        # Records Document Type - Classification
        'records_document_type.py': [
            "name = fields.Char(string='Document Type Name', required=True)",
        ],
        
        # Bin Unlock Service - Service tracking
        'bin_unlock_service.py': [
            "service_start_time = fields.Datetime(string='Service Start Time')",
            "service_rate = fields.Float(string='Service Rate', default=25.0)",
            "invoice_id = fields.Many2one('account.move', string='Invoice')",
        ],
        
        # Shredding Service Log - Time tracking
        'shredding_service_log.py': [
            "duration_minutes = fields.Float(string='Duration (Minutes)')",
        ],
        
        # Res Partner Key Restriction - Security fields
        'res_partner_key_restriction.py': [
            "key_issuance_allowed = fields.Boolean(string='Key Issuance Allowed', default=True)",
        ],
        
        # Customer Retrieval Rates - Rate management
        'customer_retrieval_rates.py': [
            "partner_id = fields.Many2one('res.partner', string='Customer', required=True)",
        ],
        
        # File Retrieval Work Order - Service tracking
        'file_retrieval_work_order.py': [
            "retrieval_item_ids = fields.One2many('retrieval.item', 'work_order_id', string='Items to Retrieve')",
            "rate_id = fields.Many2one('base.rates', string='Applicable Rate')",
            "invoice_id = fields.Many2one('account.move', string='Invoice')",
        ],
        
        # Visitor POS Wizard - Processing fields
        'visitor_pos_wizard.py': [
            "quantity = fields.Float(string='Quantity', default=1.0)",
            "processing_start_time = fields.Datetime(string='Processing Start Time')",
        ],
        
        # Transitory Field Config - Configuration management
        'transitory_field_config.py': [
            "customer_id = fields.Many2one('res.partner', string='Customer', required=True)",
            "show_box_number = fields.Boolean(string='Show Box Number', default=True)",
        ],
        
        # Records Container Movement - Movement tracking
        'records_container_movement.py': [
            "actual_start_time = fields.Datetime(string='Actual Start Time')",
            "state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='draft')",
        ],
        
        # Records Box Movement - Box movement tracking  
        'records_box_movement.py': [
            "actual_start_time = fields.Datetime(string='Actual Start Time')",
            "state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='draft')",
        ],
        
        # Records Chain of Custody - Audit trail
        'records_chain_of_custody.py': [
            "transfer_date = fields.Datetime(string='Transfer Date', default=fields.Datetime.now)",
            "verified = fields.Boolean(string='Verified', default=False)",
        ],
    }
    
    total_added = 0
    
    for model_file, fields_to_add in additional_fixes.items():
        model_path = os.path.join(models_dir, model_file)
        
        if os.path.exists(model_path):
            print(f"\n📄 Processing {model_file}...")
            
            for field_definition in fields_to_add:
                # Extract field name from definition
                field_name = field_definition.split('=')[0].strip()
                
                # Check if field already exists
                if check_field_exists(model_path, field_name):
                    print(f"  ✅ {field_name} already exists")
                    continue
                
                # Add the field
                success = add_field_to_model(model_path, field_name, field_definition)
                if success:
                    print(f"  ➕ Added {field_name}")
                    total_added += 1
                else:
                    print(f"  ❌ Failed to add {field_name}")
        else:
            print(f"  ⚠️  Model file {model_file} not found, skipping...")
    
    print(f"\n🎯 PHASE 2 SUMMARY: Added {total_added} additional missing fields")
    print("=" * 60)

if __name__ == "__main__":
    fix_additional_missing_fields()
