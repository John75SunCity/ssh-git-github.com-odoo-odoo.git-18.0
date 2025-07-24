#!/usr/bin/env python3
"""
Comprehensive test of KeyError fixes so far
"""

def count_problematic_one2many_fields():
    """Count problematic One2many fields"""
    import re
    import os
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    
    fixed_count = 0
    safe_count = 0
    potentially_problematic = 0
    
    print("=== COMPREHENSIVE ONE2MANY FIELD ANALYSIS ===\n")
    
    # Scan all Python files
    for filename in os.listdir(models_dir):
        if not filename.endswith('.py') or filename.startswith('__'):
            continue
            
        filepath = os.path.join(models_dir, filename)
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Find One2many fields
        one2many_pattern = r"fields\.One2many\([^)]+\)"
        matches = re.findall(one2many_pattern, content)
        
        if matches:
            print(f"📄 {filename}:")
            for match in matches:
                if "compute=" in match:
                    print(f"  ✅ {match[:50]}... (SAFE - compute method)")
                    fixed_count += 1
                elif "'mail." in match or "'ir.attachment'" in match:
                    print(f"  ✅ {match[:50]}... (SAFE - standard model)")
                    safe_count += 1
                elif "parent_id" in match and filename in match.split(',')[0]:
                    print(f"  ✅ {match[:50]}... (SAFE - self-referential)")
                    safe_count += 1
                else:
                    print(f"  ⚠️  {match[:50]}... (NEEDS CHECK)")
                    potentially_problematic += 1
            print()
    
    print(f"=== SUMMARY ===")
    print(f"✅ Fixed (compute methods): {fixed_count}")
    print(f"✅ Safe (standard/self-ref): {safe_count}")
    print(f"⚠️  Still need checking: {potentially_problematic}")
    print(f"📊 Total fields analyzed: {fixed_count + safe_count + potentially_problematic}")
    
    improvement = fixed_count / (fixed_count + safe_count + potentially_problematic) * 100
    print(f"🎯 Fixed fields percentage: {improvement:.1f}%")
    
    return potentially_problematic

if __name__ == "__main__":
    remaining = count_problematic_one2many_fields()
    print(f"\n🔍 Fields still needing review: {remaining}")
    if remaining == 0:
        print("🎉 ALL FIELDS FIXED OR VERIFIED SAFE!")
    else:
        print("⚡ Continue with systematic review...")
