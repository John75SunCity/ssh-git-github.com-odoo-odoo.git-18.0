#!/usr/bin/env python3
"""
Critical Field Adder Script
Systematically adds missing critical fields to Records Management models
"""

import os
import re

def add_critical_fields_to_model(filepath, model_name, missing_fields):
    """Add missing critical fields to a model file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the class definition
        class_match = re.search(r'class\s+\w+\([^)]+\):\s*\n', content)
        if not class_match:
            print(f"   ❌ Could not find class definition in {filepath}")
            return False
        
        # Find a good place to insert fields (after _description or _name)
        insertion_point = -1
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if '_description =' in line or '_name =' in line:
                # Find the end of this definition
                j = i
                while j < len(lines) and (lines[j].strip().endswith(',') or lines[j].strip().endswith('"') or lines[j].strip().endswith("'")) and not lines[j].strip().endswith(','):
                    j += 1
                insertion_point = j + 1
                break
        
        if insertion_point == -1:
            # Try to find after class definition
            for i, line in enumerate(lines):
                if 'class ' in line and '(models.' in line:
                    insertion_point = i + 1
                    while insertion_point < len(lines) and (lines[insertion_point].strip().startswith('_') or lines[insertion_point].strip() == ''):
                        insertion_point += 1
                    break
        
        if insertion_point == -1:
            print(f"   ❌ Could not find insertion point in {filepath}")
            return False
        
        # Generate field definitions
        fields_to_add = []
        
        if 'name' in missing_fields:
            fields_to_add.extend([
                "",
                "    # ============================================================================",
                "    # CORE IDENTIFICATION FIELDS",
                "    # ============================================================================",
                "    name = fields.Char(",
                "        string='Name',",
                "        required=True,",
                "        tracking=True,",
                "        index=True,",
                "        default=lambda self: _('New'),",
                "        help='Unique identifier for this record'",
                "    )"
            ])
        
        if 'active' in missing_fields:
            if 'name' not in missing_fields:
                fields_to_add.extend(["", "    # Framework fields"])
            fields_to_add.extend([
                "    active = fields.Boolean(",
                "        string='Active',",
                "        default=True,",
                "        tracking=True,",
                "        help='Set to false to hide this record'",
                "    )"
            ])
        
        if 'company_id' in missing_fields:
            fields_to_add.extend([
                "    company_id = fields.Many2one(",
                "        'res.company',",
                "        string='Company',",
                "        default=lambda self: self.env.company,",
                "        required=True,",
                "        index=True,",
                "        help='Company this record belongs to'",
                "    )"
            ])
        
        if 'state' in missing_fields:
            fields_to_add.extend([
                "    state = fields.Selection([",
                "        ('draft', 'Draft'),",
                "        ('confirmed', 'Confirmed'),", 
                "        ('done', 'Done'),",
                "        ('cancelled', 'Cancelled'),",
                "    ], string='Status', default='draft', tracking=True, required=True)"
            ])
        
        # Add auto-naming method if name field was added
        if 'name' in missing_fields:
            # Find a place to add the create method (at the end before last line)
            create_method = [
                "",
                "    # ============================================================================",
                "    # ORM METHODS",
                "    # ============================================================================",
                "    @api.model_create_multi",
                "    def create(self, vals_list):",
                "        \"\"\"Override create to add auto-numbering\"\"\"",
                "        for vals in vals_list:",
                "            if vals.get('name', _('New')) == _('New'):",
                f"                vals['name'] = self.env['ir.sequence'].next_by_code('{model_name}') or _('New')",
                "        return super().create(vals_list)"
            ]
            fields_to_add.extend(create_method)
        
        # Insert the fields
        lines[insertion_point:insertion_point] = fields_to_add
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"   ✅ Added {', '.join(missing_fields)} to {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating {filepath}: {e}")
        return False

# Models that need critical fields (from our analysis)
MODELS_TO_FIX = [
    ('records_management/models/invoice_generation_log.py', 'invoice.generation.log', ['name', 'active', 'company_id', 'state']),
    ('records_management/models/paper_bale_inspection.py', 'paper.bale.inspection', ['name', 'active', 'company_id', 'state']),
    ('records_management/models/paper_bale_source_document.py', 'paper.bale.source.document', ['name', 'active', 'company_id', 'state']),
    ('records_management/models/portal_feedback_communication.py', 'portal.feedback.communication', ['name', 'state']),
    ('records_management/models/portal_feedback_escalation.py', 'portal.feedback.escalation', ['name', 'state']),
    ('records_management/models/records_billing_line.py', 'records.billing.line', ['name', 'active', 'state']),
    ('records_management/models/records_usage_tracking.py', 'records.usage.tracking', ['name', 'active', 'company_id', 'state']),
    ('records_management/models/revenue_analytic.py', 'revenue.analytic', ['name', 'active', 'company_id', 'state']),
    ('records_management/models/signed_document_audit.py', 'signed.document.audit', ['name', 'active', 'company_id', 'state']),
    ('records_management/models/document_search_attempt.py', 'document.search.attempt', ['active', 'company_id', 'state']),
]

def main():
    """Main function"""
    print("🚀 Adding critical fields to Records Management models...\n")
    
    success_count = 0
    total_count = len(MODELS_TO_FIX)
    
    for filepath, model_name, missing_fields in MODELS_TO_FIX:
        print(f"🔧 Processing {model_name}...")
        if add_critical_fields_to_model(filepath, model_name, missing_fields):
            success_count += 1
        print()
    
    print(f"📊 Summary: {success_count}/{total_count} models updated successfully")
    
    if success_count > 0:
        print("\n✅ Critical fields added! You should now:")
        print("1. Run syntax validation")
        print("2. Check the analysis script again to see improvements")
        print("3. Test the updated models")

if __name__ == '__main__':
    main()
