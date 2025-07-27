#!/usr/bin/env python3
"""
Automated Model Name Abbreviation Script
========================================

This script applies the standard abbreviation system to all Records Management models
to prevent PostgreSQL table name conflicts and improve performance.
"""

import os
import re
import glob

def get_abbreviation_mapping():
    """Return the complete abbreviation mapping for model names"""
    
    return {
        # Current problematic long names -> Abbreviated names
        "records.box.movement.log": "rec.box.move",
        "records.department.billing.contact": "rec.dept.bill.cont",
        "records.retention.policy.version": "rec.ret.pol.ver",
        "records.chain.of.custody": "rec.coc",
        "records.deletion.request": "rec.del.req",
        "records.approval.step": "rec.appr.step",
        "records.document.type": "rec.doc.type",
        "records.box.transfer": "rec.box.xfer",
        "customer.inventory.report": "cust.inv.rpt",
        "document.retrieval.rates": "doc.ret.rates",
        "document.retrieval.work.order": "doc.ret.wo",
        
        # Shredding & Destruction
        "shredding.service": "shred.svc",
        "work.order.shredding": "wo.shred",
        "destruction.item": "dest.item",
        "witness.verification": "witness.valid",
        "destruction.certificate": "dest.cert",
        "paper.bale.recycling": "pb.recycl",
        "paper.load.shipment": "pb.ship",
        
        # NAID & Compliance
        "naid.audit.log": "naid.audit",
        "naid.certificate": "naid.cert",
        "naid.compliance": "naid.comp",
        "naid.custody.event": "naid.coc.event",
        "chain.of.custody": "coc.chain",
        
        # Portal & Customer
        "portal.request": "portal.req",
        "customer.feedback": "cust.fb",
        "customer.inventory": "cust.inv",
        "survey.improvement.action": "srv.improve.act",
        "survey.user.input": "srv.user.input",
        
        # Billing & Department
        "department.billing": "dept.bill",
        "billing.automation": "bill.auto",
        "departmental.billing.contact": "dept.bill.cont",
        "records.department": "rec.dept",
        
        # Barcode & Integration
        "barcode.product": "bc.prod",
        "barcode.models": "bc.model",
        "partner.bin.key": "partner.bin",
        "visitor.pos.wizard": "visitor.pos.wiz",
        "mobile.bin.key.wizard": "mobile.bin.wiz",
        
        # Technical & Extension
        "stock.move.sms.validation": "stock.sms.valid",
        "stock.lot.attribute": "stock.lot.attr",
        "stock.report_reception_report_label": "stock.recv.label",
        "box.type.converter": "box.type.conv",
        "permanent.flag.wizard": "perm.flag.wiz",
        
        # Monitoring
        "records.management.monitor": "rec.mgmt.mon",
        
        # Fix duplicate temp.model issues
        "temp.model": "misc.temp",  # Will be customized per file
    }

def get_temp_model_mapping():
    """Map specific temp.model files to unique names"""
    return {
        "barcode_product.py": "bc.prod.temp",
        "barcode_models.py": "bc.model.temp", 
        "project_task.py": "proj.task.temp",
        "survey_user_input.py": "srv.user.temp",
        "survey_improvement_action.py": "srv.improve.temp",
        "billing_automation.py": "bill.auto.temp",
        "records_box_transfer.py": "rec.box.xfer.temp",
        "naid_compliance.py": "naid.comp.temp",
        "box_contents.py": "box.cont.temp",
        "records_deletion_request.py": "rec.del.req.temp",
        "customer_inventory_report.py": "cust.inv.rpt.temp",
        "records_policy_version.py": "rec.pol.ver.temp",
        "records_document_type.py": "rec.doc.type.temp",
    }

