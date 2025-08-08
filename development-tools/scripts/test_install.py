#!/usr/bin/env python3
"""
Quick test to check if records_management module can be imported
"""
import sys
import os

# Add paths
sys.path.insert(0, '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')
sys.path.insert(0, '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/addons')

print("Testing basic Python syntax...")

# Test each model file individually
model_files = [
    'records_management/models/container.py',
    'records_management/models/records_location.py', 
    'records_management/models/records_box.py'
]

for model_file in model_files:
    try:
        print(f"Checking {model_file}...")
        with open(f'/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/{model_file}', 'r') as f:
            content = f.read()
            compile(content, model_file, 'exec')
        print(f"✅ {model_file} - syntax OK")
    except SyntaxError as e:
        print(f"❌ {model_file} - Syntax error: {e}")
    except Exception as e:
        print(f"⚠️ {model_file} - Other error: {e}")

print("Basic syntax check complete.")
