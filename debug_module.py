#!/usr/bin/env python3
"""
Debug script for Records Management Module
This script helps you test and debug your Odoo module code without running a full Odoo server.
"""

import sys
import os

# Add the workspace to Python path
sys.path.insert(0, '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')
sys.path.insert(0, '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management')

def test_module_imports():
    """Test if all module imports work correctly"""
    print("🔍 Testing module imports...")
    
    try:
        # Test basic model imports
        from records_management.models import records_document
        print("✅ records_document imported successfully")
        
        from records_management.models import records_box
        print("✅ records_box imported successfully")
        
        from records_management.models import pickup_request
        print("✅ pickup_request imported successfully")
        
        print("🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def analyze_model_structure():
    """Analyze the structure of your models"""
    print("\n📊 Analyzing model structure...")
    
    try:
        # This would work in a real Odoo environment
        # For now, we'll just check the Python files
        models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
        
        python_files = [f for f in os.listdir(models_dir) if f.endswith('.py') and f != '__init__.py']
        
        print(f"📁 Found {len(python_files)} model files:")
        for file in sorted(python_files):
            print(f"   • {file}")
            
        return python_files
        
    except Exception as e:
        print(f"❌ Error analyzing models: {e}")
        return []

def debug_specific_model(model_file=None):
    """Debug a specific model - set breakpoints here!"""
    print(f"\n🐛 Debugging model: {model_file or 'records_document.py'}")
    
    # THIS IS WHERE YOU CAN SET BREAKPOINTS!
    # Click on line numbers in VS Code to set breakpoints
    
    # Example: Let's examine the records document model
    model_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/records_document.py'
    
    print("📖 Reading model file...")
    try:
        with open(model_path, 'r') as f:
            content = f.read()
            
        # Count lines, classes, methods
        lines = content.split('\n')
        classes = [line for line in lines if line.strip().startswith('class ')]
        methods = [line for line in lines if 'def ' in line]
        
        print(f"📊 Model statistics:")
        print(f"   • Lines of code: {len(lines)}")
        print(f"   • Classes found: {len(classes)}")
        print(f"   • Methods found: {len(methods)}")
        
        # Print class names
        if classes:
            print(f"🏗️  Classes:")
            for cls in classes:
                class_name = cls.split('class ')[1].split('(')[0].strip()
                print(f"   • {class_name}")
                
        # SET A BREAKPOINT ON THIS LINE TO INSPECT VARIABLES
        breakpoint_here = "You can set breakpoints on this line!"
        print(f"🔍 {breakpoint_here}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading model: {e}")
        return False

def main():
    """Main debugging function"""
    print("🚀 Starting Records Management Module Debug Session")
    print("=" * 60)
    
    # Test imports first
    if not test_module_imports():
        print("\n⚠️  Import issues detected. Check your module structure.")
        return
    
    # Analyze structure
    models = analyze_model_structure()
    
    # Debug specific model
    debug_specific_model()
    
    print("\n✨ Debug session complete!")
    print("\n💡 Next steps:")
    print("   1. Set breakpoints in VS Code by clicking line numbers")
    print("   2. Press F5 and select 'Debug Records Management Module'")
    print("   3. Use Step Over (F10) to move through code line by line")
    print("   4. Check the Variables panel to inspect values")

if __name__ == "__main__":
    main()
