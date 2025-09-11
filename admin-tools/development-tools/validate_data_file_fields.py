#!/usr/bin/env python3
"""
Comprehensive Data File Field Validator

This script validates ALL field references in ALL data XML files to ensure
they exist in their corresponding models before Odoo tries to load them.
"""

import os
import sys
import glob
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import json

class DataFileFieldValidator:
    def __init__(self, module_path):
        self.module_path = module_path
        self.models_path = os.path.join(module_path, 'models')
        self.data_path = os.path.join(module_path, 'data')
        self.model_fields = {}  # model_name -> set of field names
        self.issues = []
        self.all_records = []  # All records found in data files
        
    def scan_models(self):
        """Scan all model files and extract field definitions, including inherited fields."""
        model_files = glob.glob(os.path.join(self.module_path, 'models', '*.py'))
        
        # Define common Odoo base model fields that are inherited
        base_odoo_fields = {
            'product.product': {
                'name', 'description', 'list_price', 'standard_price', 'cost', 'categ_id',
                'uom_id', 'uom_po_id', 'default_code', 'barcode', 'type', 'sale_ok', 'purchase_ok',
                'active', 'company_id', 'currency_id', 'taxes_id', 'supplier_taxes_id',
                'invoice_policy', 'expense_policy', 'detailed_type', 'tracking', 'weight',
                'volume', 'sale_line_warn', 'purchase_line_warn', 'sale_line_warn_msg',
                'purchase_line_warn_msg', 'product_tmpl_id', 'image_1920', 'can_image_1024_be_zoomed',
                'image_1024', 'image_512', 'image_256', 'image_128', 'website_sequence'
            },
            'product.template': {
                'name', 'description', 'list_price', 'standard_price', 'cost', 'categ_id',
                'uom_id', 'uom_po_id', 'default_code', 'barcode', 'type', 'sale_ok', 'purchase_ok',
                'active', 'company_id', 'currency_id', 'taxes_id', 'supplier_taxes_id',
                'invoice_policy', 'expense_policy', 'detailed_type', 'tracking', 'weight',
                'volume', 'sale_line_warn', 'purchase_line_warn', 'sale_line_warn_msg',
                'purchase_line_warn_msg', 'product_variant_ids', 'product_variant_count'
            },
            'res.partner': {
                'name', 'display_name', 'date', 'title', 'parent_id', 'child_ids', 'ref',
                'lang', 'tz', 'user_id', 'vat', 'bank_ids', 'website', 'comment', 'category_id',
                'credit_limit', 'active', 'customer_rank', 'supplier_rank', 'employee', 'function',
                'phone', 'mobile', 'email', 'street', 'street2', 'zip', 'city', 'state_id',
                'country_id', 'partner_latitude', 'partner_longitude', 'email_formatted',
                'commercial_partner_id', 'company_id', 'color', 'user_ids', 'partner_share',
                'contact_address', 'commercial_company_name', 'company_name', 'country_code',
                'is_company', 'is_public', 'partner_gid', 'additional_info', 'phone_sanitized',
                'mobile_sanitized'
            },
            'res.users': {
                'name', 'login', 'password', 'active', 'lang', 'tz', 'groups_id', 'partner_id',
                'company_id', 'company_ids', 'email', 'signature', 'action_id', 'menu_id',
                'new_password', 'password_crypt', 'login_date', 'share', 'sel_groups_1_2_3',
                'sel_groups_4_5_6_7_8_9', 'sel_groups_10_11', 'in_group_1', 'in_group_2',
                'in_group_3', 'in_group_4', 'in_group_5', 'in_group_6', 'in_group_7',
                'in_group_8', 'in_group_9', 'in_group_10', 'in_group_11'
            },
            'ir.sequence': {
                'name', 'code', 'implementation', 'active', 'prefix', 'suffix', 'padding',
                'number_increment', 'number_next_actual', 'number_next', 'use_date_range',
                'company_id'
            },
            'mail.template': {
                'name', 'model_id', 'model', 'subject', 'body_html', 'email_from',
                'email_to', 'email_cc', 'reply_to', 'mail_server_id', 'report_name',
                'report_template', 'lang', 'user_signature', 'auto_delete', 'partner_to',
                'attachment_ids', 'ref_ir_act_window'
            }
        }
        
        for model_file in model_files:
            if model_file.endswith('__init__.py'):
                continue
                
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract model names using _name and _inherit
                model_names = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                inherit_names = re.findall(r"_inherit\s*=\s*['\"]([^'\"]+)['\"]", content)
                
                # Process _name models (new models)
                for model_name in model_names:
                    if model_name not in self.model_fields:
                        self.model_fields[model_name] = set()
                    
                    # Extract field definitions
                    field_patterns = [
                        r"(\w+)\s*=\s*fields\.\w+\(",
                        r"(\w+)\s*=\s*fields\.\w+\s*\(",
                    ]
                    
                    for pattern in field_patterns:
                        fields_found = re.findall(pattern, content)
                        for field_name in fields_found:
                            if not field_name.startswith('_'):  # Skip private fields
                                self.model_fields[model_name].add(field_name)
                
                # Process _inherit models (extending existing models)
                for model_name in inherit_names:
                    if model_name not in self.model_fields:
                        self.model_fields[model_name] = set()
                    
                    # Add base Odoo fields if this model inherits from a known base model
                    if model_name in base_odoo_fields:
                        self.model_fields[model_name].update(base_odoo_fields[model_name])
                    
                    # Extract additional field definitions from the inheriting model
                    field_patterns = [
                        r"(\w+)\s*=\s*fields\.\w+\(",
                        r"(\w+)\s*=\s*fields\.\w+\s*\(",
                    ]
                    
                    for pattern in field_patterns:
                        fields_found = re.findall(pattern, content)
                        for field_name in fields_found:
                            if not field_name.startswith('_'):  # Skip private fields
                                self.model_fields[model_name].add(field_name)
                                
            except Exception as e:
                print(f"Error scanning {model_file}: {e}")
                continue
        
    def _extract_model_fields(self, filepath):
        """Extract all field definitions from a model file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract model names and their fields
            model_matches = re.finditer(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            inherit_matches = re.finditer(r'_inherit\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            
            model_names = []
            for match in model_matches:
                model_names.append(match.group(1))
            for match in inherit_matches:
                model_names.append(match.group(1))
                
            # Extract field definitions
            field_pattern = r'(\w+)\s*=\s*fields\.\w+'
            field_matches = re.finditer(field_pattern, content)
            
            fields = set()
            for match in field_matches:
                field_name = match.group(1)
                # Exclude private fields and methods
                if not field_name.startswith('_') and field_name not in ['self', 'fields']:
                    fields.add(field_name)
                    
            # Store fields for all model names found in this file
            for model_name in model_names:
                if model_name not in self.model_fields:
                    self.model_fields[model_name] = set()
                self.model_fields[model_name].update(fields)
                
        except Exception as e:
            print(f"❌ Error analyzing {filepath}: {e}")
            
    def scan_all_data_files(self):
        """Scan ALL data XML files for field references"""
        print("📋 Scanning ALL data files for field references...")
        
        data_files_found = 0
        for filename in os.listdir(self.data_path):
            if filename.endswith('.xml'):
                filepath = os.path.join(self.data_path, filename)
                print(f"   Checking: {filename}")
                self._validate_data_file(filepath)
                data_files_found += 1
                
        print(f"✅ Validated {data_files_found} data files")
        
    def _validate_data_file(self, filepath):
        """Validate all field references in a single data file"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Find all record elements
            for record in root.findall('.//record'):
                model_name = record.get('model')
                record_id = record.get('id', 'unknown')
                
                if not model_name:
                    continue
                    
                record_info = {
                    'file': os.path.basename(filepath),
                    'record_id': record_id,
                    'model': model_name,
                    'fields': [],
                    'issues': []
                }
                
                # Check all field elements in this record
                for field_elem in record.findall('field'):
                    field_name = field_elem.get('name')
                    if field_name:
                        record_info['fields'].append(field_name)
                        self._validate_field_exists(field_name, model_name, filepath, record_id, record_info)
                        
                self.all_records.append(record_info)
                
        except ET.ParseError as e:
            self.issues.append({
                'type': 'xml_parse_error',
                'severity': 'error',
                'file': os.path.basename(filepath),
                'message': f"XML parse error: {e}"
            })
        except Exception as e:
            self.issues.append({
                'type': 'file_error', 
                'severity': 'error',
                'file': os.path.basename(filepath),
                'message': f"Error processing file: {e}"
            })
            
    def _validate_field_exists(self, field_name, model_name, filepath, record_id, record_info):
        """Validate that a field exists in the specified model"""
        
        # Check if model exists
        if model_name not in self.model_fields:
            issue = {
                'type': 'unknown_model',
                'severity': 'warning',
                'file': os.path.basename(filepath),
                'record_id': record_id,
                'model': model_name,
                'field': field_name,
                'message': f"Model '{model_name}' not found in scanned models"
            }
            self.issues.append(issue)
            record_info['issues'].append(issue)
            return
            
        # Check if field exists in model
        model_fields = self.model_fields[model_name]
        if field_name not in model_fields:
            # Check for common Odoo base fields that might not be explicitly defined
            base_fields = {
                'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
                'display_name', '__last_update', 'name', 'active', 'company_id'
            }
            
            if field_name not in base_fields:
                issue = {
                    'type': 'invalid_field',
                    'severity': 'error',
                    'file': os.path.basename(filepath),
                    'record_id': record_id,
                    'model': model_name,
                    'field': field_name,
                    'message': f"Field '{field_name}' not found in model '{model_name}'"
                }
                self.issues.append(issue)
                record_info['issues'].append(issue)
                
    def generate_comprehensive_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE DATA FILE VALIDATION REPORT")
        print("="*80)
        
        # Summary statistics
        total_files = len(set(record['file'] for record in self.all_records))
        total_records = len(self.all_records)
        total_fields = sum(len(record['fields']) for record in self.all_records)
        error_count = len([i for i in self.issues if i['severity'] == 'error'])
        warning_count = len([i for i in self.issues if i['severity'] == 'warning'])
        
        print(f"\n📈 SUMMARY:")
        print(f"  Data files validated: {total_files}")
        print(f"  Total records checked: {total_records}")
        print(f"  Total field references: {total_fields}")
        print(f"  Models scanned: {len(self.model_fields)}")
        print(f"  Issues found: {len(self.issues)}")
        print(f"  Errors (will cause loading failures): {error_count}")
        print(f"  Warnings: {warning_count}")
        
        # Group issues by type and file
        issues_by_file = defaultdict(list)
        issues_by_type = defaultdict(list)
        
        for issue in self.issues:
            issues_by_file[issue['file']].append(issue)
            issues_by_type[issue['type']].append(issue)
            
        # Report critical errors first
        if error_count > 0:
            print(f"\n🚨 CRITICAL ERRORS (WILL CAUSE LOADING FAILURES):")
            print("-" * 60)
            
            error_issues = [i for i in self.issues if i['severity'] == 'error']
            for issue in error_issues:
                record_id = issue.get('record_id', 'unknown')
                print(f"  ❌ {issue['file']} :: {record_id}")
                print(f"     Model: {issue.get('model', 'N/A')}")
                print(f"     Field: {issue.get('field', 'N/A')}")
                print(f"     Issue: {issue['message']}")
                print()
                
        # Report by file
        if issues_by_file:
            print(f"\n📁 ISSUES BY FILE:")
            print("-" * 40)
            
            for filename, file_issues in issues_by_file.items():
                error_count_file = len([i for i in file_issues if i['severity'] == 'error'])
                warning_count_file = len([i for i in file_issues if i['severity'] == 'warning'])
                
                if error_count_file > 0:
                    print(f"  🔴 {filename}: {error_count_file} errors, {warning_count_file} warnings")
                elif warning_count_file > 0:
                    print(f"  🟡 {filename}: {warning_count_file} warnings")
                else:
                    print(f"  ✅ {filename}: No issues")
                    
        # Detailed field analysis
        print(f"\n🔍 MODEL FIELD COVERAGE:")
        print("-" * 40)
        
        models_used = set()
        for record in self.all_records:
            models_used.add(record['model'])
            
        for model in sorted(models_used):
            field_count = self.model_fields.get(model, set())
            if model in self.model_fields:
                print(f"  ✅ {model}: {len(field_count)} fields available")
            else:
                print(f"  ❓ {model}: Model not found in scanned files")
                
        # Save detailed report
        report_file = os.path.join(self.module_path, '..', 'development-tools', 'data_file_validation_report.json')
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'files_validated': total_files,
                    'records_checked': total_records,
                    'field_references': total_fields,
                    'models_scanned': len(self.model_fields),
                    'total_issues': len(self.issues),
                    'errors': error_count,
                    'warnings': warning_count
                },
                'issues': self.issues,
                'all_records': self.all_records,
                'model_fields': {k: list(v) for k, v in self.model_fields.items()},
                'validation_timestamp': '2025-08-28'
            }, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return error_count == 0
        
def main():
    module_path = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    print("🔬 Comprehensive Data File Field Validator")
    print("=" * 60)
    
    validator = DataFileFieldValidator(module_path)
    
    # Run validation steps
    validator.scan_models()
    validator.scan_all_data_files()
    
    # Generate comprehensive report
    success = validator.generate_comprehensive_report()
    
    if success:
        print("\n✅ All data file field references are valid!")
        print("   Module should load without field-related errors.")
        return 0
    else:
        print("\n❌ Data file field issues found - see report above")
        print("   Fix these before attempting to load the module.")
        return 1

if __name__ == '__main__':
    exit(main())
