#!/usr/bin/env python3
"""
Find Missing Related Fields - Focus on KeyError issues
"""

import os
import re

def find_related_field_issues():
    """Find related field issues that cause KeyErrors"""
    print("🔍 SEARCHING FOR RELATED FIELD ISSUES...")
    print("=" * 60)
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    issues_found = []
    
    # Pattern to find related fields
    related_pattern = r"(\w+)\s*=\s*fields\.\w+\([^)]*related\s*=\s*['\"]([^'\"]+)['\"]"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = re.findall(related_pattern, content)
                for field_name, related_path in matches:
                    # Check if related path looks problematic
                    parts = related_path.split('.')
                    if len(parts) >= 2:
                        print(f"📄 {filename}:")
                        print(f"   Field: {field_name}")
                        print(f"   Related: {related_path}")
                        print(f"   Target Model: {parts[0]} -> Field: {parts[1]}")
                        print()
                        
                        # Add to issues list for further analysis
                        issues_found.append({
                            'file': filename,
                            'field': field_name,
                            'related_path': related_path,
                            'target_model': parts[0],
                            'target_field': parts[1]
                        })
                        
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
    
    print(f"\n📊 SUMMARY: Found {len(issues_found)} related fields to verify")
    
    # Analyze specific common issues
    print("\n🎯 COMMON POTENTIAL ISSUES:")
    
    model_field_requirements = {
        'visitor_id': ['name', 'email', 'phone'],
        'vehicle_id': ['vehicle_capacity_weight', 'vehicle_capacity_volume'],
        'customer_id': ['billing_account_id', 'key_issuance_allowed', 'key_restriction_reason', 'container_count'],
        'partner_id': ['billing_account_id', 'key_issuance_allowed', 'key_restriction_reason', 'container_count'],
        'box_id': ['name', 'customer_id', 'location_id'],
        'location_id': ['max_capacity'],
        'base_rate_id': ['base_rate']
    }
    
    for issue in issues_found:
        target_model = issue['target_model']
        target_field = issue['target_field']
        
        # Check if this is a known problematic pattern
        if target_model in model_field_requirements:
            required_fields = model_field_requirements[target_model]
            if target_field in required_fields:
                print(f"✅ {issue['file']}: {issue['field']} -> {issue['related_path']} (Should be OK)")
            else:
                print(f"⚠️  {issue['file']}: {issue['field']} -> {issue['related_path']} (POTENTIAL ISSUE)")
        else:
            print(f"❓ {issue['file']}: {issue['field']} -> {issue['related_path']} (UNKNOWN)")

def find_compute_field_issues():
    """Find compute field dependency issues"""
    print("\n🔍 SEARCHING FOR COMPUTE FIELD ISSUES...")
    print("=" * 60)
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    
    # Pattern to find @api.depends decorators
    depends_pattern = r"@api\.depends\(['\"]([^'\"]*)['\"]"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = re.findall(depends_pattern, content)
                for depends_field in matches:
                    if depends_field.strip():  # Skip empty depends
                        print(f"📄 {filename}: @api.depends('{depends_field}')")
                        
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")

def main():
    """Main function"""
    find_related_field_issues()
    find_compute_field_issues()
    
    print("\n🔧 NEXT STEPS:")
    print("1. Verify that target models have the required fields")
    print("2. Add missing fields to target models") 
    print("3. Check for circular dependencies")
    print("4. Verify field types match expectations")

if __name__ == "__main__":
    main()
