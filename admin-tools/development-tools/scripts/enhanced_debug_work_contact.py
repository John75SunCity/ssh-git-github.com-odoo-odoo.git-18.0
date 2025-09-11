#!/usr/bin/env python3
"""
Enhanced Debugging Script for work_contact_id Error
Uses the debug flag mentioned in install logs to get complete traceback
"""

import os
import subprocess
import sys
from datetime import datetime

def run_odoo_debug_install():
    """
    Run Odoo installation with enhanced debugging to get complete traceback
    This will show us exactly which field is causing the work_contact_id error
    """
    
    print("🔍 ENHANCED DEBUGGING FOR work_contact_id ERROR")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 Debug Strategy:")
    print("   Using: --log-handler odoo.tools.convert:DEBUG")
    print("   This will show us the EXACT field causing the KeyError")
    print("   Complete traceback with field names and model context")
    print()
    
    # Common Odoo debug commands to try
    debug_commands = [
        # Try different possible Odoo binary locations
        "./odoo-bin -d records_management -i records_management --log-handler odoo.tools.convert:DEBUG --stop-after-init",
        "python3 odoo-bin -d records_management -i records_management --log-handler odoo.tools.convert:DEBUG --stop-after-init",
        "python odoo-bin -d records_management -i records_management --log-handler odoo.tools.convert:DEBUG --stop-after-init",
        # Try with full path if in different location
        "python3 /home/odoo/src/odoo/odoo-bin -d records_management -i records_management --log-handler odoo.tools.convert:DEBUG --stop-after-init",
        # Alternative database name patterns
        "./odoo-bin -d john75suncity-ssh-git-github-com-odoo-odoo-git-18-0-22339409 -i records_management --log-handler odoo.tools.convert:DEBUG --stop-after-init"
    ]
    
    print("🚀 TRYING DEBUG COMMANDS:")
    print("   (Looking for complete traceback with field details)")
    print()
    
    for i, cmd in enumerate(debug_commands, 1):
        print(f"📋 Command {i}: {cmd}")
    
    print()
    print("💡 WHAT TO LOOK FOR IN OUTPUT:")
    print("   • Complete field setup traceback")
    print("   • Exact model and field name causing KeyError")
    print("   • Field relationship details (One2many -> Many2one)")
    print("   • inverse_name parameter causing the issue")
    print()
    
    # Check if we can find Odoo executable
    possible_paths = [
        "./odoo-bin",
        "odoo-bin", 
        "/home/odoo/src/odoo/odoo-bin",
        "../odoo-bin"
    ]
    
    odoo_path = None
    for path in possible_paths:
        if os.path.exists(path) or subprocess.run(["which", path.split()[0]], capture_output=True).returncode == 0:
            odoo_path = path
            break
    
    if odoo_path:
        print(f"✅ Found Odoo executable: {odoo_path}")
        print()
        print("🔧 RUNNING DEBUG COMMAND...")
        print("-" * 40)
        
        # Run with debug logging
        debug_cmd = f"{odoo_path} -d records_management -i records_management --log-handler odoo.tools.convert:DEBUG --stop-after-init"
        print(f"Command: {debug_cmd}")
        print()
        
        try:
            # Run the command and capture output
            result = subprocess.run(
                debug_cmd.split(), 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            print("📊 DEBUG OUTPUT:")
            print("=" * 40)
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            
            # Look for specific patterns in the output
            full_output = result.stdout + result.stderr
            
            if "work_contact_id" in full_output:
                print("\n🎯 FOUND work_contact_id REFERENCES:")
                lines = full_output.split('\n')
                for i, line in enumerate(lines):
                    if "work_contact_id" in line:
                        # Print context around the error
                        start = max(0, i-3)
                        end = min(len(lines), i+4)
                        print(f"\nContext (lines {start}-{end}):")
                        for j in range(start, end):
                            marker = " >>> " if j == i else "     "
                            print(f"{marker}{lines[j]}")
            
            if "setup_nonrelated" in full_output:
                print("\n🔍 FIELD SETUP CONTEXT FOUND")
                # Extract field setup details
                
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out after 5 minutes")
        except Exception as e:
            print(f"❌ Error running command: {e}")
    
    else:
        print("❌ Could not find Odoo executable")
        print("📋 Manual Commands to Try:")
        for cmd in debug_commands:
            print(f"   {cmd}")
    
    print()
    print("🎯 NEXT STEPS AFTER GETTING DEBUG OUTPUT:")
    print("   1. Look for the exact field name in the traceback")
    print("   2. Find which model is trying to create the inverse field")
    print("   3. Locate the One2many field with incorrect inverse_name")
    print("   4. Fix the field definition or remove the problematic field")

def analyze_current_state():
    """Analyze the current state of the module for clues"""
    
    print("\n📋 CURRENT MODULE STATE ANALYSIS:")
    print("=" * 40)
    
    # Check for any files that might have been missed
    patterns_to_check = [
        "work_contact",
        "contact_id", 
        "One2many.*contact",
        "inverse_name.*contact"
    ]
    
    print("🔍 Searching for contact-related patterns...")
    
    for pattern in patterns_to_check:
        print(f"\n   Pattern: {pattern}")
        try:
            result = subprocess.run(
                ["grep", "-r", "-n", pattern, "records_management/"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(f"   Found matches:")
                for line in result.stdout.split('\n')[:5]:  # Show first 5 matches
                    if line.strip():
                        print(f"     {line}")
            else:
                print(f"   No matches found")
        except Exception as e:
            print(f"   Error searching: {e}")

if __name__ == "__main__":
    # Change to the correct directory
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    # Run enhanced debugging
    run_odoo_debug_install()
    
    # Analyze current state
    analyze_current_state()
    
    print("\n✅ ENHANCED DEBUGGING COMPLETE!")
    print("   Check the debug output above for the exact field causing the error.")
