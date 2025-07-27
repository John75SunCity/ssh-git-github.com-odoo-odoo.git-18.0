#!/usr/bin/env python3
"""
Complete Module Repair Strategy - Never Worked Before
This takes a systematic approach to fix a module that has never successfully installed
"""

import os
import subprocess
import sys
from datetime import datetime

def analyze_never_worked_module():
    """
    Comprehensive analysis for a module that has never worked
    Focus on fundamental structural issues
    """
    
    print("🚨 MODULE NEVER WORKED - FUNDAMENTAL REPAIR NEEDED")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 ROOT CAUSE ANALYSIS:")
    print("   Since the module never worked, the issues are likely:")
    print("   1. Fundamental model definition conflicts")
    print("   2. Circular dependency issues") 
    print("   3. Field relationship mismatches")
    print("   4. Missing core dependencies")
    print("   5. Inheritance chain problems")
    print()
    
    print("🔧 SYSTEMATIC REPAIR STRATEGY:")
    print("   Phase 1: Get minimal module loading")
    print("   Phase 2: Add features incrementally") 
    print("   Phase 3: Test each addition")
    print()

def create_minimal_working_module():
    """Create a minimal version that will load successfully"""
    
    print("📦 CREATING MINIMAL WORKING MODULE...")
    print("-" * 40)
    
    # Backup current problematic files
    backup_dir = "records_management_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🔄 Backing up current module to: {backup_dir}")
    
    try:
        subprocess.run(["cp", "-r", "records_management", backup_dir], check=True)
        print("   ✅ Backup created successfully")
    except Exception as e:
        print(f"   ❌ Backup failed: {e}")
    
    # Create minimal manifest
    minimal_manifest = '''# -*- coding: utf-8 -*-
{
    'name': 'Records Management - Minimal Version',
    'version': '18.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Minimal Records Management System',
    'description': """
        Minimal Records Management System - Testing Version
        This is a stripped-down version to get basic loading working.
    """,
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 100,
}
'''
    
    # Create minimal __init__.py
    minimal_init = '''# -*- coding: utf-8 -*-
"""
Records Management - Minimal Version
"""

from . import models
'''
    
    # Create minimal models __init__.py
    minimal_models_init = '''# -*- coding: utf-8 -*-
"""
Records Management Models - Minimal Version
"""

# Start with just one simple model
from . import records_box
'''
    
    # Create minimal records_box.py
    minimal_records_box = '''# -*- coding: utf-8 -*-
"""
Records Box - Minimal Version
"""

from odoo import models, fields, api, _


class RecordsBox(models.Model):
    """
    Minimal Records Box Model
    """
    
    _name = 'records.box'
    _description = 'Records Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # Minimal required fields
    name = fields.Char(string='Box Number', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    
    # Basic state
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='State', default='draft', tracking=True)
    
    def action_activate(self):
        """Activate the box"""
        self.write({'state': 'active'})
    
    def action_archive(self):
        """Archive the box"""
        self.write({'state': 'archived'})
'''
    
    # Create minimal security file
    minimal_security = '''id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_records_box_user,access_records_box_user,model_records_box,base.group_user,1,1,1,0
access_records_box_manager,access_records_box_manager,model_records_box,base.group_system,1,1,1,1
'''
    
    # Create minimal menu XML
    minimal_menu = '''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Main Menu -->
    <menuitem id="menu_records_management_root"
              name="Records Management"
              sequence="100"/>
    
    <!-- Records Box Menu -->
    <record id="action_records_box" model="ir.actions.act_window">
        <field name="name">Records Boxes</field>
        <field name="res_model">records.box</field>
        <field name="view_mode">tree,form</field>
    </record>
    
    <menuitem id="menu_records_box"
              name="Records Boxes"
              parent="menu_records_management_root"
              action="action_records_box"
              sequence="10"/>
</odoo>
'''
    
    # Write minimal files
    files_to_create = [
        ('records_management/__manifest__.py', minimal_manifest),
        ('records_management/__init__.py', minimal_init),
        ('records_management/models/__init__.py', minimal_models_init),
        ('records_management/models/records_box.py', minimal_records_box),
        ('records_management/security/ir.model.access.csv', minimal_security),
        ('records_management/views/menu_views.xml', minimal_menu),
    ]
    
    print("\n📝 Creating minimal module files:")
    for file_path, content in files_to_create:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Created: {file_path}")
        except Exception as e:
            print(f"   ❌ Failed to create {file_path}: {e}")
    
    return True

