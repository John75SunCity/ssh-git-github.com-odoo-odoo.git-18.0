#!/usr/bin/env python3
"""
Optimized Dependencies for Records Management Module
Creates a safer dependency configuration for Odoo.sh deployment
"""

def create_optimized_manifest():
    """Create optimized dependency configuration"""
    
    print("🔧 CREATING OPTIMIZED DEPENDENCY CONFIGURATION")
    print("=" * 60)
    
    # Core dependencies (absolutely required)
    core_deps = [
        'base',
        'mail', 
        'web',
        'portal',
    ]
    
    # Business dependencies (required for functionality)
    business_deps = [
        'product',
        'stock',
        'account',
        'sale',
    ]
    
    # Communication dependencies
    communication_deps = [
        'sms',
    ]
    
    # Web/Portal dependencies
    web_deps = [
        'website',
    ]
    
    # POS dependencies
    pos_deps = [
        'point_of_sale',
    ]
    
    # Optional dependencies (may not be available in all editions)
    optional_deps = [
        'barcodes',  # Sometimes not available
        'sign',      # Enterprise only
        'hr',        # Usually available
        'project',   # Usually available  
        'calendar',  # Usually available
        'survey',    # Usually available
    ]
    
    # Create the complete dependency list
    all_deps = core_deps + business_deps + communication_deps + web_deps + pos_deps + optional_deps
    
    print("\n📋 OPTIMIZED DEPENDENCY LIST:")
    print("-" * 40)
    
    print("Core Dependencies (Required):")
    for dep in core_deps:
        print(f"  ✅ '{dep}',")
    
    print("\nBusiness Dependencies (Required):")
    for dep in business_deps:
        print(f"  ✅ '{dep}',")
    
    print("\nCommunication Dependencies:")
    for dep in communication_deps:
        print(f"  ✅ '{dep}',")
    
    print("\nWeb/Portal Dependencies:")
    for dep in web_deps:
        print(f"  ✅ '{dep}',")
    
    print("\nPOS Dependencies:")
    for dep in pos_deps:
        print(f"  ✅ '{dep}',")
    
    print("\nOptional Dependencies (Enterprise/Conditional):")
    for dep in optional_deps:
        print(f"  ⚠️  '{dep}',")
    
    print(f"\n📝 COMPLETE DEPENDS SECTION:")
    print("-" * 40)
    print("'depends': [")
    print("    # Core Odoo Dependencies (Required)")
    for dep in core_deps:
        print(f"    '{dep}',")
    
    print("    ")
    print("    # Business Logic Dependencies (Required)")
    for dep in business_deps:
        print(f"    '{dep}',")
    
    print("    ")
    print("    # Communication Dependencies")
    for dep in communication_deps:
        print(f"    '{dep}',")
    
    print("    ")
    print("    # Web/Portal Dependencies")
    for dep in web_deps:
        print(f"    '{dep}',")
    
    print("    ")
    print("    # POS Dependencies")
    for dep in pos_deps:
        print(f"    '{dep}',")
    
    print("    ")
    print("    # Optional/Enterprise Dependencies")
    for dep in optional_deps:
        print(f"    '{dep}',  # Optional - may not be available in all editions")
    
    print("],")
    
    print(f"\n🎯 LOADING SEQUENCE OPTIMIZATION:")
    print("-" * 40)
    print("Current sequence: 1000 (loads after most modules)")
    print("✅ This is correct - your module should load AFTER all dependencies")
    print("✅ The quality_mrp_workorder failure occurs BEFORE your module loads")
    print("✅ Therefore, the issue is NOT in your dependencies")
    
    print(f"\n⚠️  QUALITY MODULE ISSUE ANALYSIS:")
    print("-" * 40)
    print("The logs show:")
    print("  468/784: quality_mrp_workorder loads")
    print("  469/784: records_management loads") 
    print("")
    print("Since quality_mrp_workorder loads BEFORE your module,")
    print("the test failure is in the quality module itself, not your code.")
    print("")
    print("Possible causes:")
    print("1. Missing quality test data in Odoo.sh")
    print("2. Enterprise edition sync issue")
    print("3. Temporary test infrastructure problem")
    print("4. Quality module missing dependencies")
    
    return all_deps

if __name__ == "__main__":
    deps = create_optimized_manifest()
    print(f"\n✅ Analysis complete. Total dependencies: {len(deps)}")
