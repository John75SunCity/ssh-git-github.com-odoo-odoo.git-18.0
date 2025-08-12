#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix View Naming Standards Script

Fixes all XML view files to follow Odoo's standard naming conventions:
1. Record ID: view_<model_name>_<view_type> (underscores, tree instead of list)
2. View name field: <model.name>.<view.type> (dots, tree instead of list)
3. Proper comments with consistent formatting
4. Standard view type naming (tree, form, search, etc.)

Author: Records Management System
Version: 18.0.6.0.0
"""

import os
import re
import glob
from pathlib import Path

def fix_view_naming_standards():
    """Fix all view files according to Odoo naming standards"""
    
    views_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views"
    
    # View type mappings (old -> new)
    view_type_mapping = {
        'list': 'tree',
        'List': 'tree', 
        'LIST': 'tree'
    }
    
    fixed_files = []
    
    # Get all XML files in views directory
    xml_files = glob.glob(os.path.join(views_dir, "*.xml"))
    
    print(f"🔍 Found {len(xml_files)} XML files to process...")
    
    for xml_file in xml_files:
        print(f"\n📄 Processing: {os.path.basename(xml_file)}")
        
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix patterns one by one
            content = fix_record_ids(content)
            content = fix_view_names(content)  
            content = fix_comments(content)
            content = fix_view_types(content, view_type_mapping)
            
            # Only write if changes were made
            if content != original_content:
                with open(xml_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(os.path.basename(xml_file))
                print(f"✅ Fixed: {os.path.basename(xml_file)}")
            else:
                print(f"⏭️  No changes needed: {os.path.basename(xml_file)}")
                
        except Exception as e:
            print(f"❌ Error processing {xml_file}: {str(e)}")
    
    print(f"\n🎉 Successfully fixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  ✅ {file}")
    
    return fixed_files

def fix_record_ids(content):
    """Fix record ID naming: view_model_name_view_type"""
    
    # Pattern: id="view_some_model_list" -> id="view_some_model_tree"  
    content = re.sub(
        r'id="(view_[^_"]+(?:_[^_"]+)*?)_list"',
        r'id="\1_tree"',
        content
    )
    
    # Pattern: id="view_some_model_List" -> id="view_some_model_tree"
    content = re.sub(
        r'id="(view_[^_"]+(?:_[^_"]+)*?)_List"', 
        r'id="\1_tree"',
        content
    )
    
    return content

def fix_view_names(content):
    """Fix view name field: model.name.view.type"""
    
    # Pattern: <field name="name">view.model.name.list</field>
    # Replace with: <field name="name">model.name.tree</field>
    def replace_name_field(match):
        full_match = match.group(0)
        name_value = match.group(1)
        
        # Remove 'view.' prefix and replace list with tree
        if name_value.startswith('view.'):
            name_value = name_value[5:]  # Remove 'view.' prefix
        
        name_value = name_value.replace('.list', '.tree')
        name_value = name_value.replace('.List', '.tree')
        
        return f'<field name="name">{name_value}</field>'
    
    content = re.sub(
        r'<field name="name">([^<]+)</field>',
        replace_name_field,
        content
    )
    
    return content

def fix_comments(content):
    """Fix comment formatting to be more descriptive and consistent"""
    
    # Pattern: <!-- View model.name View List -->
    # Replace with: <!-- Tree view for model.name -->
    def replace_comment(match):
        comment_content = match.group(1).strip()
        
        # Extract model name from comment
        model_match = re.search(r'View\s+([^\s]+(?:\.[^\s]+)*)\s+(?:View\s+)?(list|List|form|Form|search|Search|tree|Tree)', comment_content, re.IGNORECASE)
        
        if model_match:
            model_name = model_match.group(1)
            view_type = model_match.group(2).lower()
            
            # Convert list to tree
            if view_type == 'list':
                view_type = 'tree'
                
            # Generate proper comment
            if view_type == 'tree':
                return f"    <!-- Tree view for {model_name} -->"
            elif view_type == 'form':
                return f"    <!-- Form view for {model_name} -->"
            elif view_type == 'search':
                return f"    <!-- Search view for {model_name} -->"
            else:
                return f"    <!-- {view_type.title()} view for {model_name} -->"
        
        return match.group(0)  # Return original if no match
    
    content = re.sub(
        r'    <!--\s*([^>]+)\s*-->',
        replace_comment,
        content
    )
    
    return content

def fix_view_types(content, mapping):
    """Fix view type references throughout the file"""
    
    # Fix in arch type="xml" tags - change list to tree
    content = re.sub(
        r'<(list)([^>]*)>',
        r'<tree\2>',
        content
    )
    
    content = re.sub(
        r'</(list)>',
        r'</tree>',
        content
    )
    
    return content

if __name__ == "__main__":
    print("🚀 Starting View Naming Standards Fix...")
    print("=" * 50)
    
    fixed_files = fix_view_naming_standards()
    
    print("\n" + "=" * 50)
    print(f"🎯 Process Complete! Fixed {len(fixed_files)} files.")
    
    if fixed_files:
        print("\n📋 Summary of changes applied:")
        print("  ✅ Record IDs: view_model_name_tree (instead of _list)")
        print("  ✅ View names: model.name.tree (instead of view.model.name.list)")
        print("  ✅ Comments: Standardized descriptive format")
        print("  ✅ View types: <tree> instead of <list>")
        print("\n🚀 Ready for commit and deployment!")
    else:
        print("✨ All files already follow Odoo naming standards!")
