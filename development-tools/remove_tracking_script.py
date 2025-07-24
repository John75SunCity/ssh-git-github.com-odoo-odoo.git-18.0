#!/usr/bin/env python3
"""
Script to remove all tracking=True parameters from Odoo 18.0 Records Management module
and ensure proper mail.thread inheritance is in place.
"""

import os
import re
import glob

def process_file(file_path):
    """Process a single Python file to remove tracking=True parameters"""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remove tracking=True parameters with various formatting
    patterns = [
        r', tracking=True',
        r',\s*tracking=True',
        r'\s*tracking=True,',
        r'\s*tracking=True\s*,',
        r'tracking=True,\s*',
        r'tracking=True\s*',
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content)
    
    # Clean up any double commas or spaces that might have been left
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r',\s*\)', ')', content)
    content = re.sub(r'\(\s*,', '(', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Updated: {file_path}")
        return True
    else:
        print(f"  ⏭️  No changes needed: {file_path}")
        return False

def check_mail_thread_inheritance(file_path):
    """Check if a model file has proper mail.thread inheritance"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for model class definitions
    model_classes = re.findall(r'class\s+(\w+)\(models\.Model\):', content)
    
    if not model_classes:
        return True  # No models in this file
    
    # Check if mail.thread is inherited
    has_mail_thread = (
        "'mail.thread'" in content or
        '"mail.thread"' in content or
        "'mail.thread', 'mail.activity.mixin'" in content or
        '"mail.thread", "mail.activity.mixin"' in content
    )
    
    return has_mail_thread, model_classes

def main():
    """Main function to process all model files"""
    print("🔧 Odoo 18.0 Tracking Parameter Cleanup Script")
    print("=" * 50)
    
    # Get all Python files in models directory
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    python_files = glob.glob(os.path.join(models_dir, "*.py"))
    
    # Filter out __init__.py and other non-model files
    model_files = [f for f in python_files if not f.endswith('__init__.py')]
    
    updated_files = 0
    total_files = len(model_files)
    
    print(f"📁 Found {total_files} model files to process")
    print()
    
    # Process each file
    for file_path in sorted(model_files):
        if process_file(file_path):
            updated_files += 1
    
    print()
    print("📊 SUMMARY")
    print("-" * 20)
    print(f"Total files processed: {total_files}")
    print(f"Files updated: {updated_files}")
    print(f"Files unchanged: {total_files - updated_files}")
    
    print()
    print("🔍 Checking mail.thread inheritance...")
    print("-" * 40)
    
    # Check mail.thread inheritance
    for file_path in sorted(model_files):
        result = check_mail_thread_inheritance(file_path)
        if isinstance(result, tuple):
            has_mail_thread, model_classes = result
            filename = os.path.basename(file_path)
            if not has_mail_thread:
                print(f"⚠️  {filename}: Models {model_classes} may need mail.thread inheritance")
            else:
                print(f"✅ {filename}: Mail.thread inheritance found")
    
    print()
    print("🎉 Tracking parameter cleanup completed!")
    print("📋 Next steps:")
    print("   1. Review any models that need mail.thread inheritance")
    print("   2. Test the module installation")
    print("   3. Verify audit trail functionality works properly")

if __name__ == "__main__":
    main()
