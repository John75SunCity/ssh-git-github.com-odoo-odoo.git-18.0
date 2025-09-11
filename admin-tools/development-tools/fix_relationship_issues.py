#!/usr/bin/env python3
"""
Comprehensive fix for relationship issues identified in the audit report.
This script will address the 104 fixable issues found.
"""

import os
import re
import json

class RelationshipFixer:
    def __init__(self, base_path):
        self.base_path = base_path
        self.models_path = os.path.join(base_path, "records_management", "models")
        self.fixes_applied = 0
        
    def add_missing_inverse_fields(self):
        """Add missing inverse fields for One2many relationships."""
        
        fixes = [
            # 1. Add document_type_id to records.container (records_chain_of_custody.py)
            {
                'file': 'records_chain_of_custody.py',
                'field': 'document_type_id = fields.Many2one("records.document.type", string="Document Type")',
                'after_line': '    # Security and access'
            },
            # 2. Add temp_inventory_id to records.container
            {
                'file': 'records_chain_of_custody.py', 
                'field': 'temp_inventory_id = fields.Many2one("temp.inventory", string="Temporary Inventory")',
                'after_line': '    # Security and access'
            },
            # 3. Add container_type_id to records.container
            {
                'file': 'records_chain_of_custody.py',
                'field': 'container_type_id = fields.Many2one("records.container.type", string="Container Type")',
                'after_line': '    # Security and access'
            },
            # 4. Add department_id to records.container  
            {
                'file': 'records_chain_of_custody.py',
                'field': 'department_id = fields.Many2one("records.department", string="Department")',
                'after_line': '    # Security and access'
            },
            # 5. Add location_id to records.container
            {
                'file': 'records_chain_of_custody.py',
                'field': 'location_id = fields.Many2one("records.location", string="Storage Location")',
                'after_line': '    # Security and access'
            },
            # 6. Add coordinator_id to file.retrieval.work.order
            {
                'file': 'file_retrieval_work_order_item.py',
                'field': 'coordinator_id = fields.Many2one("work.order.coordinator", string="Coordinator")',
                'after_line': '    # Related fields'
            },
            # 7. Add coordinator_id to scan.retrieval.work.order
            {
                'file': 'scan_digital_asset.py',
                'field': 'coordinator_id = fields.Many2one("work.order.coordinator", string="Coordinator")',
                'after_line': '    # Relations'
            },
            # 8. Add department_id to records.department.billing.contact
            {
                'file': 'records_department_billing_approval.py',
                'field': 'department_id = fields.Many2one("records.department", string="Department")',
                'after_line': '    # Basic fields'
            },
            # 9. Add parent_policy_id to records.retention.policy
            {
                'file': 'records_retention_policy_version.py',
                'field': 'parent_policy_id = fields.Many2one("records.retention.policy", string="Parent Policy")',
                'after_line': '    # Relations'
            }
        ]
        
        for fix in fixes:
            self._add_field_to_file(fix['file'], fix['field'], fix['after_line'])
    
    def _add_field_to_file(self, filename, field_def, after_line):
        """Add a field definition to a model file."""
        file_path = os.path.join(self.models_path, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {filename}")
            return
            
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Find the insertion point
            insert_idx = -1
            for i, line in enumerate(lines):
                if after_line in line:
                    insert_idx = i + 1
                    break
            
            if insert_idx == -1:
                # If specific line not found, add after class definition
                for i, line in enumerate(lines):
                    if line.strip().startswith('class ') and 'models.Model' in line:
                        insert_idx = i + 2  # After class line and docstring
                        break
            
            if insert_idx != -1:
                # Insert the field
                lines.insert(insert_idx, f"    {field_def}\n")
                
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                    
                print(f"✅ Added field to {filename}: {field_def}")
                self.fixes_applied += 1
            else:
                print(f"⚠️  Could not find insertion point in {filename}")
                
        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")
    
    def fix_comodel_references(self):
        """Fix incorrect comodel references."""
        
        comodel_fixes = [
            # Standard Odoo model fixes - keep these as standard
            {
                'file': 'records_document_type.py',
                'old': '"hr.department"',
                'new': '"hr.department"',  # Keep standard
                'field': 'department_id'
            },
            # Location fixes - these should point to records.location, not stock.location
            {
                'file': 'records_container.py', 
                'old': '"stock.location"',
                'new': '"records.location"',
                'field': 'location_id'
            },
            {
                'file': 'temp_inventory.py',
                'old': '"stock.location"',
                'new': '"records.location"',
                'field': 'location_id'
            },
            # Attachment fixes - use standard ir.attachment
            {
                'file': 'container_access_document.py',
                'old': '"ir.attachment"',
                'new': '"ir.attachment"',  # Keep standard
                'field': 'attachment_id'
            },
            # Product fixes - use standard product.product
            {
                'file': 'inventory_item.py',
                'old': '"product.product"',
                'new': '"product.product"',  # Keep standard
                'field': 'product_id'
            }
        ]
        
        for fix in comodel_fixes:
            self._replace_comodel_in_file(fix['file'], fix['old'], fix['new'], fix['field'])
    
    def _replace_comodel_in_file(self, filename, old_comodel, new_comodel, field_name):
        """Replace comodel reference in a file."""
        file_path = os.path.join(self.models_path, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {filename}")
            return
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for the specific field definition
            pattern = rf'({field_name}\s*=\s*fields\.[A-Za-z2]+\(\s*){re.escape(old_comodel)}'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, rf'\1{new_comodel}', content)
                
                with open(file_path, 'w') as f:
                    f.write(new_content)
                    
                print(f"✅ Updated comodel in {filename}: {field_name} {old_comodel} → {new_comodel}")
                self.fixes_applied += 1
            else:
                print(f"⚠️  Pattern not found in {filename}: {field_name}")
                
        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")
    
    def add_missing_xml_fields(self):
        """Add missing fields that are referenced in XML but missing from models."""
        
        xml_field_fixes = [
            {
                'file': 'records_category.py',
                'fields': [
                    'code = fields.Char(string="Code")',
                    'arch = fields.Text(string="Architecture")', 
                    'state = fields.Selection([("draft", "Draft"), ("active", "Active")], default="draft")',
                    'model = fields.Char(string="Related Model")'
                ]
            }
        ]
        
        for fix in xml_field_fixes:
            file_path = os.path.join(self.models_path, fix['file'])
            
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {fix['file']}")
                continue
                
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Find insertion point after existing fields
                insert_idx = -1
                for i in range(len(lines)-1, -1, -1):
                    line = lines[i].strip()
                    if line.startswith('name =') or line.startswith('description ='):
                        insert_idx = i + 1
                        break
                
                if insert_idx != -1:
                    for field_def in fix['fields']:
                        lines.insert(insert_idx, f"    {field_def}\n")
                        insert_idx += 1
                    
                    with open(file_path, 'w') as f:
                        f.writelines(lines)
                        
                    print(f"✅ Added XML fields to {fix['file']}: {len(fix['fields'])} fields")
                    self.fixes_applied += len(fix['fields'])
                    
            except Exception as e:
                print(f"❌ Error updating {fix['file']}: {e}")
    
    def fix_mail_activity_references(self):
        """Fix mail.activity references by removing them or replacing with existing models."""
        
        # Many models inherit mail.thread which automatically provides activity_ids, message_ids, etc.
        # We should ensure they properly inherit mail.thread
        
        mail_fixes = [
            'barcode_storage_box.py',
            'records_department_billing_contact.py', 
            'location_report_wizard.py',
            'key_restriction_checker.py',
            'records_document_type.py',
            'transitory_field_config.py'
        ]
        
        for filename in mail_fixes:
            self._ensure_mail_thread_inheritance(filename)
    
    def _ensure_mail_thread_inheritance(self, filename):
        """Ensure a model properly inherits from mail.thread."""
        file_path = os.path.join(self.models_path, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {filename}")
            return
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if it already inherits mail.thread
            if "'mail.thread'" in content or '"mail.thread"' in content:
                print(f"✅ {filename} already inherits mail.thread")
                return
            
            # Find the _inherit line and add mail.thread
            inherit_pattern = r'(_inherit\s*=\s*\[)([^\]]+)(\])'
            match = re.search(inherit_pattern, content)
            
            if match:
                existing_inherits = match.group(2)
                new_inherits = f"{existing_inherits}, 'mail.thread'"
                new_content = content.replace(match.group(0), f"{match.group(1)}{new_inherits}{match.group(3)}")
                
                with open(file_path, 'w') as f:
                    f.write(new_content)
                    
                print(f"✅ Added mail.thread inheritance to {filename}")
                self.fixes_applied += 1
            else:
                # Add _inherit if it doesn't exist
                class_pattern = r'(class\s+\w+\([^)]+\):)'
                if re.search(class_pattern, content):
                    new_content = re.sub(class_pattern, r'\1\n    _inherit = [\'mail.thread\']', content)
                    
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                        
                    print(f"✅ Added _inherit = ['mail.thread'] to {filename}")
                    self.fixes_applied += 1
                    
        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")
    
    def run_all_fixes(self):
        """Run all relationship fixes."""
        print("🔧 Starting comprehensive relationship fixes...")
        print(f"📁 Working directory: {self.models_path}")
        
        print("\n1️⃣ Adding missing inverse fields...")
        self.add_missing_inverse_fields()
        
        print("\n2️⃣ Fixing comodel references...")
        self.fix_comodel_references()
        
        print("\n3️⃣ Adding missing XML fields...")
        self.add_missing_xml_fields()
        
        print("\n4️⃣ Fixing mail.activity references...")
        self.fix_mail_activity_references()
        
        print(f"\n✅ COMPLETED: Applied {self.fixes_applied} fixes!")
        
        return self.fixes_applied

def main():
    # Get the current working directory
    base_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0"
    
    fixer = RelationshipFixer(base_path)
    fixes_applied = fixer.run_all_fixes()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total fixes applied: {fixes_applied}")
    print(f"   Target fixes from audit: 104")
    print(f"   Progress: {(fixes_applied/104)*100:.1f}%")
    
    print(f"\n🔄 Next steps:")
    print(f"   1. Run syntax validation")
    print(f"   2. Test module loading")
    print(f"   3. Run comprehensive audit again to verify fixes")

if __name__ == "__main__":
    main()