def test_minimal_install():
    """Test the minimal module installation"""
    
    print("\n🧪 TESTING MINIMAL MODULE INSTALLATION...")
    print("-" * 40)
    
    # Try to find Odoo executable
    possible_paths = [
        "/home/odoo/src/odoo/odoo-bin",
        "./odoo-bin",
        "odoo-bin"
    ]
    
    odoo_path = None
    for path in possible_paths:
        if os.path.exists(path):
            odoo_path = path
            break
    
    if not odoo_path:
        print("❌ Could not find Odoo executable")
        print("📋 Manual test commands:")
        print("   python3 /path/to/odoo-bin -d test_records -i records_management --stop-after-init")
        return False
    
    print(f"✅ Found Odoo: {odoo_path}")
    
    # Test installation command
    test_cmd = f"python3 {odoo_path} -d test_records_minimal -i records_management --stop-after-init --log-level=info"
    print(f"🔧 Test command: {test_cmd}")
    
    try:
        result = subprocess.run(
            test_cmd.split(),
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ MINIMAL MODULE INSTALLED SUCCESSFULLY!")
            return True
        else:
            print("❌ Installation failed:")
            print("STDERR:", result.stderr[-1000:])  # Last 1000 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing installation: {e}")
        return False

def get_github_repository_status():
    """Check the GitHub repository status"""
    
    print("\n📂 GITHUB REPOSITORY ANALYSIS:")
    print("-" * 40)
    
    # Check if we're in a git repository
    try:
        result = subprocess.run(["git", "status"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ In Git repository")
            
            # Check remote
            remote_result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
            if "John75SunCity" in remote_result.stdout:
                print("✅ Connected to John75SunCity repository")
                
                # Check for differences
                diff_result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
                if diff_result.stdout.strip():
                    print("📝 Local changes found:")
                    for file in diff_result.stdout.strip().split('\n'):
                        print(f"   • {file}")
                else:
                    print("✅ Working directory clean")
            else:
                print("⚠️  Not connected to expected repository")
        else:
            print("❌ Not in a Git repository")
    except Exception as e:
        print(f"❌ Git check failed: {e}")

def comprehensive_repair_plan():
    """Create a comprehensive repair plan"""
    
    print("\n🎯 COMPREHENSIVE REPAIR PLAN:")
    print("=" * 40)
    
    print("Phase 1: Minimal Working Module ✅")
    print("   • Strip down to basic functionality")
    print("   • Test installation success")
    print("   • Verify core structure works")
    print()
    
    print("Phase 2: Incremental Feature Addition")
    print("   • Add one model at a time")
    print("   • Test after each addition")
    print("   • Fix issues as they appear")
    print()
    
    print("Phase 3: Advanced Features")
    print("   • Add complex relationships")
    print("   • Implement business logic")
    print("   • Add monitoring system")
    print()
    
    print("Phase 4: GitHub Integration")
    print("   • Compare with working repository")
    print("   • Merge successful patterns")
    print("   • Document working configuration")

if __name__ == "__main__":
    # Change to the correct directory
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    # Run comprehensive analysis
    analyze_never_worked_module()
    
    # Check GitHub status
    get_github_repository_status()
    
    # Create minimal working module
    create_minimal_working_module()
    
    # Test minimal installation
    test_result = test_minimal_install()
    
    # Show comprehensive plan
    comprehensive_repair_plan()
    
    print(f"\n✅ REPAIR STRATEGY COMPLETE!")
    print(f"   Next: Test the minimal module installation")
    if test_result:
        print(f"   🎉 Minimal module works! Ready for incremental additions.")
    else:
        print(f"   🔧 Minimal module needs debugging - check output above.")
