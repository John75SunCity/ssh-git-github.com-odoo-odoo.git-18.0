#!/usr/bin/env python3
"""
Find all KeyError: 'partner_id' issues in One2many relationships
"""

import os
import re

def find_one2many_partner_id_issues():
    """Find One2many fields looking for partner_id that might not exist"""
    print("🔍 FINDING One2many FIELDS WITH partner_id INVERSE...")
    print("=" * 60)
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    issues_found = []
    
    # Pattern to find One2many fields with partner_id as inverse
    one2many_pattern = r'(\w+)\s*=\s*fields\.One2many\(\s*["\']([^"\']+)["\']\s*,\s*["\']partner_id["\']\s*,'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = re.findall(one2many_pattern, content, re.MULTILINE | re.DOTALL)
                
                for field_name, target_model in matches:
                    issues_found.append({
                        'file': filename,
                        'field': field_name,
                        'target_model': target_model,
                        'inverse': 'partner_id'
                    })
                    print(f"📋 {filename}: {field_name} -> {target_model} (looking for partner_id)")
                    
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
    
    return issues_found

def check_model_has_partner_id():
    """Check which models actually have partner_id fields"""
    print("\n🔍 CHECKING WHICH MODELS HAVE partner_id FIELDS...")
    print("=" * 60)
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    models_with_partner_id = []
    models_without_partner_id = []
    
    # Pattern to find partner_id field definitions
    partner_id_pattern = r'partner_id\s*=\s*fields\.'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Get model name from class definition
                model_pattern = r'class\s+(\w+)\(models\.Model\):\s+_name\s*=\s*["\']([^"\']+)["\']'
                model_matches = re.findall(model_pattern, content, re.MULTILINE | re.DOTALL)
                
                has_partner_id = bool(re.search(partner_id_pattern, content))
                
                for class_name, model_name in model_matches:
                    if has_partner_id:
                        models_with_partner_id.append((filename, class_name, model_name))
                        print(f"✅ {model_name} ({filename}): HAS partner_id")
                    else:
                        models_without_partner_id.append((filename, class_name, model_name))
                        print(f"❌ {model_name} ({filename}): NO partner_id")
                    
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
    
    return models_with_partner_id, models_without_partner_id

def find_potential_fixes():
    """Find potential fixes for the KeyError issues"""
    print("\n🔧 ANALYZING POTENTIAL FIXES...")
    print("=" * 60)
    
    # Get One2many relationships looking for partner_id
    one2many_issues = find_one2many_partner_id_issues()
    
    # Get models with/without partner_id
    with_partner_id, without_partner_id = check_model_has_partner_id()
    
    # Create lookup dictionaries
    model_has_partner_id = {}
    for filename, class_name, model_name in with_partner_id:
        model_has_partner_id[model_name] = True
    
    for filename, class_name, model_name in without_partner_id:
        model_has_partner_id[model_name] = False
    
    print(f"\n🎯 ANALYSIS RESULTS:")
    print(f"Found {len(one2many_issues)} One2many fields looking for partner_id")
    
    fixes_needed = []
    for issue in one2many_issues:
        target_model = issue['target_model']
        has_partner_id = model_has_partner_id.get(target_model, False)
        
        if not has_partner_id:
            fixes_needed.append({
                'target_model': target_model,
                'referencing_file': issue['file'],
                'field_name': issue['field']
            })
            print(f"🔧 NEEDS FIX: {target_model} needs partner_id field (referenced by {issue['file']}:{issue['field']})")
        else:
            print(f"✅ OK: {target_model} already has partner_id field")
    
    return fixes_needed

def suggest_fixes():
    """Suggest specific fixes for each model"""
    fixes_needed = find_potential_fixes()
    
    if not fixes_needed:
        print("\n✅ NO FIXES NEEDED - All models have required partner_id fields")
        return
    
    print(f"\n🔧 SPECIFIC FIXES NEEDED:")
    print("=" * 60)
    
    # Group by target model
    by_model = {}
    for fix in fixes_needed:
        model = fix['target_model']
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(fix)
    
    for model_name, fixes in by_model.items():
        print(f"\n📋 MODEL: {model_name}")
        print(f"   Referenced by: {', '.join([f['referencing_file'] + ':' + f['field_name'] for f in fixes])}")
        
        # Suggest the fix based on model type
        if 'work.order' in model_name:
            print(f"   💡 SUGGESTED FIX: Add partner_id as related field to customer_id")
            print(f"      partner_id = fields.Many2one('res.partner', related='customer_id', store=True)")
        elif 'shredding' in model_name:
            print(f"   💡 SUGGESTED FIX: Add partner_id as related field to customer_id")
            print(f"      partner_id = fields.Many2one('res.partner', related='customer_id', store=True)")
        else:
            print(f"   💡 SUGGESTED FIX: Add partner_id field")
            print(f"      partner_id = fields.Many2one('res.partner', string='Partner')")

def main():
    """Main function"""
    print("🚀 PARTNER_ID KEYERROR ANALYZER")
    print("=" * 60)
    
    suggest_fixes()
    
    print("\n📋 NEXT STEPS:")
    print("1. Add missing partner_id fields to models that need them")
    print("2. Use related fields where appropriate (e.g., related='customer_id')")
    print("3. Commit changes and test deployment")
    print("4. Continue systematic error resolution")

if __name__ == "__main__":
    main()