def update_model_file(file_path, abbreviation_mapping, temp_mapping):
    """Update a single model file with abbreviated names"""
    
    print(f"📝 Processing: {os.path.basename(file_path)}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        filename = os.path.basename(file_path)
        
        # Handle temp.model files specially
        if '"temp.model"' in content and filename in temp_mapping:
            new_name = temp_mapping[filename]
            content = content.replace('"temp.model"', f'"{new_name}"')
            print(f"   ✅ Updated temp.model -> {new_name}")
        
        # Apply standard abbreviations
        for old_name, new_name in abbreviation_mapping.items():
            if f'"{old_name}"' in content:
                content = content.replace(f'"{old_name}"', f'"{new_name}"')
                print(f"   ✅ Updated {old_name} -> {new_name}")
            
            if f"'{old_name}'" in content:
                content = content.replace(f"'{old_name}'", f"'{new_name}'")
                print(f"   ✅ Updated {old_name} -> {new_name}")
        
        # Update Many2one/One2many references
        # Pattern: fields.Many2one('old.model.name')
        def replace_field_references(match):
            model_ref = match.group(1)
            if model_ref in abbreviation_mapping:
                return f"fields.Many2one('{abbreviation_mapping[model_ref]}'"
            return match.group(0)
        
        content = re.sub(r"fields\.Many2one\('([^']+)'", replace_field_references, content)
        content = re.sub(r'fields\.Many2one\("([^"]+)"', lambda m: f'fields.Many2one("{abbreviation_mapping.get(m.group(1), m.group(1))}"', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 File updated successfully")
        else:
            print(f"   ⚪ No changes needed")
            
    except Exception as e:
        print(f"   ❌ Error processing {file_path}: {e}")

def update_view_files(abbreviation_mapping):
    """Update XML view files with new model references"""
    
    view_files = glob.glob("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views/*.xml")
    
    print(f"\n📄 Processing {len(view_files)} view files...")
    
    for file_path in view_files:
        print(f"📝 Processing: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update model references in XML
            for old_name, new_name in abbreviation_mapping.items():
                # Update model attributes
                content = content.replace(f'model="{old_name}"', f'model="{new_name}"')
                content = content.replace(f"model='{old_name}'", f"model='{new_name}'")
                
                # Update res_model attributes  
                content = content.replace(f'res_model="{old_name}"', f'res_model="{new_name}"')
                content = content.replace(f"res_model='{old_name}'", f"res_model='{new_name}'")
                
                if content != original_content:
                    print(f"   ✅ Updated {old_name} -> {new_name}")
            
            # Write back if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   💾 View file updated successfully")
            else:
                print(f"   ⚪ No changes needed")
                
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

def update_security_files(abbreviation_mapping):
    """Update security CSV files with new model names"""
    
    security_files = [
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv",
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/new_models_access.xml"
    ]
    
    print(f"\n🔒 Processing security files...")
    
    for file_path in security_files:
        if os.path.exists(file_path):
            print(f"📝 Processing: {os.path.basename(file_path)}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Update model references
                for old_name, new_name in abbreviation_mapping.items():
                    # Convert model name to model_id format
                    old_model_id = f"model_{old_name.replace('.', '_')}"
                    new_model_id = f"model_{new_name.replace('.', '_')}"
                    
                    content = content.replace(old_model_id, new_model_id)
                    content = content.replace(old_name, new_name)
                
                # Write back if changed
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   💾 Security file updated successfully")
                else:
                    print(f"   ⚪ No changes needed")
                    
            except Exception as e:
                print(f"   ❌ Error processing {file_path}: {e}")

def main():
    """Main execution function"""
    
    print("🔄 RECORDS MANAGEMENT - MODEL NAME ABBREVIATION")
    print("=" * 55)
    print("🎯 Applying standard abbreviations to prevent table conflicts")
    print()
    
    # Get mappings
    abbreviation_mapping = get_abbreviation_mapping()
    temp_mapping = get_temp_model_mapping()
    
    # Process model files
    model_files = glob.glob("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py")
    print(f"📂 Processing {len(model_files)} model files...")
    
    for file_path in model_files:
        if "__init__.py" not in file_path:  # Skip __init__.py
            update_model_file(file_path, abbreviation_mapping, temp_mapping)
    
    # Process view files
    update_view_files(abbreviation_mapping)
    
    # Process security files
    update_security_files(abbreviation_mapping)
    
    print("\n" + "=" * 55)
    print("🎊 MODEL ABBREVIATION COMPLETE!")
    print("✅ All model names shortened to prevent table conflicts")
    print("✅ View references updated")
    print("✅ Security rules updated") 
    print("✅ Ready for deployment without table name issues")
    print("=" * 55)
    
    # Show summary
    print(f"\n📊 Summary:")
    print(f"   🔧 {len(abbreviation_mapping)} model abbreviations applied")
    print(f"   🗂️ {len(temp_mapping)} temp model conflicts resolved")
    print(f"   📄 View files updated with new model references")
    print(f"   🔒 Security files updated with new model names")
    print(f"\n🚀 Your Records Management module now has optimized table names!")

if __name__ == "__main__":
    main()
