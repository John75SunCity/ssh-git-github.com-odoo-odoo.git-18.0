#!/usr/bin/env python3
"""
Categorize the 35 missing models to determine:
1. Core Odoo models that should exist (probably view issues)
2. Legitimate new models that need creation
3. Possible naming mismatches with existing models
"""

import os
import re
from collections import defaultdict

def get_existing_models():
    """Get all models that actually exist in the system"""
    models_dir = "records_management/models"
    existing_models = {}
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find _name definitions
                name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                for model_name in name_matches:
                    existing_models[model_name] = filename
                    
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return existing_models

def analyze_missing_models():
    """Categorize the 35 missing models"""
    
    # The 35 missing models from our validator
    missing_models = [
        "bin.issue.report.wizard",
        "custom.box.volume.calculator", 
        "customer.inventory.report.wizard",
        "document.retrieval.metrics",
        "field.label.helper.wizard",
        "file.retrieval",
        "file.retrieval.item", 
        "hr.employee",
        "ir.model",
        "ir.ui.view",
        "key.restriction.checker.wizard",
        "mobile.bin.key.wizard",
        "pos.config",
        "product.template",
        "rate.change.confirmation.wizard",
        "records.billing.config.line",
        "records.billing.line",
        "records.container.type.converter.wizard",
        "records.deletion.request.enhanced",
        "records.document.flag.permanent.wizard",
        "records.permanent.flag.wizard",
        "records.permanent.flag.wizard.manager",
        "records.user.invitation.wizard",
        "records_management.bale",
        "res.config.settings",
        "serial.number",
        "shredding.bin",
        "shredding.bin.barcode.wizard",
        "shredding.bin.sequence.reset.wizard",
        "shredding.inventory.item",
        "stock.picking.records.extension",
        "system.flowchart.wizard",
        "visitor.pos.wizard",
        "wizard.template",
        "work.order.bin.assignment.wizard"
    ]
    
    # Core Odoo models that definitely exist (views probably wrong)
    core_odoo_models = [
        "hr.employee",
        "ir.model", 
        "ir.ui.view",
        "pos.config",
        "product.template",
        "res.config.settings"
    ]
    
    # Wizard models (probably need creation)
    wizard_models = [
        "bin.issue.report.wizard",
        "custom.box.volume.calculator",
        "customer.inventory.report.wizard", 
        "field.label.helper.wizard",
        "key.restriction.checker.wizard",
        "mobile.bin.key.wizard",
        "rate.change.confirmation.wizard",
        "records.container.type.converter.wizard",
        "records.document.flag.permanent.wizard",
        "records.permanent.flag.wizard",
        "records.permanent.flag.wizard.manager",
        "records.user.invitation.wizard",
        "shredding.bin.barcode.wizard",
        "shredding.bin.sequence.reset.wizard",
        "system.flowchart.wizard",
        "visitor.pos.wizard",
        "wizard.template",
        "work.order.bin.assignment.wizard"
    ]
    
    # Business models (might need creation or renaming)
    business_models = [
        "document.retrieval.metrics",
        "file.retrieval",
        "file.retrieval.item",
        "records.billing.config.line", 
        "records.billing.line",
        "records.deletion.request.enhanced",
        "records_management.bale",
        "serial.number",
        "shredding.bin",
        "shredding.inventory.item",
        "stock.picking.records.extension"
    ]
    
    return core_odoo_models, wizard_models, business_models

def check_similar_existing_models():
    """Check if there are similar models that views should reference instead"""
    existing = get_existing_models()
    
    # Look for similar models
    similar_patterns = {
        "shredding.bin": ["shredding.service.bin"],
        "file.retrieval": ["records.file.retrieval", "container.retrieval"],
        "records.billing.line": ["records.billing", "billing.line"],
        "shredding.inventory.item": ["shredding.service", "inventory.item"]
    }
    
    print("🔍 CHECKING FOR SIMILAR EXISTING MODELS:")
    for missing, potential_matches in similar_patterns.items():
        print(f"\n❓ Missing: {missing}")
        for potential in potential_matches:
            if potential in existing:
                print(f"  ✅ Found similar: {potential} (in {existing[potential]})")
            else:
                print(f"  ❌ No match: {potential}")

def main():
    """Analyze what to do with the 35 missing models"""
    
    print("🎯 ANALYSIS: Do You Need 35 New Models or Fix References?")
    print("=" * 70)
    
    core_models, wizard_models, business_models = analyze_missing_models()
    existing_models = get_existing_models()
    
    print(f"\n📊 CATEGORIZATION OF 35 MISSING MODELS:")
    print(f"  🏢 Core Odoo Models (views probably wrong): {len(core_models)}")
    print(f"  🧙 Wizard Models (probably need creation): {len(wizard_models)}")  
    print(f"  💼 Business Models (need analysis): {len(business_models)}")
    
    print(f"\n🏢 CORE ODOO MODELS (Fix views, don't create models):")
    for model in core_models:
        print(f"  ❌ {model} - This is a core Odoo model, views are wrong!")
    
    print(f"\n🧙 WIZARD MODELS (Probably need creation):")
    for model in wizard_models:
        print(f"  🆕 {model}")
    
    print(f"\n💼 BUSINESS MODELS (Need individual analysis):")
    for model in business_models:
        print(f"  ❓ {model}")
    
    check_similar_existing_models()
    
    print(f"\n✅ RECOMMENDATIONS:")
    print(f"1. 🚫 DON'T CREATE core Odoo models ({len(core_models)} models)")
    print(f"   - Fix view inheritance instead")
    print(f"   - Example: hr.employee views should inherit/extend existing hr.employee")
    
    print(f"\n2. 🆕 CREATE wizard models ({len(wizard_models)} models)")
    print(f"   - These are legitimate business wizards")
    print(f"   - Create as TransientModel classes")
    
    print(f"\n3. 🔍 ANALYZE business models ({len(business_models)} models)")
    print(f"   - Check if similar models exist with different names")
    print(f"   - Consider if they're needed or views should reference existing models")
    
    print(f"\n📋 IMMEDIATE ACTION PLAN:")
    print(f"  1. Fix core Odoo model view references (6 models)")
    print(f"  2. Remove/fix views that incorrectly extend core models")
    print(f"  3. Create only necessary wizard models")
    print(f"  4. Consolidate business models with existing ones where possible")

if __name__ == "__main__":
    main()
