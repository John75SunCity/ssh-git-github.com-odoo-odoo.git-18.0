#!/usr/bin/env python3
import subprocess
import sys
import os

# Test module loading
print("Testing records_management module installation...")

try:
    result = subprocess.run([
        'python3', 'odoo-bin', 
        '-d', 'john75suncity-ssh-git-github-com-odoo-odoo-git-8-0--21773170',
        '-u', 'records_management',
        '--stop-after-init',
        '--log-level=info'
    ], capture_output=True, text=True, timeout=60)
    
    print("STDOUT:")
    print(result.stdout[-2000:])  # Last 2000 characters
    print("\nSTDERR:")
    print(result.stderr[-1000:])   # Last 1000 characters
    print(f"\nReturn code: {result.returncode}")
    
    # Check if the menus file was loaded
    if "records_management_menus.xml" in result.stdout:
        print("✅ Menus file was loaded!")
    else:
        print("❌ Menus file was NOT loaded")
        
except subprocess.TimeoutExpired:
    print("❌ Command timed out")
except Exception as e:
    print(f"❌ Error: {e}")
